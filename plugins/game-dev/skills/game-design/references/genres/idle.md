# Idle and incremental games

What is particular to games that progress without the player: offline earnings, exponential costs, prestige, and the
return visit as the reward. The genre-neutral layers underneath are in `../motivation.md` (why players return),
`../economy.md` (curves, sinks, modelling) and `../feedback.md` (feedback for background processes). Sources:
`../../evidence/genres/idle.jsonl`. Nearly every developer row is one person, Anthony Pecorella of Kongregate, across
several talks; Spiel et al. and Buergi are the only research on the genre's design.

## The return is the reward moment

- Constant growth means no need to play constantly; a check-in makes "a celebratory moment every time that you
  return"; "the longer you're away from the game, the greater your incentive to return"; idle games act as a "natural
  energy system" (practitioner, Game Developer write-up of Pecorella's GDC talk). The speaker called Egg Inc's 2-hour
  offline cap "a mistake" and churned largely because of it. Genre players are motivated mainly by Completion and
  Power, a Quantic Foundry survey he cites (developer, Pecorella, GDC Europe 2016, slides read).
- Why no cap is needed: offline earnings grow linearly while costs grow exponentially, so time is "a release valve, a
  (somewhat) self-balancing system" and the cost curve is the soft limit. Absence is never punished, and nothing moves
  the player backwards: lost money or progress "feels against the spirit" of a progress machine. If players
  run auto-clickers, rapid tapping is optimal, which is "an error in design", not cheating (developer, Pecorella,
  GDC 2016 and MIGS 2016 slides, full text). It is the genre's case of Soren Johnson's rule that players will
  optimise the fun out of a game: whatever is optimal, players will do, however tedious (`overview.md`).
- Fifteen minutes can show a year's worth of the core loop, so the opening must also show what comes later
  (developer, Global Games Forum on AdVenture Capitalist, snippet; row in `../../evidence/onboarding.jsonl`).

Without notifications or streaks the pulls left are: a gap left open, a goal visibly near, a return that pays more the
longer the absence, and a choice the player made that is still working.

## Costs outgrow income, and the wait is the readout

- Idle games pace by letting costs outgrow income, and read the balance off one number: the wait until the next
  purchase. Prestige exists partly to "rein growth back into a more manageable number", and takes a root or log of
  earnings to do it. Smooth curves "lack surprise and delight"; targets should go "beyond just making bigger numbers"
  (developer, Pecorella, Math of Idle Games I and III, GDC 2016 slides).
- Part I plots each source's income over time and observes that the newest generator is nearly always dominant once it
  can be bought (developer, Pecorella, Math of Idle Games I). Inference: if that holds, the older sources carry no
  decisions, so a share-of-income plot is a cheap check.
- A model player that buys the best income-to-cost item at every chance lands "roughly in this ballpark" of
  what humans do, who usually bulk-buy; it over-favours higher-end, slower sources. A gain that is optimal
  but too small to feel is not worth the player's effort to consider (same source). The model is not a
  simulation (Pecorella's own caveat).

## Prestige: each run must get farther, and the reset needs a target

- The prestige formula sets the balancing target: with a square root a run must earn about 4x the last to double the
  currency, with a cube root about 8x (developer, Pecorella, Math of Idle Games III). A common rule of thumb is to
  reset at +50% to +200% currency (developer, Pecorella, GDC Europe 2016 slides); that fits endless games, and a game
  with a fixed run cost and an end needs its own target (inference).
- Each run's opening should go quickly and the player should get noticeably farther than last time. Changing some
  rules on a prestige so it is not just the same thing faster is (unverified). Make cycle lengths bumpy too: Part III
  recommends similar variation in prestige resets (developer, Pecorella, Math of Idle Games III).
- Expect any prestige model to be wrong right after a big milestone, since players keep going through the fast part
  (developer, Math of Idle Games III).

## Options must differ in what they give, not just how much

- Idle designers describe the genre as exploration with "little consequences of failure", and each new layered system
  should change the decisions (research, Spiel et al. CHI PLAY 2019).
- When almost any action boosts production, choice carries little weight (research, secondary, Buergi 2024).
- Gnorp Apologue's upgrades are optional and change behaviour; a multiplier per upgrade bought was rejected because it
  rewards buying everything (developer).

- A pure "which upgrade next" is close to a solved problem. In the Cookie Clicker model the optimal buy order has a
  polynomial dynamic-programming solution (fixed and increasing cost), a greedy algorithm approaches optimal for
  large targets, and only the discrete-timestep version is strongly NP-hard (research, Demaine et al., paper body
  read). Buying the best rate per cost lands near optimum (inference from that and the model player above).
- Opt-in constraint runs are the genre's answer to "I solved it". Antimatter Dimensions challenges are modified
  runs of a reset layer "entered at will"; completing one improves autobuyers or earlier mechanics, and Eternity
  challenges can be completed up to five times for a stronger reward (practitioner, wiki, full; intent not stated).
  Its developer says challenges were inspired by Idle Wizard, is proud of Reality for "plenty of choices to make
  and variance between player experiences", and admits the opening is a "click the green button -simulator"
  (developer, IncrementalDB interview, full). Players invent their own, such as beating a game without
  meta-progression (practitioner, thepaperpilot's guide, full). No account was found of why challenges work or how
  the autobuyer tuning was balanced.
- Dominance is prevented by interacting layers, not by capping any one: "multiple interacting mechanics" make players
  "constantly change their strategies" (practitioner, Machinations, full); Spiel quotes a designer on how a new system
  fits the existing economy and should change decision-making (research, as above).
- Idle Loops: "every single playthrough is a micro-prestige" and "automation persists fully between runs" (opinion,
  IncrementalDB review, full; one reviewer).

Rule (inference): decisions worth having are between things of different shape, where no single ratio ranks them.

The general method for decisions without a fail state (bottlenecks, no solve button) is in `../motivation.md`.

## Automation: when it arrives, and what it does to decisions

- Players resent a long hand-work phase before automation. Revolution Idle gates autobuyers behind many resets:
  "I don't want to get carpal tunnel because I need to spam clicks for many hours to unlock autobuyers"; one player
  defended the delay as deliberate (verbatim, one Steam thread, full).
- Factorio's old tutorial took 30-45 minutes to reach automation; the redesign put the core automation concept in the
  first level (developer, FFF #241, full; row in `../../evidence/onboarding.jsonl`; detail in `../onboarding.md`).
- AdVenture Capitalist and Universal Paperclips offer automation as soon as money exists: tap first, then buy the
  thing that taps for you; Paperclips chains tiers by count (MegaClippers after 75 AutoClippers) (practitioner,
  snippets). No designer statement on why was found.
- Players split on whether automation removes the decisions or is the decision. Against: "There aren't any interesting
  decisions to make; you are at best grinding out the ability to automate a task" (opinion, Increlution player
  comments). For: Idle Awakening's "powerful, flexible and relatively simple" action lists, and Idle Loops' saved
  movelists to "hotswap between" (opinion, IncrementalDB reviews, single sources, weak individually). Reading
  (inference): automation earned as a grind draws the complaint; automation as the player's own plan draws the praise.
- Demand for automation the base game does not give shows up as third-party scripts: Melvor Idle (action
  queue, auto-sell, triggers) and Kittens Game (Kitten Scientists) (practitioner, snippets; what the base
  games offer was not confirmed).
- Queue-style offline play is a common model. Milky Way Idle's queue runs offline until empty or a limit (default
  10 h, extendable in the paid store) and skips an action whose materials are missing; Increlution's auto-pauses
  when the queue is empty; Kittens Game banks offline time as a resource to spend later; Idle Fantasy's wait is the
  loop ("return up to an hour later to collect") (practitioner and developer, wiki and Steam snippets, not stated
  for the Milky Way page).

## Benchmarks, for context only

- Mobile idle games averaged 8 min per session, 5.3 sessions a day and 18% DAU/MAU; top-10% idle games had D1 45.55%
  (practitioner, GameAnalytics blog, read not stated; sample and period not stated; mobile with notifications, so
  these are visit habits that design produces, not targets). Browser-idle session or retention numbers were not found
  (Pecorella's 2015 talk with Kongregate metrics is members-only).
- One indie developer's prestige-timing opinion (first prestige at 25-35 min, wished 15-20) is opinion
  without data (opinion, snippet).
- Clicker Heroes: no offline cap, idle damage only, ascension needs the player present (developer, blog, read not
  stated); a no-cap data point only.

## Genre expectations

An idle player expects progress as a milestone: a build, a level, a count going up. A goal outside that model, such
as keeping several lines in balance, reads as unintuitive however plainly it is worded (inference, an illustrative case:
an ending gated on several production chains held in balance; see SKILL.md's genre-fit rule and
`../../evidence/genre-fit.jsonl`).

## What the evidence cannot say

No source gives how often a good idle game should ask for a real decision, or a "new thing every N minutes" rate. No
developer account of feedback design inside Cookie Clicker, Melvor Idle, Kittens Game or Antimatter Dimensions, and no
postmortem on how an idle game's screen grows, was found. No idle-specific drop-off or retention data.
