#!/usr/bin/env bash
# PostToolUse hook: redact credential VALUES out of tool output before it reaches the
# model's context. Thin wrapper; all logic and the full rationale are in the .py.
#
# Fails OPEN by construction: if python3 is missing or the script errors, this exits 0
# having emitted nothing, and the harness uses the original tool output unchanged.
# Not `exec python3 ... || exit 0`: a failed exec ends a non-interactive bash with 127
# before the `||` runs, so a missing python3 surfaced as a hook error on every call.
python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/secret-redact.py" 2>/dev/null
exit 0
