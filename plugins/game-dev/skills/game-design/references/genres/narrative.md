# Story-driven games

What is particular to games where the story is a main reason to play: delivering it, pacing it against play, choices,
mysteries that progress by learning, and surprise. The genre-neutral layers are in `../progress.md` (where progress
is, marking what moves the story), `../onboarding.md` (teaching through the game's own voice) and SKILL.md's genre-fit
rule (mechanics that agree with the story). Sources: `../../evidence/genres/narrative.jsonl`. The research is thin and
mostly on text or film; developer accounts are mostly second-hand write-ups or talk captions, Pope's devlog and Smith
and Worch's slides were unreadable, and the Edith Finch talk's captions were only searched by keyword.

## Story keeps players going, and playing pulls them in more than watching

- Playing the opening of Hellblade raised narrative engagement over watching a recording of it (research, Ferchaud et
  al. 2020, n=198, 45 minutes; used Busselle and Bilandzic's engagement scale, which was built on film and TV
  viewers).
- Players will do things they "don't really care about in order to experience the story" (research, Børgesen 2021,
  student thesis, convenience sample).
- WoW players have clear reasons to watch or skip each of 11 kinds of non-interactive story; the author recommends a
  way to replay arcs when a skip costs information the player needs to play (research, Wang 2021 thesis, abstract).
- No skip-rate telemetry for cutscenes was found (null).

## Story as the reward for play, so play is never wasted

- Hades: "It was an explicit goal of our early development, to take the pain out of dying and having to restart";
  story progress on every death means "the time you spent wasn't a waste of your time". Events are chosen from player
  state: "We have no idea, apart from a couple of moments, how things are going to be sequenced" (developer, Kasavin,
  Game Developer). Players "hit a difficulty wall" when "you just want to see how the story ends", so Supergiant
  builds in ways past it (developer, same). The design goal was that "every time you died the story would advance".
  Each character's events carry requirements plus "good old-fashioned randomness", generic repeatable lines at the
  bottom; barks play from a shuffle bag until "the whole table is depleted" so none repeat back to back. Most
  characters can be walked past, but the first boss "stands in your way" every run, so the story the player cannot
  skip rides on her (developer, Kasavin and Korb, GDC 2021, captions).
- Firewatch spaces its recurring conversation by time since the last one ("we wanted to space these out"), and the
  variant with the most met requirements wins; a fact the player never set still counts, so the other character
  "will assume things about you". When the player walks away from a scene, it gets louder and characters "yell at you
  as you flee" rather than letting the story stall. Required beats sit inside branching dialogue, and they made some
  conversations non-interruptible after one added choice could leave the radio dead for the rest of the game
  (developer, Campo Santo, GDC 2017, captions). A counter to "let the player interrupt anything".
- Pacing stalls when travel "lasts longer than whatever emotive content it's offering", or repeats with "no new
  content or meaning" (opinion, Emily Short on Heaven's Vault).
- A Dark Room "gives the player no more than what they need to move from one steppingstone in the story to the
  next"; a hut's follow-up arrives "a random amount of time later" (opinion, student critique). No player complaint
  about not knowing when the next story bit comes was found for A Dark Room, Kittens Game, Candy Box or Progress
  Knight (null, thin).

Rule (inference): tie story to play the player is already doing, so the beat lands as a result of the play, not after
a gap with no input; put the beats that can't be missed on what the player can't avoid. Where a beat waits on a clock
or a hidden value, `../progress.md` applies: show the wait.

## Environmental story: missable on purpose, so never load-bearing

- Harvey Smith contrasts "push" (a character tells you) with "pull" (you infer it from the scene), and concedes "It
  has to be possible to miss some things to make finding them meaningful" (developer, Arkane, via Nieman Storyboard;
  the GDC 2010 slides were unread).
- Miyazaki: "there are a huge number of things... we make no attempt to explain to the player, and many more that they
  simply have no way of finding out" (developer, Dark Souls Design Works, fan translation).
- Strife Hayes' gap list for Dark Souls (`../onboarding.md`): many finish it without knowing what kindling does.

Rule (inference): pulled story can be missed, which is its value; so nothing the player needs to progress lives only
there. Lore can hide; progress cannot (`../progress.md`).

## Choices: the difference must be foreseeable, and acknowledgement buys most of it

- A linear story that acknowledged each choice in text matched a branching one on most agency questions; branching
  still won on "the story would have been different" (research, Fendt et al. 2012, text adventure, online sample).
- With n=88, agency rose when the options differed in situational content the player could foresee, even though the
  outcomes didn't actually branch (research, Cardona-Rivera et al. AIIDE 2014).
- Choices felt meaningful when "consequential, social and moral" (27 players describing choices from 24 games). In
  an experiment (n=192, one short text story), a meaningful choice raised appreciation over no choice (d=0.30); a
  low-meaningful choice did not, and having a choice made no significant difference overall. Which ending the player
  got didn't change appreciation. "Consequential" meant a felt impact with clear stakes, not a changed outcome: "more
  important than the outcome of a choice is that the impact of what one has done is felt" (research, Iten et al. CHI
  2018, read in full). That choice alone left prosocial behaviour unchanged is from Iten's dissertation abstract.
- Telltale's "will remember that": Vanaman says some players disliked the notice, not most (snippet). No controlled
  study of it was found (null).

Rule (inference): make options visibly different in what happens next, give them stakes the player feels, and
acknowledge the choice when it is made. Real branching moved one agency question in one text study and didn't move
appreciation in another; it is the expensive part with the weakest evidence.

## Consequences: late, visible, and traceable to a choice the player understood

- "Delayed and 'really delayed' consequences make the biggest impression on players", and "design for the visibility of
  consequences; investing in something not telegraphed well is mostly not worth it" (developer, Sasko, CDPR, GDC 2023,
  via a summary; the talk itself is video only). The Witcher 3's Bloody Baron shows the warning in action: the visible
  dilemma (the botchling) has "minimal impact" on the Baron's fate, which reads an earlier, unmarked choice in another
  quest (opinion, community wiki read in full); one player only learned it branched from that wiki (snippet). No source gives a delay length past which the link is lost
  (null).
- "Choice is only interesting when it is both impactful and informed"; a consequence the player cannot understand "is
  no fun" (developer, Soren Johnson on Meier).
- Consequence is the expensive third of choice, and its cost grows fast with complexity; "twenty variant endings
  aren't ten times as good as two" (developer, Failbetter 2012). Telltale's Walking Dead postponed deaths so a choice
  shifted relationships instead of the plot (opinion, Kashyap 2017).
- Frostpunk's consequences are "a boiled frog": small steps that add up (developer, Stokalski). A meter breach gives a
  warning and a few days with a named goal to reverse it (snippet).

- The counter-case: a critic found Telltale's deaths came "regardless of your choices - it just comes down to when",
  and felt "a bit deceived" by the promise that the story "adapts to the choices you make" (opinion, Game Informer
  2015, one critic). Callbacks (a character repeating what you said) kept the world feeling responsive anyway
  (opinion, GamesBeat).

Rule (inference): delay is fine and even stronger, provided the payoff names what caused it (a line that refers back,
a number whose source is the choice). A hidden branch is wasted work.

## Dilemmas: "oh no, now what?" versus "that's not fair"

- Players who meet outcomes "they couldn't foresee may feel unfairly treated"; a choice whose result breaks
  expectation draws "the game is unfair"; keep the scenario as clear as possible (practitioner, Wanjek and Bopp 2024,
  sample not stated). Higher mechanical stakes push players to pick strategically rather than morally (same source).
- A dilemma fails when one option plays clearly worse: "make sure no choice leads to an inferior game"; its pull comes
  from a gameplay goal colliding with the player's picture of themselves (practitioner, Stokalski 2017).
- Pentiment makes the impossible choice the point: the murder cannot be solved for certain, so the player picks who
  dies, and choices play out across time jumps of years (developer, Sawyer). Sawyer finds protagonists who can save
  everyone uninteresting (developer, snippet).
- Regret tracks controllability and self-blame (research, Roese and Olson 1995, snippet; no game-context test). If
  the player feels they could have done otherwise it reads as fair; blame lands on the game when a cause was out of
  their sight (opinion, about difficulty).
- "There cannot be an optimal play-through. Every decision has to be fully justifiable by a human being" (developer,
  Pink, The Walking Dead). Both sides of a key scene were written so "the choice taken and the choice not taken [were]
  just as important" (developer, Bruner).
- Frostpunk's designers say a good way out always exists; child labour pays at once and costs Hope later (snippet).
  Reigns' four bars make balance "basically impossible", death is "unforgiving" but written funny, and the dynasty
  carries on (developer, Alliot), so a loss is a turn in the story, not a game over.
- Under scarcity, guilt comes from inside: "remorse can be raised only from inside"; a This War of Mine playtester
  who stole "judged herself morally", and the consequence fell on characters ("others may be happy because you have
  what you need") rather than on a score (developer, Miechowski).
- Crusader Kings 3 prices acting against a character's nature as stress shown at the choice (a Compassionate ruler
  gains 42 Stress executing a prisoner); past a threshold a Mental Break event lands later, its options shaped by
  traits. Stated aim: "make them think twice", not punish (developer, Dev Diary #31, read in full).
- Fallout: New Vegas: "mechanical clarity is more important than immersion" for reputation and karma; both options
  should "contain virtue and sacrifice" (developer, Sawyer, GDC 2012 abstract and blog).

Rule (inference): the bind should follow from the player's own earlier choice, which they knew was a commitment when
they made it; show what each option costs at the dilemma; keep every option defensible. Unforeseeable cause →
"unfair"; foreseeable cause that collides with something else they value → "damn".

## Promises: made visibly, priced to break, tested later

- Ironsworn makes a vow an object: written down with a rank (1 to 5). Forsaking it ("renounce your quest, betray your
  promise, or the goal is lost") is a legal move costing spirit equal to the rank and the item sworn on; a failed
  fulfil roll offers recommitting at a higher rank or forsaking (developer, SRD). Breaking is priced and dramatic, and
  no timer exists (developer, SRD).
- Frostpunk 2's promises buy council votes and carry deadlines; a missed one costs a faction's trust. Overcommitting
  snowballs ("more promises, which led to more promises"), schedule rules can make deadlines unmeetable, and one
  faction stayed angry after a kept promise's building was destroyed (opinion and snippets; no developer statement on
  why deadlines). Its values "are not the same for everyone", so promises clash between factions (developer,
  Stokalski).
- Mass Effect 2 builds to a finale where earlier loyalty and preparation decide who dies (snippet, Kindregan). A
  columnist: "remembering those you've lost carries more emotional weight than saving everyone" (opinion). The one
  case players call unfair is a role whose fit the game never signalled; loyal squadmates in the wrong role still died
  (snippet, forum threads).
- Persona retreated from neglect penalties: Persona 3 reversed or broke a bond for wrong answers or missed time,
  Persona 4 softened it, Persona 5 removed it so "players are freer to express themselves" (practitioner). Stardew
  decays friendship for neglect but stops at a floor that protects an earned bond (snippet, wiki).
- Darkest Dungeon shows the stress meter in full but not what an affliction will do; the loss of "complete control" is
  intended (developer).

Rule (inference): a promise is an object the player can see (named, ranked or counted), breaking it is a legal choice
with a stated price higher than declining, and it is tested by a later situation, not a clock. Signal the fit of any
role whose wrong choice costs a life; an unsignalled fit is the case players call unfair.

## Reacting to patterns, not meters

- Players preferred characters who react by their own values, immediately or later, over good/evil meters (research,
  Wright and Denisova 2024: 30 survey completers, 11 interviews). Mass Effect's meter is criticised for rewarding one
  pole; "something like 92%" of players were Paragon, a former BioWare designer recalls, and the one-path incentive
  is why Mass Effect 3 changed it (developer, Ebenger's tweet: a recollection, not telemetry).
- Storylet systems track qualities, numbers that rise and fall, as the world state; counting how much of a thing has
  happened, not only whether, is the cheap way to react to a habit (practitioner, Emily Short). Cost: bookkeeping, and
  large libraries overwhelm.

- The Walking Dead tracked relationships, not plot branches: "episode 1 and 2 combined make Kenny's mood in episode
  3"; paths reconverge while relationships stay diverged (developer, Pink). Disco Elysium: "people remember that you
  said or did certain actions", and "I hope we can signal it before this happens" (developer, Kurvitz).

Rule (inference): count tendencies per kind of choice and let characters read the count; avoid a single moral axis.
Relationships are the cheap carrier of a consequence: the plot can reconverge while who trusts you does not.

## Consequences in games played with long absences

- No study of absence penalties in idle or async games was found (null). Broken streaks demotivate and can lead to
  quitting (snippet: Silverman and Barasch 2023 JCR, via secondary pages). Free currency sent to players predicted to
  churn raised churn from 8.4% to 11.4% in one Wooga test (snippet).
- Idle developers show events that happened while away on return; one considered auto-closing unanswered events
  because they stalled play (snippet). Grimshire advertises permadeath, but only some characters can die; villagers
  never starve, and a reviewer found its deaths "hollow" (developer Steam page; opinion, review read in full). Its
  deaths are scripted, not systemic.
- Deaths a builder's players call unfair come without warning: in Banished a temporary shortage of labour spirals into
  starvation, "their absence makes it increasingly hard to recover", with no warning described (opinion, Play the
  Past); players report gatherers starving beside full barns and say the low-resource alert would have saved them, and
  reviewers faulted "a lack of feedback" (snippets). Its developer never planned survival ("it just sort of seemed
  like the obvious next step") and frames disasters as difficulty the player chooses (developer, Hodorowicz). Against the Storm puts
  a visible Impatience meter, raised by villagers leaving or dying, before failure (snippet). RimWorld "tries to hurt
  but not kill the colony", wants a death spiral to "play out over a long dramatic arc, or even be reversed", and eases
  off as the population drops (developer, Sylvester).
- Offline catch-up killing kittens in Kittens Game was filed as a bug by its players (snippet). Fallen London's
  opportunity cards wait in hand and an empty action candle loses nothing (opinion, guide). Cultist Simulator's
  always-running timers drew stress complaints and requests for auto-pause (developer post plus player snippets).

Rule (inference): in a game the player leaves for days, a commitment breaks through a choice the player makes when
present, never through a timer that expired while away; a dilemma waits for them.

## Progress by learning: the record shows where, the player finds how

- Outer Wilds' ship log maps discoveries by how they connect, with arrows to undiscovered entries, to show new players
  "what sort of a game Outer Wilds actually is" and that it is "a mystery they can try to solve" (developer, Mobius,
  2018 post). On the ground: "telegraph where paths lead", "We're trying to avoid explicit signs as much as possible",
  and "we give you enough information that you make conscious choices" (developer, Beachum, 2016). "The only possible
  reason you could have to explore was for the sake of curiosity" (developer, via Game Developer).
- Return of the Obra Dinn validates fates only in sets of three, so silence after three means something is wrong
  (opinion and snippet, The Register and Kotaku via Wikipedia). Critics read it as blocking guesswork; Pope's own
  reason is in his devlog, which was unreadable (null).
- Breath of the Wild places large landmarks as visual markers and small shapes to set the tempo, so "the objective
  order changes depending on how the player likes to play" (developer, Nintendo CEDEC 2017, translated notes).
- Her Story is the counterexample: progress depends on thinking of search terms, and a critic found it hard to tell
  whether they were progressing (snippet).
- What Remains of Edith Finch set "the constraint that there are no tutorials in the game because the game is about
  this sense of discovery": each vignette had a mechanic new to the player that had to be learnable by trying, to
  keep players in a "beginner's mind" (developer, Dallas, GDC 2018, captions searched by keyword, not read in full).
  A story-led reason to teach nothing, which only works when every mechanic is discoverable (`../onboarding.md`).

Rule: this is the stated-progress rule at its purest. The log or book says what is open and how far along it is;
the route stays the player's.

## Surprise and spoilers

- Spoiled ironic-twist and mystery stories were preferred to unspoiled ones (research, Leavitt and Christenfeld 2011,
  12 short stories, press release only). Replications disagree: a spoiler before the story lowered enjoyment, one
  mid-story did nothing (research, snippets: Levine et al.; Johnson and Rosenbaum 2015).
- No spoiler experiment on games was found (null). The text studies say nothing about a twist the player causes.

Rule (inference): don't lean on "spoilers don't matter"; the evidence is split and none of it is from games. Keep
reveals out of goal text (`../progress.md`: a gate names its condition, not its find).

## Mechanics that agree with the story

Beyond Hocking's 2007 essay (SKILL.md), Toh models dissonance, resonance and irrelevance from interviews with a few
expert players (opinion, book review; sample not given). No large-sample measure of ludonarrative dissonance exists
in what was found.

## What the evidence cannot say

No study of story pacing in games, beats per hour, or what a stalled story costs. No developer source on marking the
critical path among many quests (`../progress.md`). Not read: Pope's devlog, the Edith Finch GDC talk in full, Disco Elysium's or Kentucky Route Zero's makers on signposting, Townsend or Lantz in their own words.
