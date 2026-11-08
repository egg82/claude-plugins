# Making systems and automation legible

How to let a player see what a system will do, what it did, and why. Sources: `evidence/legibility.jsonl`. Primary
sources are thin: the GDC talks (Slay the Spire metrics, RimWorld, Into the Breach) have no transcripts, and Klei's
forums refuse scripted fetches. Several rules below are inference and say so.

## Show what will happen before it happens, so failure traces to a choice

- Into the Breach: "This lead us to use of telegraphed enemy attacks as a core mechanic"; "We prefer games with clear
  rulesets"; with every attack shown and little chance, "it's very clear how or why you failed so that you can feel
  like you can improve" (developer, Justin Ma, Game Developer Road to the IGF 2018). "A push to be more deterministic
  in the moment-to-moment gameplay" is Matthew Davis's; "no fog of war and no percentages" is the writer's wording
  (practitioner, PC Gamer). The system is made simple enough to show, rather than deep and hidden.
- Slay the Spire's "central innovation is enemy intents": early play is learning patterns, later play "all about
  having a plan" (opinion, LessWrong review). In Slay the Spire 2, intent icons carry damage and hit count
  (practitioner, snippet). Intents were not planned up front: they "came about over hundreds of hours of play testing
  with an eager Early Access audience" (practitioner, a repost of an Ars Technica interview with Mega Crit; original
  not reached). They replaced a "Next Turn" display that broke down with several enemies (snippet, a Wikipedia
  mirror's account of the Ars piece). A legibility fix found by watching players, not designed in.

Rule: few symbols, numbers printed on them. Intents show facts (damage 12 x 2), not advice; whether a game should
ever hand the player a verdict is a design stance, not a finding.

## In a player-written rule list, the order on screen is the logic

- Final Fantasy XII's gambits: a numbered list, slot 1 highest priority, offensive and defensive commands coloured red
  and blue; nothing described marks the gambit currently firing (practitioner, dev.to). Gambits were adopted because
  real-time combat risked being "too fast-paced and difficult" (developer, Kato, PlayStation Blog 2017). Katano,
  recalling Ito, says it was hard to judge whether it would work until the end (developer, same article).
- No developer source was found on how any rule-list game shows which rule fired (null, well supported for FFXII;
  Dragon Age tactics and Factorio circuits unread). "Players can see why the AI did that" is unestablished.

Inference: since order is priority, marking "this one is acting now" is the cheapest honest answer to "why did it do
that".

## Let the player choose which overlay is on

- "Once you enable ALT mode you rarely disable it"; players want per-layer choice, want recipes shown on machines and
  call module icons clutter; one turns the overlay off to spot idle machines (verbatim, Factorio forum).
- When the Beacon drew its modules on the entity itself, Factorio could "remove Alt-mode from the Beacon" (developer,
  FFF #351). Items and entities should explain themselves directly, through tooltips; tips only for what players
  actually don't get. A tooltip that showed recipe and hid spoilage was split into two hover targets (developer,
  Factorio Friday Facts #361, #426).
- Oxygen Not Included: one overlay per concern on its own hotkey, and a complaint that one overlay is nearly useless
  (verbatim, single player source, snippet; no Klei statement found).

Rules: put information on the thing when it is always relevant; keep an overlay for what is sometimes relevant; one
overlay or tooltip answers one question. A global all-in-one toggle ends up always on or always off (inference).

## A readout of state is not an explanation of an action

- Dwarf Fortress's look panel gives Relations, Thoughts, Needs, an Overview of "the highest priority information", and
  updates live (practitioner, PCGamesN). A UX reviewer came in "later than we should have" and produced the building
  menu among other fixes (developer, Tarn Adams).
- Sylvester aimed for "a simulation that was not overly complex, and that a player can observe and comprehend";
  RimWorld "shows enough that it constrains the imagination a little bit" (developer, Game Developer interview).
  Nothing was found on why a pawn acted or how the thoughts list was designed.

Inference: where a system acts for the player, show the state ("hungry") plus the condition that matched ("because:
hungry"). State alone leaves the player to guess the link.

## Let the player watch, share and compare their machine

"It's satisfying to watch factories work, and especially so when it's one of your own design"; Opus Magnum exports
GIFs and has several metrics to optimize (cost, area, cycles) (developer, Game Developer). Inference: watching rewards
the author of the system, not only debugging; separate numbers give more than one way to judge a solution.

"The ability to share functioning gifs has been a crucial part of Opus Magnum's success" (developer, Game Developer,
full; only the GIF-sharing point is in that article, nothing on histograms or metrics).

## State the ordering rule on an automation control

- Players report confusion over how automation chooses: one could not find an explanation, two found the priority
  order unclear (opinion, three Steam threads, snippets). RimWorld's Work tab (priority 1-4 per colonist per job) is
  called hard to read: its left-to-right order is the meaning and the tutorial does not say so. Leaf Blower
  Revolution's autobuy priority list is called confusing. Revolution Idle players could not find how autobuyers choose
  and had it explained by another player ("buys the lowest item available").

Rule (inference): state the ordering rule on the control itself: what runs first, and what happens when two are
ready. Extends "In a player-written rule list, the order on screen is the logic" with player reports, not only FFXII's
layout.

## Let the player see a change's effect without making it

- Spiel et al. name UIs that signal a change's effect without making it, citing Kittens' tooltips and chat
  channels, as a way to facilitate player safety (research, Spiel et al. CHI PLAY 2019; row in
  `evidence/genres/idle.jsonl`).

## What the evidence cannot say

No developer account of displaying which rule fired, why a rule didn't, or why a simulated agent chose an action. No
transcript of the RimWorld or Into the Breach postmortems.
