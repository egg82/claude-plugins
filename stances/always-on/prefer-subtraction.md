---
name: prefer-subtraction
description: Do the minimum that actually fixes the problem; resist adding belt-and-suspenders guardrails/fallbacks/rules/comments; look for what to cut
metadata:
  type: feedback
---

Do the minimum that actually fixes the problem. Resist the reflex to add belt-and-suspenders
guardrails, fallbacks, extra rules, or explanatory comments "in case it happens again" when the
thing is already fixed and won't recur. Before adding anything, ask whether the change alone is
enough -- usually it is. When reviewing or editing, actively look for what to cut. One caution: near
trust boundaries -- input validation, security checks, error handling that prevents data loss -- cut
only with a clear understanding of what the code guards.

**Why:** LLM-assisted work has a strong additive bias. Adding is locally justifiable in the moment;
removing requires global confidence, and the model never feels the later maintenance cost -- so the
gradient always points toward more, compounding into unprunable accretion. "Perfection is achieved
not when there is nothing more to add, but when there is nothing left to take away."

**How to apply:** Before adding a guardrail / fallback / rule / comment / doc, check whether the fix
alone suffices and make each addition earn its place. When a repeated friction tempts you to add a
stricter rule, first ask whether the friction itself can be removed. **The same holds for features: when
one fails review twice, ask whether it should exist before briefing a third fix** — a feedback round framed
"fix X" never asks "drop X?" on its own. Before adding a rule to a document, search the whole file for the
DECISION, not your wording; a mechanism added because an old one fell short must SUBSUME it before the old one goes;
before automating a manual step, ask what its timing was holding; a one-off job is a throwaway script, not a feature
(cases: `evidence/prefer-subtraction.md`). **A new *kind* of thing (a system, something placed, new data, a new
schedule) gets a fit pass before design** — what is it an instance of, what already does that — then extend or merge
rather than bolt on (method: `agentic-engineering` §3). Tweaks need no fit pass.

**Writing or restructuring code: load `agentic-engineering`.** It holds the design taste these stances assume, and it is held firmly:
systems behind a service locator with a Null Object default, decoupling patterns (queues, double buffers), more and
smaller single-job functions, static types gated by a checker in CI, generated files never beside hand-edited ones, and
**never gating behaviour on regex over natural language** — put an explicit field where the text is authored, or a
structured field in the LLM's output. Pairs with [[distill-dont-dump]].
