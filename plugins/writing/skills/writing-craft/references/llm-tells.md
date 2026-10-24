# LLM tells and their fixes

An editor's flag list for reading a draft, and the method for keeping it current. It is never a gate (SKILL.md):
every item has legitimate uses. **Fix what is under the tell.** "Delve" swapped for "explore" leaves the same inflated
sentence. Ask what the line is trying to say and say that; the tell usually goes with the padding around it.

## Read for clusters, against a dated list

- **A cluster is the signal; one tell is coincidence.** Readers who use LLMs heavily named several kinds of clue
  at once when they caught model-written articles (the clue table, measured: `explanations-and-essays.md`). A count
  of shared ChatGPT conversations reached the same verdict: no single word convicts (measured, Washington Post via
  https://www.bostonglobe.com/2025/11/13/business/chatgpt-writing-style-clues/).
- **Every list is dated to the models it was measured on.** Consecutive Claude versions share 18.7 to 45.5% of
  their over-represented phrase lists, and suppressing one tell shifts others in. Claude Opus's em-dash rate fell
  from 0.66 to 0.015 per thousand words between Opus 4 and 5.5, and one model's rate moves about fivefold by task
  (measured, secondhand: Graphite's data as reported in a blog,
  https://blog.pebblous.ai/report/opus-5-5-em-dash-ai-tells-drift/en/).
  "Delve" fell to about one chat in a thousand by mid-2025, with "crucial" and "ensure" falling too (measured,
  Washington Post, above). The multiples below name their model and version; for a model not named, measure it.
- **Families differ.** GPT-4o avoids joining clauses with "and" where Llama 3 overuses it, so there is no single
  LLM grammar (measured, Reinhart et al., PNAS 2025, https://arxiv.org/abs/2410.16107), and phrase fingerprints
  cluster by model family (measured, Paech et al., Antislop, ICLR 2026, https://arxiv.org/abs/2510.15061).

## The turn and the aphoristic close

Where a reference says to end on a turn, this is what it means, and the aphoristic close is what it rules out.

- **A turn** leaves one specific, concrete thing for the reader to complete, inside this text's world: "Two of the
  riders do not come back." The reader supplies what happened to them; nothing is explained or concluded.
- **An aphoristic close** states a general maxim or lesson that would hold outside the text: "Salt keeps. So do
  grudges." Lyrical phrasing and personification ("the river remembers", "tastes of iron") travel with it.

The aphoristic close is the measured giveaway in short text. A model grader caught Claude-written short lines (Claude
Sonnet, version unrecorded) only when they carried an aphorism or a lyrical turn; plainly written Claude lines
passed as human in every register tested: game, prose, chat and UI (measured, small: 60 lines, then 160,
`evidence/flagcheck-results.txt`). So cut the maxim first, and check that what remains is a concrete fact the reader
can finish. Whether human readers catch the same thing is untested.

**The appended beat fills the slot the maxim left.** Told to drop the aphoristic close and the tidy turn, Claude
ends on one more ", and ..." clause instead: a complete sentence, then a coordinated extra beat of description. Final
", and ..." clauses in figurative lines: human pre-1929 prose 10 of 40, Claude default 14 of 40, Claude under these
rules 25 to 29 of 40, Claude continuing two real sentences by the same author 15 of 40 (measured, local, Claude
Sonnet, `evidence/flagcheck-results.txt`; first noticed by a reader as a habit of tacking on a little
more"). The likely mechanism: told to be specific, the model treats detail as something to add, so it adds it after
the sentence is done. **Fix:** build detail into the phrase that names the thing, where the thing first appears ("the
brass knocker with its tongue out"), and let the sentence end on its point, which is what the stress position is for
(`editing-pass.md`); if the extra beat matters, give it its own sentence, or cut it (judgement: good writing leads with
the detail up front). Any rule that removes a closing move needs a check for what replaced
it.

**The knowing narrator.** Two related moves read as trying to be poetic, worst when they open the line: an inanimate
thing given a mind for ironic effect ("At noon the road gave up its pretence of going anywhere") and a wry sweep that
compresses a life into an aside ("They carved his name in marble and wept over it for a season"). Tagged by a model
across the same sets, wry personification appeared in 23 of 40 Claude default lines against 11 of 40 human ones
(measured, local, tags by Gemini 3.1 Pro, `evidence/flagcheck-results.txt`). Its cousin is **the decorative simile for
an abstraction**, an idea likened to a pretty creature and then elaborated ("Time goes through the world like a heron
through a pond, slow, with its neck folded"): a reader called it a first-poem habit (judgement, one reader,
unmeasured). **Fix:** let a person act and the place stay a place; if an idea needs an image, use one the scene
already holds, and stop after it. Human lines in the same sets named a specific person in 14 of 40 lines, Claude's
default lines in 5 of 40: a named person doing something is a mark of human prose (measured, local, heuristic count).

When the writing model changes, or the kind of text has no measured list, build one. This is the method behind
every measured list cited here (practitioner, from the sources above):

1. **Collect human text of the same kind:** same register, venue, language and length. Published product strings
   for UI text, real forum posts for posts, the same genre for fiction. Antislop used Reddit creative writing and Project Gutenberg for phrases and general
   word frequencies for words; Graphite used web articles from before 2022.
2. **Generate the model's output on the same tasks,** through the prompt, settings and system prompt the real call
   uses. Several prompts with many samples each; a single prompt measures that prompt.
3. **Rank by over-representation.** For words, two- and three-word sequences, divide the model's rate per million
   by the human rate, with smoothing and a minimum count so rare items don't top the list. Count constructions the
   same way: "not X, but Y", participial tails, sentence openers.
4. **Read the top of the list by hand.** Drop topic words the task forced; keep style words and stock beats.
5. **Stamp it** with model id, task and date. Re-measure after a prompt change, since a suppressed tell makes room
   for another.

EQ-Bench's slop score is one published weighting: 60% over-used words, 25% "not X but Y" patterns, 15% over-used
trigrams, each list built against human baselines (measured, https://github.com/sam-paech/slop-score). The ranked
list points the editor at lines to read; it never passes or fails them.

## Words and phrases, strongest evidence first

1. **"Not X, but Y" and its family.** "It's not just X, it's Y", "not because X but because Y", "no X, no Y, just
   Z", the two-fragment form ("It's not bold. It's backwards."). 6.3 times the human rate in some models
   (measured, Antislop, above); in about 6% of GPT-4o chats (measured, Washington Post); the heaviest-weighted
   pattern in the slop score. **Fix:** state Y.
2. **Stock body beats and scene furniture.** Across 67 models, "flickered" made the over-used list for 98.5% and
   "voice barely a whisper" for 68.7%; Gemma-3-12B wrote "heart hammered against ribs" 1,192 times the human rate
   and "felt a profound sense" 550 times (measured, Antislop). Also breath caught, words hung in the air, dust
   motes, the door creaked open, a chill down the spine (measured, https://github.com/sam-paech/slop-forensics).
   **Fix:** one detail that belongs to this scene only.
3. **Abstract mood words standing in for detail.** GPT-4o on fiction prompts: camaraderie 162x, tapestry 155x,
   intricate 119x, underscore 107x, amidst 100x, palpable 95x, solace 95x; Llama 3 Instruct: unease 63 to 101x,
   palpable about 47x (measured, Reinhart et al.). Gemma-3-12B: unsettlingly, shimmered, stammered, each over
   2,000x (measured, Antislop). Whispered, lingered, faintly, acrid, bustling, cacophony across ten models
   (measured, slop-forensics). In expository text: crucial, pivotal, testament, vibrant (practitioner,
   https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing). **Fix:** name the particular feeling or object.
4. **Thesis-announcing phrases (Claude Opus 5.5, one prompt, indicative only).** On article-style text from a
   single fixed prompt, which by step 2 above measures that prompt more than the model: "this matters" 116x, "is
   more than a ..., it" 98x, "why ... matters" 92x, "looking ahead, the" 40x, "rather than simply" 32x, "adds
   another layer" 27x, "dependable" 23x (measured, secondhand, Graphite via the blog above). **Fix:** state the
   consequence.
5. **Stock names.** **Fix:** `naming.md`.
6. **Inflated verbs and copula avoidance.** delve, underscore, showcase, serves as, stands as, boasts, where "is",
   "has" or "shows" would do (measured in academic text, Kobak et al., https://arxiv.org/abs/2406.07016). **Fix:**
   "is", "has", "shows".
7. **Em dashes in quantity.** In 1,000-word essays, per thousand words: GPT-4.1 10.6, Claude Opus 4.6 9.1, Claude
   Sonnet 4 8.3, GPT-4o 4.1, Gemini 2.5 Pro 3.5, GPT-5.4 1.4, against a small, noisy human sample of 3.2 (measured,
   https://www.alphaxiv.org/abs/2603.27006). In over half of GPT-4o chat replies by mid-2025 (measured, Washington
   Post). The tell ordinary readers know best (practitioner, snippet, https://www.rollingstone.com/culture/culture-features/chatgpt-hypen-em-dash-ai-writing-1235314945/).
   **Fix:** comma, colon or full stop; for Claude, the prompt fix in `generated-lines.md`. The human baseline is
   essays only: literary fiction and speeches use dashes heavily, so flag them there only in quantity beside other
   tells.
8. **Emoji, bold and markdown where the venue is plain text.** **Fix:** `conversational-and-web-copy.md`.
9. **Rhetorical tics.** A question answered at once ("What did she feel? Everything and nothing."); the fragment
   reveal ("She smiled at him: not with kindness. With liberation."); emotion labelled ("A wave of grief washed over
   her"); a wisdom line closing the scene ("Some wounds, she understood now, never fully closed"); a catalogue of
   the senses; a reflective "-ing" opener (practitioner,
   https://www.sleuthsayers.org/2026/02/what-ai-fundamentally-misunderstands.html). Redundant adjective pairs and
   metaphors that add nothing ("a symphony of colors") (practitioner, community list,
   https://docs.google.com/document/d/1l3OLrnWaXUqH0ycS-0so65Hd6ayxSQqUypRtrFHMt3M/mobilebasic). **Fix:** keep the
   question or the answer; show the trace the feeling leaves; end the scene a line earlier, on the turn, before
   the maxim (above).
10. **Threes and hopeful closers.** Lists of three for the sound of completeness, a section that ends on a vague
    upbeat note (practitioner, weak: Wikipedia list; https://gptzero.me/news/the-rule-of-three/). **Fix:** as many
    items as the facts support; cut the closer. Speeches use the triad on purpose, for the ear
    (`speech-and-scripts.md`); the tell is the reflexive three in prose.
11. **Fiction-level tells.** Exposition, tidy endings, stated morals, softened dark registers (measured; the rule
    and its source are in SKILL.md, "Know who must be told"). **Fix:** cut the explanation; end on the turn (above)
    and stop. Fiction only, and by genre: romance and cozy promise the bright ending (`story-beats.md`).
12. **A style that shifts between scenes,** ornate here and plain there (practitioner, snippet,
    https://itch.io/post/15301334). **Fix:** one register; see `world-lines.md`.
13. **Notation where a sentence belonged.** Arrows and stat shorthand in a line meant to be read (judgement; the
    shipped games in `game-ui-text.md` never do it). **Fix:** `game-ui-text.md`.
14. **Vague, wordy description:** long, saying little (practitioner,
    https://sindome.org/bgbb/game-discussion/game-problems/ai-generated-writing-ic-721/). **Fix:** one concrete
    detail and a length cap.

## Grammar tells

Measured on GPT-4o and Llama 3 against human text of the same genres (Reinhart et al., above). The gaps are larger
in instruction-tuned models than base ones and do not shrink with size. Word swaps cannot touch these; the
sentence step of `editing-pass.md` can.

- **Participial tails,** "..., reflecting its lasting relevance": GPT-4o 5.3 times the human rate, instruction-tuned
  models 2 to 5 times. **Fix:** end the sentence there; give the tail its own subject and verb, or cut it.
- **Nominalisations,** "the implementation of the plan": GPT-4o 2.1 times, instruction-tuned models 1.5 to 2.
  **Fix:** characters as subjects, actions as verbs: "they carried out the plan".
- **Subject "that" clauses** ("That the road had closed surprised no one"), 2.6 times, and **paired phrases** ("X
  and Y"), 1.9 times. **Fix:** put the actor first; drop the half of the pair that repeats the other.
- **Too few agentless passives:** GPT-4o uses about half the human rate. People write "the road was closed" when
  who closed it doesn't matter. Don't convert every passive; an active sentence with an invented agent is its own
  tell.
- **Past perfect in descriptive flourish** ("had worn", "had been", "and had gone"): about twice the human rate in
  Claude Sonnet's figurative lines, 17 to 20 of 40 lines against 9 of 40 in pre-1929 human prose (measured, local,
  one set, `evidence/flagcheck-results.txt`; first noticed by a reader). It reaches into backstory where the
  human lines stay in the scene's own time. **Fix:** keep the moment in simple past or present; give history its own
  scene, or one concrete trace of it.

## Across a batch

Some tells exist only at volume: every line opening the same way, one sentence shape twenty times, a fact's wording
reused verbatim, a pet object in every third line. Read lines side by side, or count repeated three- and four-word
sequences across them; the count points a reader at lines and is never a gate. `generated-lines.md` covers where
repetition in generated text comes from.

## Weak, so don't flag on these alone

A tricolon count (about twice the human rate per document) seen only in a search summary; "something shifted".
