# If several people share a Claude Code setup

A setup used by one person and one used by a group (a plugin marketplace, several users, work split
across projects) have the same *diagnosis* but a different *prescription* in a few places. Read
`knowledge-organization.md` (in this directory) first for the scheme; this file is only where
multiple users change the answer.

## Expect the same diagnosis

If the setup grew the usual way — a memory store as the default destination, because it's the one the
harness names — expect to find:

- **Status journals filed as memories.** The biggest single file is often a build log with dated
  sections, describing a project that has since finished or been replaced.
- **Memories asserting things that stopped being true.** An app that moved, a stack declared complete
  and torn out days later, an automation named as a service that was superseded, a migration recorded
  as blocked that shipped. Each had a sub-second probe that would have caught it.
- **Committed files pointing at agent-local memory by name.** Unresolvable to a fresh clone or to
  anyone else. Grep the repos for references to memory files.
- **An index approaching the 25KB / 200-line cap**, past which entries silently stop loading.

The `hygiene.py` in this skill finds the mechanical subset of these.

## 1. Recurring root causes are a verdicts log, not memories

Notes of the form *"issues with symptom X are usually cause Y"* are valuable and should be kept, but
they are mis-homed as memories. There is no system state a probe could falsify. They are a **verdicts
log** — the same shape as an attributed-signature file or a per-item decisions log. Keep it as a
companion file of the skill that uses it, because:

- it's *looked up by symptom* rather than recalled by luck
- it's append-only and merges cleanly when several people add rows
- it ships and versions with the skill through the marketplace
- the skill can instruct the lookup explicitly

The clause that pays for itself: **record the verdicts that changed nothing.** "Investigated, not a
bug" writes nothing anywhere else, so the next person re-investigates at full cost, and may reach a
different, wrong answer.

## 2. Per-user values belong in plugin `userConfig`, not in edited skills

The failure mode in a shared marketplace is users editing an installed skill to point at their own
project, endpoint or token. That divergence is what makes a skill un-shareable.

`userConfig` is the native fix: declare the keys in `plugin.json`, and Claude Code prompts each user
once at enable, stores per-user (sensitive values to the keychain), and substitutes
`${user_config.KEY}` into skill bodies at use.

```json
{
  "name": "<plugin>",
  "userConfig": {
    "ISSUES_BASE_URL": { "description": "Your issue tracker base URL" },
    "DEFAULT_PROJECT":  { "description": "Default project key" },
    "API_TOKEN":        { "description": "Personal token", "sensitive": true }
  }
}
```

Two limits: it's **plugin-level**, so a bare skill needs packaging into a plugin to use it; and skill
bodies have no other variables beyond `${CLAUDE_SKILL_DIR}` and backtick command injection.

## 3. Project knowledge belongs in the project repo, not the marketplace

A marketplace skill installs **globally per user**, so project-specific knowledge shipped that way
has no owner and no natural review — the same defect as a memory store, with more contributors.

When projects become a real unit of work, put project knowledge in **`.claude/` committed to the
project repo**: `CLAUDE.md`, `rules/*.md` with `paths:` frontmatter, and project-scoped skills. That
gives per-project scoping, normal code review as the contribution path, and no marketplace
round-trip to change something. Path-scoped rules make it cheap — they cost nothing until a matching
file is touched.

**Keep the marketplace for what it's genuinely good at**: versioned distribution of *methods*, with
install and update semantics you don't have to build.

**Sequencing:** `userConfig` is worth doing immediately, since it removes per-user editing pressure.
Hold the project-local pattern until projects actually exist; premature structure is just more to
maintain.

## 4. Where an MCP lookup server earns its keep

The pattern behind every stale memory: **it was a cached answer to a question something else could
answer live.**

That's the genuine server use case — not a memory server, but a **lookup server that makes memories
unnecessary**. For a workflow built around an issue tracker the split is:

| | Source | Why |
|---|---|---|
| Item **data** (status, history, links, comments) | MCP server, live | changes constantly, has an authoritative source |
| Root-cause **patterns** | companion file of the skill | judgment, accumulates, no live source exists |

The value is **shared** access with one consistent auth path, rather than N users configuring N
tokens against the same system. It does *not* apply to a single-user setup where the agent already has
direct CLI access: there, wrapping an existing command in a server buys nothing.

**Do not build a memory server or a vector store** for this. See the benchmark evidence in
`findings-and-sources.md`: a filesystem-and-grep agent beat a graph-memory product on its own
maintainer's benchmark, and retrieval was never the bottleneck.

## 5. Seed packs are the wrong shape for everything except a stance

A plugin marketplace makes it tempting to ship a "seed memory pack" that each installer copies into
their own memory store. For shared knowledge that is **the wrong mechanism**, and the reason
generalizes beyond marketplaces.

Route by where a fact's **invalidation** lives. A copy handed across a boundary has **no owner**: the
original's invalidation path — a merge request, a `/plugin update` — cannot reach it. The moment the
file lands in someone's memory dir it forks, and the only repair is asking every installer to
re-copy, which does not happen. So:

| Kind | Ship it how | Why |
|---|---|---|
| **Shared truth** — root causes, method, org facts, field IDs | **In the plugin, read in place.** A skill companion the skill reads on demand. | One owner, one change fixes everyone, `/plugin update` delivers it, and it costs the installer **zero** index lines. |
| **A stance** — push back rather than hedge, prefer subtraction | **Seed it, and say "delete what you disagree with".** | Divergence is not a defect here; it is the point. There is no shared truth to preserve, so a fork is correct. |
| **Group policy** — e.g. what may never be posted publicly, or required wording in outward-facing notes | **Enforce it**, don't seed it. In the skill body, or a hook. | Seeding policy is the worst case: it *looks* adopted while each person can silently drop their copy. |

Two forces make the seed-everything instinct actively harmful rather than merely untidy:

- **The index is hard-capped** (200 lines / 25KB, silent truncation past it) **and loads every
  session.** A large pack spends a big share of a newcomer's budget before they have written a single
  note of their own, and a bloated index recalls *worse*.
- **A `check:` probe in a shared memory file is arbitrary shell execution** on a machine belonging to
  someone who did not write it, the moment they run the probe runner. That is fine on a single-user
  box and is not fine the instant files are distributed. Whoever may author a `check:` line is a
  policy decision, and the runner's own gate should stay closed by default.

**Never seed a `user`-type note.** It is read by every installer's agent as a fact about *them*, and
whatever it asserts (a role, a level of access) is false for most of them. Ship none, and tell people
to write their own; that note is the anchor for everything else, so it has to be theirs.

**The consumption side follows from the same split.** For shared truth, the consumer should *reference*,
not copy — which also means a newcomer needs a **symptom-keyed index** rather than a pile of files, so
lookup works before familiarity does. For the personal layer, hand over the *shape and worked examples*
rather than a finished set: a preference someone did not arrive at themselves does not bind, which is
the same reason every rule in this scheme carries the failure that motivated it.

## 6. Distribution: the failure is deletion, not transport

When config moves between machines by rsync-style union sync, it rarely fails at moving bytes. It
fails at:

1. **Deletion propagation** — a union sync never deletes, so every removal needs manual replay on
   every host or a peer resurrects it
2. **Prose reconciliation** — divergent index files need judgment, so the tool correctly refuses to
   guess
3. **Transport fragility** — a per-item connection loop trips the SSH daemon's startup throttle, and
   the resulting timeouts read exactly like a host being down

**Git fixes all three**, and is less infrastructure rather than more: deletions propagate on pull,
divergence becomes a reviewable merge, each host pulls independently with no fan-out, and you get
history for free. The portable content is small — typically under 1MB for skills, rules and memory.

A marketplace already gives you most of this for skills. The gap worth closing is anything *outside*
the marketplace that's still being copied around.
