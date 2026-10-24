#!/usr/bin/env bash
# Regression suite for the agent-depth gate.
# Default target is the plugin's hooks/agent-depth-gate.sh; override with GATE=/path/to/gate.
#
# Uses REAL agent ids from recorded sessions when the machine has them. For any depth with no
# recorded id it writes a sidecar (<session>/subagents/agent-<id>.meta.json with spawnDepth) into a
# temp dir, which is the format the gate documents; those cases are labelled "synthetic". A case
# that still cannot run prints SKIPPED and makes the suite exit nonzero (UNCHECKED, not passing).
# Must-allow cases matter as much as must-block: a gate that blocks everything passes a
# block-only suite.
GATE="${GATE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../hooks/agent-depth-gate.sh}"
pass=0; fail=0; skip=0
SYN=$(mktemp -d); trap 'rm -rf "$SYN"' EXIT
TP="$SYN/sess.jsonl"

if [ ! -f "$GATE" ]; then
  echo "NO GATE at $GATE — nothing was tested (UNCHECKED, not passing)."
  echo "Set GATE=/path/to/agent-depth-gate.sh."
  exit 1
fi

# Resolve one real agent id per recorded depth. Unset means "this machine has none".
eval "$(python3 - <<'PY'
import json, glob, os, collections
by = collections.defaultdict(list)
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*/subagents/*.meta.json")):
    try:
        d = json.load(open(f))
    except Exception:
        continue
    if d.get("spawnDepth") is not None:
        by[d["spawnDepth"]].append(os.path.basename(f)[6:-10])
for k in (1, 2, 3):
    if by.get(k):
        print(f"D{k}={by[k][0]}")
PY
)"

mksidecar() { # mksidecar <agent_id> <depth>
  mkdir -p "$SYN/sess/subagents"
  printf '{"spawnDepth": %s}' "$2" > "$SYN/sess/subagents/agent-$1.meta.json"
}
SYNTH=""
for k in 1 2 3; do
  v="D$k"
  if [ -z "${!v:-}" ]; then eval "$v=a${k}0000000000000000"; mksidecar "${!v}" "$k"; SYNTH="$SYNTH $k"; fi
done
[ -n "$SYNTH" ] && echo "note: no recorded agent for depth(s)$SYNTH — using synthetic sidecars"

mkjson() { # mkjson <tool_name> <agent_id|-> <description>
  python3 -c '
import json,sys
d = {"tool_name": sys.argv[1], "tool_input": {"description": sys.argv[3], "prompt": "x"},
     "transcript_path": sys.argv[4], "session_id": "test"}
if sys.argv[2] != "-":
    d["agent_id"] = sys.argv[2]; d["agent_type"] = "general-purpose"
print(json.dumps(d))' "$1" "$2" "$3" "$TP"
}

t() { # t <expect> <label> <tool> <agent_id|->
  exp="$1"; label="$2"
  out=$(mkjson "$3" "$4" "probe spawn" | bash "$GATE" 2>&1); rc=$?
  if [ "$rc" -eq "$exp" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n        %s\n' "$rc" "$exp" "$label" "${out:0:100}"; fail=$((fail+1)); fi
}

s() { # s <label> <what-is-missing> — cannot be run here, and says so instead of failing
  printf '  SKIPPED  %s — no %s agent recorded on this machine yet (UNCHECKED, not failing)\n' "$1" "$2"
  skip=$((skip+1))
}

echo "MUST ALLOW:"
t 0 "main session (no agent_id) — breadth at top" Agent -
if [ -n "$D1" ]; then t 0 "depth-1 subagent may still spawn" Agent "$D1"
else s "depth-1 subagent may still spawn" "depth-1"; fi
t 0 "unknown agent id — fails OPEN"               Agent "afffffffffffffffff"
t 0 "non-Agent tool is ignored"                   Bash  "${D2:-afffffffffffffffff}"

echo "MUST BLOCK:"
if [ -n "$D2" ]; then t 2 "depth-2 subagent may not spawn" Agent "$D2"
else s "depth-2 subagent may not spawn" "depth-2"; fi
if [ -n "$D3" ]; then t 2 "depth-3 subagent may not spawn" Agent "$D3"
else s "depth-3 subagent may not spawn" "depth-3"; fi

echo "THRESHOLD IS CONFIGURABLE:"
if [ -n "$D2" ]; then
  out=$(mkjson Agent "$D2" "probe" | CLAUDE_MAX_SPAWN_DEPTH=3 bash "$GATE" 2>&1); rc=$?
  if [ "$rc" -eq 0 ]; then printf '  PASS  (rc=0) depth-2 allowed when limit raised to 3\n'; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=0) raising CLAUDE_MAX_SPAWN_DEPTH\n        %s\n' "$rc" "${out:0:100}"; fail=$((fail+1)); fi
else
  s "depth-2 allowed when limit raised to 3" "depth-2"
fi

echo
echo "pass=$pass fail=$fail skipped=$skip"
if [ "$skip" -gt 0 ]; then
  echo "UNCHECKED: $skip cases skipped — they proved nothing either way."
fi
exit $(( fail > 0 || skip > 0 ))
