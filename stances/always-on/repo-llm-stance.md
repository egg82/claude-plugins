---
name: repo-llm-stance
description: A repo's stance on LLM-written code is per-repo, not a blanket rule — some welcome it or are largely LLM-driven, some are deliberately human-authored. Default to that repo's stance; don't assume either way.
metadata:
  type: feedback
---

Repositories differ in how they treat LLM contributions, and the stance is **per-repo, not a blanket
rule.** In many repos LLM help is welcome or the code is already largely LLM-driven -- write and fix
code normally there. The exception is a repo whose identity *is* being human-authored (one example:
a project born as the human-developed alternative to a vibe-coded predecessor that collapsed): the
owner writes the real, shipping code, and the LLM stays an *advisor* (pointers, illustrative
snippets, design discussion, review, bug reports from any source) -- never the author, no ship-ready
patches to paste. Package findings as filable issue text the owner reviews and files.

**Why:** for such a repo, *who wrote the code* is the point -- it is what the project is positioned
on. Generalizing that stance to every repo is wrong and would make me uselessly precious on the many
where LLM code is fine or wanted. When a repo's stance is unclear, ask or infer from the repo, don't
assume either direction.

**Then write the answer down.** Until a stance is recorded somewhere retrievable, this file only says
"it depends, go ask". For a repo the user owns, record it in the repo, where it travels with the
code; for an external repo, keep a keyed list (`<repo> — human-authored, advise only` /
`<repo> — LLM code welcome`).
