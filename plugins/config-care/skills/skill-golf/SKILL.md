---
name: skill-golf
description: "Audit a skill or memory file you own — which rules change behaviour, which are ignored or too vague, what can be cut. Use when a skill or memory has grown long, agents load it and still do what it forbids, deciding whether a new lesson belongs in it, or for a periodic \"is this earning its length\" pass. NOT creating or trigger-testing skills (skill-creator) or choosing models (model-golf)."
---

# Golf a skill

A skill is a document that claims to change behaviour. This is how you find out whether it does,
rule by rule, and delete the parts that don't.

The failure this exists for is specific and invisible from inside: **an agent loads the skill and
then violates it immediately.** Measured instance — an agent called `Skill(search-craft)`, read the
companion `instance.md` five seconds later, and eight seconds after that issued a query violating
the rule sitting under a ⚠ in section 1. The skill was not missing the rule. It was not stale. It
was read, and it did not fire.

So the question is never "should this skill say X". It is **"does saying X change anything, and what
is the rest of the length costing the rules that do?"**

## Grep before you write anything down

**The single highest-value step, and the cheapest.** Before adding a lesson to a skill, search the
skill for it.

On the audit this came from, six lessons were extracted from a real session. **Four were already in
the skill, verbatim, under their own headings** — including two under warning markers. The only
honest conclusion available at that point was that the content was fine and the compliance was not,
which is the opposite of the "add a section" reflex that produced the length in the first place.

Had that grep not run, the audit would have shipped a longer document that restated its own ignored
rules — making the real defect worse while feeling like progress.

Run it as a real search, not a skim: the lesson will be phrased differently than you would phrase
it. Grep the *concept words*, then read around every hit.

**Prose is not a fix for a trap that prose already failed to prevent.** If the rule is present and
was violated anyway, the candidate fixes are: cut something else so it is findable, move it to where
it fires, make it one checkable question instead of a category distinction — or escalate it out of
prose entirely. Writing it again, more emphatically, is the one move known not to work.

## Check the founding failure for recurrence — do this before anything expensive

**Every rule in a skill was written because something went wrong once. Find that incident, then
measure whether its signature still appears.** This is the cheapest evaluation available and in the
source audit it was the *only* one that produced positive evidence — after four experimental
conditions, 123 headless cells, two judge panels and a human baseline had all returned nulls.

It works because the founding incident gives you three things a designed experiment cannot: a
failure you know is real, a pre-registration written before any of this was contested, and a
**measurable signature**. In that case the incident was eleven consecutive synonym-permutations of
one query; the signature is "longest run of near-identical consecutive queries per session", and it
took one pass over transcripts already on disk.

Two things to get right:

- **Distinguish the pathology from things that merely resemble it.** The longest post-skill run
  looked bad at 6 until it was read: it swept one entity across six retailer sites. Varying the
  *entity* while holding the frame is enumeration; holding the *target* while permuting synonyms is
  thrashing. A similarity metric cannot tell those apart — you have to look.
- **Say plainly that it is correlational.** One pre-skill incident is not a baseline. Absence of a
  recurrence is genuine evidence and it is not a controlled comparison; report it as the former.

If the founding incident is not written down anywhere, that is itself the finding: nobody can say
what the rule is for, and it cannot be evaluated at all.

## Mine real usage; do not invent test cases

Anything you author yourself encodes your assumptions, so testing against it confirms them. A skill's
own eval prompts are written by whoever wrote the skill, in the vocabulary of the skill.

Pull what the skill was actually used *for* out of the transcripts — the real queries, the real
briefs, the real outputs — and audit those. The extraction is a one-off script per skill; the shape
that worked: walk `~/.claude/projects/**/*.jsonl`, pull every `tool_use` of the relevant tool with
its surrounding brief and its tool_result, and stratify the sample across outcomes so the review
is not just a parade of failures.

**Stratify, or the lesson set skews.** Sampling only the bad cases teaches rules that fire on
disasters and say nothing about the ordinary path. Take weak and strong outcomes in a known ratio
and shuffle before reviewing.

**Scope to since the skill existed.** Usage before the skill shipped measures the baseline, which is
useful — but not if it is silently mixed into the treatment.

## Judge head-to-head against a human, blind

The strongest signal available without ground truth is a skilled human doing the same task. It costs
their time and nothing else, and it finds things no metric was designed to catch.

**Run it blind and in this order**: show the human the *information need* and the agent's artifact,
never the outcome. Get their version. *Then* run both, same day, same index, and reveal. Showing the
outcome first anchors both of you, and the exercise then measures agreement rather than quality.

**Re-run the original too.** Comparing the human's fresh attempt against an artifact captured weeks
ago measures index drift, not judgement.

**Expect the human to lose some, and treat those as the valuable ones.** In the source audit the
human won 4, the agent won 2, two tied — and the two agent wins produced the sharpest rules, because
they marked the boundary of an over-general lesson. A rule extracted only from wins is a rule with
no known limits.

**Compress the task statement at your peril.** Two results in the source audit were inverted by the
one-line summary of the need: one bundled two questions with an "and", another was ambiguous between
three readings. The human optimised for the summary and lost to the agent, who had the full brief.
If you must compress, tag the *answer type* (single fact / inventory / artifact / methodology) —
that carries the shape without leaking the answer.

## Falsify the rule; do not confirm it

A rule that only ever gets confirmed has not been tested. **Construct the case where it should fail
and run it.**

Worked example: a skill said *never put the answer you expect into the query*. A real agent violated
it and got the right answer anyway. Rather than record a win for the agent, the audit ran the premise
**backwards** — asserting the opposite relationship — to see whether the result set would correct it.
It did.

That single reversed run converted an absolute rule into a conditional one with a stated mechanism:
the presupposition is dangerous in proportion to how *weak* the retrievable corpus is; against strong
first-party documentation the corpus overrules the premise. Neither the original violation nor its
successful outcome could have shown that. Only the falsification did.

**Ask of every rule you are about to keep: what would the world look like if this were wrong, and
can I cheaply produce that world?**

## Compliance metrics are falsely clean

You will be tempted to score adherence mechanically — a script over the artifacts, a violation rate
per rule, a nice table. **Build it, then immediately push your known-bad case through it.**

In the source audit the detector was good work: seven rules, thirty-seven passing tests, each rule
with a must-flag and a must-not-flag case, and its author sabotaged a rule to prove the suite could
fail. It scored the corpus **89% clean**.

It also scored **CLEAN** the single query known to have produced a confidently wrong answer, and
CLEAN the query with a false premise baked into it. The one rule that fired on a known-bad case was
the rule its own author recommended discarding (52 hits, ~0 real).

The reason generalises: **the violations that cost you answers are semantic, and a string matcher
sees syntax.** "Contains a claimed relationship" and "is secretly two questions" are not provable
from the artifact's text without false positives — and a checker with false positives gets switched
off, which is strictly worse than the prose it replaced.

So: mechanical rules are a **sanity signal**, never the primary metric. Keep only the rules that
survive a known-bad probe, and say plainly in the output which rules were dropped and why. A
compliance score that cannot fail on your worst case is measuring itself.

For the primary metric, use an LLM judge on a single checkable question, blinded to arm, scored in
both orders, keeping only order-agreement — and a judge that is not competing in the comparison.

## Prefer one checkable question to a correct taxonomy

The rules that survived the source audit were not the most accurate ones. They were the ones that
could be applied in the seconds before acting.

A rule phrased as a distinction — *hypothesis words versus topic words* — is correct and requires the
reader to classify their own tokens, at exactly the moment they are least able to. The same content
phrased as a question — ***would a page plausibly be TITLED with these words?*** — subsumed three
separate sections of the original skill and needs no classification at all.

When auditing, for each rule ask: **can this be applied without first understanding it?** If not,
try to collapse it into a question. A rule that requires correct classification to apply will be
applied incorrectly, and its failures will look like the rule not existing.

## The verdict is cut / rewrite / promote

Bias hard toward cutting. A rule that demonstrably changes nothing is not neutral — it is spending
the reader's attention, and attention is the scarce resource that made the followed rules unfollowed.

| finding | verdict |
|---|---|
| rule present, followed, changes outcomes | **keep** |
| rule present, ignored, and re-statable as one checkable question | **rewrite** — collapse and move to the front |
| rule present, ignored, cannot be made checkable | **cut**, or escalate out of prose to something the harness executes |
| rule present, followed, but the outcome is the same either way | **cut** — it is describing the default |
| genuinely new lesson, survived falsification | **promote** — and only then |

**Front-load what fires at action time; demote the rest to reference.** The rules that must fire
when the artifact is being written belong in a short card at the top. Everything explanatory is
reference material that a reader consults, not instructions that fire — and mixing them is what
buries the ones that matter.

## Measured redundancy is not a licence to cut — check portability first

**A skill is a shareable artifact; the environment it was measured in is not.** If an ablation shows
a rule changes nothing, ask *why* before deleting it. "Redundant because a local memory, a
CLAUDE.md, or a house convention already covers it" is a fact about **this machine**, and the person
you hand the skill to has none of those. Cutting on that measurement silently makes the skill
non-portable, and it fails for the recipient in exactly the place you can no longer observe.

So separate the verdicts:

| the rule is… | do |
|---|---|
| redundant with something **inside the same skill** | cut it — genuine duplication |
| redundant with an **always-resident memory / CLAUDE.md** | **keep both** — see the asymmetry below |
| redundant with a **team convention the recipient won't have** | keep it in the skill |
| changing nothing anywhere, including for a naive recipient | cut it |

**Skills load on demand; memories are always resident. That asymmetry makes the overlap deliberate,
not wasteful.** A skill's rule protects only the runs where something actually loaded the skill —
and agents routinely do not, even with it listed in front of them. A memory's copy is the only thing
covering those runs. Delete it and you remove coverage precisely where the skill already failed.

Size the overlap to the miss rate: the more often the skill goes unloaded, the more the memory needs
to carry on its own. The stable split is **memory = the trigger plus the few rules that must fire
when the skill is NOT loaded; skill = the full method.** That keeps one authoritative copy of the
method while still covering the unloaded case, and it is what stops two statements of one rule from
drifting apart.

This is the one place where the measurement actively misleads, in both directions: an ablation run
in a rich environment under-values every rule that environment already supplies (bad for the
recipient who lacks it), while an ablation that strips the environment over-values rules the local
memories would have covered anyway. Neither number alone tells you what to cut.

**Instance data does not belong in the skill.** Measured rates, dated validations, machine-specific
routing — those go in a companion file in `~/.claude/local/<skill>/`, so the method can be handed to someone else
without editing. If the audit produced numbers about *your* skill, they belong in the audit output
or a companion, not in the skill being audited.

## Companion files

Working harness from the audit this skill came from, in `example-harness/` — a starting shape to
edit, not a library to call, and `build_v2.py` hardcodes the originating machine's path. What each
file does: `references/measuring-a-skill.md`. Nothing there is needed to apply the method.

## What this does not cover

| you want | use |
|---|---|
| create a skill, or test that it TRIGGERS on the right prompts | `skill-creator` |
| compare models, effort levels, or run any A/B matrix | `model-golf` — pre-registration, arm design, knob verification, grading traps, null/oracle baselines |
| spot stale or misplaced content by inspection, no runs | `config-hygiene` |
| cut what is paid for on EVERY request — resident prefs, the skill roster's weight | `always-on-prune` |
| decide where a newly-learned fact should live at all | the `knowledge-routing` memory |

**This method is not limited to skills — run it on a memory too.** A memory and a skill are the same
substance, markdown carrying rules; what differs is only *when* the text loads. Nothing in the verdict
table above depends on a `SKILL.md`: "present but ignored" and "followed, but the outcome is the same
either way" are cuts wherever the rule lives, and a resident memory is the case where a rule that
changes nothing is most expensive, because it is paid on every request rather than on every load.
The one thing that does change is the counterfactual — for a memory the comparison arm is a run with
that pref absent, and it is always in context, so you cannot get an honest baseline by simply not
loading it.

**`always-on-prune` is the natural companion and they are usually run together, in that order** — it
decides which tier a piece of content belongs in and pushes catalogs down a rung, which makes some
skill longer, which is this skill's cue. They stay separate because the methods do not overlap: that
one measures per-request cost and routes content between tiers, this one runs the thing and tries to
break the rule. Merging them would load both methods every time you needed either, which is the exact
failure they both exist to prevent.

`model-golf` owns the harness. Do not restate its method here — when this skill needs an A/B (skill
vs rewritten vs none), that is a model-golf matrix with the skill as the variable, and every one of
its scars applies: byte-identical prompts, verify the knob was actually applied, a control that
fails at least one task, null and oracle runs to test the grader in both directions.

## Choosing a metric that can actually move

Measured on a pilot, not reasoned — **read `references/measuring-a-skill.md` before designing any A/B
over a skill or memory**; each rule below has its incident there.

- **Correctness saturates, because agents recover** (21/21 on every arm, including no-skill). Measure
  the artifact the skill governs directly, not the downstream outcome.
- **Some tasks cannot discriminate, by their shape** — drop tasks where the defect cannot occur.
- **Pick tasks the model cannot already do from memory**, or the null is guaranteed. Cheap probe: run
  the task with no tools and no skill; that is the floor.
- **Reproduce the CONDITION, not just the task** — real fan-out briefs, not one clean question.
- **At a low base rate, report raw agreement AND κ, and compute the ordering under at least two
  aggregation rules.** One judge scored twice is not two judges.
- **Your control arm inherits the environment** — have it report its own context back; enforce
  ablations at the tool layer (`--disallowedTools`), never by request; name the control for what it
  actually is.
- **Don't let the brief smuggle in the behaviour you are measuring.**
- **Measure the budget before rationing it.**
