# LLMs inside the product

Load when a feature has a model deciding or writing something at runtime: prompts, tool schemas, generated lines,
LLM-labelled corpora kept over time. (SKILL.md §9. The no-regex-over-prose rule is also in SKILL.md.)

- **A stateless call can't keep a rate.** Frequencies are seeded rolls in code, with the numbers in a
  data file; the prompt says what this one call does.
- **Never gate behaviour on words in prose.** Regex over natural language misfires (a short keyword matching
  inside a longer word, an everyday word read as a trigger; many places in one repo). Put a field where the text is authored, or a
  structured field in the model's output; word matching is only for flagging something to a human.
- **Have the model emit structured fields when it writes**, and let code re-check them later. Never
  re-ask a model whether a stored line still holds.
- **Variety comes from code** (a seeded lens per call, shuffle-bag pools), not personas or "avoid
  clichés". Pick the model per output kind by a blind batch; the biggest model came last on the shortest outputs.
- **A quoted example in a prompt or tool description becomes the template.** One example sentence in a tool
  field's description became the opener of most lines the model generated. Describe
  the shape instead, or rotate examples from code.
- **Give an agent general capabilities, not one feature per use.** When the product's model can write and run
  code, build the means (libraries in its run image, compute backends, where it may run, data it reads) and put the
  method in its editable skill. Do not build a tool for each analysis. One product's feature request was first cut as
  features, one per kind of calculation, then rewritten as general tools plus the agent's choice of what, when and
  where.
- **Tool schemas are provider-specific inputs.** A JSON-schema keyword one provider accepts can make another reject
  every call (Gemini 400s on nested `maxItems` alongside a strict response format), and a fallback route hides the
  outage. Keep bounds in the parser, and count calls per provider and outcome after any schema change.
- **LLM-labelled data kept over time** (a corpus classified into named buckets) fails with confident wrong
  numbers and no error:
  - **Labels are a function of the prompt, not just the label set.** Labels (and derived figures such as
    "coverage") compare only between runs with the same prompt, few-shot exemplars included. Store a prompt
    hash per label row (a re-run in progress holds two prompts), refuse to carry labels across any wording
    change even with byte-identical class definitions, and leave old rows NULL rather than backfilling a
    guessed provenance. After one exemplar refresh a fifth of previously matched items stopped matching
    because labels had been carried forward.
  - **A guard whose input is produced by the thing it gates can't fire the first time it matters.** A digest
    compared with a row only the labelling pass writes finds no row, so "if row and differs" is False and the
    check passes. Interrogate the population (rows carry provenance), not a side table, and write provenance
    only after the work it describes succeeds. SQL: `col <> :v` matches zero rows when every row is NULL; use
    `IS DISTINCT FROM`, and confirm which branch fires on live data before fixing.
  - **Sweep a corpus by partition, never by agent exploration**, which samples it without knowing it did.
    Chunk contiguously by date (a time-clustered problem concentrates in one chunk; striding smears it under
    every threshold), one worker per chunk, assert `items_read == corpus_size`, isolate per-chunk failures and
    exit non-zero if any failed: steady yield looks healthy while a fifth of the corpus is missing.
  - **Name classes by the symptom the reporter sees; keep cause as a separate overlay of hypotheses.** Labels
    are permanent and causes are guesses. Each cause carries one concrete check that would refute it, and the
    check must separate the mechanism from its likeliest alternative. Look in structured columns (request
    type, reporter) before the prose: many reporters with byte-identical text is a machine, not a habit.
  - **Exemplars: choose by margin, re-test after every prompt change.** Take items claimed by exactly one
    class with nothing close behind, re-classify each candidate under the prompt that will contain it, and
    after adding classes re-run the regression over ALL classes (every class shares one prompt). Validate
    exemplar ids against the real key set; the proposing model can invent one.
  - **Framing moves the headline number; a favourable sub-sample gives direction, not size.** "An empty list
    is a good answer" undercounted matches, so A/B it against neutral wording. A gain measured on items known
    to have a home was about half that corpus-wide. A monotonic climb in the running total across partial
    samples is an ordering effect.
