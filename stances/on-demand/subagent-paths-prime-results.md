---
name: subagent-paths-prime-results
description: Descriptive output paths/labels handed to a subagent become part of its prompt and bias its result — use opaque names for A/B and eval runs
metadata:
  type: feedback
---

Anything handed to a subagent is part of its prompt, including things that feel like bookkeeping:
output directory paths, run labels, task descriptions. A descriptive name primes the result.

Caught while benchmarking a skill under eval. The eval directories were named
`eval-0-differential-oracle-hunt`, `eval-1-tracker-lead-root-cause`, `eval-2-negative-mature-repo`,
and each name was passed to the agent inside its "save outputs to ..." path. All three leaked the
tested technique into the **baseline** (no-skill) prompts — so the baseline was handed "differential",
"root cause", and "expect negatives" for free, which biased the comparison *against* the skill and
made the baselines look stronger than they were.

**Why:** the harm is invisible because the path reads as configuration, not instruction — but the
model has no such separation; it's all one prompt.

**How to apply:** for A/B comparisons, evals, or any run whose value depends on the agent not knowing
what you're looking for, use opaque identifiers (`run-a`, `iteration-2/01`) and keep the descriptive
name only in a metadata file the agent never reads — the point of a fresh context is that it's
genuinely uninformed. The companion trap (an eval baseline is never unguided) is in
[[skill-authoring-craft]]; see also [[ground-claims-with-a-cold-agent]].
