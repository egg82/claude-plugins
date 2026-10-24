#!/usr/bin/env bash
# PreCompact: persist machine-observable working state to DISK before the context window is summarized.
#
# WHY PreCompact for this and SessionStart(compact) for the pointer: this hook's value is a side-effect
# (a file), not its stdout — so it does not matter that its output would itself be compacted. The
# companion postcompact-handoff.sh points at what this wrote, in the fresh window.
#
# LIMIT, stated so nobody trusts it too far: a shell hook can only capture what is observable on disk.
# It cannot capture intent, a decision, or why something was left half-done. Those still need a written
# handoff. This exists so the *silent* losses — uncommitted work, a running agent, a snapshot hash — do
# not have to be remembered.
set -uo pipefail
# PreCompact delivers JSON on stdin; session_id is the only reliable way to identify OUR task dir.
_payload=$(cat 2>/dev/null || true)
SID=$(printf '%s' "$_payload" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("session_id") or "")
except Exception: print("")' 2>/dev/null)
mkdir -p "${HOME}/.claude" 2>/dev/null || true
OUT="${HOME}/.claude/.precompact-state.md"
{
  echo "# Pre-compaction state snapshot"
  echo
  echo "Written automatically at $(date -Iseconds) by \`precompact-snapshot.sh\`."
  echo "Machine-observable only — it does not know *why* any of this is mid-flight. Pair it with any"
  echo "\`~/.claude/HANDOFF-*.md\`, which carries the intent."
  echo

  echo "## Repositories with uncommitted or unpushed work"
  echo
  found=0
  for d in "${HOME}"/*/ ; do
    [ -d "${d}.git" ] || continue
    name=$(basename "$d")
    dirty=$(git -C "$d" status --porcelain 2>/dev/null | wc -l)
    sb=$(git -C "$d" status -sb 2>/dev/null | head -1)
    ahead=$(printf '%s' "$sb" | grep -oE 'ahead [0-9]+' || true)
    if [ "$dirty" -gt 0 ] || [ -n "$ahead" ]; then
      found=1
      printf -- '- **%s** — %s uncommitted path(s)%s\n' "$name" "$dirty" "${ahead:+, $ahead}"
      printf -- '  - branch: `%s`\n' "$sb"
      git -C "$d" status --porcelain 2>/dev/null | head -8 | sed 's/^/    - `/; s/$/`/'
      [ "$dirty" -gt 8 ] && echo "    - …and $((dirty - 8)) more"
    fi
  done
  if [ "$found" -eq 0 ]; then
    echo "None among the top-level directories of \$HOME. Repos nested deeper (e.g. ~/src/foo) are"
    echo "NOT scanned — treat those as unchecked rather than clean."
  fi
  echo

  echo "## Background agents from this session"
  echo
  # Prefer the dir belonging to THIS session; `ls -d` sorts alphabetically, so the old
  # "most recent match" comment was false and it reliably picked a different session's tasks.
  td=""
  if [ -n "${SID:-}" ]; then
    for _c in /tmp/claude-*/*/"$SID"/tasks; do [ -d "$_c" ] && { td="$_c"; break; }; done
  fi
  [ -n "$td" ] || td=$(ls -dt /tmp/claude-*/*/*/tasks 2>/dev/null | head -1)
  if [ -n "${td:-}" ]; then
    n=$(ls "$td"/*.output 2>/dev/null | wc -l)
    case "$td" in
      */"${SID:-__nosid__}"/tasks)
        echo "Task transcripts: \`$td\` ($n) — matched to THIS session by session_id." ;;
      *)
        echo "Task transcripts: \`$td\` ($n) — newest under /tmp, NOT session-matched; it may belong"
        echo "to another session, so check the agent ids before trusting it." ;;
    esac
    echo "Resume one with SendMessage using the agent id in the filename; they keep their context."
    echo "**Do not read those .output files directly — they are full JSONL transcripts and will flood context.**"
  else
    echo "No task directory found for this session."
  fi
  echo

  echo "## Frozen snapshots (a review in progress reads these, so do not edit the live tree)"
  echo
  s=0
  for snap in /tmp/claude-*/*/*/scratchpad/*freeze*; do
    [ -d "$snap" ] || continue
    s=1
    printf -- '- `%s` — %s files, hash `%s`\n' "$snap" "$(find "$snap" -type f | wc -l)" \
      "$(cd "$snap" && find . -type f -exec sha256sum {} + 2>/dev/null | sort | sha256sum | cut -c1-16)"
  done
  [ "$s" -eq 0 ] && echo "None."
  echo

  echo "## Tracked work"
  echo
  for ow in "${HOME}"/.claude/projects/*/memory/open-work.md; do
    [ -f "$ow" ] || continue
    n=$(grep -cE '^- \*\*' "$ow" 2>/dev/null) || n=0
    printf -- '- `%s` — %s items\n' "$ow" "$n"
  done
  for h in "${HOME}"/.claude/HANDOFF-*.md; do
    [ -f "$h" ] || continue
    printf -- '- `%s` — %s\n' "$h" "$(sed -n '1s/^# *//p' "$h")"
  done
} > "$OUT" 2>/dev/null

# Only tell the summarizer the state file exists if it actually got written.
if [ ! -s "$OUT" ]; then
  echo "PreCompact could not write $OUT — machine-observable state was NOT captured. Carry what"
  echo "matters into the summary yourself: in-progress work, the next action, and what was ruled out."
  exit 0
fi

# --- The part a script cannot do, and cannot make happen either. ---
#
# PreCompact accepts exit 2, and it does block — but the harness immediately re-runs the hook and
# proceeds, so blocking buys no model turn. Observed directly: the interlock marker below was created
# by the first invocation and removed by the second, with no turn in between. So do NOT block here;
# it would only risk a stall at the moment context is already exhausted, for nothing.
#
# What is left is stdout, which lands in the context the summarizer reads. Bias it toward keeping
# intent, which is the part summaries lose first.
cat <<'MSG'
Preserve in the summary, above any narrative recap: what is in progress and the NEXT concrete action;
decisions already made and why; what was ruled out and why; anything waiting on a person; and anything
promised to the user but not yet done. Machine-observable state is already on disk in
~/.claude/.precompact-state.md and does not need restating.
MSG
exit 0
