# Iterating, and diagnosing a failed search (§4, §5)

Load when results disappoint, before rewording a query you already tried, or when you notice you are on
round three of near-identical queries.

## 4. Iterate on what you READ, not on what you imagined

This is the difference between research and thrashing, and the surface action looks identical.

**Terms harvested from a document you just read are new information. Synonyms invented in your own
head are re-rolling the same dice.** Collect the vocabulary the results use — the product's real
name, the feature's actual term, the error's upstream identifier — and run a fresh round with it.
Expect two or three rounds on anything non-trivial.

**Often the snippets alone are enough** — you don't have to open anything to learn that the feature
is called "clustering" rather than "sync." Reading the listings is both your triage step (§8) and
your cheapest vocabulary source, which is why it comes before fetching.

(Librarians call this *pearl growing*; the read-search-read loop is *berrypicking*.)

When you are editing a query rather than starting a new round, condition the move on what came back:

| last query | do |
|---|---|
| **results came back, none useful** | add terms, fix vocabulary, correct spelling, expand the acronym |
| **partly useful** | substitute, reorder, or add terms |

**Change one thing, then look.** Stacking edits blind means you can't tell which one moved anything.
Don't throw away terms that are working — but measured growth across a whole successful session is
under one term, so this licenses keeping what works, not accreting a long query.

**Don't over-plan.** Time spent composing the perfect query correlates with worse outcomes; more
cheap cycles correlates with better.

## 5. Read the failure shape instead of rewording

The shape of a disappointing result set tells you which of three things is broken. Rewording only
ever fixes the first.

| symptom | broken | move |
|---|---|---|
| **Zero / near-zero** | the **query** — over-ANDed, too many terms, a long quoted phrase, a dead engine | drop terms; unquote; confirm the probe *can* return non-zero |
| **Junk, off-topic, wrong register** | the **index** or the **vocabulary** | switch index; harvest the term of art first |
| **Good on-topic results that don't contain the answer** | the **question** | stop and reframe |

The third row is expensive and easy to miss: every result is relevant, well-ranked and reputable, so
the natural move is "search again, slightly differently" — which can burn ten queries on a question
with no answer in the form you're asking. Tells: asking for one recommended value where the real
answer is "measure it"; asking which of N is "best" where it's "depends"; asking for a stated fact
that only exists as a table row or a calibration procedure.

**But "nothing relevant exists" is an inference people are measurably bad at** — confidence that a
topic has no answers tracks how hard it *feels*, not whether answers exist. Treat it as a hypothesis
and spend one cheap external check: does this attribute appear on *any* comparable spec sheet? A zero
result set can be the same thing in disguise — don't assume row one on a clean zero.

**Detect cycling.** Productive iteration adds and removes *concepts*; struggling iteration
substitutes *words* while staying close to the first query.

**Abandon a poisoned line — this failure is architectural for you and not for a human.** When a
retrieval returns nothing useful, experts discard the material entirely and start elsewhere. An agent
keeps appending *something* retrieved, so one bad hit contaminates every later query: a miss on a
country's president pulled in the wrong country's ex-president, whose name then rode along in every
subsequent query and foreclosed the answer. Dropping a line is a distinct move from refining a
query — name the contaminated terms and stop using them.

**Cap it.** Past ~5 reformulations on a fact-finding task, change medium: switch index, fetch a
source directly, or ask.
