<!-- Template. The inventory an agent checks before building something new. Delete these comments. -->
# Systems

<!-- Opening: who reads this, what to do with it, and the update rule. -->
The inventory an agent checks before building something new (`CLAUDE.md`, the fit pass): what kind of thing is this,
and which row below already answers that question? Extend or combine that system; add a row only when none fits, and
say why in the open-work item's "Fits into:" line. Update this file in the same change that adds, merges or retires
a system, and when a copied rule below is removed (delete its entry). Paths are under
`app/`.

<!-- Say how systems are reached (service locator, Null Object default) and which rows are not behind it yet. -->
A system many places call is reached through the service locator (`recipes_app/services.py`): one named interface,
a Null Object default, callers never importing the implementation. "Who asks, how" says whether a row is behind it
yet. Every backticked path and `module.symbol` here must resolve (`tests/test_doc_citations.py`); a planned one
reads `` `planned: <target>` ``, which skips it while its target is missing and fails once it exists.

## What counts as a system

<!-- The four-part test. Everything else is a plain import. -->
A thing is a system only if all four hold:

1. **Many callers, across packages.** One caller is a function call.
2. **One question, behind a narrow interface.** If the interface keeps widening, it is two systems.
3. **A second implementation is plausible.** An A/B variant, a Null Object, a fast stand-in for tests.
4. **It owns a policy or state**, not a data shape.

## Pricing and units

<!-- One section per area, each a table. Section names are domain nouns, not layers. One row per system. -->
| System | Owns (the question it answers) | Where | Pattern | Who asks, how |
|---|---|---|---|---|
| Unit conversion | How many grams is "1 cup" of this ingredient? | `recipes_app/units/convert.py` (`to_grams`); page `src/units.ts` `toGrams` | Strategy per ingredient density table | Scaler via `services.units`; the shopping list still has its own copy (below) |

<!-- The systems in hiding: one rule written in two or more places. Check each by reading every copy. Lead with
"Already disagrees:" where the copies have drifted -- that is the finding that matters most. Say what removes
the copy (and point at its queue item), or say why the copy is forced (another repo, another runtime) and
what gates it. Delete an entry when its copies are gone. -->
## Rules copied by hand

Each entry is one rule written in two or more places, checked by reading the copies. Where the copies already
disagree, that comes first.

- **Grams per cup, twice.** `recipes_app/units/convert.py` (`to_grams`) and the shopping list's own table.
  **Already disagrees:** the shopping list rounds to whole grams before summing, so two recipes asking for half a
  cup of flour each show 120 g instead of 125 g. Removed by the list calling `to_grams` (issue #1).

<!-- The no-op verdicts: things checked against the four-part test and found not to be systems (or found fine).
Recording them is what stops the next agent asking the same question and answering it differently. -->
## Looked at, and not systems

- **The recipe importer.** One caller (the import page), one implementation; a tool, not a system.

## Maintenance

<!-- Tools and scripts that read the systems above. -->
Tools live in `app/tools/` (`import_recipes.py`, `ship.sh`).
