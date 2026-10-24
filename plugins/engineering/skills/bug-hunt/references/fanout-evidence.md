# Fan-out evidence — what the measurements behind `SKILL.md`'s coverage rules showed

Read when a coverage or finder-briefing rule sounds arguable, or when choosing a model for finders.

## Dealing a partition out once is not covering it

Bug Hunt Bench replicated one fixed configuration — same model, prompt, harness and effort — three
times over the same repo: across the three it **ever** fixed 33 of 105 planted bugs, yet only **11
fell in all three**, and 12 in exactly one. Model choice is held constant, so that spread is
run-to-run nondeterminism on identical input. Caveats: planted bugs, a one-shot brief with no execute
instruction, one arm at n=3. (`phuryn/bug-hunt-bench`, `results/run-notes.md`.)

## The expensive model does not find more; executing does

One 12-file Java package, identical brief, two runs each across haiku / sonnet / opus / Fable:
**every distinct real defect was found by at least one cheap run.** Fable produced **no finding the
others missed** — its top defect (a `Matcher.groupCount()` misuse) was also found by haiku, by
reading, for ~1/30th the cost. What separated runs was **whether the agent built a harness and ran
the code**, not which model it was: Fable executed the parser and proved its findings, and so did opus
and sonnet when they chose to. Caveat: two runs per model, one package, one language — enough to
kill "the expensive model finds more", not enough to rank models.

Cost anchors, cold-equivalent, per agent on that task: haiku ~$1, sonnet ~$5–8 (two write-ups of the
run disagreed), opus ~$15 (Opus 5), Fable ~$30.
The expensive models wander outside a stated scope, which is pure cost.

## The execute instruction is the whole effect

Same model, same package, one sentence added to the brief — *"You MUST confirm every finding by
EXECUTING the code, not by reasoning about it… A finding you cannot demonstrate by running something
is not a finding"*:

| brief | ran code | tool calls |
|---|---|---|
| without the instruction | **0 / 3** | 14–16 |
| with it | **3 / 3** | 31–50 |

~3× the tool calls, and it changed what the findings were worth. Without it, runs asserted a *backwards* mechanism — that `computeIfAbsent` caches
the null and suppresses later logging; it never stores it. With it, runs proved the real behaviour
(`map.size = 0`, function invoked every call), and promoted a defect a read-only pass had dismissed as
cosmetic. **Reading produces confident mechanisms; only running distinguishes the right one.**

## Counting citations measured formatting, not coverage

The first analysis of the model comparison extracted `File.java:LINE` citations and compared the
sets, which made Fable look like it had found two unique defects. Both were also reported by opus and
sonnet, written as prose against a line already cited. Dedup findings by the *claim*.
