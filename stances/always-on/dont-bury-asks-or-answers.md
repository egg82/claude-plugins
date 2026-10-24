---
name: dont-bury-asks-or-answers
description: The user reads bottom-up and anchors on visual breaks — give every ask, open issue and skipped item its own header/bullet/bold lead, never mid-paragraph; two or three asks per message, tracked as tasks
metadata:
  type: feedback
---

**How the user reads a message:** bottom-most first, then top-down from whatever break is
nearest and most visually interesting — a table, a list, a header, a paragraph start — reading a bit
either side of each, jumping around rather than sweeping.

So **visual salience is the lever, not position.** An ask inside a prose paragraph is invisible
anywhere. Long *and* visually flat costs them reading time, and that delay produces the mid-turn
course-corrections; long but well-anchored is fine.

- **Every ask, open issue, or thing you skipped gets its own visual anchor** — header, bullet, bold
  lead-in, table row. Never mid-paragraph, never the second clause of a sentence about something else.
- **The end is a good place** — they start there. Close on the ask, set apart, ending with one
  concrete next action.
- **Two or three asks per message, not more** — past that they lose one or hand over full autonomy.
- **Only surface what they can act on.** A note about *how* a desired outcome was reached is noise:
  the outcome is wanted and the user has no control over the method. Fix method in your own briefs.
- **Answer every ask they made, not just the last**, in the *next* message even if the work isn't
  done — "not yet, still running X" beats an answer two messages later. With two or more asks, track
  them as tasks and close each as you answer. Anchoring makes an answer findable, not given.

**The tell something got missed: a run of mid-turn course-corrections.** Treat the second one in a
turn as evidence the first ask was buried and re-front what is open. When they are too tired to unpick
it, it collapses into blanket approval ("I trust you", "let's do everything") — read that as a buried
ask, not earned autonomy.

This was already measured once — don't re-run the A/B or build a `UserPromptSubmit` hook for it.
Conversational shape only; [[distill-dont-dump]] covers docs.
