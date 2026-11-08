---
name: game-design
description: "Evidence-labelled game design method for any genre and for gamified apps — what makes a game fun, how it feels and looks, teaching, pacing, economies, difficulty, randomness, multiplayer, playtests, legible systems, game screens. Use when designing or reviewing fun, juice, game feel, controls, button feel, visual readability or polish; 'dopamine' or compulsion-loop claims; onboarding or tutorials; rewards, streaks, return visits; currencies, sinks and faucets, inflation, cost or XP curves, balance and dominant strategies; difficulty, assists, failure, checkpoints; random drops, odds, pity timers, loot boxes; co-op, toxicity, matchmaking, leaderboards; genre conventions (roguelike, puzzle, strategy, platformer, idle and incremental with offline progress and prestige); planning a playtest or modelling progression; making automation or simulations understandable; laying out a HUD or touch controls. NOT prose or game lines (writing-craft) or data dashboards (ui-craft)."
---

# Game design

Research-backed rules for the design questions every game and gamified app meets: what makes it fun, how an action
feels and reads, how a player learns it, why they come back, how its economy and difficulty hold up, how chance and
other players behave, how to test it, whether they can see what their systems are doing, and how the screen is laid
out. Each reference states its rules as verdicts and labels each with its evidence, so a rule resting on one forum
post is never mistaken for one resting on a 45,000-player study.

**A project's design doc wins.** Where the project has a decisions file, design rules or a style doc, read it first;
its decisions override anything here. This skill supplies evidence for checking a decision, not the decision.

## The loop

1. **Name the player, the moment and the genre.** A newcomer in minute one, a returning player on day four, a genre
   veteran on hour twenty: the same rule can be right for one and wrong for another. Say which player the decision
   serves and what genre contract they arrive with.
2. **Load the matching reference** (table below). Load only what the question needs.
3. **Check the decision against it.** For each rule that applies, does the design agree, conflict, or leave a gap? A
   conflict with a well-evidenced rule (research, developer, guideline) needs a stated reason; a conflict with an
   opinion or snippet does not.
4. **Design the test that would show you wrong.** Name the observation that separates the outcomes: what a cold tester
   would do, what a log would show, what a simulation would print. `references/playtesting.md` has the method. A change
   with no test is a guess.

Scale it to the stakes. A tweak to one effect or label gets the reference glance in step 3; a new system, a lesson,
an economy or a pacing change gets the whole loop.

## Which reference

| The question is about... | Load |
|---|---|
| What makes it fun, MDA, flow, "dopamine", player types (Bartle, Hexad), core and compulsion loops | `references/fun.md` |
| Control feel, input latency, coyote time, hit-stop, button states, haptics, UI sound, silhouette and colour readability, polish | `references/feel-and-look.md` |
| Juice, effects, response time, screen shake, flashes, reduced motion, feedback for background progress | `references/feedback.md` |
| Tutorials, first-session teaching, hints, popups, when to explain a mechanic, skippable lessons | `references/onboarding.md` |
| Rewards, streaks, curiosity gaps, return visits, session and week pacing, "one more turn", decisions without a fail state | `references/motivation.md` |
| Currencies, faucets and sinks, inflation, multiple currencies, cost and XP curves, balance, dominant strategies, RMT, modelling an economy | `references/economy.md` |
| Difficulty, adaptive difficulty, assists and modes, failure, checkpoints, fairness | `references/difficulty.md` |
| Random drops and rolls, displayed odds, weighted randomness, pity timers, input vs output randomness, loot boxes | `references/randomness.md` |
| Co-op, competition, toxicity, reporting, matchmaking, leaderboards, gifting, light social features | `references/social.md` |
| Planning or reading a playtest, how many testers, think-aloud, surveys, telemetry vs watching | `references/playtesting.md` |
| Automation, player-written rules, simulations, overlays, tooltips, "why did it do that" | `references/legibility.md` |
| Screen layout, HUD, diegetic UI, an interface that grows, touch targets, hover, mobile browser viewport | `references/game-ui.md` |
| What players of a genre expect: roguelike, puzzle, strategy/4X, platformer, narrative, simulation | `references/genres/overview.md` |
| Idle and incremental games: offline progress, exponential costs, prestige | `references/genres/idle.md` |

The source rows behind each reference, with url, how much was read, and the label, are in `evidence/<topic>.jsonl`
(genre rows under `evidence/genres/`, genre-fit rows in `evidence/genre-fit.jsonl`). Check a row before leaning hard
on a rule.

## Rules that fire every time

- **Your own play is a smoke test, never a clarity test.** The designer knows the design, and a genre-literate
  designer hides exactly the gaps a newcomer hits (developer, Hodent; research, RITE recruited genre newcomers). Judge
  clarity by watching someone new.
- **Watch what testers do; what they say is a lead.** Take the problem they report and discard their fix (developer,
  Valve playtest slides).
- **Teach only what can't be discovered, at the moment it is first needed.** Tutorials paid only in the complex game
  of three tested (research, Andersen et al. CHI 2012); players skip text.
- **Answer every input at once**, even if only with a press state or a refusal; 100 ms is the ceiling for "it reacted"
  (practitioner, Nielsen), and precise, deadlined actions need far less: on a direct touchscreen, drag lag was noticed
  from 11 ms on average and tap lag from 69 ms (research, Claypool 2010; Jota et al. 2013; Deber et al. 2015).
  An input that does nothing reads as a bug.
- **Feedback has a ceiling.** In 3,018 players the most-juiced version scored lowest on every measure that differed,
  while no juice fell short only on competence, play time and actions; making the same feedback bigger lowered
  competence. The effects are small, so trust the shape, not the size (research, Kao 2020, Kao et al. CHI 2024). Tie
  the size to what happened, and never escalate one event class over time.
- **Reduced motion removes movement, never information**, and neither colour nor sound carries information alone
  (guideline, WCAG, Game Accessibility Guidelines, Xbox XAG).
- **Design for curiosity and surprise, not "dopamine hits".** Curiosity was the only predictor of free playtime
  (research, Kao et al. CHI 2024); dopamine signals prediction error and wanting, not pleasure (research, Schultz
  1997; Berridge 1998). The usual source for "games release dopamine" is an 8-man PET study whose own group later said
  head movement may have biased it (research, Koepp 1998; Egerton 2009).
  A loop that brings players back doesn't show they enjoy it.
- **A reward should inform, not pay.** Expected rewards for doing a task cut later interest; positive feedback raised
  it (research, Deci, Koestner & Ryan 1999). A highlighted broken streak lowered the next action (research, Barasch &
  Silverman, mostly simulated tasks).
- **Hours played is not success.** Need satisfaction (autonomy, competence) predicts enjoyment and does not predict
  hours; obsessive play does, and play time barely moves well-being (research, Ryan et al. 2006; Przybylski et al.
  2009; Vuorre et al. 2022).
- **Show what a system will do before it does it**, as facts with numbers on them, so failure traces to the player's
  choice (developer, Into the Breach).
- **Weight randomness for feel, but keep every shown number true.** Players read 85% as certain (developer, XCOM);
  smooth streaks and bound droughts (PRD, pity timers, shuffle bags) rather than silently inflating a displayed
  percentage (`references/randomness.md`).
- **Every faucet ships with its sink, and every currency has one job.** A growth engine runs away without a drain
  (research, Dormans); a parallel currency earns its place only by doing what the others can't
  (`references/economy.md`).
- **Balance means many viable options, not equal power.** A dominant option is a non-choice; players will optimise the
  fun out of a game if the designer doesn't price it first (practitioner, Sirlin; developer, Meier, Johnson).
- **Anything that matters is reachable without hover** (guideline and practitioner, `references/game-ui.md`).
- **Guarantee the tools work; never protect the player from their own choices.** A rule, check or default earns its
  place if it makes sure a player who uses the taught tools never has to watch, or can see enough to choose well. One
  that stops a player choosing badly, decides for them (one-click fixes, auto-installed rules, suggested picks), or
  tunes the game so the worst player is never behind waters the game down to no decisions at all. Not knowing a tool
  is a teaching problem; not wanting one is the player's choice. Hold simulations to a typical player who uses the
  tools, and only report the neglectful one (inference; consistent with Factorio's "a button that solves it removes the game").
- **Use the genre's native mechanics and language, and fit each mechanic to the game's type and story.** Players arrive
  with the genre's mental model: they sort games by aesthetic and mechanics more than by genre label (research, Lewis
  et al. 2007, abstract), and prior experience transfers into a new game (research, Oliver and Pelletier 2005,
  abstract). A platformer player expects forgiving jumps, a strategy player a priced
  dominant option, an idle player progress as a milestone. A goal outside that model reads as unintuitive however
  plainly it is worded (inference; `references/genres/overview.md`, and no source measures what breaking a convention
  costs). A mechanic that rewards what the story says doesn't matter pulls the two apart (practitioner, Hocking's 2007
  essay on BioShock, a game he didn't make; the player studies found are small). Test a goal on both axes before wording it: if it is
  hard to state in the UI's voice, suspect the goal, not the words (inference, an illustrative case: an ending that
  demands a balance the story calls unimportant). Sources:
  `evidence/genre-fit.jsonl`, `evidence/genres/overview.jsonl`.
- **A simulation fails only on invariants; rhythm is a readout.** Softlocks, runaway spirals, a tool user forced to
  babysit and a shown number that doesn't come true are failures. How often a player meets a new thing or a decision
  is taste: report it, never hold content to a target, or the content contorts to the number and the game goes stiff
  (inference; no source gives a decision rate for any genre).
- **In a gamified app, a miss is the person's life, not a play.** Letting losses from the player's own choices stand
  is right for a game and wrong for a fitness tracker: there, nothing goes down and absence is never punished. Before
  carrying a rule between the two, name which side it came from (inference, an illustrative comparison of
  a game's rules with a fitness app's).

## Evidence words

**research**: a study, paper or thesis. **developer**: a game's makers on their own game. **guideline**: a published
standard or platform guide (WCAG, Apple, Android, Xbox, Game Accessibility Guidelines). **verbatim**: a player's or
author's own words, quoted. **practitioner**: a working designer's or researcher's published advice, not about their
own game. **opinion**: critics, reviewers, forum posts. **snippet**: seen only in a search result or summary.
**unverified**: not checked against the source. **inference**: reasoned from cited findings that do not state it.
Weight rules by label: a snippet or opinion is a starting point to test, not a reason to override a design decision.
Most sources are from commercial games; rules for gamified apps (fitness or learning apps and the like) are inference unless a
reference says otherwise. A **null** ("none found") records a search, not proof of absence.
