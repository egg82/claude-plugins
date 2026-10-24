# Where a resource ends

`SKILL.md` §1 says the canon does not tell you where a resource ENDS, and that this is the part that
actually bites. It then answers the **schema** half — three near-duplicate types collapse to
`Item` + `StockLevel` — and stops. This file is the other half: which URL a question lives at,
and when two endpoints are one resource wearing two names.

The distinction matters because the schema fix can succeed completely while the routing stays
wrong, and it looks like success. In the worked case below, one `StockLevel` type really was served by
both endpoints, exactly as §1 prescribes — and the two endpoints still disagreed about three
defaults, shipped three user-visible bugs, and left one field permanently null on one of them.

## The test

**Two endpoints are one resource if a consumer would ever want to move between them by changing one
input value.**

Not "do they return the same type" — that is §1's question and it is necessary, not sufficient. Ask
what the client does when the user drags a slider, widens a filter, or asks about a different
moment. If the answer is "call a different URL", the thing that varies is a **parameter** that has
been promoted to a path segment, and every parameter promoted to a path is a parameter that can now
have two defaults.

## The four axes a resource gets split along by mistake

Each is a spectrum in the domain that becomes a fork in the URL space. They are listed in the order
they are easy to miss.

### 1. Time

`/things` and `/snapshot/things`. `/things/{id}/history` and `/things/{id}/projection`. Past, present and
future are values of one parameter, not three resources.

The tell is a docstring arguing that a reconstruction is *not* a live query with a time parameter
bolted on. That argument is usually true about the **data** — a past answer is under-complete, a
future one is uncertain — and it is an argument for saying so in the response, never for a second
URL. The caveat a client needs is one it can read at runtime; a caveat that lives in the choice of
endpoint is a caveat only the author ever sees.

**Ask instead: is "now" simply the default value of `at`?** Where it is, the API is point-in-time
throughout and there is no live/historical distinction left to encode anywhere.

### 2. Source

`/things` proxying an upstream, `/snapshot/things` reading your own store. This one hides behind the
time axis and outlives it: even after you accept that time is a parameter, "but they read different
backends" feels like a reason to keep two paths.

It is not. **Which backend answered is a property of the answer, not of the question.** A client
asking "what was here at T" does not care whether that came from a cache, an upstream fetch, a
recorded row or an interpolation — it cares *how much to trust it*, which is a field.

The genuine consequence is that coverage changes discontinuously across the boundary: a store holds
only what was collected, so `at=now` and `at=now-5m` can differ enormously. **That discontinuity is
real and two URLs do not remove it — they remove the obligation to name it.**

### 3. Cardinality

One instant vs a span. One entity vs many. One layer vs all layers.

These get separate endpoints because each was built when a different screen needed it, and each is
individually defensible. The result is a set of endpoints that are degenerate cases of one another:
a span of one instant is a snapshot; a snapshot of one layer is a list.

**The diagnostic is to write them as one signature and see whether the parameters collapse.** If
`start=T, end=T` is a legal call that returns what the single-instant endpoint returns, they were one
endpoint.

### 4. Consumer

An endpoint named after the screen that needed it — `/timeline` for a slider, `/summary` for a
dashboard, `/popup` for a click handler. **A name that describes the caller rather than the answer
is the strongest available signal that the boundary was drawn around a feature, not a resource**, and
it survives long after the feature is gone because renaming a path feels like a breaking change.

Name an endpoint for what it returns. If you cannot, you do not yet know what it returns.

## Why it is invisible while you are drawing it

Three things, and they compound:

- **Each endpoint is correct in isolation.** Nothing is broken. Every test passes. There is no
  failure signal at the moment the second path is added, because the first still works for
  everything it covered.
- **The justification is written at the site of the split, in the voice of whoever understood the
  problem best.** A docstring explaining why a reconstruction is a different animal reads as
  considered design; it is also the closest thing to a written admission that the two endpoints
  answer one question.
- **The affordance catalogue (`affordances.md`) is additive by construction.** Every item in it is
  "the client cannot ask for X, so build the affordance." None of them says *and now check whether
  the new affordance subsumes the endpoint that needed it*. A range endpoint added beside the
  single-instant endpoints it generalises is that catalogue working exactly as written.

**So it needs a closing step, and it belongs in the same breath as the build: after adding an
affordance, list the endpoints it makes degenerate, and delete them.** An affordance added beside its
predecessor is a second mechanism with the first left in place — locally justified, permanently
paid for.

## What the split costs, measured

From one app — a stock-keeping API for a chain of shops, typed responses throughout, a contract
test suite, one shared `StockLevel` type across the live and stored paths — i.e. one that had already
taken §1 seriously.

**Three user-visible bugs, all the same shape: two endpoints for one question, defaults chosen
independently.** All three were diagnosed and fixed in the *client*, which is where they appeared:

| control | live default | stored default | what the user saw |
|---|---|---|---|
| store scope | the shop the user is signed in to | every shop in the chain | the whole chain's catalogue loaded into one grid, and the browser froze |
| page limit | 200 | 2500 | the grid about twelve times longer when dated back than when live |
| low-stock floor | 5 units | none | the reorder badge jumped several-fold overnight |

Each fix was the client passing one more parameter to force the two endpoints to agree. None of the
three was recognised as the same bug, because each appeared in a different layer on a different day.

**One concept, five spellings, three units.** The staleness tolerance — how old a count may be and
still be treated as the current figure — appeared as `max_age_seconds` (three endpoints, three
different upper bounds), `fresh_within_s`, `recount_after_seconds`, `stale_minutes` and
`history_days`. Every spelling was locally reasonable. No consumer could carry one value between
them.

**And the one that is not cosmetic: the fourth copy of a query is where the correctness comment stops
being copied.** The "latest location row per item, then keep the selected shops" query existed six
times. Four applied the shop filter to the *chosen* row, with a comment in caps warning that
filtering first puts anything transferred between shops in the wrong one. The fifth — in the
cross-category endpoint, written later, in another file — filtered inside the CTE. It reported stock
that had been moved out of the selected shops as still sitting in the last one it left, with a stale
timestamp and a wrong on-hand figure.

**That is the real cost and it is not a taste argument.** A duplicated endpoint duplicates its query;
a duplicated query drifts; and the copy that drifts is the one furthest from the comment explaining
why it must not.

**Plus the quiet one:** a field the live path populates and the stored path cannot (because the
column was never stored) renders as `null` on one endpoint and meaningfully on the other, with
nothing in either response saying which you got. This is `pydantic-fastapi-traps.md` trap 2's "same field, populated
on one route and permanently empty on another" — reachable without any constructor typo at all, just
by having two routes.

## The fix shape

One path per resource. The axes above become parameters. Provenance becomes a block.

```
GET /api/<kind>?at=<t>&<scope>&max_age_seconds=&limit=&offset=
    at defaults to now

GET /api/<kind>/{id}?include=<expansion>
GET /api/<kind>/{id}/history?start=&end=          # what happened
GET /api/<kind>/{id}/projection?as_known_at=&…     # what we say will happen
GET /api/overview?kinds=&<scope>&at= | start,end,step
```

And one envelope, whose provenance block is **discriminated, not nullable**:

```jsonc
{
  "as_of": "...",
  "basis": {
    "origin": "upstream" | "recorded",
    "source": { /* attribution, when something upstream told us */ },
    "max_age_seconds": 900,
    "oldest_age_seconds": 47.2,
    "coverage_note": "what this answer could not see",
    "omitted": [ { "reason": "no_clock", "count": 3 } ]
  },
  "page": { ... },
  "items": [ ... ]
}
```

**The discriminator is the point.** Without it you get one envelope with two disjoint halves of
optional fields, which is two envelopes with extra steps — and a client cannot tell "not applicable"
from "not measured", which is the `no-fabricated-certainty` failure arriving through the schema.
Note how few values it needs: `origin` is two, because the *endpoint name* already says what kind
of answer this is. See the section immediately below for why that is not an accident.

**`omitted` is a list of `{reason, count}` rather than a counter field per cause.** Causes differ
per source, so a fixed set of columns is mostly zeroes and a client has to learn all of them; one
list is learned once. An entry whose count is zero is absent rather than present-as-zero. This
replaced six per-feed spellings of "rows that matched and are not here" in the worked case, one of
which was a pre-filter total the client had to subtract from — and which went negative across a
paginated result set, so the client had given up and was recounting rendered items instead.

### The axis that is NOT a resource boundary: what the caller explicitly asked for

Time being a parameter is the rule above. This is its limit, and it was found by building the
merged version and having it rejected in one sentence by the person who would have written the
client. Their objection, restated: someone who calls an endpoint named for a projection has already
said which answer they want, and handing back the recorded figure instead overrules them.

The merged design had one per-entity endpoint returning a series over a span and resolving the *best
available basis* at each point — recorded where a recording existed, predicted beyond it, on the
reasoning that a prediction of a past event is simply a recorded event. That reasoning is true
about the data and wrong as an API: **it has the endpoint second-guessing an explicit request.** A
caller who names a prediction wants a prediction, including a wrong one — which is the only way
the predictor is testable at all.

**So two endpoints whose names describe different KINDS OF ANSWER are not one resource, even when
they cover one span and share a type.** Contrast the four axes above, every one of which is
something the caller does not care about. *What you want back* is not one of them.

Two consequences, and the first is what a design review misses:

- **Merging makes the response shape unstable over time.** Ask for a span now and get a projection;
  ask for the identical span an hour later and get recordings, with nothing in the request changed.
  A client can never rely on what it is holding. Kept apart, each endpoint returns one kind of
  thing — which is also the difference between a response you can cache and one you cannot.
- **The endpoint name then carries the mode, so the provenance block does not have to.** The merged
  design needed a per-point discriminator, a rank over four modes, and a segmented payload so
  clients would not have to re-partition it. Split, `/history` is recorded by definition and
  `/projection` is predicted by definition, and every bit of that machinery evaporates. **Structure
  added to solve a problem the merge created is the tell that the merge was wrong.**

**This section guards against over-applying the one above it.** A rule that collapses endpoints
will happily collapse two that should not be, and it feels like consistency while doing it.

What survives from the merged design, because it was right for its own reasons:

- **A VANTAGE parameter — the moment a prediction is made FROM, as distinct from the span it
  covers.** "What did we think was going to happen, standing at T−1h?" is a third question, and
  the "nearly free" below is the part to get right, because the instinct is to defer it.

  **Deferring it was the wrong call, and the reasoning is worth keeping because it generalises.**
  The judgement was "speculative, no consumer has asked, leave room for it." But the fix this design
  *already* requires is replacing a hardcoded `now()` in the history query with a parameterized
  anchor — and the vantage parameter **is** that anchor, exposed. Deferring it means deliberately
  hiding a parameter that has to exist internally anyway. **So before deferring a parameter as
  speculative, check whether the refactor in front of you already builds it**; when the answer is
  yes, "not yet" costs a second migration to add a default-valued argument.

  It also buys a comparison that is otherwise unaskable — the same span requested twice, once with a
  past vantage and once without, diffed — which is how a predictor becomes **gateable** rather than
  merely self-reported. An internal backtest field scores a model's fit against the data it was
  fitted to; only an external vantage query asks whether the projection was right.

  **The constraint that makes it honest needs its own test:** the vantage must bound what the
  producer may *see*, not merely where it starts. Same `<= anchor` clause, no extra work, but it is
  the difference between a backtest and a fabrication. Test it by adding data after the vantage and
  asserting the answer does not move.

**Where a mode genuinely cannot be served — a feed nothing records, asked about the past — return a
typed 4xx naming the reason.** Not a missing endpoint. A client discovers a limit it can read; it
cannot discover the absence of a URL.

## The check

Add to the request-count check in `affordances.md`, which counts requests for one real screen. Two more
passes, both cheap:

- **Group every query parameter in the spec by concept, not by name**, and assert one spelling, one
  unit, one default and one bound per concept. The name-keyed version of this check passes vacuously
  on exactly the drift you are looking for: `max_age_seconds` and `fresh_within_s` are different
  identifiers, so a check keyed on identifiers never compares them. (In the worked case the existing
  test did this *and* restricted itself to **path** parameters, so it quantified over an empty set
  while every instance of the defect sat in query parameters. See `verification-gate` on a check that
  quantifies over nothing.)
- **For every pair of endpoints returning the same item type, diff their parameter lists.** A
  parameter present on one and absent on the other is either a missing affordance or a default about
  to disagree with its twin.
