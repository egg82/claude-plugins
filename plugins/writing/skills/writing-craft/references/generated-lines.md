# Lines an LLM generates

Rules for text a model writes at runtime (one stateless call per line) and for many lines drafted by agents in bulk.
The common thread: variety and correctness come from the code around the model, and quality is checked over
batches; the prompt and the choice of model come after.

## Runtime calls

1. **Variety comes from the code.** Send one or two facts per call and a seeded lens per call, never the whole
   state; a call handed many facts tends to recite them all in order, in one sentence shape (judgement). A lens is
   an angle on the same facts: for a minor character it might be one thing they own, one quoted line, or what a
   bystander noticed; for product descriptions, the buyer's use, one material detail, a customer's phrase.
   Prompt style and personas did not reduce sameness (measured, Anderson, Shah and Kreminski, C&C'24,
   https://mkremins.github.io/publications/Homogenization_C&C2024.pdf); many rotated seeds did, and mixing model
   vendors adds almost none (measured, https://arxiv.org/abs/2501.19361).
2. **Make facts coherent before sending.** The model uses contradictory facts faithfully, so independently sampled
   ones that clash (a child's age and a spouse) reach the line unchanged (judgement).
3. **Pass facts as attributes, never finished phrases.** A fact's wording leaks into the prose, and key names are
   prose too: a key like `found_at` can turn into "found at" on every line (judgement). Send `age: 12` and let the
   model choose the words.
4. **Pools are big and drawn without repeats.** A shuffle bag per pool, plus exclusion of recently used items read
   from stored history, sized so a month of use rarely repeats one. Ten items across thirty calls must repeat; that
   is arithmetic, and no prompt fixes it.
5. **No frequency words in the prompt.** "Rarely", "sometimes", "now and then" mean nothing to a stateless call: it
   has no count of what it did before, so it does the thing whenever it finds an excuse, or never. Decide the rate in
   code (a seeded roll, or a count from stored history) and tell the call "this time, X is allowed". Keep the rates
   as data. A descriptive phrase stated as a fact ("done now and then") is fine (judgement).
6. **Match the ending to the kind of line.** Lore, vignettes, horror and humour end on a concrete turn, never an
   aphoristic close (`llm-tells.md`, the turn); an event log may ask for a flat record; a hint, status message or
   any informational line states its point and stops.
7. **Each kind of line gets the cheapest model that does it adequately,** chosen by a blind batch per kind and model
   rated by a human, never by assumption. The largest model need not be the ceiling for short lines: in one blind
   batch its lines read as more flowery and on the nose than a mid-size model's (judgement, one reader).
8. **Fewer constraints.** Reliability falls past about five simultaneous constraints (snippet, single-author
   preprint). "Avoid clichés" barely helps (SKILL.md). Exemplars do more than rules (below).

## Prompt levers, and what doesn't work

- **Human exemplars of the same kind are the strongest prompt-side lever measured.** Matching a target style, as
  scored by an authorship verifier: zero-shot 3 to 7%, one example 68 to 95%, a few examples 91 to 100% (measured,
  open models from Llama, Qwen and Mixtral, essays, https://arxiv.org/abs/2509.24930). Two examples did about as
  well as ten, and the author's own text gave the biggest gain in human-likeness (measured, GPT-4o, Gemini, Llama
  and others, https://arxiv.org/abs/2509.14543). Detectors still flagged most of that output, and informal writing
  stayed weakest, so exemplars help without finishing the job.
- **Frame the call as continuing a document,** with the exemplars as the document so far: text completion scored
  97 to 100% on the same verifier (measured, 2509.24930 above). Locally the same held for figurative lines: Claude
  continuing two real sentences by the same author was caught by a grader 68% of the time, against 78 to 90% for every
  rule-based strategy (avoid these moves, one quirk at most, edit the draft), and it was the only strategy that did
  not swap the banned closing move for an appended ", and ..." beat (measured, local, Claude Sonnet, 40 lines per
  strategy, `evidence/flagcheck-results.txt`). Rules about which moves to avoid move the tell; examples move the voice.
- **For Claude, ask for flowing prose with no markdown.** Its em dashes tracked markdown habits: Opus 4.6 fell from
  9.1 to 0.19 per thousand words when told to write plain prose without markdown, and GPT-4.1 barely moved
  (measured, https://www.alphaxiv.org/abs/2603.27006). Measured on Opus 4.6 only, and later Opus versions write far
  fewer dashes (`llm-tells.md`); check the current model.
- **Doesn't help:** personas and prompt style (measured, Anderson, Shah and Kreminski, above); temperature and other
  parameter changes, which left the gap in new ideas between human and GPT-4 essays (measured, snippet,
  https://arxiv.org/pdf/2604.01504); min-p sampling, whose claimed gains did not survive reanalysis (measured,
  snippet, https://arxiv.org/abs/2506.13681); humanizer tools, whose evidence is about evading detectors, never
  about what a reader sees (measured, snippet, https://arxiv.org/abs/2501.03437). No study was found that measures
  a draft-critique-rewrite pipeline or a negative-instruction list against a slop count.
- **With open weights only:** the antislop sampler backtracks when a listed phrase appears and suppresses thousands
  of patterns where plain token bans break down at about 2,000; its fine-tune (FTPO) cut slop about 90% while
  holding benchmark and creative-writing scores, and DPO did worse on both (measured, abstract, Paech et al.,
  https://arxiv.org/abs/2510.15061; https://github.com/sam-paech/antislop-sampler). Base models don't show the
  tics: their text reads as human to detectors where instruction-tuned text doesn't (measured, snippet,
  https://arxiv.org/pdf/2605.19516), and co-writing with a base model didn't narrow people's essays (measured,
  https://arxiv.org/abs/2309.05196). None of this runs on a hosted API without logits.

## Which model writes

Rule 7 decides, per kind of line. A published leaderboard is at most a shortlist, and goes stale with each release;
autograded ones agree poorly with expert writers (measured, vendor-run, Surge's Hemingway-bench, which found the
EQ-Bench autograder agreeing with its experts as little as 43% of the time,
https://surgehq.ai/blog/hemingway-bench-ai-writing-leaderboard).

## Checking output

- **Check a batch, never a line.** Compare new output against recent output for repeated shapes, openings and
  three- or four-word sequences, and feed what repeats back into the pools and the lens list. The count points a
  reader at lines to look at; it is never a gate.
- **No per-line critic at runtime.** It costs two to three times the call and makes output more alike (below).
  Quality is checked offline over batches.

## Many lines drafted by agents

For a story bible, a lore set or a batch of curated lines, where the cost of a team is affordable:

- **No compute-matched study shows a multi-agent team beating one model for fiction.** Every multi-agent story paper
  beats an unmatched single call; on reasoning tasks, compute-matched single agents tie or win (measured, abstract
  only, Tran and Kiela, https://arxiv.org/abs/2604.02460).
- **Debate makes writing more alike; fixed lenses fix that.** Plain debate raised quality and cut diversity below a
  single agent; giving each agent a fixed lens and showing it only its most dissimilar peers raised lexical
  diversity at equal quality (measured, model judge, not fiction, https://arxiv.org/html/2609.00683). A team's
  stories can repeat trigrams more than a single call's (measured, Agents' Room, https://arxiv.org/html/2410.02603).
- **Draft alone, critique blind, revise your own** beat debate by a small margin (measured, model judge,
  https://arxiv.org/html/2601.08003v1).
- **Plan first,** with a detailed outline (measured, `story-beats.md`).
- **So:** one lead owns canon in a keyed file (one fact per line, with id, source and status) and is the only writer
  to it; several proposers work alone, each through a lens chosen by code, never seeing each other's drafts; blind
  critics answer narrow yes/no questions with a quoted span (ends on a concrete turn or a maxim, on the nose, repeats a shape
  already used); each writer revises only its own draft; a continuity check reads proposals against the canon facts
  they touch. Humans rate blind batches (`judging.md`). Expect several times the cost of a single pass (unmeasured).
