# Playtesting and reading players

How to run a test that can show the design is wrong, and how to read what it shows. Sources:
`evidence/playtesting.jsonl`. Primary method sources are thin and partly paywalled (Hodent's book, the Microsoft
Games User Research chapters); much circulating advice is unsourced practitioner advice repeating itself.

## Watch what they do; treat what they say as a lead

- Valve lists direct observation as the core method: "importance of what people do, not what they say", with the
  minuses that observers bias results and behaviour needs interpretation. Q&A: "people don't know why they do what
  they do". Think-aloud is good for "why" but "interferes with gameplay" and is "inaccurate and biased" (developer,
  Ambinder, GDC 2009 slides).
- Think-aloud is "an unnatural task" whose load "may lead people to the right answer"; it works best in co-op games
  where players explain to each other; the moderator stays neutral but not silent (practitioner, Bromley,
  gamesuserresearch.com). RITE sessions did use think-aloud (Medlock et al.).
- Don't explain mid-session: an explanation hands the tester information the shipped game won't. Log hesitations and
  stuck points (practitioner, snippet).
- Take the problem a tester reports and discard their proposed fix: they reason from a flawed model of the design
  ("problems yes, solutions no"; practitioner, no primary source found).
- Valve first blamed outside testers and by the third or fourth round accepted "it's our fault" (developer, Faliszek).
- Valve added physiological measures because of "lots of biases in current playtesting procedures", paired with
  surveys, not replacing them (developer, Ambinder, GDC 2011).
- Testers act bolder or more careful when watched; keep the observer small, or record and watch later (opinion).

## Few testers, many rounds, a fix between each

**"Five users" is a rule about iterating, not about sufficiency, and is weaker than its reputation.**
- Nielsen's model: problems found = N(1-(1-L)^n), L about 31%, with stated conditions: the five are followed by a fix
  and a fresh five, users are comparable, and each distinct user group gets 3-4 (research, nngroup.com).
- On websites the first five found about 35% of a larger set's problems (Spool & Schroeder, secondhand; unverified);
  testers 6-18 each still found 5+ new ones (Perfetti & Landesman); Virzi's five-person spread was 55% to nearly 100%
  (research, snippet; websites, not games).
- RITE: fix as soon as one tester exposes a problem with a clear cause, then keep testing. An RTS tutorial test with 16
  testers new to the genre: changes after testers 1, 2, 5, 8, 9, 10, then 6 more with no regression; 31 problems
  found, 30 fixed; 6 of 36 fixes had to be redone. Unclear causes get more testers before any fix. Preconditions:
  must-pass tasks agreed beforehand, fixes within hours, decision makers present (research, Medlock et al., UPA 2002).
- A stopping rule is the part teams drop. After 1 change-free tester you have only ruled out problems that hit 80%+
  of users; after 6, about a quarter; after 10, about 15% (practitioner, measuringu.com citing the RITE authors).

Verdict for a small team: few testers, many rounds, a fix between each, and "nobody stumbled on the last N" as the
stop. One tester's slip is not a finding until a second repeats it or you can see the cause.

## Usability and fun are different studies

"Could they do it, where did they stall" needs a handful watched closely; "did they like it" needs enough players to
count, through surveys and diaries. One session aiming at both gets muddled (practitioner, PlaytestCloud). Games intend
challenge, so speed is not a pass criterion: a stall the player enjoys is not a defect (opinion).

## Match the test's session shape to the play's

Idle Miner Tycoon was tested with 7 remote players over three 15-minute sessions two hours apart. It exposed a stall a
single sitting would not: players poured upgrades into one part and ignored the part that moved resources. Teaching
at that moment fixed it (developer, Kolibri, vendor case study, no effect sizes). For idle games, one long session
tests the opening and cannot test the return; the same holds for any app used in short visits across days
(inference).

## Telemetry says where; a watched session says why

- Funnels and time-to-first-churn locate exits; pair them with watched sessions (practitioner, snippet).
- Across 275 games, D1 retention was 31% when the first session beat the 9-minute mean against 20% below, and the
  author concedes short sessions may be a result of churn, not its cause (research, weak; deltaDNA). Don't set a
  session-length target from it.
- Mobile retention benchmarks are vendor-reported and conflict (D1 21-27%); no idle-specific drop-off source was
  found. With a handful of players there are no usable funnel statistics: read the log as one person's story (what
  they tapped, in what order, when they came back).

## The developer cannot judge clarity, and a genre-literate developer least of all

- "Curse of knowledge": "You know your design, so it's really hard to have objective knowledge of it"; remedy, watch
  the target audience (developer, Hodent, talk report, secondhand).
- The RITE tutorial test recruited only players new to the genre, because they were the audience (research, Medlock).
- Test genre newcomers alongside fans: a genre-literate tester supplies motive and vocabulary the newcomer lacks and
  so hides exactly the gaps the first minutes must close (practitioner).

Verdict: the developer's own play is a smoke test (does it run, is the pacing plausible), never a clarity test.

## Surveys: short, piloted, about what the session could not show

Completion falls after about five minutes; one idea per question; include a "never" option; pilot it; end with a broad
open question, since players use different words from the team (practitioner, Games User Research tips). After a
watched session, a recognition check ("which of these lines did you see?") with invented lines mixed in measures what
was seen without asking anyone to remember or flatter (opinion; standard signal-detection practice, no source).

## Remote and recorded sessions lose the quiet signals

Unmoderated sessions scale and remove the observer effect, but lose the in-the-moment question, posture, off-screen
hesitation and the glance away; asking afterwards is "vastly inferior" to seeing play (practitioner, thin evidence;
snippet).

## What the evidence cannot say

Not found: Hodent's own text, the Pagulayan et al. chapter, Spool & Schroeder's full text, any Valve source for "never
help the tester", any study comparing RITE with ordinary rapid testing, and any solo or small-team multi-session
playtest account for an idle game.
