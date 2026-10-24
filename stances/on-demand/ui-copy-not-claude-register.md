---
name: ui-copy-not-claude-register
description: "In the user's apps and games, player/user-facing text must not carry Claude's conversational register; they spot it at once"
metadata:
  type: feedback
---

The user spots Claude's register in UI copy immediately: it is the kind of thing you pick up on after interacting
with Claude a lot. Seen in a game's first design pass: controls phrased as
questions, and flavour lines that each reach for a twist.

**Why:** controls written as friendly full sentences or questions, and flavour lines that all reach for a twist,
read as an assistant talking rather than a game.

**How to apply:** controls and labels are terse nouns and verbs ("Start", "Pause", "Cost 12", "Unknown"); world
text follows the project's own voice rules (look for a decisions or style doc in the repo). Before
showing the user any screen, reread every string as a player would and cut sentences, questions and narration from
controls.
