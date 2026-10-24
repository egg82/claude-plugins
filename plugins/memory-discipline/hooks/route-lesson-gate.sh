#!/usr/bin/env bash
# hook-version: 6   # bump on any behaviour change
# Stop: when the session HIT something but routed nothing, say so before it ends.
#
# WHY THIS EXISTS: noticing was never the gap. What fails is the step after: the breakage gets fixed,
# the session moves on, and capturing the lesson only happens when the operator says "we should
# capture this" — exactly the prompting this is meant to remove. A memory (`route-lessons-yourself`)
# exists and has measurably not held; instruction text does not gate behaviour.
#
# TRIGGER: structure in the transcript, never the assistant's prose (matching admission phrases
# misfired on descriptions of other people's bugs and missed admissions phrased any other way).
# ONE signal: STREAK consecutive failed Bash runs — a Bash tool_result with is_error true whose
# content starts `Exit code `. A successful Bash resets the streak; other tools, and Bash results
# that are not a failed run (hook blocks, permission denials, harness refusals), leave it alone.
# It fires when that streak ends after the last routing write.
#
# DROPPED, with the reason, so they are not re-added:
#   - hook blocks: the trap is already gated, so the lesson is already captured (36 of 83 sessions).
#   - reverted Edits: breaking a check and restoring it to prove it can fail is the method
#     verify-dont-anchor asks for, not a mistake.
#   - per-file and per-tool streaks: they counted harness preconditions ("File has not been read
#     yet"), not failed work.
#
# ROUTED means a Write/Edit/MultiEdit/NotebookEdit to a skill, hook, memory or settings path, or a
# Bash command touching decisions.jsonl. Reads do not count.
#
# LOOP SAFETY: honours stop_hook_active, and fires at most once per session (the stamp). A record of
# an unexpected shape is skipped; it never aborts the scan.
#
# LIMIT: it sees only failures the harness recorded. A wrong conclusion that never errored leaves
# nothing structural behind.
set -uo pipefail

payload=$(cat 2>/dev/null || true)
[ -z "$payload" ] && exit 0

PAYLOAD="$payload" python3 - <<'PY'
import json, os, sys, pathlib

try:
    d = json.loads(os.environ.get("PAYLOAD") or "{}")
except ValueError:
    sys.exit(0)
if not isinstance(d, dict):
    sys.exit(0)

# Never re-fire into our own continuation: that is how a Stop hook loops.
if d.get("stop_hook_active"):
    sys.exit(0)

tp = d.get("transcript_path") or ""
if not isinstance(tp, str) or not tp or not os.path.exists(tp):
    sys.exit(0)

session = d.get("session_id") or os.path.basename(tp)
stamp = pathlib.Path(os.path.expanduser("~/.claude/.lesson-routed")) / f"{session}"
stamp.parent.mkdir(parents=True, exist_ok=True)
if stamp.exists():          # one nudge per session, then never again
    sys.exit(0)

STREAK = 3
ROUTE_TARGETS = ("/.claude/skills/", "/.claude/hooks/", "/.claude/memory/",
                 "decisions.jsonl", "/.claude/settings")
WRITERS = ("Write", "Edit", "MultiEdit", "NotebookEdit")

bash_ids = set()            # tool_use ids of Bash calls
last_route, streak, fired_at = -1, 0, -1


def text_of(content):
    if isinstance(content, list):
        return " ".join(c.get("text", "") for c in content if isinstance(c, dict))
    return content if isinstance(content, str) else ""


def blocks(rec):
    """The content blocks of one transcript record, or [] for any shape we do not expect."""
    msg = rec.get("message") if isinstance(rec, dict) else None
    content = msg.get("content") if isinstance(msg, dict) else None
    return [c for c in content if isinstance(c, dict)] if isinstance(content, list) else []


pos = 0
try:
    with open(tp, encoding="utf-8", errors="ignore") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            for c in blocks(rec):
                pos += 1
                if c.get("type") == "tool_use":
                    name, inp = c.get("name"), c.get("input")
                    inp = inp if isinstance(inp, dict) else {}
                    if name == "Bash":
                        bash_ids.add(c.get("id"))
                    if name in WRITERS:
                        blob = " ".join(str(inp.get(k, "")) for k in ("file_path", "notebook_path"))
                        if any(t in blob for t in ROUTE_TARGETS):
                            last_route = pos
                    elif name == "Bash" and "decisions.jsonl" in str(inp.get("command", "")):
                        last_route = pos
                    continue
                if c.get("type") != "tool_result" or c.get("tool_use_id") not in bash_ids:
                    continue
                if c.get("is_error") is True:
                    if text_of(c.get("content")).startswith("Exit code "):
                        streak += 1
                        if streak >= STREAK:
                            fired_at = pos
                    # anything else (hook block, permission denial, harness refusal): neutral
                else:
                    streak = 0
except OSError:
    sys.exit(0)

if fired_at <= last_route:
    sys.exit(0)

stamp.write_text("fired\n")
sys.stderr.write(
    "This session hit %d or more failed Bash runs in a row, and nothing was routed afterwards — no "
    "skill, hook, memory or decisions entry was written.\n\n"
    "Before finishing: decide where the lesson belongs, or say explicitly that it does not "
    "generalise. If it is provable from a command string and you run the shell-safety plugin's "
    "gate, propose a rule for it (with a must-block AND a must-allow case); otherwise write the "
    "lesson where it belongs. Needs task context -> the owning skill, beside the procedure it "
    "breaks. About how work should be done -> your memory or CLAUDE.md. A per-item verdict -> a "
    "keyed log kept beside the runs. One nudge per session; this will not fire again.\n"
    % STREAK
)
sys.exit(2)
PY
rc=$?
# Only the deliberate nudge propagates; a bug in this hook must never wedge a session.
[ "$rc" -eq 2 ] && exit 2
exit 0
