---
name: no-fabricated-certainty
description: An artifact must never assert a value it does not have — a missing measurement rendered as zero, a threshold written from memory, or a comparison between incomparable things
metadata:
  type: feedback
---

A report, dashboard, test or check must never present a confident value where it has none — the
reader cannot tell a fabricated number from a measured one, so the artifact has to. Three shapes,
each shipped here and caught by a human:

- **A missing measurement rendered as an ordinary one** — a timed-out probe stored `pending = 0`.
  Render unknown as unknown (`—` with a tooltip); never let an absent field mean "fine". A broken
  update mechanism and a fully up-to-date service must not look identical.
- **A threshold written from memory** — fixed-version numbers recalled for "which services are behind"
  flagged a batch of current services as vulnerable. Every threshold traces to a citable source, or the row
  does not ship.
- **A comparison between incomparable things** — `26 < 2017` across a vendor's changed versioning
  scheme. Detect mismatched scales and say "cannot compare".
- **Two sources feeding one view** — the working one hides the broken one; a half-full panel reads
  as working. Count per source (`GROUP BY` collector/version) before trusting the whole.

**A caveat beside a number does not neutralise it** — the figure travels and the caveat doesn't. If a
measurement can't stand unqualified, fix the comparison or say "unproven" with no number. A bound
is not a value, and ask what a number is a number OF (cases: `verification-gate`'s
`references/instrument-failures.md` Part 2).

Before shipping a computed claim, ask what happens when the input is missing, stale, or on another
scale, and make each render *differently* from a real value. Prefer omitting a row to guessing its
threshold. When a check can only be right for some inputs, gate it and label the rest rather than
applying it everywhere. Incidents: `~/.claude/memory/evidence/no-fabricated-certainty.md`. Relates to
[[verify-dont-anchor]], [[prefer-subtraction]].
