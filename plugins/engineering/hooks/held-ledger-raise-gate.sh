#!/usr/bin/env bash
# hook-version: 2   # bump on any behaviour change; the session hook reports skew
# Stop: block once when a repo this session touched has a HELD LEDGER whose counts went UP.
#
# WHAT A HELD LEDGER IS. The `agentic-engineering` skill's ratchet gates (function size, file
# size, pyright errors, raw SQL...) freeze today's violations in per-file JSON ledgers --
# `tools/held/*.json` or `*_held.json`, shaped `{file: {kind: count}}` -- that may only shrink.
# The CI test fails when the code exceeds the ledger, so the one way to "fix" a red gate
# without fixing the code is to rewrite the ledger upward (`--write`).
#
# WHY THIS EXISTS RATHER THAN MORE PROSE. In one app repo, agents raised held counts to get a
# change through twice, and both times the real cause was a fixable regression. The rule then
# became a CLAUDE.md line. A rule that has already failed as prose gets escalated to the
# harness (`route-lessons-yourself`).
#
# WHY A Stop CHECK OF STATE, NOT A PreToolUse GATE. The common route is a Bash `--write` run
# by the gate's own script, which no command string can judge: the same command LOWERS a
# ledger after a split, which is the correct move. Only the resulting numbers say which
# happened, so this diffs the ledger against the merge-base with the remote default branch,
# which also catches a raise that was already committed.
#
# WHAT COUNTS AS A RAISE: a (file, kind) whose count is higher than at the merge-base, or one
# that is new in a ledger that existed there. A ledger that did not exist at the merge-base is
# being SEEDED, which is the intended first step, so it is allowed. A lowered or removed entry
# is the ratchet working. A new entry in a file that did not exist at the merge-base, with the
# kind's ledger-wide total not risen, is a MOVE (a split carried the findings into the new file)
# and is allowed: v1 blocked a module split whose pyright total fell.
#
# FALSE POSITIVES: the user may genuinely approve a raise. Hence once per session: the block
# names the entries, and a second stop passes. LOOP SAFETY: honours stop_hook_active.
# COST: silent on the common path -- `git` reads only for repos named in this session's own
# tool calls that contain a ledger.

set -uo pipefail
payload=$(cat)
[ -z "$payload" ] && exit 0

PAYLOAD="$payload" python3 -I - <<'PY'
import json, os, subprocess, sys, pathlib

try:
    d = json.loads(os.environ.get("PAYLOAD") or "{}")
except ValueError:
    sys.exit(0)
if d.get("stop_hook_active"):
    sys.exit(0)

session = d.get("session_id") or os.path.basename(d.get("transcript_path") or "x")
stamp = pathlib.Path(os.path.expanduser(os.environ.get("HELD_GATE_STAMP_DIR", "~/.claude/.held-ledger-gate"))) / session
try:
    stamp.parent.mkdir(parents=True, exist_ok=True)
    if stamp.exists():
        sys.exit(0)
except OSError:
    sys.exit(0)


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=10)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


# Directories this session acted in: Bash commands' cd targets and absolute paths, and the
# file paths of Write/Edit calls. Tool INPUTS only, never the transcript's free text, so the
# hook's own report quoted back cannot make a repo look touched.
paths = set()
tp = d.get("transcript_path") or ""
if d.get("cwd"):
    paths.add(d["cwd"])
if tp and os.path.exists(tp):
    for line in open(tp, errors="replace"):
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        content = (rec.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if not (isinstance(c, dict) and c.get("type") == "tool_use"):
                continue
            inp = c.get("input") or {}
            for key in ("file_path", "notebook_path"):
                if inp.get(key):
                    paths.add(os.path.dirname(inp[key]))
            cmd = inp.get("command") if c.get("name") == "Bash" else None
            if cmd:
                for tok in cmd.replace(";", " ").replace("&&", " ").split():
                    tok = tok.strip("'\"")
                    if tok.startswith(("/", "~")):
                        paths.add(os.path.expanduser(tok))

repos = set()
for p in paths:
    while p and not os.path.isdir(p):
        p = os.path.dirname(p)
    if p:
        top = git(p, "rev-parse", "--show-toplevel")
        if top:
            repos.add(top.strip())


def is_ledger(rel):
    return rel.endswith(".json") and ("/held/" in "/" + rel or rel.endswith("_held.json"))


def counts(text):
    try:
        data = json.loads(text)
    except ValueError:
        return None
    out = {}
    if isinstance(data, dict):
        for f, kinds in data.items():
            if isinstance(kinds, dict):
                for k, n in kinds.items():
                    if isinstance(n, (int, float)):
                        out[(f, k)] = n
    return out


raised = []
for repo in sorted(repos):
    listed = (git(repo, "ls-files", "--cached", "--others", "--exclude-standard") or "").splitlines()
    ledgers = [r for r in listed if is_ledger(r)]
    if not ledgers:
        continue
    head = (git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD") or "").strip()
    default = head or next((b for b in ("origin/main", "origin/master") if git(repo, "rev-parse", "--verify", "-q", b)), "")
    base = (git(repo, "merge-base", "HEAD", default) or "").strip() if default else ""
    if not base:
        base = "HEAD"
    for rel in ledgers:
        old_text = git(repo, "show", f"{base}:{rel}")
        if old_text is None:
            continue                     # not in the base: being seeded
        try:
            new_text = pathlib.Path(repo, rel).read_text()
        except OSError:
            continue                     # deleted: nothing held is fine
        old, new = counts(old_text), counts(new_text)
        if old is None or new is None:
            continue

        def kind_total(led, kind):
            return sum(n for (_, k), n in led.items() if k == kind)

        for key, n in sorted(new.items()):
            if n <= old.get(key, 0):
                continue
            # A MOVE, not a raise: the entry's file did not exist at the base (a split or
            # move created it) and this kind's total across the ledger did not rise. A
            # raise in a file that already existed still blocks even when the total
            # falls -- that is the "a fix pays for a regression" case per-file ledgers
            # exist to stop.
            moved = (git(repo, "cat-file", "-e", f"{base}:{key[0]}") is None
                     and kind_total(new, key[1]) <= kind_total(old, key[1]))
            if not moved:
                raised.append((repo, rel, key[0], key[1], old.get(key), n))

if not raised:
    sys.exit(0)

try:
    stamp.write_text("")
except OSError:
    pass

home = os.path.expanduser("~")
lines = "\n".join(
    f"  {r.replace(home, '~')}/{rel}: {f} {k}: {'new' if o is None else o} -> {n}"
    for r, rel, f, k, o, n in raised[:20])
more = f"\n  ...and {len(raised) - 20} more" if len(raised) > 20 else ""
sys.stderr.write(
    "A held ledger went UP compared with the default branch:\n%s%s\n\n"
    "Held counts may only shrink (agentic-engineering skill, section 2). A raise lets a "
    "regression through: in one repo both raises hid a real, fixable bug. Revert the ledger "
    "and fix the code (split the function, fix the type error), or, if the user explicitly "
    "approved this raise, say so in your reply and stop again.\n" % (lines, more)
)
sys.exit(2)
PY
rc=$?
[ "$rc" -eq 2 ] && exit 2
exit 0
