#!/usr/bin/env python3
"""PostToolUse redactor: strip credential VALUES from tool output before it reaches context.

WHY THIS EXISTS, and why it is not another rule in bash-footgun-gate.sh
----------------------------------------------------------------------
That gate blocks credential leaks with a deny-list of COMMANDS (`vault kv get`,
`vault read`, `vault token lookup`). The list is correct and it did not hold:
credentials kept reaching transcripts after it landed, because the
set of commands that can print a secret is OPEN. `talosctl get machineconfig`
prints a cluster's entire PKI. So does `cat controlplane.yaml`. So does any app
dumping its own config.

Measured: two machine-config dumps in one session, the second piped
through `sed -n '<range>'`. The operator's `print-names-not-values` note warns that
a deny-list of secret-ish WORDS always misses one, because the set of words meaning
"secret" is open. The gate had reproduced that bug one level up -- deny-listing
command NAMES instead of field names. A `talosctl` rule would have been the same
mistake a fourth time.

So this hook never asks what ran. It asks what came back. That question has a
closed answer.

WHAT IT DOES NOT DO, so nobody over-trusts it
---------------------------------------------
  * The command already ran; the value hit the real terminal and any pipe it had.
  * The hooks doc states OpenTelemetry spans and analytics capture the ORIGINAL
    output before this hook runs.
  * It covers whatever the settings.json matcher lists (currently `Bash|Read`).
    A tool outside that matcher never invokes it at all -- and a hook that is not
    matched cannot log its own absence, so widening is a deliberate act.
  * gitleaks flags an AWS secret access key but not a bare `AKIA...` access key ID.
    That is defensible (an ID is closer to a username than a secret) but it is a
    behaviour to know rather than discover.

MEASURED, because the docs do not say: the on-disk transcript receives ONLY the
redacted form. A synthetic token was emitted live and the session
JSONL contained zero occurrences of the raw value and three of the tag. So the
value does not persist locally either -- not just absent from context.

What it buys is the part that matters most: the value never enters the
conversation, so it is never sent to the API on this or any later turn.

FAILURE POSTURE
---------------
Fail OPEN, always. Any exception, unknown schema, missing binary or timeout means
exit 0 emitting nothing, and the original output is used unchanged. A redactor that
mangles or drops legitimate output would be switched off within a day, which is
strictly worse than the prose it replaces.
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

GITLEAKS = next((g for g in (os.path.expanduser("~/.local/bin/gitleaks"), shutil.which("gitleaks"))
                 if g and os.path.exists(g)), os.path.expanduser("~/.local/bin/gitleaks"))
CONFIG = next((c for c in (os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gitleaks-extra.toml"),
                           os.path.expanduser("~/.claude/gitleaks-extra.toml")) if os.path.isfile(c)), "")

# ---------------------------------------------------------------------------
# Prefilter. gitleaks costs ~520ms per invocation and it is ALL process startup
# (measured identical for 2KB and 56KB), so running it on every tool call would add
# half a second to every ls, grep and git status. This decides cheaply whether it is
# worth paying.
#
# It must be at least as broad as gitleaks' own detection, because anything it skips
# is a SILENT false negative -- the one failure mode with no symptom. So it is
# deliberately over-broad: a false hit costs only latency, a false skip costs a leak.
# Every MUST case in test-secret-redact.sh is asserted to pass this filter, so the
# suite fails if a future edit narrows it below gitleaks' reach.
# ---------------------------------------------------------------------------
_PREFILTER_SUBSTRINGS = (
    "begin ", "private key", "ls0tls1", "eyj", "akia", "hvs.", "hvb.", "hvr.",
    "password", "passwd", "secret", "token", "credential", "apikey", "api_key",
    "api-key", "access_key", "access-key", "client_secret", "authorization",
    "bearer ", "bootstrap", "aescbc", "secretbox", "-----",
)
_PREFILTER_RE = re.compile(r"://[^\s:/?#@]{1,64}:[^\s/?#@]{6,}@")

# The substring list above covers `apikey`, `api_key`, `access_key`, `client_secret`
# and friends but NOT a bare `key`, so `SOME_MODEL_KEY=sk-<48 hex>` matched
# nothing, looks_risky() returned False, and gitleaks never ran -- while gitleaks,
# run directly on that same text, reports it as generic-api-key. A live key reached a
# transcript that way. The claim above that this filter "must be at least
# as broad as gitleaks' own detection" was simply false for the commonest rule there is.
#
# So mirror generic-api-key's own shape instead of guessing keywords: its keyword set,
# then an assignment, then >=10 value characters. The length floor matches gitleaks'
# capture group, so this cannot be narrower than the rule it gates -- and it keeps
# `apiVersion: v1` and `kube-apiserver:vX.Y.Z` out, whose values are far too short.
#
# A false hit costs ~520ms of gitleaks startup; a false skip costs a leak. `client-id:
# <guid>` now pays that latency and is still correctly NOT redacted, which is the right
# side of that trade.
_PREFILTER_KEYVAL_RE = re.compile(
    r"(?i)(?:key|api|token|secret|client|passwd|password|auth|access)"
    r"[\w.\-]{0,20}\s*[:=]\s*[\"'`]?[A-Za-z0-9+/=_.\-]{10,}"
)


def looks_risky(text):
    if not text:
        return False
    low = text.lower()
    for s in _PREFILTER_SUBSTRINGS:
        if s in low:
            return True
    if _PREFILTER_KEYVAL_RE.search(text):
        return True
    return bool(_PREFILTER_RE.search(text))


# ---------------------------------------------------------------------------
# PROVENANCE: a value that came out of a secret store is a secret, whatever it
# looks like.
#
# Everything above asks what the text LOOKS like, and that is the right primary
# question -- the set of commands that can print a secret is open, so deny-listing
# them was the mistake this hook was built to replace. But shape-matching has its
# own blind spot and it is not exotic: a short, ordinary-looking password under a
# field name that contains none of the words meaning "secret".
#
# Example. A device credential stored under a username-like field name (`svc-user`) --
# not a keyword -- is printed as `  svc-user: <value>`. It passes everything:
#
#   * a caller's own guard that is a substring deny-list (`pass|secret|key|token`),
#     which `svc-user` does not match. That is the exact failure `print-names-not-values`
#     warns about.
#   * _PREFILTER_SUBSTRINGS: no match.
#   * _PREFILTER_KEYVAL_RE: needs a keyword before the separator. No match.
#   * so gitleaks never runs, and would very likely not flag it either --
#     generic-api-key wants a keyword too.
#
# AND A PRE-TOOL GATE CAN ALREADY HAVE PASSED IT. A rule that blocks a bare
# `vault kv get` and exempts a command that REDIRECTS TO A FILE is sound, since a file
# is not the transcript. Nothing then checks what the next command does with that file:
# `vault kv get ... > f.json; python3 -c "...print(v)"` is the exemption working as
# designed and a leak anyway.
#
# So: when the command that produced this output read a secrets store, the values in
# it are credential material by provenance, and are redacted without asking gitleaks
# whether they look the part. The field NAME survives, which is the whole point -- it
# is what tells you what to rotate -- and the tag keeps `len` and `sha256:12`, which
# is exactly what the operator's habit wants to see instead of a value anyway. That
# makes a false positive cheap: you still get everything you should have printed.
#
# `kv list` is deliberately NOT here. It returns names, never values, and redacting a
# listing would be a false positive with no upside.
# ---------------------------------------------------------------------------
_SECRET_STORE_READ_RE = re.compile(
    r"\b(?:vault|bao)\s+(?:kv\s+get|read|token\s+(?:lookup|create|renew)|print\s+token)\b"
)

# Field names whose values are structure, not secrets. Vault's own table header and
# metadata, plus the shapes the `print names, not values` habit produces on purpose --
# redacting a `len=` or a `sha256=` that somebody deliberately printed INSTEAD of a
# value would be the gate punishing the correct behaviour.
_NOT_A_SECRET_FIELD = {
    "key", "keys", "value", "field", "fields", "len", "length", "sha256", "classes",
    "created_time", "deletion_time", "destroyed", "version", "custom_metadata",
    "mount_type", "refresh_interval", "lease_duration", "lease_id", "renewable",
    "data", "metadata", "path", "type", "accessor", "policies", "ttl", "num_uses",
}

# Values that cannot be a credential: booleans, small integers, placeholders, and
# anything already redacted.
_NOT_A_SECRET_VALUE = re.compile(
    r"^(?:true|false|null|none|n/a|-+|<nil>|\[\]|\{\}|\d{1,10}|<REDACTED\b.*)$", re.I
)

# `key: value`, `key = value`, `"key": "value"`, and Vault's own two-column table
# (which separates with a run of spaces). One pair per line, anchored, so a sentence
# containing a colon is not mistaken for an assignment.
_FIELD_LINE_RE = re.compile(
    r"""^(?P<pre>\s*["']?)(?P<key>[\w.\-/]{1,64})(?P<mid>["']?\s*(?::|=|\s{2,})\s*["']?)"""
    r"""(?P<val>\S.*?)(?P<post>["']?,?\s*)$"""
)


def redact_store_values(text):
    """Blank the value side of every field in output produced by a secret-store read.

    Returns (new_text, count). Leaves the key, the punctuation and the indentation
    exactly as they were, so the output still reads as the thing it is.
    """
    if not text:
        return text, 0
    out, n = [], 0
    for line in text.split("\n"):
        m = _FIELD_LINE_RE.match(line)
        if not m:
            out.append(line)
            continue
        key, val = m.group("key"), m.group("val")
        if key.lower() in _NOT_A_SECRET_FIELD or _NOT_A_SECRET_VALUE.match(val):
            out.append(line)
            continue
        out.append(m.group("pre") + key + m.group("mid")
                   + tag(val, "vault-field") + m.group("post"))
        n += 1
    return "\n".join(out), n


def walk_store_redact(node, counter, depth=0):
    """`redact_store_values` over a whole tool response, mirroring `walk_redact`."""
    if depth > 8:
        return node
    if isinstance(node, str):
        new, n = redact_store_values(node)
        counter[0] += n
        return new
    if isinstance(node, list):
        return [walk_store_redact(v, counter, depth + 1) for v in node]
    if isinstance(node, dict):
        return {k: walk_store_redact(v, counter, depth + 1) for k, v in node.items()}
    return node


def tag(value, rule):
    digest = hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:12]
    return "<REDACTED %s sha256:%s len=%d>" % (rule, digest, len(value))


def scan(text):
    """Return raw gitleaks findings (list of dicts), or None if the scan failed."""
    if not text.strip():
        return []
    cmd = [GITLEAKS, "stdin", "--no-banner", "--report-format", "json",
           "--report-path", "/dev/stdout"]
    if os.path.exists(CONFIG):
        cmd[1:1] = ["--config", CONFIG]
    try:
        proc = subprocess.run(
            cmd, input=text.encode("utf-8", "replace"),
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=20,
        )
    except Exception:
        return None  # None == "could not scan", distinct from [] == "scanned, clean"
    try:
        data = json.loads(proc.stdout.decode("utf-8", "replace") or "[]")
    except Exception:
        return None
    if not isinstance(data, list):
        return None
    return [f for f in data if isinstance(f, dict)]


def redact(text, findings):
    """Blank out each finding using its LINE/COLUMN span, not a string match.

    DETECTION IS NOT REDACTION, and conflating them shipped a hook that found the
    leak and passed it through anyway. gitleaks decodes base64 before matching and
    reports the DECODED bytes in `Secret` -- so for a Talos machine config, where the
    cluster PKI is stored base64-wrapped, `Secret` is a PEM block that does not occur
    anywhere in the output being redacted, and `text.replace(secret, ...)` silently
    replaces nothing. The finding is tagged `decoded:base64` and the span is still
    reported against the ORIGINAL text, which is what makes offsets the right handle.

    Caught only because the regression suite asserted the OUTPUT no longer contained
    a secret. An earlier corpus run counted gitleaks FINDINGS, said 14/15 caught, and
    was measuring something that did not imply the thing it was used to claim.
    """
    if not findings:
        return text, 0
    lines = text.split("\n")

    spans = []
    for f in findings:
        try:
            sl, el = int(f.get("StartLine", 0)), int(f.get("EndLine", 0))
        except Exception:
            continue
        # StartLine/EndLine are 1-BASED. Verified by putting a token on the third
        # line and checking which hypothesis produced a slice that actually contained
        # it -- NOT by reading the docs, and not by the first probe I wrote, which
        # scored both hypotheses as correct because the 0-based slice was the empty
        # string and `"" in secret` is True. An empty input passes a containment test.
        s, e = sl - 1, el - 1
        if s < 0 or e < s or e >= len(lines):
            continue
        spans.append((s, e, f.get("Secret") or "", f.get("RuleID") or "secret"))

    # Bottom-up, so an earlier rewrite cannot shift a later span's line numbers.
    spans.sort(key=lambda t: t[0], reverse=True)

    # Column offsets are deliberately NOT used. gitleaks' StartColumn disagreed with
    # the secret's true offset by one on a live sample, and the semantics are not
    # documented clearly enough to depend on. Line range plus content search needs no
    # such arithmetic and cannot slice a credential in half.
    key_prefix = re.compile(r"^(\s*[\w.\-\[\]\"']{1,64}\s*[:=]\s*[\"']?)")

    n = 0
    for s, e, secret, rule in spans:
        seg = "\n".join(lines[s:e + 1])
        if not seg.strip():
            continue
        # The "already redacted" guard lives on the FALLBACK path only, below. It used
        # to sit here, and being line-scoped rather than secret-scoped it dropped every
        # finding after the first ON THE SAME LINE: once one secret was tagged the line
        # contained "<REDACTED ", so its neighbours were skipped. That is how a `ps`
        # dump leaked a live API key -- two keys in one enormous `podman exec` argv,
        # gitleaks reported BOTH, one was redacted, and the banner said "1 value
        # removed", which reads as success rather than as half a job.
        if secret and secret in seg:
            # Direct hit: blank the credential only, so a field name beside it
            # survives -- the name is what tells you what to rotate.
            new = seg.replace(secret, tag(secret, rule))
        else:
            # Only the span-blanking path needs this: re-blanking a span that is
            # already a redaction tag would nest tags and destroy the field name.
            # A direct hit above is safe without it, because a secret that is still
            # literally present has demonstrably not been redacted yet.
            if "<REDACTED " in seg:
                continue
            # gitleaks decodes base64 before matching and reports the DECODED bytes,
            # so for a Talos machine config `Secret` is a PEM block that appears
            # nowhere in the text being redacted. Fall back to blanking the span,
            # keeping any `key:` prefix on its first line.
            m = key_prefix.match(lines[s])
            prefix = m.group(1) if m else ""
            new = prefix + tag(seg[len(prefix):], rule)
        lines[s:e + 1] = new.split("\n")
        n += 1
    return "\n".join(lines), n


def walk_redact(node, counter, depth=0):
    """Redact every credential-bearing string in a tool response, in place.

    Operates on a COPY OF THE REAL RESPONSE rather than a synthesised one, so the
    schema is preserved by construction. That matters: the hooks doc says a
    replacement not matching the tool's own output schema is silently discarded, and
    only Bash's schema is published -- so building a `Read` reply by hand would be
    guesswork that fails invisibly. Mutating what arrived cannot get the shape wrong.
    """
    if depth > 8:
        return node
    if isinstance(node, str):
        if not looks_risky(node):
            return node
        findings = scan(node)
        if not findings:
            return node
        new, n = redact(node, findings)
        counter[0] += n
        return new
    if isinstance(node, list):
        return [walk_redact(v, counter, depth + 1) for v in node]
    if isinstance(node, dict):
        return {k: walk_redact(v, counter, depth + 1) for k, v in node.items()}
    return node


def main():
    try:
        raw = sys.stdin.read()
    except Exception:
        return
    if not raw.strip():
        return
    try:
        ev = json.loads(raw)
    except Exception:
        return

    tool = ev.get("tool_name")
    resp = ev.get("tool_response")

    # Did the command that produced this read a secret store? Read defensively: a
    # missing or oddly-shaped `tool_input` must mean "no provenance pass", never an
    # exception, because this hook's whole posture is to fail open.
    try:
        command = (ev.get("tool_input") or {}).get("command") or ""
    except Exception:
        command = ""
    from_store = bool(tool == "Bash" and _SECRET_STORE_READ_RE.search(command))

    # Every tool the matcher sends (Bash and Read) is redacted in place: the walk keeps
    # the response's own shape, because a replacement not matching the tool's output
    # schema is silently ignored. Only Bash gets the banner below; its stdout is the one
    # documented free-text field an extra line cannot break.
    if not isinstance(resp, (dict, list, str)):
        return
    # The provenance pass needs no scanner, so a machine without gitleaks still gets
    # it. Everything else does need one, and `scan()` already degrades to "no
    # findings" rather than raising if the binary vanishes mid-session.
    if not os.path.exists(GITLEAKS) and not from_store:
        return

    # Cheap whole-payload gate before any per-string work: if nothing anywhere in the
    # response looks risky, this returns in well under a millisecond, which is what
    # makes a hook on every Bash and Read call affordable at all.
    try:
        blob = resp if isinstance(resp, str) else json.dumps(resp)
    except Exception:
        return
    # `from_store` bypasses the prefilter deliberately: the prefilter asks what the
    # text looks like, and the whole point of the provenance pass is the values that
    # look like nothing.
    if not looks_risky(blob) and not from_store:
        return

    counter = [0]
    new_resp = walk_redact(resp, counter)
    if from_store:
        # After the gitleaks pass, so a value it already tagged is matched by
        # _NOT_A_SECRET_VALUE and not wrapped twice.
        new_resp = walk_store_redact(new_resp, counter)
    if counter[0] == 0:
        # Scan ran and found nothing actionable. Emit nothing so the original output
        # is used -- a failed or empty scan must never silently blank real output.
        return

    # The banner only fits Bash, whose stdout is free text. For other tools an
    # invented field would break the schema and be discarded, so the <REDACTED ...>
    # tags speak for themselves there.
    if tool == "Bash" and isinstance(new_resp, dict) and isinstance(new_resp.get("stdout"), str):
        new_resp["stdout"] += (
            "\n[secret-redact] %d credential-shaped value(s) removed before this "
            "output entered context. The command still PRINTED them to the real "
            "terminal, so if any was live, treat it as locally exposed and rotate "
            "it.\n" % counter[0]
        )

    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "updatedToolOutput": new_resp,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass  # fail open: emit nothing, original output is used
    sys.exit(0)
