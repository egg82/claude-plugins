# Difficulty, challenge and failure

How hard a game should be, whether to adapt it, what failure should cost, and how to offer assists. Sources:
`evidence/difficulty.jsonl`. Most evidence is small purpose-built games, short sessions and self-report; nothing here
was tested in a gamified app. Whether challenge-skill matching is the fun lever at all is in `fun.md`.

## Adaptive difficulty: performance gains are real, enjoyment gains are not shown

- Hidden adaptation raised self-reported immersion in tiny purpose-built games (research, Denisova & Cairns CHI PLAY
  2015, n=42, a game of about 90 s; Denisova & Cairns 2019, n=120 and n=60).
- n=221, adaptive vs constant vs ever-increasing difficulty: the adaptive group performed better, with no difference in
  enjoyment or flow (research, Robb & Zhang 2022, abstract).
- Hamlet, an academic DDA system, reports no player evaluation; "boring when too easy, frustrating when
  too hard" is its authors' premise (research, Hunicke & Chapman, partial).
- Adapting to a 50% success rate made players more overconfident about their chances than random difficulty did,
  strongest in a motor game and absent where players saw part of the task before betting. Enjoyment was not measured;
  "overconfidence raises motivation" is the authors' stated assumption (research, Constant & Levieux CHI 2019, n=138).
- Telling players the game adapts raised reported immersion even when no adaptation existed, and the effect held at
  20 minutes (research, Denisova & Cairns 2019).

Rules: adapt quietly and cheaply if you adapt, expecting better performance, not proven enjoyment. Disclosing "the game
adjusts to you" raised immersion in two short studies, though one unreviewed thesis snippet found told players rating
the game harder (inference); never claim adaptation that isn't there. Since belief alone moves the self-report, read
any immersion gain from a DDA study that didn't control for expectation as unproven (inference).

## Aim a little above skill, and expect frustration to be the cost of hard

- Denisova & Cairns: the challenge-skill claim is "only backed up by theoretical literature ... without much empirical
  evidence" (research, 2015). A trivially easy Tetris (best pieces dealt) did not differ significantly from the
  balanced one on overall flow; one subscale favoured balanced (research, Lora Ariza et al., n=40, unfinished preprint).
- In internet chess, close games and stronger opponents were more enjoyable than blowouts and weaker ones (research,
  Abuhamdeh & Csikszentmihalyi 2012, snippet; curve shape unverified).
- Failing to master the controls or the difficulty raised frustration and, in a survey of 300 players, lowered enjoyment
  (research, Przybylski et al., via a university press release).

Rule: treat "challenge equals skill" as a heuristic. Close contests beat blowouts; the controls must never be the
difficulty (`feel-and-look.md`).

## Failure is the product; avoidable failure is the kind players value

- Juul's paradox of failure: we avoid failure, meet it in games, and seek games anyway; the pain accompanies and enables
  the pleasure (research, Juul "The Art of Failure", snippet; book not read).
- 244 players valued failure for learning, for the social experience and for the feeling, including frustration turning
  to pride; scripted or inevitable failure felt weaker than avoidable failure (research, Foch & Kirman, qualitative,
  self-selected).
- No controlled study of telegraphing, readability or "unfair deaths" was found. Into the Breach's stated reason for
  showing every attack, "it's very clear how or why you failed", is the nearest developer evidence (developer, see
  `legibility.md`).

Rule: make every failure traceable to something the player could see and do differently: visible, consistent rules,
no off-screen kills (inference from Foch & Kirman and Into the Breach).

## Arbitrary-feeling resume points scored worst

- N=72 in four groups on one platformer: checkpoints (placed by the designer) scored lowest; player-chosen savepoints
  beat them on autonomy, permadeath on autonomy and curiosity; permadeath, which gives no choice, scored as high as
  savepoints, against the authors' own hypothesis that it would feel least autonomous. The authors' untested theory is
  that checkpoint placement felt arbitrary (research, Cuerdo, Mahajan & Melcer, IEEE CoG 2021; about 18 per group;
  source read via a dissertation chapter, partial).
- No study isolating retry speed, load time or checkpoint spacing was found; Super Meat Boy's instant restart is a
  documented feature and no developer statement of why was found (snippet).

Inference: the progress lost matters less than whether the resume point felt like the player's, or at least not
arbitrary. Small sample; test before copying.

## Assists: granular, changeable at any time, never shamed

- Celeste's Assist Mode changes game speed, stamina, air dashes and invincibility separately; the makers changed the
  wording ("essential" became "intended") and removed the save-file icon marking assist use after an accessibility
  critic called the text othering; Maddy Thorson, the designer, said the icon "feels like the same exclusionary
  reasoning" (developer, Vice, partial).
- The Last of Us Part II: "accessibility is orthogonal to difficulty"; options are granular, changeable any time,
  nothing gated behind a difficulty (developer, Naughty Dog, secondary coverage, snippet).
- Hades' God Mode starts at 20% damage resistance and adds 2% per death, so the death-and-retry loop stays (inference); Kasavin:
  difficulty settings "may need to be proprietary to the game" (developer, relayed by Can I Play That, partial; the
  reported 80% cap is unverified).
- Game Accessibility Guidelines: a wide choice of difficulty levels and adjustable game speed are basic; changing
  difficulty during play and assist modes are intermediate (guideline).
- Whether assists cheapen other players' achievements: no study, only split forum opinion.

Rules: offer assists as separate switches, changeable mid-play, worded without judgement. Tie achievements to assist
use only on purpose, and say so in the option text.

## What the evidence cannot say

Whether DDA raises enjoyment or retention in shipped games over weeks. Effects of retry delay, checkpoint spacing or
punishment severity. Telegraphing as a cause of perceived fairness. Unread: Juul's book, Hunicke's "Case for DDA",
GameFlow's full text, primary Naughty Dog and Supergiant interviews.
