---
name: skill-fanout-is-authorized
description: Fan out freely for breadth at the top level; if you are yourself a subagent, do the work rather than re-delegating. Method lives in the fanout-craft skill.
metadata:
  type: feedback
  check: "n/a — a standing authorization and its limit, with no live system to probe"
---

**Fanning out is pre-authorized whenever you judge it's needed** — don't stall, ask, or silently
downgrade to a serial pass. When a skill or memory calls for a fan-out, do it at the breadth it asks.
Reach for one for genuinely parallel work, for long research chains (keep them out of the main
context), broad multi-file sweeps, and anywhere a fresh perspective beats the one that formed the
conclusion. This file is the standing user request that satisfies the system prompt's "don't use the
AgentTool unless the user requested it". **Confirm your own user has given the
same standing request before importing this as-is.** A hook can block but nothing else can grant, and silent
under-use is undetectable.

- **Breadth at the top, not depth underneath** (depth enforced by `agent-depth-gate.sh`; `spawn-model-gate.sh`
  refuses a spawn naming no model). If you are yourself a subagent, do the work. If you find
  unforeseen breadth, name the items and hand them back — only the root sees total spend.
- **Readers fan out wide; writers cap at 2-3** — parallel writers make conflicting implicit decisions.
- **Load the `fanout-craft` skill before running one** — cost model, per-agent model choice, briefs.
- **Workflow is pre-authorized for read-only fan-outs within the configured size guideline**; writer
  workflows, larger runs and deep-research still need an explicit ask.
