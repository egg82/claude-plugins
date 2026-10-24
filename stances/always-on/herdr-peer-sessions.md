---
name: herdr-peer-sessions
description: Start new Claude sessions as herdr agents (a tab per session) so the user can see and track them
metadata:
  type: feedback
---

When the user runs Claude Code inside herdr, **a new session they should see and track is a herdr agent, not a
`claude --bg` or `claude -p` worker**: herdr's tabs never show those. The point is that the user can
see and track them in the herdr harness. Applies when `HERDR_ENV=1`.

**How:** method is `herdr --skill` (the installed binary is the authority on syntax). The shape is
`herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd <repo> --label <name>`, then
`herdr agent start <name> --kind claude --pane <root_pane> -- --model <model>`, then
`herdr agent prompt <name> "<brief>"`. A long-running session gets its own tab; a short helper can be a sibling pane
(`pane split --current --no-focus`).

Relates to [[skill-fanout-is-authorized]].
