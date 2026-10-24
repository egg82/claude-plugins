#!/usr/bin/env bash
# PreToolUse(Agent): stop a fan-out from recursing past a chosen depth.
#
# WHY: an always-on memory told agents not to over-delegate and it changed nothing — measured, in the
# session that wrote it: a top-level agent launched WITH the new brake in its context spawned a child
# that spawned five grandchildren. Text in context does not gate behaviour. The harness runs this.
#
# HOW IT KNOWS WHO IS CALLING: a PreToolUse payload from a SUBAGENT carries `agent_id`/`agent_type`;
# the same payload from the main session does not. So an absent agent_id means the root is calling,
# which is always allowed. For a subagent, its own depth is in the sidecar the harness already writes
# beside the transcript: <project>/<session>/subagents/agent-<id>.meta.json -> {"spawnDepth": N}.
#
# WHERE THE THRESHOLD COMES FROM (default 2, i.e. depth-2 agents may not spawn):
#   main -> depth 1 -> depth 2 is allowed; depth 3 is not.
# On the run this was built from, depth 3 was 30 agents and 49% of the session's cost, while depths
# 1-2 were the work actually asked for. Blocking depth-3 spawns alone would have removed about half
# the spend while leaving "subagents may spawn subagents" intact.
#
# FAILS OPEN. A missing or unreadable sidecar allows the spawn: this is a cost control, and blocking
# real work because bookkeeping is late would be a worse failure than the one it prevents.
set -uo pipefail

MAX_DEPTH="${CLAUDE_MAX_SPAWN_DEPTH:-2}"

payload=$(cat 2>/dev/null || true)
[ -n "$payload" ] || exit 0

HOOK_PAYLOAD="$payload" MAX_DEPTH="$MAX_DEPTH" python3 - <<'PY'
import json, os, sys, glob

try:
    d = json.loads(os.environ["HOOK_PAYLOAD"])
except Exception:
    sys.exit(0)

if (d.get("tool_name") or "") != "Agent":
    sys.exit(0)

agent_id = d.get("agent_id")
if not agent_id:
    sys.exit(0)  # main session — breadth at the top is the whole point

try:
    max_depth = int(os.environ.get("MAX_DEPTH", "2"))
except ValueError:
    max_depth = 2

# The sidecar sits beside the calling agent's own transcript. transcript_path points at the SESSION
# transcript, so derive the subagents dir from it rather than assuming a layout.
tp = d.get("transcript_path") or ""
meta = None
if tp.endswith(".jsonl"):
    cand = os.path.join(tp[:-6], "subagents", "agent-%s.meta.json" % agent_id)
    if os.path.exists(cand):
        meta = cand
if meta is None:
    hits = glob.glob(os.path.expanduser(
        "~/.claude/projects/*/*/subagents/agent-%s.meta.json" % agent_id))
    meta = hits[0] if hits else None

if not meta:
    sys.exit(0)  # fail open: cannot prove depth, do not block real work

try:
    depth = int(json.load(open(meta)).get("spawnDepth"))
except Exception:
    sys.exit(0)

if depth < max_depth:
    sys.exit(0)

desc = (d.get("tool_input") or {}).get("description") or "(no description)"
sys.stderr.write(
    "Blocked by agent-depth-gate: you are a depth-%d subagent, and the spawn limit is %d.\n\n"
    "  attempted: %s\n\n"
    "Do this work yourself and report. If you have found breadth that genuinely warrants its own\n"
    "agents — one per DISTINCT source, not the same question re-asked — return the work-list to your\n"
    "caller instead, naming each item. The root can see total spend and sibling count; you cannot,\n"
    "which is why this limit exists rather than being left to judgement.\n\n"
    "Raise it deliberately for a run with CLAUDE_MAX_SPAWN_DEPTH if the breadth is real.\n"
    % (depth, max_depth, desc)
)
sys.exit(2)
PY
rc=$?
[ "$rc" -eq 2 ] && exit 2
exit 0
