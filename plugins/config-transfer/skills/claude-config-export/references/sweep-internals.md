# Sweep and freshness-gate internals — why the gates are shaped as they are

Read when a step-5 gate result surprises you, when editing `scrub-sweep.sh`, `freshness-gate.py` or
an allowlist, or before arguing that a gate is wrong. `test-sweep.sh` and `test-freshness-gate.sh`
in the skill's directory cover the behaviours below; run both after any change.

## Freshness gate

**A clean scrub says nothing about whether the copy is CURRENT** — a stale file and a fresh one are
the same shape. A diff is meaningless by design (scrubbing changes content), so the fact is captured
at copy time instead: `stage` records the source's sha256 in `MANIFEST.json`, and the gate compares
it with the source's sha256 now. `scrub-sweep.sh` chains it; a missing gate script fails rather than
passing quietly.

**Why not landmarks.** The previous gate compared headings and the first six words of bold lead-ins
between source and copy. It refused correctly scrubbed copies whose lead-in was reworded (and grew an
allow-list to quiet them), and it passed a stale copy whenever the source edit left every heading
alone. A hash has neither failure. What it gives up: it cannot see a scrub that removed something
load-bearing — the cold-read lenses in 5b own that.

**Why not mtime.** Every file in a bundle dir is stamped at copy time, so a staged copy is always
newer than its source, and "is the source newer than the copy?" says *inherit* forever by
construction. This shipped stale files, including a hook missing a block the installed file
carried, both under the SAME version number, so the version
line couldn't catch it either.

**Why inherit the previous bundle.** Re-copying from the source is always *safe* but undoes the
scrub, forcing a full re-scrub **and** a full re-cold-read, and the cold-read fixes are the expensive
artifact; a fresh copy silently discards them. When a source moves on, edit the staged copy to match
and `record` it, rather than re-copying.

**The zeros — collapsing them makes the gate lie.** Nothing staged under the mirrored trees is a
hunks-only bundle and genuinely clean. A staged file with no `MANIFEST.json` record is UNKNOWN and
fails: an earlier gate counted unpaired files as checked and so verified the whole memory tier with
nothing, because memories are re-tiered into `memory/<tier>/` while installed flat. The record now
names its source explicitly, so pairing is not inferred from paths at all. A project-scoped source is
stored as `projects/*/memory/<name>` (the dir name encodes the home path) and must resolve to exactly
one file.

## Re-copy undoes the scrub

Updating a bundled file by copying the local original over it silently reintroduces every
generalized token.

## Allowlist is span-level, not line-level

The filter used to drop the whole result line, so one generic allowlisted word silently carried
every real token sharing that line out with it: an allowlisted generic word took a person's first name
past a PASS. Filtering is by matched *span* now: allowlisted spans are blanked
and whatever remains is re-tested. If you ever re-implement the re-test, translate POSIX bracket
classes before compiling in Python — `re` reads `[[:space:]]` as an ordinary character class, so a
real secret on an allowlisted line can go out clean, announcing itself only as a `FutureWarning`.

## NO-SHIP matcher shape

**Match the form, not the description.** Narrowing the check to a bare `NO-SHIP` on its own line —
which is what "a literal marker" sounds like — matched *none* of the real files and silently disabled
the gate. Collapsing it the other way, to a single `grep -rIl 'NO-SHIP'`, fires on any file that
merely *documents* the marker — including the SKILL.md section — and whoever needs a bundle out will
then silence it. The two-stage shape is load-bearing: the outer find is cheap, the head-scoped
re-test is what decides. Verify any change against the actual marked files, never a fixture you wrote
to match your change. `test-sweep.sh` covers both directions.

## A gate firing is not a finding

A skill can be withheld because two patterns fired on its worked case, when the name that matched was
the exporter's own public handle on their own machine. Once the premise is copied into several places
they all agree, and no single review surfaces it. Say what the matched token identifies before
excluding anything, and measure a claim like "scrubbing would gut the case study" instead of assuming
it.
