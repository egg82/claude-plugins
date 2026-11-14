---
name: knowledge-routing
description: Route a fact by what would make it wrong, not by what it is about — skill, doc, keyed data file, or global memory.
metadata:
  type: feedback
---

Before writing a fact down, ask **what would make it wrong** — that decides where it lives:

| Goes stale when… | Home |
|---|---|
| you deliberately revise the method | the skill's `SKILL.md` |
| the code beside it changes | a doc in that directory |
| the world moves underneath you | a keyed data file beside the runs (`known-benign.md`, `decisions.jsonl`) |
| this session ends (branches, worktrees, paused agents, peer agreements) | the next session's **prompt**; only if it won't fit, `~/.claude/HANDOFF-<topic>.md`, which the receiving session reads and **deletes first** so no stale handoff outlives it. The queue stays in the repo's own queue file, pointed to, never copied |
| never — it's how you want work done | global memory (`~/.claude/memory/`) — the **last** resort |

- **A skill must survive being handed to someone else.** MAC addresses, counts, dated "validated
  on…", device names go in a companion file beside it (`instance.md`, `config.json`).
- **A skill only exists when something loads it; a memory is always resident.** Agents skipped a skill
  named in their first line ~9% of the time under long multi-constraint briefs (0% on short focused
  ones) — it fails where the guidance matters most. So: memory = the trigger plus the few
  rules that must fire unloaded; skill = the method. That overlap is deliberate, not duplication.
  A skill's `description` is part of the skill: extend the trigger when you extend what it can do.
- **Record no-op verdicts** ("looked, it's fine"), keyed by subject — nothing else records what was
  considered and rejected, so it gets re-derived, sometimes wrongly.
- **Capture while it's live**, into the artifact that owns it; end-of-session retros leave platitudes.
- **A doc that REQUESTS an upstream change goes wrong the moment it lands**, and nothing prompts a
  revisit: write what will be true when they act. Cite the SUBJECT, never a position or number ("ADR-0007", "item 3", "step 4"): reordering breaks the
  citation with no diff at the citation site. Write the claim, or point at a path whose name says its subject, and gate it
  (every cited path resolves). An applied database migration is immutable (its hash is checked at deploy): exempt it.
- Colocation is the forcing function: a doc beside the code moves with it and dies with it. Don't add
  "remember to update this" — add a check that reports drift (`config-hygiene`).
- **When adding to anything that routes by symptom, make the row name every entry that answers that symptom.** A new
  entry can capture a symptom a sibling already answered; grep the neighbours for the mechanism you just wrote up, since
  the one you are duplicating is the one that will contradict you.

Full reasoning: `~/.claude/memory/evidence/knowledge-routing.md`.
