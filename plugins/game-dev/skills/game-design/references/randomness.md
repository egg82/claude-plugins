# Randomness, odds and reward schedules

When to use chance, how players read it, how to weight it so it feels fair, when to show odds, and what the loot-box
evidence says. Sources: `evidence/randomness.jsonl`. Most sources are press reports of talks, fan wikis and search
summaries; no study was found that tests pity timers, PRD or streak breakers on satisfaction or retention. The
developers' own reasons for PRD, pity timers and 2RN were not found.

## "Feels random" is the target, not "is random"

- Players don't read displayed odds as written: an 85% shot is not felt as a 15% miss (developer, Jake Solomon on
  XCOM, via CogConnected), and Solomon described his own frustration at misses (developer, interview).
- Ratio perception isn't mathematical: Civilization Revolution's testers accepted losing at 2-to-1 but were upset losing
  at 20-to-10, and the team concluded combat couldn't be pure maths (developer, Meier GDC 2010, via Game Informer; talk
  not read).
- Shipped games weight the distribution:
  - Dota 2's pseudo-random distribution raises the chance after each failure and resets on success (practitioner,
    Liquipedia, snippet).
  - Hearthstone guarantees a Legendary within 40 packs and within an expansion's first 10, with no duplicates until the
    set is owned (practitioner, wiki citing Blizzard).
  - Slay the Spire's rare-card chance climbs 1% per common offered and resets on a rare (practitioner, fan wiki,
    snippet).
  - XCOM Enemy Within reportedly guarantees no fourth straight miss on Easy, and does nothing of the kind on Classic
    (developer, Anand Gupta via PCGamesN, secondhand).
  - Shattered Pixel Dungeon prefers summed dice (roughly 2d6 over 1d12) to pull damage toward the middle (snippet).
- Fire Emblem's "2RN" displays 80 and actually rolls about 92, and displays 20 and rolls about 8; later games show the
  true number below 50 (practitioner, Fire Emblem Wiki; no designer rationale found).

Rule: weight randomness for feel, but keep any number you show true. PRD, pity timers and shuffle bags keep the stated
rate true on average and only cut streaks and bound the worst drought. A displayed percentage that the game silently
inflates (2RN) breaks the promise that shown numbers come true, and the players who do the maths are the ones a
show-the-odds game is for. If the feel needs better odds, raise the real odds. XCOM Enemy Within hides help on easy
modes and gives none on hard; decide on purpose whether reloading re-rolls (inference, from the sources above and the
SKILL.md rule on shown numbers).

## Input and output randomness: the folk rule is unsettled

- Output randomness falls between a choice and its result (dice combat); input randomness comes before the decision (a
  generated map, a shuffled hand). They are a continuum: a generated map that makes a run unwinnable wrecks planning as
  surely as a bad die roll (practitioner, Burgun, Game Developer 2014).
- One controlled study found the reverse of "input good, output bad": in a card game, input randomness lowered
  satisfaction (p=0.024) and output randomness had no significant effect; participants said the modes without input
  randomness allowed more strategic planning (research, Zhang et al. 2021, arXiv, n=18, one custom game; the authors
  call it likely underpowered).
- Output randomness distorts the feedback a player learns from and "will in general lead to unfair results"
  (practitioner, Fischer 2015).
- Randomness needs a collection of systems and rules to be more than "a glorified slot machine" (developer, Derek Yu,
  Spelunky book excerpt, via summary).

Rule: put chance where the player can still plan around it (shown odds, low variance, a choice after the roll), and
playtest your own game rather than adopting either camp.

## Loot boxes: show odds, and know the harm evidence is correlational

- Loot-box spending was associated with problem gambling more strongly than other paid items (eta² .054 vs .004, n=7,422,
  direction unknown) (research, Zendle & Cairns 2018, abstract). A meta-synthesis found a mean r=.27, positive in 12 of
  13 publications, with causal direction unestablished (snippet, Spicer et al. 2022, via summary).
- Of 879 players in China, 84.6% of loot-box buyers had seen the odds and 19.3% of those said they spent less (research,
  snippet; self-report). Disclosure is table stakes, not protection (inference).
- Belgium's Gaming Commission judged paid loot boxes in three of four games examined to be games of chance (2018);
  China has required published odds since May 2017 (regulatory, via press, snippet).
- No human study was found testing that variable-ratio schedules in games cause addiction; the mechanism comes from
  animal work (null; `fun.md` on "dopamine").

Rules: show odds for any paid chance. In a gamified app, never mix paid chance with progress rewards (inference).

## What the evidence cannot say

No outcome study of pity timers, PRD or streak breakers. No primary Valve, Blizzard, Firaxis or Intelligent Systems
statement on why they exist. Unread: Meier's GDC 2010 talk, Costikyan's "Uncertainty in Games", Garfield, Engelstein's
and Shattered Pixel's talks. The Belgian report and Chinese notice were reached only through press coverage.
