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
