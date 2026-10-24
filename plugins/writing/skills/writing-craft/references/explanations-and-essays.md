# Explanations and essays

Essays, blog posts, explainers, and how-tos and tutorials published as articles: prose whose job is to tell a
reader something they didn't know. A project's own docs and README go to `doc-cold-read`. Words, sentences and rhythm follow `editing-pass.md`; this file covers what the piece says, who it is for,
and how it is ordered.

## What readers catch

Readers who use LLMs heavily catch model-written articles almost every time (detection figures and scope:
`judging.md`). The clues they gave, by share of their written explanations (measured, 300 articles, Russell,
Karpinska and Iyyer, ACL 2025, https://arxiv.org/abs/2501.15654):

| Clue | Share | What they meant |
|---|---|---|
| Vocabulary | 53% | "crucial", "testament", the stock words in `llm-tells.md` |
| Sentence structure | 36% | "not only ... but also", lists of exactly three |
| Grammar and punctuation | 25% | too polished; human articles carry small errors |
| Originality | 24% | safe, predictable, no surprise or humour |
| Quotes | 22% | formal, in the narrator's own register, parked at paragraph ends |
| Clarity | 20% | over-explains, adds irrelevant detail |

Casual contractions and "just" or "actually" read as human to the same readers. The articles were 300 to 1,000
words from GPT-4o, Claude 3.5 Sonnet and o1-Pro; shorter text was not tested.

The table is the checklist for this kind of text: the words step fixes the first row, the sentence step the second,
and the rest are fixed at the substance stage below, where a model's draft is weakest.

## Say something the reader didn't have

- **Tell the reader something new and useful,** then cut whatever doesn't serve it (practitioner, Paul Graham,
  https://paulgraham.com/writing44.html). A model draft tends to arrive looking finished, with nothing cut and
  nothing surprising (judgement). Treat it as notes.
- **The point comes from a person.** What the piece claims, the example that proves it and the thing that went
  wrong come from someone who did the work (`editing-pass.md`, substance).
- **Keep the topic narrow.** One specific question answered well beats a survey of the field; specificity respects
  the reader's time (practitioner, Julia Evans, https://jvns.ca/blog/2019/09/13/a-year-explaining-computer-things/).
- **Write from a trial.** Good explainers start from a basic question the writer actually had ("what does a shell
  even do?"), say what they tried and broke, and say what they still don't know (practitioner, Evans, above). A
  model explainer tends to survey the topic with no first person, no failed attempt and no admitted gap
  (judgement). Only the person can supply those, and they must be true.
- **Park digressions.** Tell a real surprise from a tangent; tangents go in a footnote or out (practitioner,
  Graham, above).

## Name the reader, then explain to them

- **The human failure is the curse of knowledge:** the writer forgets what the reader doesn't know, uses jargon
  undefined and skips steps that feel obvious (practitioner, Pinker, https://www.psychologicalscience.org/observer/the-curse-of-knowledge-pinker-describes-a-key-cause-of-bad-writing).
- **The model failure is its inverse** (judgement). With no particular reader in mind, a model defines everything,
  including what the reader already knows, and still skips the one step that is truly unobvious. Write down who the reader is
  and what they already know; define only what that reader lacks.
- **Show the concrete scene or procedure** in place of the abstract finding: taps moving up the arm, then the
  illusion they produce (Pinker, above).
- **Write like you talk.** Ask of each sentence whether you would say it to a friend; replace what clanks with what
  you would say. A hard subject gets no longer sentences than everyday talk (practitioner, Graham,
  https://paulgraham.com/talk.html).
- **Show the draft to someone like the reader.** Imagining their confusion doesn't work; watching it does (Pinker).

## How-tos and tutorials

- **Work the first case fully, then fade.** Novices learn more from a worked solution studied before trying than
  from solving cold, and the advantage reverses as they gain skill, so later steps become clutter (measured,
  secondary summaries only, worked-example effect and expertise reversal,
  https://en.wikipedia.org/wiki/Worked-example_effect). A model tutorial tends to give every step at one density for
  an unnamed reader (judgement). Work the first example step by step, then leave later steps to the reader, then hand them a
  problem with part of the solution filled in.
- **The skill's "leave the last step to the reader" does not apply until the reader can take it.** In instructions,
  spell out every step a newcomer would get wrong; leaving it implicit is a fiction rule
  (`plain-language.md` has the full conflict).
- **Give the reader the tool to try it themselves:** the command, the input, what they should see (practitioner,
  Evans, above).
- **Headings as the reader's plain questions** ("what does this flag do?"), and a short tl;dr first (practitioner,
  Evans). Category-noun headings ("Overview", "Key Considerations") are the model habit (judgement).
- **Specific and quantified:** a real count, a real version number, a real error message.

## Structure and endings

- **Structure should go unnoticed.** McPhee settled his lead and his ending before ordering the middle, and wants
  the reader not to notice the frame (opinion, secondhand blog on *Draft No. 4*,
  https://www.goodreads.com/author_blog_posts/16709873-does-the-end-come-before-the-beginning). A model tends to
  announce its structure ("In this article we will..."), signpost every turn and end by summarising (judgement). Cut the announcement,
  and end on the place the piece was heading.
- **Write for a skimmer.** If stuck, put the most important sentence first (Graham, writing44, above).
- **Weak article tells, from forums only:** a scene-setting opener ("In today's fast-paced world"), an "In
  conclusion" paragraph that restates, every paragraph one expanded thought of the same length (opinion, snippet,
  https://the-decoder.com/reddit-users-compile-list-of-words-and-phrases-that-unmask-chatgpts-writing-style/).
  Flag them in a cluster, never alone.
- **Quotes from real people sound like people.** If every quote shares the narrator's polish and lands at the end
  of a paragraph, readers notice (Russell et al., above). Quote what was actually said, rough edges included, and
  never invent a quote.

## Where the evidence is thin

No controlled comparison of human and model tutorials was found, and Zinsser, McPhee and Pinker's classic-style
chapter were read only secondhand. The reader-clue table is measured; the tutorial-order advice rests on
educational research summaries, so treat it as a starting point to test with real readers (`judging.md`).
