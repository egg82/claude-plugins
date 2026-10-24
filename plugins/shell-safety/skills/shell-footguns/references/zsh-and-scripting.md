# Shell and scripting traps

Catalog entries moved out of `SKILL.md`. A `[gate:<name>]` tag means `bash-footgun-gate.sh` enforces
the entry; everything else is prose-only.

The Bash tool's shell is **bash** (`CLAUDE_CODE_SHELL=/usr/bin/bash`). Remote commands sent with
`ssh host '...'` still run under the remote **zsh** login shell — those traps are in
[Remote zsh](#remote-zsh-ssh-host-) below, and are not gated.

## Sourcing and script invocation

**A `bash -c` body run as a script file shifts every argument by one.**
`[gate:bash-file-underscore-arg]` `bash -c 'body' _ a b` sets `$0=_`, `$1=a`. The *same* body in a
file, `bash body.sh _ a b`, sets `$0=body.sh`, `$1=_`, `$2=a` — so a body reading `$1` gets the
placeholder and everything after it is off by one.

This matters because of *how* it fails. Extracting a helper's `bash -c` body to a file to test it is
a good instinct — you are testing the real code rather than a retyped copy — and the shifted
arguments made the probe operate on a path that did not exist. It moved nothing, printed nothing,
and exited 0. A verification that returns an empty result and success looks exactly like a
verification that passed. Keep the `bash -c` form when testing a `bash -c` body:
`bash -c "$(cat body.sh)" _ "$real_arg"`.

The general defence is a **positive control** — see `verification-gate`.

**A markdown backtick inside a double-quoted `--description` is command substitution.**
`[gate:backtick-in-prose-flag]` The shell runs whatever is between the backticks, so a sentence written as
``answers `400` rather than `404` `` sends "answers  rather than " — the codes are gone, the flag is
still accepted, and the MR reads fine at a glance. Nothing errors; the only trace is `command not
found: 400` on stderr, easily lost in a long command's output. This bit a real MR description
explaining what those status codes proved. Write the body to a file and pass `"$(cat body.md)"`: that
is substituted once by the shell and never re-interpreted. The damage lands in prose a human will
read rather than in a command.

## Iterating over filenames

**`for f in $(find ...)` word-splits every path containing a space.** `[gate:for-in-find-ls]` The shell
splits the command substitution on whitespace, so `Quarterly Report [v2].csv` becomes three "files"
that are not paths. It fails silently and at a scale that disguises itself: a per-file probe over a
few hundred such files produced **far more rows than files, every extracted field empty**, which read
as *"the probe tool found nothing"* rather than *"my loop is broken"*, and cost three rounds of
debugging the wrong component. Use
`find ... -print0 | while IFS= read -r -d '' f`, or `find ... -exec`.

**`IFS=$'\t' read -r a b c` COLLAPSES empty fields.** Ungated: tab-separated reads are often right. Tab is
IFS whitespace, so a run of tabs is one separator and every field after an empty one shifts left: an origin
address landed in a timestamp column and the record still parsed. Use a non-whitespace separator (`|`,
`\037`) for any row that can hold an empty field, and test a row with one.

**`read -d` is a bash extension and dies quietly under `sh -c`.** `[gate:read-d-posix-sh]` dash and
busybox `read` reject `-d`, so the loop body never runs — zero rows, no error, exit 0. The same loop
worked on the host under bash, which is what made it look like missing data rather than a broken
command. Use `bash -c`, or newline-delimited `while IFS= read -r f` when values cannot contain newlines.

All of these produce an **empty result that looks like a finding about the world**. That is the
signature to distrust: before believing a zero from a loop you wrote, make the loop prove it can emit
one non-zero row.

## Shell-reserved variable names

**Under bash a reserved name is SILENT, and it takes the surrounding loop with it.** A script that
used `GROUPS` as an ordinary array never populated it — bash reserves `GROUPS` for the caller's group
IDs and ignores assignments — and the enclosing `while` loop *exited* rather than erroring, so a
confirmation prompt and everything after it were skipped with no message at all. It read as "the
prompt is missing", not "the variable is reserved". `bash -x` is what located it, in one pass, after
guessing had failed twice.

Also not gateable: these are written with the file tools, so no command string carries the bug. The
practical defence is to know the reserved names before reaching for a generic one — `GROUPS`,
`SECONDS`, `LINENO`, `RANDOM`, `PIPESTATUS`, `BASH_*`, `FUNCNAME`, `HISTFILE`, `IFS`, `PWD`, `OLDPWD`,
`REPLY`, `OPTARG`, `OPTIND`, `SHLVL`, `UID`, `EUID`, `PPID`, `HOSTNAME`, `COLUMNS`, `LINES`. Prefix
script variables (`HOST_GROUPS`) rather than auditing against that list each time.
`UID`, `EUID` and `PPID` are readonly in bash too, but fail loudly.

## Writing a script

**A trailing `cmd && arr+=(x)` as the last statement of a loop body is a `set -e` landmine.** The
loop's exit status is its last command's, so a false final iteration makes the loop return 1 and
errexit ends the script — at a point that looks like clean completion. Write it as `if cmd; then
arr+=(x); fi`.

**When testing a script that generates a file, assert on the FILE, never on the `set -x` trace.**
The trace shows `+ printf '%s\n' 'worker_threads = 12' ... 'cache_mb = 384'` — the *call*, not what it
wrote — so a suite grepping the trace passes on output the script never produced, and fails on output
it did. The same distinction is a security property, not just a testing one: moving a here-doc to
`printf` put an API token into the trace that the here-doc had kept out of it.

**Never pipe `cat -A` through a line-prefixing `sed`.** `[gate:cat-a-through-line-prefix]` `cat -A`
is run to see the exact bytes of each line, leading whitespace included; `| sed 's/^/  /'` to indent
it for readability adds two columns to every line, so the indentation you read is wrong by exactly
the prefix width. Hit three times in one session, and each time the misread indentation went into a
scripted edit's anchor, which then failed to match -- silently, because `str.replace` returns the
string unchanged and exits 0.

The gate can only prove the `cat -A` case, where prefixing is never right. The broader rule is
judgement a command string cannot supply: **do not write an edit anchor from any output you have
reformatted for display.** `sed -n '10,20p' file | sed 's/^/  /'` is fine to look at and unsafe to
anchor from, and no regex can tell those two intentions apart.

## Resolving merge conflicts with a regex

**Anchor the markers to whole lines** (`re.M`, `^=======\n`, `^<<<<<<< `, `^>>>>>>> `). An unanchored
`=======\n` also matches the tail of a comment rule like `# ==========`, so the "ours" side is cut at
the first banner comment and the real separator survives into the file. Measured on a Python file
full of `# ====` section banners: the resolver printed success and the file failed to parse. Assert
afterwards that no line matches `^(<<<<<<<|=======|>>>>>>>)`, and parse the file with its real
parser. Also note that `git checkout -m <path>` recreates the conflict with the labels `ours`/`theirs`,
not `HEAD`/`<branch>`, so a pattern keyed on branch names finds nothing on the retry.

## CLI flags that mean something else

`[gate:glab-ci-list-b-is-a-date]` **`glab ci list -b` is `--updated-before`, not a branch.**

```bash
glab ci list -b my-feature    # Parsing time "my-feature" as "2006-01-02T15:04:05Z"
glab ci list -r my-feature    # what you meant
```

`-b` is the branch flag in `git`, and in glab's own `mr list`, so guessing it here is natural and
wrong: for `ci list` it is `--updated-before` and wants ISO 8601.

**What earns this a gate is not the typo, it is where the typo lives.** This flag gets reached for
inside a *poll loop* watching a pipeline, and there the error goes to stderr while the loop reads
stdout through a `grep`. Every iteration then reports a clean-looking nothing. Measured:
forty iterations printing `status=none`, read as "the pipeline has not appeared yet" rather than
"this command has never once run", and ten minutes spent waiting on a command that never ran. Same
family as the false-zero traps — the loop's own formatting is what hides it.

Fires only on a literal that is not a date, so a real `--updated-before 2026-01-01T00:00:00Z` and any
`-b "$SINCE"` pass untouched.

**`git push -o ci.skip` also skips the MR's pipeline.** Pushed to a branch that already has an open MR it
leaves the MR with no pipeline for that head, so "merge when green" has nothing to wait on and the change
merges unverified. Use it only on a branch's first push. Not gated: that is its legitimate use and the
string cannot tell whether an MR exists.

**`glab mr merge` waits only for a RUNNING pipeline.** If the MR's pipeline is still `created` or `pending`
it merges immediately, unverified, and prints the same MR URL either way. Read `head_pipeline.status` first
and merge only on `running` (to auto-merge) or `success`; afterwards check `state` together with
`merge_when_pipeline_succeeds`. Not gated: the state lives on the server.

**Never move a hand-grabbed download into a category a library manager scans.** (Not gated in this copy.)
Manual grabs land in the download client's default category, and "fixing" that to one a library manager
watches puts the payload where it scans. It then adopts the loose file onto whichever
record parses closest **as an upgrade**, deleting what was there — no error, and the only symptom is
a file size that looks wrong. Observed twice in one session, on a trap that was already written down.
Use `category=manual-hold` (watched by nothing) and import explicitly.

## Remote zsh (`ssh host '...'`)

On the remote hosts the login shell is zsh, so a single-quoted `ssh host '...'` body runs under zsh. These were
gate rules while the local shell was zsh too; the gate cannot tell which part of a command string
runs remotely, so they are prose now. The simplest escape from all of them is to send a script:
`ssh host bash -s < script.sh` (not a piped value, see `ssh-bash-s-stdin`), or `ssh host bash -c '...'`.

- **Unquoted glob in a flag value aborts the command.** `--include=*.py` is expanded against the
  cwd, and with `nomatch` (the zsh default) an unmatched pattern kills the whole command:
  `no matches found`. Quote it. A bare unmatched glob in a pipeline is worse: `ls /nope/*.log | wc -l`
  prints `0` and exits 0.
- **No word splitting of unquoted scalars.** `for x in $VAR` runs ONCE with the whole string;
  `set -- $line` leaves `$2`, `$3` empty; `CMD="ssh -o X"; $CMD host` is `command not found` for a
  command literally named `ssh -o X`. Use arrays (`A=(a b c)`, `"${A[@]}"`), `${=VAR}`, or
  `${(f)VAR}` for lines. A uniform answer across all items is the tell.
- **`$var:word` loses a letter to a history modifier.** After `$var:`, `a c e h l q r s t u A P Q`
  are modifiers (`f F g w` prefix one), so `$img:latest` becomes `<img>atest` — quoting does not
  help, unquoted heredoc bodies included. `${img}:latest` is safe; `:/` and `:$` are not modifiers.
- **`mapfile`/`readarray` do not exist.** `command not found`, then the next line runs on an empty
  array and reports zero.
- **`${PIPESTATUS[0]}` is empty**; zsh's array is `${pipestatus[1]}` (lowercase, 1-indexed). Under
  local bash it is the other way round, which `zsh-pipestatus-in-bash` gates.
- **MULTIOS: `cmd > file 2>&1 | head -5` truncates the FILE.** zsh duplicates stdout to the file and
  the pipe, `head` exits, the producer takes SIGPIPE mid-write. Measured: 88 lines of a 5,462-line
  file. Size-dependent, so it passes on small files. Write the file, then `head` it.
- **Readonly names fail loudly:** `UID`, `EUID`, `PPID`, plus `status` and `path` (tied to `$?` and
  `$PATH`), with an error that names the value rather than the variable.
- **Sourcing a bash script** leaves `${BASH_SOURCE[0]}` unset (`parameter not set` under `set -u`).
