#!/usr/bin/env bash
# hook-version: 1   # bump on any behaviour change; the session hook reports skew
# Stop: report a repo you do NOT own that has been left on a non-default branch.
#
# WHY THIS EXISTS RATHER THAN MORE PROSE. `assume-the-checkout-is-shared` says plainly
# never to `git checkout` a branch in a clone you do not own, because a clean tree is not
# consent -- the user may have an editor open on it. That memory was resident
# and got hit twice, the second time two commands after remediating the first. Knowledge
# that is present and does not fire is an argument for changing the environment, not for
# remembering harder.
#
# WHY NOT A PreToolUse BLOCK, which is the obvious shape: `git checkout main` is also the
# REMEDIATION. A gate on the action blocks the fix as readily as the mistake, and the
# checkout's working directory is frequently not in the command string at all -- the Bash
# tool's cwd persists between calls, so `git checkout foo` names no repo. Neither half is
# provable from a command string, which is the test for whether a rule belongs in
# `bash-footgun-gate.sh`. This checks STATE instead, where the question is decidable.
#
# THE NARROWED VERSION WAS RECONSIDERED AND STILL REJECTED. Gating `git checkout -b` / `switch -c`
# alone would answer the remediation half, since creating a branch is never how you put a tree back,
# and the PreToolUse payload carries `cwd`. It still should not be built:
#   * `git checkout -b` at HEAD rewrites NO files; an editor open on that tree sees nothing change.
#     Later work lands on the wrong branch, which the checkout this hook asks for repairs.
#   * This hook fired in time on both hits and the branch was pushed both times, so nothing was at
#     risk. A second mechanism for a failure the first catches is the accretion prefer-subtraction
#     is about.
#   * `git worktree add` before the FIRST write is a judgement about the work, which no command
#     string proves.
# So this stays a Stop report. If it fails to fire, or fires on damage a restore cannot undo, that is
# the evidence that would change the answer.
#
# WHAT IT WILL NOT CATCH: a checkout made and reverted within one session leaves no trace,
# and that is fine -- the harm is leaving someone else's tree moved, not touching it.
#
# FALSE POSITIVES ARE POSSIBLE AND TOLERATED: the user may legitimately be working on a
# branch in their own clone, and this cannot tell that from damage. Hence "left on", a
# named branch, and no accusation. It costs a line in a report and can never block an
# action -- the reasoning that bars false positives applies to gates that BLOCK.
#
# LOOP SAFETY: honours stop_hook_active, fires at most once per session.
# COST: zero tokens on the common path -- two `git` reads per candidate repo, silent when
# every one is on its default branch.

set -uo pipefail
payload=$(cat)
[ -z "$payload" ] && exit 0

PAYLOAD="$payload" python3 - <<'PY'
import json, os, subprocess, sys, pathlib, glob

try:
    d = json.loads(os.environ.get("PAYLOAD") or "{}")
except ValueError:
    sys.exit(0)
if d.get("stop_hook_active"):
    sys.exit(0)

session = d.get("session_id") or os.path.basename(d.get("transcript_path") or "x")
stamp = pathlib.Path(os.path.expanduser("~/.claude/.shared-checkout")) / session
try:
    stamp.parent.mkdir(parents=True, exist_ok=True)
    if stamp.exists():
        sys.exit(0)
except OSError:
    sys.exit(0)


def git(repo, *args):
    try:
        r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


home = os.path.expanduser("~")
# The user's own top-level clones. NOT worktrees under /tmp or a scratchpad -- those are
# ours by construction and moving them is the whole point of making one.
candidates = [p for p in glob.glob(os.path.join(home, "*", ".git")) if os.path.exists(p)]

# THREE CONDITIONS, and the first version had only one -- which is why this reports nothing
# on its own machine most of the time and is worth reading when it does.
#
# Branch-is-not-default ALONE fires on every clone the user is legitimately working in, every
# session, identically. Measured on the first real run: three repos, none of them this
# session's, and two last touched weeks ago. A check that says the same thing every time is
# one nobody reads, which is the failure it exists to prevent.
#
# So also: HEAD must have moved AFTER this session started (reflog), and the repo must appear
# in this session's own transcript. The second is what separates us from a CONCURRENT session
# -- both move a tree inside the same wall-clock window, and only the transcript says which
# one did it.
session_start = None
commands = []
tp = d.get("transcript_path") or ""
if tp and os.path.exists(tp):
    try:
        for line in open(tp, errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            ts = rec.get("timestamp") or ""
            if ts and (session_start is None or ts < session_start):
                session_start = ts
            # BASH COMMAND STRINGS ONLY, never the whole transcript. Matching the raw text
            # made the hook fire on its own output: its report names the repo paths, that
            # report is quoted back in the transcript, and the path then "appears" -- so a
            # repo nobody touched satisfied the did-we-touch-it test purely because the hook
            # had complained about it once. Exactly the substring trap `verify-dont-anchor`
            # describes, committed inside the probe. Scoping to the tool input means only an
            # actual command counts.
            msg = rec.get("message") or {}
            content = msg.get("content")
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_use" and c.get("name") == "Bash":
                        cmd = (c.get("input") or {}).get("command")
                        if cmd:
                            commands.append(cmd)
    except OSError:
        pass
transcript_text = "\n".join(commands)
if session_start is None:
    sys.exit(0)   # cannot bound the window; say nothing rather than guess

import datetime
try:
    floor = datetime.datetime.fromisoformat(session_start.replace("Z", "+00:00")).timestamp()
except ValueError:
    sys.exit(0)

stray = []
for dotgit in candidates:
    repo = os.path.dirname(dotgit)
    branch = git(repo, "branch", "--show-current")
    if not branch:
        continue  # detached HEAD is not this hook's subject
    # Did WE touch it? A path this session never mentioned is somebody else's business.
    if repo not in transcript_text:
        continue
    # Did HEAD move inside this session? `%ct` is the committer date of the reflog entry,
    # which for a checkout is when the checkout happened.
    last = git(repo, "reflog", "show", "HEAD", "-1", "--format=%ct")
    try:
        if not last or float(last.split()[-1]) < floor:
            continue
    except (ValueError, IndexError):
        continue
    # The default branch as the REMOTE reports it, not assumed to be `main`: this estate
    # has at least one repo on `master`, and hardcoding would report it as stray forever,
    # which is how a check gets ignored.
    head = git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    default = head.split("/", 1)[1] if "/" in head else ""
    if not default:
        default = "main" if git(repo, "rev-parse", "--verify", "-q", "origin/main") else ""
    if default and branch != default:
        stray.append((repo.replace(home, "~"), branch, default))

if not stray:
    sys.exit(0)

try:
    stamp.write_text("")
except OSError:
    pass

lines = "\n".join(f"  {r}  is on '{b}'  (default '{d}')" for r, b, d in stray)
sys.stderr.write(
    "A checkout you do not own is left on a non-default branch:\n%s\n\n"
    "If this session moved it, put it back -- `assume-the-checkout-is-shared`: a clean tree "
    "is not consent, and the user may have an editor open on it. Work in "
    "`git worktree add /tmp/... <branch>` instead, which never moves their tree. If they "
    "were already on that branch, ignore this.\n" % lines
)
sys.exit(2)
PY
rc=$?
[ "$rc" -eq 2 ] && exit 2
exit 0
