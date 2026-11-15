# Friction and quality of life

Quality of life is a tool, not a virtue. A convenience that removes friction can also remove the decision, discovery,
tension or sense of place the friction was carrying, and then the game is smoother and emptier. Ask a QoL feature to
"add something beyond comfort" (Razbuten, "Qualitying The Life Out of Games", 2026; full transcript read).

## The test, before adding or removing friction

Ask, in order (a working synthesis of the sources below, not any one source's list):

1. **What did the friction carry?** A decision with a cost, a discovery, tension, a sense of the world's size or place,
   or the reason the next system exists. If nothing, it is tedium: remove it.
2. **Does it still carry that on the 50th time?** Friction wears out with repetition; what bit on the first night can
   frustrate on the tenth runback.
3. **Can the bypass cost something,** so it stays a decision rather than a skip?
4. **Can it arrive later,** once the loop has been learned, or be opt-in?
5. **What does the freed time buy?** A removal that leaves nothing in its place made the game shorter, not better.

## What the evidence supports

- **Good friction carries a decision with a cost; friction without a tradeoff is tedium.** Interesting decisions come
  from giving something up; Old World's tile micromanagement was cut because its decisions had "no costs or are
  temporary" (Soren Johnson, designer-notes.com/?p=2087, read via summary). A choice always made the same way is not
  interesting (Sid Meier, GDC 2012, write-up only: check the talk before quoting).
- **Delete the rote decision itself; keep a bypass only as a resource.** Johnson made yields permanent instead of adding
  a skip. Pragmata's autohack works because it spends a gauge that competes with a better use; Dawnwalker's skill tree
  lets you opt out of combat and puts nothing in its place (Razbuten).
- **Friction is often why the next system exists, so time the convenience.** Factorio keeps early mining slow so there
  is a reason to automate, and dresses the wait (Kovarex, FFF-106). Minecraft's bed is cheap and early and undercuts the
  night loop; Dark Souls' Lordvessel gives fast travel late, after the world has been walked (Razbuten).
- **Judge a convenience against the game's intended experience, not "every game has it".** Fields of Mistria moves
  Stardew's friction rather than removing it, to make the town feel alive (Razbuten); friction aligned with the intended
  experience is a design tool (the Space Warlord developer, Game Developer, read via summary). "It's only an issue because
  your game is boring" on fast travel (Itsuno, snippet only).
- **Discovery friction makes memories and sweeter rewards; offer guidance optionally.** Navigating by observation and
  treasure-map steps beat following a waypoint, which lays a "video game layer on top" of the world (Mark Brown, GMTK
  "Following the Little Dotted Line", full transcript). Banquet for Fools has no quest log, and a player recalled a
  two-month gap in two minutes from their own notes (Razbuten; one player's report).
- **Fast travel, minimaps and markers began as concessions** that made bigger worlds playable; as defaults they show
  diminishing returns (Razbuten). Settings and accessibility options are always fair; changes inside the core loop are
  where the cost lands.

## In idle, automation and teaching

- **Automation is the clearest case of test question 4:** hand-play first, so the player feels the chore the automation removes
  (Kovarex). Whether to gate *when* automation arrives is open; gating *which conditions* a rule may test is not
  (`legibility.md`).
- **Over-teaching is QoL applied to learning:** a tutorial that explains every concept removes the discovery that makes
  a system the player's own (`onboarding.md`, "no need to explain every single concept"). Teach the one thing the
  player cannot find; let them find the rest.

## Auto-resolve in strategy games: the bypass that costs

Strategy games' auto-battle is the clearest worked case of test question 3. It is opt-in, and when it resolves worse
than manual play the choice stays real: auto-resolve the trivial fights, fight the ones that matter by hand.

- **Auto costs more than manual:** Age of Wonders: Planetfall's auto combat "generates much larger losses than in case of
  manual combat" (gamepressure guide, read in full; third-party, not the developer).
- **A forecast before committing:** Total War: Warhammer III's battle design shows the predicted outcome before the player
  commits (a Creative Assembly designer quoted by GameWatcher, read in full); Songs of Conquest's Quick Battle shows one on
  the deployment screen (guide, snippet only).
- **See the auto result, then retry by hand** is widely remembered from the Heroes of Might and Magic family (Heroes III
  HotA, Heroes VI), but unconfirmed: only player comments and search summaries, and HotA's release notes don't mention it.
  The pattern spends the player's effort only where the automation falls short; treat it as a design idea, not a sourced
  convention.
- **No developer's stated reasoning was found** for any of these. Sources: `evidence/autobattle-sources.jsonl`.

## Gaps

No designer words found on skip buttons or auto-loot, none on idle-game automation beyond Factorio, and no retention
data: every claim here is designer or critic argument. Not yet read: Pecorella's idle-game GDC talks, the Game Wisdom
friction essay (403), the DiGRA friction papers.
