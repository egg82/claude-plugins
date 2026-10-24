#!/usr/bin/env bash
# SubagentStop: append a finished subagent's own digest to a durable log.
#
# WHY THIS EXISTS: the harness already stores every subagent transcript, so a child's work is not
# actually lost when its parent dies. What is lost is *knowing it is there* — the sidecar carries no
# status, so "finished, nobody collected it" and "still running" look identical. This writes the
# completion marker that separates them, and carries the digest so a reader never has to parse a
# multi-MB JSONL to find out what the agent concluded.
#
# WHY A HOOK: the harness runs it. Asking an agent to persist its own findings fails exactly when
# the agent is the thing that died, which is the case the design exists for.
#
# COST: zero tokens. last_assistant_message arrives on stdin already; no model is involved.
#
# LIMIT, stated so nobody trusts it too far: this fires when a CHILD stops, and the harness only
# gives it text the child actually emitted. A child killed mid-tool-call, having emitted no prose,
# leaves nothing here worth reading. Covering that needs the child to write artifacts as it goes —
# a hook cannot substitute for it.
#
# The payload is passed through the environment rather than interpolated into a quoted Python
# string: an apostrophe in a comment silently terminated that string once already.
set -uo pipefail

OUT_DIR="${HOME}/.claude/agent-digests"
mkdir -p "$OUT_DIR" 2>/dev/null || exit 0

payload=$(cat 2>/dev/null || true)
[ -n "$payload" ] || exit 0

HOOK_PAYLOAD="$payload" OUT_DIR="$OUT_DIR" python3 - <<'PY' 2>/dev/null
import json, os, sys, time

try:
    d = json.loads(os.environ["HOOK_PAYLOAD"])
except Exception:
    sys.exit(0)

sid = d.get("session_id") or "unknown-session"

# Cap the digest generously rather than trimming to a guessed "useful" size.
digest = d.get("last_assistant_message") or ""
CAP = 20000

# Named fields are the ones observed on a live payload, NOT the ones the docs advertise. Two
# documented claims were wrong when tested: stop_reason is null on a normal finish rather than
# "end_turn", and transcript_path points at the PARENT session, with the agent's own transcript
# arriving as the undocumented agent_transcript_path.
KNOWN = {
    "session_id", "agent_id", "agent_type", "stop_reason", "transcript_path",
    "agent_transcript_path", "cwd", "last_assistant_message", "hook_event_name",
    "permission_mode", "prompt_id", "stop_hook_active",
}

rec = {
    "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    "session_id": sid,
    "agent_id": d.get("agent_id"),
    "agent_type": d.get("agent_type"),
    "stop_reason": d.get("stop_reason"),
    "agent_transcript_path": d.get("agent_transcript_path"),
    "parent_transcript_path": d.get("transcript_path"),
    "cwd": d.get("cwd"),
    "digest": digest[:CAP],
    "digest_truncated": len(digest) > CAP,
    "digest_chars": len(digest),
    # Anything the harness sends that is not named above. A non-empty value here means the payload
    # shape changed and this hook should be revisited — which is how agent_transcript_path was found.
    "unmapped": {
        k: v for k, v in d.items()
        if k not in KNOWN and not isinstance(v, (dict, list))
    },
}

# Single-line O_APPEND writes; concurrent subagents finishing at once is the normal case, so this
# must never read-modify-write.
with open(os.path.join(os.environ["OUT_DIR"], sid + ".jsonl"), "a") as f:
    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
PY

# Never block or fail a session on account of bookkeeping.
exit 0
