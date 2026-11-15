# Held ledgers: adopting rules in code that already breaks them

Load when a repo must adopt a size, type, boundary or time gate while existing code already violates it, when two branches
conflict on a ledger, or when an agent is tempted to raise a count or loosen a check. (SKILL.md §2.)

New code starts with an empty held list that stays empty. Existing code cannot meet the limits on the
day the rule arrives, so freeze today's violations in a **per-file ledger** that may only shrink.

- **Per file and kind, never one global count.** A global count lets a fix in one file pay for a new
  violation in another. Repo A proved that with a planted swap.
- **Fail in both directions.** Over the held count, or new, fails naming the file. Under it fails too,
  as "stale, lower it", so the ledger always equals the code.
- **Parallel writers conflict on the ledger at every merge.** Take neither side whole: apply each
  branch's per-file delta (its ledger minus its merge base's) onto the target's, check no file or rule
  rose, then set the final counts from CI's "stale, lower it" output. A split moves counts between
  files, so it may re-seed only when no pre-existing file rises in any rule. (One repo's rework
  merged a dozen branches this way; taking one side whole silently undoes the other's reductions.)
- **Never raise a held count or loosen a check to get a change through.** Agents did it twice in
  repo A, and both times the real cause was a fixable regression. Put this line in the repo's CLAUDE.md
  and in every worker's brief. A Stop hook can enforce it (`held-ledger-raise-gate.sh` in this setup).
- **In a downstream fork, the upstream merge is the one change allowed to re-seed.** Code that someone
  else keeps growing can't be held to "never raise", and a gate that fails every upstream merge gets
  switched off. The merge script rewrites the ledgers after merging, so that MR's ledger diff records
  what upstream grew; every other change stays held.
- **Replacing a gate with one that measures better is a design change, not loosening**: allowed with
  evidence the old one mismeasured and the owner's approval, as its own change stating both.
- **Nor make the code worse to stay under a limit**, e.g. by cramming lines, deleting explanatory
  comments, or moving SQL work into Python to save a line. No count rises, so only review sees it. Pay
  with a real reduction, split the file, or report it.
- **A suppression is a fix the count can't tell apart:** `# pyright: ignore`, `# noqa` and `typing.cast`
  all remove an error the way a fix does. Each one names its rule and a reason on the same line, and the
  suppressions are counted in their own held ledger. Never cast a value to quiet a *safety* type (e.g.
  `cast(LiteralString, f"…")` defeats psycopg's SQL-injection guard); fix the types instead.
- Templates in `templates/`: `held_ledger.py`, `test_function_size.py`, `test_file_size.py`,
  `pyright_gate.py`, `conftest_time_gate.py`, `test_boundaries.py` and `test_doc_citations.py` (with
  its extractor `doc_citations.py`), each with its own controls and
  setup notes. Copy them, set the package path, seed with `--write`, and commit the ledger with the gate.

Using ledgers, one repo roughly halved its raw SQL calls outside `db/` while still shipping
features. The same mechanism holds pyright errors: adopted with over a thousand errors, it was tractable.
That backlog was only tractable as a ratchet.
