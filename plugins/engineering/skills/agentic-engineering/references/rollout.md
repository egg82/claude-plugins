# Rolling this out to an existing repo

Load when adopting the method in a repo that already exists and breaks it.

1. Measure it: functions over 80 lines, files over ~300, pyright errors, slowest tests, import hubs,
   and CI wall time per job against a stated budget.
2. A docs-only pass before any code change: a consistency sweep of the doc layer against the code
   (every cited path and symbol resolves, every system that exists has a `systems.md` row) and
   against the doc conventions in `templates/project-docs/`. It is not a writing exercise. Its output
   is the inventory the fit pass reads, so later work extends an existing system instead of
   duplicating it.
3. Write `docs/engineering.md` with the repo's rules, test budget and risk tiers, pointing at the
   ledgers for the numbers rather than a dated table (the table goes stale with the first split).
   Queue "bring the suite to the current rules"
   (`verification-gate/references/suite-conformance.md`) as an item.
4. Add the gates with ledgers seeded at today's counts, each with its controls, in CI.
5. Trim CLAUDE.md toward a router: the house rule, "never raise a held count", the fit pass, and
   pointers.
6. Queue the worst offenders as backlog items, each split byte-identically when touched. Don't start
   with a big-bang refactor.

Ledger mechanics: `references/held-ledgers.md`.
