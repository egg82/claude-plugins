# Judging a rewrite

Whether a revision reads as human and whether it is good, and who decides each.

## Why the writer can't judge

**The model that wrote a line cannot hear its register.** Neither can a fresh agent of the same model, which shares
the ear and prefers it: judges recognise their own family's text above chance and score it higher (measured,
Panickssery, Bowman and Feng, NeurIPS 2024, https://arxiv.org/abs/2404.13076), and they reward smooth, predictable
prose whoever wrote it (measured, snippet, https://arxiv.org/abs/2410.21819), which is the quality being removed.
Models flag AI-written fiction with precision around 0.42 to 0.46 (measured, Chakrabarty et al.,
https://arxiv.org/abs/2409.14509), and model judges don't track experts on holistic quality (measured, abstract only,
https://arxiv.org/abs/2309.14556) or on humour (`humour.md`).

So your own reread, or a subagent's, is a draft check against the tells list. It never counts as the verdict, and a
report should not say a rewrite "reads human" on that basis.

## Who judges: two questions, two panels

**"Can you tell a model wrote this?" Readers who use LLMs heavily for writing.** On non-fiction articles of 300 to
1,000 words they are the best detectors measured: on 300 such articles from GPT-4o, Claude 3.5 Sonnet and o1-Pro, a
majority vote of five caught 99.3% with no false positives, and kept catching text run through a humanizer.
Individual experts ranged from 59% to 97%. Readers who rarely use LLMs scored at chance (56.7% caught, 51.7% of
human articles wrongly flagged) while feeling confident (measured, Russell, Karpinska and Iyyer, ACL 2025,
https://arxiv.org/abs/2501.15654). Shorter text was not tested, and nothing else validates a detector there, human
or machine. For short lines use the same panel on batches as the best available probe, and treat its verdict as
untested. Verse and children's text name their own panels in their references; UI uses the reader tests below.

**"Is it good of its kind?" Readers of the genre or venue,** blind, old against new. Readers who don't use LLMs
are fine here, and the person commissioning the text can rate blind batches as a taste check. For instructions,
UI text, plain-language and explanatory text, "good" means understood and acted on, which the tests below measure
better than a preference vote.

For both panels:

- **Batches, never one piece,** since model writing shows its sameness across texts (SKILL.md). Show twenty pairs.
- **No labels.** Told which passage was human, both people and LLM judges preferred it, the models about 2.5 times
  as strongly; blind, both were near indifferent (measured, https://arxiv.org/abs/2510.08831).
- **Randomise per reader** which version is A, vary the order, and map back before counting. No sample-size guidance
  for human raters was found.
- **Ask the right question:** which version says what it means, and which a person wrote. "Which do you like"
  rewards fluency, the model's strength.
- **Self-reported LLM use is unverified.** No recruiting route verifies it (policy,
  https://docs.prolific.com/documentation/core-concepts/finding-the-right-participants); ask and record the answer.

## Testing non-fiction and UI text with readers

These measure whether a reader understands and acts, not who wrote it; no source ties them to detecting model text
(null result of searches). Run them with the real audience: a low score can mean missing background, not bad
writing.

- **Cloze test.** Blank every fifth or sixth word of a passage of 150 words or more; each reader fills the blanks
  alone; accept synonyms. An average of 60% or more is reasonably comprehensible for that audience (practitioner,
  NN/g, https://www.nngroup.com/articles/cloze-test-reading-comprehension/); the US FEC targeted 50% and scored 65
  to 98% (practitioner, GDS blog,
  https://gds.blog.gov.uk/2016/04/06/guest-post-looking-at-the-different-ways-to-test-content/). Suits technical
  content: finance, regulation, health. No sample size beyond "as many as possible".
- **Highlighter test.** Readers mark what is clear in one colour and confusing in another (or "makes me feel
  confident" against "less confident"), then you ask why; compare across sessions (policy, Digital.gov,
  https://digital.gov/guides/research-collaboration/testing/content).
- **Moderated probes,** 20 to 30 minutes with a facilitator: summarise it in your own words without rereading
  (understood if they can); "What does the word X mean to you?" (finds jargon); "Imagine a person said these words
  to you. Who would that person be?" (tone, and a check for a generic assistant voice). Unmoderated sessions are
  discouraged for content because people rush (practitioner, NN/g,
  https://www.nngroup.com/articles/testing-content-websites/).
- **Preference tests only paired with "explain it in your own words",** so a person judges understanding (GDS blog,
  above).
- **Readability formulas don't measure comprehension:** they miss word order and familiarity, and rewriting to lower
  the grade score did not raise understanding (practitioner, snippets; `plain-language.md`).
- **A five-second test measures first impressions of a page's look,** not comprehension (measured, snippet, Gronier
  2016).
- **A/B tests say which version won, never why,** and need traffic: the rules of thumb behind them come from
  experiments of hundreds of thousands to millions of users (measured, Kohavi et al., https://exp-platform.com/rules-of-thumb/).
  Before reading any lift, check the observed split matches the planned one; a mismatch means a data fault and the
  result can't be trusted (measured, Fabijan et al., KDD 2019,
  https://www.lukasvermeer.nl/publications/papers/2019/07/25/diagnosing-sample-ratio-mismatch-in-online-controlled-experiments.html).
  A surprising win is a reason to check validity before shipping (Twyman's law). A small site or game rarely has
  the traffic; use the tests above instead.

## Where to find readers

- **The venue's or genre's own community.** For fiction and games: interactive-fiction forums, where authors recruit
  free beta readers (practitioner, snippet,
  https://intfiction.org/t/beta-testers-wanted-for-where-is-mr-beaver/75890), and writing critique groups that bar
  AI work (policy, snippet, e.g. https://www.bsfwriters.com/policies--procedures/bsfws-ai-policy-be-pro-human). For
  product, support or plain-language text: the product's actual users, and for easy-read text, people with
  intellectual disabilities, whose review is what separates easy-read from merely simplified (`plain-language.md`).
- **Feedback threads where the text will live:** readers who know the form but are not screened for LLM use.
- **Paid panels.** Prolific has no AI-use filter; screen with a custom question and a small screen-out payment.
  Minimum pay is GBP 6 an hour, recommended GBP 9, on actual completion time, plus a platform fee (policy,
  https://researcher-help.prolific.com/en/articles/445266-how-much-should-i-pay-participants). Heavy LLM users for
  the detection panel are easier to find this way than people who avoid LLMs.
- **Start free, then pay** if free readers are too few.

## Screens before human readers

Human readers are slow and scarce, so run cheap screens first and send readers only what survives. Screens only
reject: clearing every screen means the draft is ready for readers and says nothing about whether it reads human.
The order: tells list, other-family model flaggers, detectors, then blind human readers.

**Model flaggers.** Use a different family from the writer, under these conditions:

1. **Prove it on known-human controls first.** Give it a mixed, unlabelled batch of known-human text in the same
   form and register and known model text. If it can't sort them well above chance, its flags are noise for this
   kind of text; re-prove when the kind changes. `scripts/flagcheck.py` measures this separation for a grader. A
   prompted GPT-4o detector managed 78% caught with 10.7% false positives even on whole articles (measured, Russell
   et al., above), and no study was found of one family judging another's style, so the proof is required, not
   ceremony.
2. **Pairs beat single lines.** Judging one text alone, GPT-4 sat at chance on its own output; separating human from
   model text in a pair was its strongest setting (measured, Panickssery et al., above). Put a known-human line in
   the pair.
3. **Both orders, count only stable verdicts.** After swapping order, GPT-4 stayed consistent 65% of the time,
   GPT-3.5 46%, Claude-v1 24% (measured, snippet, Zheng et al., https://arxiv.org/abs/2306.05685). Length-match the
   pair.
4. **No labels, several families, aggregated.** A rubric of yes/no items does not remove self-preference, and
   several judges reduce it without removing it (measured, abstract,
   https://www.alphaxiv.org/abs/2604.06996).
5. **Ask it to quote the giveaway phrase,** never to score or approve. A quoted span can be checked by a person; a
   score cannot. Treat what it returns as leads, and rewrite by hand.

**Measured on short lines** (`scripts/flagcheck.py`; human lines against Claude Sonnet lines, version unrecorded,
for the same slots; `evidence/flagcheck-results.txt`): on well-known game lines Gemini 3.1 Pro caught 52% of model
lines at 10% false positives, every catch an aphoristic close or lyrical turn. On obscure human text in game, prose,
chat and UI registers against plainly written Claude lines, neither Gemini 3.1 Pro nor GPT-5.2 separated the two in
any register (Gemini 22% caught at 22% false positives; GPT-5.2 26% at 39%). So these graders detect the flourish
(`llm-tells.md`, the turn) and not authorship: use one to find flourishes, never as evidence that short text reads
human.

**Automatic detectors.** No detector is validated on one- or two-sentence text. All four academic detectors in one
study degraded as text shortened and stayed "very limited" under 50 words (measured,
https://arxiv.org/abs/2508.08096). Plain, simple human writing is the false-positive trap: seven detectors flagged
61% of non-native English essays as AI (measured, 2023 detectors, https://arxiv.org/abs/2304.02819), and short game
and UI lines are plain by design. On 300 modern articles, Pangram (98% caught, 2% false positives) and GPTZero (85%,
0.7%) were strong; Fast-DetectGPT, Binoculars and RADAR were weak, and worse on humanized text (measured, Russell et
al.). Pangram's vendor says it returns no prediction under 50 words while an independent paper says it "largely
holds up" there (practitioner, https://www.pangram.com/de/blog/third-party-pangram-evals; measured, snippet,
https://www.nber.org/papers/w34223). So run a detector only after it passes known-human lines of the same kind; a
clean score is weak evidence, a confident flag is worth a rewrite.

**Two tiers, measured locally** (`evidence/flagcheck-results.txt`; Claude Sonnet, 15 to 40 items per condition, two
human control sets, pre-1929 fiction and 2018 Reddit fiction). Visible style can be brought to passing: against
modern amateur prose Gemini could not separate Claude's short lines from people's at all, and the knowing-narrator
and appended-beat tells are fixable by hand. Paragraph-level statistics did not move: Pangram caught 80 to 100% of
Claude's ~100-word paragraphs under every prompt-side method tried (default, avoidance rules, a one-quirk budget,
editing the draft, continuing real human sentences, keeping the best of five by another grader) and flagged no human
paragraph. Selecting candidates with one grader fools that grader only, and Gemini 3.1 Pro drafting the same
paragraphs was caught 14 of 15 times too. Plan for this: text that a strong detector
may check needs a human rewrite of its sentences, not a better prompt; whether a light human edit is enough is
untested.

## The final check

**People are the bar; detectors are a ceiling.** The goal is that a reader cannot tell. A statistical detector such
as Pangram is a proxy that sits above that bar (it caught paragraphs no prompting moved, above), so passing readers
while a detector still flags the text is success; chasing the detector is optional work for text a detector will
actually check. The strongest readers measured use LLMs heavily; a rater who reads charitably misses most of it (judgement, two raters, `evidence/`).

For prose of a few hundred words: readers who use LLMs heavily, five of them, majority vote, blind, on a batch. For
verse and children's text, the panel that reference names; for UI, the reader tests above; for other short lines,
the same five-reader panel on batches. No detector, human or machine, is validated on short text, so report a short
text's result as a reader check, never as proof that it reads human.
