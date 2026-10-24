---
name: always-on-prune
description: "Decide which loading tier each piece of instruction text belongs in — CLAUDE.md imports, skill descriptions, memory indexes, path rules, skill bodies, references — and move it to the cheapest tier that still delivers it. Use to reduce always-on load, prune resident memory or CLAUDE.md, when skill descriptions are dropped from the listing, a hygiene check reports growth, or context feels heavy. Also to split a skill into method plus references, move instance data out, or dedupe a rule across skills."
---

# Pruning the always-on tier

**BLUF: the goal is loading things that matter, when they matter — not making things smaller.**
Deletion is the last resort and usually the wrong move. Almost every win here is *relocation*: taking
content that is paid for on every request and moving it down a rung, so it is paid for only when the
situation it addresses actually arises. A rule that survives the move costs nothing when idle and is
still there when needed. A rule you deleted is just gone.

So the question for every passage is **not "is this worth keeping?"** — it is **"what is the cheapest
rung that still delivers this at the moment it is needed?"**

**A preference and a skill are the same substance** — markdown text carrying rules; what differs is
*when it loads*. The pattern has a name already, so use it rather than a coinage of your own:
**progressive disclosure** (Anthropic's term, vendor doc — name+description always in context, body on
activation, bundled files on demand). Content is **always-loaded** or **on-demand**, and the moment an
on-demand piece is fetched is **activation**, i.e. *just-in-time context retrieval*.

**Three orthogonal axes, not one ladder** — conflating them is how a routing decision goes wrong:

- **trigger** — when it loads. That is the table below.
- **scope** — where it applies: user / project / path. A project-scoped file and a user-scoped file
  load at the *same* moment; they differ in applicability, not timing. So moving something into a
  project memory index is a scope change, not a demotion — it buys nothing except in the projects
  that never open it.
- **control locus** — who decides it loads: the **application**, the **user**, or the **model**
  (terms from the MCP spec, vendor doc). "Loads when the model decides" and "loads when the harness
  matches a glob" have identical timing and completely different reliability; only this axis
  separates them.

| rung | control | loads when, and what belongs there |
|---|---|---|
| always-loaded prefs (`CLAUDE.md` `@import`s) | application | every request — triggers, and rules that must fire when nothing else is loaded |
| skill roster (name + description) | application | every request — just enough trigger vocabulary for the skill to fire |
| path-scoped rules (a `paths:` glob) | application | the harness sees a matching file — rules about editing one class of file |
| user-invoked (`@file`, slash command, "read X") | **user** | a human asks for it by name |
| skill body / memory recall | model | the model judges it relevant — the method, per-project facts |
| `references/` beside a skill | model | the model opens that reference — catalogs, tables, evidence |
| **not context at all**: a hook, a linter, a settings policy | the harness *executes* it | — |

The two rungs people leave out are the two best ones. **User-invoked** is cheaper than a
model-triggered load *and* more reliable, because a human named it — so anything a person predictably
asks for by name goes there rather than hoping a description fires. And the **bottom rung is not
context at all**: zero tokens, adherence effectively total, because the harness runs it instead of the
model choosing to comply. Two vendors route content out of instructions for exactly this reason —
*use a linter instead of pasting a style guide*, *if it must run at a fixed point write a hook*
(vendor docs). **Try it first for any rule a machine can check.**

Most bloat is content sitting one or two rungs above where it belongs. The always-on tier is invisible,
it compounds across subagents, and nothing in the normal workflow pushes back on its growth. But
**know each rung's failure mode before moving something into it** — "cheaper" is not the only property
that changed.

- **The compaction trap — check this before demoting anything that must survive a long session.**
  After a context compaction the project-root instruction file is re-read and re-injected, but
  **nested instruction files and path-scoped rules are not** (vendor doc); they return only on the
  next match. Demoting a rule one rung can make it vanish exactly when a long session most needs it.
- A path-scoped rule fires when a matching file is *read*, and on at least one implementation **not
  when a new matching file is created** — so a rule about writing a class of file is absent at exactly
  the moment the first one is written.
- **Splitting a resident file into `@import`s does not reduce context** (vendor doc) — imports load at
  launch too. Anyone attacking resident bloat by splitting files has done nothing.

None of these is a reason to avoid a rung; each is a reason to leave a resident trigger behind when the
rule must hold on the run where its rung never fires.

**The case for cutting rests on four things, strongest first** — and the one everybody reaches for is
the weakest of them:

1. **The number of competing directives, not the byte count.** A measured study (IFScale, arXiv
   2507.11538, 20 models) varies the *count* of distinct instructions and finds frontier models at only
   ~68% adherence at 500 of them, biased toward the earlier ones. Read alongside the size-null in step
   4: **directives compete; bytes do not.** So when auditing, **count directives, not just bytes** — a
   long file stating one rule with the incident behind it is cheaper on this axis than a short one
   stating fifteen.
2. **Reviewability.** A tier nobody can read in one sitting is a tier nobody audits, and it grows.
3. **Scope-correctness.** A rule that does not apply here is a distractor competing with the ones that
   do — the scope axis again, and the reason *where* beats *how much*.
4. **Money, which is weaker than it sounds — say so rather than overselling it.** A resident prefix
   bills at **~0.1x on cache reads** (vendor pricing; less on some models, see CR_MULT), so residency is cheap per request. Measured here,
   relocation still saves 95–100% of the resident cost, because the destinations in this pass load in
   under 6% of sessions; it becomes a *loss* only when the destination loads in nearly every session
   and loads early — which is the definition of something that should have stayed resident, so the
   lookup-moment test already selects against it. `relocation-economics.py` computes it per
   destination; step 2 runs it.

**And a one-off pass does not hold.** A real cut with nothing watching afterwards has left the tier
**larger than its pre-trim baseline six days later**. If you finish without installing a
ratchet you have bought a few weeks; step 6 is not optional garnish.

**Which reference to load:**

| situation | file |
|---|---|
| starting a pass: attribution, the measurer scripts, the roster and its listing budget (steps 1–2) | `references/measure.md` |
| appending to `prune-log.jsonl`, re-recording the floor, or asking "deleted or relocated?" | `references/prune-log.md` |
| splitting a skill into method + per-kind references, or deduplicating a rule across skills | `references/skill-restructure.md` |
| this machine's baselines, measured costs, f per destination, local mechanisms | your own `~/.claude/local/always-on-prune/instance.md` (record it as you measure) |

## Scope, and what to hand off

**The split is by question, not by file type** — "skills over here, memories over there" is the wrong
division, since the two are the same substance and every question below applies to both:

| the question | tool | what settles it |
|---|---|---|
| **Should this rule exist at all?** Does it change behaviour, or is it describing the default? | **`skill-golf`** | running the thing and falsifying the rule — a real before/after test |
| **Which rung should it live on, and what does that rung cost?** | **this skill** | measured per-request cost, plus the lookup-moment test |
| **Will the skill fire when it should?** | **`skill-creator`** | a description is a trigger, not prose; measured by whether it fires |

**`skill-golf`'s method applies to a resident preference just as well as to a skill rule** — nothing
in it assumes a `SKILL.md`, and "rule present but ignored" and "rule followed, outcome identical" are
both cuts wherever the rule lives. Run them together, in that order. They stay separate because the
methods do not overlap: this one measures cost and moves content between rungs, that one runs the
thing and tries to break the rule.

**Before either question, ask the cheap one: is it simply on the wrong rung?** Moving a skill's bulk
into `references/`, or a catalog out of a resident preference, is not a cut at all — nothing is lost,
nothing needs testing, and the artifact gets cheaper every time it loads. Tables, catalogs, worked
examples, evidence appendices and per-variant detail almost always belong a rung down, with a line
above saying when to go read them. Do this first. It often concludes "move the catalog into skill X",
which makes X longer; that is correct, and the follow-up is to push X's own bulk into `references/`.
Splitting a skill into method plus per-kind references, or deduplicating a rule across skills, is
`references/skill-restructure.md` — the target shape, the loss check, and owner-plus-pointer.

## 0. Say what you are going to do, then do it

Before measuring, tell the user: *"I'll audit and measure first, then apply the whole batch and
report — I won't check back per file."* Then don't.

This one sentence is worth more than it looks: in the previous pass the largest cluster of avoidable
user interjections was re-granting permission already given, caused by an agent repeatedly
announcing "I'll apply this once I have measurements" — which reads as *blocked, awaiting approval*.
Batch the decisions into one table at the end. Per-file approval turns a two-hour job into an
afternoon and produces no better decisions. What genuinely needs the human is in step 7, and it is
not "is this cut OK".

## 1. Attribute first — this may not be your problem at all

**Before measuring the resident tier, find out whether it is where your consumption actually goes:**
run `usage-attribution.py` and `where-the-bar-goes.py` (beside this file). If residency is a small share
and subagent model choice or long sessions dominate, **stop and go fix those instead** — unless the
workload is subagent-heavy, where the resident prefix is a much larger fraction of each fresh agent's
context. Two commands; skipping them is how a pass optimises a rounding error. Detail and what the
answer looked like here: `references/measure.md`.

## 2. Then measure the tier itself

Run all four measurers — `measure-resident-cost.py`, `overlap.py`, `lookup-moment.py`,
`relocation-economics.py` — plus the skill-roster count; they take seconds and routinely overturn the
plan. Three findings to carry into every pass (commands, docstring traps and the roster snippet are in
`references/measure.md`):

- **Measure bodies, not files** — frontmatter is stripped at load, so a checker counting file bytes
  overstates.
- **The skill roster is the other half of the always-on tier** and usually nobody counts it. Its length
  is functional: cut only padding, and measure triggering before cutting deeper.
- **A roster over the harness's listing budget is a triggering outage, not a cost problem** — rarely-used
  skills silently go name-only. Names without descriptions in a live listing mean trim; then re-check
  firing with `trigger-test.sh`.

**Do not write another measurer** — ctxlint, AgentLinter and `/doctor` already count tokens (listed in
`references/measure.md`). What is unclaimed is the **decision** — which rung a passage belongs in, and why.
That is what this skill is.

## 3. The governing test: is there a lookup moment?

For each preference, ask: **will the reader ever realise they need this and go fetch it?** The lookup
moment is **activation** seen from the other side — content that never gets activated was not
relocated, it was shelved.

- **Yes** — they will hit the situation, know a skill covers it, and load it. The content belongs in
  the skill. Nothing needs to stay resident.
- **No** — the failure mode is *not knowing to look*. Then a **trigger** stays resident and the
  **catalog** moves. The resident half is a few sentences: this situation exists, here is the shape
  of the trap, load skill X. Everything else is lookup-able once you are looking.

Almost every file resolves to that second case, which is why the output of a good pass is a tier of
short triggers rather than a shorter list of long files.

This is testable, not a matter of taste. `lookup-moment.py` counts how often the situation arose with
none of the covering skills loaded. Measured here, one preference's situation arose an order of
magnitude more often than the skill covering it was ever loaded — so the trigger stays. Expect that
shape: skills are loaded far less often than the situations they cover arise, and that gap is
precisely what the resident tier is for.

**Its sample hits are verbatim commands out of your transcript store** — which is what makes them
worth reading (they are how you tell a working regex from one measuring itself) and also why they stay
on the machine. Quote the counts, not the samples, in anything you hand on.

Two ways to get a confident wrong answer out of this, both hit while building the script:

- **Never test for a skill by searching for its name in the transcript.** A resident preference that
  mentions the skill is injected into every session, so the flag is true from line one and the probe
  can never return non-zero. Count real loads only.
- **Read the sample hits before believing the count.** A loose situation regex will match the briefs
  of agents you spawned to investigate this very question — the investigation counting itself.

## 4. What is *not* the reason to cut

Each of these is a plausible instinct that wastes the pass or does damage.

**"It's too long, adherence will suffer."** The best available evidence says no: a measured factorial
study of instruction-file variables (arXiv 2605.10039) finds file size and internal contradictions to
be *affirmative nulls* for adherence (BF10 0.05–0.10) — a bigger file is not followed less well. What
does degrade is compliance over a long session, which trimming does not fix. The adherence cost that
*is* measured attaches to the **number of directives**, not the size of the file carrying them, so
count those instead (see the four motivations above).

**"There's bound to be duplication."** Measure it; there is usually far less than expected. Measured
here the largest overlap between any two preferences was a rounding error and most files shared no
8-gram with anything at all, so if dedup is your plan `overlap.py` will tell you in seconds whether
the lever exists. A low score does not prove the *idea* isn't repeated, only the text — use it to find
candidates, not to clear files.

**"The checker says we're over, so get under."** A size threshold is a growth tripwire, not a target,
and it is usually measuring the wrong bytes (see the frontmatter point in `references/measure.md`). The honest deliverable is
"here is the floor I can defend, and here is what going below it would cost" — not a number hit by
cutting something load-bearing.

**"This scored no-effect in a test, so it's redundant."** Only if the test had headroom. In the
previous pass three cells scored a perfect 1.00 *in the control* — the task could not get worse, so
the preference could not show an effect. Calling those redundant would have licensed deleting rules
the experiment never tested. A null licenses a cut only when the probe could have shown a difference.

## 5. Deciding and applying

Work file by file into one table: **keep / trim-to-trigger / move / cut**, with body bytes before and
after and a one-line reason. Then apply the batch.

Rules that make the difference between a good pass and a damaging one:

- **Never delete a behavioural rule — relocate it.** Every sentence removed must either already exist
  at the destination (verify by reading it, do not assume) or be written there in the same edit. In
  the previous pass this check fired twice on content that had *no* home in the target skill and
  would simply have been lost.
- **Then check the trigger you left behind actually names the destination.** Relocation preserves a
  rule only if something reliably says *load skill X*. On this pass one destination measured **zero**
  loads across the whole window — the resident trigger is doing all the
  work and the relocated catalog is write-only until it fires. The trigger's wording matters more than
  the move; `relocation-economics.py` will show you an f of zero, which is a warning, not a saving.
- **Keep the why.** These files persuade because they carry the incident that produced the rule. Trim
  ceremony, restated conclusions, cross-reference chains and process residue. Trading measured
  behaviour for a few hundred tokens is a bad trade — when you find yourself about to strip the
  evidence that makes a rule convincing, stop; you have reached the floor.
- **Carry measurements verbatim or drop them.** Never round, paraphrase, or refresh a number you did
  not re-measure.
- **Retire, don't delete.** Copy each file aside before rewriting. Cuts get reversed, and the reversal
  is where you learn the criteria were wrong. For a resident preference, the cheapest relocation that
  loses nothing is an **evidence copy**: the full original in a non-imported directory beside the
  store, with the resident file distilled to rules plus a one-line incident each and a pointer to it.
  Then hand old-vs-new to a cold agent to list rules lost or weakened — on the pass that introduced
  this it found seven, all of which a self-review had passed.
- **Run every test suite after moving text out of a `SKILL.md`.** A test that asserts on the skill's
  content (every gated rule is documented, a heading exists) reads `SKILL.md` by path, and the move
  breaks it silently until someone runs it. Here that was the footgun gate's doc-sync check.
- **An empty mechanism is a cut, not a fixture.** A section that was added to accumulate entries and
  has accumulated none is paying rent for an intention.
- **Log every relocation to `prune-log.jsonl`, in the same edit that moves the text** — one line per
  moved chunk, with a `phrase` greppable at the destination. A prune is otherwise indistinguishable from
  content being lost, and a sync tool has already tried to restore one. If the floor lives in a separate
  file, a prune is two appends and the second gets forgotten. **Re-record the floor only after a real
  prune review, never to silence the ratchet.** Schema, header rule and the floor: `references/prune-log.md`.
- **Instance data does not belong in a resident file.** A hostname, a device name, a node name, a
  dated line, an item count: that belongs beside its subject. This is also what makes the tier
  shareable — see below.

## 6. Install the ratchet, or this all comes back

Nothing was wrong with the last pass's decisions; there was simply nothing watching afterwards, and
every individual addition since was locally justified — which is how the tier ended up above its
pre-trim size inside a week. So finish by making growth visible. This skill
owns the **policy**; the mechanism is whatever periodic checker the setup runs (here, `config-hygiene`'s
`hygiene.py memory`, wiring recorded in your own `~/.claude/local/always-on-prune/instance.md`).

1. **Record a baseline** — today's body-byte total, written to `~/.claude/local/always-on-prune/baseline.txt` (the
   checker reads it from there), never into prose that will drift. Take it from
   `measure-resident-cost.py`'s printed total, not a second counter that can disagree.
2. **The checker must count the real number** — bodies not files, the skill roster as well as the
   preference tier, and any per-project memory index (it loads in full in its project and is usually
   counted by nothing). Keep a newly-added term OUT of the total the delta compares, or the ratchet fires
   on your own definition change. A checker that overstates gets discounted; one that misses a third of
   the budget is worse. Every setup names its checker differently; if nothing audits the store yet — grep hooks and scheduled jobs for its
   path — that is the finding: write one.
3. **Report growth against the baseline, not an absolute threshold** — a delta fires when someone can
   still remember why; a threshold becomes wallpaper. Current → silent; grown → name both numbers;
   **baseline missing or unreadable → INERT, never silence**.

A pass that ends without this is a pass you will run again.

## 7. What to escalate

Decide everything else yourself. Bring these to the user:

- **Anything encoding how *they* work** — how they read a message, what they know and don't, their
  stance on a repo. You cannot test these and getting one wrong degrades every future session
  invisibly. Ask; do not infer from the file.
- **Anything where they know how the system is actually used** and you are guessing. In the previous
  pass the two highest-value interjections were both this, and neither was derivable from the data.
- **A cut you would make that contradicts a recorded earlier verdict.** Recorded no-op and reversal
  decisions exist precisely so they are not re-derived; if you are about to overturn one, say so and
  give the new evidence.

## Keeping this shareable

This skill is meant to work for someone who has none of the preferences, hooks or skills referenced
above. Two consequences worth honouring when you edit it:

- **Keep machine-specific facts in an `instance.md` you write in `~/.claude/local/always-on-prune/`**, never in `SKILL.md`
  (files beside a plugin-installed skill are wiped by `/plugin update`). Baselines,
  thresholds, per-file verdicts, model prices and host names are all instance data; every number
  quoted here is either cited to a public source or belongs in that file. If `instance.md` is absent
  the method still runs — you just measure your own baseline instead of reading one.
- **Name mechanisms generically.** "The periodic checker", "the Stop hook", "the preference store" —
  someone else's will have different names, and a rule keyed to a filename they don't have reads as
  broken rather than as inapplicable. Where a concrete example helps, mark it as an example.

The scripts hold to the same rule — standard locations, specifics as arguments. The one exception is
`measure-resident-cost.py`'s model price table, guaranteed to go stale; check it, and the per-model
cache-read multipliers in `CR_MULT`, before quoting a dollar figure.
