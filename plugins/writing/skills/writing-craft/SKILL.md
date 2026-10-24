---
name: writing-craft
description: "How to write text a person reads so nobody can tell an LLM wrote it. Use when writing or revising any prose — essays, tutorials, UI and game microcopy, emails, support replies, posts, product copy, speeches, fiction, lore, dialogue, poetry, non-English text, names, headlines, lines an LLM generates at runtime; when text \"sounds like AI\"; when asked to de-slop, humanize, voice-pass or review prose; before showing a rewrite as finished. Docs: the de-LLM pass (doc-cold-read owns structure). NOT visual UI design (ui-craft)."
---

# Writing craft

Readers who use LLMs heavily catch model-written articles of a few hundred words almost every time, and anyone who
catches it stops trusting the writer. What they notice is samey vocabulary, grammar too even for the register,
florid lines that hide what they mean, safe and predictable content, and the same upbeat shape in every message.
Short text (a line, a label, a message) has no validated detector, human or machine. The model that wrote the text
cannot hear any of this in its own output, so this skill pairs a writing and editing method with a judging method
that does not rely on the writer's ear. First, no reader can tell a model wrote it; then, it is a good one of its
kind.

**A voice doc wins.** Where the project has a style guide, voice doc or design-rules file, or the person has a
documented voice (for filed issues, if you've derived one as `bug-hunt`'s "Voice for filed issues" describes), read it first. Its decisions
override anything here; this skill supplies the method for meeting them and the checks for having met them.

## The loop

1. **Name the kind of text, its reader, and the doc that governs it.** An error message, a tutorial, a support
   reply, a product description, a speech, a mystery chapter, a picture book, a name and a runtime-generated line
   each follow different rules, and the same rule can be right for one and wrong for another. Find the voice doc
   for that kind; if none exists, say so and use the matching reference.
2. **Draft under the matching reference.** Load only the ones the text needs. When a model drafts, give it human
   exemplars of the same kind (`references/generated-lines.md`).
3. **Revise with the editing pass** (`references/editing-pass.md`): substance, then words, then sentences, then
   rhythm, then a cold reader. The words step flags against `references/llm-tells.md`, a list dated to the models
   it was measured on.
4. **Judge by `references/judging.md`.** Cheap screens first (other-family models proven on known-human text of the
   same kind, detectors proven the same way), then blind human readers, who give the verdict: readers who use LLMs
   heavily for "can you tell"; readers of the genre or venue, or the real audience in a comprehension test, for
   "is it good". Your own reread, or a fresh agent's, is a draft check and never the verdict.

**Scale the loop to the stakes.** A one-off short text (an error message, a Slack reply) gets its reference, the
words and editing pass, and a glance at the tells. Published prose or a large batch gets the full loop, readers
included. Regenerate the tells list (method in `llm-tells.md`) only when a model it doesn't name will write a lot of
text.

## Which reference

| The text is... | Load |
|---|---|
| Any prose, before calling it done; "sounds like AI"; a de-slop pass; a new model's tells | `references/llm-tells.md` |
| Revising a draft, a model's or a person's | `references/editing-pass.md` |
| Essays, blog posts, explanations, reports; tutorials and how-tos published as articles | `references/explanations-and-essays.md` |
| Text for broad audiences: low literacy, cognitive disability, screen readers, non-native readers; alt text | `references/plain-language.md` |
| Product UI: buttons, labels, tooltips, errors, empty states, onboarding, permission prompts, voice prompts | `references/ui-text.md` |
| Game UI: effect and upgrade lines, counters, the game's event log, waits, blocked actions, end-of-content | `references/game-ui-text.md` |
| Chat messages, personal email, forum, Discord and social posts, a person's own review, web copy | `references/conversational-and-web-copy.md` |
| Workplace email, Slack, support replies, apologies, cover letters, LinkedIn | `references/work-and-support-messages.md` |
| Product descriptions, ads, email subject lines, brand social; never a review in a customer's voice | `references/commercial-copy.md` |
| Speeches, presentations, video, podcast and audio scripts, voice-over | `references/speech-and-scripts.md` |
| Fiction prose: a scene, chapter, short story, narration | `llm-tells.md` (the turn, #2, #9, #11), `world-lines.md` (line rules), `dialogue.md`; the plan in `story-beats.md` |
| Character dialogue, distinct voices, game conversations and choices, barks | `references/dialogue.md` |
| Jokes, comic registers (dry, witty, dark, absurd...), running gags, getting a joke to land | `references/humour.md` |
| Memes, meme formats and templates, captions, "Nobody: / Me:" posts, internet-native humour | `references/memes.md` |
| Lore, item text, in-fiction journals and records, vignettes, flash fiction, worldbuilding | `references/world-lines.md` |
| A story plan, beats, an arc, genre conventions, "is this derivative?" | `references/story-beats.md` |
| Picture books, middle grade, educational text for children | `references/children.md` |
| Poetry, song lyrics | `references/verse.md` |
| Text in a language other than English; politeness, address forms, names across cultures | `references/other-languages.md` |
| A title, headline, brand or product name, character or place name | `references/naming.md` |
| Lines an LLM generates at runtime, prompts for that generation, bulk drafting by agents, which model writes | `references/generated-lines.md` |
| Deciding whether a rewrite is better; comprehension tests; screens and graders; recruiting readers | `references/judging.md` |

Visual design of the page belongs to `ui-craft`. For documentation (READMEs, a repository's `docs/`, wiki and
Confluence pages, ADRs, design docs), structure and clarity belong to `doc-cold-read` (and `confluence-kb-docs` for
Confluence knowledge-base articles); this skill still supplies the de-LLM pass: `references/llm-tells.md` and
`references/editing-pass.md` apply to a doc's prose like any other, and `references/explanations-and-essays.md`
covers how-to and explanatory pages. **Not researched here:** résumés and CVs, release notes, push notifications, legal and terms text,
press releases, academic abstracts. Start from the nearest reference (work messages for a CV, `ui-text.md` for
notifications, explanations for abstracts and release notes) and treat its advice as untested for that kind.

## Rules that fire every time

- **Say what it means, in the plainest words that carry it.** Simple wording exposes an empty thought where fancy
  wording hides it (practitioner, Paul Graham, https://paulgraham.com/simply.html). If a plainer sentence says the
  same, use it.
- **Concrete beats general.** One particular object, act, number or name does more than any adjective
  (practitioner, Failbetter Games' writer guidelines,
  https://www.failbettergames.com/fallen-london-writer-guidelines-part-iii/; Julia Evans on explaining: be
  specific and quantified).
- **People do things.** Characters as subjects, actions as verbs; no participial tails or nominalisations
  (measured rates in `llm-tells.md`, grammar tells).
- **Know who must be told and who may infer.** In fiction and lore, leave the last step to the reader:
  spelled-out explanation, tidy upbeat endings the story didn't earn, inserted morals and softened dark registers
  are the fiction tells shared across GPT, Claude and Llama (measured, Chakrabarty et al., CHI'25,
  https://arxiv.org/abs/2409.14509). Leaving a step means ending on a concrete turn, never on a maxim
  (`llm-tells.md`, the turn). Everywhere else, say it: instructions, UI, safety text, explanations, plain language,
  children's text and calls to action state the implied thing outright, because a reader left to infer can infer
  wrong (policy, W3C COGA, `references/plain-language.md`). The genre decides the ending too: romance and cozy
  promise the bright one.
- **Tells go stale.** Consecutive Claude versions share under half their over-used phrases (measured,
  `references/llm-tells.md`). Read for clusters, and re-measure for the model in use instead of trusting a list.
- **"Avoid clichés" does not work as an instruction.** It barely moves output, and a self-critique pass tends to
  trade one cliché for another (measured, Chakrabarty et al.). Human exemplars move output; rules don't.
- **Sameness shows across texts, rarely inside one.** The measurable deficit of model writing is a narrow range of
  themes and shapes over many outputs (measured, Ismayilzada et al., https://arxiv.org/abs/2411.02316). Review in
  batches: read twenty side by side and look for the repeated shape.
- **Names come from outside the model.** Model-proposed names collapse onto the same few (measured,
  `references/naming.md`). A human chooses the title of a work and a product's name; character names come by a
  rule; headlines and subject lines can be drafted and then checked.
- **Never gate prose with a regex or a CI check.** Word matches misfire on legitimate uses and teach writers to
  swap words while keeping the vague sentence. The tells list is for a reader.
- **Never fabricate a first-hand story** in text sent under a person's name: no invented anecdote, struggle or
  discovery narrative. Write what actually happened, and add personal detail only from the person.

## Evidence words used in the references

**measured**: counted over many texts or rated in a study. **practitioner**: a working writer's, editor's or
copywriter's published rule, or a product's shipped strings. **developer**: a game studio's own published writing
rule. **policy**: a published style guide, standard or venue rule. **opinion**: critics, forums, player posts,
reviews, vendor blogs. **judgement**: reasoning with no source behind it; "judgement, one reader" marks a rule that
rests on one person's ratings. Qualifiers: **snippet**, **secondhand** (or secondary) and **abstract only** mean the source was
read through a search result, summary or someone else's report; **unverified** means not checked against the source;
**inference** means reasoned from a cited source that does not state it. Weight rules accordingly, and where a
reference says the evidence is thin, treat its advice as a starting point to test. Many rules began from game and
fiction sources; where a rule holds only there, its reference says so.
