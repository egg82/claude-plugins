# Bringing an existing suite to the current rules

Load when a suite is slow, predates the current test rules (`agentic-engineering` §5-6), or its queue
item says "bring the suite to the current rules". The aim is a per-PR gate inside the repo's stated
budget with no loss of what the suite catches. The number of unit tests is almost never the problem.

## 1. Audit: where the time goes, measured

Read CI, not a local run (a laptop is several times faster than a shared runner, and local runs skip
what CI supplies). For each per-PR job: wall time, runner-minutes, and whether it is on the critical
path. Then sort the cost into these buckets, which between them usually hold most of the
waste:

| Bucket | How it shows | Probe |
|---|---|---|
| Simulations on every PR | a few jobs own most runner-minutes; huge fixture setup against seconds of test calls | `pytest --durations=0 --durations-min=0` from one CI run (setup and teardown rows included; a 1 s floor hides exactly the range a per-test ceiling is set in); job timings per PR |
| Real waits | tests that take seconds and burn no CPU | wall time against CPU time per test; grep for timeouts, `sleep`, connects to closed ports |
| The same work twice | the suite rerun under a second job (another database, another matrix leg) that the tests do not depend on | which tests actually touch what the second leg varies |
| No path filter | a docs-only PR pays the full gate | job list on a docs-only PR |
| Snapshot readouts as approval tests | reds fixed by editing only the expected output | `git log` of red runs: did the next commit touch only tests or snapshots? |
| Duplicate suites | a writer's suite and a blind suite over one contract | pairs of files testing one interface |
| Full-suite runs by agents | locally, not in CI | count pytest runs with no path, `::`, `-k` or `-m` in the transcripts |
| Unpinned or slow runners | the same job varies several-fold between runs | per-runner timings |

Compare against the budget and the outside figure, never the suite's own past (`agentic-engineering` §6).

## 2. Value: what the suite actually catches

Sample fix commits from full history (about 30). For each, did the bug reach main, and which kind of
test would have caught it: unit or contract, simulation, data guard, or none possible (visual, live
hardware, LLM wording)? In audits, most escapes were unit- or contract-sized and very few needed
a simulation. Also read what each red in CI was: a defect, or a change detector going off on an intended
change. This tells you which tests are earning their time and which kind to add.

## 3. Safety net first

**Record a mutation score on the code whose tests you will touch, before any change**, and again after.
It must not drop. Mutation-test changed code only (whole-suite mutation runs were 85% unproductive at
Google at first). Per-test timeouts are thread-based, since about 1 in 10 mutants hangs.

## 4. Rework order: cheapest wins first

1. **Path filters**: docs-only and unrelated changes skip the expensive jobs. Each of these traps was hit:
   - A docs-only path still runs the tests that read docs: citations, and guards scanning every tracked file.
   - The aggregate check requires the filter job's success, success from exactly this run's job set and a skip from
     the rest; "success or skipped" lets a failed filter job pass everything.
   - A deploy job downstream of it needs `always()` plus named results (GitHub Actions' implicit `success()` counts
     by-design skips as failures). Check the first push to main actually released.
   - A simulation filter uses the engine's import closure, not each test file's (that is the whole app).
   - A diff-based selector needs git in the job image, and its fallback to "everything" prints why.
2. **Simulations out of the per-PR path**: nightly, one smoke route per PR sized from CI's durations,
   the full run on a label. Before the per-PR jobs go, read the nightly lane's history and see it green
   (one had been red since creation, unseen), and give its red somewhere read. If it is red on a real
   defect, find its cause first (bisect); then move with the red queued by name at the top of the queue
   and the owner told, or hold the move if the owner wants the fix first. To try a schedule on a
   branch, the CI rules must admit it (GitLab: a `$CI_PIPELINE_SOURCE == "schedule"` rule).
3. **Run once, not twice**: drop the second leg for tests that don't touch what it varies, decided by a
   probe of what each test opens (wrap the connect over a CI run), never by test kind: a "database-free"
   kind turned out half database. Guard the skip marker, and keep files with lane-skipped tests.
4. **Real waits to injected clocks and fail-fast fakes** (`SKILL.md` §7). The flakes under load are
   usually these.
5. **Readouts to non-failing reports**: they print and archive, never fail the build.
6. **Duplicate suites to one per contract**, keeping the blind one.
7. **The old CPU-only gate to wall-clock budgets** (`agentic-engineering` §6, its template). This is a
   gate replacement, a design change made with evidence and the owner's approval, never loosening to
   pass one change. Quote the owner's words, with the date, in the decisions doc the change updates: a PR line
   saying "approved" is the agent's claim, not a record. When a job's timeout becomes its budget, drop retries on timeout (GitLab's
   `retry: when: stuck_or_timeout_failure`), or a budget breach runs three times before it shows.
8. **Runner pinning and caches**, measured before and after.

Each step is its own PR with before and after CI times in its text.

## 5. Removing a test needs evidence

A test may go when the PR states one of:

- **a duplicate**: which test covers the same behaviour, shown by both failing on the same mutant. A mutation tie
  says nothing where the operators cannot produce the failure (a field leaking into a log or a response): there,
  name the surviving test that checks the same property, or keep it;
- **a change detector**: its CI history shows it red only on intended changes, never on a defect.

**Never removed, whatever the evidence:** guards against silent or data-losing defects (save and
data integrity, migrations, secrets, personal data in tracked files, release and deploy locks). Waiting
for one of those to fail means waiting for the harm. They may be made faster, never deleted. Moving a
test to the nightly lane is not removing it.

## 6. Done means

Measured from CI: the per-PR wall time inside the budget, a docs-only PR in about a minute, the nightly
lane green at least once, mutation score not lower, no held count raised, and every removal's evidence in
its PR.
