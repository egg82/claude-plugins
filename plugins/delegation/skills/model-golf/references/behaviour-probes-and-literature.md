# Behaviour probes, and four borrowed baselines

Detail behind the last two method sections of `SKILL.md`. Open it when designing the probe set.

## Probe behaviour, not just correctness

Correctness on well-formed tasks is the easy half. The differences that actually bite in delegated work
show up on malformed input, and they need probes designed for them.

**Plant a false premise and see who refuses it.** The single sharpest discriminator on the source run
was accidental: a research prompt asked what causes a failure state in a product that *has no such
state*. The expensive model cloned the repo, grepped for the term, proved it absent with a canary, and
reported the question was malformed — naming the product the term actually came from. The cheaper models
produced fluent, well-cited answers about a thing that does not exist. **Neither answer looks wrong
until you know the premise was.** Build at least one probe on a premise you know is false.

**Probe for clarification-seeking on genuine ambiguity.** Write a task that legitimately reads two ways
and score whether the agent asks rather than silently picking one and proceeding. For delegated work
this matters more than raw accuracy: a subagent that guesses wrong and reports confidently costs more
than one that comes back with a question.

**Plant a logical contradiction as well as a false premise.** "Synchronous but returns a Promise",
"O(1) but scans N". Does it notice the premise cannot hold, or implement something and move on? Same
shape as the false-premise probe, a different failure.

**Probe destructive-operation safety.** Ask for something whose obvious implementation is irreversible —
`rm -rf`, `dd`, a force-push or a hard reset. Whether a model reaches for the destructive form
unprompted matters far more for delegated work than a point of accuracy.

**Other behavioural dimensions worth a probe each**, because none of them show up in a pass rate:
scope expansion (does it do more than asked — measurable by whether findings land outside the stated
scope), over-compliance with a bad instruction, fabricated citations (resolve every pointer), and
premature "done" claims on work that isn't finished.

Score these as their own rows, not folded into accuracy. A model can be more accurate *and* worse to
delegate to.

## Four things from the literature that this session didn't teach

Everything above is a scar. These four are borrowed, and they are here because they cover gaps the
run genuinely didn't expose.

**Run a null agent as a baseline — the cheapest check there is.** An agent that does nothing, answers
"N/A", or dumps the whole file. **If it scores above zero, your grader is what's being measured.**
Applied to ten popular agentic benchmarks, the Agentic Benchmark Checklist ([arXiv:2507.02825](https://arxiv.org/html/2507.02825v1))
found misestimations up to 100% relative — a trivial empty-response agent passes **38%** of τ-bench's
airline tasks, and SWE-Lancer scored **100%** without solving anything because the agent could reach
the test files. A null run would have caught the citation-counting bug here immediately: an agent
emitting citations and no findings would have "covered" as much as a real one.

**Add an oracle run and a non-AI baseline too.** An oracle proves each task is solvable at all; `grep`
or a linter proves the task needs a model. For bug-hunting especially, if `grep` finds it, the
comparison is measuring the harness.

**`pass^k`, not `pass@k`, when the question is "can I route work here."** pass@k measures the
capability ceiling (any of k attempts succeeds); **pass^k measures reliability (all k succeed)** and is
the decision-relevant number for delegation. τ-bench ([arXiv:2406.12045](https://arxiv.org/abs/2406.12045))
introduced it because GPT-4o scored pass^8 under 25% where pass@1 was ~50%.

**Never let a model judge a comparison it competes in.** Self-preference isn't just style bias: models
recognize their own generations, and recognition accuracy is *linearly correlated* with preference
strength ([arXiv:2404.13076](https://arxiv.org/pdf/2404.13076)). Blinding labels is not enough — it can
identify itself from prose. Use a judge outside the field, score both orders, keep only order-agreement.

**And the caution that most directly checks this session's instinct:** cheap baselines — retry, raise
temperature across retries, escalate to a pricier model only on failure — matched or beat SOTA agents
for orders of magnitude less ([arXiv:2407.01502](https://ar5iv.labs.arxiv.org/html/2407.01502)); one
agent cost ~50× a warming baseline for equal accuracy. **A cheap model with retries is the baseline any
expensive model has to beat**, and it is almost never run. Relatedly, on the cost–accuracy Pareto
frontier fewer than a third of models sit on it, and in only 1 of 9 benchmarks was the most expensive
model on it at all. Plot cost against accuracy; a single accuracy number is not a result.
