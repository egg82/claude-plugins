# Where progress is: goals, gates, waits and the story marker

How a player knows what moves the game forward: which goal counts, what reaching it means, what a wait depends on.
The route to a goal is the player's to work out; where the goal is, and what it means, is not. Sources:
`evidence/progress.jsonl`. The guidelines are firm on showing the current objective; nothing found tests hidden
gates or hidden clocks directly, so several rules below are inference and say so.

## State where progress is; leave the route to the player

- Playability heuristics: "Provide clear goals, present overriding goal early as well as short-term goals throughout
  play" and "A player should always be able to identify their score/status and goal in the game" (research, Desurvire
  et al. CHI 2004, HEP; heuristics adapted from productivity software, not an empirical ranking).
- In 108 critical game reviews, "training and help" (36 of 285 usability problems) and "game status information" (28)
  were among the most common complaints ("The map function reveals everything about a particular location except
  where you are"); "Provide users with information on game status", objectives included, became a heuristic. An
  evaluator: "Still don't understand what I'm supposed to be doing" (research, Pinelle et al. CHI 2008, read in full;
  reviews and expert inspection, no players tested; nothing on unlock conditions).
- "Players can review current tasks and objectives at any time", including "what they should do next"; waypoints and
  hints are optional, offered when the player has made no progress (guideline, Xbox XAG 109). A reminder of the
  current objective, shown permanently, on request or automatically (guideline, Game Accessibility Guidelines).
- "Will players know where to go for their next objective?" is a stock games-user-research study question (snippet,
  GUR book extract); a team's playtests found missed next-step instructions did the most damage (snippet, gamedev.net
  "7 UX Lessons"). No source ranks it as the top playtest finding.
- Idle-game players report "no idea how to open the doors" and ask how a store unlocks (snippet, itch.io and Steam
  comments).
- **Counterexample:** Pathologic 2 deliberately drops main and side quests and does "not reveal how many such nodes
  are ahead", but keeps a visible map of what has happened; the designer says it may not suit every game (developer,
  Ice-Pick Lodge). Hiding the extent of what remains is a choice a game can make; hiding what moves it is not the same
  choice.

Rule (inference from the above): **any condition that unlocks something shows as a goal the player can read before
meeting it, with what meeting it means.** A gate a player can meet only by accident is a defect: the player who
meets it learns nothing, and the one who doesn't has no lead. Stating the goal is not stating the route. "Reach harbour tier 3" leaves the how open.

## Marking the route is a separate choice: the yellow-paint trade

The 2023 yellow-paint argument (Resident Evil 4 remake, Final Fantasy VII Rebirth, later Assassin's Creed Shadows) is
about marking the *route*: painted ledges and boxes. It is not about marking the goal.
- Developers on record say playtests forced it. Of Assassin's Creed Shadows: "we didn't have it until players were
  really struggling in playtests to find their path... giving a bit of guidance was needed" (developer, Dumont,
  Ubisoft Quebec, via 80.lv; no numbers). Final Fantasy VII Rebirth's director: "there are definitely times where that
  is needed" (developer, Hamaguchi, via Kotaku). Designers answering the backlash: "Someone has never sat in on an
  observed playtest"; "people skip over environmentally realistic props" (verbatim, Faliszek and a Ubisoft designer,
  via Know Your Meme). The "players are dumb" framing is the headlines', not any developer's quoted words.
- Why realistic art needs it: "the push towards more realistic art increases the need for more unrealistic visual
  cues"; "realism is less immersive", since immersion is flow and "the things that break immersion are the things
  that break your flow... you know what you need to do but can't figure out how to interact with the game to do it";
  "Trying to open 30 doors to find one we can go through breaks immersion" (practitioner, Schubert, Boss Fight, via
  GamesRadar 2023, which quotes the thread at length). An artist who thought "Players aren't stupid. Let them
  explore" saw one playtest and said "put it back" (practitioner, Hoffstein, The Division, same article).
- The case against: "If it feels like it's like 'go here,' it's not anymore a decision for the player. Somebody
  already decided for you"; the same director concedes the risk of being "impenetrable" (developer, Kasurinen, Control
  Resonant, Game Developer). Paint steals "opportunities for players to discover things on their own" (opinion, PC
  Gamer).
- The alternatives cost playtesting: Arkane called avoiding paint "a choice and investment" needing "a constant dialog
  with the playtesters", using lights, sounds and in-world signs, and still painted one ledge red (developer, Bakaba,
  Deathloop, via GamesRadar). Naughty Dog's Emilia Schatz: "Explicit and Defined messaging break immersion and so
  should be considered a fallback plan"; shape and structure do the subtle work (practitioner, 80.lv write-up). Use
  every guidance tool so each can be subtle (developer, Tost, The Witcher 4, GamesRadar). Star Wars Outlaws ships an
  "Explorer Mode" that turns off the "guiding color on core navigational elements" (opinion, PC Gamer preview; not
  tested in the writer's build).
- No controlled study measures paint against getting lost or immersion (null). Milam and El Nasr's guidance patterns
  (Path Target: a "visible landmark to attract movement", used "in a similar way as wayfinding signage") come from four
  designer interviews and video coding, with no player testing; one of their games keeps its goal abstract ("Go to the
  Data Center") (research, Sandbox 2010, read in full; descriptive, so evidence for neither side).

Rule (inference): **mark the goal always; mark the route only as far as testing shows it is needed, and offer a
toggle when you do.** Players resent being told how; no one has argued for hiding where. Explicit route marks are the
fallback after shape, light and landmarks fail with cold testers, and the fallback is cheaper than the iterations the
alternatives need. In an idle or menu game the route is the player's plan (which resource, which upgrade), so route
marks amount to advice, which `legibility.md` treats as a design stance, not a finding.

## With several tracks, mark the one that moves the story

- XAG 109 asks for the objective log "ideally separated by main vs side quests" (guideline).
- No developer source was found on marking the critical path among many progress bars (null; Breath of the Wild and
  Elden Ring searched, nothing primary). Pathologic 2 is the deliberate opposite (above).

Rule (inference): when a player sees several bars that can fill, put a story marker on whatever the next beat waits on
(whatever bar or building the next beat waits on), plus one short line where a wait or a mix of conditions needs
words.

## No hidden clocks on progress

- "The design should always keep users informed about what is going on" (guideline, Nielsen Norman Group heuristic 1;
  not game-specific).
- The famous timer complaints are about **visible** clocks found too harsh: Fallout's water chip deadline is shown in
  the Pip-Boy with reminders, and Avellone prefers System Shock 2's, where expiry leaves you "inconvenienced, not fail
  the game" (practitioner, Avellone; snippet for the Pip-Boy detail). Capcom dropped Dead Rising 4's timer because it
  kept players from side content (snippet). Harshness and hiddenness are separate defects.
- Stardew Valley gates events on unshown delays (a child event about 14 days after agreeing) with no complaint found
  (snippet, wiki). No developer statement on timer visibility was found for Majora's Mask, Pikmin or Animal Crossing
  (null).

Rule (inference): a clock is fine; hiding it is the defect when progress waits on it. Show any wait the next beat
depends on with its countdown and what pauses it. A wait that only gates flavour can stay hidden: Stardew's quiet
delays draw no complaints.

## A gate names its condition, not its find

- Curiosity follows a perceived "gap in knowledge" (research, Loewenstein 1994, abstract only). Players like "a
  delicate balance between uncertainty and the anticipation of future rewards" (research, Tang and Kirman 2024,
  questionnaire; does not test this pattern).
- Hidden achievements split players: accepted when they reward discovery, called "really unfair" when they hid a
  completion list (snippet, forum threads and one reviewer).
- No study tests showing a gate's condition while hiding its reward (null).

Rule (inference): show "Cartography rank 4" in the slot, then the item once found. Naming the find in the goal spends
the surprise before it lands; hiding the condition spends the player's lead. The condition is progress (state it);
the find is story (keep it).

## Design checks

- List every condition that unlocks anything. Can a player read each one before meeting it?
- With every progress bar on screen, can a cold tester say which one moves the story?
- Does anything the next beat waits on change without showing its value, rate or what pauses it?
- Does any goal name the thing it unlocks?

## What the evidence cannot say

No study of hidden progress gates, hidden progress clocks or condition-shown, reward-hidden goals. The rules here rest
on guidelines and review-derived heuristics for objectives, plus inference.
