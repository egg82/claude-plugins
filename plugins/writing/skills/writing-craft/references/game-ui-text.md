# Game UI text

Upgrade and effect lines, counters, event logs, waits, blocked actions, choices and end-of-content messages in a
game, mostly incremental and story games. The product-UI rules in `ui-text.md` (buttons, case, errors, colour)
apply here too; this file adds what games do differently.

## Labels and effect lines

**Labels stay terse nouns and verbs; a line that says what a change does is one short plain sentence.** Every game
read keeps labels as bare nouns ("Eternity gain multiplier", "Inserter capacity bonus") and writes an effect as a
clause or sentence. None puts an arrow or "from X to Y" in a string meant to be read (practitioner: shipped
strings of A Dark Room, Antimatter Dimensions, Slay the Spire, Factorio, Cookie Clicker, sources below). No
published UX-writing guidance on arrow phrasing was found, so this rests on the games.

- **Subject first, then what it now does.** "the rickety cart will carry more wood from the forest" (A Dark Room,
  https://raw.githubusercontent.com/doublespeakgames/adarkroom/master/script/room.js); "The mouse and cursors are
  twice as efficient." (Cookie Clicker, snippet, https://cookieclicker.fandom.com/wiki/Cookies_per_Click).
- **Name the consequence the player cares about, over the stat.** "carrying more means longer expeditions to the
  wilds" (A Dark Room, same file).
- **A changed number keeps the sentence and changes only the number,** which the UI highlights. "Deal 6 damage."
  becomes "Deal 9 damage." (Slay the Spire, https://slaythespire.wiki.gg/wiki/Cards_List). Show the amount:
  incremental players ask how big an effect is before buying (opinion, snippet, https://itch.io/post/15706897).
- **Notation belongs in totals and compact lists; the single choice gets a sentence.** Antimatter Dimensions writes
  one effect three ways: "Multiply Eternity gain by {value}" for one source, "Eternity gain ×{value}" for the
  total, a bare noun for the label (https://raw.githubusercontent.com/IvarK/AntimatterDimensionsSourceCode/master/src/core/secret-formula/reality/glyph-effects.js).
  A Dark Room's rates are "+1 per 10s" in a tooltip because the prose lives elsewhere
  (https://raw.githubusercontent.com/doublespeakgames/adarkroom/master/script/engine.js).
- **A cap can be a consequence in the game's voice:** "more traps won't help now"; "no more room for huts." (A Dark
  Room). This is a voice choice for a game with a narrator; a plain "Max 10" or "Limit reached" is correct
  everywhere else, and product UI states limits plainly.
- **A count that changes is shown by its counter,** and the text narrates the event: "a weathered family takes up in
  one of the huts." while the population ticks (A Dark Room,
  https://raw.githubusercontent.com/doublespeakgames/adarkroom/master/script/outside.js).
- **A tier-up can be a comparison:** "iron's stronger than leather" (A Dark Room, room.js).
- **Restrictions are a plain sentence, second person, present tense:** "You cannot draw additional cards this turn."
  (Slay the Spire).
- **Gains and losses keep a fixed colour and position,** with a sign or word beside the colour (practitioner,
  snippet, https://terraria.wiki.gg/wiki/Tooltips; `plain-language.md`, colour).

**Worked example.** "Forge Lv 3 → output 4 → 6" puts two arrows on two axes (level reached, amount changed) and
drops the noun the number counts. Rewritten: *"Forge level 3: it makes 6 nails a batch instead of 4."* Or, with
the amount moved to a tooltip, A Dark Room's form: *"the forge makes more nails at once"*.

## Length of log lines

**Event-log lines in idle games run short.** A Dark Room's lines have a median of 34 characters, Universal
Paperclips' 38 (measured from their source: https://github.com/doublespeakgames/adarkroom,
https://www.decisionproblem.com/paperclips/main.js). A log line has to be looked at directly; reading span reaches
about 14 to 15 letters right of the fixation (snippet, Rayner 1998). These medians describe a scrolling log; they
are not a target for tooltips, help or story text. Much of Paperclips' story is in its project buttons
(practitioner, https://if50.substack.com/p/2017-universal-paperclips), so the words a player must read go on the
control.

## Text read again and again, and choices

Failbetter's rules for text a player sees many times (developer,
http://www.failbettergames.com/narrative-snippets-writing-for-story-games/ and
http://www.failbettergames.com/narrative-snippets-agency-and-choices/):

- **The more often a text is read, the shorter it is:** one sentence for a recurring description, a paragraph for
  an event; past four or five paragraphs is too far.
- **Lead with the important thing;** after the second read, players skim.
- **No semicolons or parentheses** in repeated text.
- **Success text a little longer or more interesting than failure text.**
- **A series of small two-option choices beats one big menu;** never re-offer the choice just made.
- **Reminders in content** reorient players who come back after a gap; **[advisory text in square brackets]** gives
  explicit guidance or a warning (developer, https://www.failbettergames.com/fallen-london-writer-guidelines-part-ii).
- **Many changes in one result make each matter less.**

Choices inside conversations are in `dialogue.md`.

## Rules, waits, blocks and ends

- **State a control's rule on the control.** The automation failure players report is not finding a feature but
  understanding its rules: RimWorld's work priorities, Leaf Blower Revolution's autobuy order, Revolution Idle's
  autobuyer choice (practitioner, snippets, e.g.
  https://steamcommunity.com/app/294100/discussions/0/1736594593603694059). Write the rule in a short line where the
  setting is ("runs the top card first; when two are ready, the cheaper one").
- **When something new can join an existing system, say so once, in plain words,** where the new thing appears. A
  marker dot gets noticed by beginners (developer, snippet,
  https://theshadowmaster.itch.io/atom-idle/devlog/1034482/atom-idle-051-alpha-v1-is-available-now), but a dot alone
  does not say what to do with the thing.
- **A wait states that it is a wait, and its rate or length.** Fallen London: "1 every 10 minutes, whether or not
  you're playing, up to the maximum of 20" (developer, https://fallenlondon.wiki/wiki/Beginner's_Guide). A wait that
  fits the fiction reads as acceptable; an arbitrary cap reads as a block, and relabelling the same numbers changes
  how players feel (practitioner, https://mobilefreetoplay.com/eliminating-energy/).
- **A blocked action says why it is blocked and what it waits for,** so retrying it has no appeal. A player with no
  reason on screen will tap the same blocked control again and again and then leave.
- **Never word a wait like a sales pitch for skipping it** when there is nothing to sell; timers that sell skips
  read as scarcity by design (opinion, snippet, https://unwinnable.com/?p=105117).
- **The end of current content gets a plain, out-of-fiction statement** ("This is as far as the game goes for now"),
  with a date only if one is true. In-world cues for the end are missed or read as a missing item; players ask for
  "a non-immersive popup that declares the end of the content" (opinion, player forum,
  https://steamcommunity.com/app/427410/discussions/0/6369856944156969129); Forever Skies' "End of current content"
  is what Aloft players wanted (opinion, player forum,
  https://steamcommunity.com/app/1660080/discussions/0/632293373538001141). A vague line like "wait for the events
  to unfold" was read as the end (opinion, snippet, https://itch.io/post/8051372).

## Voice

UI text and world text are separate registers. A label in the world's voice ("the hearth hungers") hides what the
control does; a world line in UI voice breaks the fiction. In a game without a narrator voice, keep effect lines
free of narration and questions to the player. A game with a narrator may write them in that voice, as A Dark
Room does above, provided each line still says plainly what changed. The project's voice doc decides which kind of
game it is.
