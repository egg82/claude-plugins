#!/usr/bin/env bash
# hook-version: 2   # bump on any behaviour change; the session hook reports skew
# PreToolUse gate for memory files — blocks the write BEFORE the file exists.
#
# WHY: path-scoped rules load on Read, not Write (anthropics/claude-code#23478, closed
# not-planned), so memory-write-discipline is absent exactly when a new memory is created.
# PostToolUse cannot block (the tool already ran), so this must be PreToolUse.
# Exit 2 blocks and returns the message to Claude. Exit 1 would FAIL OPEN — Claude Code
# treats 1 as a non-blocking error and proceeds. Never use 1 here.
# Not covered here: a memory authored through Bash (`cat > mem.md`, a python heredoc, `sed -i`) never
# reaches a Write|Edit hook. Two companion mechanisms cover it where installed:
#   - `bash-footgun-gate.sh` [gate:memory-write-via-bash] blocks the shapes a COMMAND STRING can
#     prove -- a `>`/`>>` redirect, `tee`, `sed -i`, a Python write -- matched against raw_cmd so a
#     heredoc body is still visible.
#   - `memory-bash-write-backstop.sh` (Stop) catches what no string can prove -- a path built from a
#     variable, a script written elsewhere and executed -- by comparing mtimes against the Write/Edit
#     calls the transcript records.
#
# A BROAD path-based Bash gate is deliberately not attempted: it would fire on legitimate bulk
# operations -- transfer-bundle `cp`, a cross-project `mv`, appends to MEMORY.md (already exempt) --
# several times per session, and a gate with false positives gets switched off, which is strictly
# worse than the prose it replaced.

set -uo pipefail
payload=$(cat)

# path and content on SEPARATE lines: a path containing a space used to truncate under IFS
# word-splitting, which silently matched no case arm and let the write through (fail-open).
parsed=$(printf '%s' "$payload" | python3 -c '
import json,sys,re
try: d=json.load(sys.stdin)
except Exception: print("PARSE_FAIL"); print(); print(); print(); print(); raise SystemExit
ti=d.get("tool_input") or {}
p=ti.get("file_path") or ti.get("path") or ti.get("notebook_path") or ""
raw=(ti.get("content") or ti.get("new_string") or "")[:1500]
old=(ti.get("old_string") or "")[:1500]
# MultiEdit puts every fragment in edits[]; reading only the top-level keys let a MultiEdit that
# deleted a `check:` line straight through.
ed=ti.get("edits") or []
if ed:
    raw=("\n".join((e.get("new_string") or "") for e in ed if isinstance(e,dict)))[:1500]
    old=("\n".join((e.get("old_string") or "") for e in ed if isinstance(e,dict)))[:1500]
shape=("write" if ti.get("content") is not None else
       "edit" if (ti.get("new_string") is not None or ed) else "unknown")
m=re.match(r"\s*---\r?\n(.*?)\r?\n---", raw, re.S)
fm=m.group(1) if m else ""
print("OK"); print(d.get("tool_name") or ""); print(p)
print(raw.replace("\n","\\n")); print(fm.replace("\n","\\n"))
print(old.replace("\n","\\n")); print(shape)' 2>/dev/null)
status=$(printf '%s' "$parsed" | sed -n '1p')
tool=$(printf '%s' "$parsed" | sed -n '2p')
path=$(printf '%s' "$parsed" | sed -n '3p')
content=$(printf '%s' "$parsed" | sed -n '4p')
# frontmatter only — an example `check:` sitting in prose must NOT satisfy the gate
fmatter=$(printf '%s' "$parsed" | sed -n '5p')
oldstr=$(printf '%s' "$parsed" | sed -n '6p')
shape=$(printf '%s' "$parsed" | sed -n '7p')

# FAIL CLOSED on an unreadable payload. Without this, a missing python3 or malformed JSON yielded an
# empty path, fell through the path cases, and allowed the write with no message at all.
if [ -z "$status" ] || [ "$status" = PARSE_FAIL ]; then
  echo "BLOCKED — the memory write gate could not read its input (empty, no python3, or unparseable" >&2
  echo "payload). Refusing rather than allowing an unchecked write. Fix the hook, don't bypass it." >&2
  exit 2
fi

# M11: only act on writes. Registered with matcher "*" this hook otherwise BLOCKS READS of the
# memory store while printing a message about writing. An absent tool_name is treated as a write,
# since older payload shapes omit it.
case "$tool" in
  ""|Write|Edit|MultiEdit|NotebookEdit) ;;
  *) exit 0 ;;
esac

# An explicitly-named write tool whose target we could not extract is a parse failure, not a
# non-event. Permitting it is how a payload-shape change silently disables this gate.
case "$tool" in
  Write|Edit|MultiEdit|NotebookEdit)
    if [ -z "$path" ]; then
      echo "BLOCKED — $tool payload carried no recognisable file path. The gate could not tell what" >&2
      echo "is being written, so it is refusing. If the payload shape changed, fix the hook." >&2
      exit 2
    fi ;;
esac

# A `user`/`feedback` type is SELF-DECLARED and this gate cannot judge whether it is honest — that is a
# known, deliberate hole (a preference has no falsifier, so forcing a probe on one is worse than none).
# What it CAN do is notice when a note claiming to be a preference reads like a claim about a system.
# Warn only: a false positive must never block a legitimate stance.
warn_mislabel() {
  printf '%s' "$1" | grep -qE '(^|\\n)[[:space:]]*type:[[:space:]]*(user|feedback)' || return 0
  local hits
  # a figure inside `backticks` is being DISCUSSED, not asserted — same reason hygiene.py strips it
  hits=$(printf '%s' "$2" | sed 's/`[^`]*`//g' | grep -oE '\b[0-9]+\.[0-9]+\.[0-9]+\b|/(etc|var|opt|usr)/[a-z]|\b[a-z0-9-]+\.(corp|local|internal|lan)\b|\b(systemctl|kubectl|rpm -q|dnf) ' | wc -l)
  [ "$hits" -ge 2 ] || return 0
  echo "note: this is typed as a preference but reads like a claim about a system ($hits signals:" >&2
  echo "version strings, absolute paths, hostnames, or commands). A preference has no falsifier; if this" >&2
  echo "actually describes a live system, retype it project/reference and give it a check:, or move it to" >&2
  echo "the thing it describes. Not blocking — the type is yours to declare." >&2
  return 0
}

# Repo-doc decay warnings used to live here. Removed: they only ever warned, and their
# `# EDIT ME` path list silently matched nothing for anyone but the author — a check
# reporting clean because it never ran. `hygiene.py doccontent` covers it and says so.
case "$path" in
  */.claude/projects/*/memory/*.md|*/.claude/memory/*.md) ;;
  .claude/projects/*/memory/*.md|.claude/memory/*.md) ;;
  *) exit 0 ;;
esac
case "$path" in */MEMORY.md) exit 0 ;; esac

# A write we cannot READ is a write we cannot judge. If the payload named a memory file but carried
# no content, new_string or edits[] that this gate understands, refuse instead of consulting the
# pre-write file on disk — that fallback would approve the change on the strength of the OLD content.
if [ "$shape" = unknown ]; then
  echo "BLOCKED — a write to a memory file arrived in a payload shape this gate cannot read (no" >&2
  echo "content, new_string or edits[]). It cannot tell whether the result keeps a check:, so it is" >&2
  echo "refusing rather than trusting the pre-write file. If the tool is legitimate, teach the hook." >&2
  exit 2
fi

# An Edit whose old_string carries a `check:` line and whose new_string does not is a REMOVAL of
# the probe. The disk fallback below sees the pre-edit file, still containing it, and would approve.
if printf '%s' "$oldstr" | grep -qE '(^|\\n)[[:space:]]*check:' \
   && ! printf '%s' "$content" | grep -qE '(^|\\n)[[:space:]]*check:'; then
  cat >&2 <<'MSG'
BLOCKED — this edit removes the `check:` probe from a memory.

The probe is what makes the memory falsifiable. If the fact is no longer checkable, the memory does
not belong here: move it beside its subject, or if it is genuinely unprobeable say so explicitly with
  check: "n/a — <reason>"
which records a deliberate decision instead of an absence.
MSG
  exit 2
fi

# check the content being written; fall back to the file if this is an edit
probe=0; pref=0
printf '%s' "$fmatter" | grep -qE '(^|\\n)[[:space:]]*check:' && probe=1
printf '%s' "$fmatter" | grep -qE '(^|\\n)[[:space:]]*type:[[:space:]]*(user|feedback)' && pref=1
# An Edit sends only a fragment, which usually has no frontmatter — fall back to the file on disk,
# reading ONLY its frontmatter block for the same reason.
if [ "$probe" = 0 ] && [ "$pref" = 0 ] && [ "$shape" != write ] && [ -f "$path" ]; then
  disk_fm=$(awk 'NR==1 && /^---/ {f=1; next} f && /^---/ {exit} f' "$path")
  printf '%s' "$disk_fm" | grep -qE '^[[:space:]]*check:' && probe=1
  printf '%s' "$disk_fm" | grep -qE '^[[:space:]]*type:[[:space:]]*(user|feedback)' && pref=1
fi
if [ "$probe" != 0 ] || [ "$pref" != 0 ]; then warn_mislabel "$fmatter" "$content"; exit 0; fi

cat >&2 <<MSG
BLOCKED — $(basename "$path") has no 'check:' probe and is not type user|feedback.

A memory describing a system must carry a command that would prove it wrong:
  check: "<cheap read-only command>"

If you cannot write one, it is NOT a memory. It belongs with its subject — a doc beside the
code, a companion file beside the skill, or a keyed log beside the runs. Put it there instead.
Genuinely unfalsifiable but about a system? Say so: check: "n/a — <reason>".
MSG
exit 2
