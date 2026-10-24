# What breaks a generated OOP client, ranked

The question this answers: given an OpenAPI document, what in it decides whether
`openapi-generator`, Kiota or NSwag emit a usable object model or a bag of `Object` /
`Map<String,Object>` / `UntypedNode`?

Ranked by how much damage each does, with the FastAPI or Pydantic construct that produces it. Every
item was checked against real issue trackers rather than recalled — the issue numbers are there so a
claim can be re-checked when a generator fixes something.

**Before believing any of this still holds, check it against your installed FastAPI and Pydantic.**
Several entries are version-sensitive and at least one (#6) is a regression that arrived with a
Pydantic major version rather than anything an API author wrote.

---

## 1. Scalar unions — `int | str`, `int | Literal["discontinued"]`

**The worst thing in this file, and the one most likely to look harmless.** Pydantic v2 renders any
`X | Y` as an `anyOf` of primitive subschemas ([pydantic#12178](https://github.com/pydantic/pydantic/issues/12178),
[fastapi discussion #14264](https://github.com/fastapi/fastapi/discussions/14264)). Kiota falls back
to `UntypedNode` — documented in a dated production case on an ASP.NET Core API emitting
`type: ["integer","string"]`, [written up here](https://gordonbeeming.com/blog/2026-01-07/fixing-kiota-when-int-becomes-untypednode-aspnet-core-openapi-3-1-bug),
where **the fix was in the API, not in the tool.**

**Measured directly rather than repeated, because the obvious claim is wrong in the letter.**
Running `openapi-generator -g java` over a real FastAPI spec carrying `int | str | None`, the
generated field is **not** `Object`. The generator synthesises a **271-line wrapper class** per union
field, `OnHand extends AbstractOpenApiSchema`, with a registry of candidate types, a custom
Gson TypeAdapter, and this as the only way to read a value:

```java
public Object getActualInstance()          // and the consumer writes the instanceof chain
```

So the *field* is typed and the *value* is not. What it actually costs is worth being precise about,
because "it generates `Object`" understates one part and overstates another:

- a 271-line class per union field, which the consumer must learn;
- an `instanceof Integer / instanceof String` branch at every read site;
- **a new runtime failure mode** — `throw new IOException("Failed deserialization … no class matches
  result")` — so a value outside the declared union fails at parse time rather than being handled;
- and none of it is visible in the field's declared type, which reads as a clean named class.

Compare the same field after splitting it into a number plus a boolean: `private Integer
onHand;` and `private Boolean isDiscontinued = false;`. Two lines, no wrapper, no branch, no
parse-time throw.

It is tempting because it is honest — the source really does send a number or the string `"discontinued"`,
and a union says so. But honesty about the wire is not the same as a usable contract.

**Fix at the spec, two ways:**
- **Split the fact into two fields** — a number plus a boolean. Usually the right answer, and usually
  already sitting somewhere else in your own codebase, because whoever wrote the storage layer had to
  normalise it to get it into a column.
- **Wrap it in a discriminated object** — `{"kind": "count", "value": 60}`. The one construct
  every source agrees is reliable. Heavier; reach for it when the variants are genuinely different
  things rather than one thing with a sentinel.

## 2. `oneOf` / `anyOf` over objects with no `discriminator`

Without one, every generator degrades to trying each subschema in sequence. Two of the failures are
outright crashes: [#15298](https://github.com/OpenAPITools/openapi-generator/issues/15298) is a
StackOverflow, [#5565](https://github.com/OpenAPITools/openapi-generator/issues/5565) is broken either
way. Kiota's docs make a discriminator effectively mandatory for object unions.

**With a discriminator it is still buggy** — [#23276](https://github.com/OpenAPITools/openapi-generator/issues/23276)
picks only one subtype, [#17763](https://github.com/OpenAPITools/openapi-generator/issues/17763) ignores
it in Python, [#18450](https://github.com/OpenAPITools/openapi-generator/issues/18450) treats an
ordinary property as one.

**Stack-specific gap worth knowing:** FastAPI and Pydantic attach `discriminator` to `anyOf`, not
`oneOf` ([fastapi#4959](https://github.com/fastapi/fastapi/issues/4959)), while most generators
pattern-match on `oneOf` + `discriminator`. That was still open at last check — **re-verify before
designing around it.**

Practical consequence: if you can express a family as one type with an open `kind` string rather than
as a union, do. A union of five shapes is a client-generation problem; one shape with a `kind`
discriminant a human can read is not.

## 3. `extra="allow"` and untyped `dict[str, Any]`

Produces `additionalProperties: true` with no `properties` — exactly the shape
[`DefaultCodegen`](https://github.com/openapitools/openapi-generator/blob/master/modules/openapi-generator/src/main/java/org/openapitools/codegen/DefaultCodegen.java)
classifies as free-form. Several generators then **refuse to emit a class at all**
([java#796](https://github.com/OpenAPITools/openapi-generator/issues/796),
[ts-angular#4119](https://github.com/OpenAPITools/openapi-generator/issues/4119),
[rust#14514](https://github.com/OpenAPITools/openapi-generator/issues/14514)) and hand the client a
`Map<String,Object>` instead of a type. For that field the whole exercise is defeated.

Note the tension with `pydantic-fastapi-traps.md` trap 5, which sometimes wants `extra="allow"` at a model
boundary. Both are true: `allow` at the boundary is right where responses pass upstream output
through, **and** it costs you the generated type. Prefer `allow` plus a test asserting zero
undocumented fields — the test is what lets you keep the declared field list complete enough that the
generated type is still worth having.

`list[dict[str, str | None]]` is the same trap wearing a list's clothes, and it is the common one: a
two-field thing that never got a name. Name it.

## 4. Un-named inline and synthesized schemas

FastAPI auto-synthesizes component names for anything that is not a single named Pydantic model at
the top level — `Body_pdf_parse_tables_api_v0_..._post`, `GenericResponse_Profile_`. **That synthesized
string becomes the literal generated class name.**

Worse: the names are **unstable across FastAPI versions**
([fastapi#14177](https://github.com/fastapi/fastapi/issues/14177) is a documented naming regression),
so a checked-in generated client breaks on a routine dependency upgrade with zero application
changes.

**This is the gotcha that bites Pydantic generics**, which are otherwise the right tool for a shared
envelope: `Page[Item]` emits a component named `Page_Item_`. Give the instantiation an
explicit name — a named subclass, or `model_config = ConfigDict(title=...)` — rather than shipping
the synthesized one.

## 5. Missing, duplicate or default `operationId`

FastAPI's default is `function + path + method`, producing
`related_items_api_items__item_id__related_get`. It is unique and it is what every generated
method gets named. Two routers reusing a function name is the direct cause of collisions
([micronaut-openapi#361](https://github.com/micronaut-projects/micronaut-openapi/issues/361)).

`ItemsApi.getItem(...)` requires one clean tag per route plus either
`generate_unique_id_function` wired up or an explicit `operation_id=` per route. **This is the
cheapest win in the file** — one function, ten lines, and every method name in every generated client
improves at once.

## 6. `required` + `nullable` interaction (a Pydantic v1→v2 regression)

v2 emits `required: [name]` **plus** `anyOf: [{...}, {"type": "null"}]` for `Optional[X] = None`,
where v1 simply left it out of `required`. A user's own words in
[fastapi#9900](https://github.com/fastapi/fastapi/issues/9900): *"the former generates better
TypeScript code."*

Nothing the API author did wrong, and nothing you can fix per-field — worth knowing so you recognise
it in a generated client rather than hunting for a cause in your own models. Related:
[og#579](https://github.com/OpenAPITools/openapi-generator/issues/579),
[og#21612](https://github.com/OpenAPITools/openapi-generator/issues/21612),
[OAI#3148](https://github.com/OAI/OpenAPI-Specification/issues/3148) on OpenAPI 3.1 nullable semantics
generally.

## 7. Enum values that are not valid identifiers

FastAPI and Pydantic emit enum **values**, not display names, so a value with a leading digit,
punctuation, or a case-collision with a sibling reproduces straight into generated code that does not
compile ([#20779](https://github.com/OpenAPITools/openapi-generator/issues/20779),
[#1475](https://github.com/OpenAPITools/openapi-generator/issues/1475),
[#18426](https://github.com/OpenAPITools/openapi-generator/issues/18426),
[#19204](https://github.com/OpenAPITools/openapi-generator/issues/19204) — the generator *altering*
your values). `x-enum-varnames` is the escape hatch and is itself
[underspecified](https://github.com/OpenAPITools/openapi-generator/issues/3246).

## 8. `format: date-time`

Lowest severity here — the wire format is unambiguous and the remaining hazards are generator-side
(which Java type it maps to, locale-dependent codegen of default values).

**But the thing that actually bites is not in this list, because it is not a generator bug: one field
name carrying several TYPES across your own schemas.** A timestamp emitted as a unix `number` on one
model, an ISO `string(date-time)` on a second and a bare untyped `string` on a third generates
`Double` / `OffsetDateTime` / `String` for one name. The generator is behaving correctly and the
client is unwritable. See `SKILL.md` §2's one-name-one-type rule and its test — no tool in this
file catches it.

---

## Tools you can actually run

- **[vacuum](https://quobix.com/vacuum/)** — single Go binary, Spectral-ruleset-compatible, no network
  dependency. Start from the built-in `spectral:oas` baseline, then add rules for: `operationId`
  required; any object with no `properties` plus `additionalProperties` reaching a request or
  response; `discriminator` required on object-member `oneOf`/`anyOf`; and **bare-primitive
  `anyOf`/`oneOf` as an error outright**, since nothing generates it cleanly regardless.
- **`openapi-generator validate`** — structural errors, not style. Free if the toolchain already has
  it, and worth running as a pre-flight.
- **Actually generate a client in a target language, then COMPILE it.** The cheapest check in this
  file, the one people skip, and the only one that answers the actual question. Two containers, about
  a minute:

  ```bash
  podman run --rm -v "$PWD:/local:z" docker.io/openapitools/openapi-generator-cli:latest \
      generate -i /local/openapi.json -g java -o /local/probe --skip-validate-spec
  podman run --rm -v "$PWD:/local:z" -w /local/probe docker.io/library/maven:3.9-eclipse-temurin-21 \
      mvn -B compile
  ```

  Generating tells you what the types look like; **compiling tells you whether they are real.** Every
  trap in this file shows up in the model directory as a wrong type name, and several of them
  (non-identifier enum values, name collisions) only show up at `mvn compile`.

  Skim two things afterwards: `src/main/java/.../api/*.java` for the method names a consumer will
  type, and `ls model/ | grep -E '_|Inline|^Body'`, which should print nothing — anything it prints
  is a synthesised name from §4, and it is a name your consumers will be stuck with.

  Do this **before** believing anything in this file, including the parts of it that were measured.
  The entry on scalar unions above was wrong in its first version because it was inherited from a
  survey rather than run.
- Unverified but plausibly useful: [superfaceai/openapi-linter](https://github.com/superfaceai/openapi-linter),
  explicitly framed as "is your spec ready for SDK generators". Its rule internals were not readable
  from a page fetch; it would need cloning to inspect.
