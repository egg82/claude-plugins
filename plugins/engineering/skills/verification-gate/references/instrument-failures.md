# Instrument failures: the case files

The incidents behind the rules in the resident `verify-dont-anchor`, `no-fabricated-certainty` and
`assert-scripted-edits` preferences. Those preferences carry every rule as a claim, plus how to apply
it; these files carry the **proof** — the specific probe, the specific wrong answer, and what would
have caught it.

Come here when a rule sounds arguable, when you are deciding whether it applies to the probe in front
of you, or when you are about to overturn one. A rule with its incident attached is a different thing
from a rule asserted. This page is the index: open the one file whose kind matches the probe in front
of you.

> **This set is a SUBSET, deliberately.** The document it was extracted from carries further case
> studies that are not here. A case study was kept only where its lesson survives losing its subject;
> where the evidence *was* the environment it happened in, removing that leaves no incident behind,
> only an assertion — and an assertion with no incident is the one thing these files must not contain.
> So: do not read a gap here as "that failure mode has not been seen", and do not treat the set as
> finished. **The useful move on receiving this is to append your own** — the value is in the worked
> specifics, and yours will be about your own instruments. Add a case to the file of its kind, and a
> line here.

## Part 1 — probes that lied (from `verify-dont-anchor`)

**The further rules — stated across many incidents rather than one — are in
[instrument-failures/probe-rules.md](instrument-failures/probe-rules.md).** In one line each:

- A null result is not a negative finding; make the probe prove it can return non-zero, with the bug you hunt as the control.
- A control whose expected value coincides with what the bug produces certifies the bug; apply that test to any number you report.
- A wrong scope answers as confidently as a wrong regex; a zero prompts suspicion, a plausible count does not.
- Several checks agreeing is not corroboration unless they could fail differently; a comparison needs one instrument held fixed.
- Cheap and adjacent is what a wrong proxy feels like from the inside; a restatement is not a second source.
- A substring probe cannot tell a violation from the comment explaining it; a match proves a reference, not a behaviour.
- Verifying a component works is not evidence it is the one used; reproduce by calling, never by retyping.
- "Shipped" names a link in merge → build → pin → run → publish; a green pipeline says nothing about the branch's base.
- "Verified" needs a sha; hash what is consumed, not what is stored; retry once before diagnosing.
- A probe launched and never collected is worse than none; before writing "cannot", name the wider instrument.
- The rules kept here rather than resident: a mechanism is not evidence, repeated measurement destroys the state, some checks expire, a new capability strands "impossible", an error on both sides "matches", a guessed key tests the guess.

**[False zeros](instrument-failures/false-zeros.md)** — probes whose silence described the instrument:

- *A partially-blind enumeration cannot report what it was not allowed to see* — `x` without `r` on a directory; globs and `find` both blind.
- *The sweep and its own verification shared a filter, so the check confirmed the blind spot* — 16 → 0 with `.gitlab-ci.yml` unswept.
- *`git log -- <path>` walks HEAD, and I read its silence as "untracked"* — `--all` is the control.
- *An empty input passes a universal check, and a missing file hashes clean* — `all([])`, the md5 of nothing.
- *A keyword filter's reject pile is where the damage hides* — audit what the filter dropped.
- *A ruled-out finding travels only as far as its probe* — a dmesg grep that could not fire; say what was run.
- *A regex is a proxy for the content, and a wrong proxy answers confidently* — prefer a loop of literal matches.
- *An `except` clause for an exception the library never raises* — a manufactured count of 0 from an unreachable branch.
- *Truncating a response for DISPLAY, then parsing the truncated copy* — the one capable model rendered `UNPARSEABLE`.
- *A paginated LIST endpoint answers a different question than "does this exist?"* — `len(results) == limit` is a page.

**[Wrong instrument](instrument-failures/wrong-instrument.md)** — a correct measurement of a different configuration from the one in question:

- *A success message that names the wrong thing* — a stale revision inside a ✔; assert on the effect.
- *"No cluster access" is not "cannot read the deployed source"* — pull the image from the registry.
- *Copying a configuration: copy every field it HAS, not the fields you thought of* — the hash proved the value, not its `raw` flag.
- *A polling loop inside one transaction samples a frozen snapshot* — `stats_fetch_consistency=cache`; read the thing at rest.
- *An out-of-process probe races the in-process lock it cannot see* — the probe was the contending session.
- *"The suite passes" is scoped to a working tree, not to the project* — the pipeline list is the instrument.
- *A benchmark that repeats ONE input cannot see a fault whose cause is the MIX* — a generic plan won only under a mixed workload.

**[Controls and inference](instrument-failures/controls-and-inference.md)** — controls on the wrong axis, and conclusions the evidence did not license:

- *The control I added to remove a confound became the confound* — 639 tokens against a 16,384 cap.
- *A control PAIR, both halves testing an axis the question was not on* — both controls measured routing, the question was auth.
- *The disproof was in the row I had already fetched* — a verified mechanism licenses the class, never the instance.
- *The failure removed its own evidence from the sample* — skipped jobs left no metric; the heavy tail self-selected out.
- *A file's current content is not evidence of when it acquired that content* — date it before crediting it.
- *The fault being diagnosed had flattened the evidence the diagnostic reads* — prefer evidence written before the fault.
- *A broken discriminator that AGREES on the one case you tested reads as validated* — one real input per output class.
- *Reachability is not content, so "not in origin" over-reports by the squash-merge rate* — reachability → patch-id → file content.
- *My "old code" control ran the new code* — pytest's `pythonpath` ini beat `PYTHONPATH`; run the control from an archived tree of the base commit.

**[Timing and waits](instrument-failures/timing-and-waits.md)** — the right object read at the wrong moment:

- *A plateau cannot tell "finished" from "stuck"* — read the terminal state, not the derivative.
- *A wait condition satisfied by state that was already there* — and the over-correction a target cannot satisfy.
- *A crashlooping container is intermittently `ready`, so one sample means nothing* — trust the monotonic counter.
- *A precondition that expired between the check and the act — because of your own other fix* — re-read immediately before.

**[Gates that pass broken code](instrument-failures/gates-that-pass-broken.md)** — checks that ran green and could not go red for the defect:

- *A health gate written as a DENY-LIST of failure states* — require the success state instead.
- *A GATE THAT FAILS OPEN WHEN ITS EVIDENCE IS ABSENT — "merge when green" with nothing to be green* — assert Y exists, then that it passed.
- *A quota bounded over the wrong window — and the test that certified the bug* — assert in the observer's units.
- *A cheap prefilter in front of an expensive check quietly BECOMES the check's coverage* — test the prefilter against the detector.
- *A test that RE-IMPLEMENTS the thing it tests passes while the thing is broken* — fix the callability; mutation-test the fix.
- *EVERY FIXTURE SUPPLIED THE FIELD; MOST OF THE REAL DATA DID NOT* — put the absent case in the builder's defaults.
- *A TEST EXEMPTION IS WRITTEN BY SUBJECT AND APPLIES BY LOCATION* — state the exemption at the seam.
- *A stub that answers EVERY request makes a missing endpoint unobservable* — diff `fetch()` targets against the route table.
- *A feature that degrades HONESTLY hides its own total failure from the test of that degradation* — assert the thing is ever available.

**[Blast radius](instrument-failures/blast-radius.md)** — a fix's siblings, an addition's readers, a move's two ends:

- *A grep for the SHAPE yields candidates, and over-correction is the likelier next mistake* — does anything in scope prove the subject exists?
- *…and where that tell is absent, because the subject is REGISTRATION state* — does a remote system also know this state?
- *Widening a value set changes the readers you never edited* — the failure renders as the designed-normal state.
- *A move has two ends, and checking the read side feels like checking the move* — the writer still targeted the old anchor.

## Part 2 — artifacts that asserted false confidence (from `no-fabricated-certainty`)

All in **[instrument-failures/false-confidence.md](instrument-failures/false-confidence.md)**. The
shapes there were each shipped, and each caught by a human or a peer rather than by its author:

- *A missing measurement rendered as an ordinary one* — a timed-out probe stored `pending = 0`.
- *Unsourced and source-not-checked look identical in the artifact* — search the evidence base before dropping a claim.
- *A threshold written from memory* — every threshold traces to a citable source, or the row does not ship.
- *A LABEL that names a narrower subject than the query behind it* — write the label from the command you ran.
- *A comparison between incomparable things* — `26 < 2017` across a changed versioning scheme.
- *A count with no denominator is not a measurement, and supplying the denominator yourself is the trap* — 2.5% that was 80%.
- *A BOUND used as a value, and the caveat quoted on the way past* — a floor of 16 compared against a bar of 20.
- *A statistic that cannot express the distinction it was added to make* — a mean where the median was 1.
- *A per-item value that is suspiciously UNIFORM across independent items is the instrument, not the world.*
- *`payload.things || []` converts a contract mismatch into an empty success* — throw on a missing collection key.
- *When two sources feed one view, the working one hides the broken one* — `GROUP BY` the source.

## Part 3 — scripted edits that silently did not apply (from `assert-scripted-edits`)

All in **[instrument-failures/scripted-edits.md](instrument-failures/scripted-edits.md)**:

- A non-unique anchor takes the first match, not the right one.
- A substring anchor passes while the insert lands at the wrong nesting level.
- Two ways a scripted edit silently did nothing in one session (a rewrapped target; `sed` across a newline).
- A framework's write API can return failure instead of raising it (`$model->save()`).
- A hand-written config block can be wrong in ways a schema-read misses (`model_validate` caught five).
- A confirmation printed before the durable write is a claim about intent, not about state (`rep()`).
- The displayed output you type an anchor from is usually your own, stripped.
- A line-oriented read-back reports a false zero on a multi-line edit — and the flatten fix has the same failure; use a control.
- A parser round-trip applies your change and reflows everything else.
- A fake engine confirms whatever you already believe, because it encodes the semantics in doubt.
- `python <file>` and `python - <<EOF` resolve imports differently, so a scratchpad script edited the wrong checkout — and the explicit-path variant.
- *A published podman port added a 208 ms stall that looked like the query* — a latency through a forwarder measures the forwarder.
