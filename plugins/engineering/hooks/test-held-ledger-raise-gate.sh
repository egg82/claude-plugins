#!/usr/bin/env bash
# Suite for held-ledger-raise-gate.sh: throwaway repos with a bare origin, a fake transcript
# that names the repo in a tool input, and the hook run on each case. GATE=/path overrides.
set -uo pipefail
GATE=${GATE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/held-ledger-raise-gate.sh}
T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
export HELD_GATE_STAMP_DIR="$T/stamps"
pass=0; fail=0

mkrepo() {   # $1 name, $2 initial ledger JSON (or "" for none) -> path printed
    local r="$T/$1"
    git init -q --bare "$T/$1.git"
    git init -q -b main "$r"
    git -C "$r" remote add origin "$T/$1.git"
    mkdir -p "$r/tools/held"
    echo x > "$r/README"
    [ -n "$2" ] && printf '%s\n' "$2" > "$r/tools/held/function_size.json"
    git -C "$r" add -A && git -C "$r" -c user.email=t@t -c user.name=t commit -qm base
    git -C "$r" push -q origin main && git -C "$r" remote set-head origin main >/dev/null 2>&1
    echo "$r"
}

run() {   # $1 label, $2 expected rc, $3 repo, $4 session id
    local tr="$T/$4.jsonl"
    printf '%s\n' "{\"message\":{\"content\":[{\"type\":\"tool_use\",\"name\":\"Bash\",\"input\":{\"command\":\"cd $3 && python tests/x.py --write\"}}]}}" > "$tr"
    printf '{"session_id":"%s","transcript_path":"%s","cwd":"/"}' "$4" "$tr" | bash "$GATE" >/dev/null 2>"$T/err"
    local rc=$?
    if [ "$rc" -eq "$2" ]; then pass=$((pass+1)); echo "  PASS  $1"
    else fail=$((fail+1)); echo "  FAIL  $1 (rc=$rc, want $2): $(head -c 200 "$T/err")"; fi
}

base='{"a.py": {"f": 120, "g": 95}}'

r=$(mkrepo raise "$base");   echo '{"a.py": {"f": 130, "g": 95}}' > "$r/tools/held/function_size.json"
run "must-block: a held count went up (uncommitted)" 2 "$r" s1

r=$(mkrepo newkey "$base");  echo '{"a.py": {"f": 120, "g": 95}, "b.py": {"h": 90}}' > "$r/tools/held/function_size.json"
run "must-block: a new entry in an existing ledger" 2 "$r" s2

r=$(mkrepo committed "$base"); echo '{"a.py": {"f": 121, "g": 95}}' > "$r/tools/held/function_size.json"
git -C "$r" -c user.email=t@t -c user.name=t commit -qam raise
run "must-block: a raise already committed on the branch" 2 "$r" s3

r=$(mkrepo underscore ""); printf '%s\n' "$base" > "$r/tools/sql_held.json"
git -C "$r" add -A && git -C "$r" -c user.email=t@t -c user.name=t commit -qm b && git -C "$r" push -q origin main
echo '{"a.py": {"f": 121, "g": 95}}' > "$r/tools/sql_held.json"
run "must-block: the *_held.json naming is covered too" 2 "$r" s4

r=$(mkrepo lower "$base");   echo '{"a.py": {"f": 100}}' > "$r/tools/held/function_size.json"
run "must-allow: counts lowered and an entry removed" 0 "$r" s5

r=$(mkrepo seed "");         printf '%s\n' "$base" > "$r/tools/held/function_size.json"
run "must-allow: a ledger seeded for the first time" 0 "$r" s6

r=$(mkrepo same "$base")
run "must-allow: unchanged ledger" 0 "$r" s7

r=$(mkrepo untouched "$base"); echo '{"a.py": {"f": 999}}' > "$r/tools/held/function_size.json"
printf '{"session_id":"s8","transcript_path":"%s","cwd":"/"}' "$T/none.jsonl" | bash "$GATE" >/dev/null 2>&1
rc=$?; if [ "$rc" -eq 0 ]; then pass=$((pass+1)); echo "  PASS  must-allow: a raised repo this session never touched"
else fail=$((fail+1)); echo "  FAIL  must-allow: untouched repo (rc=$rc)"; fi

r=$(mkrepo once "$base");    echo '{"a.py": {"f": 130, "g": 95}}' > "$r/tools/held/function_size.json"
run "must-block: first stop with a raise" 2 "$r" s9
run "must-allow: the second stop in the same session (user approved)" 0 "$r" s9

# MOVES (v2). The base tree holds a.py and b.py; pkg/new.py appears only on the branch.
mkmoved() {   # $1 name -> repo whose base has a.py, b.py and a pyright ledger over both
    local r; r=$(mkrepo "$1" "")
    echo x > "$r/a.py"; echo x > "$r/b.py"
    printf '%s\n' '{"a.py": {"rule": 3}, "b.py": {"rule": 3}}' > "$r/tools/held/pyright.json"
    git -C "$r" add -A && git -C "$r" -c user.email=t@t -c user.name=t commit -qm files
    git -C "$r" push -q origin main
    mkdir -p "$r/pkg"; echo x > "$r/pkg/new.py"
    echo "$r"
}

r=$(mkmoved move)
echo '{"a.py": {"rule": 1}, "b.py": {"rule": 3}, "pkg/new.py": {"rule": 2}}' > "$r/tools/held/pyright.json"
run "must-allow: a split moves findings into a new file, kind total unchanged" 0 "$r" s11

r=$(mkmoved movefewer)
echo '{"b.py": {"rule": 3}, "pkg/new.py": {"rule": 1}}' > "$r/tools/held/pyright.json"
run "must-allow: a split moves findings and fixes some (total falls)" 0 "$r" s12

r=$(mkmoved movegrows)
echo '{"a.py": {"rule": 3}, "b.py": {"rule": 3}, "pkg/new.py": {"rule": 1}}' > "$r/tools/held/pyright.json"
run "must-block: a new file whose findings raise the kind's total" 2 "$r" s13

r=$(mkmoved paysfor)
echo '{"a.py": {"rule": 4}, "b.py": {"rule": 1}}' > "$r/tools/held/pyright.json"
run "must-block: an existing file raised while the total falls (fix pays for regression)" 2 "$r" s14

printf '{"session_id":"s10","stop_hook_active":true}' | bash "$GATE" >/dev/null 2>&1
rc=$?; if [ "$rc" -eq 0 ]; then pass=$((pass+1)); echo "  PASS  must-allow: stop_hook_active"
else fail=$((fail+1)); echo "  FAIL  stop_hook_active (rc=$rc)"; fi

echo; echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
