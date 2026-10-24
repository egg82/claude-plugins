# What the published canon says, and which parts to ignore

Four rule sets were read for this, not cited from memory: Zalando's RESTful API Guidelines, Google's
API Improvement Proposals, Microsoft's Azure REST API Guidelines, and RFC 9457. Quotes are from the
live pages, 2026-09-12.

Read this when you are about to make a naming, nulling, enum, collection or error decision and want
to know whether there is a defensible answer or whether the field is genuinely split. It is split
more often than the confident tone of any single guide suggests — **three of the four disagree about
casing**, which is a useful calibration for how much authority to grant the rest.

## The one rule everything else hangs off

All four converge on the answer to the near-duplicate-resource problem, and two state it outright:

> "If the request to or the response from a standard method ... **is** the resource or **contains**
> the resource, the resource schema for that resource across all methods **must** be the same."
> — [AIP-121](https://google.aip.dev/121)

> "DO use the same JSON schema for PUT request/response, PATCH response, GET response, and POST
> request/response on a given URL path."
> — [Microsoft Azure Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md)

**One conceptual resource, one schema, everywhere it appears.** Not `MovieResource` and
`MovieListItem` and `MovieDetail`; not `Item` and `ItemRecord` and `ItemCount`.

Where a list view genuinely needs less than a detail view, the canon's answer is a **client-selected
subset of the one schema**, never a second hand-maintained type:

- JSON:API sparse fieldsets — `fields[item]=item_id,sku,on_hand`.
- Zalando Rule 158 — an `embed` query parameter widening a canonical resource.
- AIP — list responses may omit expensive fields, same schema.

None of the four endorses per-view named types as a design goal. That drift — the same conceptual
object with different field names depending on which endpoint served it — is what none of them
sanctions anywhere, and it is the single most expensive thing you can do to a client author.

**But note what the canon does not settle: it says "one schema per resource" without telling you
where a resource ENDS.** A live stock count and a stored stock record are arguably one resource or two, and
the rule is silent. The method file's entity/observation split is the answer that held up; the canon
gets you as far as "stop minting a type per endpoint" and no further.

## Naming — genuinely unsettled, so pick and be consistent

| question | Zalando | Google AIP | Microsoft |
|---|---|---|---|
| JSON casing | `snake_case` (Rule 118) | `camelCase` JSON generated from `snake_case` IDL (AIP-140) | `camelCase` (mandated directly) |
| arrays | pluralized (Rule 120) | "repeated fields must use the proper plural form" | — |
| ids | "IDs must be opaque strings and not numbers" (Rule 174) | — | — |
| timestamps | name contains date/time or ends `_at` (Rule 235) | — | — |
| booleans | must not be null (Rule 122) | **omit the `is` prefix** — `disabled`, not `is_disabled` (AIP-140) | — |
| units | no general rule | **short suffix in the name** — `distance_km`, `width_px` (AIP-140) | — |

**Casing has no canonical answer.** For a Python backend take Zalando's `snake_case`, because it
matches Pydantic field names with zero aliasing and every alias is a place the wire and the code can
drift. Generators handle either.

**Google's boolean rule directly contradicts Java/C#/TypeScript codegen convention**, which wants
`isDisabled` getters. Follow Google on the wire and let the generator add the prefix — a generated
`isDisabled()` over a wire field `disabled` is normal and correct.

**Take AIP-140's unit suffix without hesitation.** It is the cheapest rule in this file and the one
whose absence causes the most silent arithmetic errors. One spelling per unit, API-wide — `_ms` or
`_msec`, never both.

## Null vs absent — take Zalando, not Microsoft, and this is a deliberate departure

Microsoft is the outlier and the stricter one:

> "DO NOT send JSON fields with a null value from the service to the client. Instead, the service
> should just not send this field at all."

Zalando permits null but requires the two to be indistinguishable:

> Rule 123: "If a property is defined to be not `required` and `nullable`, both cases must be
> handled in the exact same manner."

The obvious reading is that Microsoft's rule is better for a typed client, since it removes a
tri-state. **Reject it anyway, for two reasons neither guide considers:**

1. **`exclude_none=True` makes the response's KEY SET vary per row.** Two items in one array then
   have different shapes, and the "nothing is dropped by a response model" check (`pydantic-fastapi-traps.md`,
   trap 1) has nothing stable to assert against. You trade a tri-state the client resolves for free —
   Jackson, `System.Text.Json` and Pydantic all collapse absent and null into one `Optional` — for a
   contract check you can no longer write.
2. **In a measurement API the distinction is the product.** "Unmeasured" and "measured as absent"
   are different facts, and an app whose subject is coverage needs the option to say which. Emitting
   a stable key set with explicit `null` keeps that door open; omitting the key nails it shut.

So: **explicit `null`, stable key set, every measurement optional.** Do take Zalando Rule 124 —
an empty collection is `[]`, never `null`. A client should never branch on which flavour of empty
it got.

## Enums — the canon agrees with `pydantic-fastapi-traps.md` trap 6

Neither guide bans closed enums, and both build an escape hatch, which tells you how often this goes
wrong:

- **Zalando `x-extensible-enum`** (Rule 112): document values via `examples` rather than a closed
  `enum`, so adding a value is a compatible change. The sharpest citable rule on open sets.
- **Google AIP-126**: every enum carries a reserved `*_UNSPECIFIED` zero value so an unrecognized
  wire value decodes somewhere instead of throwing — and enums "should receive new values
  infrequently," practically "no more than once a year." **For anything more volatile than that,
  AIP-126 says use a plain string.**

A naively generated Java or C# enum from a closed OpenAPI `enum` throws on an unknown value. That is
the whole risk: adding a value server-side breaks every deployed client. AIP-126's once-a-year bar is
the usable test — if you cannot promise it, the field is a string.

## Collections, pagination, versioning

- **Never a bare top-level array** (Zalando Rule 110). An object has somewhere to grow; an array does
  not, so adding a count later is a breaking change.
- **Conventional parameter names** (Zalando Rule 137): `limit`, `offset`, `cursor`, `sort`, `fields`,
  `embed`. Use these spellings rather than inventing `max_results` or `lookback_days`.
- **Cursor over offset** where the collection mutates under paging (Zalando Rule 160, AIP-158).
  Tokens must be "opaque (but URL-safe) strings ... not user-parseable."
  **The tradeoff dissolves if the request pins the population** — an explicit `start`/`end` window
  over an append-only store makes offset paging stable, because the rows a page can contain were
  fixed at request time. Reach for a cursor when you cannot pin it, not by reflex.
- **Signal the end by omitting the next token**, not by a boolean (AIP-158, Microsoft, independently).
- **Do not put the version in the URL path** — the one versioning point all four agree on. For a
  small app this mostly means: do not build the `/v1/` habit reflexively, and commit instead to
  "additive-only, clients tolerate unknown fields and unknown enum values" as the compatibility
  contract.

## Errors — RFC 9457, plus one thing it lacks

[RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) (obsoletes RFC 7807) gives you `type`, `title`,
`detail`, `instance`, served as `application/problem+json`.

**Its `type` is a URI, which is a poor `switch` target in Java or C#.** Add a short stable `code`
token alongside — JSON:API's `code` member and Microsoft's `error.code` are the same idea. That is
what a client actually branches on.

For per-field validation errors, JSON:API's `source.pointer` (a JSON Pointer into the request) is a
ready-made normative shape; RFC 9457 only illustrates one informally.

## What to skip for a small app

- **HATEOAS.** Under a fifth of surveyed real APIs implement it; clients hardcode paths anyway,
  which defeats the point. Skip entirely.
- **JSON:API's full wire format** — the separate `relationships` block, `/resource/1/relation`
  sub-URLs, distinct endpoints for attributes vs relationships. Even sympathetic critiques call it
  cumbersome for ordinary CRUD. Take the ideas (resource identity as type+id, sparse fieldsets,
  `included` for eager loading); leave the format.
- **Media-type versioning** (Zalando) and **a mandatory `api-version` parameter on every operation**
  (Microsoft). More ceremony than a slowly-evolving app needs.
- **Long-running-operation machinery** (Microsoft's 202-plus-polling) unless you actually have async
  work.
- **A blanket money-object or full unit taxonomy.** Worth doing for the two or three fields where the
  unit is genuinely ambiguous; not worth adopting as house style for every number.
