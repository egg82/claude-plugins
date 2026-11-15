# Reviewing an agent's rework

Load when an orchestrator is about to merge a writer subagent's MR, or briefing a fresh reviewer agent on a code change.

Review against these rules, not against taste. A reviewer told to "find anything" always finds
something, and acting on it adds layers. This is the check an orchestrator runs on each writer
subagent's MR before merging it, or hands to a fresh reviewer agent: **conformance** to the items
below, the repo's `engineering.md` and `systems.md`, and the owner's decisions. The writer's own tests
and gates carry correctness. A reviewer that drifts into general review lengthens every merge loop,
so mark anything beyond these items non-blocking. Read the MR diff, its pipeline, and the ledger diff:

1. **Ledgers only went down**, and the held JSON matches a `--write` run on the merged tree.
2. **A new gate shipped with its controls** (planted failures, a non-empty-input assert), and the
   MR or its commits show the plant going red.
3. **A split is byte-identical**: the MR names its proof (identical outputs or hashes, the same test
   results), and no behaviour change rides along in the same commit.
4. **Tests are blind and can fail**: written from the interface by an agent that didn't write the
   code, with a planted-mutant run or a red-first commit, not just a green suite. One suite per
   contract: the writer added no duplicate, and test depth matches the code's risk tier.
5. **The design moved toward fewer, narrower things**: net lines down or flat for a refactor, no new
   parallel system (a fit pass shows on any new kind of thing), and patterns where they remove a
   class of bug, not as decoration (no new locator for something with one caller).
6. **A split narrowed what the files share**, not just their sizes. Count shared mutable fields and how
   many files write each; a byte-identical split can turn one closure's state into an object written
   from ten files. The fix is an owner with named transitions and a held gate on writes outside it. An
   owner made of per-field setters gives traceability, not decoupling, and a setter that takes a field
   name is a door around the gate. (Case: `references/cases.md`, the JS split.)
7. **No defensive layers** were added for cases that can't happen, no thresholds were loosened, and no
   history was narrated into implementation comments.
8. **A release needing a second step names who takes it, and when.** If merging deploys, and the
   change also needs a step outside the merge (pushing scripts to another system, a hand-run
   migration, a config flip), the MR says who does it and merges only when that person is ready to
   do it straight away. Check the MR's claim about the gap against the repo's own rules, not its
   description. In one repo, a change merged without its out-of-band step broke production
   while the MR described a harmless gap.
9. **Docs follow the repo's conventions**, checked by reading, since prose isn't gated. A finished
   queue item is deleted, not marked done. A decision states what is true now. No doc restates
   another doc's subject.
10. **CI ran on production's runtime.** For any migration, query, or engine-specific SQL, the CI
    database (and interpreter) is the same major version production runs. Read both, don't trust
    the MR's version claim. In one repo, CI one major version behind production passed a migration
    production rejected at CREATE INDEX (index functions run under a restricted search_path), and the api rollout crashlooped.

Report findings as pass, or as concrete defects with file and line. A clean MR gets one line.
