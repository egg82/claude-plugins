---
name: match-existing-house-style
description: Read the sibling artifacts before authoring a new one -- copy their exact tokens and class vocabulary rather than inventing a fresh visual language that reads as foreign
metadata:
  type: feedback
---

When adding an artifact to a repo that already has siblings of the same kind — a fourth dashboard,
another page, one more ADR — **read the siblings first.** Open the most recently worked one (it carries
the accumulated fixes, often a comment naming what is shared), copy its token block verbatim, reuse
its class vocabulary and the element it styles, and add only what the new thing needs; mark in a
comment which parts are shared and which are new.

Twice I designed a fresh palette instead, and both times it looked foreign — most visibly a white box
from styling a wrapper `div` rather than `body` — once despite a header comment next door naming the
house style. **A near-miss palette reads as a mistake, not a variation: copy exact values.** If the
repo has no convention, say so rather than silently inventing one. Same for doc structure, file
layout, test shape, CLI flag naming. Relates to [[prefer-subtraction]].
