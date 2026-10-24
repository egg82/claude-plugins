# The editing pass

How to revise a draft, a model's or a person's, in the order editors work: substance, then words, then sentences,
then rhythm, then a cold reader. Each step assumes the one before it is done; polishing a sentence that the
substance step would cut is wasted work.

**Edit toward a voice.** A checklist of tells applied everywhere hardens into one more
house style (opinion, https://www.thedroptimes.com/open/71335/humanizer-ai-writing-house-style). Where a voice doc
or a person's own writing exists, that is the target.

**When revising a person's text, keep their sentences and edit by hand.** An LLM rewrite flattens the original voice;
in one study Claude and Gemini rewrites kept less of the author's style than GPT's (measured, snippet, model
versions unrecorded, https://arxiv.org/pdf/2604.22142).

## 1. Substance

- **Verify or cut** every number, name, quote and citation the draft can't support (practitioner,
  https://wonderingaboutai.substack.com/p/how-i-edit-ai-generated-copy-and).
- **The key points come from a person.** When people co-wrote with a feedback-tuned model, their essays converged,
  and the sameness came from the model's text, not the people's (measured, Padmakumar and He, ICLR 2024,
  https://arxiv.org/abs/2309.05196). Use the model for phrasing at most.
- **Ask "so what?" and "prove it" of every claim** (practitioner, Joanna Wiebe's sweeps, snippet,
  https://cxl.com/voice-of-customer/). A claim with no answer to either goes.
- **Add what a model can't supply:** a real comparison, a real quote, a detail from the actual situation. In text
  sent under a person's name it must be true and theirs; never invent it.
- **Write the paragraph plainly first** (SKILL.md, first rule). If the plain version says nothing, it needs a point
  before it needs better words.

## 2. Words

- **Replace a buzzword verb with what is actually being done.** deliver, drive, robust, utilise, going forward, in
  order to (practitioner, GOV.UK A to Z,
  https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/).
- **Replace a category noun with an instance;** add the number, name or date (practitioner, snippet, Proofed,
  https://proofed.com/knowledge-hub/ai-editing-checklist-how-to-spot-and-fix-ai-writing-patterns/).
- **The short everyday word; cut any word that can go; no figure of speech you are used to seeing in print**
  (opinion, Orwell, https://www.orwell.ru/library/essays/politics/english/e_polit). His sixth rule is the escape
  hatch: break any of them before writing something barbarous.
- **Cut compulsive hedges** (somewhat, to a certain degree); readers supply the hedges a claim needs (practitioner,
  Pinker, https://news.harvard.edu/gazette/story/2012/11/exorcising-the-curse-of-knowledge). Keep every hedge that
  carries calibration: in medical, legal, scientific and safety text, "may", "in most cases" and "the evidence is
  weak" are the content, and cutting them states a falsehood (judgement, no source measured it). Cut the reflexive
  softener; keep the hedge that names how sure anyone is.
- **Flag against `llm-tells.md`** here, and fix the thought under each tell.

## 3. Sentences

Joseph Williams's procedure turns nominalised, model-shaped sentences back into ones with people doing things
(practitioner, secondary summary, https://nysba.org/?p=27039):

1. **Find the characters,** the people or things the sentence is about.
2. **Find the actions,** often buried in nouns ending -tion, -ment, -ance, -ing.
3. **Make the characters subjects and the actions verbs.** "The intention of the committee is to improve morale"
   becomes "The committee intends to improve morale."
4. **Reconnect the logic** with because, if, when, how, which the nouns had hidden (practitioner, Boston
   University, https://www.bu.edu/teaching-writing/resources/sentence-clarity-characters-and-actions).

A quick diagnostic from the same page: mark every verb and its subject, every form of "be" and "have", and every
noun that could be a verb; sentences with few real verbs are the ones to rewrite.

**These are defaults.** Keep a familiar noun when the verb form reads worse ("I don't know her
intentions"). Keep the passive when the known item should open the sentence, since old information goes first and
new last ("The president was reelected with 54% of the vote") (Williams, above). The passive is normal when the actor
is unknown or unimportant (opinion, snippet, Pullum via https://languagelog.ldc.upenn.edu/nll/?p=1318), and models
under-use it (`llm-tells.md`, grammar tells), so converting every passive makes text more model-like.

**End sentences where the thought ends.** Cut participial tails, "that" clauses as subjects and pairs that say one
thing twice (`llm-tells.md`).

## 4. Rhythm

- **Vary sentence length.** A run of same-length sentences drones; a long sentence that builds, then a short one,
  gives emphasis (practitioner, snippet, Gary Provost, *100 Ways to Improve Your Writing*, via
  https://courses.lumenlearning.com/suny-geneseo-guidetowriting/wp-json/pressbooks/v2/chapters/206).
- **Read it aloud** for pacing (practitioner, Wondering About AI, above).
- **Count the dashes, threes and closers.** Swapping a dash for a hyphen doesn't fix the rhythm; restructure the
  sentence (practitioner, Proofed, above).
- **End on the sharpest specific line or the actual ask,** never a warm summary of what came before (practitioner,
  Proofed).

## 5. A cold reader

- **Rest, then reread** before calling it done (practitioner, Wondering About AI).
- **Your own sense of clarity is unreliable,** because you know what you meant: show the draft to a representative
  reader and revise where they stumble (practitioner, Pinker, above; snippet,
  https://www.psychologicalscience.org/observer/the-curse-of-knowledge-pinker-describes-a-key-cause-of-bad-writing).
- Whether it reads as human, and whether it is good, are decided by `judging.md`.
