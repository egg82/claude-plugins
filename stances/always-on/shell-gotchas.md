---
name: shell-gotchas
description: The Bash tool runs bash (CLAUDE_CODE_SHELL), but `ssh host 'cmd'` still runs cmd in the remote zsh login shell — send remote work as a bash script. Write non-trivial shell to a file. Catalog in the shell-footguns skill.
metadata:
  type: feedback
  check: "n/a — a property of the harness's shell, asserted as a working stance"
---

The Bash tool runs **bash** here (`CLAUDE_CODE_SHELL=/usr/bin/bash` in `settings.json`,
because a dozen gate rules existed only to catch zsh semantics). Login shells on remote hosts are still
**zsh**, so **`ssh host '<cmd>'` runs `<cmd>` under zsh** — globs, word-splitting and `nomatch` behave
the zsh way there. Send remote work as `ssh host 'bash -s' < script.sh` or `ssh host bash -c '…'`.

- **Beyond a one-liner, write a `#!/usr/bin/env bash` script to a file and run `bash <file>`.**
- **`pipefail` is off, deliberately** — on globally it makes `cmd | grep -q x` fail on SIGPIPE when the
  match is found. In a script, `set -o pipefail` and avoid `grep -q` on a pipe (`grep -c … >/dev/null`).
- **Detaching (`nohup`/`setsid`) needs a waiter armed in the same turn** — a `run_in_background` poll
  or a `Monitor`, as a separate call — or nothing ever wakes you and the result lands in an unread log.
  The waiter also catches the opposite failure: a detached job dying instantly and exiting 0. So a
  detached script sets its own `PATH` and preflights its binaries, and "it is running" is not the
  claim to verify — verify it completed one iteration of real work.
- **A script file gets the gate's rules only as advice, after the write** — `script-lint.sh`
  (PostToolUse on `*.sh`/`*.bash`) runs them over the file body; it cannot block. A script written by
  any other route (heredoc, `cp`, a generator) is unseen. Use `shell-footguns` as a checklist.
- **`set -e` typed into the Bash tool does nothing**: errexit is ignored there, even in a subshell (measured:
  `set -e; false; echo x` prints `x`). It works inside `bash <file>` or `bash -c '...'`; in the tool, chain with `&&`.
  A failed `git worktree add` once let the next `cd` fail and the rest ran in the main clone.
- Before writing a rule about a trap, ask whether the environment can make it impossible. A gate rule's advice text is
  read as a command you are about to run: three rules once recommended an array that is empty in the shell they guarded.

Catalog: the `shell-footguns` skill. The silent ones are blocked by `bash-footgun-gate.sh`; new
foot-guns go in the skill. Incidents: `~/.claude/memory/evidence/shell-gotchas.md`.
