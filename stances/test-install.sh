#!/usr/bin/env bash
# Sandboxed-HOME test of stances/install.sh: never overwrites, never duplicates an import.
set -u
inst="$1"; H="$(mktemp -d)"; mkdir -p "$H/.claude/memory"
echo keep > "$H/.claude/memory/prefer-subtraction.md"
echo '@~/.claude/memory/verify-dont-anchor.md' > "$H/.claude/CLAUDE.md"
fail=0; ck() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }
HOME=$H bash "$inst" > /dev/null
ck "dry run changes nothing" '[[ $(ls "$H/.claude/memory" | wc -l) == 1 ]]'
HOME=$H bash "$inst" --apply > /dev/null 2>&1
ck "bare --apply refuses" '[[ $? == 2 && $(ls "$H/.claude/memory" | wc -l) == 1 ]]'
HOME=$H bash "$inst" --apply --all > /dev/null; HOME=$H bash "$inst" --apply --all > /dev/null
n=$(ls "$(dirname "$inst")/always-on" | wc -l)
ck "existing file kept" '[[ $(cat "$H/.claude/memory/prefer-subtraction.md") == keep ]]'
ck "all stances present ($n)" '[[ $(ls "$H/.claude/memory" | wc -l) == "$n" ]]'
ck "no duplicate imports" '[[ -z $(sort "$H/.claude/CLAUDE.md" | uniq -d) ]]'
ck "one import per installed stance" '[[ $(wc -l < "$H/.claude/CLAUDE.md") == $((n - 1)) ]]'
ck "pre-existing file not imported" '! grep -q prefer-subtraction "$H/.claude/CLAUDE.md"'
HOME=$H bash "$inst" --apply nope > /dev/null 2>&1
ck "unknown name fails" '[[ $? != 0 ]]'
rm -rf "$H/.claude"; mkdir -p "$H/.claude/memory"
HOME=$H bash "$inst" --apply verify-dont-anchor nope > /dev/null 2>&1
ck "a typo installs nothing" '[[ $? != 0 && -z $(ls "$H/.claude/memory") ]]'
rm -rf "$H"; exit $fail
