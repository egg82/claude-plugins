#!/usr/bin/env bash
# Regression suite for freshness-gate.py (source-hash freshness).
#
# The gate decides staleness from one fact: the sha256 of the source file recorded in the bundle's
# MANIFEST.json when it was staged, against the source's sha256 now. Equal is fresh, different is
# stale, no record is unknown. Scrubbing rewrites the staged copy and must not matter.
#
# The previous gate compared the first words of headings and bold lead-ins. It refused a correctly
# scrubbed copy whose lead-in had been reworded, and it passed a stale copy whenever the source's edit
# left every heading alone. Case group NO-CRY-WOLF and BODY-EDIT are those two.
#
# Every case asserts an exit STATUS. Cases run against a FAKE claude-root under $T, never ~/.claude.
#
# Usage: bash test-freshness-gate.sh        (honours GATE= to test a copy elsewhere)
set -uo pipefail
GATE="${GATE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/freshness-gate.py}"
[ -f "$GATE" ] || { echo "NO GATE at $GATE — nothing was tested (UNCHECKED, not passing)"; exit 1; }

T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0
ROOT="$T/claude-root"

g() { python3 "$GATE" "$@" --claude-root "$ROOT"; }

t() { # t <expected-rc> <label> <bundle-dir>
  local exp="$1" label="$2" dir="$3" rc out
  out=$(g "$dir" 2>&1); rc=$?
  if [ "$rc" -eq "$exp" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else
    printf '  FAIL  (rc=%s want=%s) %s\n' "$rc" "$exp" "$label"; fail=$((fail+1))
    printf '%s\n' "$out" | sed 's/^/          | /'
  fi
}

ok() { # ok <label> <command...>  — a setup step that must itself succeed
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then printf '  PASS  %s\n' "$label"; pass=$((pass+1))
  else printf '  FAIL  %s\n' "$label"; fail=$((fail+1)); fi
}

# --- the installed tree ----------------------------------------------------
mkdir -p "$ROOT/hooks" "$ROOT/skills/demo/__pycache__" "$ROOT/memory" "$ROOT/projects/proj-secretname/memory"
printf '# Demo\n## First section\nbody on host-alpha\n' > "$ROOT/skills/demo/SKILL.md"
printf 'def f():\n    pass\n' > "$ROOT/skills/demo/tool.py"
printf 'junk' > "$ROOT/skills/demo/__pycache__/tool.cpython-311.pyc"
printf '**A stated position can be argued with.** Lead with the verdict.\n' > "$ROOT/memory/pref-one.md"
printf '**Capture while it is live.**\n' > "$ROOT/projects/proj-secretname/memory/pref-two.md"
printf 'main() {\n  :\n}\n' > "$ROOT/hooks/demo-gate.sh"

# --- bundles ---------------------------------------------------------------
B="$T/b"; mkdir -p "$B"
echo "STAGE / RECORD:"
ok "stage copies a skill dir and records every file"  g stage "$B" "$ROOT/skills/demo" skills/demo
ok "stage re-tiers a memory under memory/<tier>/"      g stage "$B" "$ROOT/memory/pref-one.md" memory/prefs/pref-one.md
ok "stage a project-scoped memory"                    g stage "$B" "$ROOT/projects/proj-secretname/memory/pref-two.md" memory/style/pref-two.md
ok "stage a hook"                                     g stage "$B" "$ROOT/hooks/demo-gate.sh" hooks/demo-gate.sh
if [ ! -e "$B/skills/demo/__pycache__" ]; then printf '  PASS  __pycache__ is not staged\n'; pass=$((pass+1))
else printf '  FAIL  __pycache__ was staged\n'; fail=$((fail+1)); fi
if [ -f "$B/MANIFEST.json" ] && grep -q 'memory/pref-two.md' "$B/MANIFEST.json" \
   && ! grep -q 'proj-secretname' "$B/MANIFEST.json"; then
  printf '  PASS  MANIFEST.json records the memory without the project dir name\n'; pass=$((pass+1))
else printf '  FAIL  MANIFEST.json missing, lacks the record, or leaks the project dir name\n'; fail=$((fail+1)); fi

echo
echo "FRESH:"
t 0 "a freshly staged bundle is clean" "$B"

echo
echo "NO-CRY-WOLF — scrubbing the staged copy must not matter:"
sed -i 's/host-alpha/<host>/; s/First section/Opening/' "$B/skills/demo/SKILL.md"
sed -i 's/A stated position can be argued with/Take a position/' "$B/memory/prefs/pref-one.md"
t 0 "reworded heading and lead-in in the staged copy, source unchanged: fresh" "$B"

echo
echo "BODY-EDIT — any source edit is staleness, headings or not:"
printf 'one more body line\n' >> "$ROOT/skills/demo/SKILL.md"
t 1 "source body edited after staging is STALE" "$B"
ok "record re-pins after the staged copy is updated by hand" g record "$B" "$ROOT/skills/demo/SKILL.md" skills/demo/SKILL.md
t 0 "after record the file is fresh again" "$B"
printf '\n' >> "$ROOT/projects/proj-secretname/memory/pref-two.md"
t 1 "a project-scoped memory source edited is STALE" "$B"
ok "re-stage the memory" g stage "$B" "$ROOT/projects/proj-secretname/memory/pref-two.md" memory/style/pref-two.md
t 0 "re-staged memory is fresh" "$B"

echo
echo "UNKNOWN — no record must not pass:"
printf 'x\n' > "$B/skills/demo/extra.md"
t 1 "a staged file with no MANIFEST record is UNKNOWN" "$B"
rm "$B/skills/demo/extra.md"
mkdir -p "$T/nomanifest/skills/demo"; cp "$ROOT/skills/demo/tool.py" "$T/nomanifest/skills/demo/"
t 1 "a bundle with no MANIFEST.json at all is UNKNOWN" "$T/nomanifest"
mv "$ROOT/hooks/demo-gate.sh" "$T/demo-gate.sh.aside"
t 1 "a recorded source that no longer exists fails" "$B"
mv "$T/demo-gate.sh.aside" "$ROOT/hooks/demo-gate.sh"
t 0 "restored source is fresh again" "$B"

echo
echo "THE ZERO — nothing to check is n/a, not a refusal:"
mkdir -p "$T/hunks/hunks"; printf 'prose\n' > "$T/hunks/hunks/one.md"; printf 'readme\n' > "$T/hunks/README.md"
t 0 "a hunks-only bundle is n/a" "$T/hunks"

echo
printf '%s passed, %s failed\n' "$pass" "$fail"
[ "$fail" -eq 0 ]
