#!/usr/bin/env bash
# Suite for glab-merge-gate.sh. A stub `glab` on PATH answers `mr view` with the pipeline status in
# $STUB_STATUS ("none" = no head_pipeline, "fail" = lookup error). GATE=<path> tests another copy;
# GATE=/nonexistent must fail every case.
GATE="${GATE:-$(dirname "$0")/glab-merge-gate.sh}"
stub=$(mktemp -d)
trap 'rm -rf "$stub"' EXIT
cat > "$stub/glab" <<'EOF'
#!/usr/bin/env bash
[ "$STUB_STATUS" = fail ] && { echo "404 Not Found" >&2; exit 1; }
if [ "$STUB_STATUS" = none ]; then echo '{"iid":7,"head_pipeline":null}'
else printf '{"iid":7,"head_pipeline":{"status":"%s"}}\n' "$STUB_STATUS"; fi
EOF
chmod +x "$stub/glab"
pass=0 fail=0
t() {
  local want=$1 status=$2 label=$3 cmd=$4 rc err
  # A crashing gate also exits 2, so a block counts only with the gate's own message.
  err=$(python3 -c 'import json,sys;print(json.dumps({"tool_name":"Bash","tool_input":{"command":sys.argv[1]},"cwd":"/tmp"}))' "$cmd" \
    | PATH="$stub:$PATH" STUB_STATUS="$status" bash "$GATE" 2>&1 >/dev/null)
  rc=$?
  if [ "$rc" = 2 ] && [[ "$err" != *"Blocked by glab-merge-gate"* ]]; then rc="2-crash"; fi
  if [ "$rc" = "$want" ]; then pass=$((pass+1)); echo "  PASS  (rc=$rc) $label"
  else fail=$((fail+1)); echo "  FAIL  (rc=$rc, want $want) $label"; fi
}
echo "MUST BLOCK:"
t 2 none    "no pipeline yet"                'glab mr merge 20 --repo group/project --yes'
t 2 pending "pending pipeline"               'glab mr merge 20 -R group/project --yes'
t 2 created "created pipeline, --auto-merge" 'glab mr merge 20 --auto-merge --yes'
t 2 failed  "failed pipeline"                'glab mr merge 20 --yes'
t 2 none    "after other commands"           'git push -q && glab mr merge 20 --yes | head -1'
t 2 none    "no MR id (current branch)"      'glab mr merge --yes'
t 2 running "MR id is a loop variable"       'for p in 1 2; do glab mr merge "$1" --sha "$s" -m "x [ci skip]" --yes; done'
t 2 running "MR id is a command substitution" 'glab mr merge $(glab mr list | head -1) --yes'
t 2 none    "merge as a loop body's first word" 'for n in 1; do glab mr merge 20 --yes; done'
t 2 none    "merge after then"               'if true; then glab mr merge 20 --yes; fi'
echo "MUST ALLOW:"
t 0 running "running pipeline (sets auto-merge)" 'glab mr merge 20 --repo group/project --yes'
t 0 success "green pipeline"                 'glab mr merge 20 --yes'
t 0 running "variables only in flag values"  'glab mr merge 54 --sha "$sha" -m "Merge $b [ci skip]" --yes'
t 0 none    "ungated escape for a repo with no CI" 'GLAB_MERGE_UNGATED=1 glab mr merge 20 --yes'
t 0 none    "not a merge"                    'glab mr view 20 -F json'
t 0 none    "merge named in an echo"         'echo then run glab mr list'
t 0 fail    "lookup fails: fail open"        'glab mr merge 20 --yes'
echo
echo "pass=$pass fail=$fail"
[ "$fail" = 0 ]
