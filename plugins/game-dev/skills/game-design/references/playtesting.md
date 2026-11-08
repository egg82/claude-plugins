# Playtesting and reading players

How to run a test that can show the design is wrong, and how to read what it shows. Sources:
`evidence/playtesting.jsonl`. Primary method sources are thin and partly paywalled (Hodent's book, the Microsoft
Games User Research chapters); much circulating advice is unsourced practitioner advice repeating itself.

## Watch what they do; treat what they say as a lead

- Valve lists direct observation as the core method: "importance of what people do, not what they say", with the
  minuses that observers bias results and behaviour needs interpretation. Q&A: "people don't know why they do what
  they do". Think-aloud is good for "why" but "interfere with gameplay" and is "inaccurate and biased" (developer,
  Ambinder, GDC 2009 slides).
- Think-aloud is "an unnatural task" whose load "may lead people to the right answer"; it works best in co-op games
  where players explain to each other; the moderator stays neutral but not silent (practitioner, Bromley,
  gamesuserresearch.com). RITE sessions did use think-aloud (Medlock et al.).
- Don't explain mid-session: an explanation hands the tester information the shipped game won't. Log hesitations and
  stuck points (practitioner, snippet).
- Take the problem a tester reports and discard their proposed fix: they reason from a flawed model of the design
  ("problems yes, solutions no"; practitioner folk rule, earliest found a 2016 designer blog, no named author).
- Valve first blamed outside testers and by the third or fourth round accepted "it's our fault" (developer, Faliszek).
- Valve added physiological measures because of "lots of biases in current playtesting procedures", paired with
  surveys, not replacing them (developer, Ambinder, GDC 2011).
- Testers act bolder or more careful when watched (practitioner, Bugnet). Keep the observer small (Bromley allows one
  or two); recording and watching later is inference.

## Few testers, many rounds, a fix between each

**"Five users" is a rule about iterating, not about sufficiency, and is weaker than its reputation.**
- Nielsen's model: problems found = N(1-(1-L)^n), L about 31%, with stated conditions: the five are followed by a fix
  and a fresh five, users are comparable, and each distinct user group gets 3-4 (research, nngroup.com).
- Testing four production websites with 49 users (an abstract; a secondary page says 18), Spool & Schroeder found
  "considerably more than five" were needed to
  reach 85% of problems (research, CHI 2001 abstract, snippet; the oft-quoted "35% after five" is unverified: a
  newsletter attributes it to them and a student deck repeats it, but the abstract does not state it, so don't repeat
  it). Testers 6-18 each still found 5+ new ones (Perfetti & Landesman, snippet).
  Virzi's abstract reports about 80% of problems found with four or five subjects, the most severe ones first
  (research, Virzi 1992, snippet); random sets of five found anywhere from 55% to 99% (research, Faulkner 2003,
  snippet). Websites and software, not games.
- RITE: fix as soon as one tester exposes a problem with a clear cause, then keep testing. An RTS tutorial test with
  16 testers new to the genre: changes after testers 1, 2, 5, 8, 9, 10, then 6 more with no regression; 31 problems
  found, 30 fixed; 6 of 36 fixes had to be redone. Unclear causes get more testers before any fix. Preconditions:
  must-pass tasks agreed beforehand, fixes within hours, decision makers present (research, Medlock et al., UPA 2002).
- A stopping rule is the part teams drop. After 1 change-free tester you have only ruled out problems that hit 80%+
  of users; after 6, those hitting just under a quarter; after 10, those hitting about 15% (practitioner,
  measuringu.com citing the RITE authors).

Verdict for a small team: few testers, many rounds, a fix between each, and "nobody stumbled on the last N" as the
stop. One tester's slip is not a finding until a second repeats it or you can see the cause.

## Usability and fun are different studies

"Could they do it, where did they stall" needs a handful watched closely; "did they like it" needs enough players to
count, through surveys and diaries. One session aiming at both gets muddled (practitioner, PlaytestCloud). Games
intend
challenge, so speed is not a pass criterion: a stall the player enjoys is not a defect (opinion).

## Match the test's session shape to the play's

Idle Miner Tycoon was tested with 7 remote players over three 15-minute sessions two hours apart. It exposed a stall a
single sitting would not: players poured upgrades into one part and ignored the part that moved resources. Contextual
tutorials at that point raised the share reaching the milestone (developer, Kolibri, vendor case study, no figures).
For idle games, one long session
tests the opening and cannot test the return; the same holds for any app used in short visits across days
(inference).

## Telemetry says where; a watched session says why

- Funnels and time-to-first-churn locate exits; pair them with watched sessions (inference, no source row).
- Across 275 games, D1 retention was 31% when the first session beat the 9-minute mean against 20% below, and the
  author concedes short sessions may be a result of churn, not its cause (research, weak; deltaDNA). Don't set a
  session-length target from it.
- Mobile retention benchmarks are vendor-reported and conflict (unverified; no source row); no idle-specific drop-off
  source was found. With a handful of players there are no usable funnel statistics: read the log as one person's
  story (what they tapped, in what order, when they came back).

## Numbers for modelling a human-paced player

**A simulated player needs human timings, and every threshold built from them is a design choice unless a row says
otherwise.** No source gives "N minutes without a meaningful event, X% leave"; a drift threshold is anchored to the
rows below and carries that label (null, supported by absence). The session and retention benchmarks are mobile or
store-wide figures, so use them for when a human might show up, never as targets (inference).
- Reading speed: silent reading of English non-fiction averages 238 wpm (175-300 for most adults), fiction 260
  (200-320); 190 studies, 18,573 adults (research, Brysbaert 2019, read in full). Going from about 250 to 500-750 wpm
  without losing comprehension is unlikely (research, Rayner et al. 2016, abstract only).
- Text read while watching a picture is slower: BBC subtitle guidance 160-180 wpm, minimum about 0.3 s per word
  (guideline, via a Clevercast copy; BBC original not reached). Netflix English timed text allows up to 20 characters
  a second for adults, 17 for children (guideline, read not stated, so unverified).
- Action time, keystroke-level model: mental preparation 1.35 s, point 1.1 s, button press 0.1 s, home 0.4 s; desktop
  only (research, Card, Moran & Newell 1980, secondary via Wikipedia). Measured on 26 real users of an enterprise
  travel-and-expense web app (two versions), including system response: a link or button 3.73 s, a pull-down 3.04 s,
  scrolling 3.96 s; varies per system (research, Sauro 2009, read in full). Simple reaction time, about 190 ms visual,
  is a floor, not the time to make a game choice (research, secondary via Wikipedia). No source found for choosing 1
  of N or for a touch equivalent.
- Attention during a wait: continuous attention to a phone broke into 4-8 s bursts in the mobile situations (8-16 s
  in lab and cafe), with up to 8 glances away in one page load; a switch-back time of 4.8-7.6 s was not found in the
  text (unverified); 28 adults, phone in transit, so desktop players will hold longer (research, Oulasvirta et al.
  CHI 2005, read in full). Nielsen's "10 seconds is about the limit for keeping the user's
  attention" is unverified: the existing Nielsen row covers only the 0.1 s limit.
- Benchmarks: mobile D1 median about 22%, D7 just under 4%, session median 3.1-3.5 min; PC D1 median about 7%,
  session median about 18 min, 1.65-1.70 sessions a day; no genre split (practitioner, GameAnalytics 2026 report,
  read not stated, so unverified).
- Churn prediction from telemetry is modest. Day-0 session features were the strongest predictors in one game, ROC-AUC
  0.7565 (research, Oulu thesis, abstract only). Single-session data had minimal predictive power for retention, one
  day better, one week better again (research, snippet via search summary). A tutorial churn spike at step 6 is a
  vendor's illustrative demo dataset, not a rate (practitioner, devtodev, read not stated).
- A strong policy is a poor stand-in for human choices: a network trained on human Candy Crush moves predicted the
  human move about 47-48% of the time, and agents trained on human data were almost 50% better in validation accuracy
  than agents trained on MCTS play (research, Gudmundsson et al. 2018, read in full; King data, so the lesson
  transfers, the numbers do not).
- Per-level churn against difficulty: Spearman r = -0.144 overall, -0.586 counting only players who churn without
  completing; AI pass rates alone mispredicted churn. A population model with per-player skill, persistence and
  boredom fitted to 95,266 players' real data improved the prediction (research, Roohi et al. CHI PLAY 2020, read in
  full). The method transfers, the fitted values do not.

Rule (inference): keep a human-paced player model separate from any optimal-play route player. With no play data,
keep churn flags binary and labelled rather than emit a probability, and make a simulated flag carry the strength of
its anchor ("anchored to a 4-8 s attention burst", not "predicts churn"), since a judgement printed as a threshold
reads as a measurement.

## The developer cannot judge clarity, and a genre-literate developer least of all

- "Curse of knowledge": "You know your design, so it's really hard to have objective knowledge of it"; remedy, watch
  the target audience (developer, Hodent, talk report, secondhand).
- The RITE tutorial test recruited only players new to the genre, because they were the audience (research, Medlock).
- Test genre newcomers alongside fans: a genre-literate tester supplies motive and vocabulary the newcomer lacks and
  so hides exactly the gaps the first minutes must close (inference from Medlock's newcomer-only recruitment).

Verdict: the developer's own play is a smoke test (does it run, is the pacing plausible), never a clarity test.

## Surveys: short, piloted, about what the session could not show

Shorter is better: a longer announced length lowered the share who started a web survey, and answers got faster
toward the end (research, Galesic & Bosnjak 2009, snippet). The common "completion falls after about five
minutes" has no primary source found (practitioner). One idea per question; include a "never" option; pilot it; end
with a broad
open question, since players use different words from the team (practitioner, Games User Research tips). After a
watched session, a recognition check ("which of these lines did you see?") with invented lines mixed in measures what
was seen without asking anyone to remember or flatter (opinion; standard signal-detection practice, no source).

## Remote and recorded sessions lose the quiet signals

Unmoderated sessions scale and remove the observer effect, but lose the in-the-moment question, posture, off-screen
hesitation and the glance away; asking afterwards is a poorer substitute for seeing play (inference; the
"vastly inferior" wording has no source row).

## What the evidence cannot say

Not found: Hodent's own text, the Pagulayan et al. chapter, Spool & Schroeder's and Virzi's full texts, any Valve
source for "never
help the tester", any study comparing RITE with ordinary rapid testing, and any solo or small-team multi-session
playtest account for an idle game.
