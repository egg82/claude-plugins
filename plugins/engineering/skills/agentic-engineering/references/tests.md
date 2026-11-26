# Tests and the test budget

Load when adding tests to a repo, designing a suite, setting CI time budgets, or briefing a blind test writer. Suite
audits and gate craft: `verification-gate`. (SKILL.md §5 and §6.)

## 5. Tests

- **Tests from the agent that made the change are weak.** A mutation audit of a large
  agent-written suite found dozens of surviving planted mutants. Agent-written fix tests showed no effect on
  outcomes.
- **One suite per contract, written blind:** a different agent, given only the interface and the
  contract, writes the tests, and the writer adds no duplicate. Isolation measurably helps; a second
  suite beside it is unmeasured (`references/evidence.md`). In repo A a blind suite found a real
  undo bug the implementation-aware tests missed. **This is the best use of an agent for a team that
  designs well and is short on test-writing time.**
- **Test depth follows risk, tiered once in the engineering doc** (the template's table): silent or
  data-losing logic gets behaviour-level tests first; glue one smoke test per entry point; UI
  render-and-look, never snapshots; one-off scripts none. In audited repos tests were about half of
  what agents wrote while most escaped bugs were unit-sized logic defects.
- **Simulations run nightly, readouts never fail.** One smoke route per PR, the full run on a label;
  very few escaped bugs needed a simulation to catch, while a nightly lane still caught regressions. A nightly
  red is read and queued the next day. Moving a suite there: `verification-gate`'s
  `references/suite-conformance.md`.
- **Property tests from the stated contract** find real bugs (56% of LLM-written reports valid in a
  100-package study). Run a fast profile on every push and a deep one on a schedule.
- **Prove a suite can fail:** plant a written list of wrong implementations (`MUTANTS.txt`), add directed
  tests for the survivors, and record equivalent mutants with the reason no test can tell them apart.
  Commit the script that plants them beside the list: plants left in scratch make a "before" score nobody can re-run.
- **Bug hunts land findings-first:** each finding is committed as a strict xfail asserting the wanted
  behaviour, then fixed in a separate commit that flips it.
- **When an interface removes or renames a type, port the existing suites in the same change.** A suite
  that no longer imports doesn't go red; it silently stops collecting (about 90 contract tests did).

## 6. A test budget from the first test

Repo A's suite grew slow and was sped up after the fact with shards, a durations file and CPU
requests. Make speed a gate while the suite still runs in seconds:

- **State the scope and a per-PR wall-clock budget at project start**, in the engineering doc (a CLI:
  under 2 min; an app with an API: about 5). Anchor it on an outside figure, never the suite's own
  history: a unit test costs milliseconds, 0.05 s at most. Hunts that compared a suite with itself made
  it faster by their own measure while the total never moved.
- **Budgets are wall clock and count setup, teardown and waiting**: each CI job's timeout is its
  budget, plus a per-test ceiling (`templates/conftest_time_gate.py`, held list starting empty). The
  CPU-only body gate this template used to be taught agents to move cost into fixtures, and passed a test waiting
  out a 5 s production timeout. Time in tests comes from an injected clock (`verification-gate` §7).
  Runner noise is real (unchanged tests swung from 1.0 s to 2.8 s between pipelines against a 2 s
  ceiling), so ceilings get generous headroom over millisecond tests, and a slow test is held with its
  own measured ceiling.
- **A time ceiling must not fail on one noisy sample, or it breeds flaky tests and rerun-until-green.**
  Speed is a budget, not correctness. A test over its ceiling is timed again once, alone. It fails only
  if it is over again; otherwise it is reported as slow. Most flaky reruns across three repos were this
  gate tripping at 1-8% over the limit (`cases.md`, "Flaky tests: our own gates"). When tests creep
  toward the ceiling, look for shared world setup redone in every test: loading all content, building a
  whole fixture world, or replaying from zero. Its cost grows with the project while the ceiling stays
  fixed. Build it once per process, keyed by its inputs, and prove no test mutates the shared copy.
  Never answer the creep by raising the ceiling.
- **Per-job timeouts do not bound a PR.** Jobs multiply, chains lengthen and queueing grows while every
  job stays under its limit, and no timeout goes red. The usual path is a computed "run X when a file
  it could affect changed" rule. Either the list grows until it names nearly every file, or the work
  moves inside what it covers. Either way the per-PR set quietly becomes the nightly set. Scope by what
  the change edits, not by what could reach it. Budget the PR's **critical path** (the sum of timeouts
  along the longest `needs` chain) and gate it. Under a runner limit, queueing is on that path too: a short job
  queued behind long shards adds their run to the wall clock, so start the short jobs first. An expensive suite runs on a PR only for the slice the
  change touches, and nightly in full. A red nightly holds the next deploy.
- **Key cached artifacts by the slice they depend on, never by everything.** One hash over all inputs
  means any edit rebuilds everything, on CI and in every local refresh. Key each slice by its own
  inputs plus the previous slice's key, and test both directions: an earlier change moves every later
  key, a later change leaves earlier keys equal.
  (Cases for both: `cases.md`, "PR CI drifts into the nightly set".)
- **Measure the budget every night, or it drifts unseen**: `templates/ci_health.py` (stdlib only, copy it) reads a
  week of PR runs, compares their wall clock with the budget and lists reruns whose first attempt failed a test, and
  keeps one open issue per problem. Run it as a nightly job.
- **Whoever writes a test makes it fast before committing it**: run it under the gate and read the
  slowest durations. The usual agent-made cause is quadratic re-computation (re-simulating from time
  zero per sample); carry state forward instead.
- **Run what you touched**, plus the structural gates; CI runs the rest. A full-suite run in a
  subagent is gated (`fanout-craft`).
- **Test jobs run in a prebuilt image** with dependencies installed, rebuilt only when requirements
  change, so no job spends its first minute on `pip install`.
- **Mutation runs need per-test timeouts**, thread-based: about 1 in 10 mutants hangs. (Worker counts
  when several agents test on one host: `fanout-craft`.)
