# Where knowledge goes, and why

The scheme this skill audits. Read it when extending the scheme, when something doesn't obviously
fit, or when reorganizing a setup that has drifted into using memory as a catch-all.

## The routing question

**Not "what is this about" — "what would make it wrong."** That determines the home:

| Goes stale when… | Home | Example |
|---|---|---|
| you deliberately revise the method | the skill's `SKILL.md` — shareable, versioned | "the allow-list is per-IP, not per-signature" |
| the code beside it changes | a doc in that directory | `services/<app>/README.md` |
| the world moves underneath you | a data file beside the runs, looked up by key | `known-benign.md`, `decisions.jsonl` |
| never — it's how you want work done | global memory / a rule | `prefer-subtraction` |

*(Canonical form of this table: `~/.claude/memory/knowledge-routing.md`.)*

**Memory is the last resort, not the default.** It is the default only because it's the destination
the harness names, which is exactly why it silently becomes a catch-all.

## The probe test decides it mechanically

A memory describing a system must carry a `check:` — a cheap, read-only command that would prove it
wrong. **If you can't write one, it isn't a memory**: it's a genuine preference, or (far more often)
a fact that belongs with its subject, where the subject's own repo makes it checkable.

This converts "where does this go?" from a judgment call you can skip into a question you must
answer before the file can exist.

## Why each mechanism, with the evidence

**Colocation buys opportunity, not correctness.** Code comments are maximally colocated and still
rot; mined across ~1,500 systems, inconsistent comment changes are ~1.5× more likely to be
bug-introducing. Proximity means a diff *can* catch drift, not that it will. It's still worth it —
a doc that moves with `git mv` cannot name the wrong directory — but don't expect it to be
sufficient. Measured across two repos: a comment 11 lines from the code it described
stayed true, while a doc one directory away in `docs/` went false and sat unnoticed, because no diff
touching that code ever showed the file. A separate decision log fared worst — five independent
drift cases, and its own index listed an ADR as `Proposed` six weeks after the ADR itself said
`Accepted (live)`, so the artifact a reader consults *first* was the stale one. A memory in a
separate tree is further still: one such memory named the wrong cluster because the app moved a day
after it was written.

**"Keep this updated" doesn't work**, for two structural reasons: it's read when you open the doc,
but needed when you're editing the code; and it emits no signal when ignored. Replace every such
instruction with a check that reports drift.

**Don't expect the model to notice staleness.** On the STALE benchmark the best model scores ~55%,
and the dominant failure is *implicit conflict* — later evidence invalidating a claim without
explicitly contradicting it. Invalidation must be structural: probes, caps, scheduled checks.

**Deletion is the primary maintenance action, not updating.** A stale doc a human skims and ignores
is one an agent reads as ground truth and propagates into code. Bounded memory also measurably
outperforms unbounded (39% vs 13% in one published domain, 51% vs 32% in another). Prefer `git rm`
over "update later."

**Imports do not defer cost.** `@path` imports in `CLAUDE.md` expand inline at session start and
count in full — they are organizational only. The mechanisms that genuinely defer cost are
`.claude/rules/*.md` with `paths:` frontmatter (loads only when a matching file is touched),
subdirectory `CLAUDE.md` (loads on demand), and skills. Put always-relevant rules in imports and
everything conditional in path-scoped rules.

**`MEMORY.md` is hard-capped at 200 lines or 25KB.** Content past either cap is **not loaded**, and the
file shows no sign of it — Claude Code reminds Claude to shorten the index when its own write lands near
a limit and errors when it lands past one, but an index already over the cap reads as normal. Keep the
index a router — one short hook plus a link — never content. Growth is the
signal to move entries out, not to compact hooks (which, on a synced fleet, makes each host rewrite
them differently into a whole-file divergence).

**Skip the memory-product category.** Letta's own benchmark had a filesystem-and-grep agent beat
mem0's graph variant, and plain full context beat mem0 on the standard benchmark. Those tools
extract facts from conversation transcripts; the failure here is hand-authored knowledge going
stale because the world changed. Different problem.

**ADRs: append-only, or don't bother.** The supersede convention degrades because people update one
side and forget the other. If a fact will be *revised* rather than *replaced*, it wants an editable
doc beside its subject, not a numbered immutable record.

**Positional citations dangle without leaving a diff, and the scale is larger than it looks.**
Converting one repo's ADR register turned up **55 numbered citations across 19 files**, and removing
those exposed **11 more** citing positions in a *queue* — a document whose whole purpose is that
items get done and deleted. Every one was dangling, pointing at a build plan two rewrites gone.

They were found by breaking one: adding a queue item renumbered the sections and silently changed
what `item 2` in a docstring meant, during the session spent removing exactly that indirection. So
the shape is easy to miss when the target does not look like a register. Gate the fix with one test
that every cited path resolves and one that the retired scheme has not crept back — and exempt
**applied migrations**, whose comments are immutable because the file's hash is checked at deploy
time, so editing a stale comment there blocks the rollout. Record where those old keys pointed
instead.

**Updating a capability without updating what routes to it ships nothing, and it arrives in
costumes.** Three cases in one day: a merged branch with an unmoved deployment pin, a corrected
alert annotation beside prose still describing the old threshold, and a skill whose method grew two
new catches while its `description` still listed only the original defects — so anyone whose problem
was one of the new ones would never have matched the skill, and the additions were unreachable by
exactly the person who needed them. In all three the pointer and the content live apart and only one
gets updated.

## Writing the "why" without writing something that rots

A directive with a reason attached gets followed; a bare directive gets skipped under pressure. So
rules should carry the failure that motivated them. But that's the same instinct that fills a doc
with `(validated 2026-07-17)` and item counts, which is precisely what goes stale.

The line is not "narratives rot." It's:

- **A past event used as evidence is durable.** "A per-item `ssh` loop tripped `MaxStartups` and the
  timeouts read as the host being down" happened; it will always have happened, and it justifies
  batching. Keep it.
- **A measurement of current state decays on contact.** "the index is at 85% of the cap",
  "~2,000 items", "currently 9 whitelist entries" describe a moving world and are wrong shortly
  after writing.

**The test: does this detail change what the reader does?** The `MaxStartups` mechanism does — it
tells you to batch. The 85%-of-cap figure doesn't — the rule is "keep the index a router" no matter where
it sits today.

So: **keep the mechanism of a failure, drop the measurements of the moment.** In practice that means
naming what broke and why, without the date it broke, the count involved, or the current value of
anything. If a number is genuinely load-bearing (a threshold, a hard cap, a protocol constant), it
belongs — those don't drift with the world, they *are* the world.

## Reorganizing a setup that has already drifted

The ordered procedure is `first-run.md`.
