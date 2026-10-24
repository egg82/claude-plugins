---
name: agentic-engineering
description: "How to keep a codebase that coding agents write well-designed — small single-purpose functions and files, decoupling patterns, no god objects — via structural gates and held ledgers, a fit pass before new systems, tests proven able to fail, and LLM behaviour kept in code. Use when starting or restructuring an agent-built app, a file or function has become a god object, adding tests to untested code, writing a repo's engineering doc or CLAUDE.md, an agent loosened a threshold, or asked how to do agentic / vibe-coded development well."
---

# Agentic engineering

**The aim behind every rule: make bugs hard to create and easy to find.** Small functions, narrow
interfaces, named systems and decoupling patterns are how that aim looks in code. They are not goals in
their own right; a pattern earns its place by making a class of bug impossible or obvious.

**The measured fact the method rests on:** agent-written code erodes as the agent extends it, and quality
guidance in the prompt lowers the starting level without changing the rate of decay. Only structural
checks hold. Evidence and citations: `references/evidence.md`. Case files: `references/cases.md`.

## 1. A rule that can be a gate is one

- **Prose rules drift; gated rules hold.** In repo B the gated rules held: function size, and the
  engine importing nothing but itself. The ungated "update the inventory in the same change" rule drifted
  until the inventory said "nothing is built yet" over shipped code.
- **Every gate proves it can fail**, in the same change that adds it: a planted violation goes red (a
  committed `PLANT` then revert, or a control case inside the test), and the gate asserts it saw a
  non-empty input. A gate that scans nothing passes forever. The craft of that is `verification-gate`.
- **Every defect becomes a permanent guard**: the fix lands with the test or check that would have caught
  it.
- **A gate checks structure, never the wording of prose.** Code, paths, symbols, counts and
  explicit markers inside backticks can be checked; sentences cannot. A regex that fails CI on a
  phrase in a doc ("Done:", "used to") misfires, gets worked around by rewording, and teaches agents
  to write for the regex. Prose conventions are enforced in review. Word scans are fine as a
  *flag* for a reader, never as a pass/fail. This one is a hard line, not a default to weigh.

## 2. Held ledgers: adopting rules in code that already breaks them

New code starts with an empty held list that stays empty. Existing code cannot meet the limits on the
day the rule arrives, so freeze today's violations in a **per-file ledger** that may only shrink.

- **Per file and kind, never one global count.** A global count lets a fix in one file pay for a new
  violation in another. Repo A proved that with a planted swap.
- **Fail in both directions.** Over the held count, or new, fails naming the file. Under it fails too,
  as "stale, lower it", so the ledger always equals the code.
- **Parallel writers conflict on the ledger at every merge.** Take neither side whole: apply each
  branch's per-file delta (its ledger minus its merge base's) onto the target's, check no file or rule
  rose, then set the final counts from CI's "stale, lower it" output. A split moves counts between
  files, so it may re-seed only when no pre-existing file rises in any rule. (One repo's rework
  merged a dozen branches this way; taking one side whole silently undoes the other's reductions.)
- **Never raise a held count to get a change through.** Agents did it twice in repo A, and both times
  the real cause was a fixable regression. Put this line in the repo's CLAUDE.md and in every worker's
  brief. A Stop hook can enforce it (`held-ledger-raise-gate.sh` in this setup).
- **Nor make the code worse to stay under a limit**, e.g. by cramming lines, deleting explanatory
  comments, or moving SQL work into Python to save a line. No count rises, so only review sees it. Pay
  with a real reduction, split the file, or report it.
- **A suppression is a fix the count can't tell apart:** `# pyright: ignore`, `# noqa` and `typing.cast`
  all remove an error the way a fix does. Each one names its rule and a reason on the same line, and the
  suppressions are counted in their own held ledger. Never cast a value to quiet a *safety* type (e.g.
  `cast(LiteralString, f"…")` defeats psycopg's SQL-injection guard); fix the types instead.
- Templates in `templates/`: `held_ledger.py`, `test_function_size.py`, `test_file_size.py`,
  `pyright_gate.py`, `conftest_time_gate.py` and `test_boundaries.py`, each with its own controls and
  setup notes. Copy them, set the package path, seed with `--write`, and commit the ledger with the gate.

Using ledgers, one repo roughly halved its raw SQL calls outside `db/` while still shipping
features. The same mechanism holds pyright errors: adopted with over a thousand errors, it was tractable.
That backlog was only tractable as a ratchet.

## 3. Structure

- **Small files, each doing one thing, grouped in subdirectories, frontend and backend alike.** A file
  is a group of functions with one purpose, not a feature's worth of everything. Split before a file
  passes a few hundred lines. That rule plus an immediate split took repo A's entry-point file from several
  hundred lines to a handful. The split files never regrew.
- **Small files don't stop long functions.** Function size needs its own gate: 80 lines, held.
- **Fit pass before any new kind of thing** (a system, new data, a new schedule): what is it an instance
  of, which row of the systems inventory already does that, and which known pattern solves it (GoF,
  *Game Programming Patterns*, §4: these are worth checking before inventing a shape)? Extend or merge;
  build new only when nothing fits, and say why on the work item ("Fits into: …"). Without a fit pass,
  agents build "systems in hiding": the same rule hand-copied two to four times, drifting apart.
- Skeletons for `CLAUDE.md` and `docs/{engineering,systems,decisions,open-work}.md`: `templates/project-docs/`.
- **A systems inventory** (`docs/systems.md`): each system's one question, where it lives, its pattern,
  its callers, and known duplicates with the phase that removes them. Something counts as a system only
  if all four hold: many callers across packages, one question behind a narrow interface, a plausible
  second implementation, and it owns policy or state rather than a data shape. Everything else is a
  plain import. **Gate the inventory with a citation test:** every backticked path and
  `module.symbol` in it must resolve by real import, with a floor on how many it finds (the shape of
  a `test_doc_citations.py`). Give planned references an explicit marker that
  is skipped while the target is missing and **fails once it exists**. Otherwise writers drop the
  backticks to get past the gate, and the reference silently stops being checked.
- **Package layering as an executable allow-list.** A new import edge fails until it's added, which is
  the moment the design question should be asked.
- **One home per fact.** A value the server and the client both need lives in one data file, or is
  served. Generated files never share a directory with hand-edited ones: a file's location says what
  it is.
- **Static types, checked.** Annotate even where it is verbose, and make a checker (pyright/mypy, tsc)
  gate CI. Annotations nothing checks drift into claims.
- **Comments where an implementer needs them, and almost nowhere else.** API surfaces (interfaces,
  public functions, wire models) carry their contract and purpose. Implementation code carries only
  the rare "this looks optimizable but isn't, because…". Decision history and bug stories go in the
  commit and the decisions doc, where they don't age in place. Agents, Opus especially, narrate
  history into comments, so the rule goes in every writer's brief and the review. As a reference
  shape, a hand-written Java service is 22% comments in its API module and about 1% in implementation;
  one agent-written app was 29% everywhere.

## 4. Patterns, by fit

GoF and Nystrom's *Game Programming Patterns* (read the chapter, not a summary) apply far beyond games.
**Judging the fit matters more than the pattern.** Repo B planned a service locator, event queue,
observer and double buffer, and built none of them. It built Command, Type Object and a small state
machine, because those were what the work needed.

- **Command** for user actions: frozen records in one closed union behind one `decide()`. Replay,
  logging and automation come free.
- **Type Object and data files** for content: a new kind is data, not a class.
- **Service locator only for real systems** (sound, map, clock, catalogue), each behind one interface
  with a Null Object default; callers go through the locator and never import the implementation.
  **Every entry point must wire it, deploy checks and tools included.** A Null Object silently turns
  missing wiring into plausible wrong answers (repo A's deploy check reported failures the live app
  doesn't have).
- **Queues and double buffers** to decouple a producer from its consumers, worker pools draining a queue
  included. Leaf helpers stay plain imports.
- **Replace shape-sniffing with explicit fields** (Type Object or Specification). A frozen record with
  `source`/`kind`/`part` let a dozen code paths merge into one owner.
- **State that is a function of history plus a date** stays a pure query passed in, not a global
  service.
- **Template method plus per-variant strategy (an abstract updater class) needs a second extraction
  once variants converge.** Two 199-line updaters that differ in one enum argument should be one generic
  base.
- **Don't:** singletons or module globals for shared systems; god objects, or one object's fields shared
  across many mixins (that's coupling spread out, not decoupling); inheritance trees for content kinds.
- **Record rejected patterns with the reason**, and the "looked at, and fine" verdicts, so the next agent
  doesn't propose them again.

## 5. Tests

- **Tests from the agent that made the change are weak.** A mutation audit of a large
  agent-written suite found dozens of surviving planted mutants. Agent-written fix tests showed no effect on
  outcomes.
- **Blind contract tests:** a different agent, given only the interface and the contract, never the
  implementation, writes the tests. In repo A that found a real undo bug the implementation-aware
  tests missed. Interface-first designs (an API module of interfaces) make this cheap. **This is the best use
  of an agent for someone who designs well and dislikes writing tests.**
- **Property tests from the stated contract** find real bugs (56% of LLM-written reports valid in a
  100-package study). Run a fast profile on every push and a deep one on a schedule.
- **Prove a suite can fail:** plant a written list of wrong implementations (`MUTANTS.txt`), add directed
  tests for the survivors, and record equivalent mutants with the reason no test can tell them apart.
- **Bug hunts land findings-first:** each finding is committed as a strict xfail asserting the wanted
  behaviour, then fixed in a separate commit that flips it.
- **When an interface removes or renames a type, port the existing suites in the same change.** A suite
  that no longer imports doesn't go red; it silently stops collecting (about 90 contract tests did).

## 6. Fast from the first test

Repo A's suite grew slow and was sped up after the fact with shards, a durations file and CPU
requests. Make speed a gate while the suite still runs in seconds:

- **A per-test ceiling with a held list that starts empty** (`templates/conftest_time_gate.py`). Set the
  ceiling from measurement plus headroom. Speed the test up or split it; never raise the limit.
  **Measure CPU seconds, not wall seconds**: a wall-time gate fails fast tests on a slower CPU type or
  an overloaded runner, and a gate that cries wolf gets switched off. CPU time still drifts when a
  lazily built shared cache charges whichever test fills it first, and on a swapping host; the
  template's docstring says how to handle both.
- **Whoever writes a test makes it fast before committing it**: run it under the gate and read the
  slowest durations. The usual agent-made cause is quadratic re-computation, such as re-simulating from
  time zero for every sample. Carry state forward instead.
- **Test jobs run in a prebuilt image** with dependencies installed, rebuilt only when requirements
  change, so no job spends its first minute on `pip install`.
- **Mutation runs need per-test timeouts**, thread-based: about 1 in 10 mutants hangs. (Worker counts
  when several agents test on one host: `fanout-craft`.)

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
- **One queue file kept true** (`docs/open-work.md` or the repo's equivalent), swept against the code
  periodically for done or never-built claims.
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
- **Written scope rules don't cap agent-accelerated scope.** Repo A's own decisions said "scope it
  tightly" and it reached hundreds of commits in days. Scope is the human's call, made per item.

## 9. LLMs inside the product

- **A stateless call can't keep a rate.** Frequencies are seeded rolls in code, with the numbers in a
  data file; the prompt says what this one call does.
- **Never gate behaviour on words in prose.** Regex over natural language misfires ("ash" in "cashier",
  "fine" read as a penalty word; 17 places in one repo). Put a field where the text is authored, or a
  structured field in the model's output; word matching is only for flagging something to a human.
- **Have the model emit structured fields when it writes**, and let code re-check them later. Never
  re-ask a model whether a stored line still holds.
- **Variety comes from code** (a seeded lens per call, shuffle-bag pools), not personas or "avoid
  clichés". Pick the model per output kind by a blind batch; the biggest model came last on the shortest outputs.

## Reviewing an agent's rework

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
   code, with a planted-mutant run or a red-first commit, not just a green suite.
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
    the MR's "PG 17". In one repo, CI on postgres:16 passed a migration that 17 rejected at CREATE
    INDEX (index functions run under a restricted search_path), and the api rollout crashlooped.

Report findings as pass, or as concrete defects with file and line. A clean MR gets one line.

## Rolling this out to an existing repo

1. Measure it: functions over 80 lines, files over ~300, pyright errors, slowest tests, import hubs.
2. Write `docs/engineering.md` with the repo's rules, pointing at the ledgers for the numbers rather
   than a dated table (the table goes stale with the first split).
3. Add the gates with ledgers seeded at today's counts, each with its controls, in CI.
4. Trim CLAUDE.md toward a router: the house rule, "never raise a held count", the fit pass, and
   pointers.
5. Queue the worst offenders as backlog items, each split byte-identically when touched. Don't start
   with a big-bang refactor.
