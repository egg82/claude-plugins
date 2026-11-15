---
name: search-craft
description: "How to construct, diagnose and iterate a web search query so it finds the answer. Use BEFORE any web search — WebSearch, SearXNG, or a site's own search box — and again whenever results disappoint, especially before rewording a query you already tried."
---

# Search craft

**What routes you here:** `hooks/search-craft-gate.sh` blocks the session's first `WebSearch` (and a fourth
without this loaded). A block means the mechanism is working; extend the gate, not prose
(`references/gate-rationale.md`).

## ⚡ Pre-flight — five questions, before you press enter

All five restate rules below; none is new. If you read nothing else here, read this.

1. **The title test — would a page plausibly be TITLED with these words?** If a token only describes
   your uncertainty ("also counts toward", "which is better", "is it worth it"), cut it. If it would
   appear in a page title — an identifier, product name, named event, error literal, term of art —
   keep it however long the query gets. *(§1 "Judge waste, not length" and "Never put the answer you
   expect into the query", in `references/building-queries.md`)*

2. **Is this one question?** A conjunction in what you want means two queries. Split before issuing.
   *(§1 "Split compound queries before issuing")*

3. **Am I supplying a value I'm trying to learn?** A query containing a candidate answer retrieves
   the pages containing it and cannot falsify it. To relate two things, **name both and let the
   corpus supply the relationship**. *(§1 "Never put the answer you expect into the query")*

4. **Do I have the term of art yet?** If you can't name the thing in its own vocabulary, no wording
   works. Find a taxonomy first, harvest the words, then search. *(§2 "Aim at what is certainly
   documented", in `references/orientation.md`)*

5. **Am I trying to prove an absence?** You cannot search for a missing feature. Enumerate or read
   the spec instead. *(§1 "You cannot search for an absence")*

**If results disappoint, do not reword first.** Read the failure shape: zero → the query; junk → the
index or your vocabulary; good pages lacking the answer → **the question**. *(§5, in
`references/iterating-and-failure-shapes.md`)*

---

A search engine is an index, not an oracle. It matches your words against **words that appear on
pages**. Everything below follows from that.

The characteristic LLM failure is not verbosity. It is **aiming the query at the question instead of
at the answer**, then re-rolling the same dice and calling it iteration.

`references/tool-routing.md` holds tool-by-tool routing (your own notes go in `~/.claude/local/search-craft/`): which engines honour which
operators, per-platform native search syntax, and how to reach indexes the default tools can't.

Section numbers (§0–§12) are stable: the companion files and the references cite them. Each rule below
is the short form; the reference named at the end of each holds the examples, measurements and mechanism.

## 0. Can you name the authority?

Ask first. **Yes** (you can name the governing body / canonical doc / upstream project): put the name in the
query and go. **No**: you are in orientation, so don't fire the specific question yet; §2 is your section.
Naming from memory fails *silently* when the memory is wrong, so spend one query confirming it governs
*your* case; bottom-up reconstruction costs roughly 30x (3 searches vs ~90 minutes). Beware an authoritative
source written for a different role than yours. *(`references/orientation.md`)*

## 1. Build the query

- **Search the user's problem, not their words**; every term should be printed on the answer page.
  Question-vocabulary (`best`, `how to`, `vs`, `forum`) **retargets** at people asking. Judge waste, not length.
- **⚠ Never put the answer you expect into the query.** `"vm.max_map_count" "65530"` returned ~23 results
  confirming 65530; `… "default" "65536"` ~24 confirming 65536. Use answer-shaped phrasing to **locate a
  source**, never to **settle a value**. Same for asserted relationships: name both entities.
- **Error strings: cut what your machine wrote** (paths, PIDs, versions), **keep what the software wrote**;
  quote short invariant fragments, not one long literal.
- Wrong-register results mean a wrong-register query; add a *genre* term, prefer a positive term to a negation.
- **You cannot search for an absence**; enumerate or read the spec. **Split compound queries** before issuing.

*(`references/building-queries.md`)*

## 2. Aim at what is certainly documented

When the attribute you want is rarely written down, **add** one that always is, never substitute. If you can
only DESCRIBE the thing, search where it was USED (12 description queries failed in ~40 min; one usage detail
bounded it to 298 threads). Restate the ask and diff it against the original to catch a mis-parsed term of art
(an ordinary word with a technical meaning). No term of art: find a taxonomy first. *(`references/orientation.md`)*

## 3. Fan out in parallel — for coverage, not for ranking

One query sees a small fraction of what exists (two professionals overlap ~0.27 on terms, ~0.17 on results).
Issue several genuinely different formulations at once and take the union, varying **register**,
**specificity** and **abbreviated vs spelled out**. No `(a OR b) AND (c OR d)`; don't rank by agreement
between variants on one engine. **If you delegate the searching, name this skill in the brief**: *"Load the
`search-craft` skill before searching."* A subagent is a fresh context and many never open a skill.
*(`references/fan-out-and-delegation.md`)*

## 4. Iterate on what you READ, not on what you imagined

Terms harvested from a document you just read are new information; synonyms invented in your head re-roll the
same dice. Change one thing, then look. *(`references/iterating-and-failure-shapes.md`)*

## 5. Read the failure shape instead of rewording

| symptom | broken | move |
|---|---|---|
| **Zero / near-zero** | the **query** | drop terms; unquote; confirm the probe *can* return non-zero |
| **Junk, off-topic, wrong register** | the **index** or **vocabulary** | switch index; harvest the term of art |
| **Good on-topic results that don't contain the answer** | the **question** | stop and reframe |

Detect cycling (adding/removing *concepts* is productive; swapping *words* is not). **Abandon a poisoned
line**: name the contaminated terms and stop using them. **Cap it**: past ~5 reformulations on a fact-finding
task, change medium (switch index, fetch a source, or ask). "Nothing relevant exists" is an inference people
are measurably bad at; spend one cheap external check. *(`references/iterating-and-failure-shapes.md`)*

## 6. Quote multi-word entities, never whole queries

Quote to subtract noise you have already seen. A quoted long query returns zero. Operators buy far less than
they appear to (`AND`/`+` no effect, `OR` worse on one engine); per-engine dialects are in `references/tool-routing.md`.
*(`references/building-queries.md`)*

## 7. Route to the index before crafting the query

Switching index beats improving the query: ask where this kind of answer *lives* before what to type.
Retrieve-then-grep beats query-by-query. *(`references/index-routing-and-site-search.md` holds the table)*

## 8. Triage in two phases, then judge

Scan listings across all result sets, fetch several candidates in one batch, then read and synthesize. Click
restraint. **Lateral reading**: never judge a source from its own pages. Ranking is not authority; prefer
primary sources; trust a synthesized summary's links, verify its prose. *(`references/triage-testing-and-reporting.md`)*

## 9. Never bake the current year into a query

It filters for pages containing that literal string. Use the engine's recency filter. Same class: don't append
`reddit`, `forum` or `github` as bare words; use `site:`, a bang, or go to that index. *(`references/building-queries.md`)*

## 10. Site-native search is a different game

A catalog matcher over titles and tags. Read the facet rail first: facet means filter, indexed text means keep
it in the query. Many catalog engines never return zero. *(`references/index-routing-and-site-search.md`)*

## 11. Close the loop by testing, not just by reading

A search result is a hypothesis; where the claim is executable, execute it (`--help`, a one-liner in a scratch
dir, `kubectl explain`, `curl -I`). The real error message is the best next search term. Prefer local,
reversible checks. *(`references/triage-testing-and-reporting.md`)*

## 12. Before reporting what you found

- Run a **known-item check**: name 5–10 documents the query must return.
- **A zero is not a finding** until the probe is proven able to return non-zero.
- **HTTP 200 is not success** (anti-bot interstitials); a quoted-phrase hit is not proof the phrase is on the page.
- **Only the bytes can be quoted**, not a summary of them (a fetch-and-summarize step fabricated a quotation here).
- **"Not in the excerpt" is not "not on the page"**: a retrieval failure, not a search failure; re-fetch at the
  anchor or fetch and grep before touching the query.
- Say "I verified" vs "a result asserted", and say plainly when something was unreachable.

*(`references/triage-testing-and-reporting.md`)*

## Which reference

| situation | file |
|---|---|
| composing or auditing a query: terms, expected-answer trap, error strings, quoting, operators, year (§1, §6, §9) | `references/building-queries.md` |
| can't name the authority or the term of art; rarely-documented attribute; can only describe the thing (§0, §2) | `references/orientation.md` |
| issuing variants; briefing a subagent to search (§3) | `references/fan-out-and-delegation.md` |
| results disappoint; rewording; cycling (§4, §5) | `references/iterating-and-failure-shapes.md` |
| picking where to search; site-native or catalog search (§7, §10) | `references/index-routing-and-site-search.md` |
| judging sources; testing a claim; before reporting (§8, §11, §12) | `references/triage-testing-and-reporting.md` |
| engines, operators, tool routes | `references/tool-routing.md` (your own notes: `~/.claude/local/search-craft/`) |
