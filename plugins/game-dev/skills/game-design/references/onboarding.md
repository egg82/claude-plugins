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
- A caveat from a small study: a tutorial raised flow and intent to keep playing for non-experts in one simple mobile
  game (research, Passalacqua et al. 2020; n=40, about 10 per cell, flow and intent rather than retention). Andersen's
  "nothing measurable in simpler games" was engagement across 45,000 players; the two measure different things.
- Just-in-time instructions beat an up-front instruction screen in a *simple* VR wave shooter: more enjoyment (IMI,
  r=.40), joy (r=.50) and positive feeling, less frustration, but no difference in performance, immersion or how much
  players felt the tutorial helped (research, Frommel et al. CHI PLAY 2017, n=39, mostly VR novices, same wording in
  both). The authors: Andersen found this "mainly for complex games, our study showed similar effects for a rather
  simple game". So timing pays in how it feels even where it doesn't change learning.
- In VR, tooltips placed on the controllers beat text-only instructions on learning the controls in two of four games,
  with negligible differences in the other two (research, Kao, Magana and Mousas CHI PLAY 2021; 433 players). Put the
  instruction on the thing it is about.

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

## A good opening, by one critic's four tests

Josh Strife Hayes, who reviews games' new-player experience for a living, scores openings on four tests and walks six
games through them (practitioner, "How to Design a Tutorial", 2022, captions read in full):
1. **Say it, then let them use it at once, safely.** Information "flows directly into the next player action"; told
   to lock on, the player finds an enemy placed in front of them. A screen of systems the player cannot use yet (Deus
   Ex: Human Revolution's ninety-second inventory video) is forgotten by the time it matters.
2. **Stack mechanics**, least to most complex, and the first time two combine, say so: "a brand new player won't know
   the previous learned actions have synergy". After that, combine without explaining (Dead Space's tram puzzle uses
   everything taught in its first ten minutes). Mechanics shown once each are "a gallery of what the designer has
   chosen to put in".
3. **Teach through the channel the game already speaks in.** Dark Souls teaches with the orange floor messages players
   later use to talk to each other; Dead Space through the suit's hologram. A meta-voice the rest of the game never
   uses (Human Revolution's tutorial videos) breaks the flow.
4. **Make it the opening, not a separate area.** Naming a level "Tutorial" tells players it doesn't matter.

His gaps are as telling: Dark Souls never teaches kindling or reverse hollowing, and "many people have completed the
game without knowing what these things do"; Morrowind's first real fight comes with no safe practice. Same four
points as Valve's checklisting and Nintendo's ordering above, from the player's side. His goal: "make them aware of
what they can do, give them a chance to do it and then combine it until they eventually know everything".

- Plants vs. Zombies (developer, George Fan, GDC 2012, captions read in full):
  - "A maximum of eight words on the screen at any given moment", which he calls "pretty much impossible to maintain"
    but "a good thing to shoot for". His evidence is intuition: of four sentences, "I think it's more likely they're
    going to read zero."
  - The biggest flaw, found by watching a non-gamer, was not planting sunflowers early. The fix was cost and light,
    not text: sunflower cost and starting sun both 50, so only the sunflower is lit at the start; players "press the
    bright shiny object".
  - A tip appears only to players making the mistake (all peashooters in the right column), so others keep "the
    chance to feel smart". Don't freeze play for an OK dialog; put passive text at the bottom of the screen. Arrows
    and flashing get the player to do an action once (first coin, seed packet).
  - "No need to explain every single concept": past the first minutes, experimenting beats hand-holding. New
    features arrive spaced out (a new zombie every other level, the store at 3-4).

## Visual cues first; words where testing finds the gap

The celebrated wordless openings use words, or something as blunt. Portal's fix for testers who "stubbornly refused to
look up" was a ladder and portal surfaces on moving pistons (developer, Valve commentary, above); its portal-gun room
has big arrows pointing at the gun (practitioner, Strife Hayes). No source found shows Portal shipping a literal "look
up" sign (null). Dark Souls' glowing orange messages are a glow that carries words. Plants vs. Zombies shows a big arrow
at the first coin, once (developer, Fan). AAA studios add yellow paint after testers get lost (`progress.md`). An
indie developer's list of "things that seemed obvious to me but weren't during playtests": players kept jumping right
into the void until a spinning staircase turned them left; nobody entered a village's houses until one got a giant
exclamation point; a necessary item on a pedestal went untaken until it floated and glowed (developer, Braga, Inner
Voices, via GamesRadar 2023).

Rule (inference from those): start with shape, light and glow; watch cold testers; add words, briefly and at the
moment, wherever a cue was missed or misread. A glow says "here", never "why". A glow only teaches once something has
tied it to a meaning: Dark Souls' item shine works because the first shine was on the key (practitioner, Strife
Hayes).

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
- In 50,128 Android players of one puzzle game, 58% of those who began the tutorial finished it, and per-level quit
  rates were similar whether they finished or not (developer, Game Developer, GameAnalytics data). It did not measure
  reading.
- No instrumented study of how much tutorial text players read was found (null). "Players don't read" rests on
  developer anecdotes: plausible, unmeasured, and no excuse for skipping the few words a missed cue needs.

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

## A lesson the player must read cannot be missable

- For tutorial windows and dialogue, let the player lengthen the time "up to at least 10x the default" or "disable
  duration limits entirely so elements can be dismissed or advanced on input" (guideline, Xbox XAG 116). "Instead of a
  timer, dismiss information on a player action"; distraction makes players miss key information (guideline, Game
  Accessibility Guidelines). A message that vanishes after 5 seconds is exempt only if the user can learn the same
  thing another way (guideline, WCAG 2.2.1 Understanding doc).
- On a phone, attention to the screen breaks into bursts of 4 to 8 seconds, with glances away up to 8 times while
  waiting on one page load (research, Oulasvirta et al. CHI 2005; walking web-search task, small sample, not games).
- Players hunt for ways to reopen a tutorial they closed by accident, and critics ask for replay from the pause menu
  (snippet, a Dwarf Fortress how-to and a Kotaku column). No game was confirmed to keep a log of lessons (null for
  Hades, Monster Hunter and Persona).

Rules: no auto-dismiss timer on a step the player must read; it advances on input. A lesson that was covered,
scrolled away or interrupted comes back later instead of recording as seen (inference: a phone player who looks away
for eight seconds has not read it). Keep taught lessons reachable afterwards (Andersen's "availability of help",
above).

## Teach a state change when it happens, naming the cause

- Factorio prints a named cause on a stalled machine ("Waiting for space in destination", "No power"), and wrong
  statuses draw bug reports; Oxygen Not Included players ask for a "duplicant is stuck" alert because only food, bed
  and toilet problems are announced (snippet, forum threads; both forums refuse scripted reads).
- An always-present red dot stops being seen: "if it's always there, it might as well not be there at all" (snippet,
  vendor UX blog, apps not games).
- A game's own explanations that are "usable but unverifiable" prompt action without building causal understanding
  (research, Guo 2026 preprint, one game, no player data).
- No study compares a named-cause message with a bare highlight (null).

Rule (inference): when something the player relies on changes (a supply route closes, a machine stalls), say what
changed, why, and what replaces it, at that moment and next to the thing. A glow with no words reads as random:
Factorio's stalled machine says "No power" or "Waiting for space in destination" (above), where a bare pulsing outline
would say only "look here". This is the moment-of-need rule above, triggered by the game, not the player.

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
- Does any step the player must read dismiss itself on a timer? Does a lesson that was covered or scrolled away come
  back?
- When something the player relies on stops or changes, does the screen say why in words?
- Is the step where players skip or stall recorded? That is where Valve's "too many concepts" failure shows.

## What the evidence cannot say

No controlled study of popup or tooltip dismissal was found: a gap, not proof that popups work. Skip-rate data from
shipped games was not found.
