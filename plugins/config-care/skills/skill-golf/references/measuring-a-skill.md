# Measuring a skill — metrics, confounds, and the example harness

Detail behind the "Choosing a metric that can actually move" section of `SKILL.md`. Open it before
designing any A/B over a skill or memory.

## Choosing a metric that can actually move

A pilot validated this section; the findings below are measured, not reasoned. A worked harness is
in `example-harness/` beside `SKILL.md` — collector, knob-verifier, grader with a both-directions
self-test, and a blind-judging prep step. Run-specific constants are at the top of each.

**Correctness saturates, because agents recover.** A 21-cell A/B over three arms — current skill,
rewritten skill, no skill — scored **21/21 correct on every arm**, including the arm with no skill
at all, and including a task chosen *because* a real agent had got it wrong. Agents that write a bad
query simply fetch their way out of it, so answer-correctness measures whether recovery happened,
and recovery nearly always happens.

**So measure the artifact, not the outcome.** The same runs scored on query quality gave a 21–36%
failure band — unsaturated, and directionally sensible. Whatever the skill governs *directly* is
what has headroom; the downstream result has been laundered by every recovery step in between.

**Some tasks cannot discriminate, by their shape.** In that pilot, needs dominated by proper nouns
and identifiers produced **0 violations across every arm** — there is no room for uncertainty
phrasing in a query made of identifiers. Only the "which / whether" shaped needs discriminated.
Sort candidate tasks by whether the defect you are hunting *can occur* in them, and drop the rest
or keep them explicitly as ties.

**Pick tasks the model cannot already do from memory — or the skill has nothing to contribute and
your null is guaranteed.** The sharpest confound found in the source audit, and it was invisible
until a human ran one of the tasks without prior knowledge.

`search-craft` is largely about what to do when you *don't* know a domain: orient, find the taxonomy,
harvest the vocabulary, work out who to believe. Every task in a 93-cell matrix sat comfortably
inside the model's priors — so every arm skipped the skill's advice entirely and went straight to a
source it could already name, and the no-skill arm matched the skill arm because **neither needed
it**. The measurement was real; it just measured a condition where the skill is inert.

The general form: **a skill that supplies knowledge or method the model already has will measure as
worthless on any task where it already has it.** Before trusting a null, ask what the model would do
with no skill at all — if the answer is "the same thing, from memory", the task cannot discriminate,
however hard it looks.

Cheap probe: have the model attempt the task with no tools and no skill. Whatever it produces from
memory is the floor your task must clear.

The worked example (a human-baseline comparison, not shipped — record your own): a skilled human and two
agents on the same unfamiliar-domain question, where the agents' entire advantage turned out to be
knowing the authority's name, not searching better.

**Reproduce the CONDITION, not just the task.** The violations that motivated that audit came
overwhelmingly from subagents inside large parallel fan-outs — long briefs, five competing
constraints, fifteen agents at once. The pilot ran one focused agent on one clean question and
could not reproduce a single violation. A skill that holds under a well-posed single question and
collapses under fan-out load is the normal case, and a harness that only tests the former will
report a null and license deleting a rule that was working.

Re-running the same arms against **real briefs lifted verbatim from the transcripts** — ~1,100
characters, competing constraints, a broad mission — immediately produced what the clean version
could not: **9% of cells never loaded the skill they were instructed to load, versus 0% of 48
clean-question cells**, and the first non-cost difference between arms (adherence to an explicit
budget stated in the brief). Nothing about the tasks' subject matter changed. Only the shape did.

**The instruction to load the skill is itself a rule that fails under load** — so the routing
consequence cannot live here, in a file that only exists once something loads it. It is stated
where it stays resident, in the `knowledge-routing` memory. What belongs *here* is the measurement
above and the harness that produced it.

**At a low base rate, compute BOTH aggregations — and if they disagree on the ordering, you have no
effect.** Two judges on 399 queries agreed 90% of the time, which sounds decisive and is not: at a
7–15% failure rate, chance agreement is already high, so **Cohen's κ was 0.51** and the judges
differed on roughly a third of the failures. Scoring "both judges say FAIL" ranked the arms
C-worst; scoring "either judge says FAIL" over the identical data ranked them **A-worst**. Same
runs, same judges, opposite conclusion — the ranking was a property of the aggregation choice.

Had only the consensus number been computed, it would have matched the ordering seen in every
earlier run and been written up as a replicated effect. **Always report raw agreement AND κ, and
always compute the ordering under at least two aggregation rules.** A rare-event metric needs far
more agreement than a balanced one to say anything.

**One judge scored twice is not two judges.** Ours reported perfect order-agreement and then
volunteered that its second pass applied a rule settled during the first rather than re-deriving
each call. That is honest and it is also not the measurement you wanted. Use two independent judges
where the verdict matters.

**Your control arm inherits the environment — check what is IN its context, not what it called.**
The sharpest error in the pilot, and it was caught by the human going "that doesn't add up", not by
any check in the harness. The "no skill" arm was verified only by confirming it never invoked the
Skill tool. It was still running with the user's full `CLAUDE.md`, which imports sixteen behavioural
memories — one of which *instructs loading the very skill under test*, and two more of which carry
overlapping epistemic discipline. The arm labelled "no guidance" had most of the guidance. Every
result from it was uninterpretable.

Before trusting an ablation, have the arm **report its own context back to you**: one throwaway run
asking "list the memory files loaded and quote any instruction about <the skill's subject>" settles
it in seconds. A knob check that only inspects tool calls verifies the *action* and misses the
*ambient* condition, which is where a skill's content most often already lives.

**Never let the brief instruct what the environment contradicts.** That same arm was *asked* not to
load a skill while its memory told it to load that skill. Nobody knows what an agent does with an
incoherent instruction, and you certainly cannot attribute the result to your variable. Enforce
ablations at the tool layer (`--disallowedTools`), never by request.

**And name the control for what it actually is.** Once the memories are acknowledged, "skill vs no
skill" was never available — the honest arms are *skill* / *rewritten skill* / *memories only*. That
is also the decision-relevant question, since in production the memories are always there. A control
you cannot build is a signal to restate the question, not to fudge the label.

**Don't let the brief smuggle in the behaviour you are measuring.** The pilot's output format
demanded `ANSWER / SOURCE / CONFIDENCE`. Requiring a source pushes every arm toward first-party
verification — which is a large part of what the skill teaches. The harness built the good behaviour
in, then measured that everyone had it. Strip any scaffolding from the brief that overlaps what the
skill is supposed to supply.

**Measure the budget before rationing it.** Fear of cost nearly cancelled that pilot; the whole
21-cell run turned out to be ~1% of a weekly limit. Take a usage reading before and after a small
batch, divide, and let the arithmetic decide the scale — a caution based on a guessed cost is
itself a cost. (Measure the conversion on your own account.)

## Companion files

Working harness from the audit this skill came from, in `example-harness/`. **They encode that run's
task set, and `build_v2.py` additionally hardcodes the originating machine's path** — the rest join
against a module-level base or take the path as an argument, so the "every file hardcodes it"
warning that used to sit here overstated the work by five files. They are a starting shape to edit,
not a library to call. Nothing here is needed to apply the method.

| file | does |
|---|---|
| `run_pilot.py` | Runs one cell per (task, arm, rep) as a headless `claude -p`; stamps arm + brief fingerprint *inside* each artifact; lockfile prevents overlapping runs |
| `extract_runs.py` | Parses the stream-json into queries/fetches/skills/answer, and does **knob verification** — marks any cell whose arm loaded the wrong thing as INVALID rather than grading it |
| `grade_pilot.py` | A `claude -p --json-schema` judge classifies each prose answer into `{"abstained", "claim": <per-task enum>}` (or an exact `value`), and the grade is a field comparison; an off-schema reply counts as unscored, apart from wrong and abstained. A self-test pushes null, known-good, wrong and malformed judge replies through and refuses to grade real runs if any fails |
| `judge_prep.py` | Strips arm labels behind opaque ids and emits a blind judging set plus a key you never show the judge |
| `rulecheck.py` | Mechanical rule detector with must-flag/must-not-flag tests per rule — kept as the worked example of a compliance score that reads CLEAN on the known-bad case. Its output is a precision-first proxy metric, never a verdict |
| `build_v2.py` | Builds the treatment skill as *original + inserted card*, asserting the line-count delta so the arms differ by exactly one thing |
| `tasks.json` | The task set, with per-arm lines isolated to a single substitution |
