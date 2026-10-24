---
name: shell-footguns
description: "Foot-guns in the Bash tool's shell (bash; remote ssh runs zsh) and when a command's result can lie — sourcing, grep as a function, process matches hitting the harness wrapper, canaries that cannot fail. Use when writing a shell script, a command reports success but the result looks wrong, a probe returns zero, a wait loop returned impossibly fast, matching/killing processes, or adding a rule to bash-footgun-gate."
---

# Shell craft

The Bash tool's shell is **bash** (`CLAUDE_CODE_SHELL=/usr/bin/bash` in `settings.json`). A command
sent with `ssh host '...'` still runs under the remote host's **zsh** login shell — see the Remote zsh
section of `references/zsh-and-scripting.md`.

**What is enforced where, because it decides whether you can rely on being warned.** Everything a
command string CAN prove is in
`bash-footgun-gate.sh` (measured: 38 blocks over 16 sessions in a month, on ~13k Bash calls — rare
enough not to be wallpaper, frequent enough to be doing the work); `script-lint.sh` runs the same rules
over a `*.sh` file after a Write/Edit, as advice it cannot block; and un-waited detached work is
caught by `detached-work-gate.sh` at Stop. The resident copies of those two were removed once the hooks
were measured firing: prose that has already failed to prevent a trap does not get restated, it gets
executed. This skill is the catalog behind all of it — traps that fire in specific situations, and that
mostly fail *silently*.

**The gate is scoped by TOOL NAME.** It runs for `Bash` and `Monitor` (both run a `command` in this
shell). Widening it takes two edits that must agree: the `matcher` in `settings.json` and the
`tool_name` check at the top of the hook; widening only the matcher invokes a hook that exits at once.

**The theme worth holding onto: most of these produce a plausible-looking success.** A truncated file
reports exit 0, a dead regex reports a clean result, a killed process reports "alive". None of them
announce themselves, so the defence is checking the result rather than the exit status.

## Rules that apply on every use

- **Before believing a zero, make the probe prove it can return non-zero** — a control you know is
  present, ideally one you know is absent. A canary puts one token per line.
- **Never silence stderr on a command whose output you are about to draw a conclusion from.**
- **A pipeline reports its LAST stage's status, and an `echo` reports intent, not outcome.** Redirect
  and read the file, or `set -o pipefail`; in bash the array is `${PIPESTATUS[0]}` (zsh's
  `${pipestatus[1]}` is empty here). A `run_in_background` wrapper ending `cmd; echo "exit=$?"; tail log`
  completes "exit code 0" whatever `cmd` did: end it `rc=$?; ...; exit $rc`, or read the output before
  believing the notification (a failed ship sat ten hours that way).
- **When a probe contradicts something you read with your own eyes, trust the reading and fix the
  probe.**
- **A gate blocked you?** Its tag is `[gate:<name>]`; `grep -rn '<name>' references/` finds the entry
  and the reason.

## The catalog — open the file for the situation you are in

- **Writing or sourcing a script, quoting, loops over filenames, reserved variable names, `set -e`,
  merge-conflict regexes, misleading CLI flags, and zsh traps in `ssh host '...'` bodies** →
  `references/zsh-and-scripting.md`.
- **A probe returned zero / a clean result / "alive" and you are about to believe it** — `2>/dev/null`,
  `bfs` timestamps, `grep` with a leading-dash pattern, sudo-side globs, `Restart=` services,
  `~/.local/bin` over ssh, empty JSON payloads, reused `-o` paths, `sort -u` locale, sorted `head`,
  `nc -zu`, unpaged `ldapsearch`, `node --check` → `references/probes-that-lie.md`.
- **A status check, watcher or wait loop said success (or failure) and you are not sure it is true** —
  `grep -q` under pipefail, formatters (`tail`/`sed`/`tee`) masking status, `$(cmd || fallback)`,
  unguarded `echo "PUSHED"`, `git commit …; git push` running after a failed commit, `tty`/`psql` errors on stdout,
  `pipestatus` vs `PIPESTATUS` → `references/exit-status-masking.md`.
- **Matching or killing processes, `ssh … bash -s`, `sudo` eating stdin, `while read` loops calling
  ssh/az/kubectl, `kubectl exec` data or long jobs, detaching work, Vault output, writing memory or
  skill files from Bash, a debug pod cloned from a Deployment** → `references/processes-remote-containers.md`.

## Adding a new foot-gun

**Don't rely on remembering.** Documenting these in an always-on memory was tried for weeks and
sessions kept hitting them anyway — the unquoted-glob rule was in context, verbatim, during three
separate hits in the session that audited it. So the workflow is evidence-driven, not memory-driven.

The transcripts already record every failure, so no extra logging is needed. Run the `mine-failures.py` beside this
SKILL.md:

```bash
python3 mine-failures.py         # ranked by recurrence
python3 mine-failures.py globs   # break down the top offender
```

**Promote a signature to the gate when it is both frequent AND statically detectable with no
legitimate false positive.** Those two conditions do real work:

- `for f in $(find ...)` qualifies — word-splitting a command substitution of paths is never what
  you meant, and `find -print0 | while read -d ''` always works instead.
- A bare path glob (`/sys/block/sd*`) does **not** qualify — sometimes expansion is exactly what you
  want. It stays documented here and ungated.

**Writing the test case is when the gate will bite you.** A gated pattern written as an ordinary
command argument — `t "must-block" 2 'pgrep -af x'` — puts the pattern in the *command string*, so the
gate fires on your test harness before it ever runs. Heredoc bodies are already stripped, and
`test-gate.sh` is immune because its cases live in a file; a throwaway inline check is not. Put the
case in a file and `bash` it, or `base64 -d` the payload. This is deliberately **not** gated around:
detecting "this is a test" would cost more false positives than the friction is worth. It cost two
round trips in one session.

Then add the rule to your copy of the gate (or fork the plugin) **and a case to `test-gate.sh`, both a
must-block and a must-allow.** A gate tested only on bad input cannot be told apart from one that
blocks everything; the must-allow cases are what stop it becoming annoying enough to disable. Run
`bash test-gate.sh` — it should end `fail=0`.

Write the rule from the **literal command string** of the incident, not from its summary, and make
that exact string a must-block case (the Vault entry in `references/processes-remote-containers.md`
is the worked example). **A gate's advice string is part of the gate** — the `PIPESTATUS` entry in
`references/exit-status-masking.md` shows advice text that caused the trap it guarded.

Traps that are real but *not* statically detectable stay in the catalog as prose, filed under the
matching `references/` file. That is the honest split: the gate catches what a string can prove, and
the catalog carries the rest.

## Measuring whether an environment fix actually worked

When a foot-gun is fixed in the environment rather than warned about, the before-numbers are the only
thing that makes the fix checkable — and they stop existing the moment you fix it. Record them in a
companion file under `~/.claude/local/shell-footguns/`, not in the skill: they are per-machine
measurements, not method, and they go stale by design.

Two things that decide whether the later re-measure means anything:

- **Filter by mtime** (`find … -newermt <fix-date>`). Without it the pre-fix corpus swamps the signal
  and a real drop reads as slow decay.
- **Fix the denominator and say which one you used.** Subagent transcripts outnumber top-level
  sessions several to one, so "32% of transcripts" and "49% of sessions" describe the same world and
  answer different questions. Quote both or neither.

**A transcript newer than the fix is not the same as a shell that has the fix.** The `.zshrc` line
only takes effect in shells started after it was written, and the Bash tool initializes its shell
once per session from a snapshot. So a session that began before the edit and ran on afterwards has a
**pre-fix shell and a post-fix mtime** — it will show hits and drag the post-fix rate up. The session
that made this measurement is itself an example.

Practically: date the cutoff from the *first session started after the fix*, not from the edit, and
discard anything straddling it. And do not read a small post-fix sample at all — at a ~30% base rate,
a handful of transcripts cannot separate a real drop from noise in either direction.

And be clear what a drop proves: for the unmatched-glob case it measures **visibility, not
correctness** — the pipeline still prints `0` and exits `0`, it just also writes a visible error now.
