---
name: api-contract-first
description: "Give an HTTP API a contract a client can turn into typed objects — one schema per resource, one type per field name, typed errors, constrained parameters, affordances so clients need not poll or over-fetch. Use when a route returns bare `dict`/`Any`, near-duplicate schemas disagree on a field, deciding new-endpoint-vs-parameter, a generated client is full of `Object`, adding response models to a shipping API, or naming new fields. NOT auth or transport security."
---

# Contract-first APIs

A route that returns a bare `dict` type-checks fine, serialises fine, and publishes a schema saying
the response is "an object" — worth nothing to anyone writing a client. **The endpoint looks
documented and is not.** Nothing fails when the shape drifts, so nothing stops it drifting.

The fix is a model per response, a model per error, and constrained query parameters. It makes the
API bigger and it is worth it, for three things a dict does not give you:

1. **The schema is exact.** A client can be generated rather than reverse-engineered.
2. **The framework validates on the way OUT.** A handler returning the wrong shape fails at the
   boundary rather than in somebody's browser — the direction that matters, because an outgoing
   contract break is invisible to every test that only checks status codes.
3. **Errors are typed too.** A documented error body is something a client branches on. An untyped
   one is a string somebody parses with a regex.

The rule that keeps it honest: **the bundled client may use nothing that is not in the models.** If
the page needs a field, the field is on a model, in the schema, and available to anyone.

**And where the bundled client is TypeScript, go one further: generate its types from the spec and
delete the hand-written ones.** Then the rule above is enforced by the compiler rather than by
review, and the first compile is a free audit of every disagreement that has accumulated. Measured on
one real migration, replacing a four-figure count of hand-maintained lines: **several hundred errors
on the first run.** Roughly half were fields that had moved or been renamed — real, and the kind a
reviewer eventually catches. A large minority were **"possibly null" on fields the hand-written types
had declared non-null**, which is the half worth doing this for: each one is a place the client was
confidently formatting a value the server had never promised, and not one of them was visible in any
diff, any test or any page that happened to have data that day.

Two things make this cheap enough to be unarguable. The generation is one command
(`openapi-typescript spec.json -o schema.d.ts`), and keeping the old names costs a file of pure
aliases (`export type Device = components["schemas"]["Device"]`), so no import in the app changes.

**Gate BOTH links or you have moved the drift rather than removed it.** The chain is routes → spec →
`.d.ts`, and each hop can fall behind: one test that the checked-in spec equals what the app
generates, one CI step that regenerates the `.d.ts` and fails on a diff. Skipping the second leaves a
frontend compiling happily against a contract the server stopped serving — which is the original
defect, one link along and harder to see because everything now *looks* generated.

**That first step is necessary and nowhere near sufficient**, which is the thing this skill exists to
say. An API can carry a model on every route and still be unusable. Four things decide whether it is:
one schema per resource, one name per type, shapes a generator can compile, and **affordances that
let a client fetch exactly what it needs.**

## The test of whether you are done

**Could a consumer deserialize straight into typed objects, or would it have to hand-parse
defensively?**

Answer it by reading a consumer rather than the spec. **A client that supplies a fallback for `id`
does not trust the contract at all**, however complete, live and codegen-clean the document behind
it is. So when judging an API, do not ask whether the schema is complete. Ask **what a careful
consumer would have to write, and whether any of it is a workaround.** An illustrative case, with
the workarounds to look for, is in `references/case-invoicing-app.md`.

## Which reference

| The work is... | Load |
|---|---|
| Adding response models to FastAPI; deriving a model from live data; choosing `extra=`; constraining a parameter to an enum | `references/pydantic-fastapi-traps.md` |
| A client polls, over-fetches, loops N lookups or probes for what exists; adding range, `fields`, `since=`, batch or an index | `references/affordances.md` |
| Deciding new-endpoint-vs-parameter; two endpoints differing only by *when*, *where from*, *how many*, *who asked* | `references/resource-boundaries.md` |
| A generated client full of `Object`/`Map<String,Object>`, wrappers or synthesised names; running a generator | `references/codegen-traps.md` |
| Naming fields, shaping a collection and its counts, non-JSON routes, parameter bounds | `references/small-rules.md` |
| Citing the published guides (AIP, Microsoft, Zalando); null vs absent, pagination, errors | `references/design-canon.md` |
| Typing an API that already ships | `references/migration.md` |
| Judging a third-party API by the client written against it | `references/case-invoicing-app.md` |

## 1. One conceptual resource, one schema, everywhere

Two of the four major guides state this outright — AIP-121's *"the resource schema for that resource
across all methods must be the same"*, Microsoft's *"DO use the same JSON schema for PUT
request/response, PATCH response, GET response, and POST request/response."* Where a list view needs
less than a detail view, the answer is a client-selected subset of the one schema (sparse fieldsets,
an `embed` parameter), **never a second hand-maintained type**. `references/design-canon.md` has the
citations and the places the guides genuinely disagree.

**But the canon does not tell you where a resource ENDS**, and that is the part that actually bites.
The recurring shape is three schemas per domain — a live one, a stored one, a per-sample one — that
drift apart:

| | a real example |
|---|---|
| `Item` | live row: identity + current stock, 17 fields |
| `ItemRecord` | stored row: identity + last count + `first_stocked`/`last_counted`, 15 fields |
| `ItemCount` | one count from history, 9 fields |

Each was written when its endpoint was, each is defensible alone, and they disagree in small ways no
reviewer catches — one spells the timestamp `time` and another `counted_at`; one encodes "discontinued"
as a sentinel string inside the quantity field and another as a boolean beside it.

**Split by entity and observation instead.** The thing that has an identity and the count that has
a clock are two resources, and every endpoint composes them:

```
Item         { id, and only what does not change between counts }
StockLevel   { item_id, counted_at, and only what a count measures }

live view    ->  items: [{ item, stock }]
one item     ->  { item, latest: StockLevel | null, stored: {...} }
its history  ->  items: [StockLevel]
```

Three schemas collapse to two, every endpoint serves the same two, and the drift has nowhere to live.

**Do NOT push this across domains.** A shelf count carries a quantity and the shop it was taken in; a
supplier delivery carries a carrier and a received status. Forcing both through one `Event` means deliveries
carrying `on_hand` and shelf counts carrying `carrier`, and every consumer having to know
which fields are meaningless for which kind — precisely the knowledge a typed model exists to remove.
**Unify within a domain; use each domain's own vocabulary across domains, and say so in the
docstring** so the next reader does not "fix" it.

**And the half this section does not answer: which URL the question lives at.** Everything above
collapses near-duplicate *schemas*. It is entirely possible to do that correctly and still ship two
endpoints for one question — a live one and a historical one, a single-instant one and a range one,
each with its own defaults that drift apart. Measured on an API that had already taken this section
seriously, sharing one `StockLevel` type across both paths: three user-visible bugs from independently
chosen defaults, one concept spelled five ways across three units, and a correctness comment that
stopped being copied at the fourth duplicate of a query.

The test is one line — **two endpoints are one resource if a consumer would ever want to move
between them by changing one input value** — and the four axes a resource gets wrongly split along,
the envelope that replaces the split, and the checks are in `references/resource-boundaries.md`.
Read it before adding an endpoint whose name differs from a sibling only by *when*, *where from*,
*how many*, or *who asked*.

## 2. One field name, one type, API-wide

The rule nothing in the tooling enforces and nothing in the canon names, and the one most likely to
be silently violated in an API that otherwise looks fine.

A count over one 65-schema spec found `observed_at` emitted as three different wire types across seven
models — a unix `number` on one, an ISO `string(date-time)` on five, a bare untyped `string` on two.
A generated Java client gets `Double`, `OffsetDateTime` and `String` for one field name. Four more
names (`at`, `created_at`, `epoch`, `since`) were split the same way. Every individual model was
locally reasonable.

**The check is one pass over the spec and takes a minute** — group every property by name across all
schemas, assert one type per name. Structural, needs no network, and cannot pass vacuously if you
assert the group count is non-zero. It is the cheapest gate in this skill and it catches a class of
defect that no amount of per-model review will.

Same discipline on units: one spelling per unit, API-wide. `_ms` or `_msec`, never both — and put the
unit in the name at all (AIP-140: `weight_kg`, not `weight`).

## 3. Do not make a generator emit `Object`

Ranked list with the FastAPI or Pydantic cause of each is in `references/codegen-traps.md`. Three
worth holding in memory:

- **A scalar union is the worst thing you can write.** `int | str`, `int | Literal["discontinued"]`. It is
  tempting because it is *honest about the wire*, and honesty about the wire is not a usable
  contract. Split the fact into a number plus a boolean — and look in your own storage layer first,
  because whoever wrote the schema for the column has already done it. `openapi-generator -g java`
  does not literally emit `Object`: it synthesises a wrapper class per union field whose only accessor
  returns `Object`, so the field is typed and the value is not (measured, `codegen-traps.md` §1);
  Kiota does fall back to `UntypedNode`. Generate a client and look before repeating anyone's version
  of this, including mine — it is one `podman run`.
- **An anonymous `dict` is a type you forgot to name.** `list[dict[str, str | None]]` generates
  `List<Map<String,Object>>`, and several generators refuse to emit a class at all. It is almost
  always a two-field thing that never got a name.
- **`operationId` is the cheapest win in the file.** FastAPI's default produces
  `related_items_api_items__item_id__related_get` as the generated method name. One
  `generate_unique_id_function` fixes every method in every generated client at once.

**One measured thing that contradicts the obvious move: Pydantic subclassing gives a client
nothing.** `class Sub(Base)` emits a *flat* schema — no `allOf`, no shared component — so composing a
repeated envelope by inheritance produces N independent classes with N copies of the fields. **To
hand a client a reusable type you must NEST a named sub-model:**

```python
class Attribution(BaseModel):   # one generated class, referenced N times
    name: str; license: str; license_url: str; attribution: str

class ItemResponse(BaseModel):
    source: Attribution         # <- a $ref, which is the point
```

Verify against your installed Pydantic rather than trusting it — one `model_json_schema()` call, and
the answer decides your envelope design. **Confirmed end-to-end on a real generated client:** after
nesting, `Attribution` is one Java class referenced by 10 generated models and `Page` by 18, where
the flattened version had put five and four fields into every one of them. Same document, same
generator; the only variable was nesting versus inheritance.

**And the other half of the payoff, also measured:** because every top-level request and response is
a named Pydantic model rather than a generic or an inline shape, **zero** generated classes carry a
synthesised name — no `InlineResponse200`, no `Body_…`, no `Page_Item_`. That is the trap in
`references/codegen-traps.md` §4, and avoiding it costs nothing at author time and cannot be fixed
afterwards without renaming a client's classes.

## 4. Let the client write good code — affordances

Everything above makes a response *describable*; affordances make it *fetchable*. **A client's bad
code is often an API's missing affordance**, and it will be diagnosed in the client, where it cannot
be fixed. Three rules fire every time (catalogue and incidents: `references/affordances.md`):

- **Count the requests one real screen or job must issue.** If the count scales with rows, frames or
  time while nothing changes, the API is missing a range, `fields`, `since=`, batch or index
  affordance. Fix it there, and put it in the schema — an optimisation nobody can discover does not
  exist.
- **An affordance is done when something CALLS it**, not when it serves. Grep the client for the new
  path before writing that the problem is solved, and write the doc in the tense that is true.
- **After adding one, list the endpoints it makes degenerate, and delete them.**

## 5. FastAPI and Pydantic: the traps that serve a 200 over a broken contract

Catalogue, incidents and detectors in `references/pydantic-fastapi-traps.md`. The rules:

- **`response_model` FILTERS** — a field the model does not declare silently never reaches the
  client. Check producer fields against model fields in both directions.
- **For every field on a response model, find the code that ASSIGNS it.** A kwarg the model does not
  declare is dropped by `extra="ignore"`; a field never passed, or wired to a literal, ships as a
  constant forever. The highest-yield audit in this skill.
- **Every measurement field is optional** — a row with nothing to report must still validate.
- **Sample across the axis the data varies on**, and a contract test iterates a whole population and
  asserts it was non-empty.
- **`extra=` is decided at the one layer that discards an unexpected field**, and the loud test goes
  there.
- **Never enum a set the repo treats as open** — find out first; leave it a string when unsure.

## Method in the skill, DECISION in each repo

Do not copy this skill's reasoning into a repo. Each `models.py` keeps the argument **that repo
actually had**, because the binding reason is what stops a later reader "tidying" the convention away:

| app | why an unexpected field must not be rejected |
|---|---|
| a metrics app | rejecting one drops a *measurement*, and the app exists to refuse exactly that |
| an asset-lookup service | the entity-type list is open by design — config plus a sync, never a migration |
| a stock-keeping app | the source layer is an allow-list, so nothing unexpected reaches the model at all |

Same convention, three different reasons, and the reason is the part worth writing down locally.

**Cite this skill BY PATH from each repo's models docstring.** A skill only exists when something
loads it; a convention three repos agreed to and none references is a convention they forgot.

## Migrating an API that already ships

If typing an existing API rather than designing a new one, read `references/migration.md` first —
order of operations, why renames wait for a deprecation window, and the one exception (an
unintegrated API can rename now).

## The tests worth having

Keep them in one file next to the app's other tests. The ones that earn their place — and note that
every one must iterate a population and assert that population was non-empty:

- No documented JSON endpoint has an anything-goes response schema — with a control asserting the
  named components actually exist, since "every endpoint is `{}`" would pass the first check.
- Nothing is dropped by a response model (both forms from `references/pydantic-fastapi-traps.md` trap 1).
- No model is constructed with a kwarg it does not declare (trap 2 there, the AST pass).
- **One field name resolves to one type across every schema in the document.**
- Every measurement field is optional, so a row with nothing to report still validates.
- A member added as DATA is served — the test that would have caught trap 6 there.
- Every JSON error a client can hit has a declared body — **every error, on every path**.
- Every constrained parameter publishes its bounds — every parameter, on every path.
- The counts stay coherent: rows and the summary served with them describe one population.
- The bundled client reads no field that is not in a model. (Beware the probe: a first cut of this at
  one app used a regex whose lookbehind matched nothing and reported a clean pass on zero samples.
  Control it by asserting the number of *declared* fields the client reads is large.)
