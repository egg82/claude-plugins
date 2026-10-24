---
name: stateless-calls-cant-keep-a-rate
description: When designing anything an LLM runs repeatedly with fresh context, frequency words in the prompt ("rarely", "sometimes") don't work; decide the rate in code
metadata:
  type: feedback
---

A prompt that runs as a fresh call each time cannot keep a rate. "Do this rarely", "now and then",
"sometimes" — with no history in context, the model either does the thing whenever it finds a slight
excuse or never does it. A prompt that asks a game character to "rarely" change its mind fails this way.

**Why:** each call is a new session. The model has no count of how often it did the thing before, so a
frequency word is just a weak bias, not a rate.

**How to apply:** when a feature built on repeated LLM calls needs something to happen at a rate,
decide it in code — a seeded roll, or a count read from stored history — and give the call an explicit
per-call instruction ("this time, X is allowed"). Keep the rates as data the tuning pass can adjust.
Never write "rarely/sometimes/occasionally" as an instruction in such a prompt; descriptive phrases
given as facts ("done now and then") are fine. The same holds for instructions to me across sessions:
a cadence needs a backing store (a dated log or schedule file), not a sentence. Relates to
[[verify-dont-anchor]]. History: `evidence/stateless-calls-cant-keep-a-rate.md`.
