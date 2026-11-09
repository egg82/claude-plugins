# Genre conventions

What players of each major genre arrive expecting, in their makers' words, so a design uses the genre's native
mechanics. Idle and incremental games have their own file (`idle.md`). Sources: `../../evidence/genres/overview.jsonl`
and `../../evidence/genre-fit.jsonl`. **No source measures what breaking a convention costs, in any genre**; every
"breaking it costs" below is a maker's account or inference. Most makers' statements were reached through news
reports and summaries of GDC talks, not the talks.

## Genre is a bundle of mechanics, not a label

- Players sort games by mechanics and aesthetic more than by marketing genre (research, Lewis, McGuire & Fox 2007,
  abstract). Prior game experience transfers into a new game (research, Oliver & Pelletier DiGRA 2005, abstract).
- Players are predicted better by motivation than by genre (snippet, Quantic Foundry coverage; `../fun.md`).

Rule: copy the mechanic the player expects, not the genre's name. A gamified app inherits its users' motives, not a
genre's contract (inference).

## Roguelikes and roguelites

- The Berlin Interpretation lists high-value factors (random generation, permadeath, item discovery redone each game)
  from five canonical games; it is a community definition and says missing traits don't decide membership
  (practitioner, 2008).
- Randomness without interacting systems is "a glorified slot machine" (developer, Derek Yu, Spelunky book excerpt).
- Kasavin: even resetting roguelikes leave the player their knowledge of the mechanics; he imagined bosses who
  remember. When story-engaged players hit a difficulty wall, Supergiant built systems to mitigate it (developer,
  Kasavin, GDC podcast, partial). Hades' God Mode keeps the death loop while easing it (`../difficulty.md`).
- Slay the Spire's devs treat pick rate and win rate as the two key balance metrics (developer, Game Developer coverage
  of Mega Crit's GDC 2019 talk, partial; `../economy.md`).

## Puzzle games

- Hempuli divides Baba Is You's areas by the rule-words they introduce, puts harder levels on the same word in the same
  area, and nudges a stuck player elsewhere. Difficulty grows fast with the number of rules active at the start. Hard
  optional levels are marked "Extra" and kept off the early path; numbered levels fight the habit of "return later"
  (developer, interview).
- Blow and ten Bosch: build a system that expresses a truth cleanly and let its behaviour supply the puzzles, rather
  than assembling puzzles combinatorially (developer, blog blurb and a GDC Europe report; talk not read). In The
  Witness "there's just a layer of ramping difficulty across all these puzzles" (developer, Blow, Game Developer; `../onboarding.md`).
- Zachtronics ships open-ended puzzles and lets players find their own solutions (developer, GDC 2019 blurb).
- Players complain when a teaching level arrives after it was needed (`../onboarding.md`).

## Strategy and 4X

- Every decision should be situational with real tradeoffs; a dominant option is a non-choice; acknowledge every
  decision, even with a sound; too many fast, complicated decisions make the player feel out of control (developer,
  Meier GDC 2012, via a news report).
- "Players will optimize the fun out of a game": find the dominant strategy before they do and price it. Civilization
  IV's per-city maintenance grew with city count to stop small-city spam, which had made high difficulties trivial
  (developer, Soren Johnson, Designer Notes, partial).
- Remove mechanics that make players micromanage to avoid waste (Civ IV carries overflow production to the next item);
  keep the player the star, not the designer or the AI; offer toggles for exploits some players value, such as
  save-reload (developer, Johnson).

## Action and platformers

- Celeste widens timing and position windows in the player's favour in ways that are hard to notice: coyote time, jump buffering,
  corner correction, wall-jumps from 2 px at 320x180, dash corner pop-up. Thorson's reason: "a little cheating"
  improves how the controls feel (developer, via a Gigazine summary). No developer gives frame counts
  (`../feel-and-look.md`).
- Inference: a precise-jump game without these forgiveness windows reads as unresponsive to players raised on them.

## Narrative and choice-driven games

Story delivery, pacing, choices, discovery and spoilers: `narrative.md`. A humanities analysis argues that choices which
don't change the plot can still work as a thought experiment on a theme (research, abstract; argument, not player
data).

## Simulation, management and colony games

- The game is a generator of player-made stories; an experience is "an arc of emotions, thoughts, and decisions inside the
  player's mind" (developer, Sylvester, snippet). RimWorld aimed for "a simulation that was not overly complex, and
  that a player can observe and comprehend" (developer, `../legibility.md`).
- RimWorld uses named AI storytellers (Cassandra, Phoebe, Randy), reportedly modelled on Left 4 Dead's AI Director
  (snippet, unverified).
- Factory games: the bottleneck is the puzzle and a solve button removes the game (`../motivation.md`).

## Across genres

- What is interesting once may not be interesting ten times; a repeated decision needs a changing situation
  (developer, Meier, snippet; inference).
- Meier says a third or more of attempted features get cut; one good game beats two competing cores; a designer's own
  play style is a poor proxy for the audience (developer, Meier and Johnson, via reports).

## What the evidence cannot say

What breaking a convention costs, anywhere. Player-sourced expectation lists per genre. Unread: GDC talks by Meier,
Blow and ten Bosch, Barth, Giovannetti and Ingold; Sylvester's "Designing Games"; Yu's full book; any Slay the Spire
design talk; critics of the Berlin Interpretation.
