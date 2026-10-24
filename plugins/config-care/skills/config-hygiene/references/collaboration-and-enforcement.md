# Teams, enforcement, and what the evidence actually supports

For deciding what to enforce, and how, wherever agents do a meaningful share of the work.

**Read the tier before you repeat anything here.** Most claims carry a source URL. A URL means the source
was located — it does not mean every figure beside it survived checking. An independent fact-check of the
URL-carrying claims found wrong denominators, figures read from the wrong table, a figure credited to the
wrong tool, and several claims the cited page actively contradicts. Those are corrected in place below,
and where a source turned out not to support a claim the claim was cut or its tier dropped. Section 2, the
harness-behaviour section, is the one you are most likely to act on and the one most likely to change
under you between versions, so check it against your installed version rather than trusting this file.

**`[Ø]` marks a number that circulates but has no locatable source.** Those entries exist so that silence
is not mistaken for support. This subject area is unusually prone to it: several widely-repeated figures
turn out to have a real-looking near-neighbour in the literature measuring something slightly different —
a different metric, a different experimental setup, two category averages read as a per-model range. Where
that is the case, the entry names the trap.

One citation is **version-pinned** because its figures live in an image and change between revisions of the
paper. Leave the pin in place.

- **[V]** verified directly against a primary source
- **[M]** measured, peer-reviewed or with disclosed method
- **[P]** vendor telemetry / practitioner report — directional only
- **[Ø]** no evidence found; stated so you don't assume silence means support

---

## 1. The single most important finding: prose doesn't bind

**[M]** On an SOP-following benchmark with expert-written handbooks and 824 deterministic criteria spanning
**65 tasks** (824 is the criterion count, not the scale), the **best of 30 model configurations scored
36.2% strict pass@1**; most frontier configs under 25%.
The characteristic failure: *"Nearly every failed trajectory ends with a confident statement that the
handbook was followed, frequently citing the specific sections that were violated."*
— *HANDBOOK.md: A Benchmark for Long-Context Agentic Instruction Following*,
<https://arxiv.org/abs/2607.25398>

**[M]** Across 1,650 Claude Code sessions / 16,050 observations: instruction-file **size and internal
contradictions are null for *adherence*** — a bigger file is not obeyed less well, which is a
different question from what it costs to carry (every instruction is paid for in the context
budget on every session, and the size thresholds in the scanner are about that cost, not about
adherence). Those two are *affirmative* nulls, *"supported by affirmative-null Bayes
factors (BF10 between 0.05 and 0.10)."* **Position and single-vs-split are not** — they are *"failures to
reject without Bayes-factor support,"* i.e. underpowered non-findings rather than evidence of no effect.
What does matter: task identity, and compliance falling **~5.6% in odds per step (OR = 0.944)** within the
session lengths tested, *"though the relationship is non-monotonic rather than a constant per-step
effect."*
— *Instruction Adherence in Coding Agent Configuration Files: A Factorial Study of Four File-Structure
Variables*, <https://arxiv.org/abs/2605.10039>

**[P]** Of 580 instruction files across 568 repos, only **3.8% of lines are machine-verifiable**;
**74% of files contain zero extractable rules** (430 of 580).
— a DEV Community post by Brad Kinnard presenting output from **his own parser** (RuleProbe;
`npm install -g ruleprobe` is on the same page).
Tiered **[P]**, not [M]: directional, method not independently disclosed.
<https://dev.to/moonrunnerkc/we-parsed-580-ai-instruction-files-96-of-the-content-cant-be-verified-4cg5>
**[Ø]** A widely-repeated claim that ~62% of such files merely restate what a linter already enforces has
**no locatable source.** The nearest real figure belongs to a **different tool** — ctxlint, by Vamshidhar
Reddy, in a separate DEV post, whose output reads
`Signal: 40 tokens (38%) ✓  Noise: 64 tokens (62%) ✗` for a single example file. Kinnard's page contains no
62% and no token-share figure at all. Different tool, different quantity. Do not use it.

**[M]** Context files do **not** generally improve success while adding **>20% cost** (20% and 23% on
average across two settings). But naming a concrete tool took its usage from **<0.01 to 1.6 invocations
per instance** — agents obey *specific, checkable directives*; narrative repository overviews do nothing.
— *Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?*,
<https://arxiv.org/abs/2602.11988> (the paper carries no institution line; don't attach one).

**[V]** Anthropic's own documentation: *"Unlike CLAUDE.md instructions which are advisory, hooks are
deterministic and guarantee the action happens"*, and *"If Claude already does something correctly
without the instruction, delete it or convert it to a hook."* Also: *"Bloated CLAUDE.md files cause
Claude to ignore your actual instructions!"* All three are on
<https://code.claude.com/docs/en/best-practices> — not on the hooks or memory pages.

**What follows:** write the rule down so humans understand *why*; enforce it with a check. Prose is
documentation, not control. Two consequences people miss — **shorter sessions beat better
documents** (compliance decays as a session runs), and **adding instructions has a cost** paid by
every other instruction.

---

## 2. Enforcement mechanisms — and three traps that look like enforcement and aren't

**[V] `exit 1` fails open.** *"Claude Code treats exit code 1 as a non-blocking error and proceeds with
the action, even though 1 is the conventional Unix failure code."* A policy hook written with `set -e`
therefore enforces nothing while appearing correct. **Use `exit 2`** — which blocks on **15 events**,
including `PreToolUse`, `UserPromptSubmit`, `Stop`, `SubagentStop` and `PreCompact`.

> **Section 2 is the one to verify yourself.** These are harness behaviours, documented across four pages —
> <https://code.claude.com/docs/en/hooks>, <https://code.claude.com/docs/en/settings>,
> <https://code.claude.com/docs/en/permissions> and <https://code.claude.com/docs/en/sandboxing> — but they
> are also the claims most likely to change under you between versions, and the ones you will actually act
> on. Check them against your installed version rather than trusting this file.

**[V] `PostToolUse` cannot block** — the tool has already run. Enforcement must be `PreToolUse`.

**[V] A `Write(path)` permission rule is a no-op.** Permissions are checked against `Edit(path)` and
`Read(path)` **only**; a rule written for `Write`, `NotebookEdit`, `MultiEdit` or `Glob` is *accepted and
never consulted*. It is not silent, though — startup prints `Permission deny rule
(.claude/settings.json): Write(docs/**) is not matched by file permission checks — only Edit(path) rules
are. Use Edit(docs/**) instead`. This is the trap behind a rule like "agents may not modify tests."
— <https://code.claude.com/docs/en/permissions>
Scope this to *path-scoped permission rules*: a bare tool name passed to `--allowedTools` is a
different mechanism, and `Glob` **is** consulted there (see §6). The same tool name means one thing
in a `Glob(path)` rule and another on the command line.

**[V] Deny rules don't cover subprocesses.** `sed` is caught; a script that opens the file itself is
not. **`sandbox.filesystem.denyWrite`** closes exactly that gap — but *only* that gap: *"Built-in file
tools: Read, Edit, and Write use the permission system directly rather than running through the sandbox."*
It governs Bash commands and their children, nothing else. So "agents may not modify tests" needs **both**
controls — an `Edit` deny rule for the file tools *and* `denyWrite` for subprocesses. Neither on its own is
immutability. — <https://code.claude.com/docs/en/sandboxing>

**[V] Underused:** `PreToolUse` can return **`updatedInput`**, rewriting the tool's arguments before
execution — auto-correction rather than refusal. The difference between a gate people resent and one
they forget is there.

**[V] Path-scoped rules load on READ, not WRITE.** A `.claude/rules/*.md` with `paths:` frontmatter
fires when a matching file is read, **not when one is created** — reported, reproduced, and closed
as *not planned*. So a rule intended to govern authoring is absent at authoring time. Independently
confirmed by a second researcher, who noted it is *"precisely the moment a duplicate helper gets
written."* **Anything that must govern creation has to be a `PreToolUse` hook.**

**[M] Static-analysis-in-the-loop helps, but be careful which numbers you quote.** Feeding analyser output
back to the model measurably reduces defects: security issues drop to **13.41%**, readability violations to
**11.38%**, reliability warnings to **10.75%**. Those three figures are **three different configurations**
of the same experiment — Table V's "2 issues selected", "5", and "All" rows respectively. No single run
yields all three, so don't state them as one outcome (the paper's own abstract does the pairing, which is
where the habit comes from). It is GPT-4o only, on PythonSecurityEval only, up to ten iterations, and the
Error column barely moves (~20.4% → 13.6–15.6%).
— *Static Analysis as a Feedback Loop: Enhancing LLM-Generated Code Beyond Correctness*,
<https://arxiv.org/abs/2508.14419>.
**[Ø]** Two figures often cited for this effect — "~20% fewer semantic errors" and a defect rate going
49% → 19% — have no locatable source. Use the ones above.

**[M]** No study isolates the format of an *individual* rule, though ContextCov compares the same
constraint set enforced executably versus stated as prose — checks compiled from the same AGENTS.md the
prose arm receives, over all 300 SWE-bench Lite tasks: *"ContextCov achieves 88.3% compliance compared to
67.0% (vanilla) and 50.3% (LLM Reflection)."*
— *Deriving and Enforcing Executable Constraints from Agent Instruction Files*,
<https://arxiv.org/html/2603.00822>

**Order to implement:** hooks (`exit 2`, consider `updatedInput`) → sandbox `denyWrite` **plus an `Edit`
deny rule** on tests and generated files (both, per the trap above) → custom lint/AST rules →
module-boundary fitness functions → runtime schema validation at model-output boundaries → golden
examples → generators last.

---

## 3. Verification — the part most likely to be built wrong

**[M] Verifier error *direction* is a domain property you cannot predict.** One verifier had an
**84.45% false-positive rate** on Blocksworld (*Can Large Language Models Really Improve by Self-critiquing
Their Own Plans?*, <https://arxiv.org/abs/2310.08118>, Table 2); another had a **95.8% false-negative
rate** on graph colouring (*On the Self-Verification Limitations of Large Language Models on Reasoning and
Planning Tasks*, <https://arxiv.org/abs/2402.08115>). And self-critique **destroyed** performance in a
third setting: a 16% baseline fell to a single correct instance out of 100 when the model backprompted
itself (*GPT-4 Doesn't Know It's Wrong: An Analysis of Iterative Prompting for Reasoning Problems*,
<https://arxiv.org/abs/2310.12397>).
Four things to keep straight when quoting this. Do **not** cite 2310.08118's 40% → 55% as "self-critique
helped": the paper declines that reading itself — *"the marginal improvement over the generator-LLM-only
method might not solely be attributed to the LLM verifier. The backprompting itself, which offers the
generator LLM multiple opportunities to produce a plan, could be a contributing factor."* A **sound**
verifier in that same Table 1 (LLM+VAL) reaches **88%**. Blocksworld is also that paper's *only* domain, so
it supports no across-domain comparison of its own. The FPR and FNR come from **two papers four months
apart** (same lab, same underlying model) — the error direction is a property of the **domain**, not of one
experiment, and in the later paper's own Blocksworld row the FPR is 18.55%. The collapse figure is the
paper's "one correct instance out of 100", not a printed percentage; a later paper reports 2% for that
cell. **[Ø]** A "+10.9 / −3.0" pair sometimes attached to this finding has no locatable source.

**→ Measure your verifier's FPR and FNR before trusting any loop. A loop with a bad verifier is
worse than no loop, not neutral.** This is the first thing to do, before adopting any review or
critic pattern.

**[M] An unsound critic is an injection vector, not dead weight.** A model "fixed" deliberately
**fabricated** criticism — an "evil" backprompt claiming a *correct* edge was wrong — at a **94% rate**,
identical to its rate on genuine errors, "without regard for overall correctness."
— <https://arxiv.org/abs/2310.12397>

**[M] "Verification is easier than generation" is not reliable.** On the coding split of JudgeBench, one
frontier model solves at **88.10%** and judges at **64.29%** — under the paper's own heading "Is verifying
a problem's solution easier than solving the problem itself?"
— <https://arxiv.org/abs/2410.12784>, Table 4. Note this is the *coding* column specifically.

**[M] Imperfect verifiers impose a hard accuracy ceiling regardless of compute.** At a cost-benefit
ratio of 4, **the optimal number of samples is K ≤ 5 for all four models shown in Figure 4** (the Llama-3.1
and Code Llama families; the paper itself tests around fourteen models) — "sample a lot and pick the best"
has a low optimum. — *The Limits of Inference Scaling Through Resampling*, <https://arxiv.org/abs/2411.17501>.
The false-positive rate also **rises with K**, which is the counterintuitive part — but quote the
direction, not a curve. The paper states the trend in prose and shows it in a figure; the steep version
belongs to one model on one benchmark (the worst of nine). Do **not** summarise the stronger model as
"0.07→0.08": that is a first-and-last-bar read of Figure 10's GPT-4o panel, which prints no numbers at all
and, read across, starts ~0.07 at K=1, **peaks ~0.15 at K=4–7**, then sits ~0.08 at K=8–15 with the K≥16
bins empty. The truncation hides a doubling and covers a shorter K range than Llama-3.1-70B's.

**[M] Execution grounding inherits your test suite's blind spots.** A much larger test set reduces
pass@k by **up to 19.3–28.9%** (EvalPlus, <https://arxiv.org/abs/2305.01210> — note that is an *up-to*
bound, not an average), and **31.08%** of passing patches on one benchmark were "suspicious… due to weak
test cases" (SWE-Bench+, <https://arxiv.org/abs/2410.06992>). Execution is still the best available
oracle — it is not a perfect one.

**[M] LLM-judge agreement figures are usually tie-excluded.** The widely-quoted **85%** is the
tie-*dropped* setup, whose human-human comparison is **81%**. With ties **included** the judge scores
**66%** against a human-human **63%**, on a **33% random floor**. Position bias is systematic, not noise:
one model is **65.0%** self-consistent under an answer-order swap, another **23.8%**.
— *Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena*, <https://arxiv.org/abs/2306.05685>:
the agreement figures are in **Table 5(a)** and the position-bias ones in **Table 2**. (Table 6 is the
Chatbot Arena table — no (a)/(b) subtables, no human-human cell; Table 3 is the verbosity attack.)
**Never pair "85%" with "63%"** — they come from different setups. 85% goes with 81%; 66% goes with 63%.
The 85% figure is the one that circulates, which is why the mismatch is easy to make.

**[M] Judge panels don't pay.** A 9-judge panel yields **2.18 effective votes** (95% CI 2.07–2.31), and
on one benchmark the panel's 72.0% "barely edges the best single judge (71.8%) by 0.2pp — within noise."
— *Nine Judges, Two Effective Votes: Correlated Errors Undermine LLM Evaluation Panels*,
<https://arxiv.org/abs/2605.29800>

**Three rules worth adopting verbatim:**
1. **Never let the model be its own stopping condition.**
2. **Feedback *existence* dominates feedback *richness*.** Spend on soundness, not prose.
   **[Ø] The specific 40%→74%→86% figures could not be sourced and are withdrawn.** The nearest real
   measurement is weaker than the slogan. One ablation in *GraphInstruct: A Progressive Benchmark for
   Diagnosing Capability Gaps in LLM Graph Generation* (<https://arxiv.org/abs/2605.09997>) runs
   `retry 0.7488 → verify-only 0.7946 → coarse 0.8021 → fine 0.8099`, so a binary pass/fail signal
   captures ~75% of the total gain (+0.046 of +0.061). But the paper treats the remaining quarter as
   material — *"our fine per-constraint signal unlocks the additional 25%"* — and this is a single model
   (GPT-4o-mini) at a fixed T=3, on the paper's own benchmark, ablating the paper's own method. "Richer
   feedback adds close to nothing" overstates it.
3. **Always budget-match the baseline** — on GSM8K, multi-agent debate at 6 responses (**83.2%**)
   *loses* to plain self-consistency at 6 (**85.3%**); at 9 responses it is 83.0% vs 88.2%. Most
   prompting comparisons never run this. — *Large Language Models Cannot Self-Correct Reasoning Yet*,
   <https://arxiv.org/abs/2310.01798>, Table 7.

---

## 4. Multiple agents — what the evidence says not to build

**[M] No peer-reviewed result shows role-based multi-agent beating a single strong agent at matched
compute on coding.** A capability-saturation threshold matters: "baselines above approximately 45%
predict zero-to-negative multi-agent gains", and that rule "matches the sign of the multi-agent gain in
94% of 16 SWE-bench Verified and Terminal-Bench model × benchmark configurations." Frontier models sit
far above 45%. Every top solver on the main benchmark is single-agent; a no-agent fixed pipeline beat
contemporaneous role-decomposed systems at a fraction of the cost.

**[M] Costs, from that same study.** **Coordination** overhead — *not* reasoning overhead — runs from
**0%** (SAS, the single-agent baseline) to **515%** (Hybrid), with Independent 58%, Decentralized 263% and
Centralized 285% in between: *"Coordination complexity is parameterized by communication overhead: the
total number of inter-agent message exchanges required per task."* Reasoning tokens are the variable the
study **holds constant** — *"All systems matched for total reasoning tokens (mean μ=4,800 per trial)"* — and
the phrase "reasoning overhead" appears nowhere in it. Error amplification ranges **4.4×–17.2×**:
Independent systems amplify trace-level errors 17.2× through unchecked propagation while centralized
coordination contains it to 4.4× via validation bottlenecks. Those are min/max **across architectures**,
not a range of one quantity.

**One study, two citations — not two sources.** *Capable language models can outgrow the benefits of
collaboration* (Nature Machine Intelligence, <https://www.nature.com/articles/s42256-026-01268-y>) and
*Towards a Science of Scaling Agent Systems* (<https://arxiv.org/abs/2512.08296>) are the same work: a
byte-identical 20-author list, the same N=260 configurations, and the Nature page cites the preprint.
Citing both corroborates nothing.

Separately, multi-agent systems "use about 15× more tokens than chats"
(<https://www.anthropic.com/engineering/multi-agent-research-system>).
**[Ø] Withdrawn:** a "~62× for debate" figure and a "single agent used 86% fewer tokens" figure could not
be sourced. The nearest real debate numbers are 36×–49× by agent count and 17×–29× by round; the "86%"
that surfaces in search is an unrelated duplication-rate metric.

**[M] Where the failures are:** **44.2%** system design, **32.3%** inter-agent misalignment, **23.5%**
task verification — architectural, and *not* solved by a better model. — *Why Do Multi-Agent LLM Systems
Fail?* (MAST), <https://arxiv.org/abs/2503.13657v3>.
**Pin the version.** These numbers are in a figure, not the text, and they change between revisions: v1
reads 37.17/31.41/31.41 and v2's text reads 41.77/36.94/21.30. Only **v3** matches. An unpinned citation
will silently read as false.

**[P] The mechanism that matters once more than one agent is running:** parallel agents make **implicit decisions that
silently conflict**. Not file collisions — assumptions. The rule that follows: **writes stay
single-threaded; extra agents contribute intelligence, not actions.**

**[V]** *"Agent teams are experimental and disabled by default"*, and Claude Code's own docs warn
*"Two teammates editing the same file leads to overwrites"*, advise *"Start with 3-5 teammates for most
workflows"*, and head a best-practice section *"Start with research and review"* rather than parallel
implementation. Teammates inherit the lead's permission mode: *"If the lead runs with
`--dangerously-skip-permissions`, all teammates do too."*
— <https://code.claude.com/docs/en/agent-teams>

**[P] The practitioner ceiling is 2–3 concurrent agents**, reported independently many times. But
note the distinction that matters: that ceiling is about **writing** agents, where the constraint is
human review and the risk is conflicting decisions. Read-and-advise agents (investigation, review,
research) parallelise safely and widely.

**[V] Worktree isolation is native** (`--worktree`, per-subagent `isolation: worktree` —
<https://code.claude.com/docs/en/worktrees>) — don't buy an orchestrator for it. The third-party
orchestrator layer has thinned: `reworkd/AgentGPT` (36,299 stars) is archived, and OpenAI's `swarm`
(21,872) states *"Swarm is now replaced by the OpenAI Agents SDK."* And a live search of the SWE-bench
leaderboard — ~180 entries across splits, up from ~103 in Jul 2025 — finds **no** submission naming
LangGraph, CrewAI, AutoGen, LangChain, AG2 or MetaGPT, against 273 hits for `swe-agent`, 49 for `openhands`
and 23 for `agentless`. **Read that zero carefully: the leaderboard has no framework field**, so it is the
absence of the *name*, not proof the framework went unused.

**[P] Fan-in is the unsolved half.** Every orchestrator distributes; none integrates. One promising piece
of plumbing is an entity-level **tree-sitter merge driver** — it parses base/ours/theirs into semantic
entities — reported as resolving **31/31** scenarios against git's **15/31**.
— <https://github.com/Ataraxy-Labs/weave>.
**Three precisions that matter.** The README calls those *"31 real-world merge scenarios"*, but the "Full
breakdown" page it links from that very sentence
(<https://ataraxy-labs.github.io/weave/benchmarks.html>) heads the identical suite **"Synthetic
benchmarks — 31 hand-crafted merge scenarios across 7 languages"**, with entries like "Both add different
imports (TS)" — so this is the project's own synthetic suite, not real-world data, and the two pages also
**contradict each other** on TypeScript regressions (0 vs 3). An existing tool, Mergiraf v0.16.3, already
scores **26/31**. And "deterministic rather than LLM-based" is an inference — the README uses neither word.
Hence **[P]**: self-reported numbers on a self-authored suite.

---

## 5. Reuse, duplication, and repo shape

**[M]** Agents demonstrably under-reuse: average max redundancy **0.2867 for agents vs 0.1532 for
humans — a 1.87× increase** (Mann-Whitney, p<0.001) — while reviewers expressed *more* neutral-to-positive
sentiment toward the agent PRs. **The two findings are different samples.** The redundancy figure is
Dataset B, *"617 PRs from the crewAI repository"* — the single-repo caveat applies to that number alone.
The reviewer sentiment is Dataset A, *"3,858 PRs across all filtered Python repositories."*
— *More Code, Less Reuse: Investigating Code Quality and Reviewer Sentiment towards AI-generated Pull
Requests*, <https://arxiv.org/abs/2601.21276>

**[P] Treat the widely-quoted duplication trend numbers with care.** The much-cited +81% duplication
and −35% connectivity figures come from a vendor time series that **never identifies AI-authored
code** — AI is the assumed cause. Independent difference-in-differences work confirms rising
complexity and static-analysis warnings but finds **duplicate-line density insignificant**. The
literature reconciles as: **duplication shows up in greenfield generation, and is null in brownfield
patching.** A team maintaining existing systems is largely in the second case.

**[M] The one controlled study of repo cleanliness is a partial null**: across 660 trials on matched
repo pairs, cleanliness **did not change pass rate** — but clean repos used **7–8% fewer tokens and
34% fewer file revisitations**. Repo shape buys **navigation efficiency, not task success**.
— *Does Code Cleanliness Affect Coding Agents? A Controlled Minimal-Pair Study* (SonarSource),
<https://arxiv.org/abs/2605.20049>

**[M] Both local size and coupling predict failure — and local size predicts it harder.** Per standard
deviation, *"every +1SD in code lines suppresses the odds of success by ≈55%, whereas a +1SD in harmonic
centrality suppresses them by ≈20%"*, with *"both features contribut[ing] complementary information."* So
coupling is not the thing that dominates layout — size is the stronger single predictor. The **55% / 0%**
pair that circulates alongside this is a *different quantity*: the overall easiest and hardest conditions,
where 0% is four simultaneous corruptions, not the most-connected end of a centrality scale.
— Breakpoint, <https://arxiv.org/abs/2506.00172>

**[M] Visibility dominates.** Code the agent cannot see, it cannot reuse. On CrossCodeEval the best 15.5B
model reaches only **8.82%** code exact-match on Python with no cross-file context; retrieved cross-file
context takes it to **15.72%** with BM25. A third setting reaches 21.01%, but that one retrieves using the
*reference completion* — the paper calls it an estimate of the upper bound and says it cannot be applied to
realistic completion, so **15.72% is the attainable figure and 21.01% is an oracle**.
— <https://arxiv.org/pdf/2310.11248>
Beware two similar-looking numbers in the same paper. First, the same model's Identifier-Match F1 is 48.16
(Table 2); the 39.70 that circulates is the 1B StarCoderBase variant's cell in Table 7 ("Evaluation of
additional code LMs") — a different *model* as well as a different metric. Second, the genuine trap:
**15.72 appears twice**, as StarCoder-15.5B's code-EM with BM25 *and* as its Identifier-Match Python EM in
the in-file setting. That collision is almost certainly how the tables got crossed in the first place.

**[M] Retrieve definitions, not lookalikes.** A system retrieving APIs by semantic description improved
pass@1 by up to **+20%** over prior approaches, while retrieved *similar code* "often introduces noise,
degrading results by up to 15%". Note the +20% is a whole-system comparison rather than a clean ablation
isolating definitions as a context type; the −15% is a direct finding.
— <https://arxiv.org/abs/2503.20589>

Tension worth knowing: a separate study found *usage examples* in API docs contribute more than parameter
lists. Best read — usage examples for a specific API help; lookalike code from elsewhere hurts. Unresolved.

**[Ø] "Retrieval value is size-dependent"** — the widely-passed-around version of this, that search tooling
measures *negative* reward under ~400K LOC and clearly positive from 400K–2M, **could not be sourced at
all.** Don't quote the thresholds. Claude Code ships code-intelligence LSP plugins — symbol lookup with no
MCP overhead — and grep-first on a small repo remains sensible practice; it just isn't what those numbers
show.

**[Ø] Anti-patterns are folklore.** No controlled evidence that utility grab-bags, re-export chains,
or large files hurt agents.

**[Ø] The obvious experiment has never been run**: same tasks, one arm with a dependency in-tree and
one behind a boundary, counting reimplementations.

---

## 6. Reviewing agent-authored changes

**[M] Cap diff size — the one rule with real numbers.** Of **142,652** agentic PRs collected from 59,412
repositories, **107,026 were successfully processed through deterministic merge simulation**, and 29,609 of
those exhibited merge conflicts — **a 27.67% rate over the 107,026, not over the 142,652** (on the larger
denominator it would be 20.8%). Conflict rate climbs with size: ~**9.9%** at a median churn of 2 lines
versus nearly **30%** at 25 lines, stabilising around **32–33%** for 46–185 lines.
— *AgenticFlict: A Large-Scale Dataset of Merge Conflicts in AI Coding Agent Pull Requests on GitHub*,
<https://arxiv.org/abs/2604.03551>.
**Two precisions:** the axis is *median churn per size bin*, not raw lines changed; and the rate
**declines** for the very largest PRs, so "bigger is always worse" is not what the paper shows.

**[P] Review rigour degrades silently.** Across two years of data from **22,000 developers** and 4,000
teams: review time **+441.5%** at the median, incidents-per-PR **+242.7%**, and the load-bearing number —
**PRs merged with no review at all up 31.3%.** The queue never visibly blocks.
— Faros AI, *AI Engineering Report 2026*,
<https://pages.faros.ai/hubfs/AI_Engineering_Report_2026_The_Acceleration_Whiplash_Faros.pdf>.
**Framing correction:** all three deltas are a **cross-sectional contrast between low- and high-AI-adoption
teams**, not a before/after of one population. Do not present them as "AI caused X".

**[P] The risk profile shifts rather than shrinking**: trivial syntax errors **−76%** and logic bugs
"more than 60%" lower, but privilege-escalation paths **+322%** and architectural design flaws **+153%**.
Reviewers should stop hunting typos and start asking *what does this now have access to?*
— Apiiro, <https://apiiro.com/blog/4x-velocity-10x-vulnerabilities-ai-coding-assistants-are-shipping-more-risks/>
(the live URL 403s; text confirmed via Wayback). Vendor telemetry with no disclosed method — the **[P]**
tier is doing real work here.

**[M] Dependency additions are a supply-chain surface.** Hallucinated packages average **at least 5.2%
for commercial models and 21.7% for open-source ones** — those are the two *category averages*, not a
per-model range — and **43% of hallucinated names repeated in all 10 re-queries**, which hands an attacker
a stable target list. Gate any new dependency on a registry-existence check.
— *We Have a Package for You!*, USENIX Security '25, <https://arxiv.org/abs/2406.10279>

**[V] Attribution:** commit and PR attribution text is set by the `attribution` object
(`commit`, `pr`, `sessionUrl`) — <https://code.claude.com/docs/en/settings>. Setting
`attribution.commit` to an empty string suppresses commit attribution, so how the trailer is
controlled **is** documented. `includeCoAuthoredBy` no longer appears in the settings, changelog
or glossary pages: treat it as replaced, not as an undocumented mechanism. **[P]** `Glob` is the
one exception to the ignored-tools list above — it *is* consulted when passed via
`--allowedTools`.

**The defensible accountability rule:** *"the author must have read every line"* doesn't survive
contact and nobody has data that it's enforceable. **"You must be able to explain it, and you must
have proven it runs"** does — a model cannot be paged; whoever merges owns it. **The merge button
stays human.**

---

## 7. What nobody has studied

State these as gaps rather than assuming silence means safety:

- **No study of N independent agents diverging on the same task** — the central question for anyone
  running agents in parallel, and it is unanswered.
- **No evidence agents use `git log`/`git blame` for rationale.** Putting the "why" in commit
  messages is unsupported as a strategy.
- **ADRs for agents:** no tooling, no study, no adoption data. The only credible proposal reshapes an
  ADR into a path-glob + runnable check — i.e. it stops being an ADR.
- **No measurement that any semantic-search tool reduces duplicate helpers.** Every published number
  is speed, cost or accuracy — never reuse rate.
- **Nothing shipping expresses "you may read this, but do not weaken it."** Every protection
  mechanism is a *read/visibility* control; write-protection means the sandbox or nothing.

**Practice is ahead of the literature on the central question.** That makes first-hand accounts from
people already working this way worth more than another literature pass — ask them what they gate,
what they abandoned, and what bit them in production.
