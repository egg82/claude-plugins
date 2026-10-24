# FastAPI and Pydantic traps, each of which cost someone real time

Load when adding response models to a FastAPI app, deriving a model from live data, choosing `extra=`,
or constraining a parameter to an enum. Each trap is a way a typed API goes on serving a 200 while the
contract is wrong; the tests that catch them are listed in `SKILL.md`.

## 1. `response_model` FILTERS — an under-described model drops fields SILENTLY

The one to internalise. FastAPI passes the response *through* the model, so a field the model does not
declare simply does not reach the client. Status 200, valid JSON, nothing in the logs, and a broken
page. Applying models to a metrics app's chart endpoint quietly removed `span` and `bars[].note` from
one board on the first run.

**Two checks, and they fail differently — you want both:**

- **Structural, and the better one.** Assert the producer's declared field list equals the model's
  field set, **failing in both directions**. Produced-but-undeclared is data being dropped;
  declared-but-unproduced is an aspirational model. Needs no network, no database, and cannot pass
  vacuously on an empty sample.
- **Live.** Diff what the handler RETURNS against what the endpoint SERVES, per endpoint, and assert
  the difference is empty.

The live check alone is not enough, and the reason is subtle: **it passes trivially for any field no
current row populates.** A field the schema forgot, that nothing sets today, is invisible to it and
caught by the structural one. Control either by deleting a field from a model and confirming the
check goes red.

## 2. The CONSTRUCTOR drops an unknown kwarg, and neither check above sees it

A second mechanism wearing trap 1's clothes, found live in a stock app. A handler built
`Delivery(..., receipt_status=row[7])` where the model declares `status`. Pydantic's default
`extra="ignore"` discarded the kwarg; the field serialised as `null` on that endpoint and correctly on
the sibling endpoint that spelled it right. **The same field, populated on one route and permanently
empty on another** — precisely the "declared but never filled in" complaint people make about other
people's APIs.

Trap 1's structural check compares a *source module's* field list to a model. This is a *handler's*
kwargs against a model, so that check cannot see it — and the live check cannot either, because
`null` is a perfectly valid value for an optional field.

**The detector is an AST pass and runs in under a second:** walk every `Call` whose callee names a
model, diff `node.keywords` against `model_fields | aliases`, report any kwarg that is not a field.
Worth running over any codebase where models and handlers live in different files.

**But one shape of this needs no detector at all, and it is the one that recurs: a model built by
SPLATTING a producer's dict — `Coverage(**scenario.coverage())`.** There, `extra="forbid"` on the
model turns the silent drop into a construction-time error, so the producer and the model cannot
drift without something going red. Measured on a real reporting app: the producer returns three keys
or five depending on the scenario, the first model declared three, and the two it would have dropped
were precisely the fields that say the answer is PARTIAL — the ones naming why a case went unevaluated
and what was ignored. The silent failure was a scenario claiming complete coverage it did not have.
Note the asymmetry that makes `forbid` right *here* specifically and wrong as a default (trap 5): on a
splat the input is your own code one function away, so a 500 is a bug you introduced seconds ago, not
a page taken down by an upstream adding a field.

It also argues for the entity/observation split in `SKILL.md` §1 — the bug was only *possible*
because two near-duplicate models disagreed about a name.

**And its exact blind spot, which an adversarial review found six live instances of: that check reads
the kwargs that ARE there, so it cannot see an OMISSION.** A field added to a model *after* the
handler was written is never passed, defaults quietly, and ships as a constant — `0`, `null`, `false`
— on every response forever. It is the "declared but never filled in" property that makes somebody
else's API untrustworthy, arriving through your own diff, and it is *likeliest* in exactly the
situation where you are being careful: adding a field because a reviewer pointed out a silent drop.

Two shapes of it, both measured in one codebase:

- **The field added and never wired.** Worst case seen: a count was computed, logged, and then not
  passed — beside a comment asserting the field did not exist, a few lines from where it was declared.
- **The field wired to a constant.** `cached=True` hardcoded on a path that had just fetched;
  `enabled=True` hardcoded where the real predicate is one call away. These are worse, because they
  survive a "is anything null?" check and are only visible by reading the assignment.

**The check is the one from trap 1 pointed the other way: for every field on a response model, find
the code that ASSIGNS it.** A field with no assignment anywhere, or whose only assignment is a
literal, is the finding. It is a grep per field and it is the single highest-yield audit in this skill
— the constructor pass, the schema gates and the live diff all miss it by construction.

## 3. A required field breaks the rows that have nothing to report

Deriving a model from live data by walking each row's KEYS **cannot see a key that is absent
entirely**. A field typed required because it was null on every row ever observed, then 500'd every never-observed
host, which carries identity fields and no measurement keys at all.

**Absence and null differ in the measurement of the data as much as in the data.** Make every
measurement optional. In an app whose subject is coverage, this is just "unmeasured is omitted, never
zero" moved into the schema — and it means the schema cannot reject the very rows the product exists
to surface.

## 4. Sample across the axis the data VARIES on

Modelling a family of endpoints from one member is the one-sample trap. Two chart kinds from one
board; enumerating five found a third plus three more chart-level keys. A venue-booking app sampled
four venues and exactly one field's TYPE varied: an integer seat count at most venues and the literal
string `"standing"` at one. One venue gives you whichever it happened to hold.

The axis is geography, tenant, board, source — whatever the data actually varies along. **Rows of one
sample are not a sample.**

**And the same trap eats the TESTS you write to prevent it**, which is how it survives. All three of
that app's contract tests asserted over a sample of one: the error-shape test checked one route's
502 and nothing else, so five 404s serving an undeclared body passed unnoticed; the query-bounds test
checked three parameters of seventy, so an unbounded `limit` was invisible. **A contract test names a
population or it is not a contract test** — iterate every path, every parameter, every model, and
assert the iteration was non-empty.

## 5. Know which layer DISCARDS an unexpected field, and put the loud test THERE

`extra=` is a decision, not a default, and the right value depends on where the discard happens:

- **`ignore`** (the default) silently drops an unexpected field. Almost never what you want — and see
  trap 2 for what it does on the way IN.
- **`forbid`** rejects the response — loud, and it takes the page down over one new field.
- **`allow`** carries it through undocumented, which needs a test to stay honest.

But the rule is not "use allow". It is that **an unexpected field is discarded at exactly one layer,
and the test belongs there.** Where responses pass upstream output straight through, that layer is the
model boundary — use `allow` plus a test asserting zero undocumented fields, so CI shouts while
production keeps serving. Where the source module is an explicit allow-list, the new field is dropped
*at the source* and never reaches the model: `allow` buys nothing there and the test belongs on the
source's field list. **A guard on the model boundary leaves the other half unguarded, and vice versa.**

## 6. An enum can contradict a product invariant

The sharpest one, because it reads as pure rigour and is what a reviewer would praise on the way past.
Constraining a path or query parameter to a closed set is correct only if the set is genuinely closed.

A metrics app nearly shipped `board` as an enum of the boards that existed that day — while
the boards live in a lookup table keyed by view, so a board is added by an INSERT and one
more was already planned. It would have returned 4xx for a board that genuinely exists, while the
untyped endpoint it replaced served it fine. A lookup service has the same shape in sharper
form: its entity-type list is open by design, so an enum over `object_type` would close the thing the
product is built on.

**Before constraining a parameter to a closed set, go and find whether the repo documents that set as
OPEN.** Where there is no statement either way, leave it a string and say so — wrongly closing a set
costs far more than an undocumented range. AIP-126 gives a usable bar: if the set gains values more
often than about once a year, it is a string, not an enum.

And note what the enum was actually buying: a helpful error. Get that instead by validating against
the real source at request time and naming the valid values in the message. It is more truthful anyway
— it lists what exists now, not what existed when the code was written. Where some members have a
specific model and others do not, serve the rest through a generic model typed at the shared core, and
let the response SAY which it is rather than making a client infer it from which URL answered.
