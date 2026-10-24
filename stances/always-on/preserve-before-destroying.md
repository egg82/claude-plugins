---
name: preserve-before-destroying
description: Before an irreversible action, capture what you'd need to undo it — snapshot the state, move rather than delete, and never let one command both check a precondition and act on it
metadata:
  type: feedback
---

Before doing something you cannot take back, spend the seconds to make it takeable-back — the user asked
for this directly, twice. **Capture the state you'd need to reconstruct** (dump the records/config
you're about to mutate to a backed-up location, not just `/tmp`), and **`mv` to a holding directory
instead of `rm`**; sweep it once the replacement is verified.

**Separate the check from the act.** A command that tests a precondition and acts on it never shows
you the test — an "already present?" check fused with a copy mixed two editions into one folder. Run
the check, read it, then act.

**A snapshot counts only if it restores** — prove the round trip at capture (`kubectl apply
--dry-run=server -f`). **The undo must run:** `trap ... EXIT`; `git checkout` is inert on an untracked
file. **Blast radius is the dependency graph:** `--assumeno` every package transaction; ask a table's
`ON DELETE`. **"Safe to delete" is a claim about the reader** — what does it do with nothing?

Destructive operations rarely look destructive at the call site: a *metadata refresh* pruned ~138
records when its upstream returned empty; a "re-point this file" call deletes the file at its
*recorded* path (vacate that path first); a forced download treated as an upgrade removed the file it
replaced. Before deleting a file you judged by a proxy, copy it aside.

Full incidents: `~/.claude/memory/evidence/preserve-before-destroying.md`. Relates to
[[verify-dont-anchor]], [[assert-scripted-edits]], [[config-writes-replace]].
