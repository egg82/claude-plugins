<!-- Template. A short router plus the few rules that must fire every session. Detail lives in docs/. Delete these comments. -->
# CLAUDE.md

<!-- Reading order: what to read before proposing anything, and where the queue is. -->
Read `README.md`, then `docs/decisions.md`, before designing anything. The queue is `docs/open-work.md`.
How code is built and shipped: `docs/engineering.md`. The inventory of systems: `docs/systems.md`.
Deploy is CI on push to `main`.

<!-- The fit pass: verbatim in spirit; adapt the pattern source to the domain. -->
**An ask that adds a new kind of thing (a system, new data, a new schedule) starts with a fit pass, not a design:**
what is it an instance of, which system in `docs/systems.md` already does that kind of thing, and which known
pattern solves it? Extend that system or combine the two; build a new one only when none fits, and say why. Its
open-work item carries a "Fits into:" line. Tweaks to wording and numbers need no fit pass.

<!-- The held-count rule: one line, names where the ledgers are. -->
**Never raise a held count to get a change through; split, reduce or report instead.** The gates and their ledgers
are in `docs/engineering.md`, "Structural gates".

<!-- Rules that must hold even if nothing else was read. One bullet each, one sentence plus a pointer to the
decision that owns the detail. Add one right after an incident, not before. -->
Rules that must hold even if nothing else was read:

- **Small files, each doing one thing**, grouped in subdirectories. Split before a file passes a few hundred lines.
- **Behaviour keys on fields, never on words in natural-language text.** Authored text carries an explicit field.
- **Logs carry ids and counts, never user content or secrets** (`docs/engineering.md`, "Rules from day one").
- **Cooking-time estimates are never shown as exact** (`docs/decisions.md`, "Estimates are ranges").
