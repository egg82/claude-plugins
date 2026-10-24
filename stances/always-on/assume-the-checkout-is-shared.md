---
name: assume-the-checkout-is-shared
description: Another session may be in the same clone (or the same config tree) — commit as you go, and use a throwaway git worktree for multi-step work rather than trusting the shared working tree
metadata:
  type: feedback
---

Another session — or the user — may be in the same clone. Working tree, index, HEAD and the remote branch
namespace are shared mutable state and change under you silently. `~/.claude` is a shared tree too.

- **Commit with `git commit --only <paths> -m ...`**, never `git add` + `git commit`: the pair commits
  everything *staged*, and a peer's staged feature once shipped under an unrelated commit message.
  `--only` is per FILE, not per hunk — check `git diff --stat <file>` against the size of your change
  *before* committing, and check `git show --stat` after. Once pushed, leave a mis-attributed commit
  and say so; rewriting it is the destructive move.
- **Commit early, onto your own branch** — uncommitted work is all another session's reset can kill.
- **Multi-step work in a repo someone may also be in: `git worktree add <dir under $HOME> <branch>`** (not
  the `EnterWorktree` tool; this never moves the user's checkout; not `/tmp`, which a reboot empties). Remove + prune when done.
- **Never `git checkout` another branch in a clone you do not own. Never `git stash` in any checkout
  where a subagent or session may be writing — your own included.** Stash is a whole-tree revert that
  races any agent mid-edit (it bit here in my own checkout, with my own subagent mid-edit). To compare against another state, READ it
  (`git show HEAD:path | checker`, `git diff`) — don't move the tree to look and move it back.
  `git checkout -b` is the same command: decide whether the clone is yours at the first write.
- **The second actor is often one you spawned** — a writing subagent shares your tree and HEAD.
  Decide the worktree when you delegate; partitioning files in the brief does not cover HEAD.
- **Identify an owner from `git log` on the file and `ListAgents`** — every session commits as the user.
  Something suspended that you didn't suspend (Flux, a pipeline): ask, don't resume.
- **Your green may borrow a collaborator's uncommitted work.** Before committing something whose
  validity rests on files outside your diff, `git status` those paths; the thorough check is a clean
  worktree of HEAD, which is what CI sees.
- **An editable install defeats that worktree** — `pip install -e .` imports from the original
  checkout. Set `PYTHONPATH=<worktree>/src` and prove it: `python -c "import pkg; print(pkg.__file__)"`
  must print a worktree path, run from inside the worktree. Same for symlinked `node_modules`, `go.work`, cargo path overrides:
  isolating the files does not isolate the build.
- **Tells it already happened:** "nothing to commit" right after you edited, or a branch you never
  selected. Read `git reflog` before concluding your edits were never written.

Incidents: `~/.claude/memory/evidence/assume-the-checkout-is-shared.md`. Relates to
[[verify-dont-anchor]], [[preserve-before-destroying]].
