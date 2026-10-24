# Dialogue

How characters talk, how to keep several voices apart, and what changes when the dialogue is in a game. Jokes are
in `humour.md`; speech written to be performed is in `speech-and-scripts.md`. The craft rules rest on working
writers; the game rules on developers' talks and devlogs. No measured study of dialogue quality or of distinct
voices was found.

## What carries over from prose and film

- **Plain tags, in English crime and literary prose.** "Said", no adverb: any other tag verb is the writer
  intruding on the line ("he admonished gravely") (practitioner, Elmore Leonard,
  https://fs.blog/elmore-leonard-10-rules-of-writing/). Over-varied tags (murmured, breathed, exhaled, rasped) are
  a named model tell (practitioner, https://www.sleuthsayers.org/2026/02/what-ai-fundamentally-misunderstands.html).
  The rule is a house style, not a law: children's books and much genre fiction tag more freely, and French and
  Spanish dialogue conventionally varies its verbs. What stays a tell everywhere is a tag doing the line's work.
- **Catch speech by rhythm and word choice.** No phonetic dialect or pages of apostrophes; let how people speak
  identify them (practitioner, Leonard). In "Hills Like White Elephants" the only physical detail is a hat coming
  off, and the speech does the rest.
- **"If it sounds like writing, I rewrite it"** (practitioner, Leonard). Text-game players flag dialogue polished
  with no human voice in it (practitioner,
  https://sindome.org/bgbb/game-discussion/game-problems/ai-generated-writing-ic-721/).
- **Speak around the feeling.** On-the-nose dialogue says exactly what a character feels ("I am very angry with you
  right now"); subtext keeps the meaning and changes the surface ("It's funny how you always know what to say to
  ruin my day"), through action, deflection, a changed subject, an unfinished thought (practitioner,
  https://nofilmschool.com/on-the-nose-dialogue). A blunt line is fine when the scene has earned it, and children's
  text and plain-language text say the feeling outright.
- **Give a speaker only the details that person would notice,** and vary their sentence shapes.
- **Register belongs to the world.** In a secondary world, modern or managerial idiom is the quickest giveaway of
  fake fantasy (opinion, Le Guin, "From Elfland to Poughkeepsie", snippet). In contemporary fiction the giveaway
  runs the other way: speech too formal and complete for the people saying it.

**Model dialogue failures,** named by critics, not measured (opinion,
https://www.wayline.io/blog/ai-dialogue-trap-authenticity-in-storytelling): voices that converge on one neutral
narrator; speech too smooth, with no interruptions, fragments or tangents; predictable replies; a register that
slips out of character; flat sarcasm, irony and understatement; a narrow emotional range. In games, a written
register where speech belongs (opinion, snippet, intfiction.org). **Fix:** decide the emotional beat and the
speaker's voice before writing the line, put the fragments and interruptions back, and hand-write scenes that run
on subtext.

## Keeping voices apart

- **Cover the names.** Hide the speaker names over a page of dialogue; if you can't tell who is talking, the voices
  are not distinct (practitioner, a script readers' test,
  https://www.moviemaker.com/first-draft-seven-ways-to-give-your-characters-fresh-voices/3).
- **For model-written dialogue, keep a speech profile per character and load it whenever they speak:** cadence,
  vocabulary, sentence length, hesitations, regional markers, signature phrases, things they would never say, and
  the distance between what they think and what they say. Without it, characters drift into one voice over a long
  text (opinion, vendor blog, https://www.bookwriter.vip/blog/voice-ledger). A project's own voice doc overrides
  this.
- **A strongly voiced narrator can carry a whole text:** Spaceplan's snarky onboard computer does all the talking
  (opinion, reviews, https://store.steampowered.com/app/616110).

## What is specific to games

**The player can arrive in any order.**

- **Gate a line on what the conversation has established, never on what the player happened to do first.** A
  follow-up ("Where were you that night?") is tagged to follow only the line that sets it up (practitioner, Emily
  Short, https://emshort.blog/how-to-play/writing-if/my-articles/conversation/).
- **An important question never becomes unaskable.** Mark used lines so they don't repeat, but keep answers the
  player may need re-askable; "it takes some work... to make sure that really important questions never become
  entirely impossible to ask" (practitioner, Short).
- **Decide what happens to a used line:** remove it, leave it, give it an alternate repeat line, or offer a summary.
  Information-heavy games favour recall, relationship games favour non-repetition. Give NPCs initiative so they
  change subject when a topic is spent, rather than waiting with implausible patience (practitioner,
  https://www.gamedeveloper.com/game-platforms/analysis-conversation-design-in-games).
- **Loops and trapdoors.** Loop while the conversation circles at one intensity, leave when stakes rise, and give a
  trapdoor that skips ahead; sending the player back to a loop's start can show an NPC's power (practitioner, Jon
  Ingold via Robert Yang's notes,
  https://www.blog.radiator.debacle.us/2018/11/notes-on-sparking-dialogue-great.html).

**Choices put words in the player's mouth.**

- **Rarely, and never narrate the player's feelings** in option or result text; write lines that fit many player
  histories ("Whatever happened between us in the past, business is business") (developer, Failbetter,
  http://www.failbettergames.com/narrative-snippets-agency-and-choices/).
- **Three options that differ in attitude to the conflict:** accept, reject, deflect. Two read as a false binary,
  four lose focus, and context-free filler ("What do you think?") does no dramatic work (practitioner, Ingold via
  Yang, above). Menus of three to six at most (practitioner, Short).
- **If the spoken line would be the same whichever option is picked, the option is a lie; cut it** (opinion, Tom
  Francis on Mass Effect, https://www.pentadact.com/?p=423). Fix the subtext as the structure and let the surface
  wording vary (practitioner, Ingold,
  https://kotaku.com/developer-shows-how-to-write-good-game-dialogue-using-b-1830797912).
- **Voiced lines get paraphrased options, text lines get the line itself.** Mass Effect paraphrased because reading
  the line and then hearing it felt doubled, at the cost of options that mislead about what is said (developer,
  snippet, Karpyshyn). In a text-only game, an attitude tag (Friendly, Playful, Distanced, Intimidating,
  Vulnerable) is a mask the player wears and can rewrite the option itself (developer, Roadwarden devlog,
  https://assemble-entertainment.itch.io/roadwarden/devlog/88099/writing-dialogues-for-the-clean-spear-tavern-roadwarden-devlog).
  Tone-only labels ("[Warmly]") can feel like a wall; let the line carry the tone (opinion, small forum sample,
  https://forum.choiceofgames.com/t/dialogue-choices/342).
- **Silence can be a choice.** Oxenfree and Firewatch let the player wait or interrupt, and the script tracks what
  was said (developer, snippets, unverified at source).

**Text-only tone.** With no actor, punctuation, rhythm and word choice carry all the tone, and long speeches wear;
community norms run to three to five short lines per NPC turn with a way to interrupt (opinion, snippet, not
measured).

**Barks and repetition.**

- **One bark, one piece of information,** clear and unobtrusive ("We're flanking", "Grenade"); cleverness makes it
  less useful, and combining facts multiplies the variants to write (developer, Dansky and Anderson,
  https://kotaku.com/why-video-game-characters-say-such-ridiculous-things-5921878).
- **Write for the Nth hearing.** Frequency makes a line memorable beyond intent, a small pool cycles fast, and the
  distinctive line grates first. Budget pool depth early and play-test each bark in its trigger context: a guard
  saying "Guess I'm just imagining things" right after the player broke a light (developer, same article).
- **Gate barks by a cooldown per category** (urgent short, ambient long, scaled to line length) and remember each
  speaker's last few lines; fire only when the trigger adds information (opinion, one site's figures,
  https://pulsegeek.com/articles/dialogue-barks-timing-and-cooldown-best-practices/). No studio figure for how many
  variants a bark needs was found.
- **Author reactive lines as rules keyed to world state; the most specific matching rule wins,** with general
  fallbacks, and writers add lines without a programmer (practitioner, Elan Ruskin's Left 4 Dead system via Emily
  Short, https://emshort.blog/2012/03/16/gdc-2012-talk-on-dynamic-dialogue/).
- **Procedural scenes are hand-written scripts with slots** for party, personality and history, plus alternate
  scripts per outcome (opinion, on Wildermyth,
  https://www.superjumpmagazine.com/wordplayer-wildermyth-lays-bare-the-false-promises-of-ai-storytelling/).
  Repeats in model-generated lines are handled in `generated-lines.md`.
