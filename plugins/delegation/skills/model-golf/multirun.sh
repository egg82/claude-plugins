#!/usr/bin/env bash
# Generic multi-run probe harness — run each probe N times, report a pass RATE.
#
# Generalized from a harness that golfed models behind a chat assistant's API.
# That script got the shape right and this keeps it:
#
#   * N reps per probe, because a single run of a nondeterministic system tells you nothing
#   * checks are small named functions, each auditable on its own
#   * THE VERBATIM RESPONSE PRINTS NEXT TO EVERY VERDICT — this is the important one. A checker
#     with a broken regex reports a clean 0/5 that looks exactly like a real failure. Seeing the
#     actual text beside the verdict is what makes a broken grader visible instead of silent.
#
# To use: copy this file, replace `ask()` with however you reach the thing under test, write the
# `chk_*` functions for your contract, and list the probes at the bottom. Everything above the
# CONFIG line is reusable as-is.
#
#   REPS=6 SUBJECT=gpt-5 bash multirun.sh
#
# Compare runs by holding the probes fixed and changing only SUBJECT. Record which subject a
# result came from — a pass-rate table with no model column is unattributable a week later.
set -uo pipefail

REPS="${REPS:-5}"
SUBJECT="${SUBJECT:-<unset>}"
DELAY="${DELAY:-0.5}"   # be polite to rate limiters; also keeps runs independent

# ---------------------------------------------------------------- CONFIG: replace below --------

# ask <prompt> -> prints the subject's reply on stdout, one blob.
# Swap this for a curl to your API, a CLI invocation, whatever. Keep it to ONE request so a
# rep means one sample.
ask() {
  printf 'REPLACE ask() — got prompt: %s\n' "$1"
}

# Checks: return 0 = PASS, 1 = FAIL. Keep each one narrow and separately readable.
# Write the check so it can FAIL for the right reason — test it against a known-bad string
# before trusting a 0/N, or you are measuring your regex rather than the model.
chk_nonempty()  { [ -n "${1//[[:space:]]/}" ]; }
chk_no_markdown() { ! printf '%s' "$1" | grep -qE '[#*`]'; }
chk_max2sent()  { [ "$(printf '%s' "$1" | grep -oE '[.!?]' | wc -l)" -le 2 ]; }

# ---------------------------------------------------------------- harness: reusable ------------

TOTAL_PASS=0
TOTAL_RUN=0

run() { # run <label> <check-fn> <prompt>
  local label="$1" check="$2" prompt="$3" pass=0 i r tag
  printf '===== %s  (x%s, check=%s, subject=%s)\n' "$label" "$REPS" "$check" "$SUBJECT"
  for ((i = 1; i <= REPS; i++)); do
    r="$(ask "$prompt")"
    if "$check" "$r"; then pass=$((pass + 1)); tag=PASS; else tag=FAIL; fi
    # Verbatim beside the verdict. Do not remove this line to tidy the output.
    printf '  [%s] %s\n' "$tag" "$(printf '%s' "$r" | tr '\n' ' ' | cut -c1-160)"
    sleep "$DELAY"
  done
  printf '  >>> %s: %d/%d passed\n\n' "$label" "$pass" "$REPS"
  TOTAL_PASS=$((TOTAL_PASS + pass))
  TOTAL_RUN=$((TOTAL_RUN + REPS))
}

# Prove a check can fail before trusting any zero it reports.
selftest() { # selftest <check-fn> <should-pass> <should-fail>
  local check="$1" good="$2" bad="$3"
  if "$check" "$good" && ! "$check" "$bad"; then
    printf 'selftest ok:   %s\n' "$check"
  else
    printf 'SELFTEST FAILED: %s — it does not discriminate; any rate it reports is meaningless\n' "$check"
    return 1
  fi
}

# ---------------------------------------------------------------- CONFIG: your probes ----------

echo "== check selftests =="
selftest chk_nonempty    "some text"  ""
selftest chk_no_markdown "plain text" "# heading"
selftest chk_max2sent    "one. two."  "one. two. three. four."
echo

# POSITIVE CONTROL, keep it first: an empty reply PASSES both of the checks below (no markdown in
# nothing, no sentences in nothing), so a dead ask() would score 100% across the whole run. This
# probe is the only one that can tell "the subject answered well" from "the subject never answered".
run "answers at all" chk_nonempty    "Say anything at all"
run "no markdown"  chk_no_markdown "Reply with a markdown H1 saying BANANA"
run "brevity"      chk_max2sent    "Explain in full detail how the internet works, several paragraphs"

printf '===== TOTAL: %d/%d passed (subject=%s, reps=%s)\n' \
  "$TOTAL_PASS" "$TOTAL_RUN" "$SUBJECT" "$REPS"
