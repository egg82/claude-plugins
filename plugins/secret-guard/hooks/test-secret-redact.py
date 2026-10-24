#!/usr/bin/env python3
"""Regression suite for secret-redact.py.

Three things are asserted, because any one alone is a gate you cannot trust:

  MUST    a real credential shape is redacted. Without these the hook could be inert.
  NEVER   ordinary output passes through byte-identical. Without these the hook could
          be redacting everything, which destroys legitimate output and gets it
          switched off -- the failure mode that leaves you with neither the check nor
          the habit.
  PREFILT every MUST case survives the cheap prefilter. The prefilter is the only part
          that can produce a SILENT false negative: if it narrows below gitleaks'
          reach, the hook stops scanning and reports nothing, and nothing looks wrong.

Plus a NEGATIVE CONTROL: one case is run against a stubbed scanner that finds nothing,
and the suite asserts that this case FAILS. A suite that cannot fail proves nothing --
if the control passes, every green result above it is meaningless.

All fixture values are synthetic, generated from a fixed seed. No live credential is
present in this file, and none should ever be added to it.
"""

import base64
import importlib.util
import json
import os
import random
import string
import subprocess
import sys
import time

HOOK = os.environ.get("HOOK") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "secret-redact.py")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

_r = random.Random(20260909)


def rnd(n, alpha=string.ascii_letters + string.digits):
    return "".join(_r.choice(alpha) for _ in range(n))


# Realistic LENGTHS matter. A first pass at this corpus used AWS's documented example
# key (AKIAIOSFODNN7EXAMPLE), which gitleaks allowlists on purpose, and a too-short
# Vault token -- both read as "gitleaks misses this" when the fixture was the problem.
_fake_pem = (
    "-----BEGIN EC PRIVATE KEY-----\n"
    + "\n".join(rnd(64, string.ascii_letters + string.digits + "+/") for _ in range(3))
    + "\n-----END EC PRIVATE KEY-----"
)
_b64_pem = base64.b64encode(_fake_pem.encode()).decode()

MUST = [
    ("talos-b64-pem", "    key: %s" % _b64_pem),
    ("plain-pem", _fake_pem),
    ("openssh-key", "-----BEGIN OPENSSH PRIVATE KEY-----\n%s\n%s\n"
                    "-----END OPENSSH PRIVATE KEY-----"
                    % (rnd(70, string.ascii_letters + string.digits + "+/"),
                       rnd(70, string.ascii_letters + string.digits + "+/"))),
    ("jwt", "authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkZBS0UifQ.%s"
            % rnd(43, string.ascii_letters + string.digits + "-_")),
    ("aws-key", "aws_access_key_id = AKIA%s\naws_secret_access_key = %s"
                % (rnd(16, string.ascii_uppercase + string.digits),
                   rnd(40, string.ascii_letters + string.digits + "/+"))),
    ("vault-token", "token: hvs.%s" % rnd(90, string.ascii_letters + string.digits + "-_")),
    ("azure-client-secret", "AZURE_CLIENT_SECRET=%s8Q~%s"
                            % (rnd(3), rnd(34, string.ascii_letters + string.digits + "._~-"))),
    ("url-basic-auth", "https://svcacct:%s@vault.example.test/v1/auth" % rnd(24)),
    ("talos-secretbox", "    secretboxEncryptionSecret: %s="
                        % rnd(43, string.ascii_letters + string.digits + "+/")),
]

# Cases that name the literal values which must be ABSENT afterwards.
#
# The MUST loop asserts only that "<REDACTED" appears SOMEWHERE in the output, which
# cannot tell "both secrets removed" from "one removed and one leaked". Both defects
# below shipped past that check and put a live API key in a transcript:
#
#   ps-argv-two-keys: two secrets on ONE line. gitleaks reported both; redact()'s
#     "already redacted" guard was line-scoped, so the second was skipped and the
#     banner said "1 value removed" -- which reads as success.
#   bare-key-env: the prefilter had `apikey`/`api_key`/`access_key` but no bare `key`,
#     so this text was never scanned at all. A prefilter miss is the failure mode with
#     no symptom, which is why looks_risky() is asserted separately below.
_k1 = rnd(48, "0123456789abcdef")
_k2 = rnd(48, "0123456789abcdef")
_k3 = rnd(48, "0123456789abcdef")
MUST_SCRUB = [
    ("ps-argv-two-keys",
     "35260 podman exec --user=root --env=AAA_KEY=sk-%s "
     "--env=BBB_KEY=sk-%s --env=LANG=en_US.UTF-8 dev su -m user" % (_k1, _k2),
     [_k1, _k2]),
    ("bare-key-env", "SOME_MODEL_KEY=sk-%s" % _k3, [_k3]),
]

# Controls. Every one of these preserves the SHAPE of real output this hook has to pass
# through untouched -- a private CIDR pair, an image-factory schematic hash, OIDC/directory
# GUIDs -- without carrying any actual value from this estate. A hit on any of them is a
# false positive, and false positives are what get a redactor disabled.
NEVER = [
    ("cidrs", "        podSubnets:\n            - 10.244.0.0/16\n"
              "        serviceSubnets:\n            - 10.96.0.0/12"),
    ("image-tags", "image: registry.k8s.io/kube-apiserver:vX.Y.Z\n"
                   "image: ghcr.io/siderolabs/kubelet:vX.Y.Z"),
    ("placeholder", "        password: invalid\n        token: invalid"),
    ("schematic", "image: registry.example.test/installer/"
                  "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef:vX.Y.Z"),
    ("guids", "oidc-client-id: 00000000-1111-4222-8333-444444444444\n"
              "groups: oidc:55555555-6666-4777-8888-999999999999"),
    ("sha-digest", "sha256:9f2e4b1c8a7d6e5f4c3b2a1908f7e6d5c4b3a29180f7e6d5c4b3a2918f7e6d5c"),
    ("plain-listing", "NAME                     READY   STATUS    RESTARTS   AGE\n"
                      "example-operator-5c9f8b  1/1     Running   0          3d"),
    ("kubectl-secret-names", "NAME                  TYPE     DATA   AGE\n"
                             "app-credentials       Opaque   3      44d\n"
                             "metrics-token         Opaque   1      12d"),
]


def run_hook(text, hook=HOOK, command=None):
    ev = {"tool_name": "Bash",
          "tool_input": {"command": command} if command else {},
          "tool_response": {"stdout": text, "stderr": "",
                            "interrupted": False, "isImage": False}}
    p = subprocess.run([sys.executable, hook], input=json.dumps(ev).encode(),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    return p.stdout.decode("utf-8", "replace").strip()


# ---------------------------------------------------------------------------
# PROVENANCE: output of a secret-store read, whatever the values look like.
#
# The case that motivated it: a credential stored under a username-like field name
# (`svc-user`), not a keyword -- so the prefilter never fired and gitleaks
# never ran. Each MUST case below is asserted to be
# invisible to `looks_risky`, which is what makes it a test of the provenance path
# rather than an accidental re-test of the shape path.
# ---------------------------------------------------------------------------
_VAULT_CMD = 'vault kv get -format=json secret/apps/demo > /tmp/v.json'
_pw = rnd(12, string.ascii_letters + string.digits)   # synthetic random value

STORE_MUST_SCRUB = [
    ("vault-reprinted-pair", "key names: ['svc-user']\n  svc-user: %s" % _pw, [_pw]),
    ("vault-table", "====== Data ======\nKey       Value\n---       -----\nsvc-user  %s" % _pw, [_pw]),
    ("vault-json", '  "data": {\n    "svc-user": "%s"\n  }' % _pw, [_pw]),
]

# False-positive controls for the provenance pass specifically. The third is the one
# that matters most: it is the CORRECT way to inspect a secret, and a gate that
# mangles it is a gate that teaches people to stop doing the right thing.
STORE_NEVER = [
    ("vault-list", "Keys\n----\nKEY_A\nKEY_B"),
    ("vault-metadata", "created_time     2020-01-01T00:00:00.2Z\nversion          3\n"
                       "destroyed        false"),
    ("names-and-hashes", "  field 'svc-user': len=<n> sha256=<12 hex> classes=<set>"),
]


def redacted_stdout(out):
    if not out:
        return None
    try:
        return json.loads(out)["hookSpecificOutput"]["updatedToolOutput"]["stdout"]
    except Exception:
        return None


def main():
    import shutil   # same lookup as secret-redact.py: ~/.local/bin first, then PATH
    if not (os.path.exists(os.path.expanduser("~/.local/bin/gitleaks")) or shutil.which("gitleaks")):
        print("SKIP-ALL: gitleaks not installed; the hook fails open and redacts nothing.")
        return 1

    # Load the prefilter from the real hook rather than re-implementing it, so the
    # suite cannot drift from the code it is testing.
    spec = importlib.util.spec_from_file_location("sr", HOOK)
    sr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sr)

    fails = []
    print("=== MUST redact ===")
    for name, text in MUST:
        if not sr.looks_risky(text):
            fails.append("%s: PREFILTER SKIPPED IT (silent false negative)" % name)
            print("  %-22s PREFILTER MISS  <-- FAIL" % name)
            continue
        out = redacted_stdout(run_hook(text))
        if out is None:
            fails.append("%s: hook emitted nothing" % name)
            print("  %-22s NOT REDACTED    <-- FAIL" % name)
        elif "<REDACTED" not in out:
            fails.append("%s: no redaction marker" % name)
            print("  %-22s NO MARKER       <-- FAIL" % name)
        else:
            print("  %-22s redacted" % name)

    print("\n=== MUST scrub EVERY listed value (not just 'a marker appeared') ===")
    for name, text, values in MUST_SCRUB:
        if not sr.looks_risky(text):
            fails.append("%s: PREFILTER SKIPPED IT (silent false negative)" % name)
            print("  %-22s PREFILTER MISS  <-- FAIL" % name)
            continue
        out = redacted_stdout(run_hook(text))
        if out is None:
            fails.append("%s: hook emitted nothing" % name)
            print("  %-22s NOT REDACTED    <-- FAIL" % name)
            continue
        leaked = [v for v in values if v in out]
        if leaked:
            fails.append("%s: %d of %d value(s) SURVIVED redaction"
                         % (name, len(leaked), len(values)))
            print("  %-22s %d/%d SURVIVED    <-- FAIL"
                  % (name, len(leaked), len(values)))
        else:
            print("  %-22s all %d scrubbed" % (name, len(values)))

    print("\n=== MUST scrub a secret-store read, whatever the value looks like ===")
    # THE CONTROL FOR THIS BLOCK IS THE NEXT ONE, and the two only mean something as a
    # pair: scrubbed WITH a store read, untouched WITHOUT one. Delete either and the
    # other proves nothing -- "it was redacted" cannot tell provenance from gitleaks
    # having caught it anyway, and "it was not redacted" cannot tell a working
    # provenance rule from a dead one.
    #
    # An earlier version gated these on `not looks_risky(text)` instead, reasoning that
    # a case the prefilter sees is not testing the provenance path. That was a proxy
    # and a wrong one: real `vault kv get` table output contains the `-----` separator
    # row, so it trips the prefilter every time while gitleaks still finds nothing in
    # it. The empirical pair answers the same question without guessing.
    for name, text, values in STORE_MUST_SCRUB:
        out = redacted_stdout(run_hook(text, command=_VAULT_CMD))
        if out is None:
            fails.append("%s: hook emitted nothing for a vault read" % name)
            print("  %-22s NOT REDACTED    <-- FAIL" % name)
            continue
        leaked = [v for v in values if v in out]
        if leaked:
            fails.append("%s: value SURVIVED a secret-store read" % name)
            print("  %-22s SURVIVED        <-- FAIL" % name)
        elif "svc-user" not in out:
            # The field name is what tells you what to rotate; losing it would make
            # the redaction useless even though no secret leaked.
            fails.append("%s: the field NAME was destroyed along with the value" % name)
            print("  %-22s NAME LOST       <-- FAIL" % name)
        else:
            print("  %-22s scrubbed, name kept" % name)

    # Some machines have `bao` and no `vault`; the same read must scrub under either name.
    print("\n=== MUST scrub a `bao` read exactly as a `vault` read ===")
    for name, text, values in STORE_MUST_SCRUB:
        out = redacted_stdout(run_hook(text, command=_VAULT_CMD.replace("vault ", "bao ", 1)))
        if out is None or any(v in out for v in values):
            fails.append("%s: bao kv get output NOT scrubbed" % name)
            print("  %-22s bao NOT SCRUBBED <-- FAIL" % name)
        else:
            print("  %-22s bao scrubbed" % name)

    print("\n=== and the SAME text with no store read must pass through ===")
    for name, text, _values in STORE_MUST_SCRUB:
        # The control that proves the provenance pass is keyed on provenance. Without
        # it, a rule that redacted every `key: value` line in every tool output would
        # pass every test above.
        out = run_hook(text, command="echo hello")
        if out:
            fails.append("%s: redacted with no secret-store read in the command" % name)
            print("  %-22s REWRITTEN       <-- FAIL" % name)
        else:
            print("  %-22s untouched" % name)

    print("\n=== NEVER redact (false-positive controls) ===")
    for name, text in NEVER:
        out = run_hook(text)
        if out:
            fails.append("%s: FALSE POSITIVE, output was rewritten" % name)
            print("  %-22s REWRITTEN       <-- FAIL" % name)
        else:
            print("  %-22s untouched" % name)

    print("\n=== NEVER redact, even on a store read (provenance false positives) ===")
    for name, text in STORE_NEVER:
        out = run_hook(text, command=_VAULT_CMD)
        if out:
            fails.append("%s: FALSE POSITIVE on a store read" % name)
            print("  %-22s REWRITTEN       <-- FAIL" % name)
        else:
            print("  %-22s untouched" % name)

    print("\n=== negative control (proves this suite can fail) ===")
    stub = os.path.join(HERE, ".test-stub-redact.py")
    with open(stub, "w") as fh:
        fh.write("import sys\nsys.exit(0)\n")  # a hook that never redacts anything
    try:
        out = redacted_stdout(run_hook(MUST[0][1], hook=stub))
        if out is None:
            print("  inert-hook case correctly reports NOT REDACTED -> suite can fail")
        else:
            fails.append("negative control passed; the suite cannot detect an inert hook")
            print("  inert hook was scored as redacting  <-- FAIL")
    finally:
        try:
            os.unlink(stub)
        except OSError:
            pass

    print("\n=== prefilter cost on ordinary output ===")
    ordinary = "\n".join("file-%d.yaml  ok" % i for i in range(400))
    t0 = time.time()
    for _ in range(20):
        sr.looks_risky(ordinary)
    print("  prefilter on %d bytes: %.3f ms/call (gitleaks NOT invoked)"
          % (len(ordinary), (time.time() - t0) * 1000 / 20))

    print()
    if fails:
        print("FAILED (%d):" % len(fails))
        for f in fails:
            print("  - " + f)
        return 1
    print("PASS: %d must-redact, %d must-scrub (%d values), %d controls, "
          "negative control held."
          % (len(MUST), len(MUST_SCRUB),
             sum(len(v) for _, _, v in MUST_SCRUB), len(NEVER)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
