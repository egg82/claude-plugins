# Fanning out and delegating searches (§3)

Load when issuing a set of query variants, or when handing searching to a subagent (the brief is the
only channel that reliably carries constraints).

## 3. Fan out in parallel — for coverage, not for ranking

### If you delegate the searching, put the constraints in the brief

A substantial fraction of research subagents never open this skill even though every one of them saw
it listed. A subagent is a fresh context that may or may not open a skill, so anything load-bearing
has to travel in the prompt you write. (The measured rate is instance data and lives in
`references/tool-routing.md`, where it can be re-measured; naming a subagent's *brief* as the fix is the durable
part.)

So **name this skill in the brief**: *"Load the `search-craft` skill before searching."* One line,
carries every rule, and never drifts out of date — unlike constraints copied into a prompt, which
stop matching the skill the moment it changes.

Evidence the brief is the channel that works: in that session the briefs carried "independently
re-check," "primary sources only" and "do not fabricate," and those behaviours show up plainly in
the output. What lived only in the skill reached two-thirds of the agents.

### Variants

**One query sees a small fraction of what exists.** Two professionals given the same question overlap
~0.27 on terms and ~0.17 on results; ~61% of the relevant items they find are found by exactly one of
them. There is no "obvious" phrasing.

**Issue several genuinely different formulations at once and take the union.** Cheap for you,
laborious for a human — it's what browser tabs are for. Vary along **two** axes:

> **Measured, and it holds:** across 39 real research runs the median agent issued **~6 searches
> before opening a single page** (`SSSSSSSSSSSSFF` is the typical shape), and only 9 of 39 opened a
> page after one search. The behaviour this section asks for is one of the few that is already
> reliably happening — you are reading listings across the whole variant set before committing to an
> article, which is exactly the point.

- **Register** — vendor term vs symptom vs error string vs community slang vs academic phrasing.
- **Specificity** — deliberately run one broader and one narrower than your best guess. You don't
  know which rung of the ladder the answer is written at.
- **Abbreviated vs spelled out** — `k8s` and `kubernetes`, `MTU` and `maximum transmission unit`. Some communities abbreviate and some don't; both sets are legitimate
  and they overlap less than you'd expect. This is the cheapest variant axis there is.

Refine the whole set together rather than perfecting one query before starting the next.

**Don't write `(a OR b) AND (c OR d)`.** That's machinery for unranked Boolean corpora and is inert
against a web ranker. The web translation of "OR within a concept" *is* this section: separate
queries, unioned after.

**Don't rank by agreement between variants on the same engine.** Fusing multiple runs of one system
measures worse than taking the best single run. Agreement across genuinely *different indexes* is the
validated case. Never let agreement raise your confidence in a claim — judge each result on its
merits.
