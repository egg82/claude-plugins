# Harness and fixtures: reporting, bounds, doubles, resource runaways

Load when you are building or reviewing the test harness, the doubles and fixtures it uses, or a test that executes a
runaway bug (`SKILL.md` steps 6 and 7). Shell harness traps: `bash-and-bats.md`; incidents behind the must-fail
cases below: `controls-that-lie.md`.

## Step 6: the harness can report and cannot hurt you

Shell harness traps (bats `!` and `run`, inherited `trap … EXIT`, bypassed PATH stubs, `setsid`
reaping): `bash-and-bats.md`; shell foot-guns: the `shell-footguns` skill. General traps:

- **Print failure output.** `--print-output-on-failure`, `assert_output`-style helpers,
  `expected:`/`actual:`. A gate whose failure says only "a count differed" gets
  re-run, not read.
- **Bound the run.** Per-test timeouts, and reap helper processes by *group*, not by PID (shell
  specifics in `bash-and-bats.md`).
- **Poll, never sleep.** Async-wait is ~45% of flaky causes (Luo et al., FSE'14);
  polling removes the flake ~55% of the time, while a longer sleep never does. Bind
  port 0 and report the bound port rather than picking one.
- **A race test asserts the invariant, not one interleaving.** List every answer each racer can
  correctly get, accept any of them, and assert the invariant the lock protects. One test
  pinned `[200, 409]` for two racers revoking each other's permission; `[200, 403]` was equally right
  (the loser no longer held it) and went red later. Prove the test still fails on the planted bug: the
  unlocked version gives two 200s and nobody left holding the permission.

## Step 7: fixtures — record, never invent

A double you author encodes *your belief* about the dependency, so the test confirms the belief
instead of checking the dependency (Meszaros; *SWE at Google* ch. 13-14 states it outright). This is
the single most reliable way to ship a green suite over a real bug.

- Prefer the **real thing** > a fake with a contract test > a stub > interaction
  assertions. A real external service gets **one smoke test**, not a suite run through it.
- **Time never comes from the wall.** Timeouts, leases, retries and backoff take an
  injected clock in tests (`clock.advance()`), and an unreachable dependency is a fake that
  fails at once, never a closed port behind production timeouts (one test waiting out a 5 s
  connect timeout took 30 s; at 0.1 s, 0.64 s). These races are also the flakes that appear
  only under load.
- Stub only what has **side effects on the outside world**. Mocking a pure filter
  tests your mock.
- Drive the real client against a **local server you control**. A throwaway HTTP server
  scripting a status sequence exercises real `curl` — including protocol-level
  failures a stub cannot produce, like a truncated body with a lying `Content-Length`.
- **Shape fixtures like reality, with decoys.** A one-key JSON object shaped to fit
  your parser proves nothing; a realistic body with sibling `_name` keys catches a
  loose parser.
- **Assert against the committed artifact**, at least once. A suite whose every
  fixture used `indent=2` passed while the real file was compact.
- **A subprocess and its config are part of the artifact, and no import-level check sees either.**
  Enumerate the binaries the code shells out to and assert them in the built image, remember a
  binary's own TLS/auth config is separate from the parent's, and run the deployed artifact's real
  code path once, read-only, in the real environment. (Incident: `controls-that-lie.md`.)
- **Put the absent case in the fixture builder's DEFAULTS.** A fixture is an act of completion, so
  null/missing/unknown values, which dominate real data, are the ones no fixture exercises; one
  `group by` on the real column first. (Incident: `instrument-failures/gates-that-pass-broken.md`,
  "EVERY FIXTURE SUPPLIED THE FIELD".)
- Worst case is a fixture asserting **the bug** — then the suite actively defends it.
  Re-derive expected values from observed behaviour, never from reading the code.

**A double is lenient exactly where its author's model is wrong, which is exactly where the bug is.**
That is the sharp form of "it encodes your belief", and it means a test double does not fail randomly
— it **fails toward good news**. So the mutation test you run to prove a test can fail is itself run
through the double, and passes.

**The check: make the double fail on purpose in the same dimension the bug lives in.** Not "does my
mutation test fail" — that shares the double. Assert the double's own behaviour first (`removeChild`
then read `parentNode`; the replace matched; the checker rejects the broken control), then trust what
it tells you about the code. And when a positive control passes when it should fail, suspect the
harness before concluding the code was already right — the harness is the thing you wrote most
recently and checked least.

**Other ways a must-fail case proves nothing** — each with its incident in `controls-that-lie.md`:

- **The runner cannot READ the failure** (a Job waited on `condition=complete` never sees a failure).
  Read the outcome on both paths.
- **A crash and a catch both exit non-zero**, and the harness scores the crash as `CAUGHT`. Assert
  *how* it failed; score a traceback as a distinct outcome.
- **The mutation never applied**, and the harness blamed the test. Report *did the mutation land*
  and *did the gate fire* separately; "could not plant" is its own outcome. (A same-size Python
  rewrite within one second reuses the stale `.pyc`: `PYTHONDONTWRITEBYTECODE=1`.)
- **A control that drives a restatement of the logic** rather than the function itself proves
  nothing. Call the real function with a degenerate input. A test containing SQL or a command that
  also exists in the code is testing the copy: fix the callability (an optional `conn` parameter),
  then mutation-test the fix (`instrument-failures/gates-that-pass-broken.md`, "RE-IMPLEMENTS").
- **The corruption is sometimes a no-op** (an in-place edit that rewrites a character to itself): replace the
  value, don't edit it, and assert the corrupted input differs from the original.
- **The mutation set is the blind spot.** For each rule the gate grows, ask what mutation exercises
  *that* rule.
- **A control whose bad case is always the first item cannot see state carried across items**
  (running totals, accumulators, caches): put one at position two or later. A sign-flipped
  running total passed every first-item control and an otherwise strong mutation run.
- **A new gate that fails nothing on its first run over known offenders is blind until shown
  otherwise.** Name an offender beforehand and expect it red.
- **A discriminator needs both directions proven.** Name the input that MUST be rejected, confirm it
  is present in the sample, assert it was rejected.
- **A new check excludes itself** from a registry it enumerates (`git ls-files`, a glob). Commit,
  save or register it before believing its first green.

## Resource-runaway bugs: a red-first run executes the bug

When the defect is a resource runaway (recursion, fork bomb, unbounded loop or allocation), every path
of the test that reaches it needs a bound inside the test (a depth counter, a timeout) and an outer
one root cannot bypass: `podman run --pids-limit N`, `--memory`, `timeout -s KILL`. `ulimit -u` does
nothing as root, and CI and test containers usually run as root. In one case a test copied the
recursing handler into a second, uncapped test, and its red run spawned over a thousand host
processes before the container was killed.
