# Fun, "dopamine" and player motivation models

What can honestly be said about what makes a game fun, what "dopamine" does and doesn't mean, and what player
typologies, MDA, flow and core loops are good for. Sources: `evidence/fun.jsonl`. The short version: the frameworks are
vocabularies, not predictions; the strongest measured link to playtime is curiosity under uncertainty (one study); the
pop neuroscience is mostly wrong. Why players come back over days is `motivation.md`; how an action feels in the hand
is `feel-and-look.md` and `feedback.md`.

## Fun taxonomies name targets; none predicts what will be fun

- MDA: the designer builds Mechanics, which produce Dynamics in play, which produce Aesthetics the player feels; the
  player meets them in the opposite order. Its eight aesthetics (Sensation, Fantasy, Narrative, Challenge, Fellowship,
  Discovery, Expression, Submission) are "not limited to" those eight, and the authors say there is "no Grand Unified
  Theory" (developer, Hunicke, LeBlanc & Zubek 2004). No empirical validation was found. Walk argues it cannot hold
  narrative, interface or art without "stretching MDA to the breaking point" (practitioner, argument only).
- Lazzaro's Four Keys (hard fun, easy fun, serious fun, people fun) came from a qualitative commercial study of 30
  players that disclaims statistical results; "best sellers hit three of four keys" rests on a few named titles
  (practitioner, Lazzaro 2004, full read). Use the keys as prompts, never as a finding.
- Malone's challenge, fantasy and curiosity frame is a theory written after three small studies: a survey of 65
  children rating 25 games (feature correlations: goal r=.65, score .56, audio .51, randomness .48; fantasy .06 and
  variable difficulty .17, not significant), a Breakout feature-removal test (n=10 adults: removing the bricks cost
  most, beta .77, then score .32 and bounce .30) and a Darts test (n=80 fifth graders, 10 per version: extrinsic
  fantasy raised liking, and girls spent more time on the extrinsic than the intrinsic fantasy) (research, Malone 1981,
  full). Curiosity was not tested; Malone calls the survey correlational and the samples small.
- Koster's "fun is learning patterns" (boredom when nothing is left to learn or the pattern is out of reach) is a
  coherent lens; no data was found behind it (snippet, Koster via Shortform summaries).
- A review of 87 quantitative studies: enjoyment can occur independently of challenge, and ties to need and value
  satisfaction (research, Mekler et al. CHI 2014, abstract).

Rule: name the kind of fun the design is for before tuning, and check it offers more than one. Trace a complaint down
MDA's layers ("dull" → no pressure in play → which rule removes pressure). The dynamics and aesthetics can't be read off
the rules, which is why the playtest exists (inference from MDA).

## Curiosity under uncertainty has the strongest single measured link to playtime

- In 1,699 participants, curiosity was the strongest predictor of enjoyment and the only predictor of free-choice
  playtime; uncertain success raised it (research, Kao et al. CHI 2024; one action RPG).
- In monkeys a sustained dopamine ramp tracked outcome uncertainty, peaking at 50% reward probability (research,
  Fiorillo, Tobler & Schultz 2003; animal data, so the design link is inference).
- Gaps pull when they are salient; importance amplifies (`motivation.md`, Golman & Loewenstein).

Rule: spend design effort on open questions, uncertain outcomes and things to find out. Keep what is uncertain about the
outcome, not about the rules (`randomness.md`).

## Drop "dopamine hit": dopamine signals surprise and wanting, not pleasure

- Primate dopamine neurons' output "apparently signals changes or errors in the predictions of future salient and
  rewarding events" (research, Schultz, Dayan & Montague 1997, abstract; monkey recordings). Read as reward prediction
  error, a fully predicted reward should drive little response (inference).
- "Wanting" is not "liking": rats with up to 99% dopamine depletion still showed normal liking reactions (research,
  Berridge & Robinson 1998, abstract). NIDA's director: dopamine is "not the pleasure molecule in the simple, direct way
  it is typically portrayed in the media" (verbatim, Volkow in Scientific American). Experts treat prediction-error and
  incentive-salience accounts as partial truths, not rivals settled.
- The study usually cited for "games release dopamine", Koepp et al. 1998, scanned 8 men against a blank-screen
  baseline while the game paid £7 per level, confounding game, money and motor task; mean ventral striatal binding
  change −13% (range +8 to −42) (research, full read). The group's own later reanalysis says head movement "may have
  biased" the result: with frame-by-frame motion correction, changes in individual striatal regions were much smaller
  and nonsignificant, and the correlation with performance disappeared; right ventral striatum (about −7%) stayed
  significant with anatomical regions of interest, and the overall effect of condition stayed significant after motion
  correction (research, Egerton et al. 2009, partial). No direct replication was found in the portion read.
- Kühn 2011 is cross-sectional structure data (154 14-year-olds, higher striatal grey matter in frequent gamers); Kühn
  2014 is a 2-month training study against a control group that found grey-matter gains in hippocampus, prefrontal
  cortex and cerebellum, not striatum. Neither measures dopamine release (research, Kühn et al. 2011, 2014, abstracts).
- No study was found that measures dopamine in players across a specific design pattern (loop, streak, loot box) (null,
  search level).

What people usually mean by "dopamine" in game talk (idle-game videos, say) is a rare, unpredictable, outsized payoff
tied to a real event: a screen-clearing chain, a coin burst. The research above supports the surprise part only:
better-than-expected outcomes drive prediction error, and the ramp peaked at maximal uncertainty. It does not support
more juice: success-dependent feedback raised curiosity and competence, amplified feedback lowered competence (Kao
2024), and the most-juiced condition scored lowest (Kao 2020, `feedback.md`). The payoff works because ordinary events
stay small, which is `feedback.md`'s ladder rule: rungs by what happened, a fixed size per rung, never escalate one
event class (inference).

Rules: a reward the player saw coming adds little; a better-than-expected outcome adds more (inference from Schultz).
A loop that brings players back does not show they enjoy it, since wanting is not liking: measure return and reported
enjoyment separately. In docs and copy say "surprise", "mastery" or "wanting", never "dopamine hit".

## Matching challenge to skill is not a settled engagement fix

- Preregistered, n=309: balance was manipulated successfully and had no effect on play behaviour and no inverted-U with
  positive experience; the authors point to appraisals, novelty and progress (research, Deterding & Cutting 2023; one
  game, five matches).
- Flow is useful vocabulary for too hard / too easy; Csikszentmihalyi's views on games reach us only secondhand, so
  don't quote him (research, Salisbury & Tomlinson 2016, partial).

Rule: don't treat a difficulty-matching curve as the fun fix; watch whether players feel progress and novelty.
Difficulty itself is `difficulty.md`.

## Player typologies: vocabulary for a review, never a segmentation

- Bartle on his own model: it "only applies to people who play virtual worlds for fun", is not a checklist of audiences,
  and an individual cannot be reliably typed; use a taxonomy such as Yee's for audiences (verbatim, Bartle 2009). The
  1996 types came from a debate among players on one MUD, with no stated method (practitioner, Bartle 1996).
- Yee's survey of about 30,000 MMORPG players found continuous factors everyone has some of (Achievement,
  Relationship, Immersion, Escapism, Manipulation). Gender effects were r=.20 for Achievement and .15 for Relationship
  and Manipulation; age was unrelated to hours (r=−.04) (research, Yee 2006, Presence).
- Personalising mechanics to BrainHex type failed: scores "do not significantly predict player experience of according
  game mechanics" (research, Busch et al., n=51). Hexad's scale structure has support (research, Tondello et al. 2019,
  abstract); its links to preferred elements are only partly supported (research, Tondello & Nacke 2020, partial); and
  one study could not predict type from behaviour reliably (snippet, Altmeyer et al. 2020, n=147).
- Quantic Foundry's 12-motivation model is a company model; secondhand reports say its structure replicates across
  regions, and effect sizes were not obtained (snippet).

Rule: use typologies to ask "does this design serve only one motive?" Don't segment, personalise or justify a feature
with "achievers will like it". Where elements are optional, let players choose rather than assigning by type (research,
Tondello & Nacke 2020, two samples, one image-tagging task, mixed results).

## Self-determination theory is the checklist; measure carefully

- Of 110 games-HCI papers using SDT, 82.73% used it mainly descriptively (research, Tyack & Mekler CHI 2020). PENS
  items are proprietary, several versions circulate, and its confirmatory analysis was never published; the PXI is more
  consistently sound (research, Tyack & Mekler 2024, partial).
- The Game Experience Questionnaire's 7-factor structure was not supported in a validation study (snippet, Law,
  Brühlmann & Mekler 2018; check before quoting).

Rule: ask what the design offers for autonomy, competence and relatedness (`motivation.md` has the outcome evidence).
If you measure, use a validated instrument and don't treat GEQ subscales as constructs.

## Core loops: description, not science

"Core loop" is a practitioner term for the repeated chain at the centre of play: anticipation, action, reward
(practitioner, Kim, GameAnalytics). "Compulsion loop" is folklore with a real behavioural root: its definition cites
Skinner's animal work, and no retention data was found. Variable rewards were preferred to fixed ones in one lab game,
except when the variable range was stretched: a measure of choice, not return (research, Kao 2012 thesis, partial).
Hopson, a Bungie user researcher who applied reinforcement schedules to game design, called a
contingency ethical "if the designer believes the player will have more fun by fulfilling the contingency" (developer,
Hopson 2012). That is the test: a loop earns its place by
being fun, not by bringing people back.

## What the evidence cannot say

Koster's and LeBlanc's own texts, Csikszentmihalyi's original data and Fong et al.'s challenge-skill meta-analysis
were not read. No study shows a typology-informed design beating a generic one on retention or
enjoyment. No controlled test of compulsion loops against retention. Nothing here was measured in gamified apps.
