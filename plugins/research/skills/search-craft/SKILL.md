---
name: search-craft
description: "How to construct, diagnose and iterate a web search query so it finds the answer. Use BEFORE any web search — WebSearch, SearXNG, or a site's own search box — and again whenever results disappoint, especially before rewording a query you already tried; tells whether the query, the index or the question is at fault."
---

# Search craft

**What routes you here:** `hooks/search-craft-gate.sh`, a PreToolUse gate on `WebSearch`. It blocks
the session's first search, and a fourth search taken without loading this skill, then stands aside.
It exists because an always-on memory pointing here was measured at **0 loads across 112 sessions in
30 days** — resident rent on every request for a trigger that never once fired. So if you are reading
this because a search was blocked, that is the mechanism working; extend the gate rather than adding
prose. The `search-read-the-failure` memory is kept as well, deliberately: the hook only covers runs
on a machine where it is installed.

## ⚡ Pre-flight — five questions, before you press enter

All five restate rules below; none is new. If you read nothing else here, read this.

1. **The title test — would a page plausibly be TITLED with these words?** If a token only describes
   your uncertainty ("also counts toward", "which is better", "is it worth it"), cut it. If it would
   appear in a page title — an identifier, product name, named event, error literal, term of art —
   keep it however long the query gets. *(§1 "Judge waste, not length" and "Never put the answer you
   expect into the query")*

2. **Is this one question?** A conjunction in what you want means two queries. Split before issuing.
   *(§1 "Split compound queries before issuing")*

3. **Am I supplying a value I'm trying to learn?** A query containing a candidate answer retrieves
   the pages containing it and cannot falsify it. To relate two things, **name both and let the
   corpus supply the relationship**. *(§1 "Never put the answer you expect into the query")*

4. **Do I have the term of art yet?** If you can't name the thing in its own vocabulary, no wording
   works. Find a taxonomy first, harvest the words, then search. *(§2 "Aim at what is certainly
   documented")*

5. **Am I trying to prove an absence?** You cannot search for a missing feature. Enumerate or read
   the spec instead. *(§1 "You cannot search for an absence")*

**If results disappoint, do not reword first.** Read the failure shape: zero → the query; junk → the
index or your vocabulary; good pages lacking the answer → **the question**. *(§5)*

---

A search engine is an index, not an oracle. It matches your words against **words that appear on
pages**. Everything below follows from that.

The characteristic LLM failure is not verbosity. It is **aiming the query at the question instead of
at the answer**, then re-rolling the same dice and calling it iteration.

`references/tool-routing.md` holds tool-by-tool routing (your own notes go in `~/.claude/local/search-craft/`): which engines honour which
operators, per-platform native search syntax, and how to reach indexes the default tools can't.

## 0. Can you name the authority?

**Ask this first; the answer decides which half of this file applies.**

*Yes, you can name the governing body / canonical doc / upstream project.* Put the name in the query
and go — you will usually be reading the real source in one step, and most of what follows is moot.

*No, you cannot.* You are in **orientation**; §2 is your section. Don't fire the specific question
yet — you don't have the words it must be asked in.

**Both routes fail, differently.** Naming from memory is fast and fails *silently* when the memory is
wrong: you search confidently for the wrong body, find something plausible, and nothing in the
process can catch it — so spend one query confirming it governs *your* case. Reconstructing
bottom-up cannot fail that way and costs roughly 30x (measured: 3 searches vs ~90 minutes).

Third trap: an authoritative source **written for a different role than yours**. Compliance guidance
may hold your answer encoded as a filing requirement. Prefer the most authoritative source *written
for someone in your position* — usually the practitioner/extension layer that exists to translate.

## 1. Build the query

**Search the user's problem, not their words.** Keyword-extracting the request searches your
paraphrase of a question rather than the thing they need to know.

**Every term should be a word printed on the page that answers you.** Check each one: would this
appear on the answer page, or only in the question? Question-vocabulary — `recommended`, `best`,
`how to`, `rule of thumb`, `guide`, `vs`, `explained`, `forum` — doesn't just dilute, it **retargets**
the query at pages where someone else is *asking* what you're asking.

**But a thread asking your exact question is often a fine result** — plenty end in "found it" or
"here's what I ended up doing," and that reply is frequently the best answer anywhere. Don't discard
them on sight; check whether the thread resolved.

**The signal is systemic, not per-result.** If *every* search returns nothing but unresolved
people-stuck-like-you threads, that's the query, and question-vocabulary is the usual cause.

**`good` / `bad` deserve a special note.** As general query terms they pull in unfiltered garbage.
But for **sentiment** — is this tool actually liked, did people regret it — they're the right words,
and the extra noise is cheap for you to parse. Use them deliberately for opinion, not by reflex.

**Use the term of art, not a description of it.** Domain vocabulary is among the strongest measured
markers of expert search behaviour, and it's a capability you have that a novice human doesn't.

**Judge waste, not length.** Successful human web searchers average ~4.3 terms — but that
population was answering general questions. Technical work carries part numbers, quoted error
literals and multi-word proper nouns and legitimately runs longer. `Vendorco Kestrel telescope
eyepiece 2 inch barrel manufacturer` is eight words that all do work.

So audit the words, don't count them. Measured on a real research session: **1.4% stopwords, 2.3%
hedge words** — that query set wasn't padded, and shortening it would not have helped. Its real
defects were the two below. If the stopword and hedge fraction are low and every term would appear
on the answer page, a long query is fine.

**The check that decides it: would a page plausibly be TITLED with these words?** One question, no
classification needed, applicable in the second before you press enter. Measured:
`container_memory_working_set_bytes vs container_memory_usage_bytes which to use` returned nine
on-target results (a post is titled almost exactly that); `Claude Max weekly limit Opus separate
limit also counts toward overall weekly limit` returned zero first-party sources and a **confidently
wrong answer** — nothing is titled "also counts toward".

### ⚠ Never put the answer you expect into the query

    "vm.max_map_count" "65530"            → ~23 results confirming 65530
    "vm.max_map_count" "default" "65536"  → ~24 results confirming 65536

**Both "confirm."** A query containing a candidate value retrieves the pages containing that value,
so the result set cannot falsify it — and fluent confirmation of what you expected is
indistinguishable from a measurement. Use answer-shaped phrasing to **locate a source**, never to
**settle a value**. Leave the value out, let the corpus supply it, open the page and read it.

**Relationships, not just values.** The same trap catches an asserted *link* — "X replaces Y", "A
also counts toward B". Fix: **name both entities, let the corpus supply the relation.**
`grafanactl gcx` — two nouns, no claim — returned both repos, both doc sets, the deprecation notice
and the migration path.

**Severity scales with how weak the corpus is.** Run backwards, the false premise
`grafanactl replaces gcx` was *corrected* by the results, because first-party docs dominate that
index. The Claude-limits query wasn't, because its phrasing matched only commentary and no
authoritative page ranked. The chain: hypothesis-words → match the commentary genre → no
authoritative source retrieved → nothing present to contradict the premise → fluent wrong answer.
**The wording is why nothing capable of checking it was retrieved.**

**This bites hardest on dimensions and specs**, where it looks like diligence. Real example, both run:

    aquarium filter flow rate "450 L/h" → 3 vendor pages confirming 450
    aquarium filter flow rate "600 L/h" → 3 vendor pages confirming 600

Both numbers are real — they're **different ratings** (nominal pump output and flow through a loaded filter). Querying each candidate separately
retrieves evidence for each and manufactures the appearance of a contradiction, which then gets
reported as "sources disagree, unresolved."

**A number is fine when it's a constraint, not when it's the answer.** `"600 L/h" aquarium filter` is
legitimate — you've *decided* you need 600 L/h and you're filtering. `filter flow rate "450 L/h"` is the trap —
you're trying to *learn* the flow rate and you've pre-supplied it. Same syntax, opposite epistemics: ask
whether the result set could tell you that number is wrong.

**When two candidate values both look supported, that's the trap, not a finding.** Query the
**taxonomy** instead — `how aquarium filter flow rate is rated head loss` returns guides
explaining the whole system, which resolves it. A conflict between your own confirmation queries is
evidence you asked wrong, not that the world is inconsistent.

### Error strings: cut what your machine wrote, keep what the software wrote

    "FileNotFoundError: [Errno 2] No such file or directory: '/opt/app/config.yaml'"  → 0
    "No such file or directory" + the symbol that raised it                                → 22
    "containerd 2.1.4" "failed to create shim task"                                        → 0
    "failed to create shim task"                                                           → 15 (upstream issue at #1)

Strip paths, PIDs, hostnames, versions, UUIDs. Keep symbol names, error codes, config keys, message
literals — those were typed into source and are indexed.

**Quote several short invariant fragments rather than one long literal.** Even the software's own
message gets truncated, paraphrased, or partially pasted by the people writing about it, so a long
exact phrase can return zero while its pieces return plenty. Interpolated values in the *middle* of a
message also move — a line number shifts, a custom identifier differs — which breaks a single quoted
span but not the fragments either side of it.

    ✗ "SyntaxError: Could not parse frobnicate in /opt/app/custom.py line 412"
    ✓ <library> "SyntaxError" "Could not parse"

Scope with the unquoted library or product name; quote only the fixed skeleton.

### Two smaller levers

**The register of your query selects the register of your sources.** Same engine, same topic, minutes
apart: `<topic> calculator` returned eight generated tool-farms plus an unrelated calculator;
`<topic> tutorial` returned extension services and blogs; `<topic> "<term of art>"`
returned a .gov publication at rank 1 then four universities. **Wrong register in the results usually
means wrong register in the query** — a vocabulary problem, not a ranking one.

**Add a *genre* term, not a topic term**, to steer toward a kind of page: `postmortem`, `outage`,
`"in production"` for war stories; the exact config key for docs; `changelog`, `deprecated` for
version history.

**Prefer a positive term to a negation.** `Tripoli -Libya` removes pages *containing* "Libya" — which
is exactly the good ones. Say `Tripoli Greece`.

**You cannot search for an ABSENCE — and it manufactures a false positive rather than just failing.**
Nobody writes "this product has no timer", so absence isn't indexed, and negation-as-a-word doesn't
exclude ("no" is a stopword). Measured on a retail catalogue: the top result for
`<brand> "<product>" no <feature>` was the page for the variant that *has* that feature, and
`… no <feature>` / `… <feature>` returned *the same result set* — so pairing them is not the A/B it
looks like. To establish a negative, **enumerate** (category page, filter counts) or
read the spec table.

**Split compound queries before issuing, not after they fail.** Bundling several specs into one
query — `Acme tent packed weight floor area pole length` — returns whichever sub-question
ranks best and gives no signal the rest were dropped. If a query contains two nouns you'd accept
separate answers for, it's two queries.

## 2. Aim at what is certainly documented

Pages are **bundles of attributes, not answers to questions.** When the attribute you want is rarely
written down, **add** one that always is, and collect what you wanted off the same page. A part's package type is on every distributor page; its thermal resistance often isn't.

**Add, don't substitute.** Keep the distinctive entity — it carries the discrimination that keeps you
out of the generic retail/SEO cluster. The common attribute only steers you to the right page *type*.

    ✓ Acme Zeta-9 operating temperature    (entity + certain attribute)
    ✗ industrial sensor operating temperature (attribute alone → retail listings)

**When you can only DESCRIBE the thing, search where it was USED.** An image, meme, song or gadget
you saw once: its appearance is not indexed, so description-shaped queries cannot match however many
synonyms you try. Its *context* is indexed — what it replied to, which community it circulated in.

**Ask the requester for usage context, not a better description.** "What was it a reply to?" beats
"what did it look like?". Measured on a real image hunt: twelve description-shaped queries found
nothing in ~40 minutes; one detail — *it was posted as a reply in one recurring complaint thread* —
bounded it to 298 threads and found it. Two traps hit on the way: the human was asked about art style
and platform (both worthless), and a caption that felt decisive returned zero because people post the
image **bare**, with no text to match.

**The dangerous vocabulary gap is the one that reads as ordinary English.** Jargon that *looks* like
jargon gets looked up; a term of art built from common words does not. `blast radius` parses as a
physical explosion and silently becomes a wrong model, while `idempotency-key` in the same sentence got queried
within seconds. So ask **"which ordinary-looking words here might be technical?"**

**The tell is cheap: restate the ask and diff it against the original. A detail that appears in your
restatement but not the source means you mis-parsed a term of art**, not that memory slipped. Observed:
a restatement gained "unprocessed" from reading *raw* as a property of the data — pointing at the
misread word forty minutes before it surfaced on its own.

**If you don't know the term of art, no query will work** — you cannot type a word you don't have.
Stop describing the thing and go find a **taxonomy**: a category index, spec sheet, docs table of
contents, "list of" page. Harvest the vocabulary, then search properly.

## 3. Fan out in parallel — for coverage, not for ranking

### If you delegate the searching, put the constraints in the brief

A substantial fraction of research subagents never open this skill even though every one of them saw
it listed. A subagent is a fresh context that may or may not open a skill, so anything load-bearing
has to travel in the prompt you write. (The measured rate is instance data and lives in
`references/tool-routing.md`, where it can be re-measured; naming a subagent's *brief* as the fix is the durable
part.)

So **name this skill in the brief**: *"Load the `search-craft` skill before searching."* One line,
carries every rule, and never drifts out of date — unlike constraints copied into a prompt, which
stop matching the skill the moment it changes.

Evidence the brief is the channel that works: in that session the briefs carried "independently
re-check," "primary sources only" and "do not fabricate," and those behaviours show up plainly in
the output. What lived only in the skill reached two-thirds of the agents.

**One query sees a small fraction of what exists.** Two professionals given the same question overlap
~0.27 on terms and ~0.17 on results; ~61% of the relevant items they find are found by exactly one of
them. There is no "obvious" phrasing.

**Issue several genuinely different formulations at once and take the union.** Cheap for you,
laborious for a human — it's what browser tabs are for. Vary along **two** axes:

> **Measured, and it holds:** across 39 real research runs the median agent issued **~6 searches
> before opening a single page** (`SSSSSSSSSSSSFF` is the typical shape), and only 9 of 39 opened a
> page after one search. The behaviour this section asks for is one of the few that is already
> reliably happening — you are reading listings across the whole variant set before committing to an
> article, which is exactly the point.

- **Register** — vendor term vs symptom vs error string vs community slang vs academic phrasing.
- **Specificity** — deliberately run one broader and one narrower than your best guess. You don't
  know which rung of the ladder the answer is written at.
- **Abbreviated vs spelled out** — `k8s` and `kubernetes`, `MTU` and `maximum transmission unit`. Some communities abbreviate and some don't; both sets are legitimate
  and they overlap less than you'd expect. This is the cheapest variant axis there is.

Refine the whole set together rather than perfecting one query before starting the next.

**Don't write `(a OR b) AND (c OR d)`.** That's machinery for unranked Boolean corpora and is inert
against a web ranker. The web translation of "OR within a concept" *is* this section: separate
queries, unioned after.

**Don't rank by agreement between variants on the same engine.** Fusing multiple runs of one system
measures worse than taking the best single run. Agreement across genuinely *different indexes* is the
validated case. Never let agreement raise your confidence in a claim — judge each result on its
merits.

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

## 6. Quote multi-word entities, never whole queries

Quote to **subtract noise you have already seen**, not to guess at precision.

    Acme Kestrel Studio settings        → also a restaurant, an artwork, an album
    "Kestrel Studio" Acme settings      → noise gone, official wiki surfaces

Wrapping a long query in quotes reliably returns zero — you've asserted a verbatim phrase no page
contains. Quotes earn their place on multi-word proper nouns and exact strings; a quoted single
common word does nothing.

**Operators buy far less than they appear to.** In controlled testing `AND` and `+` had no measurable
effect, `OR` made one engine worse, and only quoted phrases helped — on some engines and not others.
Reaching for operators mid-task is a signal you're struggling. Which operators work on a given engine is in
`references/tool-routing.md`; they are per-engine dialects, and an unsupported one fails silently in one of two
directions — zero results, or no effect at all.

## 7. Route to the index before crafting the query

Switching index beats improving the query, repeatedly. Ask "where does this kind of answer *live*?"
before "what words do I type?"

| question | index |
|---|---|
| how do I call this poorly-documented API? | code search — check which engine you're on (`references/tool-routing.md`) |
| does real code use this flag, and how? | `git grep` on a local clone beats every hosted code search |
| is this a known bug? | the project's issue tracker, with its qualifiers |
| exact error string | a lexical index, not a reworded web search |
| CLI flag semantics | the man page |
| long-lived OSS design rationale | the mailing-list archive |
| what do practitioners think? | HN; Reddit via the route in `references/tool-routing.md` |
| official behaviour / defaults | the vendor's own docs or wiki — go there directly |
| a table of per-item values | find the table, fetch it, read it — don't ask search for one row |

**Retrieve-then-grep beats query-by-query.** When one thread or archive plainly *is* the topic, pull
the whole thing and search it locally.

**Some communities have no public index at all** (chat-first projects on closed platforms). That's a gap, not a
query problem — say so instead of grinding.

## 8. Triage in two phases, then judge

**Don't open the first result and read it.** That's serial, expensive, and anchors you on whatever
ranked first.

1. **Scan the listings** — titles, URLs, snippets, dates — across all your parallel result sets.
   Nearly free, and where most of the judgement happens. You're identifying the **venue**.
2. **Fetch several promising candidates in one batch.**
3. **Then** read and synthesize across them.

This is **click restraint**, and it's what separates professional fact-checkers from PhD historians in
the one controlled study of the skill. Your economics beat a human's here: ten snippets cost you
almost nothing.

**Lateral reading: never judge a source's reliability from that source's own pages.** Open a second
tab and see what others say about it. In the same study, fact-checkers scored a perfect 2.0 judging a
disguised advocacy site; historians 0.7, students 0.16 — and most failed *because* they read the page
closely and applied checklist criteria (domain, tone, citations, an "about" page). Those are
production-budget signals, cheaply faked, and you are more susceptible to polished surface
credibility than the historians were.

Ranking is not authority — ranked-first is routinely a content farm. Prefer primary sources: vendor
docs, the project wiki, the repo, the spec, the changelog. Watch for scraped-StackOverflow and
SEO-slop domains. A synthesized answer summary blends sources of different vintages and states the
blend confidently — trust the links, verify the prose. And search skill does not substitute for
domain knowledge: if you don't understand the domain you won't recognise the right answer in front of
you.

## 9. Never bake the current year into a query

Appending a year is a known, prompt-patched LLM defect. It doesn't mean "recent" — it filters for
pages containing that literal string, discarding current pages that don't and promoting stale pages
that do. Use the engine's recency filter. Same class: don't append `reddit`, `forum`, or `github` as
bare words; use `site:`, a bang, or go to that index directly.

## 10. Site-native search is a different game

A site's own search box is usually a catalog matcher over titles and tags, not a semantic index.

**On shopping catalogs the pollution is inverted.** The problem isn't that your query is too wordy —
it's that the *documents* are, because sellers keyword-stuff titles. So adding terms matches more
junk, not less, and quoting is unreliable because your phrase appears inside stuffed titles of
irrelevant products.

**Read the facet rail before writing the query:**

- constraint is a **facet** → drop it from the query, filter instead
- constraint is **indexed text** → keep it in the query
- constraint is **neither** → the site can't answer; read listings by hand, or leave for a parametric
  supplier

Facet coverage varies wildly by category on the same site. Tested: an over-specified
query (`Acme umbrella "no vent" canopy`) had 2 of 10 correct — and *removing* the spec made it 0 of 10, because that category has no size
filter. "Shorten and filter" is only right when the filter exists.

**Check the field exists at all.** Searching a brand on a platform that stores no brand field cannot
work, however phrased. **Many catalog engines never return zero** — gibberish can return four figures
— so a non-empty result set is not evidence anything matched.

**Native search for facets; `site:` for text.** Native search owns the filters and pagination but
typically indexes title and tags only, so anything in a description is reachable only via a general
engine. Code and forum platforms are the opposite: real syntax, and precision pays.

## 11. Close the loop by testing, not just by reading

**A search result is a hypothesis. Where the claim is executable, execute it.** Running `--help`, a
one-liner in a scratch dir, `man`, `kubectl explain`, a `curl -I`, a throwaway container — any of
these settles in seconds what no amount of source-triage can, and it inverts the cost model: instead
of judging three blog posts of unknown vintage, run the thing once against *your* versions.

This is also the strongest answer to the failure modes above. A flag that was removed two releases
ago, a config key renamed upstream, an answer written for a different major version — all read as
authoritative and all die instantly on contact with a shell.

**And the test feeds the next round.** The real error message you get back is the best search term
available: it's the exact literal from the source, unpolluted by your paraphrase. Doing and searching
aren't sequential phases — a failed attempt is a vocabulary source (§1, §4).

Prefer the local, reversible check. Don't run a destructive or outward-facing command to satisfy
curiosity — but for the ordinary "does this flag exist, does this syntax parse, does this actually
do what the page says," testing beats reading every time.

## 12. Before reporting what you found

- **Run a known-item check.** Name 5–10 documents the query *must* return, then run it. If they're
  missing, the query is broken — not the corpus. The only completeness test here that produces a
  signal rather than a feeling.
- **A zero is not a finding until the probe is proven able to return non-zero.** A broken query, an
  invalid operator, a suspended engine and an empty corpus all look identical. (The same rule for
  shell and test probes: `shell-footguns`, `verification-gate`.)
- **HTTP 200 is not success.** Anti-bot interstitials and proof-of-work challenges return 200 with
  plausible bytes.
- **A quoted-phrase hit is not proof the phrase is on the page** — engines match meta tags, ALT text
  and rendered content you can't see. Fetch and check.
- **Reading the bytes differs from reading a summary of the bytes**, and only the first can be quoted.
  A fetch-and-summarize step fabricated a quotation during this skill's own research.
- **"Not in the excerpt" is not "not on the page."** A fetch that succeeds and then summarizes will
  truncate a long docs page, and the missing section reads exactly like a missing answer — which sends
  you back to reword a query that was already correct. The tell is the summarizer saying so out loud
  ("the content cuts off before…", "not included in the excerpt"). **Treat that as a retrieval
  failure, not a search failure:** re-fetch the page at its anchor, or fetch and grep it, before
  touching the query. This is the same retrieve-then-grep move as for threads and archives (§7),
  applied to a single long page.
- Distinguish **"I verified"** from **"a result asserted."** Say which route produced the answer, and
  say plainly when something was unreachable rather than implying you covered it.
