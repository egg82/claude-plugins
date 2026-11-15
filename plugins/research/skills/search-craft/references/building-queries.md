# Building the query (§1, §6, §9)

Load when composing or auditing a query: term choice, the expected-answer trap, error strings, quoting,
operators, the year trap. Also where the pre-flight card's questions 1, 2, 3 and 5 are argued in full.

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

**This bites hardest on dimensions and specs**, where it looks like diligence. Illustration:

    garden pump flow rate "450 L/h" → 3 vendor pages confirming 450
    garden pump flow rate "600 L/h" → 3 vendor pages confirming 600

Both numbers are real — they're **different ratings** (nominal pump output and flow through a loaded filter). Querying each candidate separately
retrieves evidence for each and manufactures the appearance of a contradiction, which then gets
reported as "sources disagree, unresolved."

**A number is fine when it's a constraint, not when it's the answer.** `"600 L/h" garden pump` is
legitimate — you've *decided* you need 600 L/h and you're filtering. `filter flow rate "450 L/h"` is the trap —
you're trying to *learn* the flow rate and you've pre-supplied it. Same syntax, opposite epistemics: ask
whether the result set could tell you that number is wrong.

**When two candidate values both look supported, that's the trap, not a finding.** Query the
**taxonomy** instead — `how garden pump flow rate is rated head loss` returns guides
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

## 9. Never bake the current year into a query

Appending a year is a known, prompt-patched LLM defect. It doesn't mean "recent" — it filters for
pages containing that literal string, discarding current pages that don't and promoting stale pages
that do. Use the engine's recency filter. Same class: don't append `reddit`, `forum`, or `github` as
bare words; use `site:`, a bang, or go to that index directly.
