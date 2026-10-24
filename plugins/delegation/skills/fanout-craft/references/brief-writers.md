# Briefing a WRITER child — resources, commits, gates

Load before briefing any child that edits code, runs a test suite, or owns a worktree, database or
container. `SKILL.md` §2 lists the one-line rules; this is the detail and the incident behind each.
Long suites also need the timeout line in `brief-hazards.md`.

## Its own resources

**Put a writer's worktree on persistent disk, not the scratchpad.** The session scratchpad lives under
`/tmp`, which a reboot empties. *(incident)* A laptop died mid-run and took two writers'
worktrees, an audit file and the render helpers with it. The transcripts survived
(`~/.claude/projects/...`), the edits did not. A worktree under `$HOME` survives the crash on its own;
commit cadence (below) is the separate rule, and neither substitutes for the other (those two briefs had
also left out the commit line).

**One test database per writer, on its own port, named in the brief — or serialise them.** It is worse
than a shared scratch directory because the collision is diagnosed as something else: two children whose
pytest runs `TRUNCATE` each other's fixtures both report "pre-existing flakiness"
(`brief-incidents.md`). When a child reports flakiness, check what else you dispatched against that
resource before accepting the diagnosis; a child cannot see its siblings.

**Pass worker counts explicitly when agents share a host** (`pytest -n 2`, `--cpus=2`). Each defaults to
every core, so N suites multiply into overload, and the slowness reads as a regression. Check the runner
has the plugin first: without pytest-xdist `-n` is an argument error.

## Resume and cleanup

**A resumed agent still holds the resources its brief named** (a database port, a worktree, a
container). Reassign one while the agent is paused and resuming it creates a collision that both agents
report as green. Keep an assignment table (agent → port, worktree, container) and check it on dispatch
and on resume.

**Clean up a child's resources only when it is finished AND you won't resume it.** A resumed child reuses
the database, container and worktree it had, and "its report arrived" is not "it is done" once you have
sent it a follow-up. *(incident)* Tidying containers after one merge, I removed a sibling's
test database minutes after resuming that sibling for a fix. Before removing anything, list which
children are live and what each one owns.

## Commit cadence

**Tell a writer child when to commit: each verified step, not each edit and not only at the end.** A
child that commits only when everything is done holds hours of work in an uncommitted tree.
*(incident)* One writer sat 4.5 h with eight files modified and nothing
committed, so a usage-limit kill or a stray reset would have left the parent reconstructing what was
finished. "Commit early and often" overshoots the other way: half-made commits that fail their own tests.
The line for every writer brief on its own branch: *"commit each coherent step once its tests pass; don't
hold more than about an hour of finished work uncommitted."*

## Gated numbers

**Forbid loosening the gate, by name.** The rule is owned by `agentic-engineering` ("never raise a held
count"); the brief's job is to carry it. A child whose change trips a threshold (a held count, a
tolerance, a snapshot) raises it to get green and reports that in passing. Write *"never raise a held
count or loosen a check to pass; find what your change did and fix that, or report the exact test"* into
any brief whose work can move a gated number, and read reports for "raised", "bumped", "updated the
expected". *(incident)* Two children in one day raised a held detector count; both times the cause was a
real defect (a false positive in the detector itself) that a behaviour or
detector fix removed.
