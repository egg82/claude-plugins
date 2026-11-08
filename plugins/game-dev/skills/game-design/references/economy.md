# Economies, currencies and balance

Resource flows, sinks, cost and XP curves, multiple currencies, persistent online economies, balance between options,
and modelling an economy before players touch it. Sources: `evidence/economy.jsonl`. Idle-specific cost and prestige
math is `genres/idle.md`. Most economy evidence is designers' statements of intent and practitioner courses; the
research (Castronova, Dormans, Heeks at abstract level, a bachelor's thesis) measures no design intervention. No maker
has published a measured effect of a sink on inflation.

## Model currencies as sources, drains, converters and traders

- Sources create a resource, drains destroy it, converters swap one for another, traders exchange between players.
  Any engine where income buys more income is positive feedback: it "amplifies small differences" and runs away, and a
  game with only positive loops seems "too random" to many players (research, Dormans 2012 thesis, partial).
- A static drain (fixed upkeep) makes upgrades worth more and sharpens the engine; a dynamic drain (scaling with
  wealth or progress) adds a true negative loop (same).
- Game goods are "costlessly created and destroyed", so the designer can peg any price; sinks are a design choice, not
  a market outcome (research, Castronova 2002, partial).

Rule: draw each currency's sources and drains before tuning numbers, and give every positive loop a counter-loop on
purpose.

## Every faucet ships with its sink

- Chart currency earned against currency spent over time; a persistent surplus of earned currency means players have
  nothing worth buying (no sense of scarcity). Leave purchased currency out, and after a balance change distrust the
  readings while players spend down stockpiles (guideline, Android Developers Blog, Mabin 2015).
- Path of Exile's makers before launch: "Games that use gold incur high inflation unless they have sufficient gold
  sinks"; such sinks are "negative mechanics that impose a burden on the player". They dropped repair costs and made
  consumable currency items the currency; most trades end with the item consumed by the recipient (developer, GGG dev
  diary 2011, via fetch summary).
- WoW took the other road: repairs, travel, and luxury sinks such as mounts and pets (opinion, Engadget 2012,
  snippet). No Blizzard statement on gold inflation or sinks was found (null, searched).
- Lehdonvirta's GDC 2014 talk catalogues six currency sinks and eleven item sinks; only the abstract was reached
  (practitioner, abstract).

Rules: name the sink in the same change that adds a faucet. Choose between tax sinks (repairs, fees: a burden that
feels like one) and luxury sinks (mounts, cosmetics: spending players want); a consumable currency makes the sink the
currency itself (inference from GGG).

## Single-player wealth is a pacing problem, not an inflation crisis

The game controls the money supply, and wealth drifts toward abundance unless capped, which is acceptable in
single-player (practitioner, Hofmann 2009). So runaway wealth mostly flattens late choices or clashes with tone
(inference). The sinks that matter are cost curves that keep late purchases
meaningful; skip faucet-and-sink machinery built for persistent worlds.

## Pick the cost curve from the game's length

- Increasing curves (twice as good costs more than twice as much) make late options strong and suit long games;
  strictly linear is "pretty rare"; decreasing curves fit where hoarding has an opportunity cost (practitioner,
  Schreiber, Game Balance Concepts Level 3, partial) and favour early play (practitioner, student notes of Schreiber).
- A choice should cost more than its parts: an X-or-Y option is priced above X and Y apart (practitioner, student notes
  of Schreiber, secondhand).
- Small rate gaps compound: 1% faster scaling is 1.35x by level 30 (1.01^30), and the faster subsystem eventually owns
  the late game (practitioner, Kill Ten Rats 2008). Keep player power and challenge on different curves on purpose;
  exact matching is boring (practitioner, same).
- A flat XP step per level grows "increasingly easy to fulfill"; aim for rising but not predictable, and hand-tuned
  per-level tables are normal (practitioner, Khaw, Game Developer 2014). Specific exponents (1.0 / 1.5 / 2.0) circulate
  without a source (unverified).
- Replace a hard cap with a bounded soft cap when hitting a wall kills the feeling of growth (developer, Ravendawn dev
  blog 2023, one small MMO, no outcome data).

## Balance means many viable options, not equal power

- Balanced means "a reasonably large number of options" are viable; a dominant option is "strictly better than any
  other" and the worst problem a competitive game can have. Judge fairness globally, not per situation; non-viable
  options "get in the way" (practitioner, Sirlin, Balancing Multiplayer Games 1 and 2).
- Transitive designs (some options simply better) balance by cost; intransitive ones (rock-paper-scissors) by counters
  (practitioner, Schreiber notes).
- Johnson: players will optimise the fun out of a game; Civilization IV priced the dominant strategy with a per-city
  cost that grows with city count (developer, Soren Johnson, `genres/overview.md`).
- For pick-one-of-many content, pick rate and win rate come first: nobody picks it, it doesn't exist; it wins too
  often, it's too strong. Data doesn't say how it feels (developer, Mega Crit via Game Developer, secondhand).
- Riot audits its buff-to-nerf mix: when over half of changes are buffs it also looks for nerfs, compares predicted with
  actual post-patch win rates, and nerfs if any skill audience is over, buffs only if all are under (developer, Riot
  /dev 2020).
- When unsure, err weak: a weak option can be buffed quietly; a strong one gets nerfed against players who adopted it
  (practitioner, Schreiber notes; second half inference).

## A parallel currency needs one job the main one can't do

- Legitimate jobs: steer players to a mode, isolate an event economy, turn duplicates into a chosen item, keep premium
  goods scarce (practitioner, Barnes 2021). Hearthstone's dust, made by destroying cards and spent on chosen ones,
  stands in for trading (opinion, Engadget 2013; Blizzard's own rationale not found). Two currencies earned and spent
  in the same places should merge (inference).
- Destiny 2 reportedly cut about 24 currencies to five over a year and a half for clarity and newcomers (opinion,
  mein-mmo; no Bungie quote). It is the nearest real-game data point on "too many".
- The hard/soft split (cash-bought vs earned) is a monetisation device; its converter rate is where one currency eats
  the other (practitioner, Barnes; Unity guide, snippet). With no cash shop, there is no reason to copy it.
- If any currency is sold for real money to EU players: show prices in real money, sell the amount needed, and avoid
  "mixing different in-game virtual currencies or requiring exchanges" (guideline, CPC Network Key Principles on
  In-Game Virtual Currencies, 21 March 2025, non-binding, via the European Commission page and a Linklaters summary for
  the quoted detail; earn-only currencies are out of scope).
- Whether virtual currency raises spending: a 2026 UK loot-box experiment (n=753, venue unidentified) reports higher
  willingness to pay in virtual currency; an Aalto lab study found currency conversion did not raise spending
  (snippets, mixed).

Rule (inference; no study measures how many currencies players can track): give each currency one visible job and
show what it buys on its own icon. A third currency needs a stated reason the first two can't meet.

## Persistent online economies: plan for the cash market and for scarcity

- Earned currency in popular online games gets sold for cash: a Norrath platinum piece traded at US$0.0107 in 2001
  (research, Castronova 2001, abstract). Before Bonds, Jagex reported about 170 billion GP a day sold from farming
  accounts and "well over 40%" of active players buying from third parties (developer, Jagex Bonds blog, pre-launch).
- The shipped answer is a company-run cash-to-gold channel. Blizzard's WoW Token launch post says third-party gold
  "negatively impacts the game experience for everyone"; the price floats and the auction house takes no cut
  (developer, Blizzard 2015). Hazzikostas later suggested it had reduced illegal gold selling, and said "we're not
  looking to become a bank" (developer, via Wowhead's summary of a Glixel interview). Neither company published
  post-launch figures.
- RuneScape removed free trade and the Wilderness to fight real-money trading, and restored both on 1 February 2011
  after over a million players voted for it (opinion, Engadget; vote figures snippet). That the restriction mainly cost
  honest players is inference from the vote.
  A cap on what free accounts can give away targets where farming happens (snippet).
- Diablo III's real-money auction house closed because it "ultimately undermines Diablo's core game play: kill
  monsters to get cool loot" (developer, Blizzard 2014). The reason was the earn loop, not prices.
- EVE: CCP called its economy "unsustainable" in 2020, since "loss is not meaningful anymore for veteran players", and
  planned three phases: a shortage phase, a redistribution phase fitting income inside a defined healthy range, and a
  self-regulating distribution system. It reported botting income cut 80%. Its Dynamic Bounty and Encounter
  Surveillance Systems were built "to dynamically curb excessive system outputs" (developer, CCP devblogs 2020).
  Players report activity fell over two years of scarcity; a fan editorial quotes CCP that "the era of scarcity will be
  a temporary one" (opinion, forums and blogs). CCP publishes a Monthly Economic Report (opinion, forum threads; its
  definitions unread).
- RMT fits ordinary economics: exchange rates, scale economies, information failure (research, Heeks 2010, abstract).

Rules: decide on day one whether you sell currency yourself or make it costly to farm; one of the two happens anyway.
Put limits at account creation, not on trade. A scarcity correction is a real cost to players' fun; say up front how
long it lasts (inference).

## When the input is a person's real actions (gamified apps)

- Income is roughly flat per person and differs several times over between people, so a curve's shape can't even out
  time to a fixed threshold: that time is threshold ÷ income. A permanent multiplier with no reset compounds with every
  new income source and needs a cap (inference).
- The wait to the next unlock is a readout, not a target. Tuning it makes the next number the point, the lever case in
  `motivation.md`. Ask whether each action visibly does something that belongs to the person, at the light end too. A
  pacing question about how many weeks a light user needs to reach an unlock is the sign the frame is wrong
  (inference).

## Model before playtesting, through the game's own code

- Artificial players with distinct strategies, run thousands of times, find dominant strategies crudely and cheaply
  (research, Dormans; practitioner, Adams 2012). Internal-economy modelling suits board, strategy and management games
  and scopes badly for abstract games like chess; Machinations holds whole numbers only and is "not designed for
  building complete games" (same).
- Averages mislead: use many randomised runs, since players don't play the optimal pattern (opinion, Machinations
  vendor blog).
- Model the time to the next goal for a light, a median and a heavy player. The model must call the game's own rules:
  a hand-written re-implementation drifts as the code changes (inference: a second copy of the rules that nothing keeps in sync).

## What the evidence cannot say

No maker's measurement of any sink's effect on inflation (WoW, RuneScape, EVE). No post-launch data on the WoW Token or
Bonds. No study of how many currencies players can track. No study of how often pre-launch economy models predicted a
launch, and no postmortem of a wrong one. Unread: Schreiber & Romero's "Game Balance" and Schreiber's XP-curve chapter,
Adams & Dormans chapter 4, Lehdonvirta & Castronova's "Virtual Economies", CCP's Monthly Economic Report definitions.
