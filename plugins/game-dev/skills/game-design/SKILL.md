---
name: game-design
description: "Evidence-labelled game design method for games and gamified apps — teaching mechanics, feedback, pacing, playtests, legible systems, game screens. Use when designing or reviewing onboarding, tutorials or first-session flow; feedback, juice, effects, reduced motion; rewards, streaks, pacing, return visits, idle or offline progress; planning or reading a playtest or cold test; making automation, rules or simulations understandable; laying out a game screen, HUD or touch controls. NOT prose or game lines (writing-craft) or data dashboards (ui-craft)."
---

# Game design

Research-backed rules for the design questions every game and gamified app meets: how a player learns it, what an
action feels like, why they come back, how to test it, whether they can see what their systems are doing, and how the
screen is laid out. Each reference states its rules as verdicts and labels each with its evidence, so a rule resting on
one forum post is never mistaken for one resting on a 45,000-player study.

**A project's design doc wins.** Where the project has a decisions file, design rules or a style doc, read it first;
its decisions override anything here. This skill supplies evidence for checking a decision, not the decision.

## The loop

1. **Name the player and the moment.** A newcomer in minute one, a returning player on day four, a genre veteran on
   hour twenty: the same rule can be right for one and wrong for another. Say which player the decision serves.
2. **Load the matching reference** (table below). Load only what the question needs.
3. **Check the decision against it.** For each rule that applies, does the design agree, conflict, or leave a gap? A
   conflict with a well-evidenced rule (research, developer) needs a stated reason; a conflict with an opinion or
   snippet does not.
4. **Design the test that would show you wrong.** Name the observation that separates the outcomes: what a cold tester
   would do, what a log would show, what a simulation would print. `references/playtesting.md` has the method. A change
   with no test is a guess.

Scale it to the stakes. A tweak to one effect or label gets the reference glance in step 3; a new system, a lesson or
a pacing change gets the whole loop.

## Which reference

| The question is about... | Load |
|---|---|
| Tutorials, first-session teaching, hints, popups, when to explain a mechanic, skippable lessons | `references/onboarding.md` |
| Juice, effects, sound, response time, screen shake, reduced motion, feedback for background progress | `references/feedback.md` |
| Rewards, streaks, daily loops, pacing over a session or week, return visits, offline progress, "one more turn" | `references/motivation.md` |
| Planning or reading a playtest, how many testers, think-aloud, surveys, telemetry vs watching | `references/playtesting.md` |
| Automation, player-written rules, simulations, overlays, tooltips, "why did it do that" | `references/legibility.md` |
| Screen layout, HUD, diegetic UI, an interface that grows, touch targets, hover, mobile browser viewport | `references/game-ui.md` |

The source rows behind each reference, copied from the research notes with url, how much was read, and the label, are
in `evidence/<topic>.jsonl`. Check a row before leaning hard on a rule.

## Rules that fire every time

- **Your own play is a smoke test, never a clarity test.** The designer knows the design, and a genre-literate
  designer hides exactly the gaps a newcomer hits (developer, Hodent; research, RITE recruited genre newcomers). Judge
  clarity by watching someone new.
- **Watch what testers do; what they say is a lead.** Take the problem they report and discard their fix (developer,
  Valve playtest slides).
- **Teach only what can't be discovered, at the moment it is first needed.** Tutorials paid only in the complex game
  of three tested (research, Andersen et al. CHI 2012); players skip text.
- **Answer every input within about 100 ms**, even if only with a press state or a refusal. An input that does nothing
  reads as a bug (practitioner, Nielsen).
- **Feedback has a ceiling.** Medium juice beat none and extreme; making the same feedback bigger lowered competence
  (research, Kao 2020, Kao et al. CHI 2024). Tie the size to what happened, and never escalate one event class over
  time.
- **Reduced motion removes movement, never information**, and sound never carries information alone (guideline, WCAG,
  Game Accessibility Guidelines).
- **A reward should inform, not pay.** Expected rewards for doing a task cut later interest; positive feedback raised
  it (research, Deci, Koestner & Ryan 1999). Players describe streaks and daily resets as obligation (opinion,
  snippet).
- **Hours played is not success.** Need satisfaction (autonomy, competence) predicts enjoyment and does not predict
  hours; obsessive play does (research, Ryan et al. 2006; Przybylski et al. 2009).
- **Show what a system will do before it does it**, as facts with numbers on them, so failure traces to the player's
  choice (developer, Into the Breach).
- **Anything that matters is reachable without hover** (guideline and practitioner, `references/game-ui.md`).

## Evidence words

**research**: a study, paper or thesis. **developer**: a game's makers on their own game. **guideline**: a published
standard or platform guide (WCAG, Apple, Android, Game Accessibility Guidelines). **verbatim**: a player's or
author's own words, quoted. **practitioner**: a working designer's or researcher's published advice, not about their
own game. **opinion**: critics, reviewers, forum posts. **snippet**: seen only in a search result or summary.
**unverified**: not checked against the source. **inference**: reasoned from cited findings that do not state it.
Weight rules by label: a snippet or opinion is a starting point to test, not a reason to override a design decision.
Most sources are from commercial games; rules for gamified apps (fitness or learning apps and the like) are inference unless a
reference says otherwise.
