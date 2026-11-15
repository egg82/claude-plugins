# How changes land, and steering the agent

Load when planning a refactor or consolidation, writing a repo's CLAUDE.md, setting up an orchestrator over writers, or
deciding who edits the shared docs. Queue layout on a forge: `references/forge-queue.md`. (SKILL.md §7 and §8.)

## 7. How changes land

- **Structure and behaviour in separate commits.** A refactor, port or move lands byte-identical first,
  proven by identical fixtures, frames, `openapi.json` or hashes. Any fix found on the way is its own
  later commit with its own test.
- **Pin before you split.** Run a mutation pass on the code about to move and add directed tests for the
  survivors, in the commit before the split. The split is then checked by tests already proven able to
  fail; in one agent-built app, existing tests had missed 50 of 73 such mutants.
- **When patches pile up, re-plan or delete.** About ten patches to one behaviour mean the design can't
  express the requirement. Re-specify in prose and replace, keeping the old bug detectors as acceptance
  tests. A third cosmetic tweak to the same feature asks "should this exist?" Several fix chains in
  Repo A ended in deletion.
- **A consolidation runs in phases**, each shipping alone and deleting one named copy, with explicit
  licence to delete cosmetic compatibility paths.
- **Ceremony scales with the task.** A new system gets interface first, a design note with "Rejected,
  and why", then an implementer and a blind test writer in parallel worktrees, with ambiguities logged to
  a gaps file. A one-sentence change just gets made, with its test.

## 8. Steering the agent

- **CLAUDE.md is a short router plus the few rules that must fire every session.** Both repos' are under
  sixty lines. Detail lives in the docs it points to (`docs/engineering.md`, `systems.md`,
  `decisions.md`). Context files cost tokens on every request and help mainly with a repo's non-standard
  rules.
- **Rules arrive right after an incident**, one sentence plus a pointer to the decision that owns the
  detail. Superseded decisions stay in place with a dated note.
- **One queue kept true**, swept against the code periodically for done or never-built claims. On a forge
  it is the forge's issues, labels and board, and an MR closes its issue; `docs/open-work.md` only where
  there is no forge. Cite an issue by number, never a position in the queue. Layout, and moving a queue
  file onto the forge: `references/forge-queue.md`.
- **When an agent errs, engineer it out.** Add one context-file line naming the bad behaviour, plus a
  check or script the agent runs into; a must-happen action goes in a hook. A rule that already failed
  once as prose is escalated, not restated.
- **The default shape for real work is an orchestrator over subagents.** Real work means anything that
  touches structure, adds a kind of thing, or spans more than one queue item. The orchestrator holds the
  plan, the rules and the conformance review, and never fills its context with implementation. Writers
  each start fresh on one item, and a separate agent writes blind tests. The value is the separation,
  not parallelism: overnight on one large rework, the orchestrator caught its writers' behaviour change in a
  structure commit, a ledger workaround and a shared database, all of which a single agent would have
  waved through in its own work. A change you can state in one sentence that the gates already cover
  just gets made, with its test. Mechanics are in `fanout-craft`: one task per fresh agent from the
  queue, writers capped at 2-3, each in its own worktree and database. The gates are what make
  parallel writers safe in one repo; without them, keep to one writer.
- **The orchestrator alone edits the shared single-file docs** (the systems inventory, a decisions index, the
  queue, `CLAUDE.md`, `engineering.md`). A writer ends its report with a doc delta, the exact rows and lines to
  change, and the orchestrator applies it at merge, after rebasing. Parallel writers editing those files collided
  at every merge in one repo, and the workaround (bullets instead of table rows, so fewer lines conflict) bloated its
  inventory to nearly a thousand lines. A writer still edits a decisions file it owns outright (where decisions are split per system), and may fix a
  backticked citation mechanically when it renames what the citation names, so its own citation gate stays green.
- **Written scope rules don't cap agent-accelerated scope.** Repo A's own decisions said "scope it
  tightly" and it reached hundreds of commits in days. Scope is the human's call, made per item.
