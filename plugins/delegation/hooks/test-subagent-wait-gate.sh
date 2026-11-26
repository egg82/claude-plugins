#!/usr/bin/env bash
# Test suite for subagent-wait-gate.sh. Honours GATE= so it can be pointed at a stub and proved to fail.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GATE="${GATE:-$HERE/subagent-wait-gate.sh}"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0
t() { # t <want_rc> <label> <json>
  local want="$1" label="$2" json="$3" rc
  printf '%s' "$json" > "$T/p.json"
  bash "$GATE" < "$T/p.json" >/dev/null 2>&1; rc=$?
  if [ "$rc" -eq "$want" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n' "$rc" "$label" "$want"; fail=$((fail+1)); fi
}
echo "MUST BLOCK, a subagent arming a waiter:"
t 2 "subagent Monitor"                  '{"agent_id":"a1","tool_name":"Monitor","tool_input":{"command":"sleep 299"}}'
t 2 "subagent gh run watch"             '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"gh run watch 123 --interval 60"}}'
t 2 "subagent gh pr checks --watch"     '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"gh pr checks 5 --watch"}}'
t 2 "subagent watch inside a chain"     '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"cd x && gh run watch 9 > /dev/null"}}'
t 2 "subagent glab ci status --live"    '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"glab ci status --live"}}'
t 2 "subagent glab ci trace"            '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"glab ci trace tests"}}'
t 2 "subagent glab ci view"             '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"glab ci view"}}'
echo "MUST ALLOW:"
t 0 "subagent glab ci status (once)"    '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"glab ci status"}}'
t 0 "subagent glab ci list"             '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"glab ci list --per-page 5"}}'
t 0 "subagent gh run view"              '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"gh run view 123 --log-failed"}}'
t 0 "subagent gh pr checks (no watch)"  '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"gh pr checks 5"}}'
t 0 "main session gh run watch"         '{"tool_name":"Bash","tool_input":{"command":"gh run watch 123"}}'
t 0 "subagent Bash run_in_background"   '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"pytest","run_in_background":true}}'
t 0 "subagent foreground Bash"          '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"pytest","timeout":600000}}'
t 0 "subagent Bash run_in_background false" '{"agent_id":"a1","tool_name":"Bash","tool_input":{"command":"ls","run_in_background":false}}'
t 0 "main session Monitor"              '{"tool_name":"Monitor","tool_input":{"command":"x"}}'
t 0 "main session background Bash"      '{"tool_name":"Bash","tool_input":{"command":"x","run_in_background":true}}'
t 0 "empty payload"                     ''
t 0 "garbage payload"                   'not json'
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
