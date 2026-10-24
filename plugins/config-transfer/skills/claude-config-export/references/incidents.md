# The failure modes behind the export rules

SKILL.md states each rule with a one-line reason. Open this when a rule seems excessive and you are
tempted to skip it, or when changing the sweep / freshness gate.

## Why inheritance is not decided by mtime (step 5)

The obvious rule is "reuse a staged copy if the live source has not been modified since it was made".
Every file in a bundle dir is stamped at copy time, so the copy is always newer than the source it was
made from and the test says *inherit* essentially forever. Content edits stop propagating and nothing
says so, because a stale file and a current one are the same shape. It ships hooks missing blocks the
installed file has, under the SAME version number as the file they are stale against, so the version
line cannot catch it either. The recipient then compares the bundle against their installed files, and
the mismatch reads as a defect in the wrong place.

Inheriting the previous bundle's scrubbed copies, decided by hash, also preserves the previous round's
cold-read fixes, which a fresh copy silently discards.

## Re-copying from the source undoes the scrub (step 5)

Copying a local original over a bundled file reintroduces every token you generalized. It is easy to
do by reflex when updating one file, which is why the sweep re-runs after any touch.

## The fixture leak (step 5b)

A fixture corpus mined from one person's real activity passes sweeps, because personal queries contain
no hostname. A skill's example harness can carry a detector suite built from real search history,
benchmark tasks naming items from a personal library, and a grader hardcoding one of those answers. The
same applies to any recorded-real-input corpus: hook test fixtures carrying real service names and
internal script names, captured commands, sample logs.

## A leak fixed in one file but not its siblings (step 5b: hand cold agents the previous findings)

A README can state that an example harness's fixtures were neutralised while sibling scripts and
another skill's SKILL.md still carry the same raw subjects. The remediation was scoped to the filename
in the finding; the population was several files and exactly one got fixed. A fix is a claim about a
population, and you probably fixed one member. Add the subject terms to your env-patterns file so the
regex catches them mechanically, but treat the pattern list as the backstop, not the method: the next
leak will be a category nobody has a pattern for either.

## A hit is a question (step 5)

A whole skill can be withheld because its case study "named an individual" when the individual was the
exporter, in their own public repo. The reasoning then sits agreeing with itself in the patterns file,
the allowlist comment and the README. Before excluding over a hit, say what the matched token
identifies and who it exposes.

## The cold read is load-bearing

A regex sweep can pass clean while the exporter's own first name sits in a README and a memory body:
names are environment-specific and are not in a default pattern list. Add your own names to the
patterns; fresh agents catch what remains.

## Dropping an instance file can gut the skill

A skill can keep its entire how-to in a companion instance file, so excluding that file leaves a
SKILL.md that says "render it and look" and never names a browser. Nothing errors and the sweep
passes. After excluding a companion file, read the parent skill and confirm it still says how to do
the thing.
