#!/usr/bin/env bash
# PostToolUse(Write|Edit|MultiEdit): run bash-footgun-gate's rules over a shell script FILE just written.
#
# The gate reads only the Bash command string, so a trap written into a script and run as
# `bash file.sh` passes it unseen — hit twice in one session (a `while read` loop drained by ssh, a
# locale-dependent `sort` in a cross-host manifest). Advisory: the file is already written, so this
# reports findings back for a fix and never blocks. Some rules are about the harness (pgrep matching
# its wrapper, writes to memory paths) and can misfire on a file; the message says to judge them.
set -uo pipefail

payload=$(cat 2>/dev/null || true)
path=$(printf '%s' "$payload" | python3 -c 'import json,sys
try: print((json.load(sys.stdin).get("tool_input") or {}).get("file_path") or "")
except Exception: print("")')
case "$path" in *.sh|*.bash) ;; *) exit 0 ;; esac
# The gate and its suite quote every pattern on purpose.
case "${path##*/}" in bash-footgun-gate.sh|test-gate.sh) exit 0 ;; esac
[ -f "$path" ] || exit 0

out=$(python3 -c 'import json,sys; print(json.dumps({"tool_name":"Bash","tool_input":{"command":open(sys.argv[1],errors="replace").read()}}))' "$path" \
  | bash "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/bash-footgun-gate.sh" 2>&1 >/dev/null)
rc=$?
[ "$rc" -eq 2 ] || exit 0

{
  printf 'script-lint (advisory, %s is already written): bash-footgun-gate rules match this file.\n' "$path"
  printf 'Fix the ones that apply to a script; rules about the harness command string may not.\n\n'
  printf '%s\n' "$out" | grep -E '^  - '
} >&2
exit 2
