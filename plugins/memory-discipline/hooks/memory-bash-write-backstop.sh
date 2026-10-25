#!/usr/bin/env bash
# hook-version: 4  # bump on any behaviour change; the session hook reports skew
# Stop: report memory/skill files that changed this session WITHOUT a Write/Edit that explains it.
#
# WHY THIS EXISTS, and why it is a second mechanism rather than a wider version of the first:
# `memory-write-gate.sh` is PreToolUse on Write|Edit|MultiEdit|NotebookEdit, so it cannot see a
# write routed through Bash. `bash-footgun-gate.sh` [gate:memory-write-via-bash] closes the shapes a
# COMMAND STRING can prove — `cat >`, `sed -i`, `tee`, a python heredoc calling `write_text()`.
# Neither can see a path the string never contains: one built from a variable, a script written to
# /tmp and then executed, an editor invocation. This catches those, because it does not read
# commands at all — it compares mtimes against the Write/Edit calls the transcript actually records.
#
# WHY IT REPORTS RATHER THAN BLOCKS: a Stop hook runs after the fact by definition. That is the
# correct trade here — the harm is not the write, it is the write going UNCHECKED, and a Stop-time
# notice still leaves time to re-run `memory-write-gate.sh` against the file before the session ends.
# Blocking was never available; the alternative was not noticing.
#
# CONCURRENT SESSIONS ARE NOT A FALSE POSITIVE TO TOLERATE EITHER. Project memories and skills are
# shared by every session on the machine, so a peer session's Edit changes a file this session never
# touched. Measured over four days of parallel sessions in different dirs: 138 of 148 flagged files
# were written by a Write/Edit in ANOTHER session's transcript. So once this session's own transcript
# leaves candidates, every other transcript touched since the session floor is checked for a
# Write/Edit of the same file at or after that floor — the PreToolUse gate ran there too.
#
# SUBAGENT WRITES ARE NOT A FALSE POSITIVE TO TOLERATE — they are a real blind spot, and the
# tolerance above is what nearly let it stand. A child's Write/Edit calls land in ITS transcript,
# never the parent's, so before this every delegated edit read as unexplained. Measured on a config
# sync: six agents edited 24 memory and skill files entirely through the Edit tool, and this hook
# reported all 24 as though they had been written from Bash. That is the cry-wolf failure at full
# volume, on precisely the workflow that touches these trees most — and the remedy it prints
# ("re-apply the change with Edit") was already what had happened.
#
# Worse than noise: with every delegated run firing it, a genuine Bash write would arrive in a list
# the operator had already learned to skim past. So the children's transcripts are read too. They
# sit beside the parent's, at `<transcript>.jsonl` -> `<transcript>/subagents/agent-*.jsonl`, and
# they are parsed with the same loop — a subagent's Write is a sanctioned write, because the
# PreToolUse gate ran inside that agent exactly as it would have here.
#
# LOOP SAFETY: honours stop_hook_active and fires at most once per session.
# COST: zero tokens on the common path — a stat walk over three small trees, silent when clean.

set -uo pipefail
payload=$(cat)
[ -z "$payload" ] && exit 0

PAYLOAD="$payload" python3 - <<'PY'
import json, os, sys, pathlib, glob

try:
    d = json.loads(os.environ.get("PAYLOAD") or "{}")
except ValueError:
    sys.exit(0)

if d.get("stop_hook_active"):
    sys.exit(0)

tp = d.get("transcript_path") or ""
if not tp or not os.path.exists(tp):
    sys.exit(0)

session = d.get("session_id") or os.path.basename(tp)
stamp = pathlib.Path(os.path.expanduser("~/.claude/.memory-backstop")) / session
try:
    stamp.parent.mkdir(parents=True, exist_ok=True)
    if stamp.exists():
        sys.exit(0)
except OSError:
    sys.exit(0)

# --- what the transcript says was written the sanctioned way, and when the session began ----------
# Both come from the same pass. `started` is the floor for "changed this session"; without it every
# memory file ever written looks new.
written, started = set(), None


def scan(path, is_parent):
    """Fold one transcript's Write/Edit targets into `written`.

    Only the PARENT sets `started`. A subagent's transcript begins when it was spawned, which is
    later than the session floor and would raise it — narrowing the window and hiding real changes
    made before the first spawn. The floor is a property of the session, not of whoever wrote last.
    """
    global started
    try:
        fh = open(path, errors="replace")
    except OSError:
        return False
    with fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if is_parent:
                ts = rec.get("timestamp") or ""
                if ts and (started is None or ts < started):
                    started = ts
            msg = rec.get("message") or {}
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict) or c.get("type") != "tool_use":
                    continue
                if c.get("name") not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                    continue
                inp = c.get("input") or {}
                p = inp.get("file_path") or inp.get("path") or inp.get("notebook_path")
                if p:
                    written.add(os.path.realpath(os.path.expanduser(p)))
    return True


if not scan(tp, True):
    sys.exit(0)

# The children, whose writes are as sanctioned as the parent's — the PreToolUse gate ran inside each
# of them. An empty glob is the normal case (no fan-out) and is not an error; it is also
# indistinguishable from a wrong path, which is why the layout is asserted by test-memory-backstop.sh
# rather than trusted here.
for child in sorted(glob.glob(os.path.join(tp[:-6] if tp.endswith(".jsonl") else tp,
                                           "subagents", "agent-*.jsonl"))):
    scan(child, False)

if started is None:
    sys.exit(0)

# ISO8601 from the transcript -> epoch, for comparison against st_mtime.
import datetime
try:
    floor = datetime.datetime.fromisoformat(started.replace("Z", "+00:00")).timestamp()
except ValueError:
    sys.exit(0)

# --- the trees this governs -----------------------------------------------------------------------
# Only THIS session's project memory, which sits beside its transcript: another project's memory
# never loads here, so a change to it is not this session's concern — globbing every project's tree
# made a session in one dir report the memories of every other dir that ran concurrently.
home = os.path.expanduser("~")
trees = [os.path.join(home, ".claude", "memory"),
         os.path.join(os.path.dirname(tp), "memory"),
         os.path.join(home, ".claude", "skills")]

unexplained = []
for tree in trees:
    for root, dirs, files in os.walk(tree):
        # skills/synced/ is the claude.ai skill bucket; Claude Code rewrites it at session start,
        # outside any tool call, so every refresh would read as an unexplained write.
        if root == os.path.join(home, ".claude", "skills") and "synced" in dirs:
            dirs.remove("synced")
        for name in files:
            if not name.endswith(".md"):
                continue
            # The index is appended to by a documented Bash idiom; not a memory body.
            if name == "MEMORY.md":
                continue
            fp = os.path.join(root, name)
            try:
                if os.stat(fp).st_mtime < floor:
                    continue
            except OSError:
                continue
            if os.path.realpath(fp) not in written:
                unexplained.append(fp)

if not unexplained:
    sys.exit(0)

# --- other sessions' transcripts: a peer's Write/Edit explains the file just as well ---------------
# Global memory and skills ARE shared by every session, so peers still matter for those. A peer that
# made the latest change logged it then, so its transcript is at least as new as the oldest candidate
# — a far tighter cut than the session floor, which for a long-lived session reaches back days and
# made this read GBs (6.75s of a 10s timeout, measured). A byte-substring prefilter on
# the home-relative path keeps this cheap (hundreds of MB a day across sessions) and is
# mount-agnostic: where $HOME is reached through a symlink, the same file is recorded under the link
# in one session and under its target in another, and realpath only reconciles them after a hit.
own = {os.path.realpath(tp)} | {os.path.realpath(c) for c in glob.glob(
    os.path.join(tp[:-6] if tp.endswith(".jsonl") else tp, "subagents", "*.jsonl"))}
pending = {os.path.realpath(fp): os.path.relpath(fp, home).encode() for fp in unexplained}
mtimes = []
for fp in unexplained:
    try:
        mtimes.append(os.stat(fp).st_mtime)
    except OSError:
        pass
peer_floor = max(floor, min(mtimes) - 5) if mtimes else floor
peers = glob.glob(os.path.join(home, ".claude", "projects", "*", "*.jsonl")) \
      + glob.glob(os.path.join(home, ".claude", "projects", "*", "*", "subagents", "*.jsonl"))
for peer in peers:
    if not pending:
        break
    try:
        if os.path.realpath(peer) in own or os.stat(peer).st_mtime < peer_floor:
            continue
        with open(peer, "rb") as fh:
            data = fh.read()
    except OSError:
        continue
    if not any(rel in data for rel in pending.values()):
        continue
    for line in data.splitlines():
        if b'"tool_use"' not in line or not any(rel in line for rel in pending.values()):
            continue
        try:
            rec = json.loads(line)
        except ValueError:
            continue
        if (rec.get("timestamp") or "") < started:
            continue
        for c in (rec.get("message") or {}).get("content") or []:
            if not isinstance(c, dict) or c.get("type") != "tool_use":
                continue
            if c.get("name") not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                continue
            inp = c.get("input") or {}
            p = inp.get("file_path") or inp.get("path") or inp.get("notebook_path")
            if p:
                pending.pop(os.path.realpath(os.path.expanduser(p)), None)

unexplained = [fp for fp in unexplained if os.path.realpath(fp) in pending]
if not unexplained:
    sys.exit(0)

try:
    stamp.write_text("")
except OSError:
    pass

shown = sorted(unexplained)[:8]
more = len(unexplained) - len(shown)
lines = "\n".join("  " + p.replace(home, "~") for p in shown)
sys.stderr.write(
    "%d memory/skill file(s) changed this session with no Write/Edit in any session's transcript to explain "
    "it, so `memory-write-gate.sh` never checked them:\n%s%s\n\n"
    "If you wrote these from Bash: that gate is PreToolUse on Write|Edit|MultiEdit only, so the "
    "write looked fine and was never validated. Re-run it against each file before finishing, or "
    "re-apply the change with Edit.\n"
    % (len(unexplained), lines, ("\n  ...and %d more" % more) if more > 0 else "")
)
sys.exit(2)
PY
rc=$?
[ "$rc" -eq 2 ] && exit 2
exit 0
