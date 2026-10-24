# Humour

How to write a joke, a funny register or a running gag that a reader laughs at, and how to tell whether it worked.
The measured evidence is mostly on one-liners (captions, roasts, headlines); the craft rules come from working
writers and comedians. Where a part is thin the text says so. Dialogue craft is in `dialogue.md`.

## Never "a joke"

- **Over 90% of 1,008 ChatGPT jokes were the same 25,** memorised rather than made (measured, GPT-3.5 era, may not
  hold now, snippet, https://arxiv.org/abs/2306.04563). Give the situation, the target and the form instead.
- **No humour in errors and failures** (`ui-text.md`). A forced joke there is worse than none.

## Registers

The registers a writer asks for are below, then the wider kinds. Both are examples of a larger space, not a closed
list: a comic voice is usually a mix, and a new kind is described the same way (mechanism, example, rule, how a
model fails it). Rules marked "unverified" come from the writer's own knowledge of the classics and have no
source behind them.

**Dry / deadpan.** The telling is calmer than the event, and the joke is never flagged. "The ships hung in the sky
in much the same way that bricks don't" (Douglas Adams). Cleese's memorial sketch for Chapman says terrible things
without smiling (opinion, study guide, snippet, https://www.shmoop.com/hitchhikers-guide-to-the-galaxy/tone.html).
*Rule:* the narrator's face stays still; no exclamation, no underlining. *Model failure:* explains the joke or adds
an exclamation mark (comedians' complaint of no subtext: practitioner,
https://arxiv.org/abs/2405.20956).

**Witty / one-liner.** A compact line that holds two readings at once. In the New Yorker caption data, the human
winners were "better phrased and more concise" and supported several readings; model captions were verbose, less
varied and sometimes ignored the picture (measured, Zhang et al., NeurIPS 2024, https://arxiv.org/html/2406.10522v2).
*Rule:* cut to the fewest words and make the joke about what is in the scene. *Model failure:* length, and
word-play by modification, which readers rate low.

**Wordplay / puns.** Works only when both senses fit the context and the sounds truly match. Wodehouse: "If not
actually disgruntled, he was far from being gruntled" (unverified). Models label anything pun-shaped a pun by
surface pattern: GPT-4o scored 0.33 on non-puns made by swapping a homophone (measured, Zangari et al., EMNLP 2025,
https://arxiv.org/html/2509.12158v1). *Rule:* check both readings by hand; do not trust "sounds like a pun".
*Model failure:* a pun whose second sense does not fit, or a template pun with no tie to the scene. The one LLM
joke an MIT Technology Review reporter rated better was wordplay tied to the show's own topic (practitioner,
https://www.technologyreview.com/2024/06/17/1093740/what-happened-when-20-comedians-got-ai-to-write-their-routines/).

**Laugh-out-loud / escalation.** Each beat follows the same logic, bigger, and the logic is obeyed to the end
(unverified). Pattern-and-break: two beats set the pattern and the third deflates it ("a brain tumor, heart disease,
and a really ugly tie") (practitioner, John Vorhaus, https://nofilmschool.com/john-vorhaus-comedy-writing-tools).
*Rule:* one logic per joke; the funny word last, because the eye has to travel to it (practitioner, Pratchett's
footnotes as a "delayed drop", https://www.lspace.org/about-terry/interviews/book-case.html). *Model failure:*
the third list item continues the pattern, so nothing deflates.

**Dark / gallows.** A violation that is benign at the same moment. Severe violations are funnier at a distance in
time, place or person; mild mishaps are funnier close up (measured, McGraw and Warren, snippet,
https://leeds-faculty.colorado.edu/mcgrawp/pdf/mcgraw.warren.williams.leonard.2012.pdf; a 2023 replication
supported the benign half, not the distance effect). A small comic image placed after a dark beat reframes the
danger as smaller: Starbuck seeing the whale as a goldfish, the gravediggers in Hamlet, the porter in Macbeth, the
boyfriend's "I'm going to marry you till you puke" after a baby's death in Lorrie Moore's "Terrific Mother"
(practitioner, https://enginesofnarrative.substack.com/p/gallows-humor). *Rule:* keep it small, put it after the
dark beat, and let the one who is suffering make it, so it helps them carry on and does not dismiss the loss.
*Model failure:* refuses the dark beat, or stacks a joke on top as if to cancel it. Comedians report that safety
tuning strips the edge and leaves "cruise ship" material (practitioner, Mirowski et al.).

**Irony.** The words say one thing and the situation another, with the reader holding both. "It is a truth
universally acknowledged..." (Austen, unverified). *Rule:* the speaker must not know, or must pretend not to.
*Model failure:* flat sarcasm and understatement (opinion, https://www.wayline.io/blog/ai-dialogue-trap-authenticity-in-storytelling).

**Absurdism.** A strange premise played straight, with its own rules kept (opinion, reviews, on Spaceplan's
potato-powered ship, https://store.steampowered.com/app/616110; no craft account found). In the Oogiri response
game models score on Novelty and humans reward Empathy: the reader must recognise something true in the strange
idea (measured, AAAI-26, https://ojs.aaai.org/index.php/AAAI/article/view/40567). *Model failure:* random
strangeness with nothing true under it.

**Callbacks and running gags.** A callback pays off an earlier detail in a changed context; without the change it is
a repeat (unverified). Ron Gilbert gives no rule for how often (practitioner,
https://killscreen.com/laughing-stock-ron-gilbert). *Model failure:* repeats the earlier line verbatim. Keeping a
running joke fresh has no measured evidence; the one tested lever is below.

**Bathos.** Build a high register, then drop to a mundane detail (unverified). *Rule:* the drop is the last word.
*Model failure:* drops too early, or explains the drop.

**Observational.** The funny thing is a small human frailty named exactly. ChatGPT's top Onion-style headline in
Gorenz and Schwarz was "Man Achieves Personal Best in Avoiding Eye Contact With Neighbors During Awkward Elevator
Ride". The joke lives in the gap between the thing shown and a real-world norm, so name the norm (measured, Hessel
et al., indirect-reference finding, press page, https://news.cornell.edu/node/326829).

**Character humour.** The target is the character's self-image. Gilbert: humour grows from building a character,
not from non-sequiturs, and a game joke should also reveal character or help with the puzzle. Portal paired a slow
GLaDOS with a frantic Wheatley, the player silent as straight man (practitioner,
https://www.shacknews.com/article/51474/gdc-08-portal-creators-on). Comic opposites: give two characters opposing
rules and lock them together; the inappropriate response (a car-chase passenger worried about fuel economy) works
where the right range is narrow (practitioner, Vorhaus). *Model failure:* every character jokes in the same voice
(`dialogue.md`).

**Anti-jokes.** Set up a joke shape, then deliver a flat truth (unverified). *Rule:* the shape must be clear enough
that the flatness reads as a choice.

## What the measurements say

- **Models win on tight, situational tasks.** With GPT-3.5, 20 outputs per prompt, blind raters preferred its roast
  replies to an awkward scenario 73% of the time (beating about 87% of laypeople), acronyms 58%, and Onion-style
  headlines tied the real Onion's. Study 2, a professional-grade comparison, was a tie. Prompts and examples did
  heavy lifting, and three random responses were shown (measured, Gorenz and Schwarz, PLOS ONE 2024,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11221738/). It does not show models write good jokes unprompted.
- **The crowd flatters the model; an expert does not.** Claude 3 Opus beat the contest's top-10 captions in 35.4% of
  crowd votes, but 1.6% with an ex-New Yorker cartoon editor. RLHF cut the win rate against the median caption from
  24.7% to 5.0%, and best-of-N cut diversity (measured, Zhang et al.).
- **Models cannot see why a joke works.** The best model matched caption to cartoon 62% of the time against 94% for
  humans, and human explanations were preferred about 2:1, so it cannot tell its own hit from its own miss
  (measured, Hessel et al.). Larger Qwen3 models were ranked funnier by automated judges; human raters found no
  difference (measured, snippet, https://aclanthology.org/2026.chum-1.7/).
- **What predicts funny in Oogiri responses:** perspective shift, ambiguity, and incongruity that resolves; shorter
  responses and re-use of the prompt's own words. Surprisal and distance from the prompt barely mattered (measured,
  correlational, Japanese, aggregator summary of
  https://www.emergentmind.com/papers/2512.21494). Models drift the other way, toward length and novel words
  (judgement, from the caption and Oogiri results above).
- **Preferred jokes skew to incongruity and absurdity over wordplay,** with low rater agreement (measured, weak,
  snippet; do not quote the numbers).

## How to get a hit

- **Generate many, keep few.** The Gorenz hits came from about 20 candidates per prompt and a selection step. Draft
  twenty, read them side by side, keep the one or two that survive.
- **Use a tight form and a concrete situation:** a fixed headline template, a roast against a stated awkward
  scenario, a setup with a named target. The winning tasks were constrained, never "be funny" (measured, USC press
  piece, https://today.usc.edu/ai-jokes-chatgpt-humor-study/).
- **Target a small human frailty,** put the reveal word last, and cut every word that is not setup or reveal.
- **Take the setup from the model and write the punchline yourself.** Twenty comedians used a model for structure,
  a rough first draft ("a vomit draft") and setups, and supplied the punchline, the perspective and the specific
  detail. "The only thing that is funny is the joke I put into the prompting"; "if you make something that fits
  everybody, it probably will end up being nobody's favorite" (practitioner, Mirowski et al.). A joke tied to the
  show's own occasion beat a free-floating one.
- **When one lands, keep what made it work** (its form, its target, its register) and use that as the exemplar for
  the next batch (`generated-lines.md`). The comedians found no way to predict a hit before trying it, so the
  evidence for "why it landed" is thin.
- **Judge with the sharpest reader available.** The sharpest-reader method of `judging.md` applies: a crowd or a
  model grader overrates model jokes, an editor with a trained ear does not. Funny is decided by human readers.

## How much, and how fresh

- **Humour does a job.** Portal's lines earned their place by hinting and by attaching players to the companion cube,
  and were shaped by playtests; "funny dialog is funny to the writer once, maybe" (practitioner, shacknews, above).
  Gilbert asks the same: a joke should also reveal character or serve the puzzle.
- **In a serious or dark work, keep the jokes small and placed after the heavy beat,** by the people it hurts
  (gallows above). Nothing found measures how much is too much, or how often a serious work can afford a joke.
- **Keeping a running joke fresh:** nothing found says how many hearings a gag survives. Treat the callback rule
  (changed context) as an untested starting point, and see `generated-lines.md` for repeats in generated text.
