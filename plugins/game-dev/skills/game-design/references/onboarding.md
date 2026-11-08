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

- Rule (inference from Andersen): simple mechanics get no teaching. The one hard mechanic gets an isolated
  place to practise it: an active tutorial may be ineffective without one (practitioner, Game Developer,
  "Different types of tutorials").
- No single teaching method fits every game (same source).

## Let the order of encounters teach

**No-tutorial teaching is an ordering discipline: a safe first exposure, then a test, then a twist.**
- Nintendo built later worlds first, found beginners struggled, and moved "easier features to the beginning of
  the level"; 1-1 was engineered so the player cannot miss the first mushroom (the first pipe bounces it back),
  simulated on paper with fallback paths. Iwata notes players did not read the manual (developer, Iwata Asks,
  NSMB Wii). The popular claim that Miyamoto said the forced mushroom shows how it differs from a Goomba is not
  on that page (unverified).
- Valve called Portal "effectively an extended player training exercise". Method, "checklisting": split a mechanic
  into the components a player must grasp, give "a very clean room to safely experiment with it", and only then "take
  a previously learned rule and turn it on its head" (developer, Valve commentary; Game Informer).
- The Witness: Blow describes "a layer of ramping difficulty across all these puzzles", with later puzzles building on
  elements learned earlier, but not teach-check-invert (developer, Game Developer "Bearing Witness", via summary).
  Celeste: a critic describes gradual introduction of climbing and dashing and one twist per chapter; Hollow Knight:
  critics assert learning through level design (opinion). Celeste's GDC 2017 abstract mentions teaching implicitly
  through level design, and no Team Cherry statement on Hollow Knight's teaching was found (developer, abstract only).
  Don't cite them as evidence for the three-step pattern.
- Baba Is You groups levels by the rule-word they introduce and keeps hard optional levels off the early path
  (developer, Hempuli; `genres/overview.md`).

## The failures playtests keep finding

**Wrong assumed models, missed cues, and too many new ideas in one step.**
- Valve's testers assumed portals led to other dimensions, assumed orange portals were exit-only, "charge[d] down the
  stairs without noticing what was creating the portals", and stalled on a puzzle that "introduced too many new
  concepts at once". "Without some serious prompting, players will rarely look up." Fix by observe-and-patch: make the
  missed element more noticeable or change the approach (developer, Portal commentary).
- Players complain when a teaching level arrives after the need for it, or a solution needs an interaction
  not yet shown (verbatim, Baba Is You Steam discussion threads, snippet). Order errors are the visible
  complaint, not missing text.

## Players do not read

**Text-heavy instruction gets skipped; the numbers behind this are informal.**
- Of "a couple of hundred" players at live events, "the vast majority (>80%)" clicked straight through the demo's
  instruction screen, and many skipped in-game prompts too (developer, Steamhounds team on GameDev.net, full read
  via Wayback; informal count).
- A mobile developer's logs: instructions barely read; drop-out came from waiting before touching controls
  (snippet, Automaton; article body not read, claim unverified).
- One postmortem: tutorial completion 55% to 85% and early churn down 20% after splitting it into chunks, each with a
  goal and an immediate reward, plus tooltips fired by action or inaction. No sample size, no control, unnamed game:
  an anecdote, not a rate (practitioner).

## Just in time, with support that fades

**Teach at the moment of first need, and thin the support as the player shows they have it.**
- Braid shows its rewind help only after the first death, the moment it is first needed; Hearts of Iron III teaches
  the player everything before they can play. Each suits a different audience (practitioner, Game Developer article).
- Expertise reversal: guidance that helps novices becomes redundant, and can hurt, for people who already know the
  material. Remedy: fade the support as expertise grows. Replicated across many materials, mostly in well-defined
  technical domains; no game study found (research, Kalyuga 2007 review). Unguided search loading novices' working
  memory is from a Wikipedia summary of the effect (research, snippet). Both pure discovery and fixed full guidance
  have documented costs; the middle is guidance that shrinks.
- Chunking lessons is a reasonable default, not a proven win: one software-tutorial study found no gain, another
  only fleeting transfer (unverified).
- **A note that explains a mechanic arrives with the mechanic's visible evidence.** A "this is a real-time wait" card
  shown minutes before the timed action whose countdown it describes reads as pointless:
  the player has no reason to believe a note until the screen shows something that matches it. Shown at the moment the
  countdown appears, the note is a one-line tutorial for that mechanic and hard to miss (inference, an illustrative case, not measured).

## Show the core automation concept in the first level

- Factorio's old tutorial took about 30-45 minutes to reach automation and constrained actions so players learned the
  tutorial instead of the concept. The redesign lists "Showing and teaching core concepts like Assembling machines and
  electricity in the first level" and "Teaching by experimentation instead of jumping through arbitrary tasks"; the
  developers said the hand-mining opening made it look like another block-building sandbox clone (developer, FFF #241, full). A later
  post says the redesigned intro was dropped for not matching the game's vision; only its snippet was read, so the
  reason is unverified (developer, FFF #342, snippet). Agrees with Andersen et al. above on teaching per mechanic.
- The one mechanism with a developer statement for pointing a beginner at something new is the red dot: Atom Idle
  added it "because beginners would notice it", and Just Another Idle moved toasts into a panel opened by a button
  that shows a dot (developer, devlog, snippet).
- Nothing was found on teaching that a new item can join existing automation (null: Pecorella's Math of Idle Games III
  and the paywalled GDC talks are silent on it).

## Design checks

- For each mechanic: discoverable by trying? If yes, no lesson.
- Is anything taught before the player needs it, or needed before it is taught?
- Does every note about a mechanic appear in the same moment as the thing on screen that proves it (the timer, the
  new control, the changed number)?
- Does any single step introduce more than one new idea?
- After a skip, can the player still reach the help (Andersen's "availability of help" dimension)?
- Is the step where players skip or stall recorded? That is where Valve's "too many concepts" failure shows.

## What the evidence cannot say

No controlled study of popup or tooltip dismissal was found: a gap, not proof that popups work. Skip-rate data from
shipped games was not found.
