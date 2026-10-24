# Naming and titles

How to find and check a title, a headline, a brand or product name, or a character or place name. This file gives
method and checks; it never generates candidates, because model-proposed names are the problem it exists to solve.

## Who chooses

**A model's first candidates are the ones every model gives.** Model-proposed names converge across users and
across models (measured, "Invented names" below).

- **The title of a work, a product name, a character's name: a human chooses,** from candidates made by the methods
  below. If asked for ideas, give the method and the checks; don't supply a list.
- **Headlines, email subject lines and section titles** are written per piece and can be drafted by anyone,
  including a model, then checked: against the over-used shapes in `llm-tells.md`, and where traffic allows, by
  testing several variants (below).

## Titles of works

All inferred from encyclopedia-level sources; no author's own account of choosing a title was read.

- **The premise or opening scene.** *A Dark Room* is its opening situation (https://en.wikipedia.org/wiki/A_Dark_Room).
- **A place in the world.** *Kentucky Route Zero* is the road the plot is about
  (https://en.wikipedia.org/wiki/Kentucky_Route_Zero).
- **A character or a term from the work.** *Hollow Knight* came from a jam game's character and an in-world term
  (practitioner, snippet, https://mcvuk.com/when-we-made-hollow-knight/).
- **A phrase from earlier literature.** *Brave New World* from *The Tempest*; *Absalom, Absalom!* from 2 Samuel
  (practitioner, https://en.wikipedia.org/wiki/List_of_book_titles_taken_from_literature).
- **Titles change.** *Disco Elysium* was *No Truce With The Furies* until late in development
  (https://en.wikipedia.org/wiki/Disco_Elysium). A working title is fine; ship the one that passes the checks.

**Checks a title or name must pass:**

1. **Exact-phrase search** in the stores and catalogues where it will live (Steam, app stores, Amazon, a trademark
   register for a product) and a general search engine finds no well-known work or product by that name
   (practitioner, snippets, https://itch.io/post/542765).
2. **The domain and the obvious handles are free,** or the project accepts a variant.
3. **Someone who hears it once can spell it** and guess roughly what kind of thing it is.
4. **Short, with no invented spelling** unless invention is the strategy. Most Steam titles are one to three words,
   and length shows no link to sales (measured, 94,371 releases,
   https://howtomarketagame.com/2025/02/03/are-game-names-getting-longer-how-to-quit-your-job-and-write-a-title-for-your-steam-game-in-2025-naming-seo-tips-faq-guide-profits-earnings-optimization/).
5. **Not a stock model shape.** It isn't built from the over-used word lists in `llm-tells.md`, and passes the swap
   test (`world-lines.md`).

## Brand, product and feature names

- **Pick the type before generating:** descriptive (clear, hard to trademark, blends into the field), evocative
  (Nike, Apple), invented or blended (Kodak; most legal room, costs money to teach), or a founder's name (opinion,
  agency taxonomy, https://fabrikbrands.com/insights/naming/types-of-brand-names).
- **Volume, then a shortlist, then customers.** Lexicon generates over a thousand ideas, shortlists 50 to 100, and
  tests with customers in each market; Swiffer was preferred over 80% of the time in tests, and Pentium was
  researched in six markets. Decide how the name should feel (fast, full, reliable) before naming, and keep
  brainstorm groups small, since groups of four or more converge under peer pressure (practitioner, David Placek,
  https://www.lennysnewsletter.com/p/how-to-find-the-perfect-name). A model asked for brand names tends to return a
  short list of descriptive compounds and smooshed words, the opposite of this process (judgement).
- **Sound carries meaning:** t, k and b read hard, fast and reliable (BlackBerry, T-Mobile); n, l and m read soft;
  v reads vibrant (practitioner, vendor, snippet, https://www.lexiconbranding.com/?p=1466).
- **A feature name in a product** follows the product's UI text rules: plain, descriptive, sentence case
  (`ui-text.md`), unless it is marketed on its own.

## Headlines and subject lines

- **Most headline tricks show no reliable effect; testing several variants does.** Over 100 publishers and 10,000
  tests, "this" or "these" was the one clear winner; articles ("a", "the") lowered click-through; headlines of 73
  characters or more raised it; questions, short punchy headlines and name-dropping showed no significant effect.
  Testing five variants found a winner about 50% above average against about 23% for two (measured, Chartbeat,
  https://chartbeat.com/?p=3627). Results vary by publisher, and a winning headline optimises one story without
  generalising (opinion, snippet, Poynter on the same data).
- **Negative words drew more clicks in one outlet's era:** across about 22,743 Upworthy A/B tests (2013 to 2015),
  each extra negative word raised click-through by 2.3%, positive words lowered it, and sad beat angry or fearful
  (measured, snippet, https://www.niemanlab.org/2023/03/negative-words-in-news-headlines-generate-more-clicks-but-sad-words-are-more-effective-than-angry-or-scary-ones/).
  It measures clicks, not whether a headline is honest or good. The short, upbeat question headline a model
  favours has no measured edge in either dataset.
- **Subject lines and commercial headlines:** `commercial-copy.md`.

## Realistic and contemporary names

- **Fix who the person is before naming them:** birth year, region, class, generation (immigrant or second
  generation), and the culture the name comes from, then take given name and surname from one tradition
  (opinion, one agent skill's documentation,
  https://claudeskills.info/skills/jwynia/agent-skills/character-naming/). Look the given name up by birth year in
  national birth records (the US SSA lists the top names per year back to 1880, snippet,
  https://www.ssa.gov/oact/babynames/decades/century.html), never today's list.
- **Swapping one stock surname for another is not a fix.** The same source names Chen, Patel, Garcia, Kim and Maya,
  Marcus, Sofia, Aiden as model defaults, and says a corrected model hops to the modal name of the next ethnic
  group (opinion, unmeasured). Models also leave non-White characters out of neutral prompts and put them in
  subordinate roles once power enters (measured, snippet, https://arxiv.org/pdf/2404.07475). Draw from a list with
  real randomisation.
- **Follow the culture's name structure, not "first name, last name".** Family name first in Chinese, Japanese,
  Korean and Hungarian; patronymics in Icelandic (people listed and addressed by given name) and Malay; two family
  names in Spanish; gender-inflected Russian patronymics; everyday nicknames in Thai; single names common in
  Southern India and Indonesia. Form of address follows too: Vietnamese by given name, titles matter in German
  (policy, W3C, https://www.w3.org/International/questions/qa-personal-names). Forms that ask for names follow the
  same page (`other-languages.md`).
- **Minor characters:** Failbetter gives them generic titles rather than names, for universality and fewer
  continuity problems (developer, http://www.failbettergames.com/points-of-light-pools-of-shadow-part-ii/). That
  suits fable-like and game writing; realist fiction names its minor characters, as people are named.

## Invented names for speculative fiction

**Never take a name from the model's own head.** Default model names are a measured tell across GPT, Claude, Gemini,
Llama, DeepSeek and Grok. No person or book was named Elara Voss before August 2023; by 2025, 62 books on Amazon
were credited to her. The family: Elara, Elena and Elias with Voss, Vex, Vance, Thorne, Finch, Solis or Dorne, plus
Aris Thorne, Kael, and places such as Erebus, Eldora and the Whispering Woods (measured, Max Read,
https://maxread.substack.com/p/who-is-elara-voss). In one open model, "elara" ran 85,513 times its rate in human
text (measured, Antislop, https://arxiv.org/abs/2510.15061). A model reaches for a name with no baggage, and "none
of us have ever actually met a person named Elara" (practitioner, Laura Wattenberg, snippet,
https://aol.com/articles/ai-generated-baby-name-rolls-195619325.html). A name that belongs to a world carries
baggage: a place, a trade, a history.

Pick names by a rule, never by asking for "a name":

1. **An outside list** that fits the setting: historical registers, parish records, gazetteers, a real language's
   word lists. A model may pick from a list a human or code supplied, and code draws it without repeats
   (`generated-lines.md`).
2. **A naming language per culture** (practitioner, A. K. Larkwood, https://aklarkwood.com/naming-language): a
   small consonant set and the vowels you like; a fixed syllable template (CV(C) gives ta, nik, ri, nam); only easy
   clusters; one spelling per sound and a spelling habit per language (c for one, k for another). Decide whether
   names mark gender, status or family. Rosenfelder's *Language Construction Kit* covers the same idea (snippet,
   https://www.zompist.com/lckbook.html).
3. **Roots from real languages,** chosen for the character's core trait: Erret from Albanian for dusk, Myrr from
   Swedish for mire. One style per region; neither plainly modern nor unpronounceable (practitioner, Ty Arthur,
   https://www.goodreads.com/author_blog_posts/16461710-what-s-in-a-name-coming-up-with-words-and-phrases-for-fantasy-worlds?tab=book).

**Place names are a specific plus a generic** that names the kind of land (peak, vale, ford, ham, ton, bay), so even
an opaque specific tells the reader what the place is (practitioner, toponymy,
https://www.anps.org.au/upload/Generic_Terms_Australia.pdf). Give each culture its own way of joining the parts,
layer languages on one feature, and let forms wear down, so names read as accreted history: Southampton is south +
ham + ton (practitioner, https://situ.readthedocs.io/brief.html). "The Three Peaks" beats "Mountain Kingdom".

**Real archaic words over coinages.** Gene Wolfe named far-future things with real, obscure words (fuligin, fiacre,
optimates), a riddle with a dictionary behind it (practitioner, https://www.sciencefictionbookclub.org/?p=2706).
Peake's names fit role and temperament (Steerpike, Sepulchrave, Swelter) (opinion, snippet, reader reviews).
**Odd concrete names do worldbuilding** ("the slime banks", "the city of fallen pylons"; `world-lines.md`).
