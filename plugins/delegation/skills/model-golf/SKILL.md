---
name: model-golf
description: "Empirically compare models, prompts or effort settings on YOUR real workload instead of benchmarks and vibes — task set, run matrix, honest grading, cost under prompt caching. Use when choosing which model to route subagents to, deciding whether an expensive model is worth it, testing whether a prompt change changes behaviour, or asked \"is X actually better than Y for this\". NOT skill triggering (skill-creator)."
---

# Golf a model choice

You are comparing options — models, prompts, effort levels — on tasks you actually run. The runs are
cheap and mostly agree. **The expensive, error-prone part is grading them**, and a grading bug does not
announce itself: it produces a clean table with a wrong conclusion in it, which you then act on.

Everything below exists because it went wrong on a real run.

**Provider-agnostic.** The subject can be Claude subagents, an OpenAI model behind an API, or a whole
assistant. The method only needs a way to issue the same request N times and read the answer back.

**If you already have a harness that golfs a non-Claude assistant** (a chat-assistant eval, a
chatbot regression suite), read it before building a new one — such harnesses tend to arrive
independently at multi-run pass-rates ("single runs lie"), programmatic checks as small named
functions, and a keep/rollback recommendation as the output. `multirun.sh` beside this file is a
generalized version of that shape. **Extend an existing harness rather than starting fresh**; use
this skill for the parts it won't cover — pre-registration, grading open-ended output by claim,
verifying the knob you're varying, and cost accounting.

## Know the model before you design tasks

**Do a reading pass first** — the vendor's prompting guide, the recommended defaults *for
coding/agentic use* specifically, and the documented failure modes. Skipping it spends probes
rediscovering documented behaviour and risks tuning against the model's grain. **Research sets the
hypothesis; probing tests it**, and neither replaces the other. Watch especially for guidance that
*conflicts with the agent harness you are running inside*: a model documented as following instructions
very closely will oscillate when a layered system prompt's autonomy rules contradict the harness's own,
so a generic "ask before proceeding" rule **hurts** there while a non-thinking model usually wants
exactly that nudge. Vendors also warn against upfront-plan/preamble prompting for some models, which can
stop them early. None of this is visible from a pass rate; it looks like the model being erratic.

**Detect thinking vs non-thinking empirically — the model id does not tell you.** Send one trivial
question and read the usage block: tens of completion tokens and no reasoning tokens, answered fast, is
non-thinking; hundreds to thousands with `usage.completion_tokens_details.reasoning_tokens` populated,
answered slowly, is thinking. For a reasoning model, sweep the effort setting across its levels and read
`reasoning_tokens` at each, so the matrix is designed around the real cost curve rather than a guess.

**Start from the published sampling presets, and know which three are traps.** The presets differ
between a model's thinking and non-thinking modes, and the published pair is a better starting point
than anything you would invent. Never run temperature 0 / greedy on a thinking model — it triggers
repetition loops. Keep `presence_penalty` at 0 for code: legitimate repetition is everywhere in source
and high values risk language-mixing (the higher figure quoted around the web is for general chat). And
a thinking deployment needs a generous output cap, because reasoning that overruns the cap truncates the
answer to *nothing* — an empty body, not an error. Observed: a vague prompt burned 4000+ reasoning
tokens and returned empty. Front-load answers and refusals so a tight client-side cap can't silently
yield nothing.

## Before you run anything

**Derive the task set from the real workload, not from imagination.** Mine your own transcripts for
what subagents were actually asked to do and weight the tasks accordingly. On the run this came from,
the real split was 46% code/repo and 41% research — while the first two hand-invented tasks were "count
some files" and "read a doc", neither of which is representative, and both of which tied across every
model and measured nothing. `mine-prompts.py` beside this file does the extraction.

**Include at least one task you expect to tie, as a negative control.** If your bounded, single-source
task separates the models, the harness is noisy and none of the other results are trustworthy.

**Pre-register the ground truth, in a file, before you see any results.** Write down the right answer,
and for open-ended tasks the full list of acceptable claims, *then* run. Grading you invent after
reading the outputs will rationalize whatever you already believe. `claims.md` beside this file is the
template — it carries verified findings, known non-findings (reporting one is a false positive), and
unresolved ones scored separately.

**Ground truth must be something the experiment cannot change.** A task counting agent-metadata files
was invalidated because the benchmark spawned agents while running, so the true answer drifted from 430
to 446 mid-experiment and every run was marked wrong against a stale number. Ask of each task: *could
running this benchmark alter its own answer?* If yes, pick a different task or freeze the input first.

**Verify the knob you are varying is actually applied.** An entire "effort" axis was run, tabulated and
reported before anyone noticed the `Agent` tool has no `effort` parameter — it was silently dropped, and
every row carried a label that never reached the model. The parameter not existing is only the first of
three ways this happens, and the other two leave even less of a trace:

- **Wrong case in the wire name.** A client that passes a model's options through verbatim needs the
  provider's snake_case names (`top_p`, not `topP`). A camelCase key is not an error — it is dropped and
  the server default applies.
- **A proxy or gateway stripping non-standard keys.** A gateway configured to drop parameters its
  upstream doesn't accept silently removes things like `top_k` / `min_p` for an OpenAI-shaped upstream;
  those have to go through an extra-body passthrough instead.

Either way the axis is a relabelled control arm. Before the real matrix, run one probe and confirm the
setting appears in the recorded metadata — and where a proxy sits in the path, in its request log too.
**A parameter that was dropped and a parameter that made no difference produce identical tables.**

## Running the matrix

**A control at the ceiling is not a result — it is a probe that failed to discriminate.** If the
control arm already scores ~1.0, there is no headroom for the treatment to move anything, so "no
effect" describes your task's difficulty, not the thing you are testing. Reporting that as
"redundant" licenses deleting something the experiment never tested. Three probes did exactly this
on one run, and the real-world evidence pointed the opposite way for all three. **Design at least one
task per condition that the control fails**, and treat a saturated control as a signal to make the
probe harder and re-run.

**Disabling a capability is not a neutral control.** Running arms with `--tools ''` looked like a
clean way to keep answers short, but it penalised one arm specifically: that arm's instructions say
*go and verify*, so the model reached for a tool it did not have and emitted a stub. Its answers
opened with exactly the target behaviour and then truncated, scoring zero against a control scoring
one. If you must constrain the environment, apply the constraint **identically in every arm as an
explicit instruction**, so it is a constant rather than a confound — and check whether the constraint
interacts with what you are measuring before you trust the table.

**Record the condition inside each artifact, not just in the directory name.** Two runs writing to
one output directory produced a dataset mixing two prompt conditions with nothing on disk to tell
them apart — discovered only because the file count exceeded what was queued. Stamp a hash of the
prompt/framing into every result file, and have the runner refuse to start when another is alive.
Related operational trap: **kill the runner's parent before its children**, or the job scheduler
respawns workers as fast as you kill them and the cleanup silently accomplishes nothing.

**Spawn all conditions of one task concurrently.** Concurrent requests with the same prefix all miss
prompt cache, so cost becomes order-invariant and you avoid the confound where whichever condition ran
first pays the cache-write and everything after reads cheaply. Keep concurrency identical across cells.

**Byte-identical prompts, one variable.** Store the prompts in a file and have the runner read them,
rather than retyping per condition. Never mention the model, the comparison, or that it is a benchmark —
that is an instruction the agent can act on.

**A runner collects; it must not grade.** Tell it explicitly to relay answers verbatim and add no
interpretation. Then grade from the transcripts on disk, not from the runner's summary — otherwise a
wrong summary launders a right answer, and you cannot tell which you have.

**Run the trials as subagents that return only the distilled result.** Many noisy calls × many reps run
inline floods the orchestrating context with raw transcripts and serialises work that should be
parallel. Spawn one agent per condition, or per adversarial category; each runs its own N reps, scores
them with the verifier, and returns **only** the pass-rate, the failing inputs, and a one-line verdict —
never the raw dumps. You stay the orchestrator. This is the practical form of the rule above: keeping
collection out of grading is partly correctness, and partly that a context full of trial transcripts
cannot compare conditions.

**Give each concurrent prober its own scratch directory.** Parallel probers default to generic filenames
(`t1.sh`, `probe.py`, `payload.json`) in one flat scratch area and silently overwrite each other's
harnesses and outputs; tell each to work under its own `mktemp -d`. **Learn the failure signature,
because it is alarming and wrong:** a prober that reads back a clobbered file finds a *sibling probe's*
fixture and may dramatize it as a planted malicious harness, or as a hidden instruction to conceal
something from you. That shape is a confabulation from a filename collision, not tampering. Before
escalating, list the scratch area and match the "malicious" content to another probe's fixture — the
probe's own results stay valid.

**Exclude runners from the graded set.** A runner quotes the task prompts, so any fingerprint-matching
grader will pick it up and score its preamble as an answer. That produced a phantom failure and a
spurious pass-rate drop before it was caught. Identify runners from structure the harness writes (an
agent another sidecar names as `parentAgentId`, or whose transcript holds an `Agent` call), not from
words in its description.

## Grading

**Grade the behaviour, not the prose about the behaviour.** A refusal probe scored on hedging language
rated a control arm 1.0 for an answer that said *"I can't give you verified numbers"* and then shipped
eleven fabricated version numbers under a `Confidence: High` column. The arm that actually withheld them
scored 0.0, because its wording ("can't *fill* this table") missed the lexicon. The result was a clean
table with the effect **inverted**. The pre-registered criterion was "unknown must render as unknown,
never as a plausible number" — so the check had to count the numbers that shipped, not the apology in
front of them. **Whenever the criterion is "does it refrain from X", grade X, never the announcement.**

**Grade by claim, not by pointer.** The single worst error on the source run: findings were compared by
extracted `File.java:LINE` citations, which made one model look like it had found two unique defects. It
hadn't — both were reported by cheaper models as prose against an already-cited line. **Counting
citations measures formatting, not coverage**, and the false conclusion was written into a skill before
it was caught. Two findings are the same claim when they describe the same defective behaviour, whatever
they cite.

**Read the answer from a field, never from the prose.** Every task prompt ends with the same
instruction (`grade.py`'s `answer_instruction`): finish with a fenced ```` ```json ```` block holding
`{"answer": <typed value>}`. The grader compares that field exactly, or within a stated numeric
tolerance; a pattern over the prose passes on "15" appearing anywhere. No block, bad JSON or the wrong
type is **unscored**, reported in its own column and left out of the pass rate. A judge is asked the
same way: `claude -p --json-schema` with an enum verdict, and an off-enum reply is unscored.

**Objective checks where a script can decide it; a judge only where it can't.** Exit codes, file diffs,
exact-match extraction, resolved citations. For a judge, hold it fixed, blind the labels, score each
pair in both orders and keep only order-agreement, use a per-criterion binary rubric rather than a
1–10 score, and hand-label a sample first to measure which way it errs. **A wrong gate misleads worse
than no gate**; verbosity bias in particular inverts cost findings, because expensive models write more.

**Grade the answer the agent delivered, not its last words.** Subagents that return through
`SubagentHandback` put the answer in that tool call and end on a sign-off ("Report delivered."). A
grader reading the last text block scored 6 of 60 correct runs as failures, split unevenly enough to
look like a model gap. When a failing row's graded text is not an answer, the grader is reading the
wrong field.

**Check citations resolve, then read what they point at.** Resolving a `file:line` proves the pointer
is real, not that the claim is true. Both are worth checking and they are different checks.

**Correctness needs many more runs than cost does.** Token and cost figures are near-deterministic given
a fixed prefix; per-run correctness is Bernoulli and needs 5+ reps per cell before a gap means anything.
Past ~5 reps, buy more *tasks* rather than more reps — between-task variance dominates.

## Cost accounting

**Report cold-equivalent cost as the headline** — price cache reads at the full input rate. That number
is order-invariant and comparable across runs. Report billed cost beside it as the practical figure.

**Put every model in the price table.** One model was omitted and silently fell through to a default,
reporting exactly half its true cost, in a table that otherwise looked fine. Assert the model is in the
table rather than defaulting.

**Never compare raw token counts as if they were cost.** A cheap model that takes twice the turns can
burn more tokens and still be far cheaper. Judge by cost; and don't assume the inversion — measure it.

**Cost is not the constraining resource on a subscription.** On a Max plan the limits are what bind, and
model-specific limit buckets may or may not be additive with the shared one — verify against the usage
page rather than reasoning from its labels.

## Reading the result

**Report where the models tied.** A finding that eight of nine task types tied is as decision-relevant as
the one that separated them, and it is what tells you the cheap model is safe for that shape of work.

**Say what the result does not cover.** Two runs per model on one package is enough to kill "the
expensive model finds more"; it is not a model ranking. Bound the claim to the workload you actually ran.

**Look for the variable you did not control.** On the source run, what actually separated the good
answers from the mediocre ones was **whether the agent executed code or only read it** — a property of
the brief, not the model, and one that had been left uncontrolled. When one condition wins, ask what
else it was doing differently before crediting the label on the column.

**Re-test after applying the change.** The pass that proved a config is not the pass that proves the
*edit* landed. Once it's applied, re-probe the cases it was meant to fix **and** run a regression sweep
over the ones that already worked — a prompt or parameter change that fixes one category and breaks
another is the normal outcome, not the surprising one.

## Test the grader in both directions

A grader has two failure modes and the cheap check only catches one. **Run a null agent to catch false
positives** (see below) — but also **run a known-good answer through the grader to catch false
negatives.** On the source run, both of the worst errors were the grader rejecting correct work, and
each looked exactly like a model failing:

- Six runs answered a count correctly; the ground truth had drifted while the benchmark ran, so all six
  scored as failures and one model looked much worse than it was.
- A finding pre-registered as a "known non-finding" turned out to be a real defect once someone executed
  it. Runs that found it would have been scored as false positives — penalized for being right.

So: for every task, push the **expected** answer through the grader and confirm it passes, alongside
pushing a null answer through and confirming it fails. A check that can't do both is measuring itself.
This is also why pre-registration earns its keep even when the pre-registration is *wrong* — writing the
claim down first is what let the error surface as "my rubric was wrong" instead of silently becoming
"that model reports junk".

## Probe behaviour, not just correctness

Correctness on well-formed tasks is the easy half; the differences that bite in delegated work show
up on malformed input. Build probes for each, and score them as their own rows, not folded into
accuracy — a model can be more accurate *and* worse to delegate to:

- **a planted false premise** (the sharpest discriminator on the source run — neither answer looks
  wrong until you know the premise was);
- **genuine ambiguity** — does it ask rather than silently pick one reading;
- **a logical contradiction** ("synchronous but returns a Promise");
- **destructive-operation safety** — does it reach for `rm -rf` / force-push unprompted;
- **scope expansion, over-compliance with a bad instruction, fabricated citations, premature "done".**

The worked cases: `references/behaviour-probes-and-literature.md`.

## Baselines borrowed from the literature

Four checks the source run did not teach, with citations and figures in
`references/behaviour-probes-and-literature.md`:

- **Run a null agent** (does nothing / "N/A" / dumps the file). **If it scores above zero, your grader
  is what's being measured.** Add an **oracle** run (task is solvable) and a **non-AI baseline** such
  as `grep` (task needs a model).
- **`pass^k`, not `pass@k`**, when the question is "can I route work here" — reliability, not ceiling.
- **Never let a model judge a comparison it competes in** — blinding labels is not enough.
- **A cheap model with retries is the baseline any expensive model has to beat.** Plot cost against
  accuracy; a single accuracy number is not a result.

## Companion files

Working harness from the run this skill came from. **All four carry run-specific constants** — task
fingerprints, repo paths, the price table — marked at the top of each. Treat them as a starting shape
to edit, not as a library to call.

| file | does |
|---|---|
| `mine-prompts.py` | Extracts real subagent prompts from transcripts and clusters them, so the task set reflects the actual workload |
| `claims.md` | Pre-registration template — verified claims, known non-findings, unresolved ones |
| `grade.py` | Identifies runs by prompt fingerprint, and the model by the id the API returned in the transcript — the sidecar holds only the alias, and `opus` has meant two differently-priced models (never the agent's self-report). Checks the typed `answer` field of the final ```` ```json ```` block, reports unscored separately, prices each run cold-equivalent; `--selftest` runs good/wrong/malformed fixtures |
| `verify-citations.py` | Resolves `file:line` citations against real source and prints the actual line, so a claim is judged against the code rather than against how convincing it sounds |

`grade.py` is also where two of the traps above are enforced in code: it excludes runners from the
graded set, and its price table asserts rather than defaults.
