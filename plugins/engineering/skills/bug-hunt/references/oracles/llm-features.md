# LLM-feature oracles — behaviour that lives in a prompt

Load when the target calls a language model at runtime: generated text, a classifier, an agent with tools, a
summarizer. The defects here are behaviour decided in prose that should be decided in code, and model output trusted as
if it were typed. The oracle is the call log: run the feature many times over fixed inputs and count what comes back.
Proof is that count, from recorded calls or a seeded replay, never one sample.

## Lenses

- **A rate written as a word.** "Rarely", "sometimes", "now and then" in a prompt that runs as a fresh call each time:
  with no history in context the model does it whenever it finds a slight excuse, or never
  — each call is a new session with no count of how often it did the thing before. Count the behaviour over many calls and compare with the rate intended; the
  fix is a seeded roll or a count from stored history, with a per-call instruction.
- **Behaviour gated on word matches over natural language.** A regex or keyword list over model output or user text
  deciding what happens. *(incident)* In an app, an unrelated word counted as a time-of-day word and an ordinary task title as a
  place name; one audit found dozens of such gates (`agentic-engineering`'s `references/cases.md`). Each is a finding;
  the fix is a structured field in the model's output or where the text is authored.
- **Output trusted unvalidated.** Model JSON parsed without a schema, an id the model returns used without checking it
  exists, a number used without a range check, a refusal or truncated reply treated as an answer. Feed it the malformed
  cases (empty, cut mid-object, extra prose around the JSON, a plausible but nonexistent id).
- **Prompt injection.** Untrusted text (a web page, an email, a user's note, another tenant's data) reaches a model
  that can act — call tools, write records, send messages. The boundary oracle from `security.md`: what can a sentence
  planted in that text make the model do, and does any permission check sit between the model's decision and the
  action?
- **Sameness across outputs.** Generated lines that each read fine and collapse onto the same few shapes or names
  across a batch. Read twenty side by side (`writing-craft`'s `references/generated-lines.md`).
- **Spend.** Tokens per user action, a whole history resent each call, retries on a failing call, a result that could
  be cached by input (`performance.md`, external calls and spend).
- **Model drift.** A pinned behaviour resting on an unpinned model alias; a prompt tuned on one model now running on
  another. Check which model id each call site actually sends.

## Traps

- **One good sample proves nothing.** Output varies call to call; a finding is a rate over a fixed input set, and so
  is its fix.
- **A hand-built call measures the call you built.** Reproduce through the feature's own entry point, with its real
  system prompt and parameters, or diff your reconstruction against the call site argument by argument
  — *(incident)* a bare CLI call once measured ~3,700 tokens of preamble the real call never paid.
