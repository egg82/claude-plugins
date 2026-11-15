---
name: herdr-peer-sessions
description: Start new Claude sessions as herdr agents (a tab per session) so the user can see and track them
metadata:
  type: feedback
---

When the user runs Claude Code inside herdr (`HERDR_ENV=1`), **a new session they should see and track is a herdr
agent, not a `claude --bg` or `claude -p` worker**: herdr's tabs never show those.

**How:** method is `herdr --skill` (the installed binary is the authority on syntax). The shape is
`herdr tab create --workspace "$HERDR_WORKSPACE_ID" --cwd <repo> --label <name>`, then
`herdr agent start <name> --kind claude --pane <root_pane> -- --model <model>`, then
`herdr agent prompt <name> "<brief>"`. A long-running session gets its own tab; a short helper can be a sibling pane
(`pane split --current --no-focus`).

**Confirm the agent came up before prompting it.** A new pane opens a login shell, and a shell-framework update
question can eat the typed start command. If it isn't a running claude, close that tab and start again.

**After the first prompt, talk to a peer only with `SendMessage`, never `herdr agent prompt` again.** Prompting types
into the pane's input box, so it splices into whatever the user is typing there, even mid-word. This holds for a
successor too. One exception: a just-started agent may not yet be reachable ("No agent named ... is reachable"); only
then fall back to a short `herdr agent prompt`, with anything long in its handoff file.

**Handing off at a context limit leaves your subagents reporting to YOU, not the successor.** Keep the old tab open to
relay their reports (append each to the handoff, then prompt the successor) and tell the user.

**One session has two names**: its herdr label and its `ListAgents` name, so a parent can report "two sessions on one
handoff" and you negotiate with yourself. The tell: `herdr agent prompt`'s `agent_session.value` is your own session id
(the uuid in your scratchpad path). Check that before telling a "duplicate" to stop.

Relates to [[skill-fanout-is-authorized]].
