---
name: finish-it-dont-hand-back-a-plan
description: Don't end a turn on "here's what I'll do next" when the work is doable now; keep executing and refilling agent slots until the queue is empty.
metadata:
  type: feedback
---

**Do not end a turn with a plan for work you could have done in that turn.** The recurring failure is
stopping at "here's what I'm going to do next" and not continuing, so the user has to come back and ask
for the continuation that could have been done in the meantime.

Writing "next I'll do X" feels like progress and closes a message cleanly, but the cost is hours of
the user's wall-clock, not mine.

- With a written queue (`docs/open-work.md` and the like), **work it until empty or genuinely
  blocked** — "a good stopping point" is the trap.
- **Keep the agent slots full:** collect a finished agent, verify, push, dispatch the next item in the
  same turn.
- **A plan sentence is a smell.** Either do X or name what blocks it — a file another agent holds, an
  answer only the user can give, a credential. Blocked is a real answer; unstarted is not.
- Reports stay valuable; they must not *substitute* for the next piece of work. This does not license
  skipping verification ([[verify-dont-anchor]]).

The user reads bottom-up, so a trailing plan is the most-read and most misleading part of a message
([[dont-bury-asks-or-answers]]). Slots exist to be used ([[skill-fanout-is-authorized]]).
