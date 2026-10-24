#!/usr/bin/env bash
# Regression suite for shared-checkout-backstop.sh.
#
# Runs against a FIXTURE HOME so it can never report on the user's real clones. Prove the
# override took effect with the control at the end -- HOOK=/nonexistent must fail every case.
set -uo pipefail
HOOK="${HOOK:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/shared-checkout-backstop.sh}"
pass=0; fail=0

run_case () {
  exp="$1"; label="$2"; fh="$3"; payload="$4"
  payload=${payload//TRANSCRIPT/$fh\/t.jsonl}
  out=$(printf '%s' "$payload" | HOME="$fh" bash "$HOOK" 2>&1); rc=$?
  if [ "$rc" -eq "$exp" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n        %s\n' "$rc" "$exp" "$label" "${out:0:150}"; fail=$((fail+1)); fi
}

# A fixture HOME holding one clone of a bare "remote", left on $1 with default branch $2.
mkfixture () {
  local on="$1" default="${2:-main}"
  local fh; fh=$(mktemp -d)
  local bare="$fh/origin.git"
  git init -q --bare -b "$default" "$bare"
  git clone -q "$bare" "$fh/proj" 2>/dev/null
  ( cd "$fh/proj"
    git -c user.name=t -c user.email=t@t commit -q --allow-empty -m seed
    git push -q origin "$default" 2>/dev/null
    git remote set-head origin "$default" >/dev/null 2>&1
    [ "$on" != "$default" ] && git checkout -q -b "$on"
  ) >/dev/null 2>&1
  mkdir -p "$fh/.claude"
  # The hook now needs a transcript that (a) bounds the session and (b) names the repo.
  # Timestamp is deliberately in the past so a fixture checkout counts as "inside" it.
  printf '{"timestamp":"2000-01-01T00:00:00.000Z","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"git -C %s/proj checkout -b x"}}]}}\n' "$fh" > "$fh/t.jsonl"
  echo "$fh"
}

echo "MUST REPORT:"
fh=$(mkfixture feature/x); run_case 2 "clone left on a feature branch" "$fh" \
  '{"session_id":"a1","transcript_path":"TRANSCRIPT"}'
fh=$(mkfixture wip master); run_case 2 "non-'main' default is respected" "$fh" \
  '{"session_id":"a2","transcript_path":"TRANSCRIPT"}'

echo "MUST STAY QUIET:"
fh=$(mkfixture main); run_case 0 "clone on its default branch" "$fh" \
  '{"session_id":"b1","transcript_path":"TRANSCRIPT"}'
fh=$(mkfixture master master); run_case 0 "on 'master' where that IS the default" "$fh" \
  '{"session_id":"b2","transcript_path":"TRANSCRIPT"}'
fh=$(mktemp -d); mkdir -p "$fh/.claude"; run_case 0 "no clones at all" "$fh" \
  '{"session_id":"b3","transcript_path":"TRANSCRIPT"}'
fh=$(mkfixture feature/x); run_case 0 "stop_hook_active -> never re-fires" "$fh" \
  '{"session_id":"b4","transcript_path":"TRANSCRIPT","stop_hook_active":true}'
fh=$(mkfixture feature/x); run_case 0 "empty payload -> silent, never crashes Stop" "$fh" ''

echo "MUST STAY QUIET — the two conditions that separate US from everyone else:"
# Without these the suite passes with both new conditions deleted, which is the whole point.
# 1. Someone ELSE'"'"'s tree: on a feature branch, moved now, but never named in our transcript.
fh=$(mkfixture feature/x)
printf '{"timestamp":"2000-01-01T00:00:00.000Z","message":{"content":[{"type":"text","text":"I mention %s/proj only in prose"}]}}\n' "$fh" > "$fh/t.jsonl"
run_case 0 "path named in PROSE only, never a command" "$fh" \
  '{"session_id":"d1","transcript_path":"TRANSCRIPT"}'
# 2. OUR repo, but HEAD last moved long before this session began.
fh=$(mkfixture feature/x)
printf '{"timestamp":"2099-01-01T00:00:00.000Z","message":{"content":[{"type":"tool_use","name":"Bash","input":{"command":"git -C %s/proj status"}}]}}\n' "$fh" > "$fh/t.jsonl"
run_case 0 "branch predates the session window" "$fh" \
  '{"session_id":"d2","transcript_path":"TRANSCRIPT"}'

echo "FIRES ONCE PER SESSION:"
fh=$(mkfixture feature/x)
run_case 2 "first call reports" "$fh" '{"session_id":"c1","transcript_path":"TRANSCRIPT"}'
run_case 0 "second call for the same session is quiet" "$fh" '{"session_id":"c1","transcript_path":"TRANSCRIPT"}'

echo "CONTROL:"
fh=$(mkfixture feature/x)
out=$(printf '%s' '{"session_id":"z","transcript_path":"TRANSCRIPT"}' | HOME="$fh" bash /nonexistent/h.sh 2>&1); rc=$?
if [ "$rc" -ne 2 ]; then printf '  PASS  (rc=%s) absent hook does not report 2\n' "$rc"; pass=$((pass+1))
else printf '  FAIL  control returned 2 from a nonexistent hook\n'; fail=$((fail+1)); fi

echo; echo "pass=$pass fail=$fail"; [ "$fail" -eq 0 ]
