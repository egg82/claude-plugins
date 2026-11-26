#!/usr/bin/env bash
# hook-version: 3   # bump on any behaviour change
# PreToolUse(Bash|Monitor): a SUBAGENT may not arm a Monitor, or wait out CI (gh run watch, gh pr checks --watch,
# glab ci status --live, glab ci trace, glab ci view).
#
# WHY: a leaf agent once armed 40 five-minute Monitors in a row just to sleep
# while its test ran in the background. A background shell is fine in a subagent: a foreground run past
# ten minutes is backgrounded automatically, and the job's completion resumes the subagent. The Monitor
# on top of it is pure polling. `fanout-craft` already said so; the briefs never carried the line.
# The main session is untouched: no agent_id in the payload means the root is calling.
set -uo pipefail
payload=$(cat 2>/dev/null || true)
[ -z "$payload" ] && exit 0
PAYLOAD="$payload" python3 - <<'PY'
import json, os, sys
try:
    d = json.loads(os.environ["PAYLOAD"])
except Exception:
    sys.exit(0)
if not d.get("agent_id"):
    sys.exit(0)
if d.get("tool_name") == "Monitor":
    print("Blocked by subagent-wait-gate: in a subagent a Monitor used to wait is polling. Run the command in "
          "the foreground (`timeout: 600000`); if it is backgrounded, end your turn and its completion resumes "
          "you.", file=sys.stderr)
    sys.exit(2)
# A writer waiting out its own PR's CI: about a third of writers' wall time in one measured repo, each fix-and-push
# restarting the pipeline. The orchestrator's merge step waits on CI; the writer pushes, reports and ends.
import re
cmd = (d.get("tool_input") or {}).get("command") or ""
WATCH = (r"\bgh\s+run\s+watch\b|\bgh\s+pr\s+checks\b[^\n|;&]*--watch\b"
         r"|\bglab\s+ci\s+status\b[^\n|;&]*--live\b|\bglab\s+ci\s+trace\b|\bglab\s+ci\s+view\b")
if d.get("tool_name") == "Bash" and re.search(WATCH, cmd):
    print("Blocked by subagent-wait-gate: a subagent does not wait out CI. Push, open the PR, report and end; the "
          "orchestrator's merge step waits on CI and sends you the failing check. To read a finished run once: "
          "`gh run view <id>`.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
PY
