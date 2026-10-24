# Project-doc templates

Skeletons for the doc set an agent-built repo keeps. Copy `CLAUDE.md` to the repo root and `docs/*` to its `docs/`;
every section has a comment saying what goes there and one invented example (a recipe tracker) to replace. Delete
the comments and the examples when you fill them in. Method: `../../SKILL.md`.

- `CLAUDE.md`: short router plus the few rules that must fire every session (fit pass, never raise a held count).
- `docs/engineering.md`: how code is built and shipped; the gate table points at ledgers, not counts.
- `docs/systems.md`: the inventory checked before building anything new; one row per system.
- `docs/decisions.md`: design rules as distilled decisions, with rejected options and dated supersessions.
- `docs/open-work.md`: the queue, with "Fits into:" lines; delete items when they ship.

Fill in this order: `engineering.md` (with the gates and ledgers in CI), `decisions.md` (what you already know you
want), `systems.md` (rows for what exists; the citation gate checks it), `open-work.md` (the backlog, worst
offenders first), then `CLAUDE.md` last, as a router over the others plus the rules that must fire unread.
