# What is measured about agent-written code

This summary is condensed from a survey made in another project, after hours of
discussion in a session there. The survey itself kept one record per source. That survey read abstracts and vendor
pages, not full papers, so treat these numbers as leads: check the paper before quoting one.

## Measured

- **Agent code erodes as the agent extends it, and prompting doesn't stop it.** SlopCodeBench (arXiv
  2603.24755) ran 15 agents extending their own code under changing specs. Erosion rose in 77% of
  trajectories, and quality guidance in the prompt lowered the starting level by up to a third without
  changing the rate of decay.
- **Agent-written tests during a fix change nothing** (arXiv 2602.07900). They were mostly print
  statements and had no effect on SWE-bench outcomes.
- **LLM-written property-based tests find real bugs** (Maaz et al., arXiv 2510.09907). 56% of reports
  were valid across 100 packages, and 86% of the top-ranked ones.
- **A fresh-context reviewer is only mildly better than self-review** (arXiv 2603.12123, injected errors).
  The gain was not significant.
- **Context files like `AGENTS.md` / `CLAUDE.md` don't generally help and cost 20% or more** (arXiv
  2602.11988). They help for a repo's non-standard rules, which is the case for keeping them a short
  router.
- **Multi-agent setups** gained 90% on Anthropic's research eval at about 15x the tokens. Nothing
  controlled exists for coding, which Anthropic says parallelises less.
- **Copy-paste overtook refactoring.** Across 211M changed lines (2020–2024), copied lines exceeded
  moved (refactored) lines for the first time in 2024, with ~40% fewer moved lines. This is secondary
  reporting; the original was not read.
- **Experienced developers were 19% slower with AI on their own repos while believing they were ~20%
  faster** (an RCT: 16 developers, 246 tasks, early-2025 tools). Measure; don't trust the feeling.
- **Writing executable tests before the implementation improved results** (LiveCodeBench/RepoEval), with
  the warning that incomplete or wrong tests give misleading feedback.
- **Not measured by anyone:** whether a blind test author (one that never sees the implementation) beats
  co-written tests. Anthropic's docs endorse the split; repo A has one anecdote of it finding a real
  bug.
- **Also not measured by anyone:** whether design docs, test-first, or planner/implementer/reviewer pipelines
  improve design quality. Measure them per project: mutation score of the contract tests, and the
  defects that escape to later bug hunts.

## What practitioners converge on

Anthropic's docs, Hashimoto, Willison, Beck, Böckeler, Huntley and the Thoughtworks Radar agree more
than they differ:

- checks the agent runs into (tests, types, linters as backpressure in the loop), not instructions it
  reads
- boundaries checked by machine (import and dependency tests, custom lint rules)
- tests from a different agent than the code, and tests proven able to fail (red first, then mutation)
- every defect becomes a permanent guard
- structure and behaviour in separate commits (Beck)
- cleanup as a standing pass over integrated code
- ceremony scaled to the task (heavy spec frameworks and swarms of parallel writers are on the Radar's
  caution side)
- reviewers scoped to correctness and requirement gaps
- **agent-friendly code shape:** simple code beats clever code in agentic contexts. Prefer functions
  over classes where nothing varies, no inheritance or magic, long descriptive names, and important
  checks kept local where the agent will see them.
- **when an agent errs, engineer it out:** a context-file line naming the bad behaviour, plus a script or
  check so the agent verifies itself (Hashimoto). A must-happen action belongs in a hook, not the
  context file.
- **one task per fresh-context session**, with a feature list the agent only flips the status of. JSON
  is preferred because models overwrite it less than Markdown. The named failure modes are one-shotting
  the whole app, declaring victory early, and marking done without an end-to-end test.
- **a nearly perfect verifier is the precondition for parallel agents** ("otherwise Claude will solve
  the wrong problem"). Parallel writers "collide, the merges are horrific", so default to one writer.
