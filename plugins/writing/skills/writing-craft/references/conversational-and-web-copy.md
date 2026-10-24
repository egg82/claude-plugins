# Conversational text and web copy

Chat messages, emails, forum, Discord and social posts written for a person, a person's own genuine review, and
landing-page and web copy. Short
interface strings on a page follow `ui-text.md`; a message under a person's name follows their documented voice
where one exists (for filed issues, if you've derived one as `bug-hunt`'s "Voice for filed issues" describes). Workplace email, support replies and
cover letters are in `work-and-support-messages.md`; product descriptions, ads and subject lines in
`commercial-copy.md`, which bars writing a review in a customer's voice.

## What getting caught costs

- **Being caught costs the reader's trust.** A reader who spots AI authorship assumes the sender can't write or
  is deceiving them, and stops reading; Paul Graham says AI-written founder emails feel "like being lied to"
  (opinion, https://the-decoder.com/y-combinator-founder-paul-graham-says-ai-written-founder-emails-feel-like-being-lied-to/).
  Trust in a writer fell when readers were told AI was involved (measured, Georgia Tech, CHI 2022,
  https://nlp.stanford.edu/~diyiy/docs/chi22_perception.pdf), and 18% of consumers in a vendor survey said they had
  unsubscribed from a marketing email they suspected was AI (measured, vendor,
  https://www.contentgrip.com/ai-email-trust-crisis/).
- **Many venues ban it outright, AI-edited text included.** Hacker News: "Don't post generated comments or AI-edited
  comments" (policy, https://news.ycombinator.com/newsguidelines.html). Moderators enforce by flags and judgement,
  not detectors, which give false positives (policy, snippet, Stack Overflow's 2023 dispute,
  https://devclass.com/2023/06/05/stack-overflow-volunteer-moderators-down-tools-over-secret-new-policy-that-obstructs-removal-of-ai-generated-content/).
  In such a venue the text must be the person's own.

## Chat and post tells

Measured on GPT-4o chats shared up to mid-2025 unless noted (Washington Post via
https://www.bostonglobe.com/2025/11/13/business/chatgpt-writing-style-clues/). These drift with model version like
every list in `llm-tells.md`.

- **Emoji as structure:** in about 70% of messages, the green check at 11 times the human rate; emoji before
  headings and bullets (measured; practitioner, https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing).
- **Markdown in plain-text venues:** headers, bold on every instance of a key phrase, list items that open with an
  inline bold header, quote markers. Markdown alone is weak evidence (practitioner, Wikipedia, above).
- **Assistant scaffolding:** "Certainly!", "Of course!", "You're absolutely right!", "I hope this helps", "Here's a
  template for...", an answer-style preamble, a hedging disclaimer, "It's important to recognize that..."
  (practitioner, Wikipedia). Leftover placeholders ("Dear [Name],") and "As an AI language model" are the tells
  ordinary readers catch with certainty (practitioner, snippet, Boston Globe, above).
- **Even, agreeable affect.** Classifiers separate model replies from human ones on X, Bluesky and Reddit, and the
  widest gap is emotional tone: people are blunter, more negative and more uneven. Instruction-tuned models were
  more detectable than base models, and bigger models were no more human (measured,
  https://arxiv.org/abs/2511.04195). A subtly promotional, positive tone is on Wikipedia's list too.
- **Uniform polish.** People bend grammar, punctuation, capitals and spelling to carry tone; in paired posts, about
  half the machine versions used full punctuation where the person had not, with more intensifiers and adjectives
  and fewer discourse markers ("well", "anyway") (measured, snippet, small qualitative sample,
  https://arxiv.org/pdf/2401.14698). Human: "lol no. not even close". Machine: "That's a great point, and not even
  close in my view."
- **No personal aside, and long.** Human comments are shorter, more varied and carry personal experience; model
  comments are on-topic, informative and repetitive (measured, snippet,
  https://sol.sbc.org.br/index.php/webmedia/article/view/38001).
- **Everything emphasised;** nothing ranked above anything else (opinion, snippet, a Reddit user quoted at
  https://www.techradar.com/ai-platforms-assistants/chatgpt/the-days-of-the-em-dash-being-a-chatgpt-giveaway-are-over-its-time-to-bring-it-back).
- **Em dashes and "not just X but Y"** (`llm-tells.md`). A colleague's emails "full of em dashes" read as AI to
  their coworkers (practitioner, snippet, Rolling Stone, cited there).

## Fixes for chat, posts and email

- **Start with the content.** No greeting, offer or sign-off the venue doesn't use; plain text where the venue is
  plain; bold one thing at most; prose, not bold-header lists (practitioner, Wikipedia). The venue clause cuts both
  ways: formal email, much workplace email and email in many languages expect a greeting and a sign-off, and
  dropping them reads as curt (`work-and-support-messages.md`, `other-languages.md`).
- **Write in the venue's own mechanics.** Read a page of real posts in that place first. Fragments, lowercase,
  dropped full stops and discourse markers belong where the people there use them. Never plant typos to look
  human: readers punish errors (practitioner, https://intfiction.org/t/thoughts-for-prospective-ifcomp-authors/12363),
  and the tell is the same polish in every register. The measured detail is in "Casual register" below.
- **Shorter, and varied message to message.** Spend emphasis on one point and let the rest be flat.
- **Take a position and ground it in the thread's specifics,** where the person is giving an opinion in a
  discussion. Don't default to the even, balanced, agreeable reply there. Support replies, mediation, and
  encyclopedic or news text are meant to be even-handed, and there the tell is vagueness.
- **One true detail only the sender would know,** supplied by the sender. Never invent an anecdote.
- **Relational emails get written by the person,** or from their own words: congratulations and thanks written by
  AI read as lazy and insincere (snippet, secondary news on Ohio State and Florida studies, via ContentGrip above).
  A rough true note beats a polished generic one (opinion, Graham, above). Check for brackets and meta-talk before
  sending.

## Casual register: tidiness and consistency

Scope: texts, chat, Discord, quick emails and forum replies. Never UI, published or professional text, which keep
their own polish (`ui-text.md`, `work-and-support-messages.md`).

**Measured here (measured, local, one model, one forum; `scripts/casual/results.txt`).** 100 Hacker News replies
(2015 to 2019) against 100 Claude Sonnet replies to the same parents, length-matched. Claude's replies were tidier:

- Fewer sentences starting lowercase (0.25% against 2.5%).
- No message ending without terminal punctuation (0% against 10%).
- No slide from a formal first sentence to a looser last one (0% against about 10% of messages with three or more
  sentences).
- Less varied sentence length (SD 6.4 against 9.4 words per message).

No clear difference in vocabulary breadth, uncommon-word share, contractions, em dashes or apostrophe drops, so
the idea that Claude's casual vocabulary is wider is unsupported here. One model, n=100: the tidiness gaps are
solid, the nulls are not proof of no difference. HN is itself a tidy venue, so the gaps are small.

Informal chat (texts, group chats) is typically looser than Hacker News on capitalisation and terminal
punctuation, and Claude is tidier than both.

**Published evidence, by strength.**

- Final period: a full stop on a short text reply (Okay, Sure) read as less sincere (measured, Klin et al. 2015,
  126 students, one-word replies only; https://time.com/4141133/ending-texts-periods). Do not stretch it to long
  messages.
- Ellipses split by age: older writers use them as a separator, younger ones as trailing off, so each misreads the
  other (practitioner, McCulloch, https://www.sciencefriday.com/segments/because-internet/). Take the convention
  of the writer you imitate and hold it.
- Lowercase can be a deliberate deadpan, and "lol" marks irony more than laughter (practitioner, secondary
  summaries of McCulloch, snippet). These are habits a writer has or lacks, not decoration.
- Text-speak is about 3% of real teen IM; the rest is conventional words (measured, Tagliamonte and Denis 2008,
  press figure, snippet; https://allthingslinguistic.com/post/26173103924). Heavy slang is as wrong as none.
- Uncorrected typos run about 2.3% on phones (measured, Palin et al. 2019, transcription task;
  https://www.pokristensson.com/pubs/PalinEtAlMobileHCI2019.pdf), mostly one slip in one word: adjacent key,
  doubled, dropped or swapped letter (measured, second-hand figures, https://arxiv.org/pdf/2105.05977).
- Injected random typos as a disguise: untested. The one humanizer study did not try them (measured,
  https://arxiv.org/html/2501.03437v1); "they read fake" is inference.

**The rule.** Match the venue's and the person's habits, held consistently: which sentences start lowercase, whether
the last sentence takes a full stop, a message that loosens as it goes, sentence lengths that jump. Take the habits
from the person's own messages; a short reply may drop the full stop where a long one would not. Never sprinkle
errors.

## Web copy

**The tells.** Polished but interchangeable: it could describe almost any business, takes no position, answers no
objection, offers no next step ("We provide innovative solutions", "Take your business to the next level")
(practitioner, https://www.markbrinker.com/ai-website-copy). Promise verbs (leverage, seamless, robust, elevate,
streamline, skyrocket), which models inherited from human marketing cliché (practitioner, snippet,
https://www.kalungi.com/blog/prompt-ai-for-better-marketing-copy; opinion, snippet, https://www.success.com/?p=78529).
Mood adjectives in place of the thing ("modern elegance", "timeless sophistication") (practitioner, snippet,
https://multipletabsopen.substack.com/p/ai-and-what-im-noticing-as-an-agency).

**The fixes:**

- **Decide the page's job before drafting:** the question it answers, the worry it settles, the mistake it prevents.
  Outline, then write one section at a time from real notes and real client questions (practitioner, Brinker).
- **Use the customers' words.** Copywriters mine reviews, surveys, interviews and comments for repeated phrases and
  reuse them; one headline lifted from a customer's book review drew several times the clicks (practitioner,
  snippet, secondary case, https://cxl.com/voice-of-customer/). Keep the rough phrasing when it carries the punch.
- **Name the result:** what changes, by how much, for whom, in place of a verb of ascent. Name the material, price
  or audience in place of a mood adjective.
- **Say it aloud, write down what you said, and don't doctor it.** Jason Fried's spoken homepage lines beat
  everything he had written, and dressing them up "because marketing" made them fall flat (practitioner,
  https://world.hey.com/jason/then-just-say-it-like-that-3fe992bb).
- **Ordinary words and simple sentences;** most editing is cutting (SKILL.md, first rule).

## Judging

Judge in a batch with readers who use LLMs heavily for "can you tell", and readers from the venue for "is it good"
(`judging.md`). Passing a detector is not the defence; specific, correct, first-hand content is.
