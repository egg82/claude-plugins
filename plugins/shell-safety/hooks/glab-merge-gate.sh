#!/usr/bin/env bash
# hook-version: 2   # bump on any behaviour change
# PreToolUse(Bash): refuse `glab mr merge` while the MR has no pipeline that can gate it.
#
# WHY: `glab mr merge` (with --yes or --auto-merge) waits only for a RUNNING pipeline. With the
# MR's pipeline still created/pending, or none yet (seconds after `mr create`), it merges at once,
# unverified, and prints the same URL either way. It was first written up as prose marked
# "not gated: the state lives on the server" — and it kept happening. A hook can read the
# server, so it is gated here.
#
# RULES:
#   - not a `glab mr merge` in command position            -> allow
#   - `GLAB_MERGE_UNGATED=1` prefixes the command           -> allow (a repo with no CI)
#   - the MR's head_pipeline is running or success           -> allow
#   - head_pipeline is missing, or any other status          -> BLOCK (exit 2)
#   - the MR id is a shell expansion (`"$1"` in a loop)      -> BLOCK: the hook sees the text, not
#     the number, so the lookup would fail open
#   - the MR cannot be looked up (no glab, API error)        -> allow, with a warning (fail open:
#     a network blip must not stop all merging; the warning says the gate did not run)
#
# Test: bash test-glab-merge-gate.sh beside this hook (stubs glab on PATH).
exec python3 -c '
import json, os, re, shlex, subprocess, sys

data = json.load(sys.stdin)
cmd = (data.get("tool_input") or {}).get("command") or ""
cwd = data.get("cwd") or os.getcwd()
m = re.search(r"(?m)(?:^|[;&|(]|&&|\|\||\b(?:do|then|else)\b)\s*((?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*)glab\s+mr\s+merge\b([^;&|\n]*)", cmd)
if not m:
    sys.exit(0)
if re.search(r"\bGLAB_MERGE_UNGATED=1\b", m.group(1)):
    sys.exit(0)
try:
    args = shlex.split(m.group(2))
except ValueError:
    args = m.group(2).split()
repo, iid, i = None, None, 0
while i < len(args):
    a = args[i]
    if a in ("-R", "--repo") and i + 1 < len(args):
        repo = args[i + 1]; i += 2; continue
    if a.startswith("--repo="):
        repo = a.split("=", 1)[1]
    elif a in ("-m", "--message", "--sha", "--squash-message") and i + 1 < len(args):
        i += 2; continue
    elif re.fullmatch(r"!?\d+", a) and iid is None:
        iid = a.lstrip("!")
    elif iid is None and not a.startswith("-") and re.search(r"[$`]", a):
        print("Blocked by glab-merge-gate: the MR id `%s` is a shell expansion, so the gate cannot look "
              "it up and would let an unverified merge through. Merge each MR by its literal number." % a,
              file=sys.stderr)
        sys.exit(2)
    i += 1
view = ["glab", "mr", "view"] + ([iid] if iid else []) + (["-R", repo] if repo else []) + ["-F", "json"]
try:
    out = subprocess.run(view, cwd=cwd, capture_output=True, text=True, timeout=20)
    mr = json.loads(out.stdout) if out.returncode == 0 else None
except Exception:
    mr = None
if not isinstance(mr, dict):
    print("glab-merge-gate: could not look up the MR (%s); the pipeline gate did NOT run." % " ".join(view), file=sys.stderr)
    sys.exit(0)
pipeline = mr.get("head_pipeline") or mr.get("pipeline") or {}
status = pipeline.get("status")
if status in ("running", "success"):
    sys.exit(0)
print(
    "Blocked by glab-merge-gate: MR !%s has %s. `glab mr merge` waits only for a RUNNING pipeline, "
    "so it would merge now, unverified, and print the same URL as a gated merge. Wait until the MR "
    "head_pipeline is running (then merge to set auto-merge) or success. A repo with no CI: prefix "
    "the command with GLAB_MERGE_UNGATED=1."
    % (mr.get("iid", iid or "?"), "no pipeline yet" if not status else "a %s pipeline" % status),
    file=sys.stderr,
)
sys.exit(2)
'
