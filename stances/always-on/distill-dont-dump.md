---
name: distill-dont-dump
description: Write docs as a distilled record (decision, not deliberation); lead with what-it-is-and-why; point to depth rather than inlining; don't leak process residue
metadata:
  type: feedback
---

LLM-written docs read like a dump of the conversation that produced them: deliberation instead of
the decision, process residue (dates, ticket/PR numbers, status amendments, notes aimed at the
authoring agent), uniform low density that defeats skimming, and an opening at maximum density
because the model already holds context a stranger lacks. The reader shares none of it.

State the thing once, lead with what-it-is-and-why, point to depth rather than inlining it. An ADR is
a distilled decision, not a build journal; a docstring is one line plus a pointer; a README is for
humans.

**Don't write a count the reader can see or nothing will contradict** — it goes stale silently (one
drifted across five files). Keep a number only where it *is* the argument, beside the thing it counts.
Same for an enumeration of files or links. **When a summary word justifies a decision, write the
checkable property instead** — an adjective about a set is a claim about whoever joins it later.

Pairs with [[prefer-subtraction]]; the `doc-cold-read` skill catches these leaks.
