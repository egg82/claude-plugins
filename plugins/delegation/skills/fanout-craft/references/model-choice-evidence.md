# Model choice — the evidence behind §1

Load before quoting any ratio, or when a model release makes you doubt the §1 rule. Detail behind the
per-agent model rule in `SKILL.md` §1. Spend figures and their re-measure commands belong in
an `instance.md` of your own in `~/.claude/local/fanout-craft/`; to re-measure model choice on your own workload, use the `model-golf` skill.

## The measured runs

77 subagents over eight task types, model varied and everything else held identical:

| model | pass rate | median tool calls | median tokens | relative cost |
|---|---|---|---|---|
| opus (Opus 5) | 100% | 2 | 212k | 3.6× |
| sonnet (Sonnet 5) | 94% | 2 | 162k | 1.1× |
| haiku (Haiku 4.5) | 81% | 4 | 290k | 1.0× |

The `opus` alias now resolves to **Opus 5.5**, re-measured on 60 subagents (five bounded tasks — a
lookup, a root cause, a computation, an 888-file aggregation, a false premise — four reps each):

| model | pass rate | median tool calls | median billed $/agent | relative cost |
|---|---|---|---|---|
| opus (Opus 5.5) | 100% | 3 | 0.34 | 2.6× |
| sonnet (Sonnet 5) | 100% | 4 | 0.35 | 2.7× |
| haiku (Haiku 4.5) | 100% | 4 | 0.13 | 1.0× |

## What they show

**Opus 5.5 costs what sonnet costs on bounded work** — fewer turns, and cache reads at half the rate —
so the 3.6× in the first table describes Opus 5, not today's `opus`. Every cell tied, so this run ranks cost only;
it says nothing new about who fails on hard aggregation. And the sonnet-to-haiku ratio moved from
1.1× to 2.7× between the two runs: it depends on turn count, so don't quote either as a constant.

**Every failure was the same shape.** Bounded work — one file, one directory, a fixture to debug, a
judgment call with the context supplied — tied at 100% across all three models. The failures landed
entirely on the one task that globbed ~900 files across *all* sessions and aggregated them: haiku
missed it 2/2, sonnet 1/2, opus 0/2. Cheap models hold on bounded single-source work and break on
multi-source aggregation.

**Cheap is not always fewer tokens.** Haiku needed 4 tool calls where opus needed 2, and each turn
re-reads the context — so haiku burned *more raw tokens* and was still ~3.6× cheaper, because the
price gap is larger than the turn gap. Judge by cost, not token count; and don't assume the inversion
(a weak model costing more in total) — it did not happen in any cell measured here.

**The ranking inverts on open-ended work.** On a scoped bug hunt, opus spent 2.77M tokens over 23 tool
calls against haiku's 0.73–1.17M over 14 — and **half of opus's extra findings came from files outside
the package it was told to examine.** That is the documented Opus 5 scope-expansion behaviour, and on a
delegated task it is pure cost. Bound the scope explicitly in the brief when you spawn opus.

**Both models found the same top bug**, with correct `file:line` in every citation. Capability showed
up as breadth of exploration, not as accuracy the cheap model lacked.

**On a subscription, cost is not the constraint — the weekly pool is, and the meters lie about it.**
Anthropic's Fable article (support article 15424964) states it plainly: *"your use
of other models draws from the same usage limits and you can never use more than your weekly limit"*,
and Fable *"draws from your plan's regular weekly usage limits and uses them faster than other Claude
models."* So the per-model bar in Settings → Usage is a **sub-cap on that model's share of the one
pool** (50% for Fable), not a separate allowance. **Do not trust the tooltip** — when the second meter
was Sonnet it read "draws from this limit only", and users documented the All-models bar rising anyway,
including screenshots of All-models at 100% locking them out while the model bar sat at 2%. Two bars on
that page cannot tell you additive from disjoint; only the doc can.

The rule in `SKILL.md` — haiku for bounded work, sonnet as default, opus when the agent must decide
what "done" means — matches Anthropic's own multi-agent guidance (Opus lead + Sonnet workers beat
single-agent Opus by 90.2%) and their published note that upgrading the model beats doubling the
token budget.

## Opus 5.5 vs Sonnet 5.5 on identical briefs

32 subagents, byte-identical briefs, all arms spawned concurrently, graded blind by Fable against
pre-registered ground truth.
Billed $ uses real cache prices — both models read cache at $0.20/MTok, so the price gap applies
only to writes and output.

| task (n per arm) | opus result | sonnet result | median requests o/s | billed $ o/s |
|---|---|---|---|---|
| T3 lookup, control (3) | 3/3 | 3/3 | 4 / 4 | 1.7× |
| T2 aggregation over ~135 vars + decoys (3) | 3/3 exact | 3/3 exact | 13 / 15 | 1.3× |
| T4 spec'd builder, oracle-checked (4) | 14/14 every run | 14/14 every run | 12 / 8 | 2.1× |
| T1 open-ended bug hunt (6) | core 5–6 of 8, median 6 | core 3–6 of 8, median 4 | 18 / 12 | 1.9× |

- **On the same brief Opus costs 1.3–2.1× Sonnet, and does not wander:** requests 1–1.5×, output per
  request equal, same tokenizer (first requests within ~40 tokens on identical prompts).
- **The quality gap appeared only on open-ended discovery** (T1): +50% of the real defects for 1.9×
  the cost. Sonnet's misses there are invisible to the delegator. A builder with an explicit spec and a
  checkable stop condition hit the ceiling on both — that is sonnet work.
- **The historical 5× per-agent gap is mostly the brief, not the model.** Over 1,100 agents in about a
  month Opus cost $4.25 vs $0.88 median (76 vs 29 requests), ~3.6× after stratifying by task; but
  on matched briefs the gap is ≤2.1×. The expensive runs were open-ended design-and-build briefs (43% of
  opus spend carried "design judgment" reasons; top runs 800+ requests) — the shape §"Builders hit the
  same wall" addresses, which no model choice fixes.
- **Not covered:** no task here ran past ~25 requests, so behaviour at 150+ requests is unmeasured.
- **Transcript trap:** a response is logged as several records and early ones carry partial
  `output_tokens`; keep the max per `message.id`, not the first. Subagent transcripts from one
  month-long window lack the final usage record for ~65% of responses, so output from that month is a floor.
