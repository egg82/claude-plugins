#!/usr/bin/env bash
# Regression suite for scrub-sweep.sh.
#
# WHY THIS EXISTS: the sweep's failure mode is INVISIBLE FROM OUTSIDE. A suppressed FAIL and a
# genuine PASS produce identical output, so "I ran it and it passed" proves nothing on its own.
# The bug that prompted this: `grep -f` treats every allowlist line as a pattern, so a BLANK line
# is an empty pattern that matches everything and, under -v, discarded the entire result set —
# the gate printed PASS while real leaks went through. A bare `#` line did the same to any result
# line containing `#`, which is most lines of any shell script.
#
# Every case below asserts an exit STATUS, because the printed text and the status are separate
# claims and only the status gates an export.
#
# Usage: bash test-sweep.sh          (honours SWEEP= to test a copy elsewhere)
set -uo pipefail
SWEEP="${SWEEP:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scrub-sweep.sh}"
[ -f "$SWEEP" ] || { echo "NO SWEEP at $SWEEP — nothing was tested (UNCHECKED, not passing)"; exit 1; }

T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
pass=0; fail=0

t() { # t <expected-rc> <label> <bundle-dir> [allowlist]
  local exp="$1" label="$2" dir="$3" al="${4:-}"
  local rc
  if [ -n "$al" ]; then bash "$SWEEP" "$dir" "$T/patterns.txt" "$al" >/dev/null 2>&1; rc=$?
  else                  bash "$SWEEP" "$dir" "$T/patterns.txt"       >/dev/null 2>&1; rc=$?; fi
  if [ "$rc" -eq "$exp" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n' "$rc" "$exp" "$label"; fail=$((fail+1)); fi
}

tc() { # same as t(), but with MARKINGS set — the markings pass is OFF by default, so a case
       # written with t() would exercise none of it and report green over untested code.
  local exp="$1" label="$2" dir="$3"
  local rc
  MARKINGS="$T/markings.txt" bash "$SWEEP" "$dir" "$T/patterns.txt" >/dev/null 2>&1; rc=$?
  if [ "$rc" -eq "$exp" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n' "$rc" "$exp" "$label"; fail=$((fail+1)); fi
}

# --- fixtures -------------------------------------------------------------
printf 'sekrit-hostname\nsekrit-project\n' > "$T/patterns.txt"

mkdir -p "$T/dirty" "$T/dirty-hash" "$T/clean"
printf 'ssh admin@sekrit-hostname\n'        > "$T/dirty/leak.md"
printf 'ssh admin@sekrit-hostname # note\n' > "$T/dirty-hash/leak.sh"
printf 'nothing to see here\n'              > "$T/clean/ok.md"

printf 'harmless-token\n'              > "$T/al-normal.txt"
printf 'harmless-token\n\nanother\n'   > "$T/al-blank.txt"      # BLANK line
printf '#\nharmless-token\n'           > "$T/al-barehash.txt"   # bare '#'
printf '# just a comment\n#\n'         > "$T/al-allcomment.txt" # nothing but comments
printf 'sekrit-hostname\n'             > "$T/al-suppress.txt"   # legitimately allowlists the hit
printf 'homelab\n'                     > "$T/al-generic.txt"    # a harmless generic word

# CO-OCCURRENCE: a real token sharing a line with an allowlisted generic word. Filtering by LINE
# drops both, so the allowlist silently exempts the leak — measured live, on a bundle that had
# already passed this sweep, with a first name riding out on a `homelab` line.
mkdir -p "$T/cooccur"
printf 'see the homelab notes, sekrit-hostname will come back\n' > "$T/cooccur/note.md"

# ...and the mirror image: the allowlisted word must still suppress a line where it is the ONLY hit.
mkdir -p "$T/only-generic"
printf 'ordinary homelab prose with nothing else in it\n' > "$T/only-generic/note.md"

# A BUILT-IN pattern written with a POSIX bracket class, on a line that also carries an allowlisted
# word. The allowlist re-test runs in a second regex engine, and Python's does not understand
# `[[:space:]]` — so this line matched the first pass and silently failed the re-test, dropping a
# real secret assignment. Any built-in using a POSIX class is exposed the same way.
mkdir -p "$T/posix-class"
printf 'homelab config: password = hunter2\n' > "$T/posix-class/conf.md"

# An allowlisted word appearing in a PATH must not exempt that file's contents.
mkdir -p "$T/homelab-dir"
printf 'ssh admin@sekrit-hostname\n' > "$T/homelab-dir/notes.md"

# --- the suite ------------------------------------------------------------
echo "BASELINE — the gate must fire at all:"
t 1 "dirty bundle, no allowlist"                  "$T/dirty"
t 0 "clean bundle, no allowlist"                  "$T/clean"
t 1 "dirty bundle, ordinary allowlist"            "$T/dirty"      "$T/al-normal.txt"

echo "REGRESSION — an allowlist must never suppress the WHOLE result set:"
t 1 "allowlist containing a BLANK line"           "$T/dirty"      "$T/al-blank.txt"
t 1 "allowlist containing a bare '#'"             "$T/dirty-hash" "$T/al-barehash.txt"
t 1 "allowlist that is entirely comments"         "$T/dirty"      "$T/al-allcomment.txt"

echo "STILL WORKS — a real allowlist entry must still suppress its own hit:"
t 0 "allowlist that legitimately covers the hit"  "$T/dirty"      "$T/al-suppress.txt"

echo "ALLOWLIST BY MATCH — a generic entry must not carry a real token out with it:"
t 1 "a real token on the same line as an allowlisted word still FAILS" "$T/cooccur"     "$T/al-generic.txt"
t 0 "a line whose only hit IS the allowlisted word still passes"       "$T/only-generic" "$T/al-generic.txt"
t 1 "an allowlisted word in the PATH does not exempt the file"         "$T/homelab-dir" "$T/al-generic.txt"
t 1 "a POSIX-class built-in still fires through the allowlist re-test" "$T/posix-class" "$T/al-generic.txt"

echo
echo "NO-SHIP — a declared-private file must never sit in a bundle:"
# This gate has been broken elsewhere by a well-meaning narrowing (requiring a bare NO-SHIP alone
# on a line), which matched none of the real files and silently disabled it. The real marker is an
# HTML comment under the frontmatter; prose merely DISCUSSING it must not trip the gate, or the
# SKILL.md section that documents the marker fails its own check.
mkdir -p "$T/noship" "$T/noship-prose"
printf -- '---\nname: private-thing\n---\n<!-- NO-SHIP: person-specific / private context. -->\n\nbody\n' > "$T/noship/private.md"
printf 'The gate fires on a NO-SHIP marker in the head of a file.\n' > "$T/noship-prose/doc.md"
t 1 "file carrying the real NO-SHIP marker"        "$T/noship"
t 0 "file that only mentions NO-SHIP in prose"     "$T/noship-prose"

echo "NO-SHIP — the finder must survive a path containing spaces:"
# A bundle staged under a path with a space ("/tmp/x/my bundle") word-split in the original
# `for f in $(grep -rIl ...)` and silently checked nothing — a security gate failing quietly.
mkdir -p "$T/with space"
printf -- '---\nname: p\n---\n<!-- NO-SHIP: private -->\nbody\n' > "$T/with space/private.md"
t 1 "NO-SHIP under a path with a space"             "$T/with space"

echo "MARKINGS — the markings pass must fire on markings and NOT on English:"
# The negative is the load-bearing one: matched case-insensitively, markings fire on ordinary prose
# ("staff only parking", "please do not forward"), and a gate that cries wolf on clean input is one
# people learn to bypass. The pass is case-SENSITIVE, which keeps every real (all-caps) marking.
printf '%s\n' '\bSTAFF ONLY\b' '\bDO NOT FORWARD\b' > "$T/markings.txt"
mkdir -p "$T/mark-marking" "$T/mark-english"
printf 'Handling: STAFF ONLY, DO NOT FORWARD\n'                     > "$T/mark-marking/doc.md"
printf 'Please do not forward this; the room is staff only.\n'      > "$T/mark-english/doc.md"
tc 1 "a marking must FAIL with MARKINGS set"            "$T/mark-marking"
tc 0 "lowercase English must PASS with MARKINGS set"    "$T/mark-english"
# Pins WHY the case above fails: the marking must be invisible with MARKINGS unset, or the case is
# not testing the code it claims to test.
t  0 "same marking is not flagged with MARKINGS unset"  "$T/mark-marking"
MARKINGS="$T/nonexistent" bash "$SWEEP" "$T/mark-english" "$T/patterns.txt" >/dev/null 2>&1; rc=$?
if [ "$rc" -eq 2 ]; then printf '  PASS  (rc=2) a missing MARKINGS file fails loudly\n'; pass=$((pass+1))
else printf '  FAIL  (rc=%s want=2) a missing MARKINGS file fails loudly\n' "$rc"; fail=$((fail+1)); fi

echo "BINARIES — a bundle must be all text:"
printf '\x7fELF\x02\x01\x01\x00binary\n' > "$T/clean/blob.bin"
t 1 "clean text but one binary file"              "$T/clean"
rm -f "$T/clean/blob.bin"
# 7-bit PostScript passes grep -I; a stray ImageMagick screen grab is exactly this shape.
printf '%%!PS-Adobe-3.0\n%%%%Creator: (ImageMagick)\n0f0f0f0f\n' > "$T/clean/sys"
t 1 "7-bit PostScript screen capture (grep -I calls it text)" "$T/clean"
rm -f "$T/clean/sys"
head -c 600000 /dev/zero | tr '\0' 'a' | fold -w 80 > "$T/clean/huge.txt"
t 1 "plain text over the size cap"                "$T/clean"
rm -f "$T/clean/huge.txt"
t 0 "clean dir passes again after removals"       "$T/clean"

echo
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
exit $(( fail > 0 ))
