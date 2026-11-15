# Triage, testing, and reporting (§8, §11, §12)

Load when judging results and sources, when a claim is executable, and before stating what you found.

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
