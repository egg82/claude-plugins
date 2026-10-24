# Gates and tests that pass over broken code

Part 1 of the [instrument-failure case files](../instrument-failures.md) (from `verify-dont-anchor`).
Load it when writing or trusting a health gate, a prefilter, a fixture, a stub, a test exemption or a
test of a fallback path. Every case here is a check that ran, reported green, and could not have gone
red for the defect that shipped — because of a deny-list, a missing input read as satisfaction, a
replica of the code, a fixture filled in by habit, or a double that answers everything.

### A health gate written as a DENY-LIST of failure states

Draining Kubernetes workers one at a time for a kernel update, the between-node gate listed every pod
and proceeded unless a status column matched
`CrashLoopBackOff|Error|ImagePullBackOff|Pending|ContainerCreating|Terminating|Evicted`. It reported
**clean** while the pods left on a lost node showed `Unknown`, which was not on the list. The drain
advanced onto the next worker, which held the other replica of two stateful services, and both went
down with it.

**A deny-list of failure states is only as complete as the author's imagination, and its gap renders
as a PASS.** Invert it: require the SUCCESS state — every pod `Running` with all containers ready, or
`Completed` — so a state nobody anticipated fails by construction. Same asymmetry as a false zero,
and in the permissive direction, which is the one that gets acted on.

Two further holes in the same gate, both true at the time and neither visible in the column it did
check: **a database replica `Running` but not ready, still replaying its log** — the actual reason
the next worker was unsafe — and **a disruption budget sitting at zero allowed disruptions for most
of an hour**. So **a gate on one dimension of a system's health is not a gate on its health**:
enumerate the components whose absence would make the next step unsafe and assert each (ready
counts, disruption budgets, nothing-pending), rather than the one with a convenient one-line summary. Written by an author using exact assertions everywhere else in
the same script; the deny-list felt like the natural shape for "is it unhealthy" and looked no weaker
than its neighbours.

### A GATE THAT FAILS OPEN WHEN ITS EVIDENCE IS ABSENT — "merge when green" with nothing to be green

The wait-condition section ([timing-and-waits.md](timing-and-waits.md)) is about a wait that returns
on adjacent state. This is its sibling one level up: a flag whose whole purpose is to gate on a
condition, applied at a moment when the condition does not yet exist, and which reads that absence as
satisfaction rather than as "not yet".

`glab mr merge <id> --auto-merge` means *merge when the pipeline succeeds*. Run seconds after
`mr create`, before GitLab had started a pipeline, it printed

```
! No pipeline running on <branch>
✓ Merged!
```

and merged immediately. **The warning and the action are both on screen and they contradict each
other**, which is the only reason it was caught — the `✓` is what a reader takes away. The change
was fine (a full suite had passed locally minutes earlier), so nothing downstream would ever have
reported it; the defect is that a merge described as gated was not gated.

**The shape: a conditional guard has THREE input states — satisfied, violated, and no-evidence — and
tools routinely collapse the third into the first.** It is the same failure as a `filter` on a field
nothing populates, or an `all()` over an empty list, arriving as a workflow flag rather than as
code. It cannot be caught by reading the flag's documentation, because the documentation describes
the two-state behaviour truthfully.

So when arming any "do X when Y passes", **first assert that Y EXISTS**, then that it passed — two
checks, not one. Here that is one extra poll: wait until a pipeline for *this branch's own sha* is
listed at all, and only then wait for it to go green; refuse to merge if none ever appears. Note
which way it fails — toward acting, and with a success message.

### A quota bounded over the wrong window — and the test that certified the bug

A collector polling a free community API that publishes no rate limit. The politeness mechanism was a
token bucket of *45 requests per minute*, chosen as three quarters of the 60/min a sibling service
publishes.

Its first run in production got **HTTP 429 on the very first request of the pod's life**.

The bucket started **full** and its capacity was a whole minute's allowance. Every target is due at
startup, so the scheduler drew all 45 tokens back to back and 45 requests left in a few seconds —
**about four or five per second**, against a reference limit of one per second. The per-minute
average was exactly as promised and was never the number being measured: **rate limiters almost
always count in a short window, and a ceiling expressed over a long one says nothing about it.**

**The test asserted the bug as the guarantee.** It read:

```python
budget = Budget(10)
taken = sum(1 for _ in range(100) if budget.take())
assert taken == 10, "the bucket does not bound a burst"
```

That passes, and it is describing the defect: *ten immediate takes* is precisely the burst. The
author had a mental model of "a bucket bounds a burst", wrote an assertion from the model rather than
from the threat, and the green result confirmed the model. **A test written from the same
misunderstanding as the code cannot discover it** — it is not a second opinion, it is the first one
restated in another file.

**Two rules.**

*When something is limited, ask over what WINDOW the far end measures it,* and bound that window. Two
limits are usually needed and neither implies the other: a minimum interval between operations (what
a limiter sees) and a sustained ceiling (the promise about volume). The same shape appears in API
quotas, disk throughput, mail sending, and anything with a "burst" allowance.

*And make the assertion about the OBSERVER, not the accounting.* "45 per minute" is an internal
bookkeeping fact; "at most N back to back" is what the other end experiences. Write the assertion in
the units of whoever is going to complain.

**The tell, in hindsight:** a bucket that starts full means the first thing a restart does is spend a
full window's allowance at once — so a crash-looping process emits a burst *on every restart*, which
is the worst possible behaviour for the exact situation that causes crash loops. Starting empty costs
one interval of latency and removes the whole class.

### A cheap prefilter in front of an expensive check quietly BECOMES the check's coverage

A two-stage gate is the standard answer to a slow detector: a cheap test decides whether to pay for
the real one. The cost is that the prefilter, not the detector, is now the gate's true coverage —
and **nothing tests the prefilter**, because every case in the suite was chosen to exercise the
detector and therefore passes the prefilter by construction.

A redaction hook runs gitleaks on tool output, gated by a substring prefilter because gitleaks costs
~520ms of process startup. The list held `apikey`, `api_key`, `api-key`, `access_key`,
`client_secret`, `secret`, `token`, `password` — and no bare `key`. So `LOCAL_MODEL_KEY=sk-<48
hex>` matched nothing, `looks_risky()` returned False, gitleaks never ran, and a live API key reached
a transcript. Run directly on that same text, gitleaks reports it as `generic-api-key` on the first
try. The comment directly above the list asserted the filter "must be at least as broad as gitleaks'
own detection"; it was not, for the commonest rule there is.

The second defect in the same hook is the partial-success shape: two secrets sat on one enormous
`podman exec` argv line, gitleaks reported **both**, and `redact()`'s "already redacted" guard was
scoped to the LINE rather than to the secret — so once the first was tagged the line contained
`<REDACTED `, and its neighbour was skipped. The banner then said *"1 credential-shaped value(s)
removed"*, which reads as success rather than as half a job.

And the suite could not see either one. Its assertion was `"<REDACTED" in out` — *a* marker appeared
— which cannot distinguish "both removed" from "one removed and one leaked".

- **Test the prefilter against the detector, not against the corpus.** The checkable question is
  "does anything the detector would flag fail to reach it?", and the cheap way to ask is to run the
  detector directly, bypassing the filter, on text the filter rejects.
- **Derive a prefilter from the rule it gates**, rather than hand-listing keywords. Mirroring
  `generic-api-key`'s own keyword set + assignment + ≥10 value chars fixed it and added no false
  positives across 8 controls.
- **A redactor's count is of findings it ACTED on, never of secrets present** — so assert on the
  literal values being absent, not on a marker being present. A marker-only assertion passes a gate
  that leaks everything after the first hit per line.
- **A process listing is a credential surface**, which is how the argv line above came to hold two
  secrets at once: `podman exec` and similar container-entry tools pass the whole environment as
  argv, so any user on the box can read another's keys out of `ps`.
- Both fixes were mutation-tested: re-breaking each one makes the new case fail (1 of 2 values
  survives; prefilter reports a miss). A regression case added without that check is decoration.

### A test that RE-IMPLEMENTS the thing it tests passes while the thing is broken

In a suite written specifically to catch the bug it then missed.

An importer used `on conflict do nothing` against a PARTIAL unique index (`where revoked_at is
null`), so a revoked row was not in the index, the insert did not conflict, and a routine re-import
silently resurrected every decision a human had deliberately taken back. The bug was found and
fixed; the test written to pin it **survived the mutation**, because it had inlined a copy of the
importer's own INSERT rather than calling the function. Mutating the real code changed nothing the
test ran.

Why the copy got written matters more than the case: the function opened its own connection and
committed, so calling it from a test would have escaped the test transaction — and re-typing the
statement was the path of least resistance. **A function that is awkward to call from a test gets a
replica instead of a caller, and the replica passes forever.**

- **If a test contains SQL (or a request, or a command) that also exists in the code, it is testing
  the copy.** Grep your own test for the statement it is supposedly exercising.
- **Fix the callability rather than the test**: an optional `conn` parameter, committing only a
  connection you opened, made the real function drivable inside a transaction. One argument, and
  the mutation then killed the suite.
- The tell is a suite staying green under a mutation aimed at exactly the line it was written for.
  **Mutation-test the fix, not just the feature** — a case added alongside a fix is the one most
  likely to be a replica, because the fix is fresh in your hands as text.

### EVERY FIXTURE SUPPLIED THE FIELD; MOST OF THE REAL DATA DID NOT

Same project, shipped to production. The sharper half.

A classifier branched on a kind field: one value → check registry A, anything else → check
registry B. Every test passed a kind explicitly and all were
green. In the collected data, **a large share of records carry no kind at all**, because one
source reports them without one. Those fell to the else branch, so legitimate
items were reported as unregistered, rendering as a wall of red on a status
board rather than as a bug.

**Writing a fixture is an act of completion.** You construct a record with every field filled in,
because that is what a record "is" in your head — so the absent, null, empty and unknown cases,
which dominate real collected data, are exactly the ones no fixture exercises. The suite covers the
population the author imagined, not the one on the wire.

- **For any field you branch on, ask what fraction of production rows actually carry it** — one
  `group by` on the real column, before writing the tests. Here it would have shown a sizeable
  fraction with no value at all.
- **Put the absent case in the fixture builder's DEFAULTS**, not in one extra test. A helper whose
  default is "everything populated" reproduces the gap in every test written after it.
- Note the direction: an unknown value falling into an `else` branch produces a confident WRONG
  verdict rather than an error — and on a status board the wrong verdict is the alarming one,
  which gets believed rather than questioned.

### A TEST EXEMPTION IS WRITTEN BY SUBJECT AND APPLIES BY LOCATION

A polling collector's test module opened with a stated exemption, and the reasoning was correct: *"the
polling-library transport is NOT tested here: a fake would encode my belief about what the library returns,
which is precisely the thing that was wrong for an hour when a crypto dependency was installed and
every authenticated request failed."* That is a real argument against a real hazard, and it still stands.

What it did not survive is that **an exemption is stated about a SUBJECT and then operates on a
REGION.** `_walk` is the transport; the untested region was every line that shared a function with
it. The target-selection query, which has nothing to do with the polling library, called a SQL function with a
whole row instead of its scalar arguments. Three `INSERT`s sat downstream
of it. None had ever executed.

The first production cycle raised `UndefinedFunctionError: function f(<table>) does not
exist` and wrote nothing at all, on a collector that had just been declared shipped.

**Two checks could have caught it and neither can, by construction:**

- The service's own migration step **verifies that every object the code calls EXISTS** — the
  function does, at the right name and the right signature. **A verifier that checks for an object
  cannot see a call site that gets its ARITY wrong**, because the object it looks up is exactly the
  one that is present.
- Every other call site in the repo spells the three arguments correctly, so grepping for the
  symbol finds a healthy population and one outlier that looks like the others.

**The shape to carry: an exemption you write for one component silently covers whatever else lives
inside it, and nothing re-states the boundary later.** The exemption is the most confident text in
the file — it was written by someone who had just diagnosed a real hazard — so it reads as a
considered decision about everything it covers, rather than about the one thing it named.

**So state an exemption at the SEAM, not at the function.** Stub the boundary and let everything
else run for real: here, `_walk` is monkeypatched and the SQL, the counter arithmetic, the
column types and the composite keys all execute against a real schema. And when a
collector reports a failure, ask which statement it died on — **the first one**, here, which means
everything after it is still unverified and the single fix is not the whole repair.

Verified the way these case files ask for: the old line was restored and the new test reproduced the
production exception verbatim before the fix was applied.

### A stub that answers EVERY request makes a missing endpoint unobservable

A render harness photographed a web client so the pictures could be reviewed. Its fixture server was
deliberately built to answer every endpoint the client calls — a hand-picked subset had already been
rejected, because an endpoint with no fixture returns 500, that layer runs dead, and the shot
photographs as a quiet page rather than as a broken feed. That reasoning is correct and the design
is right.

It also guarantees the instrument can never show you an endpoint that **does not exist**. Measured:
three paths the client fetched on every page load — a collection, a lookup, and a
per-feed status route — were absent from the application entirely, and would 404 in production. Every
shot showed them returning 200, because the fixture server was answering. Two more resources had UI
controls, a populated database and no serving route at all. The gap survived several review passes
whose entire method was *render it and look at it*.

Three things worth carrying:

- **The completeness that fixes one blindness creates the other.** A sparse stub shows you missing
  endpoints as dead layers and hides layout; a complete stub shows you layout and hides missing
  endpoints. There is no stub that does both, so the second question needs a different instrument —
  not a better fixture set.
- **Looking at it is a real method and it has a shape it cannot see.** "Render the page and read the
  PNG" catches an unstyled list, a mis-sided panel, an unreadable header. It cannot catch a contract
  gap, because the harness stands exactly where the contract would break. Knowing *which* questions
  an instrument answers matters more than trusting it on the ones it does.
- **The cheap check was one command and it was structural, not observational.** Extract the client's
  `fetch()` targets, diff against the server's own generated schema (`openapi()['paths']`, a route
  table, a router dump). It needs no database, no browser and no running service — and unlike the
  photograph, it fails loudly. It is now a committed test rather than a habit.

The generalisation past this harness: **any test double that satisfies every request removes absence
from the set of observable outcomes.** A mock HTTP server with a catch-all, an in-memory repository
that auto-creates on read, a permissive `MagicMock` — each one converts "this does not exist" into a
plausible success, and each is chosen for a good reason that has nothing to do with absence.

### A feature that degrades HONESTLY hides its own total failure from the test of that degradation

The better the "unavailable" path, the more invisible a permanent outage in it becomes. A feature
built to render *"no summary was generated: <reason>"* looks correct in every state it can
reach — including the state where it has **never once run**.

Measured. A nightly digest job defaulted to `claude-sonnet-5` and passed
`temperature=0.0`. That parameter was removed on Sonnet 5 / Opus 5 / Opus 4.8 / 4.7 and now returns
`400 invalid_request_error`, which the client correctly classified as permanent and did not retry —
while Haiku 4.5, which the codebase's two *other* model-calling jobs both use, still accepts it. So
one job failed on 100% of requests and the other two were fine.

Nothing caught it. The feature's own test —
`test_a_failed_model_call_marks_the_entry_unsummarised_not_empty` — passed throughout and
**would have passed forever**, because it asserts the behaviour on a failed call, and every call was
a failed call. The unit tests mocked the client, so they never saw a 400. The integration path had
no assertion about arguments. It surfaced only because a model-comparison run put the arms side by
side: 48/48 failures on two models against 48/48 successes on a third.

**The tell is structural, not textual: a test of a failure path cannot distinguish "handles errors
correctly" from "errors every time."** Those are the same observation. Asking the test to be
stricter does not help; it is measuring the wrong thing.

Two fixes, and the second is the one that generalises:

- **Assert the ARGUMENTS, not the error handling.** `assert "temperature" not in captured_kwargs`
  fails on the defect and cannot be satisfied by a graceful degradation.
- **Gate the PAIRING at the repo level.** The real fault was a *combination* — a model that rejects
  a parameter, and a call site that sends it — and neither half is wrong alone. A source scan over
  every call site, checking each job's configured model against whether that site passes the
  parameter, catches the next job too. Without it, the next one rediscovers this at the cost of a
  whole measurement round.

Generalises to every "optional dependency / graceful fallback" surface: a feature flag that is
always off, a cache that never hits, a retry that always exhausts, an enrichment that is always
skipped. **When a feature is designed to be fine when something is unavailable, add one assertion
that the thing is ever actually available** — a success-path assertion, not another failure-path
one. Related, from the other direction: *A stub that answers EVERY request makes a missing endpoint
unobservable* above, and [Part 2](false-confidence.md)'s *A missing measurement rendered as an
ordinary one*.
