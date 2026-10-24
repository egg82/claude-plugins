#!/usr/bin/env bash
# hook-version: 8   # bump on any behaviour change
# SessionStart: surface config drift into context, because nobody reads a report.
#
# WHY: the monthly config-hygiene job writes to a scheduler log the operator never opens.
# A finding that never reaches the agent is a finding that does not exist. This runs the
# FAST checks only (no git log walks), caches for a day, and stays silent when clean —
# so it costs nothing on the common path and cannot become noise to ignore.
set -uo pipefail
CACHE="${HOME}/.claude/.hygiene-last"
SK="${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}/skills/config-hygiene"
H="$SK/hygiene.py"
if [ -n "${HYGIENE_PY:-}" ]; then
  # This runs python3 against the value once per session, so validate it rather than trusting it.
  # Anything settable by .envrc, a shared profile, a container -e flag or a CI runner reaches here.
  _h=$(realpath -e "$HYGIENE_PY" 2>/dev/null) || { echo "── config hygiene ── HYGIENE_PY does not resolve; drift is UNCHECKED, not clean"; exit 0; }
  case "$_h" in
    "${HOME}/.claude/"*) ;;
    *) echo "── config hygiene ── HYGIENE_PY points outside ~/.claude — refusing to execute it"; exit 0 ;;
  esac
  [ -O "$_h" ] || { echo "── config hygiene ── HYGIENE_PY target is not owned by you — refusing"; exit 0; }
  if [ -n "$(find "$_h" -maxdepth 0 -perm /022 2>/dev/null)" ]; then
    echo "── config hygiene ── HYGIENE_PY target is group/world-writable — refusing"; exit 0
  fi
  H="$_h"
fi

# once per day
if [ -f "$CACHE" ]; then
  last=$(date -r "$CACHE" +%s 2>/dev/null || stat -c %Y "$CACHE" 2>/dev/null || echo "")
  # An unreadable mtime must not silently disable the limiter (nor silently enable it) — say so once.
  if [ -z "$last" ]; then
    echo "── config hygiene ── cannot read the cache timestamp; running the checks anyway"
  elif [ $(( $(date +%s) - last )) -lt 86400 ]; then
    exit 0
  fi
fi

if [ ! -f "$H" ]; then
  echo "── config hygiene ── scanner not found at $H"
  echo "  drift is UNCHECKED, not clean. Enable the config-care plugin, or set HYGIENE_PY."
  touch "$CACHE"   # a missing scanner is a standing config gap, not a transient crash — say it daily
  exit 0
fi

# Exit codes captured per-invocation: the filter below exits 1 on no-match, so pipeline status
# cannot distinguish "clean" from "crashed".
mem_out=$(python3 "$H" memory  2>&1); mem_rc=$?
ref_out=$(python3 "$H" refs    2>&1); ref_rc=$?
# `imports` carries the always-on GROWTH RATCHET and `testiso` the test-suites-must-not-mutate-live-
# state check. Both are escalations of lessons that were already written down and got hit anyway, so
# both are worthless unless something actually runs them — which is this. Both are silent when clean
# and cheap (a line scan over ~20 prefs and ~5 suites), so neither turns the hook into wallpaper.
imp_out=$(python3 "$H" imports 2>&1); imp_rc=$?
iso_out=$(python3 "$H" testiso 2>&1); iso_rc=$?
out=$(printf '%s\n%s\n%s\n%s\n' "$mem_out" "$ref_out" "$imp_out" "$iso_out" \
      | grep -vE '^==|^  clean$|^  clean —|^  \(user/feedback|carry a probe|^  always-on: ' \
      | awk '!seen[$0]++' )
# The `awk '!seen[$0]++'` dedupe is load-bearing, not tidiness: `imports` is ALSO run as part of
# `memory`, so the always-on growth line arrives twice and printed the identical sentence twice on
# the first session after this hook went to v6. A report that repeats itself is a report people stop
# reading, which is the same cry-wolf failure as a check that fires on everything.
# `^  always-on: ` is hygiene.py's unconditional inventory line ("N imports, NB loaded every
# session"). It is not a finding, and left unfiltered it prints on EVERY session, which turns a
# hook whose whole value is silence-when-clean into wallpaper. Note the anchor keeps the trailing
# colon-space so it does NOT swallow the `always-on prefs:` line, which IS a finding.
# hygiene.py: 0 = clean, 1 = findings, anything else = it broke. Only stamp the once-a-day cache on a
# run that actually completed, or a crash buys 24h of silence.
if [ "$mem_rc" -le 1 ] && [ "$ref_rc" -le 1 ] && [ "$imp_rc" -le 1 ] && [ "$iso_rc" -le 1 ]; then
  touch "$CACHE"
else
  echo "── config hygiene ── the scanner exited $mem_rc/$ref_rc/$imp_rc/$iso_rc — drift is UNCHECKED, not clean."
  echo "  Not caching this run, so the next session retries rather than skipping."
fi

# open-work items are the other thing that silently rots
n_open=0
for ow in "${HOME}"/.claude/projects/*/memory/open-work.md; do
  [ -f "$ow" ] || continue
  c=$(grep -cE '^- \*\*' "$ow" 2>/dev/null) || c=0
  n_open=$(( n_open + c ))
done

# Scheduled-run report: the monthly job writes here. This is built BEFORE the early exit below,
# because the sweep runs checks this hook does not — failing `check:` probes, skill staleness, doc
# age, doc content. Computing it after the exit meant a tidy live store threw away every one of
# them, and a swallowed finding is indistinguishable from no finding.
REPORT="${HOME}/.claude/.hygiene-report"
sched=""
# No report at all means no scheduler was ever set up. That is the default state of a fresh install,
# so it stays silent; a report that exists but has gone stale is reported below.
if [ -f "$REPORT" ]; then
  rts=$(date -r "$REPORT" +%s 2>/dev/null || echo 0)
  [ "$rts" -eq 0 ] && rts=$(date +%s)
  age=$(( ( $(date +%s) - rts ) / 86400 ))
  if [ "$age" -gt 45 ]; then
    sched="  scheduled hygiene report is ${age}d old — the monthly job may have stopped running"
  elif ! grep -qx 'clean' "$REPORT" 2>/dev/null; then
    sched="  from the last scheduled sweep:
$(sed 's/^/    /' "$REPORT" | head -8)"
  fi
fi

skew=""
# Hook version skew. A copy of this hook in ~/.claude/hooks is not refreshed by `/plugin update`, and
# Claude Code runs both. Only checked when such a copy exists; compare it with the plugin's own.
_local="${HOME}/.claude/hooks/hygiene-sessionstart.sh"
_mine=""
[ -f "$_local" ] && _mine=$(sed -n 's/^# hook-version:[[:space:]]*\([0-9]\+\).*/\1/p' "$_local" | head -1)
# Real layouts: an installed copy at cache/<marketplace>/<plugin>/<version>/hooks/, a marketplace
# checkout at marketplaces/<marketplace>/plugins/<plugin>/hooks/. (The previous two- and three-level
# globs matched neither, so this check was silently inert.)
[ -n "$_mine" ] && for _pl in "${HOME}"/.claude/plugins/cache/*/*/*/hooks/hygiene-sessionstart.sh \
           "${HOME}"/.claude/plugins/marketplaces/*/plugins/*/hooks/hygiene-sessionstart.sh; do
  [ -f "$_pl" ] || continue
  _theirs=$(sed -n 's/^# hook-version:[[:space:]]*\([0-9]\+\).*/\1/p' "$_pl" | head -1)
  if [ -n "$_mine" ] && [ -n "$_theirs" ] && [ "$_mine" != "$_theirs" ]; then
    skew="  a copy in ~/.claude/hooks (v$_mine) shadows the plugin's hook (v$_theirs): the copy keeps running
  and does not receive plugin updates. Delete it, or re-copy from the plugin."
  fi
  break
done

# Traps that keep biting across sessions — the documented-and-hit-anyway class especially.
# Weekly, because it reads every recent transcript; a daily nudge here would become wallpaper.
TRAPCACHE="${HOME}/.claude/.repeat-traps-last"
traps=""
_run_traps=1
if [ -f "$TRAPCACHE" ]; then
  _t=$(date -r "$TRAPCACHE" +%s 2>/dev/null || stat -c %Y "$TRAPCACHE" 2>/dev/null || echo "")
  [ -n "$_t" ] && [ $(( $(date +%s) - _t )) -lt 604800 ] && _run_traps=0
fi
if [ "$_run_traps" = 1 ]; then
  _tm="$SK/mine-repeat-traps.py"
  [ -f "$_tm" ] && traps=$(timeout 120 python3 "$_tm" --days 14 --quiet 2>/dev/null)
  touch "$TRAPCACHE"
fi

# The miner's pattern list has silently lost alternatives twice: patterns are matched against
# lowercased text, so a capital letter in a literal makes that alternative unmatchable. Nothing
# errors and the miner's output still looks healthy, so the only tell is a label that reports zero
# forever. Its --self-test proves each label can fire; run it here so an edit that kills a signature
# surfaces at the next session rather than never. Silent on pass -- reports only on failure.
# Probe for the flag before trusting its exit status: a miner predating --self-test makes argparse
# exit 2 and print usage to stderr, which 2>&1 captures — so this block would report "a trap
# signature is dead" every session on the strength of a missing flag. Absent flag => silence.
# Deliberately NOT `|| true`: a miner that HAS the flag and fails it must still be reported.
_tm="$SK/mine-repeat-traps.py"
if [ -f "$_tm" ] && [ "$(timeout 10 python3 "$_tm" --help 2>/dev/null | grep -c -- '--self-test')" -gt 0 ]; then
  if ! _st=$(timeout 20 python3 "$_tm" --self-test 2>&1); then
    minerbad="  mine-repeat-traps.py --self-test FAILED — a trap signature is dead, not clean:
$(printf '%s\n' "$_st" | sed 's/^/    /')"
  fi
fi

[ -z "$out" ] && [ "$n_open" -eq 0 ] && [ -z "$sched" ] && [ -z "$traps" ] && [ -z "$skew" ] && [ -z "${minerbad:-}" ] && exit 0

echo "── config hygiene ──"
[ -n "$out" ] && echo "$out"
[ "$n_open" -gt 0 ] && echo "  open-work.md holds $n_open tracked item(s) — check before starting related work"
[ -n "$sched" ] && echo "$sched"
[ -n "$traps" ] && echo "$traps"
[ -n "$skew" ] && echo "$skew"
[ -n "${minerbad:-}" ] && echo "$minerbad"

# One-time offer: a store with drift but not a single `check:` anywhere was written before these
# hooks existed, so the gate and the scanner are only holding the line. Point at the backlog pass
# once, then never again.
FIRSTRUN="${HOME}/.claude/.hygiene-reorg-offered"
have_mem=0
for _m in "${HOME}"/.claude/projects/*/memory/*.md; do [ -f "$_m" ] && { have_mem=1; break; }; done
if [ ! -f "$FIRSTRUN" ] && [ -n "$out" ] && [ "$have_mem" = 1 ]; then
  if ! grep -rlq '^[[:space:]]*check:' "${HOME}"/.claude/projects/*/memory/*.md 2>/dev/null; then
    echo "  none of your memories carry a check: probe yet, and the store already shows drift — it was"
    echo "  written before these hooks were installed. The config-hygiene skill has a"
    echo "  one-off backlog pass (\"First run\"); worth doing once."
    touch "$FIRSTRUN"
  fi
fi
echo "  full sweep: python3 $H all <your repo dirs>"
exit 0
