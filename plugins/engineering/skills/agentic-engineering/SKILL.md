---
name: agentic-engineering
description: "How to keep an agent-written codebase well-designed — structural gates, held ledgers, decoupling, a fit pass before new systems, LLM behaviour kept in code. Use when starting or restructuring an agent-built app, a god object or file, adding tests to untested code, writing a repo's CLAUDE.md or engineering doc, an agent loosened a threshold, setting up a repo's queue on GitLab/GitHub issues and boards, or asked how to do agentic / vibe-coded development well."
---

# Agentic engineering

**The aim behind every rule: make bugs hard to create and easy to find.** Small functions, narrow
interfaces, named systems and decoupling patterns are how that aim looks in code. They are not goals in
their own right; a pattern earns its place by making a class of bug impossible or obvious.

**The measured fact the method rests on:** agent-written code erodes as the agent extends it, and quality
guidance in the prompt lowers the starting level without changing the rate of decay. Only structural
checks hold. Evidence and citations: `references/evidence.md`. Case files: `references/cases.md`.

## Which reference

| Situation | Load |
|---|---|
| Repo already breaks a size/type/boundary rule; two branches conflict on a ledger; a count or check is being raised or loosened | `references/held-ledgers.md` |
| Splitting a god file; writing `docs/systems.md`; layering or citation gate; commenting rule | `references/structure.md` |
| Fit pass found a candidate pattern; decoupling a shared system | `references/patterns.md` |
| Adding tests, blind test writer, mutation audit, CI time budget | `references/tests.md` |
| Refactor or consolidation plan; writing CLAUDE.md; orchestrator over writers; who edits shared docs | `references/steering-and-landing.md` |
| Queue on GitLab/GitHub issues, labels, boards | `references/forge-queue.md` |
| A model decides or writes something at runtime; LLM-labelled corpora | `references/llm-in-product.md` |
| Merging a writer's MR | `references/reviewing-rework.md` |
| Adopting this in an existing repo | `references/rollout.md` |
| Past incidents and measured evidence | `references/cases.md`, `references/evidence.md` |
| Gate/ledger/doc skeletons to copy | `templates/` |

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
- **Gates guard correctness, honesty and order; taste is a readout.** A design remark about feel ("this
  loop feels tedious") is a "more or less" idea: make it a readout that reports, never a hard
  gate. Turned into a structural ban it outgrows its intent and designs bend around its letter. Before gating a design remark, ask
  which of the three it guards.
- **Never raise a held count or loosen a check to get a change through** (agents did it twice in
  one repo; the real cause was a fixable regression). Put the line in the repo's CLAUDE.md and every
  worker's brief. Ledger mechanics: `references/held-ledgers.md`.
- **Never gate behaviour on regex over natural language.** Put a field where the text is authored, or a
  structured field in the model's output; word matching is only for flagging something to a human
  (many misfiring places in one repo). More: `references/llm-in-product.md`.

## 2. Held ledgers: adopting rules in code that already breaks them

New code starts with an empty held list that stays empty. Existing code freezes today's violations in a
**per-file ledger** that may only shrink: per file and kind (never one global count), failing in both
directions (over the count, or stale and needing lowered). Parallel writers' merge rules, forks,
suppressions and the templates: `references/held-ledgers.md`.

## 3. Structure

- **Small files, each doing one thing, grouped in subdirectories**; split before a file passes a few
  hundred lines. **Function size has its own gate: 80 lines, held.** Test files count toward the file-size
  gate. Systems inventory, layering allow-list, one home per fact, static types, comment rule: `references/structure.md`.
- **Fit pass before any new kind of thing** (a system, new data, a new schedule): what is it an instance
  of, which row of the systems inventory already does that, and which known pattern solves it (GoF,
  *Game Programming Patterns*, §4: these are worth checking before inventing a shape)? Extend or merge;
  build new only when nothing fits, and say why on the work item ("Fits into: …"). Without a fit pass,
  agents build "systems in hiding": the same rule hand-copied two to four times, drifting apart.
- Skeletons for `CLAUDE.md` and `docs/{engineering,systems,decisions}.md` (plus `open-work.md` for a repo with no forge): `templates/project-docs/`.
- **Comments where an implementer needs them, and almost nowhere else**: API surfaces carry their contract,
  implementation code only the rare "looks optimizable but isn't, because…"; history goes in the commit
  and decisions doc. Put the rule in every writer's brief.

## 4. Patterns, by fit

**Judging the fit matters more than the pattern.** Repo B planned a service locator, event queue,
observer and double buffer, and built none of them; it built Command, Type Object and a small state
machine, because those were what the work needed. The catalogue (Command, Type Object, service locator
with Null Object, queues, explicit fields over shape-sniffing, and the don'ts): `references/patterns.md`.
Record rejected patterns with the reason.

## 5. Tests

Tests from the agent that made the change are weak (dozens of surviving planted mutants in one large suite). **One suite
per contract, written blind** by a different agent given only the interface; depth follows risk; simulations run
nightly; prove a suite can fail with planted mutants. **Bug hunts land findings-first:** a strict xfail
asserting the wanted behaviour, then the fix in a separate commit that flips it. Detail: `references/tests.md`.

## 6. A test budget from the first test

State the scope and a per-PR wall-clock budget at project start (a CLI under 2 min; an app with an API about 5),
anchored on an outside figure, never the suite's own history; budgets are wall clock including setup and
waiting. Detail and the per-test ceiling gate: `references/tests.md`.

## 7. How changes land

**Structure and behaviour in separate commits**: a refactor, port or move lands byte-identical first, proven by
identical fixtures or hashes. **Pin before you split** (mutation pass, directed tests, in the commit before).
**When patches pile up (about ten), re-plan or delete.** Ceremony scales with the task. Detail:
`references/steering-and-landing.md`.

## 8. Steering the agent

CLAUDE.md is a short router plus the few rules that must fire every session. When an agent errs, engineer it
out (a context-file line plus a check; a must-happen action goes in a hook). The default shape for real work is
an orchestrator over subagents, and the orchestrator alone edits shared single-file docs. One queue kept true
(`references/forge-queue.md`). Detail: `references/steering-and-landing.md`.

## 9. LLMs inside the product

A stateless call can't keep a rate (seeded rolls in code, numbers in a data file). Never gate behaviour on words
in prose. A quoted example in a prompt becomes the template. LLM-labelled data kept over time fails silently.
Detail: `references/llm-in-product.md`.

## Reviewing an agent's rework, and rolling out to an existing repo

Review a writer's MR for conformance to a ten-item checklist, not taste (`references/reviewing-rework.md`).
Adopt in an existing repo by measuring first, a docs-only pass, then gates seeded at today's counts, never a
big-bang refactor (`references/rollout.md`).
