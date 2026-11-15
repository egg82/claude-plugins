# Structure: files, inventory, layering, types, comments

Load when splitting a god file, setting up a repo's `docs/systems.md`, adding a layering or citation gate, or writing
the commenting rule into a brief. The fit pass itself stays in SKILL.md §3. (SKILL.md §3.)

- **Small files, each doing one thing, grouped in subdirectories, frontend and backend alike.** A file
  is a group of functions with one purpose, not a feature's worth of everything. Split before a file
  passes a few hundred lines. That rule plus an immediate split took repo A's entry-point file from several
  hundred lines to a handful. The split files never regrew.
- **Small files don't stop long functions.** Function size needs its own gate: 80 lines, held.
- **Test files count.** Point the file-size gate at tests as well as source, and split a test file by
  the subject it tests. A repo that held function size but not file size grew a test file of over ten
  thousand lines in which no function was over the limit.
- **Without a fit pass, agents build "systems in hiding"**: the same rule hand-copied two to four times, drifting apart.
  Say why on the work item when building new ("Fits into: …"). Pattern sources for the fit pass: `references/patterns.md`.
- Skeletons for `CLAUDE.md` and `docs/{engineering,systems,decisions}.md` (plus `open-work.md` for a repo with no forge): `templates/project-docs/`.
- **A systems inventory** (`docs/systems.md`): each system's one question, where it lives, its pattern,
  its callers. Under the tables, a **"Rules copied by hand"** section lists each rule written in two or
  more places, leading with "Already disagrees:" where the copies have drifted and naming what removes
  each copy; **"Looked at, and not systems"** records the no-op verdicts so nobody re-asks. Something counts as a system only
  if all four hold: many callers across packages, one question behind a narrow interface, a plausible
  second implementation, and it owns policy or state rather than a data shape. Everything else is a
  plain import. **Gate the inventory with a citation test:** every backticked path and
  `module.symbol` in it must resolve by real import, with a floor on how many it finds (the shape of
  `templates/test_doc_citations.py`). A planned reference reads `` `planned: <target>` `` inside the
  backticks: skipped while the target is missing, and **failing once it exists**. A repo with no
  package to import (shell, Containerfiles) can only check that a code-shaped name still appears as a
  word in its code, which is weaker. Without the marker, writers drop the backticks to get past the
  gate, and the reference silently stops being checked.
- **Package layering as an executable allow-list.** A new import edge fails until it's added, which is
  the moment the design question should be asked.
- **One home per fact.** A value the server and the client both need lives in one data file, or is
  served. Generated files never share a directory with hand-edited ones: a file's location says what
  it is.
- **Static types, checked.** Annotate even where it is verbose, and make a checker (pyright/mypy, tsc)
  gate CI. Annotations nothing checks drift into claims.
- **Comments where an implementer needs them, and almost nowhere else.** API surfaces (interfaces,
  public functions, wire models) carry their contract and purpose. Implementation code carries only
  the rare "this looks optimizable but isn't, because…". Decision history and bug stories go in the
  commit and the decisions doc, where they don't age in place. Agents, Opus especially, narrate
  history into comments, so the rule goes in every writer's brief and the review. As a reference
  shape, a hand-written Java service is 22% comments in its API module and about 1% in implementation;
  one agent-written app was 29% everywhere.
