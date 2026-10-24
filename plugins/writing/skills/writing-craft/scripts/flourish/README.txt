flourish: can graders tell flourished model prose from human flourish?

The flagcheck result (../../evidence/flagcheck-results.txt) found graders catch Claude lines only when they carry an
aphorism or lyrical turn. This set asks the harder question: when the model writes figurative, atmospheric,
aphoristic prose on purpose, with and without the skill, does a grader still separate it from human flourish?

NOT SHIPPED: none of the JSONL data files named below (the raw corpora were removed; no script regenerates them).
Rebuild each from its description here. round3/select.py is the only code in this directory, and
../flagcheck.py grades whatever you build.

FILES (all JSONL; fields id, text, label, register "flourish", kind, source)
  human-test.jsonl      40 human lines, Project Gutenberg only, each verified as a verbatim substring of the PG text
                        (whitespace collapsed; a line starting mid-sentence has its first letter capitalised; "MARLEY"
                        is capitalised in the PG file). 32 obscure, 8 famous (field "fame"). Source field names the
                        PG ebook and work. Authors: Dunsany, Machen, Hodgson, Blackwood, Chambers, C. A. Smith
                        (Ebony and Crystal, 1922), Shiel, Bramah, Grahame, Stevenson, plus Poe, Dickens, Melville.
                        Kinds: opening 5, closing 5, object 7, place 8, dread 7, character 6, aphorism 2.
  exemplars.jsonl       15 further human lines, disjoint from the test set, for few-shot use and as the model for
                        the skill condition.
  claude-default.jsonl  40 lines written without the skill, as Claude naturally writes flourish. Modern English.
  claude-skill.jsonl    40 lines, same slots, written under writing-craft: no llm-tells.md moves, exemplars as the
                        model for specificity and oddness. Modern English.
  claude-period.jsonl   40 lines, same slots, skill condition, in Victorian/Edwardian diction. Each is a diction
                        rewrite of the matching claude-skill line (same image), so skill vs period isolates diction.
  run-default.jsonl, run-skill.jsonl, run-period.jsonl
                        human-test + one model set (80 lines each), keeping only id, text, label, register. Join to
                        the full files by id for kind, fame and source. Model "slot" field gives the human line
                        (h01..h40) whose kind and subject area the model line matches (same subject area, not a
                        paraphrase).

MEDIAN LENGTH (words): human 25.0; claude-default 27.0; claude-skill 34.5; claude-period 35.5.

RUN
  Dry run (fake em-dash grader, no key, no network):
    python3 -I ../flagcheck.py run-default.jsonl --dry-run --out /tmp/fl-dry
  Live, one run file at a time (default, skill, period):
    python3 -I ../flagcheck.py <file> --grader gemini --gemini-model gemini-3.1-pro-preview --out <dir>
    python3 -I ../flagcheck.py <file> --grader openai --openai-model gpt-5.2 --out <dir>
  Add --flatten to rerun with case and final punctuation removed.

READING THE RESULT
  TPR = model lines called machine; FPR = human lines called machine; TPR-FPR near 0 means no separation, as in
  controls-v2. Compare the three conditions on the same human half: the human FPR should barely move between runs,
  so a change in TPR-FPR comes from the model half. Expected order if the skill works: default > skill >= period.
  Break down by kind and by fame by joining the per-line records (<out>.jsonl) to human-test.jsonl and the claude-*
  files on id. Famous lines (h01-h08) are the recognition check: if their FPR is far below the obscure lines',
  the grader is recognising them rather than judging them. Per-line phrases show which move gave a line away.

CONFOUNDS
  - Period diction. The human set is 1850-1925 prose ("hath", "roundabout", "effulgence", semicolon chains). A
    grader can win on period alone with modern-English model lines. run-period.jsonl removes that, run-skill.jsonl
    does not; read the gap between them as the cost of modern diction.
  - Length. The skill and period lines are about 10 words longer at the median than the human lines (34.5 and 35.5
    against 25.0). Check whether verdicts track length before crediting anything to style.
  - Pairing. Period lines are rewrites of the skill lines, so they are not independent samples of the skill condition.
  - Prompt wording. flagcheck.py's grader prompt says the lines are from "video games"; these are fiction excerpts.
    The prompt was left unchanged to keep results comparable with earlier runs.
  - Authorship. The model lines were written by the model whose skill is being tested, with the skill and exemplars in
    view; the skill-condition lines were chosen for the specific moves the skill names, so a pass tests the list, not
    all of Claude's flourish. The exemplars are from the same authors as the test set but different lines.
  - Memorisation. The famous lines are in every model's training data; most obscure ones probably are too, since PG
    is a standard corpus. Not tested; the famous-vs-obscure FPR gap is the available check.
  - Fixed size. 40 lines per half; with both orders pooled one verdict moves a rate by 1.25 points and one line by 2.5. Treat differences
    under about 0.15 as noise.

ROUND 2 (round2/): the same 40 human lines, four new model strategies, each line within 3 words of its paired human
line (fields words and human_words record both). Round 1 lines ran ~10 words long and were caught on contrived
specifics; round 2 asks whether length-matching and a quirk budget remove the tell.
  completion.jsonl      per slot, two consecutive sentences from a PG passage by the paired line's author (not in
                        human-test or exemplars; field frame, verbatim) and the sentence that follows, written in that
                        voice. Only text is graded.
  budget.jsonl          the skill with a quirk budget: at most one unusual detail per line and only if it does work; a
                        large plain image or a direct statement preferred; no personified abstraction, aphoristic
                        close, sensory-adjective stack or tidy turn. Modern English.
  edited.jsonl          each claude-default line revised by references/editing-pass.md (fields from, original).
  period-budget.jsonl   as budget, in the paired human line's period diction.
  run-<strategy>.jsonl  human-test + that strategy (id, text, label, register).

PARAGRAPHS (paragraphs/): for the Pangram and Sapling detectors, which need more text than a line.
  human.jsonl           15 paragraphs of 85-118 words from PG fiction before 1929, verbatim (whitespace collapsed),
                        mostly obscure authors (Dunsany, Hodgson, Morris, Blackwood, Machen, Shiel, C. A. Smith); no
                        overlap with the line sets or round-2 frames. Field source is the ebook.
  default.jsonl         15 written without the skill, matched to a human paragraph's subject kind and length (within 10
                        words; field slot names the human paragraph, not a paraphrase of it).
  budget.jsonl          15 under the quirk-budget rules, matched the same way.
  run-default.jsonl, run-budget.jsonl   human + that condition.

RUN ROUND 2 (live; spends money on the paid graders)
  Lines, gemini (as round 1; --flatten for the surface-form check):
    for s in completion budget edited period-budget; do
      python3 -I ../flagcheck.py round2/run-$s.jsonl --grader gemini --gemini-model gemini-3.1-pro-preview --out <dir>/r2-$s
    done
  Paragraphs, pangram (one text per request, forward order only; prints the cost estimate and refuses without --yes):
    python3 -I ../flagcheck.py paragraphs/run-default.jsonl --grader pangram --yes --out <dir>/pg-default
    python3 -I ../flagcheck.py paragraphs/run-budget.jsonl  --grader pangram --yes --out <dir>/pg-budget
  Sapling takes the same shape (--grader sapling --yes); either detector can also score the line runs, but is
  built for longer text. Dry run of any of these: add --dry-run (gemini/openai become the fake grader; pangram and sapling
  run through a stand-in transport with the real request shapes; no key, no network, --yes not needed).
  The pangram response shape (task_id; stage; prediction_short; fraction_ai) and the sapling one (score) follow the
  vendors' documented fields as given to the author; not yet seen against the live APIs. A line whose request fails
  or times out counts as no_answer, not as human.
  Cost: pangram is estimated at $0.0005 per word; each paragraph run is about 3,060 words (about $1.53). Sapling's
  price is not set in the script.

ROUND 3 (round3/): generate many, keep few. Five candidates per slot; a grader picks the most human-sounding one, a
seeded draw picks another, and the two sets are compared against the same human half. If selection helps, the
selected set beats the random one, and for paragraphs does so on a detector (Pangram) that did not do the selecting.
  line-candidates.jsonl   200 = 40 slots x 5. Frame reused from round2/completion.jsonl for the slot (fields slot,
                          cand, frame, text, words, human_words; id <slot>-c<n>). Each within 3 words of the human line.
  para-candidates.jsonl   75 = 15 slots x 5. Frame is the first two sentences of a Gutenberg passage by the paired
                          paragraph's author, in no other set (verbatim; frame_ebook names the PG ebook). text is
                          the continuation only, 80-120 words and within 10 of the human paragraph; only text is graded.
  grade-candidates-<lines|paras>.jsonl   the candidates as flagcheck input (label model, ids <slot>-c<n>).
  select.py               maps graded ids back to candidates; writes selected-<kind>.jsonl and random-<kind>.jsonl
                          (label model, ids c<nn> for lines, cp<nn> for paragraphs) and the run files
                          run-selected-<kind>.jsonl and run-random-<kind>.jsonl (human set + that set). Score = mean
                          machine probability over both orders (confidence if the verdict is machine, else
                          1 - confidence); lowest wins; a candidate with no usable verdict cannot win.
ORDER OF OPERATIONS (cwd = this directory; F=../flagcheck.py; <dir> = any scratch dir)
  1. Grade every candidate with Gemini, both orders (candidates only, so no human lines in the batches):
       python3 -I $F round3/grade-candidates-lines.jsonl --grader gemini --gemini-model gemini-3.1-pro-preview --out <dir>/r3-g-lines
       python3 -I $F round3/grade-candidates-paras.jsonl --grader gemini --gemini-model gemini-3.1-pro-preview --out <dir>/r3-g-paras
  2. Select:
       python3 -I round3/select.py lines --graded <dir>/r3-g-lines.jsonl --grader gemini
       python3 -I round3/select.py paras --graded <dir>/r3-g-paras.jsonl --grader gemini
  3. Paragraphs through Pangram (the estimate prints first; --yes accepts it):
       python3 -I $F round3/run-selected-paras.jsonl --grader pangram --yes --out <dir>/pg-selected
       python3 -I $F round3/run-random-paras.jsonl   --grader pangram --yes --out <dir>/pg-random
  4. Lines go to a human quiz (scripts/quiz_score.py): round3/run-selected-lines.jsonl against run-random-lines.jsonl.
     Optionally also both through Gemini; the selected set should win there, since Gemini chose it.
Dry run without keys: flagcheck.py <grade file> --dry-run, then select.py on its output. Every candidate ties under
the fake grader, so selection is a seeded pick: plumbing only.
Cost: Pangram at flagcheck.py's current estimate is about $2.30 per paragraph run (30 texts, human half included),
about $4.60 for both. CONFOUND: Gemini both selects and grades the lines, so a Gemini gain on lines is partly
selection on the test; the Pangram paragraph runs and the human quiz do not share it.
