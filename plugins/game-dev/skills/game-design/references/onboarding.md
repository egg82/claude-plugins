# Onboarding and teaching mechanics

How to teach a game's or app's mechanics with little or no tutorial. Sources: `evidence/onboarding.jsonl`. Several
of the best primary talks (Thorson, Hempuli, Blow, Subset) were unreachable, so those games appear only through
commentary.

## Decide per mechanic whether to teach it at all

**A tutorial pays only for mechanics a player cannot discover by trying.** Eight tutorial designs across three games
and 45,000+ players: tutorials raised play time up to 29% (progress up to 75%) in the most complex game, Foldit, and
did nothing measurable in the two simpler ones. Instructions at the moment of need beat an up-front manual in Foldit
(+16% play time, +40% progress) and did nothing elsewhere. Restricting freedom to focus attention showed no benefit;
on-demand help helped Foldit, did nothing in one game and hurt in another. Authors: players of experimentable games
"seem to learn more from experimentation than from reading text" (research, Andersen et al., CHI 2012).

- Simple mechanics get no teaching. The one hard mechanic gets an isolated place to practise it: an active tutorial
  fails without one (practitioner, Game Developer, "Different types of tutorials").
- No single teaching method fits every game (same source).

## Let the order of encounters teach

**No-tutorial teaching is an ordering discipline: a safe first exposure, then a test, then a twist.**
- Nintendo built later worlds first, found beginners struggled, and moved "easier features to the beginning of the
  level"; 1-1 was engineered so the player cannot miss the first mushroom (the first pipe bounces it back), simulated
  on paper with fallback paths. Iwata notes players did not read the manual (developer, Iwata Asks, NSMB Wii).
  The popular claim that Miyamoto said the forced mushroom shows how it differs from a Goomba is not on that page
  (unverified).
- Valve called Portal "effectively an extended player training exercise". Method, "checklisting": split a mechanic
  into the components a player must grasp, give "a very clean room to safely experiment with it", and only then "take
  a previously learned rule and turn it on its head" (developer, Valve commentary; Game Informer).
- The Witness, Celeste, Hollow Knight: critics describe teach-check-invert and one twist per chapter, but no designer
  statement was found (opinion, snippet). Don't cite them as evidence.

## The failures playtests keep finding

**Wrong assumed models, missed cues, and too many new ideas in one step.**
- Valve's testers assumed portals led to other dimensions, assumed orange portals were exit-only, "charge[d] down the
  stairs without noticing what was creating the portals", and stalled on a puzzle that "introduced too many new
  concepts at once". "Without some serious prompting, players will rarely look up." Fix by observe-and-patch: make the
  missed element more noticeable or change the approach (developer, Portal commentary).
- Players complain when a teaching level arrives after the need for it, or a solution needs an interaction not yet
  shown (verbatim, Baba Is You Steam reviews, snippet). Order errors are the visible complaint, not missing text.

## Players do not read

**Text-heavy instruction gets skipped; the numbers behind this are informal.**
- Over 80% of players clicked straight through a demo's instruction screen at events (practitioner, snippet).
- A mobile developer's logs: instructions barely read; drop-out came from waiting before touching controls
  (practitioner, snippet).
- One postmortem: tutorial completion 55% to 85% and early churn down 20% after splitting it into chunks, each with a
  goal and an immediate reward, plus tooltips fired by action or inaction. No sample size, no control, unnamed game:
  an anecdote, not a rate (practitioner).

## Just in time, with support that fades

**Teach at the moment of first need, and thin the support as the player shows they have it.**
- Braid shows its rewind help after the first death, "when it is first necessary"; Hearts of Iron III teaches
  everything first. Each suits a different audience (practitioner, Game Developer survey).
- Expertise reversal: guidance that helps novices becomes redundant, and can hurt, for people who already know the
  material; unguided search overloads novices. Remedy: fade the support as expertise grows. Replicated across many
  materials, mostly in well-defined technical domains; no game study found (research, Kalyuga 2007 review). Both
  pure discovery and fixed full guidance have documented costs; the middle is guidance that shrinks.
- Chunking lessons is a reasonable default, not a proven win: one software-tutorial study found no gain, another
  only fleeting transfer (research, snippet).
- Idle games: fifteen minutes can show a year's worth of the core loop, so the opening must also show what comes
  later (developer, snippet).

## Design checks

- For each mechanic: discoverable by trying? If yes, no lesson.
- Is anything taught before the player needs it, or needed before it is taught?
- Does any single step introduce more than one new idea?
- After a skip, can the player still reach the help (Andersen's "availability of help" dimension)?
- Is the step where players skip or stall recorded? That is where Valve's "too many concepts" failure shows.

## What the evidence cannot say

No controlled study of popup or tooltip dismissal was found: a gap, not proof that popups work. Skip-rate data from
shipped games was not found.
