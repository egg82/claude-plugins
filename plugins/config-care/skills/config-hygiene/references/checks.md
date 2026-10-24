# What each check means, and what to do about it

Load when a mode reports a finding and you need to judge it, or before changing what a mode checks.
`SKILL.md` has one line per mode; this is the detail.

## `memory`

Dangling index bullets (pointing at a deleted file), orphan files (present with no bullet), an index
over ~12KB, and any memory over 8KB. It also audits the **always-on prefs dir** (`~/.claude/memory`),
which has no index and so can't be checked the same way: a pref file that no `@import` in `CLAUDE.md`
loads is a dead button, an import naming an absent file is broken, and the imported total is paid in
full on every session because imports expand inline rather than deferring. It also reports each
project's `MEMORY.md` index as a third resident term (kept out of the pref-body total the ratchet
compares) and warns at 80% of the caps beyond which MEMORY.md silently stops loading (25KB / 200 lines).

A fat index is a *symptom*; the cause is facts being written to project memory that have an owner
elsewhere. Don't compact the hooks to buy room — that only shortens the prose and, on a synced
fleet, makes each host rewrite them differently into a whole-file divergence. Move the entries out
instead, per the routing rule: a fact about a file belongs in a doc beside that file; a per-item
verdict belongs in a keyed log; only ownerless behavioural rules belong in memory.

A single memory over 8KB is nearly always a build journal — dated sections accreting because each
session appended rather than distilled. Read it for the handful of durable facts, move those to
their real home, and delete the narrative.

## `imports`

The always-loaded set: `CLAUDE.md` `@import` lines and the files behind them. Also folded into
`memory`, but addressable on its own because a SessionStart hook calls it.

Different shape from a project memory store, which is why it needs its own check: there is no index
file here, so membership is defined by the import lines themselves. It flags an import naming a
missing file (loads nothing, silently), a file nobody imports (dead weight that looks live), a
dangling import path, and total size. Size is framed as **cost**, not adherence — the evidence that
file size does not move adherence is owned by `always-on-prune` §4 (and tiered in
`collaboration-and-enforcement.md` §1), while context files add >20% cost every session. So the lever
is cutting narrative that directs nothing — and anything genuinely conditional belongs in
`.claude/rules/` with `paths:` frontmatter. It always prints the byte total, even when clean, so you
can tell it looked.

## `skills`

Counts content in `SKILL.md` that goes stale on a schedule the method doesn't control: dates, hard
counts, IP addresses, MACs. Fenced code blocks are excluded, so a date inside an example payload is
correctly ignored.

The bar is that **a skill should survive being handed to someone else with minimal editing**. An
endpoint they'd obviously swap is a parameter and fine; a MAC address that resolved one
investigation, a "validated on <date>", or an item count from one run is a *finding* and belongs in
a companion data file beside the skill — the way a curation skill ships `config.json` next to its
`SKILL.md`. Public IPs are scored double: they are both the most stale-prone and the thing you
least want to hand out.

## `probes`

Runs each memory's `check:` command and reports the ones that fail. A no-op unless
`HYGIENE_RUN_PROBES=1` (see `SKILL.md`).

The gate and the probe runner both key off what the file *declares*, not what it is about: any
memory that neither carries a `check:` nor declares `type: user`/`type: feedback` is in scope,
including one with no frontmatter at all. `*/MEMORY.md` is always exempt. `user` and `feedback` memories are
preferences and physical facts with no falsifier, and a forced probe on one of those passes forever
while proving nothing — worse than none, because the run then reports green over an unvalidated
claim. A memory that is genuinely about a system but can't be falsified by a command should say so
with `check: "n/a — <reason>"`, which the check counts separately from *missing*.

**When a probe fails, suspect the probe first.** Every probe failure seen so far has been the
probe's own bug — a `command -v` that a non-interactive shell can't resolve, a grep for wording the
target doesn't use, or a probe testing whether a *precondition* currently applies rather than
whether the *claim* still holds. That last one is also a routing signal: it usually means the fact
is method and belongs in a skill.

## `docs`

Flags a doc whose directory has commits newer than the doc's own, by more than 30 days. This is the
only check that catches the ordinary case of code moving on while its doc sits still. It cannot catch
a doc that was updated *wrongly*, and it cannot catch a doc that was never near its subject —
colocation is what handles that one.

## `doccontent`

The content counterpart to `docs`: repo docs carrying dates, status words and run counts. A doc can
be freshly committed and still assert something that stopped being true, which `docs` (an age check)
cannot see.

## `hooks`

The two halves of enforcement: a hook **registered** in `settings.json` whose script is missing, and
a script **present** in `hooks/` that no registration references. Either half alone is
indistinguishable from a hook that ran and found nothing — same files on disk, same silence in the
log. Found live across the fleet: one gate absent, one present but
referenced by nothing, while every other signal said the setup was healthy. **Presence is not
enforcement**, and a parity check across hosts will not catch it because the file counts match.

## `refs`

Wiki-style `links` in skills and their companion files pointing at a memory or skill that doesn't
exist. Concatenating a memory body into a companion drags its links along; the target later moves
and the pointer dies silently. The SessionStart hook runs this one.

## `numbering` and `testiso`

**`numbering`** — colliding (level, number) section headings, or a section grafted at the end so
numbers run out of order. **`testiso`** — a test suite mutating the real `$HOME` it is supposed to
test.

## `section-inventory.py` — not a mode

A **before/after diff of your own edit**. Run it before a graft and after, and diff the two:

```bash
python3 section-inventory.py SKILL.md > /tmp/before
#   ...graft the section...
python3 section-inventory.py SKILL.md > /tmp/after
diff /tmp/before /tmp/after
```

Per section: non-blank lines, bullet count, median wrap. **A section you did not intend to touch must
not change.** There is no pattern matching in it and nothing to false-positive, because it compares
your file against itself.

It exists because of a real four-part failure: anchoring an insert on a single bullet string, assuming
that string was the section boundary. The insert split the section and orphaned its tail; a later lift
"to the next heading" then swept the orphans up, duplicating them in a second repo. **The transferable
rule: a heading-count guard is not an over-capture guard.** An assert that a lifted span contained
exactly one `###` passed — the swept-up bullets were not headings. Compare the inventory, not the
heading count.

Median wrap is the *corroborating* column, which is where a heuristic belongs: a block whose width
matches its neighbour rather than its own section was written elsewhere. `numbering` catches the
resulting number collision; neither catches the orphan on its own.
