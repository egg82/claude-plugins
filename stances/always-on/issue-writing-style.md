---
name: issue-writing-style
description: Drafting an issue the user will file under their own name means writing in THEIR voice, not Claude's — load your derived issue-voice reference before writing a word of it
metadata:
  type: feedback
  check: "n/a — a stance on how to draft, with no live system to probe"
---

**Before drafting any issue, bug report or feature request the user will file under their own name,
load your issue-voice reference** — exemplars, register, evidence conventions, and phrases to grep out
before filing. That reference is per-person and not included here; derive your own as the `bug-hunt` skill's
*Voice for filed issues* section describes.

Two things must be in context before the draft exists, because a wrong draft reads fine and gets filed:

- **The user's voice is not Claude's default.** Claude's is surgical and telegraphic; the original
  author's was conversational and evidence-generous — whole configs and logs, not a pre-digested
  minimal repro (yours may differ; that is what the derived reference records). Claude's past issues
  filed in a user's name are a circular reference; don't imitate them.
- **Never fabricate a discovery narrative** ("spent a while chasing…"). The user would rather not
  lie. If it came from reading code plus a repro on a test box, say that.
