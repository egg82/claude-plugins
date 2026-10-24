#!/usr/bin/env bash
# Tests for prompt-clock.sh: the clock line, and the context-size nudge that fires once per threshold.
set -uo pipefail
GATE="${GATE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/prompt-clock.sh}"
TD=$(mktemp -d); trap 'rm -rf "$TD"; rm -f "$HOME/.claude/state/prompt-clock/"TPC-*' EXIT
pass=0; fail=0

turn() {  # assistant record whose usage sums to $1 tokens of context
  python3 -c 'import json,sys; n=int(sys.argv[1]); print(json.dumps({"type":"assistant","message":{"usage":{"input_tokens":2,"cache_read_input_tokens":n-1002,"cache_creation_input_tokens":1000}}}))' "$1"
}
run() {  # $1=session $2=transcript -> hook stdout
  printf '{"session_id":"%s","transcript_path":"%s"}' "$1" "$2" | bash "$GATE"
}
check() {  # $1=label $2=output $3=python predicate over out
  if OUT="$2" python3 -c "import os,json; out=os.environ['OUT']; import sys; sys.exit(0 if ($3) else 1)"; then
    printf '  PASS  %s\n' "$1"; pass=$((pass+1))
  else printf '  FAIL  %s\n        %s\n' "$1" "${2:0:200}"; fail=$((fail+1)); fi
}
isjson='out.lstrip().startswith("{")'

turn 40000  > "$TD/small.jsonl"
turn 250000 > "$TD/quarter.jsonl"
turn 350000 > "$TD/mid.jsonl"
turn 480000 > "$TD/big.jsonl"

o=$(run TPC-a "$TD/small.jsonl"); check "small context: plain clock line, no nudge" "$o" "out.startswith('[clock]')"
o=$(run TPC-a "$TD/quarter.jsonl"); check "250k: no nudge" "$o" "out.startswith('[clock]')"
o=$(run TPC-b "$TD/mid.jsonl");   check "past 300k: JSON nudge" "$o" "$isjson and 'systemMessage' in json.loads(out)"
check "nudge keeps the clock for the model" "$o" "'[clock]' in json.loads(out)['hookSpecificOutput']['additionalContext']"
check "300k is the SOFT tier: no handoff asked" "$o" "'handoff' not in json.dumps(json.loads(out)).lower()"
o=$(run TPC-b "$TD/mid.jsonl");   check "same threshold again: quiet (plain clock)" "$o" "out.startswith('[clock]')"
o=$(run TPC-b "$TD/big.jsonl");   check "past 450k: fires again" "$o" "$isjson and '480k' in json.loads(out)['systemMessage']"
check "450k is the HARD tier: asks for the handoff" "$o" "'HANDOFF-' in json.loads(out)['hookSpecificOutput']['additionalContext']"
o=$(run TPC-c "$TD/big.jsonl");   check "fresh session already past 450k: one nudge" "$o" "$isjson"
o=$(run TPC-c "$TD/big.jsonl");   check "...and only one" "$o" "out.startswith('[clock]')"
o=$(run TPC-d "$TD/missing.jsonl"); check "missing transcript: plain clock, no error" "$o" "out.startswith('[clock]')"

echo; echo "pass=$pass fail=$fail"; [ "$fail" -eq 0 ]
