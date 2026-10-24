# Smaller things, all cheap

Load when naming fields, shaping a collection or its counts, declaring a non-JSON route, or bounding
parameters. Each is a one-line decision that is free at author time and a breaking change later.

- **`response_class=` on any non-JSON route.** Without it the framework advertises `application/json`
  for an endpoint returning image bytes or CSV. **A documented lie is worse than an undocumented
  endpoint**, because a client author has no reason to doubt it. Found in a stock app's product-image
  endpoint and, unchanged, in two of a metrics app's.
- **`Query(ge=, le=)` rather than a hand-rolled range check.** Both reject correctly; only one
  publishes the bounds. Assert the bounds are IN the schema, not merely enforced — **and assert it for
  every parameter**, per `pydantic-fastapi-traps.md` trap 4.
- **Constrain an identifier the same way everywhere it appears.** `/things/{id}` and
  `/things/{id}/related` taking the same id with different validation is a contract that disagrees
  with itself.
- **Models catch incomplete test fakes**, and it reads as friction the first time. A fixture that omits
  a field the old dict return had been shipping is a fixture that was lying; the model is right.
- **Wrap a list in an object.** A bare array has nowhere to grow — adding a count or a cursor later is
  a breaking change, while adding a key to an object is not.
- **Name the payload key the same thing on every collection**, and take the second benefit, which is
  not obvious: **a uniform key is what makes near-duplicate detection DECIDABLE.** Measuring one API
  before and after, the check "do these two schemas share field names but disagree about a type"
  cannot tell a generic instantiated twice from two models that drifted — unless the varying key is
  always the same one, and can therefore be excluded. Before: two genuine drifts, one of which was
  `entries` carrying `Delivery` on one model and `Receipt` on another, hidden among nine
  false positives. After, with every list called `items`: zero drifts and zero false positives,
  from the same query. The key you were going to name `products` is also the thing standing between
  you and an automated answer to "has this API started duplicating itself".
- **Ship every count a reader could confuse.** "Rows matching the filter", "rows in this response" and
  "the declared population" are three different numbers, and a client that has to derive one will
  derive it wrongly.
- **A repeated parameter, not a comma-joined string.** `status=late&status=lost` publishes an
  array; `status=late,lost` publishes a string plus a convention the client has to be told.
- **One field, one meaning, across endpoints.** A `fetched_at` that means "when we called upstream" on
  a live route and "the moment you asked to reconstruct" on a snapshot route is two fields sharing a
  name, and nothing in the response says which you got. **Treat that as a symptom before fixing it as
  a naming problem:** two routes that disagree about what a field means are usually two routes
  answering one question, and renaming the field makes the split permanent and tidy.
  `resource-boundaries.md` is the other reading.
- **Two numbers in one response must describe one population, or a client will subtract them.** A
  page's `returned` beside a whole-result-set `omitted` invites `returned - omitted`, which goes
  negative the first time the result set exceeds one page — found in a real client, which had given
  up and was recounting rendered items instead. Scope every count in a response to the same
  population and say which population that is.
