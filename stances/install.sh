#!/usr/bin/env bash
# Copy always-on stances into ~/.claude/memory/ and import each from ~/.claude/CLAUDE.md.
#   ./install.sh                 list what would be installed (no changes)
#   ./install.sh --apply a b     install the named stances (file names without .md)
#   ./install.sh --apply --all   install every stance in always-on/
# Checks every name before copying anything. Never overwrites: a stance whose name is already in
# ~/.claude/memory/ is skipped and not imported, and an @import line already in CLAUDE.md is not
# added twice. Delete any stance you disagree with afterwards.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mem="$HOME/.claude/memory"
claude_md="$HOME/.claude/CLAUDE.md"

apply=0
if [[ "${1:-}" == "--apply" ]]; then apply=1; shift; fi

if ((apply)) && ((! $#)); then
  echo "name the stances to install, or pass --all (run without --apply to list them)" >&2; exit 2
fi
[[ "${1:-}" == "--all" ]] && shift
if (($#)); then
  names=("$@")
else
  names=()
  for f in "$here"/always-on/*.md; do names+=("$(basename "$f" .md)"); done
fi

for n in "${names[@]}"; do
  [[ -f "$here/always-on/$n.md" ]] || { echo "no such stance: $n (nothing installed)" >&2; exit 1; }
done

((apply)) && mkdir -p "$mem" && touch "$claude_md"
for n in "${names[@]}"; do
  line="@~/.claude/memory/$n.md"
  if [[ -e "$mem/$n.md" ]]; then
    echo "skip   $n (a file with this name is already in $mem; left as it is and not imported)"
    continue
  elif ((apply)); then
    cp "$here/always-on/$n.md" "$mem/$n.md"
    echo "copied $n"
  else
    echo "would copy $n"
  fi
  if ((apply)) && ! grep -qxF "$line" "$claude_md"; then
    printf '%s\n' "$line" >> "$claude_md"
  fi
done
((apply)) || echo "(dry run: pass --apply to install)"
