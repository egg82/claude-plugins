#!/usr/bin/env bash
# Must-fire AND must-stay-quiet cases for route-lesson-gate.sh.
#
# The gate reads STRUCTURE from the transcript — a streak of failed Bash runs — never the
# assistant's prose. Fixtures mirror the real record shapes: assistant `tool_use` blocks with an
# `id`, and user `tool_result` blocks with `tool_use_id`, a string `content`, and `is_error` that is
# `true` on failure and false OR ABSENT on success. A hook block arrives as an is_error result whose
# content starts `PreToolUse:<Tool> hook error: [<hook command>]: ` (the harness's wrapper); it is
# deliberately not a signal.
set -uo pipefail
GATE="${GATE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/route-lesson-gate.sh}"
# GATE defaults to the copy beside this test. Pass GATE=<path> for a specific copy, and prove the path took
# effect (GATE=/nonexistent must change every result).
TD=$(mktemp -d); trap 'rm -rf "$TD"' EXIT
STAMPS="$HOME/.claude/.lesson-routed"
pass=0; fail=0

# One transcript per case, built from a tiny DSL so each fixture reads as the session it models:
#   say <text>                          assistant prose
#   call <id> <tool> <json-input>       assistant tool_use
#   ok <id> [content]                   tool_result, is_error absent (the common success shape)
#   okf <id>                            tool_result, is_error false
#   err <id> <content>                  tool_result, is_error true
mk() {  # $1=out file, stdin=DSL lines
  python3 -c '
import json, sys, shlex
out = open(sys.argv[1], "w")
for line in sys.stdin:
    line = line.rstrip("\n")
    if not line.strip():
        continue
    a = shlex.split(line)
    k = a[0]
    if k == "say":
        r = {"type": "assistant", "message": {"content": [{"type": "text", "text": a[1]}]}}
    elif k == "call":
        r = {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": a[1], "name": a[2], "input": json.loads(a[3])}]}}
    else:
        b = {"type": "tool_result", "tool_use_id": a[1],
             "content": a[2].replace("\\n", "\n") if len(a) > 2 else "ok"}
        if k == "okf":
            b["is_error"] = False
        elif k == "err":
            b["is_error"] = True
        r = {"type": "user", "message": {"content": [b]}}
    out.write(json.dumps(r) + "\n")
' "$1"
}

t() {  # $1=expected rc  $2=label  $3=transcript  $4=session  [$5=substring the message must carry]
  local exp="$1" label="$2" rc out
  rm -f "$STAMPS/$4"
  out=$(printf '{"session_id":"%s","transcript_path":"%s"}' "$4" "$3" | bash "$GATE" 2>&1); rc=$?
  rm -f "$STAMPS/$4"
  if [ "$rc" -eq "$exp" ] && { [ -z "${5:-}" ] || [[ "$out" == *"$5"* ]]; }; then
    printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s%s) %s\n        %s\n' "$rc" "$exp" "${5:+, message must name: $5}" "$label" "${out:0:200}"; fail=$((fail+1)); fi
}

# Real block content is multi-line; the DSL is one record per line, so `\n` is decoded by mk.
BLOCK="PreToolUse:Bash hook error: [bash '/home/x/.claude/hooks/bash-footgun-gate.sh']: Blocked by bash-footgun-gate — these fail SILENTLY, so the result would look fine:\n\n  - A mutating command (\`git push\`) is followed by another statement"
SKILL_W='{"file_path":"/home/x/.claude/skills/shell-footguns/SKILL.md","content":"x"}'
# The one signal, for the routing cases: three failed Bash calls in a row.
F2="call x1 Bash '{\"command\":\"a\"}'
err x1 \"Exit code 1\"
call x2 Bash '{\"command\":\"b\"}'
err x2 \"Exit code 1\"
call x3 Bash '{\"command\":\"c\"}'
err x3 \"Exit code 1\""

# A hook block is NOT a signal: the trap it caught is already gated, so the lesson is already
# captured. Replayed over 83 sessions, counting blocks made this gate nudge in 36 of them.
echo "MUST STAY QUIET — hook blocks, even several in a row:"
mk "$TD/hb.jsonl" <<EOF
call t1 Bash '{"command":"git push; git log -1"}'
err t1 "$BLOCK"
call t2 Bash '{"command":"git push; git log -2"}'
err t2 "$BLOCK"
call t3 Bash '{"command":"git push; git log -3"}'
err t3 "$BLOCK"
call t4 Bash '{"command":"git push && git log -1"}'
ok t4
EOF
t 0 "three bash-footgun-gate blocks, then the fixed command" "$TD/hb.jsonl" RA
mk "$TD/hb2.jsonl" <<EOF
call a1 Agent '{"prompt":"x"}'
err a1 "PreToolUse:Agent hook error: [bash '/home/x/.claude/hooks/spawn-model-gate.sh']: spawn refused: no model named"
EOF
t 0 "another gate's block" "$TD/hb2.jsonl" RA2

echo "MUST FIRE — an error streak:"
mk "$TD/s3.jsonl" <<'EOF'
call b1 Bash '{"command":"a"}'
err b1 "Exit code 1"
call b2 Bash '{"command":"b"}'
err b2 "Exit code 2"
call b3 Bash '{"command":"c"}'
err b3 "Exit code 1"
EOF
t 2 "three consecutive failing Bash calls" "$TD/s3.jsonl" RB "Bash"
mk "$TD/s3x.jsonl" <<'EOF'
call b1 Bash '{"command":"a"}'
err b1 "Exit code 1"
call r1 Read '{"file_path":"/w/a"}'
ok r1
call b2 Bash '{"command":"b"}'
err b2 "Exit code 1"
call e1 Edit '{"file_path":"/w/a","old_string":"x","new_string":"y"}'
err e1 "<tool_use_error>String to replace not found in file.</tool_use_error>"
call b3 Bash '{"command":"c"}'
err b3 "Exit code 1"
EOF
t 2 "other tools in between do not reset a Bash streak" "$TD/s3x.jsonl" RB2 "Bash"

# Dropped signals. A file streak counted harness preconditions ("File has not been read yet"), and a
# revert is what proving a check can fail looks like: break it, see it go red, restore it.
echo "MUST STAY QUIET — dropped signals:"
mk "$TD/f2.jsonl" <<'EOF'
call e1 Edit '{"file_path":"/w/app.py","old_string":"a","new_string":"b"}'
err e1 "<tool_use_error>File has not been read yet. Read it first before writing to it.</tool_use_error>"
call e2 Edit '{"file_path":"/w/app.py","old_string":"a ","new_string":"b"}'
err e2 "<tool_use_error>String to replace not found in file.</tool_use_error>"
call e3 Edit '{"file_path":"/w/app.py","old_string":"a  ","new_string":"b"}'
err e3 "<tool_use_error>String to replace not found in file.</tool_use_error>"
EOF
t 0 "three failed Edits on one file" "$TD/f2.jsonl" RC
mk "$TD/rv.jsonl" <<'EOF'
call r1 Edit '{"file_path":"/w/app.py","old_string":"x = 1","new_string":"x = 2"}'
ok r1
call r2 Bash '{"command":"pytest"}'
ok r2
call r3 Edit '{"file_path":"/w/app.py","old_string":"x = 2","new_string":"x = 1"}'
okf r3
EOF
t 0 "A->B then B->A: a deliberate break-and-restore" "$TD/rv.jsonl" RD

echo "MUST STAY QUIET — the lesson WAS routed after the signal:"
mk "$TD/hbr.jsonl" <<EOF
$F2
call w1 Edit '{"file_path":"/home/x/.claude/skills/shell-footguns/SKILL.md","old_string":"a","new_string":"b"}'
ok w1
EOF
t 0 "Bash streak, then a skill edit" "$TD/hbr.jsonl" RE
mk "$TD/s3r.jsonl" <<EOF
call b1 Bash '{"command":"a"}'
err b1 "Exit code 1"
call b2 Bash '{"command":"b"}'
err b2 "Exit code 2"
call b3 Bash '{"command":"c"}'
err b3 "Exit code 1"
call w1 Write '$SKILL_W'
ok w1
EOF
t 0 "streak, then a skill write" "$TD/s3r.jsonl" RE2
mk "$TD/dj.jsonl" <<EOF
$F2
call d1 Bash '{"command":"python3 log.py >> decisions.jsonl"}'
ok d1
EOF
t 0 "Bash streak, then a decisions.jsonl append" "$TD/dj.jsonl" RE3

echo "MUST FIRE — routed BEFORE the signal does not cover it:"
mk "$TD/rb.jsonl" <<EOF
call w1 Write '$SKILL_W'
ok w1
$F2
EOF
t 2 "skill write, then a later Bash streak" "$TD/rb.jsonl" RF

echo "MUST STAY QUIET — reading a skill is not routing, and is not a signal either:"
mk "$TD/rd.jsonl" <<'EOF'
call c1 Read '{"file_path":"/home/x/.claude/skills/shell-footguns/SKILL.md"}'
ok c1
EOF
t 0 "a read alone" "$TD/rd.jsonl" RG
mk "$TD/rdb.jsonl" <<EOF
$F2
call c1 Read '{"file_path":"/home/x/.claude/skills/shell-footguns/SKILL.md"}'
ok c1
call c2 Bash '{"command":"cat /home/x/.claude/memory/foo.md"}'
ok c2
EOF
t 2 "Bash streak, then only reads of skill/memory" "$TD/rdb.jsonl" RG2

echo "MUST STAY QUIET — ordinary sessions:"
mk "$TD/pr.jsonl" <<'EOF'
say "My probe was wrong, I was wrong earlier, I overwrote my own notes file, same shape as before."
call b1 Bash '{"command":"ls"}'
ok b1
EOF
t 0 "admission prose with no structural signal" "$TD/pr.jsonl" RH
mk "$TD/s2.jsonl" <<'EOF'
call b1 Bash '{"command":"grep x f"}'
err b1 "Exit code 1"
call b2 Bash '{"command":"grep y f"}'
err b2 "Exit code 1"
call b3 Bash '{"command":"ls"}'
ok b3
call b4 Bash '{"command":"grep z f"}'
err b4 "Exit code 1"
EOF
t 0 "errors broken by a success are not a streak" "$TD/s2.jsonl" RI
mk "$TD/mix.jsonl" <<'EOF'
call b1 Bash '{"command":"a"}'
err b1 "Exit code 1"
call r1 Read '{"file_path":"/w/a"}'
err r1 "File does not exist."
call b2 Bash '{"command":"b"}'
err b2 "Exit code 1"
EOF
t 0 "three errors across different tools and files" "$TD/mix.jsonl" RI2
mk "$TD/perm.jsonl" <<'EOF'
call b1 Bash '{"command":"a"}'
err b1 "Permission for this action was denied by the user."
call b2 Bash '{"command":"b"}'
err b2 "The user doesn't want to proceed with this tool use."
call b3 Bash '{"command":"c"}'
err b3 "Permission for this action was denied by the user."
EOF
t 0 "permission denials are not failures" "$TD/perm.jsonl" RI3
mk "$TD/pre.jsonl" <<'EOF'
call b1 Bash '{"command":"a"}'
err b1 "<tool_use_error>Blocked: sleep 30 followed by: ls</tool_use_error>"
call b2 Bash '{"command":"b"}'
err b2 "<tool_use_error>Blocked: sleep 30 followed by: ls</tool_use_error>"
call b3 Bash '{"command":"c"}'
err b3 "<tool_use_error>Blocked: sleep 30 followed by: ls</tool_use_error>"
EOF
t 0 "harness refusals on Bash are not failed runs" "$TD/pre.jsonl" RI4

echo "LOOP SAFETY and FAIL-OPEN:"
# Both use s3.jsonl, which DOES fire on its own (case RB), so a quiet result here means suppression.
out=$(printf '{"session_id":"RL","transcript_path":"%s","stop_hook_active":true}' "$TD/s3.jsonl" | bash "$GATE" 2>&1); rc=$?
rm -f "$STAMPS/RL"
if [ "$rc" -eq 0 ]; then echo "  PASS  (rc=0) stop_hook_active suppresses re-entry"; pass=$((pass+1))
else echo "  FAIL  (rc=$rc want=0) stop_hook_active did not suppress"; fail=$((fail+1)); fi

rm -f "$STAMPS/RM"
printf '{"session_id":"RM","transcript_path":"%s"}' "$TD/s3.jsonl" | bash "$GATE" >/dev/null 2>&1
out=$(printf '{"session_id":"RM","transcript_path":"%s"}' "$TD/s3.jsonl" | bash "$GATE" 2>&1); rc=$?
rm -f "$STAMPS/RM"
if [ "$rc" -eq 0 ]; then echo "  PASS  (rc=0) second stop does not re-fire"; pass=$((pass+1))
else echo "  FAIL  (rc=$rc want=0) second stop re-fired"; fail=$((fail+1)); fi

t 0 "missing transcript fails open"             "/nope/none.jsonl" RN
printf 'not json\n{"type":"user","message":{"content":"plain string"}}\n' > "$TD/junk.jsonl"
t 0 "malformed lines are skipped"               "$TD/junk.jsonl" RO
# Odd records must be SKIPPED, not abort the scan: a crash here exits quietly and hides the streak
# that follows. Each line below once raised AttributeError.
printf '%s\n' "$F2" | mk "$TD/f2tail.jsonl"
{
  printf '%s\n' '{"type":"user","message":"plain string"}' '["a list record"]' \
    '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"z1","name":"Bash","input":["a"]}]}}' \
    '{"type":"user","message":{"content":[{"type":"tool_result","tool_use_id":"z1","is_error":true,"content":"Exit code 1"}]}}' \
    '{"type":"assistant","message":{"content":[{"type":"tool_use","id":"z2","name":"Write","input":"not an object"}]}}'
  cat "$TD/f2tail.jsonl"
} > "$TD/odd.jsonl"
t 2 "odd records are skipped, the streak after them still fires" "$TD/odd.jsonl" RP "Bash"

echo
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
