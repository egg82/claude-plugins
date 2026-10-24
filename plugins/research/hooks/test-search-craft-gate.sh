#!/usr/bin/env bash
# Must-block AND must-allow cases for search-craft-gate.sh. A gate proven only to block is
# indistinguishable from one that blocks everything, and that is the version people switch off.
set -uo pipefail
GATE="${GATE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/search-craft-gate.sh}"
# GATE defaults to the copy beside this test. Pass GATE=<path> to test a specific copy, and prove
# the path took effect (GATE=/nonexistent must fail every case).
TD=$(mktemp -d); trap 'rm -rf "$TD"' EXIT
STAMPS="$HOME/.claude/.search-craft-gate"
pass=0; fail=0

mktranscript() {   # $1=file  $2=n prior WebSearch  $3=load-style: none|skill|read|mention
  : > "$1"
  local i
  for i in $(seq 1 "${2:-0}"); do
    printf '{"message":{"content":[{"type":"tool_use","name":"WebSearch","input":{"query":"q%s"}}]}}\n' "$i" >> "$1"
  done
  case "${3:-none}" in
    nsskill)   printf '{"message":{"content":[{"type":"tool_use","name":"Skill","input":{"skill":"research:search-craft"}}]}}\n' >> "$1" ;;
    lookalike) printf '{"message":{"content":[{"type":"tool_use","name":"Skill","input":{"skill":"research:not-search-craft"}}]}}\n' >> "$1" ;;
    skill)   printf '{"message":{"content":[{"type":"tool_use","name":"Skill","input":{"skill":"search-craft"}}]}}\n' >> "$1" ;;
    read)    printf '{"message":{"content":[{"type":"tool_use","name":"Read","input":{"file_path":"/home/x/.claude/skills/search-craft/SKILL.md"}}]}}\n' >> "$1" ;;
    mention) printf '{"message":{"content":[{"type":"text","text":"the search-craft skill says to read the failure"}]}}\n' >> "$1" ;;
  esac
}

t() {  # $1=expected rc  $2=label  $3=payload json
  local exp="$1" label="$2" payload="$3" rc out
  out=$(printf '%s' "$payload" | bash "$GATE" 2>&1); rc=$?
  if [ "$rc" -eq "$exp" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n        %s\n' "$rc" "$exp" "$label" "${out:0:120}"; fail=$((fail+1)); fi
}
pay() { printf '{"tool_name":"%s","session_id":"%s","transcript_path":"%s","tool_input":{"query":"x"}}' "$1" "$2" "$3"; }

echo "MUST BLOCK — the method is not loaded:"
mktranscript "$TD/a.jsonl" 0 none
rm -f "$STAMPS/TESTa.first"; t 2 "first search of a session"        "$(pay WebSearch TESTa "$TD/a.jsonl")"
mktranscript "$TD/b.jsonl" 3 none
rm -f "$STAMPS/TESTb.reword"; t 2 "fourth search, still not loaded" "$(pay WebSearch TESTb "$TD/b.jsonl")"
mktranscript "$TD/c.jsonl" 0 mention
rm -f "$STAMPS/TESTc.first"
t 2 "a MENTION of the skill is not a load"                          "$(pay WebSearch TESTc "$TD/c.jsonl")"

mktranscript "$TD/k.jsonl" 0 lookalike
rm -f "$STAMPS/TESTk.first"
t 2 "a skill merely ending in search-craft is not a load"        "$(pay WebSearch TESTk "$TD/k.jsonl")"

echo "MUST ALLOW — loaded, between thresholds, or not a search:"
mktranscript "$TD/l.jsonl" 0 nsskill
t 0 "loaded via a plugin-namespaced Skill name (research:search-craft)" "$(pay WebSearch TESTl "$TD/l.jsonl")"
mktranscript "$TD/d.jsonl" 0 skill
t 0 "loaded via the Skill tool"                                     "$(pay WebSearch TESTd "$TD/d.jsonl")"
mktranscript "$TD/e.jsonl" 5 read
t 0 "loaded by Reading SKILL.md, many searches"                     "$(pay WebSearch TESTe "$TD/e.jsonl")"
mktranscript "$TD/f.jsonl" 1 none
t 0 "second search — between thresholds"                            "$(pay WebSearch TESTf "$TD/f.jsonl")"
mktranscript "$TD/g.jsonl" 2 none
t 0 "third search — still between thresholds"                       "$(pay WebSearch TESTg "$TD/g.jsonl")"
t 0 "WebFetch is not a search"                                      "$(pay WebFetch TESTh "$TD/a.jsonl")"
t 0 "no transcript on disk (fails open)"                            "$(pay WebSearch TESTi /nope/none.jsonl)"
t 0 "empty payload (fails open)"                                    ""

echo "MUST ALLOW — the same threshold never fires twice (no wedge):"
mktranscript "$TD/j.jsonl" 0 none
rm -f "$STAMPS/TESTj.first"
t 2 "first call blocks"                                             "$(pay WebSearch TESTj "$TD/j.jsonl")"
t 0 "identical second call passes"                                  "$(pay WebSearch TESTj "$TD/j.jsonl")"

rm -f "$STAMPS"/TEST*.first "$STAMPS"/TEST*.reword
echo
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
