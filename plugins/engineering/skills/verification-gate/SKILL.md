---
name: verification-gate
description: "Write, audit or fix a verification gate — test suite, lint, pre-commit hook, CI job — so it fails when the code is wrong and stays quiet when it is fine. Use when adding tests to untested code, auditing a suite, designing a lint rule, introducing CI, a gate passes and you cannot say why, a broken control still passes, a check nags or reports itself inert and you want it off, or for flaky tests and coverage claims. NOT bug hunting (bug-hunt)."
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

Which structural gates an agent-written codebase needs (function and file size ledgers, type-error
counts, import boundaries, blind contract tests) is the `agentic-engineering` skill; this one is how
any single gate is made able to fail.

## The failure that hides behind every green check

A gate can pass **for a reason unrelated to what it claims**, and that reads identically
to working.

**The one question that covers all of it, ask it before writing the check:** *what would this print
if it could see nothing at all — and is that "pass"?* If a blind run is indistinguishable from a
clean run, the check has no failure signal and never will. This is the design-time twin of "make the
probe prove it can return non-zero": that one is a control you run afterwards, this one is a
sentence you can apply to a check that does not exist yet.

Wire the blind case to a **third** outcome — `UNKNOWN`, non-zero, distinct from both pass and fail.
Not because it catches more, but because of what a passing blind check *does*: it converts an
unverified assumption into apparent evidence, silently, every run, for as long as nobody looks. A
history-based check written this way was about to be wired into a container with no `git`; the
`UNKNOWN` exit is the only reason its author did not see green and conclude the wiring was correct.
**A blind check that fails costs you a debugging session. A blind check that passes teaches you
something false.**

Three real shapes, all found the hard way:

- **It examined nothing.** A checker globbed `<lib>/*.sh` non-recursively; a refactor
  moved thousands of lines into a subdirectory and they left its view entirely. The only
  signal was a *count* the gate printed — suppressions honoured dropped 8 to 5. Without
  that number it would have gone on reporting a clean pass over a fifth of the code.
  **Make a gate report what it examined, not just its verdict** — file count, rule hits,
  suppressions granted. A verdict alone cannot distinguish "clean" from "empty".
- **It stopped before reaching the thing it tests.** A test invoked a CLI end-to-end to
  prove a dispatch worked. The CI container runs as root, the program refuses to run as
  root, so the test stopped at that guard and passed — on a tree where all five paths it
  covered were dead. **A test that invokes a program end-to-end inherits every guard that
  program has**, and CI trips guards a developer's shell never sees. Exercise the unit, or
  assert you got past the guard.
- **It was right about the wrong thing.** A reachability rule flagged a module for calling
  a function defined elsewhere — correctly, except the module sourced that file itself. A
  static rule over a dynamically-loaded codebase must follow the loading, and decline to
  judge what it cannot resolve rather than guessing.

## The method

Work in this order. Steps 1 and 5 are the ones people skip, and they are the ones that
find things.

### 1. Find the defect classes from the repo's own history, not from first principles

Before writing anything, read what this repo has actually shipped and fixed. A class
fixed **more than once, in different files** is the signature of a missing gate —
someone patched the instance and the sibling kept the bug.

```bash
git log --oneline --all | grep -iE 'fix|revert|hotfix|broke' | head -60
git log --merges --oneline -40                    # MR titles are often franker
git log -p -S '<suspect idiom>' --oneline         # when did this shape appear/leave
glab mr list --all --per-page 60 ; gh pr list -L 60
```

Read the diffs, not just the subjects. Cluster them. Rank by "has this bitten, and how
badly" — not by how neat a rule would be. In one real audit the dominant class was
*reporting success after a failed step* (5 of 11 MRs), which no first-principles list
had included; the pretty rules that got written first covered classes that had never
occurred.

Traps here:

- **Check the disposition of every citation.** A rule justified by tickets that turn
  out to be closed-as-intended is a rule that will fire on correct code forever. Open
  the ticket. No tool does this for you.
- **A class needs more than one instance, or it is a regression test in costume.** A
  grep for one literal string passes forever and catches nothing while looking like
  coverage.
- **When you find the class fixed once, `git log -S` the guard and check every site that
  commit touched.** The sharpest case is a commit that fixed some sites *while editing the
  others*: one audit found `mv` unguarded in both halves of an installer, and the commit
  that added exactly that guard to two siblings had edited these two functions, skipping
  the move eight lines below. Siblings, fix and omission, one diff.
- **Splitting a file creates a class that did not exist before it.** Symbols that shared a
  scope now cross a module boundary, and a lazily-loaded one is only missing at runtime:
  three shipped in one split — a dispatcher calling into five modules nothing sourced, a
  guard function called from a module that did not load its definition, and a variable read
  in the entrypoint but assigned only in one module, fatal under `set -u`. If you split
  something, add a check that loads each piece the way production loads it.

### 2. Draw the boundary before writing anything

Three buckets. Getting this wrong is the most expensive mistake available, because you
end up trying to unit-test a disk resize or hoping a linter catches a runtime contract.

| bucket | what belongs | what it costs |
|---|---|---|
| **Static check** | shapes in the source: a discarded exit status, an idiom that misbehaves on empty input, a config key that doesn't exist in the schema, an inventory that won't cover new files | cheap, instant, no environment |
| **Unit test** | pure logic and the *argument construction and gating* around a destructive call — validators, parsers, canonicalisers, retry ladders, slug builders | cheap if the code is reachable; see step 4 |
| **Integration / real host / VM** | the destructive call itself, external-service contracts, anything needing real state | slow, but the only thing that proves it |

The line is *what the test may mutate*, and the config-management world draws it
by directory, not by cleverness: Ansible says "don't unit test your playbook";
ChefSpec says outright it "can't actually tell you if a cookbook is doing the right
thing"; Puppet Litmus requires dedicated throw-away machines. **`lvresize` belongs in
the VM run — but the function that decides whether to call it, and with what, is a
unit test and should be one.**

And know what static analysis genuinely cannot see. Verified examples: shellcheck
finds *nothing* in a bash-4ism defect history (`declare -A` under `#!/bin/bash` is
legal; there is no bash-version target); kubeconform is blind to any field under
`x-kubernetes-preserve-unknown-fields: true`, which is where chart values and plugin
config live. Test the blindness before you rely on the tool.

### 3. Make the check generative, not enumerated

> Could this fire on code nobody has written yet, in a file that doesn't exist yet?

If the answer is no, it is a **characterization test** (Feathers) wearing a linter's
UI: it describes today's tree and can never tighten. Concretely:

- **Discover inputs, never list them.** Glob the directory; identify commands by
  shebang; derive the file↔check mapping from disk. A hardcoded list of seven files
  means the eighth is silently unexamined — and the hook may still *run*, reporting a
  clean pass on a file it never opened.
- **Invert allowlist-shaped defaults.** `END_USER = {…}` exempts anything unlisted.
  List the *exceptions* (`IT_FACING = {…}`) so a new thing gets the strict standard by
  default. Defaults-not-matching-intent is the single largest complaint developers
  report about analyzers (Christakis & Bird, ASE 2016).
- **Don't anchor patterns to statement start.** Calls hide inside one-line function
  bodies and after `&&`. `^\s*err\s+"` misses `f() { err "…"; }`.
- **Refuse to report a clean pass on an empty input set.** If the check found fewer
  files than the repo must contain, exit non-zero with "I examined nothing". This is
  the failure mode users hate most and nobody instruments.
- **Force a decision on new additions.** "Every function in the module is classified
  as wrapper / viewer / probe" fires on the commit that adds an unclassified one. That
  is a completeness invariant on your own config, and it is the good kind of
  structural rule.
- **When agents write the code, a different agent writes the tests, from the contract.**
  Tests an agent writes for its own change were measured to change nothing (arXiv
  2602.07900: mostly print statements), while LLM-written property tests from a stated
  property found real bugs (arXiv 2510.09907). So: properties derived from the written
  contract, each tagged with the clause it checks (a failing property may be a contract
  bug, not a code bug), by an agent that never saw the implementation. That this beats a
  co-written suite is a hypothesis, unmeasured anywhere; measure it with the mutation
  probe in §5.
- **For an HTTP API, this step is the `api-contract-first` skill's "The tests worth having"**: each
  iterates a population read from the served schema (every endpoint, every field, every error) and
  asserts that population was non-empty.

### 4. Make the code reachable, or you will test only the easy fraction

The most common reason important logic has no tests is mechanical, not cultural: the
entry point runs on import or on source, so a test cannot reach a function without running the
program. Guard the entry point, one line per file. For bash (the `BASH_SOURCE` guard, why `if` and
not `&&`, and the repo where it made most of the code testable): `references/bash-and-bats.md`.

### 5. Break it on purpose — this is the step that finds things

Nothing before this proves anything. Two probes, both cheap:

Before either, note that **a mechanical scan generates leads and settles nothing.** Over
one session, hand-written detectors over shell source produced four false positives — two
from picking the wrong function where a module defined two near-identically-named
writers, one from a path guard that never matched because names were
package-relative, one from a regex anchored to statement start. Every real defect that
session came from reading the code. Use scans to decide *where to look*; never report their
output as a finding, and when handing them to someone else, label them unverified and say
the scanner has a false-positive history.

**Mutation probe (does the gate fail when the code is wrong?)** Seed a small fault,
run the gate, confirm it goes red, revert. Do this for every assertion you care about.
First-order mutants are usually enough (the Coupling Effect — a hypothesis, not a
settled result; the mutation-testing literature treats higher-order mutation as open):
invert a condition, delete a
cleanup line, change `>=` to `>`, make a validator `return 0`, drop a loop.

**Novelty probe (does the gate fire on what doesn't exist yet?)** Write a *new* file
containing one instance of every class the gate claims to catch. Run the gate. Delete
it. If the file was invisible, your inputs are enumerated somewhere.

Do this work in a **copy of the tree**, never in place. If you must mutate in place,
verify the restore — a `git checkout` from the wrong directory fails silently, and a
safety mechanism you removed to test a guard is a safety mechanism that is now gone.

**And check the restore's SCOPE, not just that it worked — a revert wide enough to include the fix
under test reports the fix working.** Before each seed, assert that the fix is present in the tree
and that the suite is **green before the mutation**; commit the fix before running the harness over
it, and revert only the file you mutated. (Incident: `references/controls-that-lie.md`.)

Survivors of these probes are the real findings. Expect them to be embarrassing: in
one audit, five of nineteen seeded faults survived a suite that looked good, including
"the cancel path triggers the destructive action instead of aborting".

### 6. Check the harness can report, and cannot hurt you

A gate that dies without reporting is worse than no gate. For a shell harness — bats `!` and `run`,
an inherited `trap … EXIT`, a bypassed PATH stub, reaping helpers with `setsid` — the verified traps
are in `references/bash-and-bats.md`; the zsh and lying-command foot-guns of the shell you probe
with are the `shell-footguns` skill. General traps:

- **Print failure output.** `--print-output-on-failure`, `assert_output`-style helpers,
  `expected:`/`actual:`. A gate whose failure says only "a count differed" gets
  re-run, not read.
- **Bound the run.** Per-test timeouts, and reap helper processes by *group*, not by PID (the
  shell specifics are in `references/bash-and-bats.md`).
- **Poll, never sleep.** Async-wait is ~45% of flaky causes (Luo et al., FSE'14);
  polling removes the flake ~55% of the time, while a longer sleep never does. Bind
  port 0 and report the bound port rather than picking one.

### 7. Fixtures: record, never invent

A double you author encodes *your belief* about the dependency, so the test confirms
the belief instead of checking the dependency (Meszaros; *SWE at Google* ch. 13-14
states it outright). This is the single most reliable way to ship a green suite over a
real bug.

- Prefer the **real thing** > a fake with a contract test > a stub > interaction
  assertions.
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
  code path once, read-only, in the real environment. (Incident: `references/controls-that-lie.md`.)
- **Put the absent case in the fixture builder's DEFAULTS.** A fixture is an act of completion, so
  null/missing/unknown values, which dominate real data, are the ones no fixture exercises; one
  `group by` on the real column first. (Incident: `references/instrument-failures/gates-that-pass-broken.md`,
  "EVERY FIXTURE SUPPLIED THE FIELD".)
- Worst case is a fixture asserting **the bug** — then the suite actively defends it.
  Re-derive expected values from observed behaviour, never from reading the code.

**A double is lenient exactly where its author's model is wrong, which is exactly where
the bug is.** That is the sharp form of "it encodes your belief", and it means a test
double does not fail randomly — it **fails toward good news**. So the mutation test you
run to prove a test can fail is itself run through the double, and passes.

**The check: make the double fail on purpose in the same dimension the bug lives in.**
Not "does my mutation test fail" — that shares the double. Assert the double's own
behaviour first (`removeChild` then read `parentNode`; the replace matched; the checker
rejects the broken control), then trust what it tells you about the code. And when a
positive control passes when it should fail, suspect the harness before concluding the
code was already right — the harness is the thing you wrote most recently and checked
least.

**Other ways a must-fail case proves nothing** — each with its incident in
`references/controls-that-lie.md`; open it when a control or mutation harness is involved:

- **The runner cannot READ the failure** (a Job waited on `condition=complete` never sees a failure).
  Read the outcome on both paths.
- **A crash and a catch both exit non-zero**, and the harness scores the crash as `CAUGHT`. Assert
  *how* it failed; score a traceback as a distinct outcome.
- **The mutation never applied**, and the harness blamed the test. Report *did the mutation land*
  and *did the gate fire* separately; "could not plant" is its own outcome.
- **A control that drives a restatement of the logic** rather than the function itself proves
  nothing. Call the real function with a degenerate input. A test containing SQL or a command that
  also exists in the code is testing the copy: fix the callability (an optional `conn` parameter),
  then mutation-test the fix (`references/instrument-failures/gates-that-pass-broken.md`, "RE-IMPLEMENTS").
- **The mutation set is the blind spot.** For each rule the gate grows, ask what mutation exercises
  *that* rule.
- **A discriminator needs both directions proven.** Name the input that MUST be rejected, confirm it
  is present in the sample, assert it was rejected.
- **A new check excludes itself** from a registry it enumerates (`git ls-files`, a glob). Commit,
  save or register it before believing its first green.

### 8. Watch for the assertion that cannot fail

Absence assertions and always-satisfiable claims go vacuous quietly:

- `[ ! -e "$file" ]` passes when the file was **never created** — so the cleanup you
  meant to test is unexercised. Verify the precondition really occurs.
- "Is the output parseable JSON" cannot fail if the code has a fallback that always
  emits parseable JSON. Assert a field you passed in.
- A pure-absence check on a tool's output passes when the tool **errored and printed
  nothing**. Pair every absence assertion with a positive control in the same test.
- Asserting on a **log string** couples the test to prose; a copy-edit makes it
  vacuously true. Assert on a counter, a status, or a value the code owns.
- A test that **skips** in the environment where it matters has zero coverage there.
  `[ "$EUID" -ne 0 ] || skip` in a root CI container means the privilege gate is never
  tested. Drop privileges (`setpriv`) instead of skipping.
- **In a hand-rolled runner, the summary line and the exit expression must be the last lines of
  the file.** Cases appended below them are left out of the counts *and* silently become the
  script's exit status, because a shell exits with whatever ran last — so a bare
  `[ "$fail" -eq 0 ]` sitting in the middle of a file gates nothing at all. One gate grew a new
  rule block underneath its own summary, stranded 8 cases outside the totals, and went on
  reporting green while printing a real failure on screen. A clean run cannot distinguish
  "correctly green" from "always green"; only injecting a case that *must* fail can. End with an
  explicit `exit`, and prove the non-zero.
- **For a monitoring rule, the mirror: the alert that cannot be QUIET.** Before trusting an alert,
  query its metric's history (`min_over_time` over retention) and confirm the quiet state has
  actually occurred; and check whether the signal **flaps** before choosing `for:` — when the
  emitter is slower than the evaluator, the window belongs in the expression. (Incidents and the
  second-metric fix: `references/controls-that-lie.md`.)

### 9. Design the rule so it survives contact with a deadline

For lint rules specifically, precision beats coverage — trust is the currency and
false positives spend it permanently:

- Score a rule on **developer action**, not analyzer correctness. Google's "effective
  false positive" is *any report where the user chooses not to act* — a true finding
  nobody fixes counts against you.
- **A blocking rule gets a zero-FP budget**; a commenting rule gets roughly 10%
  (Tricorder, CACM 2018; convergent with the ~20% false-positive rate Coverity reports as *typical for its
  stable checkers* — not a blanket ceiling — noting "when
  forced to choose between more bugs or fewer false positives we choose the latter").
- **The first two or three findings set the reputation permanently** (Bessey et al.,
  CACM 2010: "if the first N reports are false positives (N = 3?), people tend to utter
  variants on 'This tool sucks.'"). Ordering matters more than the aggregate rate.
- **"Is the fix a one-liner?" is a rule-quality criterion.** Error Prone's bar for
  on-by-default is "swap these arguments", not "introduce a subclass". A finding whose
  cheapest resolution is a ritual (an empty test file to satisfy a coverage rule) is
  an effective false positive even when true.
- **Prefer error-or-nothing to a warning tier.** A tier people may ignore will be
  ignored, and then trains them to ignore the channel.
- **Never overload a construct that already means something.** A suppression must be
  an inert comment naming the rule and a reason — `# no-check: <rule> - <why>`. Reusing
  `|| true` as an opt-out silently grants amnesty to every pre-existing instance and
  makes "I wrote this deliberately" indistinguishable from "I wrote this to shut you
  up". Print the suppressions you honour so the debt stays countable, and flag stale
  ones (`--warn-unused-ignores`, `RUF100`, `nolintlint`).
- **Don't hand-roll what exists upstream.** A local "shebang without +x" rule is
  strictly worse than `pre-commit-hooks`' `check-shebang-scripts-are-executable`,
  which covers the whole repo for no code.

### 10. Know which way a check fails before you trust it

A wrong verifier does not fail neutrally — it misleads, and a wrong critique gets acted on about as
readily as a right one. So establish a check's **error profile** before relying on it: does it cry
wolf, or does it wave things through? The two are not symmetric and they call for opposite
responses, and the direction is domain-dependent — the same self-checking method has measured
mostly false positives in one domain and mostly false negatives in another. The figures and how to
quote them safely: `references/error-profiles-and-adoption.md`.

The practical consequences:

- **A false-negative-prone gate is the dangerous one**, because it reports green over unverified
  work. That is the *falsely clean* failure: a broken mechanism and a healthy one look identical.
- **A false-positive-prone gate gets switched off**, which leaves you strictly worse off than the
  prose it replaced — you now have neither the check nor the habit.
- **A gate you cannot characterise is not yet a gate.** Break something on purpose and confirm it
  goes red; that is the only evidence that distinguishes "passing" from "not looking".
- **When the criterion is "does it refrain from X", the check must count X — not the announcement
  about X.** A refusal check scored on hedging language passed an answer that said "I can't give you
  verified numbers" and then supplied eleven fabricated ones. The gate ran, reported green, and was
  measuring the apology rather than the thing.
- **A gate's own "am I inert?" signal must not be computed from the gate's filtered input** — or it
  reports on the filter and calls that a verdict about the world. Derive the health count from the
  *widest* structure the scan depends on, so "I saw nothing" and "there was nothing" stay
  distinguishable. (Incident: `references/error-profiles-and-adoption.md`.)

This is why a new rule wants both a must-block *and* a must-allow case: one case alone cannot tell
a working gate apart from one that blocks everything, or from one that blocks nothing.

### 11. Introducing a gate into a repo that already violates it

The gate is only useful if it survives adoption. Before enabling anything blocking,
**replay it over the last N commits** — that is the only way to see the cost:

```bash
for c in $(git log --format=%H -20 -- '<paths>'); do
  git archive "$c" | (cd "$tmp" && tar -x) && run_the_gate "$tmp"
done
```

If it would have blocked most normal commits, the scoping is wrong. Per-*file* scoping
inherits a legacy file's entire debt the moment you touch it; you want per-*diff*, or a
generated baseline (`ansible-lint --generate-ignore`, golangci-lint's `--new-from-rev`, SonarSource's
Clean-as-You-Code) so it gates **new** findings.

If you must carry existing debt:

- **A ratchet is a budget that can only shrink.** Without a decrement path a baseline
  is amnesty with better branding (cf. ArchUnit's `FreezingArchRule`: generative rule,
  *separate* violation store, store may only shrink).
- **Prefer per-instance amnesty at the site** over an opaque baseline file — annotate
  each existing violation inline, so the debt appears in every diff that touches it and
  its count is greppable. A baseline file is invisible to the person editing the line.

Then run the checks nobody thinks to run — **does one job actually execute; does it match how code
arrives; is the tooling pinned; is the diff computation correct under CI's shallow clone; is the
gate's own code tested; is an invariant BETWEEN two artifacts actually tested** — detail for each in
`references/error-profiles-and-adoption.md`.

## The negative control you already have, and threw away

A gate is only proven when you have watched it **refuse** something, and that proof is often already
in hand, filed as an outage: a denied login, a rejected write, an unexpected 403. **When something is
refused, blocked, or broken, ask what that refusal proves before you repair it** — then check the
proof still applies to the CURRENT configuration. Worked case: `references/controls-that-lie.md`.

## What only a human can catch

State this plainly rather than pretending coverage. No gate reaches:

- **A citation whose disposition nobody checked** — a rule justified by a ticket closed
  as working-as-intended.
- **A one-off grep wearing a class costume** — correct, inert, and looks like coverage.
- **Prose that claims more than the code enforces** — "every check was verified against
  its pre-fix commit" is a sentence, not a test.
- **Whether the gate matches how the team actually works.**

## Deliverable

When you finish, be able to answer all of these. If you cannot, you have a gate you
merely believe in:

1. Which defect classes does this cover, and what is the evidence each has occurred?
2. For each assertion: what mutation did I run, and did it fail?
3. Did I write a brand-new file with a violation and watch the gate catch it?
4. What does this gate *not* cover — which bucket does the rest live in?
5. How many suppressions are honoured, and what is each one's stated reason?
6. Would this have blocked the last twenty normal commits?

## The case files

`references/instrument-failures.md` carries incidents behind the resident `verify-dont-anchor`,
`no-fabricated-certainty` and `assert-scripted-edits` preferences — the specific probe, the specific
wrong answer, and what would have caught it. Those preferences state each rule as a claim; this is
where the proof lives. Open it when a rule sounds arguable, when you are unsure whether it covers the
probe in front of you, or when you are about to overturn one. It is an index with one line per case:
Part 1 (probes that lied) is split by failure kind under `references/instrument-failures/` — the
general probe rules, false zeros, wrong instrument, controls and inference, timing and waits, gates
that pass broken code, blast radius — and Part 2 (artifacts asserting false confidence) and Part 3
(scripted edits that silently did not apply) are a file each. Open only the kind in front of you.

It is a **selected subset**, not a complete record: case studies whose evidence could not be told
without the environment they happened in were left out, so a gap there is not evidence that a failure
mode has never been seen. Append your own as you hit them, to the file of its kind with a line in the
index — the set is worth what its worked specifics are worth.

`references/controls-that-lie.md` and `references/error-profiles-and-adoption.md` carry the incidents
and evidence behind steps 5–11; `references/error-profiles-and-adoption.md` also lists the sources
worth reading directly.
