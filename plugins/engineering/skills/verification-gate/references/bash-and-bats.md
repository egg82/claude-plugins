# Bash and bats: making shell code testable, and harness traps

The shell-specific half of `SKILL.md` steps 4 and 6. Load it when the code under test is bash, or the
harness is bats or a hand-rolled shell runner. For foot-guns in the shell you *probe* with (zsh,
`BASH_SOURCE` when sourcing, process matching, canaries that cannot fail), load the `shell-footguns`
skill.

## Make the code reachable (step 4)

The most common reason important logic has no tests is mechanical, not cultural: the
file ends in a bare `main "$@"`, so sourcing it runs it. One line per file fixes it:

```bash
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
```

Use `if`, **not** `&&`. As the last statement a false `&&` returns 1, and `set -e` in
the caller takes the sourcing shell down with it — silently.

In one repo that single change moved a large fraction of the codebase from untestable to testable, and
the first thing it exposed was a set of port validators guarding which ports an
unprivileged user could open, with no tests at all.

## Harness traps (step 6)

Verified traps:

- **`!` does not fail a bats test** (SC2314). `! cmd` in a non-final position returns
  and the test passes. Use `run` plus an explicit status assertion.
- **`run` always succeeds**, and historically suppressed `set -e` — bats **1.14.0
  flipped this by default**. `bats_require_minimum_version` (available since 1.7.0) pins
  the harness version but does **not** gate this behaviour — so always assert `$status`
  explicitly and never rely on the ambient semantics.
- **Sourcing a program inherits its `trap … EXIT`**, replacing the harness's own — the
  test then *vanishes* from the output instead of failing. Source in a subshell.
- **A PATH stub is bypassed** by an absolute path, a builtin, `command`, sudo's
  `secure_path`, or systemd's fixed PATH — and bash **falls through a non-executable
  PATH match to the next directory**, finding the real binary. Assert the stub is what
  `command -v` resolves to, before any test body runs. If the stubbed binary is
  `systemctl`, that assertion is the difference between a test run and a reboot.
- **Bound the run.** Per-test timeouts, and reap helper processes by *group*
  (`setsid --wait`, or resolve the PGID and `kill -- -$pgid`; plain `setsid` does not
  fork when the caller is already a process-group leader, so under job control `$!` is a
  dead PID and every helper survives), because `kill $pid` leaks a listener holding a port and
  a non-interactive bash sets SIGINT to ignore for async children.
