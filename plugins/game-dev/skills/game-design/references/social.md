# Multiplayer and social design

Co-op, competition, toxicity, matchmaking, leaderboards and light social features in single-player games and gamified
apps. Sources: `evidence/social.jsonl`. The research is short lab sessions and cross-sectional surveys; the Riot and
Blizzard moderation figures are developers' own numbers reached through secondary write-ups, and conflict.

## Make players need each other, not just play near each other

- Interdependence (each player holds an ability the other lacks) raised felt relatedness, enjoyment and trust between
  strangers in a two-player puzzle game, whether play was cooperative or not. Cooperative framing also raised them, and
  the two add rather than multiply: no significant interaction (research, Depping & Mandryk CHI PLAY 2017, via Depping's
  2018 dissertation; 10-minute stranger pairs on MTurk).
- Cooperation raised invested effort; interdependence did not. Interdependence raised tension when players cooperated
  (interaction eta² .05) and lowered it when they competed (same).
- In 730 MMO players, in-game relatedness independently predicted enjoyment, intended future play and weekly hours. A
  competitive drive predicted worse post-play mood but more hours (research, Ryan, Rigby & Przybylski 2006 Study 4;
  cross-sectional, 93% male).

Rule: for closeness, give each player something the other lacks; for effort, share the goal. Interdependence buys
closeness with pressure, so give a fast, blameless recovery from a partner's mistake (inference).

## Play time does not make people better or worse off; why they play does

- A six-week panel across seven games and 38,935 players put the effect of play time on well-being at "probably very
  small" (the authors' words); response rates were 0.1-3%, the estimate changed sign under some missing-data
  scenarios, and only total play time was measured. Intrinsic motivation related to life satisfaction more than amount
  of play (research, Vuorre et al. 2022).
- In a cross-sectional survey of two games, play time was no longer significant once need satisfaction was in the
  model (research, Johannes et al. 2021; neither study separates social from solo play).

Rule: never claim a social feature improves well-being, or that time in game shows anything is working. This matches
the need-satisfaction rule in `motivation.md`.

## Toxicity lives on the losing side, so design the loss

- In League of Legends, reported players were on the losing team far more than half the time (under 15% winning, for
  intentional feeding). An explicit "report" in chat raised opponents' reporting odds 16.37 times, so unprompted
  reports undercount. The Tribunal's experienced reviewers still pardoned about 10-26% of reported players by category
  and region (research, Kwak, Blackburn & Han CHI 2015; observational).
- Riot's loading-screen experiment: red negative-behaviour statistics and blue positive messages cut toxicity; the red
  slogan "Who will be the most sportsmanlike?" raised every toxicity metric. Cross-team chat made opt-in cut negative
  chat (developer, Lin GDC 2013, Gamasutra write-up). That bans explained with reasons, or with chat logs, reformed
  more players rests on search snippets alone (snippet); the often-quoted percentages, 32.7% and 50-92% reform,
  disagree across sources, so cite only the direction.
- Overwatch's endorsements plus looking-for-group cut matches with abusive chat 26.4% (Americas) and 16.4% (Korea)
  (developer, Kaplan 2018 via Inven; unaudited, the two features not separated).

Rules: cut the cost of a loss (short matches, early surrender, no punitive swing on a one-sided game) before adding
punishments (inference). One-click reporting; no punishment on reports alone; tell a punished player what they did,
with the evidence. Test social copy: wording reversed Riot's effect.

## Loss streaks are the churn risk; engagement-optimised matchmaking barely helps

- In one EA PvP game, 7-day churn after three straight losses was 5.1% against 2.6-2.7% in better states (research,
  Chen et al. WWW 2017, Table 1).
- EOMM, matching to reduce churn risk, was a simulation on that data, not a live test: 0.3-1.1% more retained players
  per round at pools of 200-500, and no better than random at 100. The headline 15% is the authors' compounded
  extrapolation (same). Optimising a churn model can do this by giving some players deliberate losses.

Rule: cushion a loss streak (an easier match, a breather, a consolation) rather than leaving it to the rating. With a
small pool, fairness is a pool-size problem first: offer bots, ghosts or asynchronous matches (inference).

## A leaderboard is a goal, and the number at its top is the goal

- With a leaderboard, performance matched the difficult and impossible assigned-goal conditions (research, Landers,
  Bauer & Callan 2017, abstract; a brainstorming task).
- Points, levels and leaderboards raised output, not competence or intrinsic motivation (research, Mekler et al. 2017,
  snippet). Badges, leaderboard and graphs together raised competence; avatars, story and teammates raised relatedness,
  and the leaderboard bundle did not (research, Sailer et al. 2017, n=331, small effects).
- A ranking raised motivation and pressure together, driven by how much people compare themselves (research, HICSS
  social-comparison paper, snippet).

Rule: show a board only if you would assign the number near its top as the player's goal. Expect more output, not more
enjoyment; belonging comes from teammates and shared identity, not rank. Showing neighbours instead of the whole table
is untested (inference).

## Light social features in a single-player game or app

- In Sky, players who received or watched gifts later gave more and played more (research, Bisberg et al. CSCW 2022,
  abstract; observational). This is the only gifting result with behavioural game logs found.
- Verdict (inference from the multiplayer findings above): give relatedness a small, asynchronous, blameless channel:
  shared goals, gifts that cost nothing to send, co-op with no clock. Skip public stranger rankings, loss penalties and
  report systems: they bring pressure and moderation work and nothing says they help a game with no pool. A board, if
  any, is opt-in and friends-only.

## What the evidence cannot say

No study compares co-op, solo and competitive play for long-term retention or well-being. Nothing controlled on
gifting, visiting or friend leaderboards in single-player-first games. EOMM's live results were not found. The GDC
Vault slides behind the Riot and Blizzard figures were not reached. Leaderboard studies are single sessions, not weeks
of play.
