#!/usr/bin/env bash
# SessionStart (matcher "compact"): re-inject pointers to on-disk handoff state into the FRESH context
# after compaction.
#
# WHY SessionStart and not PreCompact/PostCompact: PreCompact output lands in the context about to be
# summarized; PostCompact stdout never reaches the model at all (its output appeared in no transcript). SessionStart stdout is injected into the new window. Mid-session state otherwise
# survives only if the summary happens to carry it — the "prose doesn't bind" failure applied to my own
# working memory.
# Silent when there is nothing to point at, so it never becomes noise.
set -uo pipefail
payload=$(cat 2>/dev/null || true)
found=0
emit() { [ "$found" -eq 0 ] && echo "── handoff state on disk (read these before continuing) ──"; found=1; echo "  $1"; }

stale=0; hf=0
for f in "${HOME}"/.claude/HANDOFF-*.md; do
  [ -f "$f" ] || continue
  hf=1
  age=$(( ( $(date +%s) - $(date -r "$f" +%s 2>/dev/null || date +%s) ) / 86400 ))
  emit "$f — $(sed -n '1s/^# *//p' "$f")${age:+ (${age}d old)}"
  [ "$age" -gt 3 ] && stale=1
done

st="${HOME}/.claude/.precompact-state.md"
if [ -f "$st" ]; then
  emit "$st — auto-captured just before this compaction: uncommitted work, running agents, frozen snapshots"
fi

for ow in "${HOME}"/.claude/projects/*/memory/open-work.md; do
  [ -f "$ow" ] || continue
  n=$(grep -cE '^- \*\*' "$ow" 2>/dev/null) || n=0
  emit "$ow — $n tracked items"
done
if [ "$found" -eq 1 ]; then
  echo "  These are on disk and did not go through compaction. Re-read rather than reconstruct."
  # A handoff outlives its task silently, and the next session cannot tell a live next-action from a
  # finished one — so it acts on stale instructions with full confidence. DELETE it when its work
  # lands; that is the only signal that distinguishes "still in progress" from "nobody cleaned up".
  # Only advise on handoffs when one actually exists — advice that fires when it does not apply is
  # how a useful line turns into noise the reader learns to skip.
  if [ "$hf" -eq 1 ]; then
    echo "  DELETE a HANDOFF file once its next-actions are done — a stale one is followed as if current."
    [ "$stale" -eq 1 ] && echo "  One is >3d old: confirm its next-actions are still real before acting on them."
  fi
fi
# prompt-clock.sh's context nudge only runs on human prompts, so an autonomous run can cross its hard
# mark and compact without seeing it. If the context was past that mark before this compaction, say so
# here. Either way, reset prompt-clock's per-session tier so a session that regrows gets nudged again.
# Compactions also happen on idle (~55min), so a small session compacting is not a reason to wrap up.
HARD=450000  # keep in sync with TIERS[-1] in prompt-clock.sh
pre=$(PAYLOAD="$payload" python3 - <<'PY'
import json, os, pathlib
try:
    d = json.loads(os.environ.get("PAYLOAD") or "{}")
except ValueError:
    d = {}
sid = str(d.get("session_id") or "")
if sid and "/" not in sid:
    (pathlib.Path.home() / ".claude/state/prompt-clock" / (sid + ".ctx")).unlink(missing_ok=True)
pre = 0
try:
    for line in open(d.get("transcript_path") or "", encoding="utf-8", errors="ignore"):
        if '"compact_boundary"' in line:
            try:
                pre = int((json.loads(line).get("compactMetadata") or {}).get("preTokens") or 0)
            except ValueError:
                pass
except OSError:
    pass
print(pre)
PY
)
if [ "${pre:-0}" -ge "$HARD" ]; then
  echo "[context] This session compacted from ~$((pre / 1000))k tokens, past the hard context mark. Finish the"
  echo "  step in hand, write the open state to ~/.claude/HANDOFF-<topic>.md, and do not start new large work"
  echo "  here. If this harness can start a tracked session and work remains, start the fresh session yourself"
  echo "  in a new labelled tab, briefed with the handoff, and tell the operator its name."
fi
exit 0
