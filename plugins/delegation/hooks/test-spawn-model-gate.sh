#!/usr/bin/env bash
# Test suite for spawn-model-gate.sh. Honours GATE= so it can be pointed at a stub and PROVED to fail
# — a suite that has only ever been observed green cannot tell "correctly green" from "always green".
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
GATE="${GATE:-$HERE/spawn-model-gate.sh}"
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
# A test must not mutate the state it tests. The gate reaches $HOME only through expanduser (agent
# definitions, subagent sidecars), so a throwaway home covers every path it can touch — and it RAISES
# coverage, because the two "refuse to overwrite a real one" branches below now always execute.
FAKEHOME="$T/home"; mkdir -p "$FAKEHOME/.claude"
pass=0; fail=0

# Cases go in a FILE and are fed on stdin, so no case text is ever part of a command line this
# session's own PreToolUse gates would inspect.
t() { # t <want_rc> <label> <json>
  local want="$1" label="$2" json="$3" rc
  printf '%s' "$json" > "$T/p.json"
  HOME="$FAKEHOME" bash "$GATE" < "$T/p.json" >/dev/null 2>&1; rc=$?
  if [ "$rc" -eq "$want" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n' "$rc" "$want" "$label"; fail=$((fail+1)); fi
}

echo "MUST BLOCK — an omitted model is the whole point of the gate:"
t 2 "Agent with no model field"            '{"tool_name":"Agent","tool_input":{"prompt":"do a thing","subagent_type":"general-purpose"}}'
t 2 "Agent with empty model"               '{"tool_name":"Agent","tool_input":{"prompt":"x","model":"","subagent_type":"general-purpose"}}'
t 2 "Agent with whitespace-only model"     '{"tool_name":"Agent","tool_input":{"prompt":"x","model":"   ","subagent_type":"general-purpose"}}'
t 2 "Agent with no subagent_type either"   '{"tool_name":"Agent","tool_input":{"prompt":"x"}}'

echo "MUST ALLOW — a named model, including the expensive one:"
t 0 "model: sonnet"                        '{"tool_name":"Agent","tool_input":{"prompt":"x","model":"sonnet"}}'
t 0 "model: haiku"                         '{"tool_name":"Agent","tool_input":{"prompt":"x","model":"haiku"}}'
# opus used to be a plain pass here. It is not any more — see the OPUS RULE block below, which
# owns both directions of that case. Left as a must-BLOCK so the change is visible in the suite
# rather than silently absent.
t 2 "model: opus without a reason now blocks" '{"tool_name":"Agent","tool_input":{"prompt":"x","model":"opus"}}'

echo "MUST ALLOW — the two deliberate exemptions:"
t 0 "fork cannot name a model"             '{"tool_name":"Agent","tool_input":{"prompt":"x","subagent_type":"fork"}}'

echo "MUST ALLOW — not an Agent call at all:"
t 0 "Bash tool"                            '{"tool_name":"Bash","tool_input":{"command":"ls"}}'
t 0 "Write tool"                           '{"tool_name":"Write","tool_input":{"file_path":"/tmp/x","content":"y"}}'

echo "MUST ALLOW — fails open rather than blocking real work:"
t 0 "unparseable payload"                  'not json at all'
t 0 "empty payload"                        ''

echo "MUST ALLOW — an agent type whose own definition sets the model:"
# Build a real definition so this exercises the frontmatter branch rather than a mock of it.
AG="$FAKEHOME/.claude/agents"; mkdir -p "$AG"
DEF="$AG/zz-gatetest-defined.md"
if [ -e "$DEF" ]; then
  echo "  SKIP  (a real $DEF exists; refusing to overwrite it) — UNCHECKED, not passing"
else
  printf -- '---\nname: zz-gatetest-defined\nmodel: haiku\n---\nfixture for test-spawn-model-gate.sh\n' > "$DEF"
  t 0 "agent type with model: in its definition" '{"tool_name":"Agent","tool_input":{"prompt":"x","subagent_type":"zz-gatetest-defined"}}'
  # And the control: same shape WITHOUT a model line must still block, or the branch above proves nothing.
  printf -- '---\nname: zz-gatetest-nomodel\n---\nfixture\n' > "$AG/zz-gatetest-nomodel.md"
  t 2 "agent type WITHOUT model: still blocks" '{"tool_name":"Agent","tool_input":{"prompt":"x","subagent_type":"zz-gatetest-nomodel"}}'
  rm -f "$DEF" "$AG/zz-gatetest-nomodel.md"
fi

echo "FABLE RULES — a Fable caller may not build a Fable tree, but anyone else may name it:"
# caller_is_fable() reads the most recent assistant turn out of the session transcript, so these
# cases need a real .jsonl to read. Building one exercises the branch instead of mocking it.
printf '%s\n' '{"type":"assistant","message":{"model":"claude-fable-5","content":[]}}' > "$T/fable.jsonl"
printf '%s\n' '{"type":"assistant","message":{"model":"claude-opus-5","content":[]}}'  > "$T/opus.jsonl"
t 2 "fable caller naming fable"            "{\"tool_name\":\"Agent\",\"transcript_path\":\"$T/fable.jsonl\",\"tool_input\":{\"prompt\":\"x\",\"model\":\"fable\"}}"
t 0 "opus caller naming fable is a choice" "{\"tool_name\":\"Agent\",\"transcript_path\":\"$T/opus.jsonl\",\"tool_input\":{\"prompt\":\"x\",\"model\":\"fable\"}}"
t 2 "fable caller omitting model"          "{\"tool_name\":\"Agent\",\"transcript_path\":\"$T/fable.jsonl\",\"tool_input\":{\"prompt\":\"x\",\"subagent_type\":\"general-purpose\"}}"
t 0 "fable caller, non-fable model named"  "{\"tool_name\":\"Agent\",\"transcript_path\":\"$T/fable.jsonl\",\"tool_input\":{\"prompt\":\"x\",\"model\":\"sonnet\"}}"
t 0 "fable named, caller undeterminable"   '{"tool_name":"Agent","tool_input":{"prompt":"x","model":"fable"}}'
t 0 "fable caller, fork exemption holds"   "{\"tool_name\":\"Agent\",\"transcript_path\":\"$T/fable.jsonl\",\"tool_input\":{\"prompt\":\"x\",\"subagent_type\":\"fork\"}}"

echo "FABLE RULES — the sidecar branch (a SUBAGENT calling, not the root):"
# caller_is_fable() has two arms and the transcript cases above exercise only one. When a subagent
# is the caller the payload carries agent_id and the model is read from its .meta.json sidecar, so
# this needs a real one in the real store. Written under a clearly-named throwaway project dir and
# removed after; if one somehow exists, refuse rather than overwrite.
SC="$FAKEHOME/.claude/projects/zz-gatetest/zz/subagents"
if [ -e "$SC" ]; then
  echo "  SKIP  ($SC exists; refusing to touch it) — UNCHECKED, not passing"
else
  mkdir -p "$SC"
  printf '{"model":"claude-fable-5","description":"fixture"}\n' > "$SC/agent-zzgatetestfable.meta.json"
  printf '{"model":"claude-opus-5","description":"fixture"}\n'  > "$SC/agent-zzgatetestopus.meta.json"
  t 2 "subagent caller on fable naming fable" '{"tool_name":"Agent","agent_id":"zzgatetestfable","tool_input":{"prompt":"x","model":"fable"}}'
  t 0 "subagent caller on opus naming fable"  '{"tool_name":"Agent","agent_id":"zzgatetestopus","tool_input":{"prompt":"x","model":"fable"}}'
  t 0 "unknown agent_id fails open"           '{"tool_name":"Agent","agent_id":"zznosuchagentid","tool_input":{"prompt":"x","model":"fable"}}'
  rm -rf "$FAKEHOME/.claude/projects/zz-gatetest"
fi

echo "OPUS RULE — opus for a subagent needs a stated reason, not just a named model:"
t 2 "opus with no justification"            '{"tool_name":"Agent","tool_input":{"prompt":"read two files and summarise","model":"opus"}}'
t 2 "opus, reason-shaped but not the token" '{"tool_name":"Agent","tool_input":{"prompt":"this really needs opus because it is hard","model":"opus"}}'
t 0 "opus WITH the justification token"     '{"tool_name":"Agent","tool_input":{"prompt":"[opus: cross-source aggregation over every session] go","model":"opus"}}'
t 0 "token is case-insensitive"             '{"tool_name":"Agent","tool_input":{"prompt":"[OPUS: adversarial review] go","model":"opus"}}'
t 0 "sonnet needs no justification"         '{"tool_name":"Agent","tool_input":{"prompt":"read two files","model":"sonnet"}}'
t 0 "haiku needs no justification"          '{"tool_name":"Agent","tool_input":{"prompt":"read two files","model":"haiku"}}'
t 0 "the word opus in a sonnet prompt"      '{"tool_name":"Agent","tool_input":{"prompt":"compare opus and sonnet outputs","model":"sonnet"}}'

printf '\npass=%s fail=%s\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
