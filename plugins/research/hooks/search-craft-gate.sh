#!/usr/bin/env bash
# hook-version: 1
# PreToolUse(WebSearch): make sure the search method is in context before the searching starts.
#
# WHY THIS IS A HOOK AND NOT A MEMORY: it was a memory — `search-read-the-failure` sat in the
# always-on tier for the sole purpose of making `search-craft` load. Measured over 112 sessions in
# 30 days: search-craft loaded **0 times**. The trigger never fired once while occupying the resident
# tier on every request, which is the definition of prose failing to gate behaviour. The harness runs
# this instead.
#
# WHAT IT DOES: blocks a WebSearch (exit 2, message goes back to Claude) at most TWICE per session,
# and never once search-craft has actually been loaded:
#   - on the FIRST search of a session — load the method, then re-issue the query;
#   - on the FOURTH — the "reword it slightly and try again" failure. Two differently-shaped queries
#     that return relevant pages without the answer mean the QUESTION is malformed, not the wording,
#     and that is the case where searching more is the expensive wrong move.
#
# WHY IT CANNOT LOOP: each threshold is stamped in ~/.claude/.search-craft-gate/<session> and fires
# once. If Claude ignores the block and re-issues, the stamp is already there and the search proceeds.
# A gate that can wedge a session gets switched off, which is strictly worse than the prose it
# replaced.
#
# HOW IT KNOWS THE SKILL WAS LOADED: the session transcript, the same way lookup-moment.py counts it —
# a Skill tool call naming search-craft, or a Read of its SKILL.md. NEVER by finding the skill's NAME
# in the text: a resident memory mentioning it made that flag true from line 1 of every transcript and
# the probe could never return non-zero. That bug is why this comment exists.
#
# NOT GATED, deliberately: WebFetch (fetching a known URL is not searching), and MCP search tools,
# whose names vary per server — matching "search" loosely in a tool name would fire on unrelated
# tools, and a gate with false positives gets disabled. Revisit if a specific MCP search tool becomes
# the usual path.
#
# FAILS OPEN on anything unexpected — no payload, no transcript, unreadable stamp dir.
set -uo pipefail

payload=$(cat 2>/dev/null || true)
[ -n "$payload" ] || exit 0

HOOK_PAYLOAD="$payload" python3 - <<'PY'
import json, os, pathlib, sys

try:
    d = json.loads(os.environ["HOOK_PAYLOAD"])
except Exception:
    sys.exit(0)

if (d.get("tool_name") or "") != "WebSearch":
    sys.exit(0)

tp = d.get("transcript_path") or ""
if not tp or not os.path.exists(tp):
    sys.exit(0)

SKILL = "search-craft"
loaded = False
searches = 0
try:
    with open(tp, errors="replace") as fh:
        for line in fh:
            if SKILL not in line and "WebSearch" not in line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            msg = rec.get("message") or {}
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for c in content:
                if not isinstance(c, dict) or c.get("type") != "tool_use":
                    continue
                name = c.get("name") or ""
                inp = c.get("input") or {}
                if name == "WebSearch":
                    searches += 1
                # A real load is the Skill tool invoking it, or a Read of its SKILL.md.
                elif name == "Skill" and ((inp.get("skill") or "") == SKILL
                                          or (inp.get("skill") or "").endswith(":" + SKILL)):
                    loaded = True
                elif name == "Read" and f"skills/{SKILL}/SKILL.md" in str(inp.get("file_path") or ""):
                    loaded = True
except OSError:
    sys.exit(0)

if loaded:
    sys.exit(0)

if searches == 0:
    key, msg = "first", (
        "Blocked by search-craft-gate: this is the session's first web search and the search method\n"
        "is not in context. Load the `search-craft` skill, then re-issue the query.\n\n"
        "This fires because the memory that used to carry this instruction never worked: over 30 days\n"
        "the skill it names loaded zero times. One block, once per session; the next search passes\n"
        "either way.\n"
    )
elif searches >= 3:
    key, msg = "reword", (
        f"Blocked by search-craft-gate: {searches} searches this session and `search-craft` still has\n"
        "not been loaded — this is the reword-and-retry pattern it exists to stop.\n\n"
        "Read the shape of the result set before touching the words. Two differently-SHAPED queries\n"
        "returning relevant pages without the answer means the QUESTION is malformed, not the wording,\n"
        "and more queries will not fix it. Load `search-craft`, or state plainly that the answer may\n"
        "not exist in the form you are asking for.\n"
    )
else:
    sys.exit(0)

stamp_dir = pathlib.Path(os.path.expanduser("~/.claude/.search-craft-gate"))
session = d.get("session_id") or os.path.basename(tp)
stamp = stamp_dir / f"{session}.{key}"
try:
    stamp_dir.mkdir(parents=True, exist_ok=True)
    if stamp.exists():
        sys.exit(0)          # already nudged at this threshold — never wedge the session
    stamp.write_text("1")
except OSError:
    sys.exit(0)              # cannot record it, so do not block: fail open

sys.stderr.write(msg)
sys.exit(2)
PY
