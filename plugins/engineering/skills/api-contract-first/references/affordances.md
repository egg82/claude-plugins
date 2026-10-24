# Let the client write good code — affordances

Load when a client polls, over-fetches, loops over N lookups, probes for what exists, or when adding a
range, `fields`, `since=`, batch or index parameter. `SKILL.md` makes a response *describable*; this
makes it *fetchable*, and it is the difference between an API a client can be efficient against and
one where **the client is forced to choose between bad options.**

HTTP's own range requests are the canonical example. Without `Range` and `Accept-Ranges`, a client
that loses a download at 99% has exactly two moves: start again, or give up. Neither is good, and no
amount of clever client code creates a third — **the third option has to be built on the server.**
That is the general shape: *a client's bad code is often an API's missing affordance*, and it will be
diagnosed in the client, where it cannot be fixed.

## The recurring failures

Each of these renders as a frontend problem:

- **No way to ask for a RANGE of the thing the client actually wants.** An endpoint answering "the
  state at moment T" forces a history slider to poll it once per step — measured at one app as about
  90 requests per minute of dragging per viewer, each one the most expensive query in the system. The
  client was careful (self-pacing, throttled, sequenced) and could not do better, because the API had
  no `start`/`end`/`step`. **Adding the range parameter turned 30 requests into 1.**
- **No way to ask for FEWER FIELDS.** A list view needs `id`, `sku`, `on_hand`; the detail panel needs
  everything. Without a `fields` parameter both pay for the heavy shape, and the client's only lever
  is to request less often.
- **No way to ask "what changed since".** Without `If-None-Match`/`ETag`, `If-Modified-Since`, or a
  `since=` cursor, a polling client re-downloads an unchanged payload forever. A 304 is nearly free
  and the client cannot manufacture one.
- **No way to ask about N things at once.** Without a multi-key lookup, a client rendering twenty
  rows issues twenty requests. N+1 is usually described as a database problem; across an API
  boundary it is a design problem.
- **No way to resume.** Cursors and ranges are the same affordance as `Range`: they let a client that
  stopped continue instead of restarting.
- **No way to ask WHAT EXISTS.** Without an index of the values that have data — which months, which
  weeks, which facets, with counts — a client that wants "the newest month with anything in it"
  can only probe: ask for a month, see it empty, ask for the one before. Measured on a history page:
  two requests per month, strictly in sequence, before the first paint. The fix is one field on a
  response the client already fetches (`available_months`), not a smarter loop.

## The request-count check

**Take one real screen or one real job, and count the requests a reasonable client must issue to do
it.** If the answer scales with the number of rows, the number of frames, or the passage of time while
nothing changes, the API is missing an affordance. Fix it there, not in the client.

And say it in the contract: **an optimisation nobody can discover does not exist.** A `fields`
parameter that is not in the schema, a cursor documented in a comment, an `ETag` nothing advertises —
each is a capability only the author knows about, which is the dead-button failure pointed at
performance.

## Built is not wired

**The sharper version, and it is the one that actually happened: an affordance BUILT and not WIRED is
worse than one never built.** A batch endpoint was added, tested, and documented as fixing a
90-requests-per-minute problem — and the client went on polling the old single-moment endpoints,
because connecting it was a separate job nobody had listed. Two documents then described the problem
in the past tense. Nothing was broken, every test passed, and the only artifact of the whole exercise
was a migration note claiming a win that had not been taken.

Three things make this specifically hard to see, and they are why it needs a rule rather than care:
the endpoint works when you test it directly; the client works, because it kept doing the old thing;
and **writing the documentation is what retires the task from your head.** So:

- **The affordance is not done when it serves. It is done when something CALLS it.** Grep the client
  for the new path before writing the sentence that says the problem is solved.
- **Write the doc in the tense that is true.** "A `/levels/range` endpoint exists; the history slider does
  not use it yet" costs one clause and cannot mislead the next person.
- **Prefer a check to a memory.** The request-count check above is the one that catches this — count
  the requests a real screen issues, after the change, and see whether the number moved.

## Then delete what it made degenerate

Every item above is phrased as an addition: the client cannot ask for X, so build the affordance. None
of them asks what the new affordance makes redundant — so a range endpoint lands *beside* the
single-instant endpoints it generalises, both keep working, and nothing fails. That is a second
mechanism added because the first fell short, with the first left in place, and it is where two
endpoints for one question come from in the first place.

So: **after adding an affordance, list the endpoints it makes degenerate, and delete them.** A span
of one instant is a snapshot; a filter accepting every value is the unfiltered list. Ask whether the
new parameter *subsumes* the old endpoint rather than merely covering the gap — the test in `SKILL.md`
§1 and `resource-boundaries.md` is the same one.
