modern: a modern human control for the flourish tests. The Gutenberg control set (pre-1929) is florid period prose that
modern readers judge as bad metaphor; this set uses amateur 2010s fiction, so the model-vs-human contrast is not
confounded by period diction.

SOURCE
  WritingPrompts (Reddit r/WritingPrompts stories, collected 2018, before LLM writing), Hugging Face dataset
  euclaise/writingprompts, train split, via the datasets-server rows API. Licence: personal research use only; the
  stories belong to their authors. Do not redistribute the extracted files or .cache/ (raw pages).

COPYRIGHT RULE
  The human stories are modern and copyrighted. Human text and frames reach disk only through extract.py. Never type,
  quote or paraphrase them in a reply or in any file extract.py did not write; refer to human items by id (mh01.., mp01..).
  Claude counterparts are written from the frame only (stored in the human-*.jsonl files, read, never retyped).

NOT SHIPPED: the extracted human-*.jsonl files, .cache/ and every file the commands below write. Regenerate
them with the COMMANDS section (extract.py refetches the pages); model-*.txt are shipped.

FILES
  extract.py            fetch 30 spread-out pages of 100 stories (seeded), clean Reddit markup and tokenizer spacing,
                        select human-lines.jsonl (40 sentences, 12-40 words, simile marker, 40 stories) and
                        human-paras.jsonl (15 paragraphs, 80-120 words, 15 other stories), each with a two-sentence
                        frame. Offsets used are recorded in offsets-used.json. Raw pages cache in .cache/.
  model-lines.txt       continuations written by Claude from the frame (not by a person; first-person narrators
                        are fiction), one per line: id|key|text, key d = default, 1-5 = candidates
  model-paras.txt       the same for paragraphs
  build_claude.py       checks lengths (lines +-3 words, paragraphs +-10 against the human item), writes
                        claude-default-{lines,paras}.jsonl and line-candidates.jsonl / para-candidates.jsonl
                        (slot, cand, text, words, human_words; no frame, join by slot to human-*.jsonl)
  make_inputs.py        writes the flagcheck inputs: grade-candidates-{lines,paras}.jsonl (all candidates, label
                        model, ids <slot>-c<n>) and run-default-{lines,paras}.jsonl (human + default)
  select.py             after grading the candidates with Gemini, picks per slot the candidate with the lowest mean
                        probability of "machine" over both orders, plus a seeded random pick; writes
                        run-selected-* and run-random-* (human + pick) and selection-<set>.json

COMMANDS, IN ORDER (from this directory; F=../flagcheck.py)
  python3 -I extract.py
  python3 -I build_claude.py
  python3 -I make_inputs.py
  python3 -I $F run-default-lines.jsonl --dry-run --out /tmp/m-dry          # dry run, no key or network
  python3 -I $F grade-candidates-lines.jsonl --grader gemini --gemini-model gemini-3.1-pro-preview --out <dir>/gc-lines
  python3 -I $F grade-candidates-paras.jsonl --grader gemini --gemini-model gemini-3.1-pro-preview --out <dir>/gc-paras
  python3 -I select.py lines <dir>/gc-lines.jsonl
  python3 -I select.py paras <dir>/gc-paras.jsonl
  then flagcheck run-default-*, run-selected-*, run-random-* with gemini and openai as in ../flourish/README.txt

CAVEATS
  Candidate grading and the selected run use the same grader, so the selected run is optimistic for Gemini; read the
  openai result and the random pick as the check. Human items are amateur drafts with typos; Claude items are clean.
  Sentence splitting is heuristic and a few frames start mid-thought.
