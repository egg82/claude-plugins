---
name: user-forcing-function-style
description: "Some users manage work by engineering their environment rather than by willpower rituals — confirm it for yours, and if it holds, design systems that don't depend on remembering"
metadata:
  type: feedback
---

**An observation to confirm, not a fact about your user.** It came from one user elsewhere and
may not describe yours — plenty of people run a weekly checklist happily. The tell is a recurring
manual step that was agreed to and then quietly stopped happening. Ask once, or watch for that, and
drop this note if it doesn't fit.

**Where it does hold, it is a design constraint.** Prefer solutions that happen by default —
automation, good defaults, push/forcing-functions — over any workflow that needs the user to
remember a recurring manual step; a "check this weekly" ritual is the wrong shape, because it has no
failure signal and its absence looks exactly like nothing being wrong (and a doc saying "remember to update
this" is read when you open it and needed when you're editing something else). Make the environment do the
remembering: a hook, a scheduled job that pushes, a check that reports drift. Offload judgment-heavy recurring chores (tagging, triage, sorting) onto Claude rather
than onto the user. Pairs with [[prefer-subtraction]] — keep the surface they touch small — and with [[knowledge-routing]], which applies the same rule to where a fact lives.
