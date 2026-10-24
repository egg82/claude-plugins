---
name: route-lessons-yourself
description: Route a lesson the moment you admit a mistake — don't wait to be told to capture it — and sweep again at wind-down; persist only verified conclusions
metadata:
  type: feedback
---

The user should never have to say "we should capture these lessons". The gap is not noticing — the
admissions are in the transcripts — it is the step after: the breakage gets fixed, the task moves on,
and capture loses to the task every time. **Treat "I just hit a trap" as part of the task and route it
in the same breath as the fix**, by [[knowledge-routing]]'s table. A trap provable from a command
string with no legitimate false positive goes in `bash-footgun-gate.sh` (procedure: `shell-footguns`).

- **Prose is not a fix for a trap prose already failed to prevent** — escalate to something the
  harness executes (enforcement here: `route-lesson-gate.sh`, `mine-repeat-traps.py`). Both fire too
  late to cause capture, which is why this rule is resident.
- **Sweep again at wind-down** ("thanks", "done for now", a natural stop, before compaction): what did
  we learn, what guidance was given, what would make the next session faster? Write what isn't captured.
- **Persist only verified conclusions.** A wrong memory anchors future sessions and reads as
  authoritative; mark a guess as a hypothesis, and correct earlier notes once verified.
- **Don't over-apply it.** A one-off slip needs no gate, and a gate with false positives gets switched
  off. "This does not generalise" is a complete answer.
