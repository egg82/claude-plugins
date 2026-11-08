# Feedback and game feel (juice)

How much feedback an action should get, how fast, and when to stop. Control feel (latency budgets, forgiveness
windows, hit-stop), button states and visual readability are `feel-and-look.md`. Sources: `evidence/feedback.jsonl`.
The primary talks (Jonasson & Purho, Nijman's "Art of Screenshake", Swink's book) were not retrievable as text;
claims about them come from secondary summaries.

## More is not better: aim for the middle, tied to what happened

**Medium feedback beats extreme, and no feedback loses on a few measures; feedback that depends on success beats
feedback that is merely bigger. The shape holds but the effects are small.**
- One action RPG built at four bundled audio-visual juice levels (None, Medium, High, Extreme; n=3,018,
  between-subjects): Extreme scored below Medium and High on competence, autonomy, presence, enjoyment, play time and
  every performance count, while None scored below them only on competence, play time and keyboard/mouse actions;
  Medium and High never differed. The effects are small (partial eta-squared .003-.010) (research, Kao 2020, full).
  One genre, desktop, audio and visual never separated; the paper's abstract says None lowered intrinsic motivation
  too, its own results show Extreme only.
- Preregistered, 1,699 participants: success-dependent feedback raised curiosity, effectance and competence.
  Amplification (the same feedback made larger) lowered effectance and competence against standard feedback, which the
  authors tentatively put down to impeded agency. Curiosity was the only predictor of free-choice playtime; enjoyment
  did not predict playtime (research, Kao et al., CHI 2024).
- The effectance scale this literature uses has poor validity (unverified: recalled Ballou et al. CHI Play 2021, no
  source row), and Kao et al. 2024 describe the juice literature as "mixed results, high measurement and
  operationalisation variance, low statistical power, and exploratory effect searching". Trust the shape, not the
  effect sizes.
- A GDC counter-talk argued juice can cost immersion (snippet, Folmer Kelly).

Rule: give feedback a ladder with a ceiling. The rung depends on what happened (an ordinary result, a first-of-kind, a
rare find, a failure), each rung has a fixed size, and the same event class never escalates over time.

## The unit of feel is one input answered by several small cues

- Juice's original claim is responsiveness to input: tweening, squash and stretch, sound; "maximum output for minimum
  input", with crude graphics mattering less than interactivity. Demonstration, not measurement (developer, Jonasson &
  Purho, secondhand).
- Nijman's "Art of Screenshake" adds 30 small tweaks to one shooter, among them shaking the screen opposite to the
  player's gunfire and a 33% chance of enemies exploding harmlessly on death (developer, via a Game Developer recap;
  no transcript, the other tweaks unread).
- Swink defines game feel as "real-time control of virtual objects in a simulated space, with interactions emphasised
  by polish". It assumes a controlled object; applying it to screens with no avatar is extrapolation (snippet).
- Juice is "excessive amounts of feedback in relation to user input", mechanically superfluous, and juice-rich
  interaction makes it hard to learn which aspects matter mechanically (research, Pichlmair & Johansen survey).

Rule: several cheap simultaneous cues (motion, sound, a number), none load-bearing alone.

## Answer within about 100 ms

**"0.1 second is about the limit for having the user feel that the system is reacting instantaneously"**
(practitioner, Nielsen, citing Miller 1968 and Card et al. 1991, which were not read). Hit flashes of 50-100 ms and
button transitions of 80-120 ms are unmeasured rules of thumb (unverified, no source found).

Rule: acknowledge every input at once even when the result is not ready: a press state, a refusal, "queued". An input
that does nothing reads as a bug, so a refusal is feedback too.

## Reduced motion is a requirement with small, concrete asks

- WCAG 2.3.3 (AAA) accepts the `prefers-reduced-motion` query or a user setting as a way to stop interaction-triggered
  motion; web.dev advises the reduced version as default for non-essential motion (guideline, snippet).
- Game Accessibility Guidelines: avoid flicker and repetitive patterns; option to hide background movement; option to
  hide all non-interactive elements; avoid sudden unexpected movement; no essential information by sound alone;
  replicate significant sound as text or visuals (guideline).
- WCAG 2.3.1 (level A): nothing flashes "more than three times in any one second period", unless the flash is below
  the general and red flash thresholds (a flash is an opposing pair of luminance changes of 10% or more; area limit
  about a quarter of a 10° field; any opposing pair involving saturated red counts as a red flash). Full-screen
  high-contrast or red strobes are its target (guideline, W3C Understanding 2.3.1). Dreamlight Valley added separate
  toggles for screen shake and flashes (practitioner, snippet).

Rule: one switch, the OS preference honoured plus an in-game setting, that replaces each motion with a still
equivalent (a colour change, a held highlight). Remove the movement, never the information. Keep flashes to three a
second or fewer. Sound never carries information alone.

## Slow and background processes need a different kind of feedback

**For a process that runs without the player, the problem is legibility over time and a signal at the end.**
- An idle-game taxonomy covers rewards, interactivity, progress rate and UI, but its abstract claims nothing about
  feedback; the body was not read (research, Alharthi et al., CHI 2018).
- Cookie Clicker reads as feedback on every cookie, generator and upgrade early, then scarcer, accomplishment-flavoured
  rewards later, with costs and income shown plainly (opinion, one analyst). Its designer speaks of "getting something
  done" and "making a number go up" but not of feedback design (developer, Orteil in Vice).
- Pecorella frames each return as "a celebratory moment" and advises calculating offline progress the same as online
  (developer, GDC 2016 slides, idle.jsonl). That a missing summary on return is a main risk is unverified.

Rule (inference from the findings above, not measured): feedback pace tracks process pace. A slow bar needs visible
creep and a distinct completion; a return needs a summary of what happened; an effect fired per tick on a constantly
ticking process becomes noise.

## Real-time waits and the end of content

**A wait that fits the fiction reads as acceptable; an arbitrary cap reads as a block. A game also has to say where
its current content stops, out of fiction.**
- Relabelling the same numbers changed how players felt: WoW halved XP, renamed "normal" versus "bonus", and players
  "felt rewarded instead of punished". The page gives no wording for a blocked tap (practitioner,
  mobilefreetoplay.com, read in full).
- Fallen London shows its wait as a persistent counter (a candle) and states the rate in plain text, not as a popup.
  No out-of-actions message was found; players still ask for faster regeneration (practitioner, fan-wiki Beginner's
  Guide, read in full; the Steam thread is a snippet).
- Timers that sell skipping them reframe neutral time as scarcity: when time is the obstacle, skipping time
  becomes the product (opinion, Unwinnable, snippet, paraphrase; the fetch returned 403). A long timer was called
  "disrespectful of players time" in one Steam thread, with a reply citing Dragon Age: Inquisition's as acceptable:
  an anecdotal split (verbatim, Steam thread, snippet).
- The Longing runs a 400-day real-time countdown with the game closed and little direction on what to do meanwhile (the shade can be
  given a simple task, such as digging a tunnel, before the game is closed). One reviewer found the forced patience
  "enigmatically compelling" yet said it ran "out of content way, way too soon" (opinion, Game Critics, read in full). Aggregated opinion calls the pace tedious, with certain in-home actions
  speeding it up (opinion, Wikipedia aggregate, snippet; machine-summarised, weak).
- Idle Fantasy makes the wait the loop: start something, close the app, return up to an hour later to collect, "no
  stamina bar, no energy system, nothing that pressures you to stay in the app" (developer, repository README,
  snippet; row in genres/idle's evidence).

Rule (inference from the above, not measured): say plainly that this is a real-time wait and how long, state the rate
where it is a refill, and word the wait so it cannot be read as selling the skip. A blocked action should say why it
is blocked and what it waits for; no source shows what wording stops repeated retries.

**Players want an explicit, out-of-fiction statement that content has ended; in-world cues are missed or read as a
missing item.**
- In Abiotic Factor an NPC turning the player back and a "nothing else, for now" line were missed or taken for a
  missing key item. The thread asks for "a non-immersive popup that declares the end of the content" and notes players
  skip in-world text, "reading while exploring in this game being a liability" (verbatim, Steam thread, read in full).
- One Aloft poster was unsure whether they had finished and cited an "End of current content" message in Forever
  Skies, wanting the same (verbatim, Steam thread, read in full).
- One itch.io comment says a game should show a screen stating there is no more content until the next update
  (verbatim, one comment; the parent post was not read).
- Kentucky Route Zero's act gaps (two years before Act IV, seven overall) cost a reviewer their memory of earlier
  acts, and no "to be continued" text was found (opinion, HonestGamers, read in full). Forum comments that players
  wait until all acts are out are snippets.

Rule (inference from the verbatims; no source measures it): the end of current content gets its own card worded out
of fiction, with a date only if one is true, and distinct from any wait.

## Three costs of over-juicing

Lost immersion (snippet, Folmer Kelly), weaker results at Extreme than at Medium or High on all ten measures that
differed (research, Kao 2020, full; partial eta-squared at most .010), lost agency (amplification lowered motivation;
Kao 2024), and bodily harm (shake and flashes reported to trigger nausea and headaches, practitioner, snippet).
Habituation and parallax as causes are inference, not sourced. The check for a new effect is "what does it show that
the player did not already see", not "does it look good". An effect with no information content is the
first cut.

## What the evidence cannot say

No developer account of feedback design inside Cookie Clicker, Melvor Idle, Kittens Game or Antimatter Dimensions was
found. Sound design specifics were not researched. Also not found: design write-ups of "come back tomorrow" wording
for Neko Atsume or Animal Crossing (only essays that progress continues while the game is off), and official
end-of-content text for Antimatter Dimensions, Kittens Game or Cookie Clicker.
