#!/usr/bin/env bash
# Regression suite for secret-redact.sh / secret-redact.py.
# Run directly:  bash test-secret-redact.sh   (HOOK=<path> tests a specific secret-redact.py)
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/test-secret-redact.py" "$@"
