#!/usr/bin/env bash
# Writes ~/.claude/.hygiene-report — the file hygiene-sessionstart.sh surfaces at session start.
#
# Run it from cron or a systemd timer (see systemd/) so probes and drift checks are re-run rather
# than written and forgotten. The CONTRACT IS THE FILE, not the scheduler: anything that writes
# .hygiene-report in this shape satisfies the session-start hook. The hook reports a report older
# than 45 days as a finding, so a scheduler that silently dies surfaces itself instead of reading as clean.
#
# Repos for the docs checks: pass git checkout paths as arguments, or set HYGIENE_REPOS to a
# whitespace-separated list. With none, the docs checks are reported as NOT run, never as clean.
set -uo pipefail
H="${HYGIENE_PY:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/hygiene.py}"
REPORT="${HOME}/.claude/.hygiene-report"
TMP="$(mktemp)"; trap 'rm -f "$TMP"' EXIT

if [ ! -f "$H" ]; then
  printf 'scanner missing at %s — drift is UNCHECKED, not clean\n' "$H" > "$REPORT"; exit 0
fi

REPOS=()
# An empty list scans NOTHING and must not read as clean; that case is reported below.
for r in "$@" ${HYGIENE_REPOS:-}; do
  [ -d "$r/.git" ] && REPOS+=("$r")
done

# probes execute shell from memory frontmatter; hygiene.py additionally skips any file not owned
# by the invoking user. Safe while every memory is yours — revisit if memory files ever become
# shared or writable by others (a distributed seed pack carrying `check:` is exactly that case).
: "${HYGIENE_RUN_PROBES:=0}"
export HYGIENE_RUN_PROBES

{ python3 "$H" memory
  python3 "$H" refs
  python3 "$H" skills
  python3 "$H" probes
  [ ${#REPOS[@]} -gt 0 ] && python3 "$H" docs "${REPOS[@]}"
  [ ${#REPOS[@]} -gt 0 ] && python3 "$H" doccontent "${REPOS[@]}"
} 2>&1 \
  | grep -vE '^==|^  clean$|^  \(user/feedback|carry a probe|^  SKIPPED — probes execute|^  Set HYGIENE_RUN_PROBES' \
  | sed '/^[[:space:]]*$/d' > "$TMP"

# Probes not opted in? That is a finding, not silence — the sweep's whole point includes them, and a
# report that omits "probes did not run" is indistinguishable from one where they all passed.
if [ "$HYGIENE_RUN_PROBES" != 1 ]; then
  echo "probes did NOT run — set HYGIENE_RUN_PROBES=1 in the scheduler environment (UNCHECKED, not clean)" >> "$TMP"
fi

if [ ${#REPOS[@]} -eq 0 ]; then
  echo "docs/doccontent did NOT run — no git repos given (pass paths or set HYGIENE_REPOS; UNCHECKED, not clean)" >> "$TMP"
fi

if [ -s "$TMP" ]; then cp "$TMP" "$REPORT"; else printf 'clean\n' > "$REPORT"; fi
exit 0
