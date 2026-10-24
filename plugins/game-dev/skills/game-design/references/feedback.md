# Feedback and game feel (juice)

How much feedback an action should get, how fast, and when to stop. Sources: `evidence/feedback.jsonl`. The primary
talks (Jonasson & Purho, Nijman's "Art of Screenshake", Swink's book) were not retrievable as text; claims about them
come from secondary summaries.

## More is not better: aim for the middle, tied to what happened

**Medium feedback beats none and extreme; feedback that depends on success beats feedback that is merely bigger.**
- One action RPG built at four juice levels (none, medium, high, extreme; visual and audio only): medium and high beat
  none and extreme on experience, intrinsic motivation, playtime and performance, n=3,018, a "goldilocks effect"
  (research, Kao 2020, reported by Pichlmair & Johansen's survey and Kao et al. CHI 2024; the 2020 paper itself was not
  read, so its effect sizes are unverified).
- Preregistered, 1,699 participants: success-dependent feedback raised curiosity, effectance and competence.
  Amplification (the same feedback made larger) lowered effectance and competence against standard feedback, which the
  authors tentatively put down to impeded agency. Curiosity was the only predictor of free-choice playtime; enjoyment
  did not predict playtime (research, Kao et al., CHI 2024).
- The effectance scale this literature uses has poor validity (research, Ballou et al. CHI Play 2021, snippet). Trust
  the shape, not the effect sizes.
- A GDC counter-talk argued juice can cost immersion (opinion, Folmer Kelly, snippet).

Rule: give feedback a ladder with a ceiling. The rung depends on what happened (an ordinary result, a first-of-kind, a
rare find, a failure), each rung has a fixed size, and the same event class never escalates over time.

## The unit of feel is one input answered by several small cues

- Juice's original claim is responsiveness to input: tweening, squash and stretch, sound; "maximum output for minimum
  input", with crude graphics mattering less than interactivity. Demonstration, not measurement (developer, Jonasson &
  Purho, secondhand).
- Nijman stacks many small cues on every shot; the numbers were not retrieved (developer, snippet, unverified).
- Swink defines game feel as "real-time control of virtual objects in a simulated space, with interactions emphasised
  by polish". It assumes a controlled object; applying it to screens with no avatar is extrapolation (snippet).
- Juice is "excessive amounts of feedback in relation to user input", mechanically superfluous, and juice-rich
  interaction makes it hard to learn which aspects matter mechanically (research, Pichlmair & Johansen survey).

Rule: several cheap simultaneous cues (motion, sound, a number), none load-bearing alone.

## Answer within about 100 ms

**"0.1 second is about the limit for having the user feel that the system is reacting instantaneously"** (practitioner,
Nielsen, citing Miller 1968 and Card et al. 1991, which were not read). Hit flashes of 50-100 ms and button transitions
of 80-120 ms are unmeasured rules of thumb (practitioner, snippet).

Rule: acknowledge every input at once even when the result is not ready: a press state, a refusal, "queued". An input
that does nothing reads as a bug, so a refusal is feedback too.

## Reduced motion is a requirement with small, concrete asks

- WCAG 2.3.3 (AAA) accepts the `prefers-reduced-motion` query or a user setting as a way to stop interaction-triggered
  motion; web.dev advises the reduced version as default for non-essential motion (guideline, snippet).
- Game Accessibility Guidelines: avoid flicker and repetitive patterns; option to hide background movement; option to
  hide all non-interactive elements; avoid sudden unexpected movement; no essential information by sound alone;
  replicate significant sound as text or visuals (guideline).
- Shipped games give separate toggles for screen shake and flashes; "no more than 3 flashes per second" is a community
  summary of the photosensitivity rule (practitioner, snippet).

Rule: one switch, the OS preference honoured plus an in-game setting, that replaces each motion with a still
equivalent (a colour change, a held highlight). Remove the movement, never the information. Cap flashes. Sound never
carries information alone.

## Slow and background processes need a different kind of feedback

**For a process that runs without the player, the problem is legibility over time and a signal at the end.**
- An idle-game taxonomy covers rewards, interactivity, progress rate and UI, but its abstract claims nothing about
  feedback; the body was not read (research, Alharthi et al., CHI 2018).
- Cookie Clicker reads as feedback on every cookie, generator and upgrade early, then scarcer, accomplishment-flavoured
  rewards later, with costs and income shown plainly (opinion, one analyst, not the designer).
- Offline-return guides name clear feedback on return as a main risk; players value offline progress matching active
  play (practitioner and player opinion, snippet).

Rule (inference from the findings above, not measured): feedback pace tracks process pace. A slow bar needs visible
creep and a distinct completion; a return needs a summary of what happened; an effect fired per tick on a constantly
ticking process becomes noise.

## Three costs of over-juicing

Habituation and lost immersion (extreme worse than medium; Kelly), lost agency (amplification lowered motivation; Kao
2024), and bodily harm (shake, flash and parallax cause nausea and headaches). The check for a new effect is "what does
it show that the player did not already see", not "does it look good". An effect with no information content is the
first cut.

## What the evidence cannot say

No developer account of feedback design inside Cookie Clicker, Melvor Idle, Kittens Game or Antimatter Dimensions was
found. Sound design specifics were not researched.
