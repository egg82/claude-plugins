---
name: confluence-kb-docs
description: "Write good wiki / Confluence docs — how-tos, troubleshooting/KB articles, system overviews, reference pages — and publish them via the confluence MCP tools if present. Starts from who lands on the page and what they want; BLUF, fix first, depth at the bottom. Use when writing, revising or publishing any wiki/KB doc, or turning a fix, procedure or system into a page. NOT auditor/compliance docs."
---

# Writing genuinely good wiki / KB docs

A general-purpose skill for high-quality knowledge-base pages (Confluence or any wiki). The single
most important move is up front, below. (Publishing assumes the confluence MCP tools are connected;
if they aren't, everything about drafting still applies -- write the page to a `.md` file and the
user places it.)

## Start with the audience -- this drives everything else

Before drafting, answer these. The whole shape of the page falls out of the answers.

1. **Who is the reader?** Not always an end user -- it can be an operator/power user (a page
   describing a system, a new tool, an internal process), a developer who isn't strong with the
   underlying tech, or a mix. Write for the primary reader first; serve the secondary one in a
   clearly separated section. Jargon that's precise and welcome for an operator is noise for an end
   user.
2. **How did they land here?** A **search query** (they have a problem in hand, want it solved)
   reads very differently from **an instruction** ("go read this / do this") or **onboarding/
   browsing** (learning a system, not yet stuck). Search-arrivals need the answer at the top and
   their exact error text visible so they know they're in the right place. Instructed readers need
   the steps in order. Learners need the concept before the commands.
3. **What do they want, and how fast?** Most people with a broken thing want to **be done and move
   on** -- give the fix immediately. *Some* are **curious why** -- serve them too, but below the
   fold so they never slow the first group. A reference reader wants a scannable table; a learner
   wants the mental model.

The fix-first / depth-at-the-bottom skeleton below serves a mixed-intent audience without
compromise: the in-a-hurry reader gets the fix at the top and leaves; the curious reader scrolls to
"why this happens." When a page has a *single* intent (pure reference, pure onboarding) the shape
changes -- let the audience answer dictate it, don't force the skeleton.

### Don't guess -- gather the answers

If audience or system facts aren't clear from the request, **find out before drafting**:

- **Ask the triggering user** about how it works, what it's for, and who the page is aimed at. Make
  questions easy to answer -- offer concrete options with a recommendation, not open-ended prose.
- **Read the project yourself** when the system is in a repo you can reach -- scripts, configs,
  READMEs, `--help`. Same verify-before-writing discipline as step 1 of the workflow: confirm
  commands, flags, paths, behavior against ground truth. Reading the code often answers the audience
  question too (who runs this, how they invoke it).

Prefer reading the project for *facts you can check*, asking the user for *intent and audience you
can't*.

## The workflow that works

0. **Analyze the audience (above), then pin destination and scope.** Standalone page vs. a section
   inside a bigger page changes everything: a section gets an H2 (not H1), no standalone intro
   blockquote, leaner framing. Confirm "its own page or part of one, and where does it sit?" before
   drafting.
1. **Verify before writing.** Confirm every command, flag, path, and behavior against the real
   scripts / configs / images -- don't trust summaries or memory blind. If a claim is testable, run
   a no-side-effect probe. Tested ground truth beats expectation, including the user's; surface
   contradictions.
2. **Draft to a `docs/<name>.md` file first** (keep the H1). It's the review artifact and the
   lasting source of truth. Don't publish yet.
3. **Iterate note-by-note with the user**, editor-style. Expect framing/tone notes, not just fact
   corrections.
4. **Scrub conversational leakage** -- read the whole draft cold and delete anything that answers
   the chat rather than the reader (dates, ticket numbers, "as we discussed", process residue).
   Then run `writing-craft`'s editing pass (`references/editing-pass.md`) over the prose for model tells.
5. **Adversarial cold read, before publishing.** Spin up 2-3 subagents with **no knowledge of this
   conversation** and have them read the finished draft cold. Give each only the draft text plus the
   one-line declared audience & intent. Give them *different lenses*: the target reader following it
   cold (where do they stall?); a skeptical fact-checker (what's asserted but unverified?); and
   optionally a wrong-audience reader (does the page signal who it's for?). Then **you weigh each
   finding and apply only the valid ones** -- a cold reader lacks context and will raise some wrong
   criticism; don't reflexively accept or dismiss. (This is the `doc-cold-read` skill's job -- use
   it.)
6. **Publish only on an explicit "send it."** With the confluence MCP tools: create under the right
   parent, add a table-of-contents macro, strip the duplicate H1, add labels, cross-link siblings.
7. **Keep the repo `.md` in sync** with what's published.

## Non-negotiables

- **Plain language up top, depth at the bottom** (calibrated to the audience -- an operator
  reference can be technical throughout; an end-user how-to cannot). Keep deep jargon in a "For
  power users" section, deepest topic last.
- **No condescension.** State the capability; don't judge the reader's instincts or past choices.
- **Don't disparage a coexisting alternative or past tooling.** Where two supported options exist
  they are different-but-equal -- never old/new/legacy/replaces/migrating.
- **Minimize emoji.** Heavy emoji is a tell that a page was machine-written and it's hard to read.
  Ceiling: at most a single page icon, plus the occasional warning marker on a genuinely destructive
  step. None in headings, bullets, or prose. When in doubt, none.
- **Accuracy is the bar.** Verified behavior over what "should" be true; surface contradictions
  rather than smoothing them over.
- **Cold-readable.** Every line must make sense to a first-time reader with no memory of the
  conversation that produced it.
