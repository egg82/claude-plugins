# Verse

Poetry and song lyrics. Rhyme in a children's picture book is covered in `children.md`; comic verse also follows
`humour.md`.

## Judge verse with poetry readers

**Lay readers can't detect LLM verse and like it more.** Non-expert panelists judged ChatGPT imitations of named
poets human more often than the real poems, scoring below chance, and rated the AI poems higher on rhythm and
beauty. The authors' explanation: AI verse is simpler and easier to follow, while complex human verse reads to a
lay reader as incoherence (measured, Porter and Machery, *Scientific Reports* 2024, via
https://www.psypost.org/people-cannot-tell-ai-generated-from-human-written-poetry-and-they-like-ai-poetry-more/).

So for verse, neither question in `judging.md` can go to general readers. "Is it good" goes to people who read
contemporary poetry, or for lyrics, people who write or closely listen to songs in that genre. "Can you tell" goes
to such readers who also use LLMs heavily, as `judging.md` asks; whether they detect LLM verse any better was not
studied, so treat that panel as untested.

## What LLM verse does by default

- **Rhyme, nearly always.** GPT poems rhymed far more often than poems published by the Poetry Foundation and the
  Academy of American Poets: by one summary, about nine in ten GPT-3.5 poems had a rhyme against about two in three
  human poems, with roughly double the share of rhymed lines (measured, indicative only, figures unverified against
  the paper). Rhyme persists even when free verse is asked for (opinion, one essay).
- **Rhymed quatrains in iambic meter, first-person plural, and the words heart, embrace, echo and whisper.** Across
  thousands of poems in many forms and subjects, GPT-3.5 and GPT-4 verse was "much more constrained and uniform"
  than human poetry (measured, snippet, Walsh, Preus and Gronski, CHR 2024, https://arxiv.org/abs/2410.15299).
- **The theme stated outright.** A critic reading ChatGPT pastiches of Byron, Whitman, Plath and Ginsberg found few
  figurative techniques, themes said rather than imaged, platitudes, mixed metaphors ("I'm a fragile, broken
  yolk"), rhymes chosen for sound over sense ("beneath" with "relief"), and a rhyme scheme or meter that slips
  partway through (opinion, single critic,
  https://pgs.org.uk/news/2025-01-24/featured-on-portsmouth-point-can-you-tell-a-human-poet-from-ai-).
- **Sweet, tidy, and about nothing in particular.** Critics call ChatGPT verse "too trite and sweet" and say it lacks
  an occasion, a felt necessity behind the poem (opinion, snippet,
  https://poettopoet.substack.com/p/machine-dreams/comments).

These GPT measurements are older models; re-measure for the model in use by the method in `llm-tells.md`, with
contemporary published poems as the human set.

## Writing it

- **Start from a real object and the senses, before form.** Pattison's object writing: pick an actual object, write
  for ten minutes to a timer through all seven senses (sight, hearing, smell, taste, touch, the body's inner sense
  and movement), favouring the neglected ones, with no rhyme or rhythm and no need for full sentences (practitioner,
  Pat Pattison, *Writing Better Lyrics*, https://writersdigest.com/wd-books/writing-better-lyrics-excerpt). A model
  tends to start from the abstract feeling and the rhyme (judgement); this reverses the order.
- **Give the poem an occasion:** the particular event, person or place it is about, which only the poet can supply.
  A model has none; a person asking for a poem usually does.
- **Free verse is the contemporary default.** Rhyme and fixed meter are choices to make for a reason, or because the
  form or genre asks for them (a sonnet, a hymn, a pop chorus).
- **Make the form agree with the meaning.** Pattison's prosody rule: decide whether an idea is stable or unstable,
  then let line length, rhythm and rhyme agree. Perfect or family rhyme for something resolved; assonance and other
  remote rhymes for something unresolved (practitioner, Berklee write-up of Pattison,
  https://online.berklee.edu/takenote/?p=18154). A model tends to use perfect end rhyme whatever the line means
  (judgement).
- **When rhyming, keep it honest:** the rhyme word is the one the sentence would have chosen anyway; the scheme and
  meter hold to the end; no word order flipped to land the rhyme.
- **Image the theme; never state it.** The poem's last line in particular should not explain the poem.

## Lyrics

Lyrics are heard with a melody, so prosody governs: stressed syllables on strong beats, line lengths that match the
musical phrase, and rhyme type chosen for the meaning as above (the rhyme rule is Pattison's; the stress and
phrase points are general songwriting practice, not read in a source here). Speak the line in its
natural rhythm and check that the melody stresses the same syllables. Choruses repeat by design; repetition inside
a chorus is the form and never a tell.

## Where the evidence is thin

The lay-reader result is measured but from a summary of the paper; the LLM style findings came through abstracts and
search summaries; the critic readings are single voices. No study compared expert and lay detection of LLM verse.
Treat the writing advice as a starting point and let poetry readers decide.
