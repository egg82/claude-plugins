#!/usr/bin/env bash
# Must-fire AND must-stay-quiet cases for html-render-gate.sh. A Stop gate proven only to fire is
# indistinguishable from one that nags on everything, and that is the version people switch off.
set -uo pipefail
GATE="${GATE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/html-render-gate.sh}"
# GATE defaults to the copy beside this test. Pass GATE=<path> for a specific copy,
# and prove the path took effect (GATE=/nonexistent must change every result).
TD=$(mktemp -d); trap 'rm -rf "$TD"' EXIT
STAMPS="$HOME/.claude/.html-render-checked"
pass=0; fail=0

tu() { printf '{"message":{"content":[{"type":"tool_use","name":"%s","input":%s}]}}\n' "$1" "$2"; }

t() {  # $1=expected rc  $2=label  $3=transcript file  $4=session
  local exp="$1" label="$2" rc out
  rm -f "$STAMPS/$4"
  out=$(printf '{"session_id":"%s","transcript_path":"%s"}' "$4" "$3" | bash "$GATE" 2>&1); rc=$?
  if [ "$rc" -eq "$exp" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n        %s\n' "$rc" "$exp" "$label" "${out:0:130}"; fail=$((fail+1)); fi
}

echo "MUST FIRE — HTML written, nothing looked at:"
tu Write '{"file_path":"/home/x/report.html"}'                      > "$TD/a.jsonl"
t 2 "one html written, never viewed"            "$TD/a.jsonl" A
{ tu Write '{"file_path":"/home/x/dash.html"}'; tu Edit '{"file_path":"/home/x/dash.html"}'; } > "$TD/b.jsonl"
t 2 "written then edited, still never viewed"   "$TD/b.jsonl" B

echo "MUST STAY QUIET — it was looked at, or no human will look:"
{ tu Write '{"file_path":"/home/x/r.html"}'; tu Bash '{"command":"podman run ... firefox --screenshot /tmp/o.png r.html"}'; } > "$TD/c.jsonl"
t 0 "rendered with --screenshot"                "$TD/c.jsonl" C
{ tu Write '{"file_path":"/home/x/r.html"}'; tu Read '{"file_path":"/tmp/out.png"}'; } > "$TD/d.jsonl"
t 0 "the PNG was actually read"                 "$TD/d.jsonl" D
tu Write '{"file_path":"/home/x/tests/fixture.html"}'               > "$TD/e.jsonl"
t 0 "fixture under tests/ is excluded"          "$TD/e.jsonl" E
tu Write '{"file_path":"/home/x/__snapshots__/a.html"}'             > "$TD/f.jsonl"
t 0 "snapshot dir excluded"                     "$TD/f.jsonl" F
tu Write '{"file_path":"/tmp/scratchpad/probe.html"}'               > "$TD/g.jsonl"
t 0 "scratchpad excluded"                       "$TD/g.jsonl" G
tu Write '{"file_path":"/home/x/notes.md"}'                         > "$TD/h.jsonl"
t 0 "no HTML written at all"                    "$TD/h.jsonl" H
{ tu Write '{"file_path":"/home/x/r.html"}'; tu mcp__claude-in-chrome__navigate '{"url":"file:///home/x/r.html"}'; } > "$TD/i.jsonl"
t 0 "driven in a real browser instead"          "$TD/i.jsonl" I

# A text-only turn is the shape of a session that asked a question and got an answer. It has message
# blocks and no tool_use, and calling that inert put a red "Stop hook error" on every such session.
text() { printf '{"message":{"content":[{"type":"text","text":"%s"}]}}\n' "$1"; }
text "here is your answer"                                          > "$TD/m.jsonl"
t 0 "text-only session is CLEAN, not inert"     "$TD/m.jsonl" M
{ text "thinking out loud"; tu Write '{"file_path":"/home/x/r.html"}'; } > "$TD/n.jsonl"
t 2 "text plus an unviewed html still fires"    "$TD/n.jsonl" N

echo "INERT must be distinguishable from clean:"
printf '{"message":{"content":"not a list"}}\n' > "$TD/j.jsonl"
t 1 "content is not a list — reports inert"     "$TD/j.jsonl" J
: > "$TD/o.jsonl"
t 1 "empty transcript — reports inert"          "$TD/o.jsonl" O
t 0 "missing transcript fails open"             "/nope/none.jsonl" K

echo "MUST STAY QUIET — one nudge per session:"
rm -f "$STAMPS/L"
printf '{"session_id":"L","transcript_path":"%s"}' "$TD/a.jsonl" | bash "$GATE" >/dev/null 2>&1
out=$(printf '{"session_id":"L","transcript_path":"%s"}' "$TD/a.jsonl" | bash "$GATE" 2>&1); rc=$?
if [ "$rc" -eq 0 ]; then echo "  PASS  (rc=0) second stop does not re-fire"; pass=$((pass+1))
else echo "  FAIL  (rc=$rc want=0) second stop re-fired"; fail=$((fail+1)); fi

rm -f "$STAMPS"/A "$STAMPS"/B "$STAMPS"/L "$STAMPS"/N
echo
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
