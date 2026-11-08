# Motivation and pacing: first session, first week

What brings a player back, and how to shape the pull without obligation. Sources: `evidence/motivation.jsonl`. What
"fun" is and what dopamine does are `fun.md`; currencies and curves are `economy.md`; idle games' offline return and
prestige are `genres/idle.md`. The biggest limit: nothing found measures what brings a player back on days 2 to 7 of a
game with no notifications or daily rewards. The first-week advice below is inference from theory plus designer
testimony.

## Players return when they feel capable and self-directed; hours played measures neither

- In-game autonomy and competence predicted enjoyment and wanting to play again; relatedness also did in the
  multiplayer study (research, Ryan, Rigby & Przybylski 2006, four correlational self-report studies).
- Intuitive controls mattered only as a gate: their effect on wanting to play again ran entirely through felt autonomy
  and competence. Clear controls are the price of admission, not the pull (same).
- Low need satisfaction went with obsessive play: more hours, post-play tension, less enjoyment. High need
  satisfaction went with harmonious play and did not predict hours (research, Przybylski et al. 2009, correlational,
  abstract only).
- Across seven games and 38,935 players, play time had a "probably very small" effect on well-being; motivation
  quality tracked it better (research, Vuorre et al. 2022; `social.md`).

Test: the healthy signal is the player saying "I chose this and it worked", not long play. A metric of time in game
rewards the wrong thing.

## Rewards as information strengthen interest; rewards as a lever weaken it

- Meta-analysis of 128 experiments: expected tangible rewards for doing, finishing or performing a task cut later
  free-choice interest (d = -0.40, -0.36, -0.28). Unexpected and task-noncontingent rewards had no effect. Positive
  feedback raised free-choice behaviour (d = +0.33) and interest (d = +0.31) (research, Deci, Koestner & Ryan 1999).
- Mostly lab tasks that were interesting to begin with: this bounds a risk, it does not predict a game's outcome.
  A review of 819 gamification papers coded the 66 controlled experiments: 19 positive, 31 mixed but mainly positive,
  12 null or evenly split, 4 mainly or fully negative; the authors call the amount of mixed results "remarkable" and
  note only 11 of the 66 tested one feature at a time (research, Koivisto & Hamari 2019, full).

Test: of each reward ask "is this telling the player how they are doing, or paying them to keep going?" The second,
promised in advance for a repeated action, is where interest erodes. Gamified habit apps, which reward a repeated
action by design, sit closest to that case (inference).

## An open, salient gap pulls the player forward

- Curiosity arises when attention lands on a gap between what one knows and wants to know; it grows as the
  information gets closer to closing the gap, and with how much one already knows (47 of 50 reads as "3 missing")
  (research, Loewenstein 1994, full).
- Salience, not importance, is what draws attention to a gap: people get curious about unimportant questions.
  Importance amplifies a salient gap; salience comes from recent priming, a knowable answer, others knowing it, and
  contrast (research, Golman & Loewenstein 2016, theory paper, full).
- "Tease the player enough so that he wants to see the next turn/level/corner" and "Reward him for getting there, but
  focus your attention on the next thing to do" (developer, Sid Meier, GDC write-up).

Test: when a reward lands, is the next question already on screen? A gap the player only discovers later pulls
nothing.

## People return to unfinished tasks; they don't remember them better

A meta-analysis of 59 publications found no memory advantage for unfinished tasks (recall ratio 1.09 without the 1927
original, dz = 0.15) but a reliable tendency to go back to them: 67% resumed against 50% chance (research, Ghibellini &
Meier 2025, full; student lab tasks, no games). "Unfinished tasks stick in memory" is folklore; "people resume what
they left open" is supported. Leave a session with something visibly in progress, not with a cliffhanger the player
must remember (inference).

## Effort rises near the goal, and a head start counts

- Effort rose with the share of distance covered; engagement dipped right after a reward and rose toward the next. A
  12-stamp card with 2 stamps pre-applied (same 10 purchases) was finished in 12.7 days against 15.6 for a plain
  10-stamp card (research, Kivetz, Urminsky & Zheng 2006, field experiment n=108; purchases and ratings, not games).

Rule: show progress as a fraction of a named goal; don't start the next bar from nothing the moment one fills; expect a
dip after each completion. Seed a head start only from real carried-over progress, since an invented one can read as
fake (inference).

## Streaks pull, and a broken one pushes away

- Highlighting a broken streak lowered the next action against highlighting an intact one (66.23% vs 57.86% chose
  another exercise in one study); the drop was larger when people blamed themselves and smaller when the streak could
  be repaired (research, Barasch & Silverman, seven experiments, over 4,000 participants, via INSEAD summary; mostly
  simulated tasks).
- In a six-week field experiment, positive streak feedback raised retention and enjoyment, but streak feedback also
  created a competing goal and increased the behaviour the app existed to reduce (research, Gershon, one sec app,
  seminar abstract, snippet).
- Duolingo split its streak from the daily goal and reported +3.3% relative day-14 retention in one A/B test, with no n
  or significance given; its "7-day streak users 2.4x more likely to return" is an observational comparison, not a test
  (developer, Duolingo blog).
- Players describe losing a long streak as burn-out and ask for modest rewards so nobody feels obligated (verbatim,
  snippet). No study of long-run churn after a lost streak was found.

Rules: if you have a streak, make it repairable and frame a miss without blame; never let the streak become the goal
in place of the thing it counts. In a fitness or learning app, nothing goes down and absence is never punished (SKILL.md).

## Interest over a session is a shape to draw and check

Schell's interest curve: a hook, then rising peaks and valleys to a climax, compared against curves playtesters draw
(practitioner, secondary only). Use it as an exercise: sketch minute 0-30 and day 1-7 and look for long flats. Flow and
challenge-skill matching are weaker pacing tools than their reputation (`fun.md`).

## Layered goals have no published numbers

The first upgrade taking too long to save for is the classic early failure; a visible next-unlock condition and a
"fill this, something happens" bar keep early players; pacing drags when gains are tiny against the wait; more
players leave in the opening minutes than at any later point (practitioner, itch.io and an idle-design guide,
snippet). No source gives "a new thing every N minutes", and Meier never stated the folklore short/medium/long-goal
formulation: don't cite him for it.

## What pulls a player back without notifications or streaks

(Inference from the sections above.) A gap left open and salient, a goal visibly near, a task left in progress, a
choice the player made that is still working, and in games that run while away, a return that pays more the longer
the absence (`genres/idle.md`).

## "One more turn" comes from consequential decisions, not compulsion loops

"A game is a series of interesting decisions"; a decision needs impact, "or at least the player should believe it
has" (developer, Meier). Dark-pattern check, from the need-satisfaction research: does the pull weaken once the player
is satisfied, or only when they stop? A healthy pull weakens at satisfaction. Compulsion loops are folklore with no
retention data (`fun.md`).

## Decisions matter without a fail state

- **The loop is find the slowest part, fix it, repeat.** In Factorio the bottleneck is the puzzle, and fixing
  it exposes the next one; that nothing is lost when a line backs up is (inference). The core choice is "whether
  investment helps you the most to move forward" (developer, Factorio FFF #300 and Kovařík interview).
- **A button that solves it removes the game.** A Factorio developer (Twinsen) called blueprint import "like putting a
  'level up' button in an RPG" that "could easily make a 100-hour game into an 10-hour game"; "it's more fun to
  make your own setups" (developer, FFF #309).
- **Don't punish mistakes; reward experiments.** "Why should we penalize players for being creative and making
  mistakes?" Of building, the interview says "you work through your checklist" (developer, Satisfactory makers,
  Heise interview).
- **Options must differ in what they give, not just how much** (developer and research, idle-game sources in
  `genres/idle.md`; Sirlin on viable options in `economy.md`).

Test: name the binding constraint on each open goal as a fact the player can see ("limited by timber, 3 per hour"). If no goal
has one, or the same option always wins, there is nothing to decide.

## Late-game "nothing to decide" turns back when a new mechanic changes the old answer

- The late complaints are "nothing to decide" and "waiting for numbers": "little to do beyond waiting for numbers to
  increase", "a number-go-up simulator" (snippet, a machine-written aggregate, weak); "drift into tedium as everything
  hits diminishing returns" (opinion, one Idle Awakening reviewer); "no amount of optimization ... will keep you from
  having to play the same thing" (opinion, Increlution player comments). Single sources; no retention data.
- What turns it back is a mechanic that changes the old answer as the old one gets comfortable: "adds new surprising
  twists just as you get comfortable" (opinion, Increlution players). Factorio's Space Age planets each have "their own
  unique theme, resource, challenges and gameplay mechanics"; the team targeted under 80 hours for an experienced
  player, "speeding things up, which doesn't mean dumbing it down" (developer, Factorio FFF #373, full).
- Watching is not the enemy: one idle developer reportedly removed the player character to keep the view on the
  numbers, and Factorio's lead likes to sit and look at a running factory (unverified: no row records either).
  Inference: the "walking simulator" is watching with nothing to change; a watcher with a visible next constraint is
  Factorio.
- Rhythm has no number: no source gives how often a good idle or automation game asks for a real decision (null,
  supported by absence). Bounds that exist: Increlution runs of "about 10-35 minutes", mostly automatable, with
  decisions at the start and at each wall (opinion, player comments); Idle Awakening "at its best" in "the first few
  days or weeks", while each unlock changes the setup (opinion, one reviewer).

Rule (inference): the cadence of decisions follows how often the binding constraint moves, since the decision is the
response to it.

## What the evidence cannot say

No controlled study shows that interrupted or open-loop sessions raise return rates in games. No study of churn after a
lost streak. Relatedness from NPCs in a single-player game is untested (the relatedness finding is multiplayer).
No developer words on decisions in Kittens Game, Melvor Idle, NGU Idle or Bitburner, and no developer account of Idle
Loops or Increlution. Nothing shows the new-mechanic cadence raises retention in games with no notifications.
