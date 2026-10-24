# Controls, doubles and harnesses that lie

The worked incidents behind the control and fixture rules in `SKILL.md` steps 5, 7 and 8. Each is a
way a proof that a gate can fail itself failed silently — usually toward good news.

## A restore wide enough to erase the subject (step 5)

**And check the restore's SCOPE, not just that it worked — a revert wide enough to include
the fix under test reports the fix working.** My harness reverted each mutant with `git
checkout -- pkg templates`, which also reverted the new validator I was
measuring, because it lived in that directory. So the seeded fault ran against the
*unfixed* tree, my new test failed for the ordinary reason that its subject was missing,
and the harness read that failure as **CAUGHT**. Two mutants reported as caught by a fix
that was no longer in the tree; a third, run later, exposed it only because the same
missing validator made the whole file fail.

Note it is the *opposite* failure to the one above — the restore did exactly what it said,
and that is what broke it — and it lands in the good-news direction, which is why nothing
prompted a second look. It is also self-inflicted in a way that generalises: a mutation
harness and the fix it grades are edits to the same tree, so any cleanup broad enough to be
convenient is broad enough to erase the subject.

The cheap discriminator is a **precondition, asserted rather than assumed, before each seed**:
that the fix is present in the tree (`assert "<new symbol>" in source`) and that the suite is
**green before the mutation**. A baseline that is already red cannot tell you anything about
what a mutant did, and a `SEED-FAILED` line is worth more than a `CAUGHT` you cannot
attribute. Commit the fix before running the harness over it, and revert only the file you
mutated.

## A subprocess and its config are part of the artifact (step 7)

- **A SUBPROCESS AND ITS CONFIG ARE PART OF THE ARTIFACT, and no import-level check sees
  either.** Three in a row on one code path: a feature that shells out to `git` shipped in an
  image with no `git`, and once that was fixed, shipped again unable to trust the internal CA —
  because `git` reads `GIT_SSL_CAINFO`, not the `SSL_CERT_FILE` the deployment sets for its HTTP
  client. Every unit test passed throughout, and so did the build's `--help` smoke test, which
  exercises every import and therefore proves nothing about a child process or its trust store.
  So: **enumerate the binaries the code shells out to and assert them in the built image**, beside
  whatever data-file check already lives there, and remember that a binary's own TLS and auth
  config is separate from the parent process's.

  The cheap discriminator that found both, and it is worth reaching for BEFORE anything is
  scheduled: **run the deployed artifact's real code path once, read-only, in the real
  environment.** Not a synthetic ping — the actual function, with its side effect made impossible
  by the inputs rather than by care. Here that was the push routine driven with an edit that
  returns "no change", so it cloned, authenticated and returned without committing. It reported
  each link in turn and stopped at the first broken one, twice. A test suite could not have found
  either, and the alternative was discovering both at 10:00 on a Sunday inside a CronJob log.

## A double fails toward good news (step 7)

Three instances in one day, three different tools, none of which announced anything:

- A DOM shim's `removeChild` never cleared `parentNode`. The bug was code reading
  `rows[0].parentNode` after detaching those rows and getting `null` in a browser. The
  shim's detached node still reported its old parent, so the new test passed against the
  broken code **and** against the fix. The shim was wrong in precisely the direction that
  made the bug invisible, because both came from the same wrong mental model of removal.
- A `str.replace`-based control on reflowed YAML silently no-oped, so it compared the file
  against itself and reported no difference.
- A structural checker passed its own deliberately-broken control.

## Other ways a must-fail case proves nothing

**The other way a must-fail case proves nothing: the runner cannot READ the failure.** A
gate run as a Kubernetes Job correctly exited 1 on its broken control, and the operator saw
only `error: timed out waiting for the condition` — because they waited on
`condition=complete`, which a failing job never reaches. The gate was perfect and the result
was unobtainable, and **an unreadable failure is indistinguishable from a hung or broken
gate.** Whatever runs the must-fail case has to read the outcome on *both* paths: poll
`status.succeeded`/`status.failed` rather than one condition, use `restartPolicy: Never` so
the terminated pod stays readable, and capture the exit code and output before the container
is reaped. Applies to any wrapper that reports pass/fail asymmetrically — a CI step whose
artifact upload runs `only-on-success`, a test runner that swallows stderr on failure.

**A fourth way, and the harness scores it as a WIN: a crash and a catch both exit non-zero.**
A mutation harness that reads "did the gate exit non-zero?" cannot tell a gate that *reported
the defect* from one that *died on a traceback* — and it renders the second as `CAUGHT`. Mine
did, for a rule whose `problems.append()` was called on a `set`: the mutation injected the
defect, the gate raised `AttributeError`, the harness printed a tick, and the whole suite
stayed green over a rule that could never fire. Note the direction — this is the mirror of the
unreadable failure above. There, a working gate looked broken; here, a **broken gate looks
like a working one**, which is the shape nobody re-reads. So the must-fail case has to assert
*how* it failed, not just that it did: grep the output for a traceback and score that as a
distinct third outcome. The control is cheap — revert the fix and watch the case flip from
`CAUGHT` to `CRASHED`.

**And one step EARLIER than any of those: the mutation never applied, and the harness scored the
subject anyway.** My harness planted a defect with `str.replace` on an anchor, ran the test, and
printed a verdict. The anchor was wrong by two spaces, so nothing was planted -- and the harness
reported `*** the cause test is VACUOUS ***` about a test that was fine. Note where that points: not
"the mutation failed" but *"your test cannot fail"*, which is the most alarming verdict a mutation
run can produce and the one you act on by rewriting a correct test. The setup broke and the subject
took the blame. It is the same false-zero-from-a-broken-probe shape as everywhere else, except the
probe here is the harness's own edit, and every mutation harness has one.

So a mutation case has **two** results to report, never one: *did the mutation land*, then *did the
gate fire*. Assert the edit applied -- `assert s.count(anchor) == 1` before writing, and abort the
case rather than proceeding -- and make "could not plant" a distinct outcome from both `CAUGHT` and
`MISSED`. A harness that prints `MUTATION SCRIPT FAILED` and then evaluates anyway, as mine did, has
told you and scored against you in the same breath.

**And a control is only a control if it drives THE SAME CODE as the subject.** Two of mine in one day
did not, and both read as thorough. One asserted `len(pairs) > MAX` — arithmetic about the fixture,
true whatever the matcher did, standing in for "a match-everything matcher breaches the bound". The
other wrote a probe file into `tests/` and expected a scanner that only walks the package directory to
find it, so it asserted against an empty list. The shape they share: **the control exercises a
restatement of the logic rather than the function itself**, which is invisible because a control is
written to pass, and a passing control is never re-read. The fix was the same both times — pull the
logic into a function, then have the control call it with a degenerate input rather than re-deriving
what it ought to have produced.

**And expect the mutation set itself to be the blind spot.** A suite of mutations proves only
the defects its author thought to write a mutation for. Seven of mine passed while three real
defects sat in the checks, because none of the seven injected an out-of-vocabulary status or a
reworded doc phrase. When a gate grows a rule, ask what mutation would exercise *that* rule —
an unexercised rule is indistinguishable from a working one.

**A DISCRIMINATOR needs both directions proven, and a control that only shows it MATCHING proves
nothing about what it rejects.** Distinct from the false-zero family (`instrument-failures/false-zeros.md`), which is about a probe
that under-reports: here the probe reports correctly and the *control* is the thing that cannot
fail. If the question is "does this filter separate A from B", demonstrating that it matches A is
half a test — and it is the half that feels like success, so it ends the investigation.

Worked case: I needed a log filter `level in (ERROR, WARN)` to admit error lines and reject DEBUG ones. I
built a paired control, which is the right instinct — one probe filtered `level in (ERROR, WARN)`, one filtered
`not (level in (ERROR, WARN))`. The first returned 482 lines and I read that as the filter discriminating.
It was not: it proved only that the filter matched *something*, and I never checked whether the
matched lines were the error ones. When the filter was later put in front of a real writer, its very
first row was a DEBUG line — the exclusion had never worked, and my control could not have
told me, because **no DEBUG lines existed during the test**. A rejection test run against a
population containing nothing to reject passes vacuously.

So: **name the input that MUST be rejected, confirm it is present in the sample, and assert it was
rejected.** If it is not present, the test is not weak — it is not a test, and saying so is the
result. Same shape as the empty-collection rule in `instrument-failures/false-zeros.md` (`all([])` is `True`), one layer up: there the
quantifier had nothing to range over, here the discriminator had nothing to discriminate against.

**And a fifth way, which only appears once: the check EXCLUDES ITSELF because it does not exist yet.**
A checker that enumerates its subject from a registry — `git ls-files`, a glob, a config's include list —
is not in that registry until it is committed, saved or added. So its first run scans everything except
itself and reports green, and **the green describes the registry's state rather than the world's.** Mine
scanned tracked source for references to documentation; its own control test held deliberately-dangling
references as string literals, so it should have failed on its own fixtures from the start. It passed,
because `git ls-files` does not list an untracked file. Committing it broke it, which is the only reason
it was found.

Distinct from a broken probe (wrong pattern) and from a wrong target (right probe, wrong tree): the probe
and the target are both correct and the *scope* is short by exactly one file — the newest, least reviewed
one. So: **commit, save, or register a new check before believing its first green**, and if it enumerates
its own kind, confirm it can see itself.

## Alerts that cannot be quiet, and signals that flap (step 8)

- **The mirror, for a monitoring rule: the alert that cannot be QUIET.** A test that cannot fail
  reports green forever; an alert whose metric has never entered the passing state fires forever,
  and the two are equally uninformative. `ExampleRegression` read
  `max(example_failures) > 0`; across every scrape retained — 79 samples over two
  weeks — that series was never once zero, minimum 2. So it had been firing continuously since it
  was written, which is indistinguishable from no alert and actively teaches whoever sees it to
  ignore the channel. **Before trusting an alert, query its metric's history and confirm the quiet
  state has actually occurred** — `min_over_time` over the retention window answers it in one
  query. Two causes are worth separating when it has not: the threshold may be wrong, or the metric
  may be counting a population that includes cases somebody already argued for and does not want
  reported. That second one needs a code change, not a threshold change, and the honest fix is a
  second metric rather than narrowing the first in place — a published number that quietly starts
  meaning something else takes every dashboard and rule built on it with it.

- **And check whether the signal FLAPS before choosing `for:`.** The same check failed a different
  set of subjects on three consecutive nightly runs, on an unchanged prompt digest with no
  recomputation between them. A single run was therefore not evidence, and `for:` could not supply
  the patience: the gauge moves once a night, so any single failure persists for 24 hours and
  satisfies any `for:` shorter than that. When the emitter is slower than the evaluator, the
  window has to be in the *expression* — `min_over_time(...[3d:1h]) > 0` asks for a failure on
  every run across three days — and its arms need proving against the live instance, including one
  that must stay silent.

## The negative control you already have, and threw away

A gate is only proven when you have watched it **refuse** something. That proof is expensive to
construct for an access gate — it needs a second real identity you usually cannot conjure — so it
tends to sit open as "waiting on a person" for a long time.

But it is often already in hand, wearing the wrong clothes. Measured: an operator could
not sign in to their own app, because the allow-list named a group they were not in. That was the
negative control, complete and live and on the real stack. It was filed as an outage, fixed inside
five minutes, and the open question *"still need a second identity to prove auth denies"* stayed on
the list for the rest of the session — with the answer already in the transcript.

**Why it is easy to miss: a failure arrives framed as an obstacle, and the fix consumes the
condition that produced the evidence.** Nothing is left pointing at it afterwards. Nobody writes
"…which incidentally proved the gate errs closed" in an incident note, because at that moment the
gate erring closed is the *problem*.

So, two habits:

- **When something is refused, blocked, or broken, ask what that refusal proves before you repair
  it.** A denied login, a rejected write, a 403 from a token you expected to work, a constraint
  violation on a bad insert — each is a control discriminating, which is the claim you were going
  to have to manufacture a test for. Bank it, name what it proved, and close the open question.
- **Then check the proof still applies to the CURRENT configuration.** The denial above happened
  under the previous allow-list. What it establishes is that the mechanism discriminates on group
  membership — not that today's list denies anyone. Those are different claims, and the gap is
  exactly where an accidentally-empty allow-list hides: a successful login cannot tell "allows
  admins" from "allows everyone". One read of the running config closes it.
