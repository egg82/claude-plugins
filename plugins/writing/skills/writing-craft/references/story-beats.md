# Story beats, arcs and tropes

Planning or reviewing a story: what each genre promises its readers, which beats readers already file as template,
and the structural faults that make a long story go flat.

## The genre's promise comes first

Each genre has a contract, and readers punish a break harder than any weak sentence. Name the genre before
planning, and check the plan against its contract before checking it against anything below.

- **Romance ends with the couple together and committed,** happily ever after (HEA) or happy for now (HFN): no
  separating them at the end, no killed love interest, no doubt the relationship survives. The reader's heart is
  not divided unless the structure is announced up front, and the couple shares scenes, so count shared scenes in
  revision (practitioner, https://writersinthestormblog.com/2026/06/three-ways-to-lose-a-romance-reader/). RWA's
  definition asks for an "emotionally satisfying and optimistic ending"; a Harlequin editor says a promise of a
  better beginning can satisfy more than a ring (practitioner, snippet). An upbeat ending is the convention here,
  not a model tell.
- **A mystery plays fair.** Every clue the detective uses is shown to the reader; the culprit is an identified
  suspect with a motive, never a bystander who vanishes; no accident or unexplained intuition solves it. A clue may
  be hidden in plain sight, and red herrings, lying suspects and a detective who keeps a theory back are allowed
  (practitioner, Knox's and Van Dine's rules as read at
  https://crimereads.com/a-magicians-contract-between-reader-and-writer-rules-for-delivering-a-whodunit/ and
  https://thrillingdetective.com/2019/01/10/father-knoxs-decalogue-the-ten-rules-of-golden-age-detective-fiction/).
  **Models fail fair play in a measured way:** in LLM detective stories, misleading was easy but the clues did
  little to narrow the outcome, later paragraphs added little, the culprit was settled for reasons other than the
  clues (GPT-4o often during the introduction), and endings were over-creative and contradicted the clues
  (measured, Wagner, Keydar and Abend, https://arxiv.org/html/2507.13841v1). Plan clues as keyed records: for each,
  the chapter it appears in and which suspects it rules out, then check the solution uses only those.
- **A cozy keeps violence and sex offstage** (the body found, the murder undescribed), peril mild, the sleuth an
  amateur in a small community, and order restored at the end (opinion, snippets, descriptive rather than a
  rulebook; boundaries vague). Low stakes are the point.
- **A thriller runs on a clock.** Shorten the timetable just as the characters seem close; end scenes on a
  question whose answer opens another. The named failure is "hurry up and wait": a countdown set up and then
  stalled (opinion, craft blogs, https://careerauthors.com/4517-2/).
- **Kishōtenketsu has no driving conflict.** Ki introduces without disrupting, shō deepens without escalating, ten
  reframes what came before, ketsu reconciles the threads; interest comes from "how do these connect?", not
  opposition (opinion, https://storytellingdb.com/kishotenketsu/; Spirited Away and Doraemon as examples). Failures:
  a rushed shō, a ten that only moves the plot, a forced ketsu. Untested on models; by inference, a model's
  escalation habit would turn the ten into a villain and the ketsu into a moral.
- **Literary fiction gets cut early for exposition.** The commonest reason given for rejecting a first novel is
  backstory crowding the first dozen pages, then overwritten openings, unclear viewpoint and unconvincing motive;
  agents decide in five to ten pages (opinion, editor and agent accounts,
  https://www.tckpublishing.com/why-novels-get-rejected/).
- **Children's stories:** the child solves the problem and the lesson is never said aloud (`children.md`).

## What model stories do, across genres

- **Upward drift and early resolution.** GPT-4 synopses took a "man in a hole" shape over half the time against
  under a third for humans, almost never a downbeat arc, with valence rising and the setback and climax placed
  early; asked for a negative arc, it complied under 55% of the time. Planning turning points explicitly raised
  "best for suspense" from 8% to 48% (measured, Tian et al., EMNLP'24, read as an overview,
  https://www.alphaxiv.org/overview/2407.13248). Where the story is meant to be dark or ambiguous this is the
  largest single risk; in romance, cozy or a bedtime story the upbeat end is correct and the risk is the early,
  unearned resolution.
- **Neat, single-thread, morally simple.** Over 10,272 prompts each answered by a person and five models, AI stories
  over-explained themes, favoured one storyline, had simpler social structures, less moral ambiguity and less
  play with time; structure alone told human from AI at 93% F1 without any style features. Claude's events
  escalated notably flatly (measured, abstract, StoryScope, https://arxiv.org/abs/2604.03136).
- **Same arrangements, stereotyped endings,** in Chinese web fiction too (measured, abstract,
  https://arxiv.org/abs/2603.14430).
- **Experts name weak endings, clichéd metaphors and thin characters without subtext** (measured, abstract,
  Chakrabarty et al., "Art or Artifice?", https://arxiv.org/abs/2309.14556).

## Tropes: worn, usable with a turn, fresh

**A familiar beat is fine; an unturned one is the problem.** The praised examples keep the convention and take a
left turn: Midsommar set aside The Wicker Man's burning finale after invoking it (practitioner, snippet,
https://www.empireonline.com/movies/news/midsommar-director-ari-aster-on-avoiding-the-influence-of-the-wicker-man).
A model planning a story tends to reach for the worn beats first (judgement), so a model-written plan gets a cold
read by a genre-literate human before more is built on it.

**Build three lists per genre** from that genre's own readers: forums, reviews, listicles and essays. *Worn:* beats
readers name as template (for post-apocalyptic fiction, raiders in wasteland costume, chosen ones, "people are the
real monsters" told as a parable; opinion, snippet,
https://www.goodreads.com/topic/show/1486060-what-is-the-most-overused-dystopian-cliche?page=2). *Usable with a
turn:* conventions readers still enjoy when the stock payoff is changed, such as the friendly village with a
sinister belief minus its sacrificial finale. *Fresh:* what readers praise as unlike the rest, such as escalation
that changes the kind of play rather than the size of a number (opinion,
https://news.ycombinator.com/item?id=36972227). The evidence for any such list is weak: it maps what readers call
template and is never a verdict on one beat. Check the plan against the worn list, and turn whatever lands on it.

## What makes a long story go flat

- **Nothing changes.** A scene that ends where it started is activity without an event (practitioner, McKee's
  *Story* via secondhand notes, https://www.goodreads.com/author_blog_posts/6550975-do-your-scenes-turn?tab=book). In
  a low-conflict story the change can be in understanding or relationship rather than fortune.
- **Clean wins stop a conflict-driven story;** "yes, but" and "no, and" keep it moving (practitioner, Sanderson and
  Kowal's try-fail cycle,
  https://www.brandonsanderson.com/blogs/blog/brandon-sandersons-2025-overview-of-story-structure-lecture-3).
- **Promises without visible progress** read as going nowhere (practitioner, Sanderson,
  https://brandonsanderson.com/blogs/blog/brandon-sandersons-2025-guide-to-plot-lecture-2).
- **Single-quality gates make grind** in a game story; players need to see what they're reaching for
  (developer, Failbetter, https://www.failbettergames.com/news/echo-bazaar-narrative-structures-part-two).
- **Unattended orderings go undramatic.** Where content can arrive in many orders, simulate many playthroughs and
  read the sequences that actually come up (practitioner, Emily Short,
  https://emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/).
- **Detailed outlines help.** A detailed outline beat a plain one on human-rated coherence and interest (measured,
  20 stories, Yang et al., DOC, ACL 2023, https://arxiv.org/abs/2212.10077).

## Checking a plan

Code and critics can answer structural questions; neither can say whether a beat is good. Have the writer declare,
per beat, fields that can be filled honestly and then checked over each route through the story. **Set the flags
by the genre's contract first.** The defaults below suit conflict-driven plots (thriller, adventure, dark fantasy,
most mysteries); in kishōtenketsu, cozy, slice-of-life, comedy vignettes or a bedtime story, a run of "none" turns
and clean yeses is the form, so flag only what the contract forbids.

| Field | Values | Flag when (conflict-driven default) |
|---|---|---|
| turn | up, down, none, reframe | three or more in a row the same way; the arc nets upward early where the genre is dark |
| outcome | yes, yes-but, no, no-and | two clean yeses in a row; a stretch with no setback |
| opens / advances / pays | promise or clue ids | unadvanced too long; never paid; paid before opened; a solution using an unshown clue |
| cost | none, time, people, goods, option, trust | a stretch with no cost; every cost the same kind |
| moves | characters whose state or understanding changes | a beat that moves no one; a recurring character unmoved for long |

A critic agent, if used, answers yes/no questions with a quoted span: does the situation end different from how it
started; does the ending break the genre's contract; is the ending tidier or brighter than the planned turn; is a
theme stated that the scene already shows. Model judges don't track experts on holistic quality (measured,
abstract, https://arxiv.org/abs/2309.14556), so whether it lands belongs to human readers of the genre
(`judging.md`).
