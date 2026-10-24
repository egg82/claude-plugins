# Judging an API by what its consumers have to write

An illustrative composite: an invoicing app's API, with details invented to carry the lessons rather
than taken from any one product. Use it for the shape of the reasoning, not as a citation.

## The question

Do not ask whether the schema is complete. **Ask what a careful consumer would have to write, and
whether any of it is a workaround.** A spec can be live, codegen-clean and still fail this test,
because completeness is a property of the document and trust is a property of the client.

## The workarounds that give it away

Read a hand-written consumer, not the spec, and look for these:

- **A default for every field.** An accessor such as `Fields.intOr(node, "id", -1)`, repeated for
  `number`, `settled`, `dueOn` and the rest. A client that supplies a fallback for `id` has stopped
  trusting the contract altogether — and that is a verdict on the whole document, not on any one
  field.
- **Ids stored instead of embeds read.** `invoice.taxScheme()` ignores the embedded object and
  fetches by `taxSchemeId`, because some routes embed the relation and the list routes send only the
  id. The client chose a round trip it can rely on over an embed it cannot.
- **Bean mapping abandoned despite honest nullability.** The schema marks optional fields nullable,
  and the client still hand-parses, because nullability says *this may be absent* and nothing about
  *which endpoints fill it in*. **Declaring a field nullable is a statement about the type; a client
  needs a statement about the endpoint.**

Each of these is a missing guarantee diagnosed in the client, where it cannot be fixed.

## What made the workarounds possible at all

- **Stable integer ids used as real foreign keys** (`customerId`, `taxSchemeId`, label id arrays).
  This is why the missing embed was slow rather than fatal: there was always a way to re-fetch.
- **One paging envelope reused verbatim** — `{offset, limit, orderBy, order, total, items}` on every
  paged list — so one deserializer covers them all. A per-type instantiation with an identical
  interior is exactly what a Pydantic generic emits.
- **Real OpenAPI enums** rather than conventions learned out of band, and **a spec served off the
  running binary**, so it cannot drift from what you are talking to.

## Where the contract fails, as rules

1. **Never let two schemas share both words in reversed order.** `BatchPaymentDto` as a two-field
   stub beside `PaymentBatchDto` as a full record: same words, swapped, opposite cardinality, and
   only the properties tell them apart.
2. **Do not name an enum like a payload.** `ExportOutcome` as `enum: [pending, done, failed]` next to
   `Export` and `ExportDto` leaves one of three near-identical names not being an object.
3. **Do not let a family that varies along one axis share nothing but a root word.** A `Tax*` cluster
   — a rate, a rate with an effective date, regional thresholds, a user's scheme, a rule group nested
   in it — where `TaxRateDto` and `TaxSchemeDto` differ by one word and mean unrelated things.
4. **Return a field-level error, never a raw internal exception.** A misspelt key should produce
   "lineIds is required", not a stack trace from the server's runtime.

## Calibration

Confusable names are usually few and cluster where the product's own concepts overlap; most of a
family is disambiguated by a consistent suffix. So **count your own**: the share of schemas a reader
could mistake for a sibling is a one-pass check on any spec, and a rising share is the early sign of
an API starting to duplicate itself. Do not generalise from the sharp cases to "this API is full of
near-duplicates".
