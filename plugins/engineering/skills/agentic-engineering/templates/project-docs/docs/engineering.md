<!-- Template. How the code is built and shipped, as rules. Numbers live in the ledgers, not here. Delete these comments. -->
# Engineering

<!-- One paragraph: what this doc covers, and where design rules live instead (decisions.md). -->
How the code is built and shipped. Each rule below is something we started the other way and later had to undo.
Product and design rules are in `decisions.md`.

## The pipeline

<!-- What runs on push, what deploys, how to deploy by hand, where secrets live (names only). -->
Push to `main` runs `.ci.yml`: tests and the type checker run alongside an image build tagged `candidate-<sha>`;
when both are green, the `release` job retags it `main-<sha>`. The deploy tool picks the newest `main-` tag and
rolls it out. A branch builds `branch-<sha>` tags that nothing deploys. Secrets live in the secret store under
`recipes/*`, never in the repo.

## Patterns

<!-- The aim, then the dos and don'ts: which patterns apply here, and the service-locator / Null Object rule. -->
The aim behind every rule: **make bugs hard to create and easy to find.** A system many places call is reached
through the service locator, with a Null Object default; callers never import the implementation.

- **Do** put a policy behind one narrow interface. **Don't** let a data shape grow methods that make decisions.

## How code gets written

<!-- Agent-facing rules: gates over prose, comment policy, refactor discipline. -->
- **A rule that can be a gate is one** (see below). Prose rules drift; gated rules hold.
- **Comments only where an implementer needs them:** API surfaces carry their contract; implementation carries
  only "this looks optimizable but isn't, because...". History goes in the commit and `decisions.md`.
- **A refactor goes in byte-identical first**; a fix found on the way is its own commit, with its own test.

## Structural gates

<!-- The gate table. Ledgers are generated (--write), live apart from hand-edited files, and may only shrink. -->
A gate with a ledger holds a per-file count, seeded at what the code had when the gate arrived. It fails when a file
is over its count or new, and when it is under ("stale, lower it"). Never raise a count. Ledgers live in
`app/tests/held/`.

| Gate | Limit | Ledger |
|---|---|---|
| `app/tests/test_file_size.py` | 300 lines | `file_size.json` |
| `app/tests/test_function_size.py` | 80 lines per function | none (held list is empty and stays empty) |
| `app/tests/test_boundaries.py` | package imports: a new edge fails until added to `ALLOWED` | none (the list is in the test) |
| `app/tests/test_doc_citations.py` | backticked paths and symbols in `systems.md` must resolve | none |

## Fast from the start

<!-- Speed as a gate: per-test ceiling in CPU seconds, how to run the suite, parallelism limit. -->
The suite runs in seconds and a per-test CPU ceiling keeps it there (`app/tests/conftest.py`). Whoever writes a
test runs it under the gate before committing.

## Rules from day one

<!-- Choices made at the first line of code that are expensive to retrofit: database, migrations, types, logging. -->
- **Postgres from the first table.** SQL lives only in `db/`; the schema changes only by a new migration revision.
- **Static types, checked in CI.** A type-ignore names its rule and a reason on its line; suppressions are counted
  in their own ledger.
- **Logging.** One `key=value` line per event; ids and counts, never user content.
