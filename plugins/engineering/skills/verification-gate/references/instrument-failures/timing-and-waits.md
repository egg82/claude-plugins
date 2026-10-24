# Timing and waits: the right object read at the wrong moment

Part 1 of the [instrument-failure case files](../instrument-failures.md) (from `verify-dont-anchor`).
Load it when writing a waiter, a poll, a progress check or a health sample, or when a check licenses
an irreversible step a few minutes later. Every case here read a real value at a moment, or against a
baseline, that could not tell "done" from "stuck", "new" from "already there", or "now" from "when I
checked".

### A plateau cannot tell "finished" from "stuck"

Two waiters watched the same conversion job. One tracked only the row count and reported
**`VERDICT: STALLED — no new rows for ~8min while Running`**. The other tracked the row count *and*
the job's terminal condition, and reported `VERDICT: SUCCESS job completed`. Same job, same minutes,
opposite verdicts — and the STALLED one was wrong, because the count had stopped moving for the best
possible reason: there was nothing left to convert.

The derivative of a progress metric is not a health signal. A flat line means "done", "blocked", or
"the thing died", and the metric that produced it cannot distinguish them at any sampling rate. Read
the **terminal state of the work** — the job condition, the exit status, the completion marker — and
use the progress metric only to say *how far along* something still running is.

Two sibling failures from the same family, both shipped in the same session:

- **An empty read rendered as a value.** A psql call that returned nothing printed
  `converted=/<total>`, and two consecutive empties would have satisfied the "same count twice" stall
  test — a broken instrument voting for a verdict about the world. An unparseable read is UNKNOWN,
  and UNKNOWN must never be compared against a previous measurement.
- **A verdict printed on a path that exits 0.** A waiter printed `VERDICT: FAILED` and returned
  success, so the harness recorded "completed" and the failure was only visible to someone who opened
  the log. **The exit status is the machine-readable half of the verdict; if they disagree, the one
  nobody reads is the one that was true.**

And the denominator in that progress line was a constant typed in when the corpus was smaller, so the
numerator overtook it: it read like an error in the very moment the job succeeded. A ratio whose
denominator is a literal is a claim that stops being true silently — ask the question that needs no
denominator instead ("are any rows still on the old digest?").

### A wait condition satisfied by state that was already there

`until <cond>; do sleep; done` returns instantly and looks like success. Three in one session: a loop
waiting for a published image tag matched the PREVIOUS tag still sitting in the file; a loop waiting
for a pod to reach `3/3` matched the OLD pod, which had been `3/3` all along, while the new one
crash-looped; and a pipeline poller grepping for `success` matched `lint: success` in the job list
rather than the pipeline's own `status: failed`, and reported a red pipeline as green — which was
then passed to the user as fact. All three: **the condition was true of something adjacent rather
than of the thing being waited for**, and it fails in the direction that stops you looking, because
"the wait returned" reads as "the thing happened".

**And the over-correction is the same bug pointed the other way: a condition the TARGET state cannot
satisfy either.** Waiting for a sync by snapshotting `max(id)` and looping until a row with
`id > that` finished is a textbook "impossible for the prior state" — but the run had already
inserted its row, so its id WAS the baseline, and the loop waited out its full timeout on a job that
had succeeded ten minutes in. A timeout reads as *it never happened*, so you go looking for a fault
that is not there. Both were written against the clock rather than against the object: take the
baseline BEFORE starting the thing, or identify the run and watch that one — its own id, its own
pod's log line.

### A crashlooping container is intermittently `ready`, so one sample means nothing

Diagnosing an OOMKilled sidecar, I sampled the pod, saw `ready=true`, and reported the rollout
complete. It was not: the container was crashlooping and I had caught the window between start and
OOM. `restartCount` said **16**. Minutes earlier I made the mirror mistake on the same pod — reading
a `BackOff` event and a replica's `connection refused` as the database being down, when both were
artifacts of a rollout in progress and the service was serving 200s throughout. **One wrong call in
each direction, five minutes apart, on the same object.**

**For anything that restarts, the honest signal is the monotonic counter, not the instantaneous
boolean.** `restartCount` only rises, so "frozen across N samples" is a real recovery claim;
`ready=true` is a claim about one instant of a sawtooth. And a system mid-rollout produces transients
that look exactly like the fault you are hunting — so before concluding either "broken" or "fixed",
check whether a rollout is in flight (phase, a target-vs-current primary field, pod ages) and wait it
out.

### A precondition that expired between the check and the act — because of your own other fix

A migration file had to be edited (a statement in it needed privileges the application role does not
have). Editing an *applied* migration is refused by a hash guard, so the correct check was run first:
querying the migrations table returned **empty**. Nothing had been applied. The edit was safe.

It was not. In the same window, a *different* fix — creating the missing extension by hand as
superuser — made the previously-failing migration succeed, and a pod applied and recorded it with the
**old** hash. The edit then disagreed with production and the guard refused every subsequent start.

This is `preserve-before-destroying`'s "separate the check from the act" with the usual mitigation
already applied: the check *was* separate, it *was* read, and it was correct when read. **What
invalidated it was another action of my own, taken between the two.** The concurrency was not a
colleague or a cron job; it was me, fixing the adjacent half of the same problem.

**The rule: when a check licenses an irreversible edit, re-read it immediately before the edit — and
treat your own in-flight changes as concurrency.** A window of "I verified this a few minutes ago" is
exactly as unsafe as a window created by somebody else, and it is far less likely to be noticed
because there is no one else to blame.

**What went right, and is worth copying:** the guard refused rather than letting the repo and the
database diverge silently, and the recovery was exact because the stored value was a *hash* —
restoring the file from git and confirming `sha256` matched the recorded digest proved the
restoration byte-for-byte rather than by eye.
