# Part 2 — artifacts that asserted false confidence (from `no-fabricated-certainty`)

Part 2 of the [instrument-failure case files](../instrument-failures.md). Load it when a report,
dashboard, alert, caption or computed figure is about to ship: every shape here is an artifact that
rendered a confident value where it had none — a missing measurement, a remembered threshold, a
label wider than its query, a denominator from somewhere else.

The shapes below were each shipped, and each caught by a human or a peer rather than by its author.


- **A missing measurement rendered as an ordinary one.** A probe that timed out stored
  `pending = 0`, which on a status page is indistinguishable from "nothing pending".
  Render unknown as unknown (`—` with a tooltip), never as a number, and never let an
  absent field mean "fine". The whole failure class is *falsely clean*: a broken update
  mechanism and a fully up-to-date service look identical unless you go out of your way to
  distinguish them.
- **Unsourced and source-not-checked look identical in the artifact.** The rule is "every threshold
  traces to a citable source, *or* the row does not ship" — and the first branch is the one that
  gets skipped. A specific statistic was deleted from a skill as unsourced when its citation sat in
  that same skill's own references file. **Search the evidence base before dropping a claim, the
  same way you would before adding one** — deleting a sourced fact is a real loss, and it reads as
  diligence.
- **A threshold written from memory.** Asked for "which services are behind on X", I wrote
  fixed-version numbers for three libraries from recollection and used a fourth from an
  advisory for a different library. It reported fully-current services as vulnerable.
  Every threshold must trace to a citable source, or the row does not ship.
- **A LABEL that names a narrower subject than the query behind it.** Three times in one day, by
  three different sessions: a grep run in one repo captioned as a fact about "either repo"; a
  read of one user's home reported as "this box has never had a graphical login"; and a pipeline
  waiter polling `--branch` printing a header that named a specific commit it had never queried.
  In all three the command was correct and returned the truth *about what it asked*. The falsehood
  was manufactured by the annotation wrapped around it. This is the most dangerous shape in this
  file because it survives review — the evidence is real, so anyone checking the output finds it
  sound, and only someone who re-reads the label against the query notices. Two of the three were
  caught by the raw value sitting next to the caption and contradicting it; one shipped into a
  published MR. **Write the label from the command you ran, not the question you meant to answer** —
  if the query said `--branch`, the caption says branch; if you read one home, the claim is about
  one home.
- **A comparison between incomparable things.** The same feature compared a backup agent's installed `3.2.0`
  against the latest release, build `4108` — the project had moved from bare build numbers to
  semantic versions — and concluded "behind" because 3 < 4108. When two values may not be on the same scale, detect that and
  say "cannot compare"; a direction guessed from mismatched units is worse than a gap.
- **A count with no denominator is not a measurement, and supplying the denominator yourself
  is the trap.** A peer reported a count of unmatched records; I paired it with a corpus size
  taken from a *different document*, got 2.5%, and shipped an alert threshold at 5%. The real
  denominator was far smaller — a truncated tuning run against a stub configuration — so the
  true figure was 80% and the rule would have fired permanently from its first evaluation.
  Nothing looked wrong: both numbers were real and the arithmetic was correct. **Ask what a
  number is a number *of* before it becomes an input; a numerator and a denominator from two
  sources are two facts about two populations.** Same reflex when *choosing* a denominator —
  prefer the one whose members had the chance to be in the numerator (records *processed*,
  not records *ingested*), or a partial run dilutes the ratio and it reads healthiest
  exactly when it is worst.

- **A BOUND used as a value, and the caveat quoted on the way past.** A model-produced citation
  count is a floor with no denominator. I wrote that in those words, quoted the source saying it,
  and three messages later compared the floor (16) against the bar (20) and called the class
  unsupported. Measured, it was 29. **Restating a warning discharges the felt obligation to act on
  it** — the caveat reads as *handled*, so nothing flags the comparison that ignores it, and the
  error arrives wearing the authority of having acknowledged the risk.

- **A statistic that cannot express the distinction it was added to make.** A product-returns
  report displayed returns-per-customer to separate "a defect hitting many buyers" from "a few
  customers sending things back repeatedly" — and used a MEAN, which collapses exactly those two
  cases into one number. Its own page said the distinction mattered, in those words, beside a figure
  incapable of showing it. The median was 1 on every row. A plausible summary statistic sitting
  beside a correct description of its purpose is very hard to see. Worse, the same investigation
  found the mean was measuring the wrong population: most returns for the bulkiest products were
  booked through one wholesale partner's account, so the "customer" was not the buyer, which made
  the figure point the OPPOSITE way on the largest rows. The ratio was arithmetically correct
  throughout.

- **A per-item value that is suspiciously UNIFORM across independent items is the instrument,
  not the world.** A dashboard showed most of its problem classes "first reported" in the
  same month, with a hard floor at one date, over a corpus spanning years. The code was
  right — `min(created)` over each class's member records — but the classification pass ran
  newest-first and had only covered the recent slice, so a boundary of the *run* leaked into a
  per-class *measurement* and rendered as a fact about the world. Item counts and reporter counts
  varied normally, which is why nothing looked wrong at a glance; dates were the one column
  where independent things agreed too closely. Same signature as a `—` column, an unresolved
  identifier repeated everywhere, or every row reporting one site. **Tests cannot catch this
  class: the computation is correct and the interpretation is false.** Only reading the
  rendered output as claims about the world finds it — and note that the author had rendered
  and looked at that page without seeing it, because they were checking layout.

- **`payload.things || []` converts a contract mismatch into an empty success, seven times in one
  project.** A client and a server were each internally consistent and each wrong about the other:
  the response envelope key, an entity/observation split, unit-bearing field names, a shared type nested
  under `thing` in three result shapes, a cell key, a collection key plus its units (`size_m`
  against the contract's `size_km`, a factor of 1000). Every instance rendered as a working
  application holding no data — the "quiet page" — and every instance was invisible to a full green
  suite of ~200 tests, because each half was tested against its own idea of the contract and nothing
  compared the two.

  **The defaulting idiom is the whole mechanism.** `x || []`, `x ?? []`, `.get(k, [])`,
  `getOrDefault(k, emptyList())` are all written for a real reason — the field is sometimes absent —
  and each one silently absorbs the case where the field is absent *because you spelled it wrong*.
  Those two cases deserve opposite handling and the idiom cannot tell them apart. The fix that
  worked was a single `itemsOf(payload, label)` helper that THROWS on a missing collection key, so
  a mismatch is loud at the first render instead of quiet forever.

  Three things worth carrying:

  - **Ask what makes the default legitimate before writing it.** Defaulting a field the contract
    marks optional is correct; defaulting a field the server never sends under that name is a bug
    wearing the same syntax. The schema's `required` list is the discriminator, and it is one read.
  - **Checking that the ENDPOINT exists does not check that the FIELDS do.** A path-level contract
    test caught three missing routes and zero of the six field-level mismatches. Both halves are
    cheap and they are different tests — the field half needs the response schema, not the route
    table.
  - **A green suite is evidence about each half separately.** Where two artifacts must agree, the
    agreement needs its own check, derived from one machine-readable source both sides can be
    compared against (an OpenAPI schema, a generated client, a shared IDL). Two hand-maintained
    beliefs about one contract will diverge, and nothing in either codebase will notice.

- **When two sources feed one view, the working one hides the broken one.** A half-full panel
  reads as working; an empty one gets investigated. So a collector, version or site that stopped
  reporting is invisible inside an aggregate the others keep populated. Check with a `GROUP BY` over
  the source (`count(*) filter (where <field> is not null)` per collector/version), and carry a band
  on the view naming what was measured against what.
