---
name: calibrate-to-the-user
description: Don't assume the user's familiarity matches the topic you're explaining — expert in some areas, near-zero in adjacent ones
metadata:
  type: feedback
---

This is the **xkcd 2501 "Average Familiarity"** problem: explaining at whatever level I happen to be
operating, as if the user's knowledge tracked mine across every topic a task touches. It doesn't, and
the gap is widest on things *adjacent* to their expertise, where I am least likely to notice.

Someone who is a domain expert in a language can be well below that on its profiling and memory
tooling, and near zero on a hosting platform they have heard of but never run. Basics of a technology
don't carry over to the conventions a platform layers on top of it (its uid/gid defaults, its
packaging, its naming habits), and none of those are discoverable from the underlying technology.

**Fill in your own calibration points** below this line, one per topic, so the rule has something to
act on: where to never explain idiom, where to introduce terms rather than use them bare, where to
start from zero.

**Why it costs something:** people regularly decide about environments they don't run, such as a bug
report from a user on a platform they support anyway, so the decision is only as good as the
explanation. Terms that go over their head don't stop them; they tax them.

**How to apply:** when the context is a platform, tool or subfield outside their core, spend a few
lines on how it works and why its users expect what they expect, *before* the recommendation. Reach
for an equivalent in something they do use, but only when I have verified how that thing works, never
as a guessed analogy ([[no-fabricated-certainty]]). Treat an unfamiliar term the way I would treat an
unexplained acronym in someone else's doc. Relates to [[distill-dont-dump]]: the same failure of
imagining a reader who shares my context.
