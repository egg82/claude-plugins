#!/usr/bin/env bash
# scrub-sweep.sh — verification gate for a Claude Code config transfer bundle.
#
# Greps a bundle directory for tokens that must NOT cross a trust boundary
# (secrets, private IPs, emails, home paths) PLUS any environment-specific
# tokens you supply. Prints file:line:match for every hit and exits non-zero
# if anything is found, so it can gate an export.
#
# Usage:
#   scrub-sweep.sh <bundle-dir> [env-patterns-file] [allowlist-file]
#
#   env-patterns-file : one extended-regex per line — YOUR environment's
#                       hostnames, domains, organisation/client names, internal
#                       tool + script names, usernames. THIS is where most real
#                       hits come from; the built-ins below are only a floor.
#                       POSIX ERE only. Matching is already case-insensitive, so
#                       write patterns in lowercase; a PCRE inline flag like
#                       "(?i)" matches NOTHING under grep -E and silently makes
#                       the whole line dead. That failure looks exactly like a
#                       clean bundle — do not use it.
#   allowlist-file    : one extended-regex per line — known false positives to
#                       drop from results (e.g. a public domain a skill cites).
#
# The built-in patterns are sensitive in ANY environment. Extend, don't rely.
#
# MARKINGS=<file> adds a case-SENSITIVE pass over the document markings your organisation
# uses (one extended regex per line) — set it when exporting FROM a machine that holds
# marked or regulated data.

set -uo pipefail

DIR="${1:?usage: scrub-sweep.sh <bundle-dir> [env-patterns-file] [allowlist-file]}"
ENV_PATTERNS="${2:-}"
ALLOWLIST="${3:-}"

# --- environment-agnostic sensitive patterns (always checked) ---
BUILTIN=(
  '\b10\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\b'                 # private IPv4 10/8
  '\b192\.168\.[0-9]{1,3}\.[0-9]{1,3}\b'                       # private IPv4 192.168/16
  '\b172\.(1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3}\b'     # private IPv4 172.16/12
  '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'             # email address
  '(/home/|/Users/)[a-z0-9_.-]+'                               # home directory path
  '/var/mnt/home/[a-z0-9_.-]+'                                 # alternate home-dir mount
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'                        # private key block
  '(api[_-]?key|secret|token|password|passwd|passphrase)[[:space:]]*[:=]' # secret assignment
  'AKIA[0-9A-Z]{16}'                                          # AWS access key id
  '(ghp|gho|ghs|ghr)_[A-Za-z0-9]{20,}'                        # GitHub token
  'glpat-[A-Za-z0-9_-]{20,}'                                  # GitLab PAT
  'xox[baprs]-[A-Za-z0-9-]{10,}'                              # Slack token
  'Bearer[[:space:]]+[A-Za-z0-9._-]{20,}'                     # bearer token
)

# --- document markings — enabled with MARKINGS=<file> ---
# For a machine that holds marked or regulated data, put your organisation's markings in a file
# (one extended regex per line, e.g. '\bSTAFF ONLY\b', '\bDO NOT FORWARD\b') and run:
#   MARKINGS=markings.txt scrub-sweep.sh <dir> <env-patterns> [allowlist]
# They are only a FLOOR: also add project, customer and contract names to env-patterns, and bias
# hard to exclude-by-default. Markings are ALL-CAPS by convention, so they run in a case-SENSITIVE
# pass: matched case-insensitively they fire on ordinary English ("staff only parking", "please
# do not forward"), and after the third spurious hit nobody reads the output and the real hit leaves
# with the noise. Case-sensitivity is a per-invocation flag, so this needs its own pass.
CASED=()
if [[ -n "${MARKINGS:-}" ]]; then
  [[ -f "$MARKINGS" ]] || { echo "FAIL: MARKINGS file $MARKINGS not found"; exit 2; }
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    CASED+=("$line")
  done < "$MARKINGS"
  [[ ${#CASED[@]} -gt 0 ]] || { echo "FAIL: MARKINGS file $MARKINGS has no patterns"; exit 2; }
fi

# Assemble the alternation.
PATTERN=$(printf '%s|' "${BUILTIN[@]}")
if [[ -n "$ENV_PATTERNS" && -f "$ENV_PATTERNS" ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    PATTERN+="$line|"
  done < "$ENV_PATTERNS"
fi
PATTERN="${PATTERN%|}"

# --- hard stop: an explicit NO-SHIP marker means the file must not be in a bundle at all ---
# Some memories are about a named individual or carry private reasoning. Prose saying so is not
# enforcement, because the person packaging the bundle is exactly the person who won't re-read it.
# So this is a hard stop with its own exit, checked BEFORE any token matching: a NO-SHIP file is
# not a token to review, it is a file that must not be in the tree.
#
# The two-stage shape is load-bearing and easy to "simplify" into a broken gate. The outer
# `grep -rIl` is only a cheap file-finder; the head-scoped re-test is what decides. Collapse it to
# a single `grep -rIl 'NO-SHIP'` and it fires on any file that merely DOCUMENTS the marker —
# including the SKILL.md section that defines it — and whoever needs a bundle out will silence it.
# Narrow it the other way, to a bare NO-SHIP alone on a line, and it matches NONE of the genuinely
# marked files while still looking like a check. Both failures have happened elsewhere. Verify any
# change against real marked files, never against a fixture written to match the change.
# NUL-delimited: an unquoted `for f in $(grep -rIl ...)` word-splits on spaces, so a bundle staged
# under a path like "/tmp/x/my bundle/..." silently skipped every file — a security gate failing
# quietly, which is the exact shape this script exists to prevent.
NOSHIP=$(grep -rIlZ 'NO-SHIP' "$DIR" 2>/dev/null | while IFS= read -r -d '' f; do
  head -25 "$f" | grep -qE '^[[:space:]]*(<!--[[:space:]]*)?NO-SHIP\b' && printf '%s\n' "$f"
done)
if [ -n "$NOSHIP" ]; then
  echo "FAIL: files carrying a NO-SHIP marker are present in the bundle:" >&2
  printf '  %s\n' "$NOSHIP" >&2
  echo "Remove them; they are person-specific or private by declaration." >&2
  exit 1
fi

# Grep the text of the bundle for sensitive tokens (grep -I skips binaries; handled below).
RESULTS=$(grep -rInEi "$PATTERN" "$DIR" 2>/dev/null)

# Second, case-SENSITIVE pass for the all-caps banner markings. Separate invocation because -i is
# per-invocation; results are appended before the allowlist filter so both passes are allowlisted.
if [[ ${#CASED[@]} -gt 0 ]]; then
  CASED_PATTERN=$(printf '%s|' "${CASED[@]}"); CASED_PATTERN="${CASED_PATTERN%|}"
  CASED_HITS=$(grep -rInE "$CASED_PATTERN" "$DIR" 2>/dev/null)
  [[ -n "$CASED_HITS" ]] && RESULTS=$(printf '%s\n%s' "$RESULTS" "$CASED_HITS")
fi

# Drop allowlisted false positives.
#
# STRIP BLANKS AND COMMENTS FIRST — this is load-bearing, not tidiness. `grep -f` treats every
# line of the file as a pattern, so a BLANK line is an empty pattern matching every result, and
# under -v it discards the whole set: the sweep then prints PASS while suppressing real hits.
# A bare `#` line is nearly as bad — it matches any result line containing a `#`, which is most
# lines of any shell script. Both failures are invisible from outside, because a suppressed FAIL
# and a genuine PASS are the same output. (`# some text` is only a literal and is harmless, but
# there is no reason to allow the shape at all.)
#
# The -s guard is independent: an allowlist that is ENTIRELY comments leaves an empty pattern
# file, and `grep -f /dev/null` matches nothing, so -v would pass every result through.
#
# ALLOWLIST BY MATCH, NOT BY LINE. `grep -v` drops the whole result line, so ONE allowlisted generic
# word silently suppresses every real token sharing that line with it. Measured, live, in a bundle
# that had already passed this sweep: `homelab` was allowlisted as a harmless word, and the line
#   "…see the notes for homelab setup, owner: <first name>"
# was dropped whole, taking the first name out with it. That is the same leak class the
# cold read exists to catch, except here the gate was actively hiding it. Prose already warned about
# this ("keep entries specific") and it happened anyway, so the fix is mechanical: blank out only the
# allowlisted SPANS, then re-test what is left. A line survives the allowlist only if nothing
# sensitive remains after its false positives are removed.
if [[ -n "$ALLOWLIST" && -f "$ALLOWLIST" ]]; then
  AL_CLEAN=$(mktemp); trap 'rm -f "$AL_CLEAN"' EXIT
  grep -vE '^[[:space:]]*($|#)' "$ALLOWLIST" > "$AL_CLEAN"
  if [[ -s "$AL_CLEAN" ]]; then
    RESULTS=$(AL="$AL_CLEAN" PAT="$PATTERN" CASED_PAT="${CASED_PATTERN:-}" python3 -c '
import os, re, sys
# The patterns are POSIX ERE, written for grep. Python re does NOT understand POSIX bracket
# classes: it reads `[[:space:]]` as an ordinary class of the characters "[:space" plus a `]*`,
# so a `<secret-word> = value` line MATCHES under grep and does NOT here. Re-testing an allowlisted
# with the untranslated pattern would therefore drop real secrets — the exact false-negative this
# whole filter exists to prevent, reintroduced by the filter. Translate before compiling.
_POSIX = {"[:space:]": r"\s", "[:digit:]": "0-9", "[:alpha:]": "a-zA-Z",
          "[:alnum:]": "a-zA-Z0-9", "[:upper:]": "A-Z", "[:lower:]": "a-z",
          "[:punct:]": re.escape("!-/:-@[-`{-~"), "[:xdigit:]": "0-9A-Fa-f"}
def ere(p):
    for k, v in _POSIX.items():
        p = p.replace(k, v)
    return p
allow = [l.rstrip("\n") for l in open(os.environ["AL"]) if l.strip()]
al  = re.compile(ere("|".join(allow)), re.I)
pat = re.compile(ere(os.environ["PAT"]), re.I)
cased = os.environ.get("CASED_PAT") or None
cre = re.compile(ere(cased)) if cased else None
for line in sys.stdin.read().splitlines():
    if not line.strip():
        continue
    # Only the TEXT of the hit is scrubbed of allowlisted spans; the "file:line:" prefix is not,
    # or an allowlisted word appearing in a PATH would exempt that whole file from the sweep.
    head, sep, body = line.partition(":")
    n, sep2, text = body.partition(":")
    if not (sep and sep2 and n.isdigit()):
        head, text, sep, sep2 = "", line, "", ""
    stripped = al.sub(" ", text)
    if pat.search(stripped) or (cre and cre.search(stripped)):
        print(line)
' <<< "$RESULTS")
  fi
fi
RESULTS=$(printf '%s\n' "$RESULTS" | sed '/^$/d')

# A scrubbed bundle must be ALL TEXT. grep -I silently skips binaries, so a binary compiled
# from PRE-scrub source (e.g. a .pyc with real hostnames in its string table) would pass
# invisibly. Treat any non-text file as an automatic FAIL, not an invisible pass.
#
# "Text" to grep -I is not "text" to a reader: ImageMagick's `import` (what a stray `import sys`
# typed into a shell runs) writes a full-screen capture as 7-bit PostScript, which grep -I passes.
# A 67 MB desktop screenshot once sat in a skill dir one copy away from shipping. So PostScript/PDF
# headers and anything over 512 KiB (no real config file comes close) count as non-text too.
BINARIES=""
while IFS= read -r f; do
  if ! grep -Iq . "$f" 2>/dev/null \
     || [ "$(stat -c %s "$f")" -gt 524288 ] \
     || head -c 5 "$f" | grep -Eq '^(%!PS|%PDF-)'; then
    BINARIES+="${f#${DIR%/}/}"$'\n'
  fi
done < <(find "$DIR" -type f)
BINARIES=$(printf '%s' "$BINARIES" | sed '/^$/d')

# Freshness. A clean scrub says nothing about whether the staged copy is CURRENT: a stale file and
# a fresh one are the same shape, and the sweep passes both. Chained here rather than left as its
# own step, because a separate step is one more thing to skip on the round a bundle is rushed.
FRESH_RC=0
FRESH_OUT=""
_FG="$(dirname "$0")/freshness-gate.py"
if [[ -f "$_FG" ]]; then
  FRESH_OUT=$(python3 "$_FG" "$DIR" 2>&1); FRESH_RC=$?
else
  # FRESH_RC must be 1, not 0. At 0, deleting or renaming the gate script silently restores the old behaviour and the
  # sweep goes back to printing PASS over a bundle whose staleness nothing checked: a missing check reading as a passed one.
  FRESH_OUT="  freshness-gate.py not found beside this script — staleness is UNCHECKED, not clean"
  FRESH_RC=1
fi

if [[ -z "$RESULTS" && -z "$BINARIES" && "$FRESH_RC" -eq 0 ]]; then
  echo "PASS — no sensitive tokens found in $DIR"
  printf '%s\n' "$FRESH_OUT"
  exit 0
fi

echo "FAIL — bundle is not clean:"
if [[ -n "$BINARIES" ]]; then
  echo
  echo "Binary/non-text files (must NOT be in a scrubbed text bundle — remove them):"
  printf '%s\n' "$BINARIES" | sed 's/^/  /'
fi
if [[ -n "$RESULTS" ]]; then
  echo
  echo "Potential sensitive tokens (review each; generalize or remove):"
  printf '%s\n' "$RESULTS" | sed "s#^${DIR%/}/##"
fi
if [[ "$FRESH_RC" -ne 0 ]]; then
  echo
  echo "Staleness (a source changed since it was staged, or has no MANIFEST.json record):"
  printf '%s\n' "$FRESH_OUT"
fi
echo
echo "Fix, then re-run. Built-in patterns are a floor — add your hostnames/domains/organisation/tool"
echo "names to an env-patterns file (and MARKINGS=<file> for document markings)."
exit 1
