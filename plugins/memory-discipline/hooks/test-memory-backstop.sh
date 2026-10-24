#!/usr/bin/env bash
# Regression suite for memory-bash-write-backstop.sh.
#
# Runs against a FIXTURE HOME, not yours: the hook resolves its trees from `~`, so overriding HOME
# gives it a throwaway tree and this suite can never report on your real memories. Prove the
# override took effect with the control below — HOOK=/nonexistent must fail every case.
set -uo pipefail
HOOK="${HOOK:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/memory-bash-write-backstop.sh}"
pass=0; fail=0

run_case () {
  exp="$1"; label="$2"; fixture_home="$3"; payload="$4"
  out=$(printf '%s' "$payload" | HOME="$fixture_home" bash "$HOOK" 2>&1); rc=$?
  if [ "$rc" -eq "$exp" ]; then
    printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else
    printf '  FAIL  (rc=%s want=%s) %s\n        %s\n' "$rc" "$exp" "$label" "${out:0:140}"; fail=$((fail+1))
  fi
}

# Builds a fixture: a HOME with a memory tree, a transcript recording `write_via_tool`, and both
# files touched AFTER the transcript's first timestamp.
mkfixture () {
  fh=$(mktemp -d); mkdir -p "$fh/.claude/memory" "$fh/.claude/skills/demo"
  t0="2020-01-01T00:00:00.000Z"
  tr="$fh/transcript.jsonl"
  python3 - "$tr" "$fh" "$t0" "$1" <<'PY'
import json, sys
tr, fh, t0, tool_path = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
recs = [{"timestamp": t0, "message": {"content": [{"type": "text", "text": "start"}]}}]
if tool_path:
    recs.append({"timestamp": t0, "message": {"content": [
        {"type": "tool_use", "name": "Edit", "input": {"file_path": fh + tool_path}}]}})
open(tr, "w").write("\n".join(json.dumps(r) for r in recs) + "\n")
PY
  echo "$fh"
}

echo "MUST REPORT — a file changed with no Write/Edit to explain it:"
fh=$(mkfixture "")                       # transcript records no tool write at all
echo body > "$fh/.claude/memory/written-by-bash.md"
run_case 2 "bash-written memory, nothing in transcript" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s1"}' "$fh")"

fh=$(mkfixture "/.claude/memory/via-tool.md")
echo body > "$fh/.claude/memory/via-tool.md"        # explained
echo body > "$fh/.claude/memory/sneaked-in.md"      # NOT explained
run_case 2 "one explained, one not -> still reports" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s2"}' "$fh")"

fh=$(mkfixture "")
echo body > "$fh/.claude/skills/demo/SKILL.md"
run_case 2 "a skill file counts too" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s3"}' "$fh")"

echo "MUST STAY QUIET:"
fh=$(mkfixture "/.claude/memory/via-tool.md")
echo body > "$fh/.claude/memory/via-tool.md"
run_case 0 "the only change WAS a Write/Edit" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s4"}' "$fh")"

fh=$(mkfixture "")                       # nothing touched at all
run_case 0 "clean session, nothing changed" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s5"}' "$fh")"

fh=$(mkfixture "")
echo "- [x](x.md) — hook" >> "$fh/.claude/memory/MEMORY.md"
run_case 0 "MEMORY.md index append is exempt" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s6"}' "$fh")"

fh=$(mkfixture "")
mkdir -p "$fh/.claude/skills/synced/bucket/docs"
echo body > "$fh/.claude/skills/synced/bucket/docs/SKILL.md"
run_case 0 "claude.ai skills/synced/ refresh is exempt" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s6b"}' "$fh")"

fh=$(mkfixture "")
echo body > "$fh/.claude/memory/written-by-bash.md"
run_case 0 "stop_hook_active -> never re-fires (loop safety)" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s7","stop_hook_active":true}' "$fh")"

fh=$(mkfixture "")
echo body > "$fh/.claude/memory/written-by-bash.md"
run_case 0 "missing transcript -> silent, never crashes Stop" "$fh" \
  '{"transcript_path":"/nonexistent/x.jsonl","session_id":"s8"}'

# Adds a subagent transcript beside the parent, at the layout the hook derives:
#   <transcript>.jsonl  ->  <transcript>/subagents/agent-<id>.jsonl
# The path is asserted here rather than trusted in the hook, because a wrong glob returns the same
# empty list as "this session spawned nothing" — so a broken derivation would look exactly like the
# normal case and every must-stay-quiet result below would be a false pass.
mkchild () {
  fh="$1"; child_path="$2"; ts="${3:-2020-01-01T00:00:00.000Z}"
  d="$fh/transcript/subagents"; mkdir -p "$d"
  python3 - "$d/agent-abc123.jsonl" "$fh" "$child_path" "$ts" <<'PY'
import json, sys
out, fh, p, ts = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
recs = [{"timestamp": ts, "message": {"content": [
    {"type": "tool_use", "name": "Write", "input": {"file_path": fh + p}}]}}]
open(out, "w").write("\n".join(json.dumps(r) for r in recs) + "\n")
PY
  test -f "$d/agent-abc123.jsonl" || { echo "  FIXTURE BROKEN: no child transcript written"; exit 9; }
}

echo "SUBAGENT WRITES — a delegated Edit is a sanctioned write, not an unexplained one:"
fh=$(mkfixture "")                                  # parent records NO tool write
mkchild "$fh" "/.claude/memory/by-child.md"         # the child does
echo body > "$fh/.claude/memory/by-child.md"
run_case 0 "a file written by a SUBAGENT is explained" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s10"}' "$fh")"

fh=$(mkfixture "")
mkchild "$fh" "/.claude/memory/by-child.md"
echo body > "$fh/.claude/memory/by-child.md"        # explained by the child
echo body > "$fh/.claude/memory/by-bash.md"         # explained by nothing
run_case 2 "a real Bash write still reports when a child ran too" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s11"}' "$fh")"

# The floor must stay the PARENT's first timestamp. If a child's later timestamp raised it, a file
# changed before the first spawn would fall below the floor and be skipped — the fix going blind in
# the window it was meant to leave alone.
fh=$(mkfixture "")
mkchild "$fh" "/.claude/memory/by-child.md" "2020-06-01T00:00:00.000Z"
echo body > "$fh/.claude/memory/by-bash.md"
run_case 2 "a child's later timestamp does not raise the session floor" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s12"}' "$fh")"

# A malformed child must not take the whole hook down: Stop must stay usable.
fh=$(mkfixture "")
mkdir -p "$fh/transcript/subagents"; printf 'not json at all\n' > "$fh/transcript/subagents/agent-bad.jsonl"
echo body > "$fh/.claude/memory/by-bash.md"
run_case 2 "an unparseable child transcript does not break the report" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s13"}' "$fh")"

# The skills/synced exemption is for the top-level synced dir only; a dir of that name inside a
# user's own skill is an ordinary Bash write and must still report.
fh=$(mkfixture "")
mkdir -p "$fh/.claude/skills/demo/synced"
echo body > "$fh/.claude/skills/demo/synced/notes.md"
run_case 2 "a dir named synced inside a user skill still reports" "$fh" \
  "$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s15"}' "$fh")"

echo "CONTROL — a nonexistent hook must fail the must-report cases:"
fh=$(mkfixture "")
echo body > "$fh/.claude/memory/written-by-bash.md"
out=$(printf '{"transcript_path":"%s/transcript.jsonl","session_id":"s9"}' "$fh" \
      | HOME="$fh" bash /nonexistent/hook.sh 2>&1); rc=$?
if [ "$rc" -ne 2 ]; then printf '  PASS  (rc=%s) control: absent hook does not report 2\n' "$rc"; pass=$((pass+1))
else printf '  FAIL  control returned 2 from a nonexistent hook\n'; fail=$((fail+1)); fi

echo
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
