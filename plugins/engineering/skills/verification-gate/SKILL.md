---
name: verification-gate
description: "Write, audit or fix a verification gate — test suite, lint, pre-commit hook, CI job — so it fails when the code is wrong and stays quiet when it is fine. Use when adding tests to untested code, auditing a suite, designing a lint rule, introducing CI, a gate passes and you can't say why, a broken control still passes, a check nags or reports itself inert, a suite is slow or predates the current rules, or for flaky tests and coverage claims. NOT bug hunting."
---

# Building a verification gate that actually verifies

A gate has one job: **fail when the code is wrong, and only then.** Almost every bad gate is bad in
one of three ways, and none of them is visible from reading it:

1. **It cannot fail.** The assertion holds for a reason unrelated to the behaviour, or
   the check examines nothing, or the harness swallows the failure.
2. **It cannot fire on anything new.** Its inputs are enumerated, so the file added
   tomorrow is invisible.
3. **It fires on work that is fine.** The cry-wolf direction, and the only one that ends with the
   gate deleted — leaving neither the check nor the habit it replaced. *Know which way a check fails
   before you trust it* carries it, including the case where a gate's own "I am blind" self-report
   was itself the false positive.

The first two look exactly like a passing gate; the third looks exactly like a finding, which is why
it gets acted on before anyone asks whether it is real. So the method is not "write checks carefully"
— it is **break the code on purpose and confirm the gate notices, then run it on correct work and
confirm it stays quiet.** Everything else in this skill is downstream of that.

Which structural gates an agent-written codebase needs (size ledgers, type-error counts, import
boundaries, blind contract tests) is the `agentic-engineering` skill; this one is how any single gate
is made able to fail. Bringing an existing suite to the current rules: `references/suite-conformance.md`.

## The failure that hides behind every green check

A gate can pass **for a reason unrelated to what it claims**, and that reads identically to working.

**The one question, ask it before writing the check:** *what would this print if it could see nothing
at all — and is that "pass"?* If a blind run is indistinguishable from a clean run, the check has no
failure signal and never will. Wire the blind case to a **third** outcome — `UNKNOWN`, non-zero,
distinct from pass and fail. **A blind check that fails costs you a debugging session. A blind check
that passes teaches you something false.** (A history-based check nearly wired into a container with
no `git` is the incident.)

Three shapes (full cases: `references/designing-the-check.md`): **it examined nothing** (a non-recursive
glob lost 4,600 lines; only a printed count moved, 8 to 5 — make a gate report what it examined, not
just its verdict); **it stopped before reaching the thing it tests** (a root CI container hit the
program's refuse-to-run-as-root guard and passed over five dead paths); **it was right about the wrong
thing** (a static rule over dynamically-loaded code must follow the loading and decline to judge what
it cannot resolve).

## The method

Work in this order. Steps 1 and 5 are the ones people skip, and they are the ones that find things.
Each step's worked detail and incidents are in the reference named in "Which reference" below, under the same step number.

1. **Find defect classes from the repo's own history, not first principles.** `git log` fixes/reverts,
   merged MRs; read the diffs, cluster, rank by "has this bitten, and how badly". A class fixed more
   than once in different files is a missing gate; one instance is a regression test in costume. Open
   every ticket a rule cites; `git log -S` the guard and check every site its commit touched; a file
   split creates a cross-module class.
2. **Draw the boundary first.** Static check / unit test (pure logic, plus argument construction and
   gating around a destructive call) / real host (the destructive call itself). Test a static tool's
   blindness before relying on it.
3. **Generative, not enumerated.** *Could this fire on code nobody has written yet?* Discover inputs,
   never list them; invert allowlist defaults; don't anchor patterns to statement start; exit non-zero
   on an empty input set ("I examined nothing"); force a classification decision on new additions.
   When agents write the code, a different agent writes the tests from the written contract. HTTP
   APIs: `api-contract-first`'s "The tests worth having".
4. **Make the code reachable.** Entry points that run on import/source can't be tested; guard them, one
   line per file. Bash `BASH_SOURCE` guard: `references/bash-and-bats.md`.
5. **Break it on purpose — the step that finds things.** A mechanical scan generates leads and settles
   nothing (four false positives in one session); label scan output unverified.
   - *Mutation probe:* seed a small fault (invert a condition, `>=` to `>`, validator `return 0`, drop
     a loop), confirm red, revert. **Red means an assertion failed, not a nonzero exit** — count a kill
     only on exit 1 *and* a `FAILED` line naming a test; a mutant that dies of your own malformed edit
     is broken, not killed.
   - *Novelty probe:* write a NEW file with one instance of each class the gate claims to catch; run;
     delete. Invisible means inputs are enumerated somewhere.
   - Work in a **copy of the tree**, never in place (killed runs left planted mutants one commit from
     shipping); a session taking over runs `git status` on every tree a mutation run used.
   - **Check the restore's SCOPE:** before each seed assert the fix is present and the suite is green
     before the mutation; commit the fix first and revert only the file you mutated. (Incident:
     `references/controls-that-lie.md`.)
   - Survivors are the real findings (5 of 19 seeded faults survived a suite that looked good).
6. **The harness can report, and cannot hurt you.** Print failure output; bound the run, reap helpers
   by group not PID; **poll, never sleep** (async-wait ~45% of flaky causes; polling removes ~55%); a
   race test asserts the invariant, not one interleaving. Bash harness traps:
   `references/bash-and-bats.md`; shell foot-guns: `shell-footguns`.
7. **Fixtures: record, never invent.** A double you author encodes your belief, so the test confirms
   it. Prefer real > fake with a contract test > stub > interaction assertions; a real external
   service gets one smoke test. **Time never comes from the wall** (injected clock; unreachable
   dependency is a fake that fails at once; a 5 s connect timeout took a test from 0.64 s to 30 s).
   Stub only outside-world side effects; shape fixtures like reality with decoys; assert against the
   committed artifact once; put the absent case in the fixture builder's DEFAULTS; never derive
   expected values from reading the code. **A double fails toward good news** — lenient exactly where
   its author's model is wrong, so a mutation test run through it passes. Make the double fail on
   purpose in the bug's own dimension, assert its behaviour first, and when a positive control passes
   when it should fail, suspect the harness before the code. Other ways a must-fail case proves
   nothing (runner can't READ the failure; a crash scores as `CAUGHT`; mutation never applied; control
   drives a restatement of the logic; no-op corruption; bad case only ever first; new gate that fails
   nothing on known offenders; new check excludes itself from its registry): rules in
   `references/harness-and-fixtures.md`, incidents in `references/controls-that-lie.md`.
8. **The assertion that cannot fail.** Absence assertions pass when the thing was never created or the
   tool errored silently (pair with a positive control); "parseable JSON" passes on an always-JSON
   fallback; log-string assertions go vacuous on a copy-edit; a **skip** in the environment that
   matters is zero coverage; **in a hand-rolled runner the summary and exit must be the last lines of
   the file** (cases appended below stranded 8 outside the totals and stayed green); a monitoring rule
   needs the alert that cannot be QUIET checked (`min_over_time` over retention; does it flap).
9. **A rule that survives a deadline (lint rules).** Precision beats coverage: score on developer
   action; blocking rule = zero-FP budget, commenting rule ~10%; first 2-3 findings set the
   reputation; error-or-nothing, no warning tier; a suppression is an inert `# no-check: <rule> - <why>`,
   never an overloaded construct like `|| true`; print suppressions honoured, flag stale ones.
10. **Know which way a check fails before you trust it.** A false-negative-prone gate is dangerous
    (green over unverified work, the *falsely clean* failure); a false-positive-prone gate gets
    switched off, leaving neither check nor habit. A gate you cannot characterise is not yet a gate.
    **When the criterion is "does it refrain from X", count X, not the announcement about X** (a
    refusal check scored on hedging passed an answer that apologised and then supplied eleven
    fabricated numbers). **A gate's own "am I inert?" signal must come from the widest structure the
    scan depends on, not its filtered input.** Every new rule wants both a must-block and a must-allow
    case. Figures and quoting: `references/error-profiles-and-adoption.md`.
11. **Introducing a gate into a repo that already violates it.** Replay it over the last N commits
    before enabling anything blocking; scope per-diff or by generated baseline so it gates new
    findings; a ratchet only shrinks; prefer per-instance amnesty at the site over an opaque baseline.
    Then the checks nobody runs: `references/error-profiles-and-adoption.md`; replay loop:
    `references/error-profiles-and-adoption.md` (step 11).

## The negative control you already have, and threw away

A gate is only proven when you have watched it **refuse** something, and that proof is often already
in hand, filed as an outage: a denied login, a rejected write, an unexpected 403. **When something is
refused, blocked or broken, ask what that refusal proves before you repair it**, then check it still
applies to the CURRENT configuration. Worked case: `references/controls-that-lie.md`.

**A red-first run of a test executes the bug.** For a resource runaway (recursion, fork bomb,
unbounded loop or allocation) bound every path inside the test and add an outer bound root cannot
bypass (`podman run --pids-limit N`, `--memory`, `timeout -s KILL`; `ulimit -u` does nothing as root).
One uncapped copy of a recursing handler spawned over a thousand host processes.

## What only a human can catch

No gate reaches: a citation whose disposition nobody checked; a one-off grep wearing a class costume;
prose claiming more than the code enforces; whether the gate matches how the team works.

## Deliverable

Be able to answer all of these, or you have a gate you merely believe in:

1. Which defect classes does this cover, and what is the evidence each has occurred?
2. For each assertion: what mutation did I run, and did it fail?
3. Did I write a brand-new file with a violation and watch the gate catch it?
4. What does this gate *not* cover — which bucket does the rest live in?
5. How many suppressions are honoured, and what is each one's stated reason?
6. Would this have blocked the last twenty normal commits?

## Which reference

| Situation | Load |
|---|---|
| Designing the check: the three shapes, defect classes from history, the boundary, generative inputs, lint-rule precision (steps 1-3, 9) | `references/designing-the-check.md` |
| Proving it can fail: reachability, mutation and novelty probes, restore scope, assertions that cannot fail, alerts that cannot be quiet (steps 4, 5, 8) | `references/making-it-fail.md` |
| Harness and doubles: failure output, bounds, polling, races, fixtures, must-fail cases that prove nothing, resource-runaway red runs (steps 6, 7) | `references/harness-and-fixtures.md` |
| Trusting and adopting it: error direction, inert self-report, replay and baselines, adoption checks, quotable false-positive/negative figures, the human-only list, case-file policy, source reading list (steps 10, 11) | `references/error-profiles-and-adoption.md` |
| Bash/bats suite: `BASH_SOURCE` guard, `!`/`run`, inherited traps, PATH stubs, `setsid` reaping | `references/bash-and-bats.md` |
| Mutation or control harness; doubles; restore scope; alerts that cannot be quiet; the refusal-as-control case | `references/controls-that-lie.md` |
| Bringing an existing suite to the current rules | `references/suite-conformance.md` |
| A rule sounds arguable or you may overturn a probe rule: the incidents behind `verify-dont-anchor`, `no-fabricated-certainty`, `assert-scripted-edits` | `references/instrument-failures.md` (index; Part 1 split by kind under `references/instrument-failures/`, Part 2 artifacts asserting false confidence, Part 3 scripted edits that silently did not apply) |

The case files are a selected subset, not a complete record; append your own to the file of its kind
with a line in the index.
