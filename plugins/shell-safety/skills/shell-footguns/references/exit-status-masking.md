# Exit status and output that lie

Catalog entries moved out of `SKILL.md`. One defect runs through all of them — **a pipeline or
script reports its LAST stage's status, and an `echo` reports intent, not outcome** — in the spellings
that have actually bitten. A `[gate:<name>]` tag means `bash-footgun-gate.sh` enforces the entry.

**`set -o pipefail` turns `grep -q` into a false failure.** `[gate:pipefail-grep-q]` `grep -q` exits as soon as it
matches, so the upstream process gets SIGPIPE and a non-zero status — which `pipefail` then reports
as a failed pipeline. `cmd | grep -q X` therefore looks like "not found" *when it did find it*, and
it is **size-dependent**: if the producer finishes before grep exits there is no SIGPIPE, so it
passes at test size and fails on real data. This tripped a canary that was correctly guarding a
different probe. Use `[ "$(cmd | grep -c X)" -gt 0 ]`, or drop `pipefail` for that check.

**A script or pipeline reports its LAST command's status, which is rarely the one you care about —
and it lies in both directions.** **Deliberately NOT gated:** the offending command is usually
inside a script file (`bash watch.sh`), so the hook only sees the wrapper and has nothing to match
on. Both halves hit the same session, on watchers built specifically to report job outcomes:

- **False success.** `kubectl wait --for=condition=complete job/x --timeout=1800s | tail -2` —
  `wait` timed out and exited non-zero, `tail` succeeded, the task reported **exit 0** and the
  harness announced completion. The job was still running. Anything ending in `| tail`, `| head`,
  `| grep`, `| awk` discards the status of what you were actually testing.
- **False failure.** A watcher ended with `grep -c WARN` as its last line to report a warning count.
  Zero warnings → `grep` exits 1 → the whole watcher reported **failure** on a perfectly clean run.
- **False "it's gone".** The same watcher, rewritten, treated a single failed `kubectl get` as proof
  the Job had been deleted and exited saying so. The Job was healthy and still working. One transient
  API error is not evidence of absence: require N consecutive failures
  (`MISSES=$((MISSES+1)); [ "$MISSES" -ge 5 ] && …`) before concluding anything is missing.

All three landed in one session, on watchers whose whole purpose was to report an outcome truthfully.
The asymmetry matters: false success is the dangerous one, because it ends the wait and you act on a
result that has not happened. Fix by testing the command you mean directly (`if kubectl wait …; then`),
capturing status before the pipe (`st=${PIPESTATUS[0]}` in bash), or ending the script with an explicit
`exit 0` / a real terminal check rather than whatever the last filter returned. `grep -c` never belongs
last — wrap it: `n=$(… | grep -c X || true)`.

## Failures that arrive on the same stream as results

**`tty` reports failure on STDOUT, so `2>/dev/null` suppresses nothing.** `[gate:tty-in-command-substitution]`
When stdin is not a terminal, `tty` prints the literal `not a tty` to stdout *and* exits non-zero. So
`$(tty 2>/dev/null)` evaluates to that string, and `$(tty 2>/dev/null || echo /dev/tty1)` evaluates to
**two lines** — both halves run. A later `exec 3<"$val"` then fails on a path that does not exist and,
under `set -e`, kills the script at the point it looked like it was succeeding.

Hit in an installer prompting for input. The script runs as `curl … | bash`, so stdin
is *always* a pipe: the broken branch was the only branch, and every install would have died
at a prompt it never displayed. **It passed testing because the harness ran it under `script -qec`,
which allocates a pty and makes `tty` succeed** — the test exercised a shape production never uses.
Reproduce the real invocation, not a convenient one.

Use `tty -s` to *test* (exit code only, prints nothing); probe `/dev/tty`, then `/dev/console`, to
*find* a device.

**`tty` is not the only one, and the general form is worse: a wait loop that tests for OUTPUT treats
the error message as the output.** `psql` prints `ERROR: …` to stdout, so
`out=$(psql -tAc "…" 2>&1); [ -n "$out" ] && break` breaks on a *broken query* and hands you the
error text as though it were your result. **Deliberately NOT gated** — the loop lives in a script
file, which the hook never sees (`shell-gotchas` documents that hole), and `[ -n "$out" ]` is
correct in most other places.

Hit while waiting for a metrics exporter to write its first post-restart rows: the probe had an
aggregate inside `GROUP BY`, psql rejected it, the loop printed `post-restart buckets:` followed by
a syntax error, and **exited 0**. Same asymmetry the false-success bullets above name — the wait
ended and the next step was to believe it. The tell was that it returned instantly.

So make the presence test discriminate: `case "$out" in *ERROR*) …;; "") …;; *) …;; esac`, or test
the *value* (`[ "$out" -gt 0 ]`) rather than the fact that bytes arrived. The wider rule, since this
generalises past psql: before believing a command's output, ask whether its failures reach the same
stream as its results. `psql` and `tty` do so on their own (both verified, above); **anything you
ran with `2>&1` does so by construction** — which is the common case, because `2>&1` is exactly what
you reach for when capturing output for a check.

## The formatter family

**Piping a script through `tee` reports TEE's exit status, so a crash reads as a clean run.**
`[gate:formatter-masks-exit-status]` The same masking, but on a status CHECK rather than a log — and
it defeats the check completely rather than degrading it. `sed`, `awk`, `cut`, `tr`, `nl`, `column`
exit 0 on essentially any input — and so do `head` and `tail` — so `$?` after them describes the
formatter and never the command.

Hit twice in one evening, and the second time was on a script written specifically to avoid false
passes: `python3 relock-check.py | sed 's/^/  /'; echo "exit=$?"` printed `exit=0` for a script that
had just correctly exited 1. Earlier the same shape read a `rc=124` timeout as "writes are not
blocked" — the pipeline was there only to indent the output, which is exactly why it is invisible.
**A formatter added for readability silently converts a real check into an unconditional pass.**

**And one where the status is honoured correctly and the OUTPUT is the casualty, which is why none
of the rules above can see it: a command that PRINTS A USABLE ANSWER and STILL exits non-zero,
wrapped in `$(cmd || fallback)` — so BOTH branches run and you get them concatenated.**
`[gate:prints-and-fails-fallback]` `grep -c` prints `0` and exits 1 when nothing matches, so
`$(grep -c X f || echo 0)` is the two-LINE string `"0\n0"`. `systemctl is-enabled` prints `masked`
or `disabled` and exits non-zero for both, so `$(systemctl is-enabled u || printf absent)` is
`"maskedabsent"`. Both shipped from one collector in one session; the first put a raw newline
inside a hash-and-length-framed record, which then arrived *(lines − 1)* bytes short and was
rejected as transport corruption — a bug three hundred lines from where it appeared to be.

**It cannot reproduce on healthy input**, because the fallback only fires on the zero-match or
empty case, which is exactly the case a quick local test does not have. Mine ran on a workstation
with pending updates, so the branch never executed there and only a sweep across many hosts found it. Capture
first, default second: `n="$(cmd)" || n=""; [ -n "$n" ] || n=0`. A bare `grep -c` and
`$(cat f || echo missing)` — where the command prints nothing usable on failure — both pass.

**And the same masking with no `$?` anywhere: a formatter-terminated pipeline used as the CONDITION.**
`[gate:formatter-as-condition]` `if git merge <branch> | tail -3; then echo CLEAN; fi` prints CLEAN
for a merge that aborted, because the condition tests `tail`. This is worse received than the `$?`
version: there is no status read to look wrong, so the line reads like an ordinary "run it and show
me the last few lines". Caught on a dry-run merge whose own output, two lines above the verdict,
visibly showed the merge had not applied — the printed conclusion is what gets believed, not the
evidence beside it. `grep`/`test`/`cmp` are excluded, since their status is the point of running
them; a formatter inside `$(...)` is fine, because it feeds a real test.

**And the third member, which had no rule until it bit: the same pipeline followed by `&&` or `||`.**
`[gate:formatter-then-and]` `git push -q origin HEAD:main | tail -3 && echo "pushed to main"` printed
a confident *pushed to main* for a push git had **rejected** as non-fast-forward — git's own
`use 'git pull' before pushing again` hint was two lines above the claim, and the claim is what got
believed. The `&&` tests `tail`. The mirror is worse and quieter: `cmd | tail || echo FAILED` never
prints FAILED, so the failure branch you added specifically to catch this is itself dead.

**This one over-fired on everyday shell and was narrowed.** `| awk '$3 != "Running" &&
$3 != "Completed" {print $1}'` was blocked: the `&&` is the awk program's logical AND, not a shell
operator, and a compound awk condition after a pipe is a staple rather than an edge case. **The
obvious fix is wrong in the other direction** — blanking quoted spans before matching also silences
`sh -c "make build | tail -3 && echo ok"`, which is a REAL instance and was already being caught, in
both quoting styles. So quoting alone does not separate them. **What does is where the quote OPENS:**
the false positive's quote opens *after* the formatter name, so the operator is that formatter's
program text; the nested shell's quote opened before the pipe, so from the formatter's position the
operator is bare. The scan therefore starts at the formatter token and tracks quote state from
*there*, not from the start of the command. All four shapes are pinned as cases.

The two siblings do **not** share this exposure, and the reason is worth keeping: they only ask
whether a formatter is the pipeline's LAST stage, which is a question quoting cannot change. Only
this member scanned *forward past* the formatter's own arguments looking for something, which is what
put program text in range. (Probing the `if` sibling with the same awk program does block it — but
that is a TRUE positive: `if ... | awk '...'` tests awk's status, which is 0 whether or not anything
matched, and that is precisely the trap. The expectation was wrong, not the gate.)

Worth noting how the family grew. Each member was gated only after it fired: the `$?` read, then the
`if` condition, then the `&&`. All three are one defect — **a pipeline's status is its LAST stage's**
— and each time the fix was scoped to the syntax that had just been observed rather than to the
defect. If a fourth spelling shows up (a `case` on `$?`, a function return), it will be for the same
reason, and the cheaper move is to add it before it costs anything.

**The fourth spelling did show up, and the prediction above guessed the wrong shape — it is not a
pipeline at all.**

```bash
git push -q origin HEAD:main
echo "PUSHED"                     # prints regardless; the push was rejected
```

No pipe, no formatter, no `$?`, so not one of the three rules above can see it. **Ungated:** the
rejection is printed directly above the claim, so the output shows the failure; what went wrong is
that the claim got read instead of the evidence. **An `echo` is a claim about what you INTENDED;
the only evidence of what happened is what the command RETURNED.** Print the return value, guard
with `&&`, or `set -e`.

`[gate:preprinted-empty-verdict]` **The sibling where the command is read-only and the echo asserts
nothing about success.** A probe, and a later statement in the *same command string*
declaring what an empty result would MEAN:

```bash
grep -rinE "api.example.com" src
echo "(empty = no API calls)"   # written before any output existed
```

**Same-command-string is the proof, not a heuristic.** The gloss was composed before the data, so it
can only encode the guess; and when the probe returns what was predicted, nothing downstream can tell
the label from a measurement. That is worse than an unconditional "PUSHED", which sits under git's
own rejection and is contradicted on screen: a pre-printed `(empty = X)` beside a genuinely empty
result looks *corroborated*. Measured in one session: four, the last three *after*
the lesson had been written into `no-fabricated-certainty`; twice the probe returned data and the
label was flatly false. Run the probe, read the output, then say what it showed; for a control,
assert it (`test -s out || echo "PROBE BROKEN"`).

`[gate:commit-then-push-unguarded]` **The gated shape: `git commit` and then a `git push` that runs
whether or not the commit worked.** That is the incident at the end of this file: the commit failed
and the push shipped nineteen untested commits that were already there. Both must be in command position, meaning
the start of a statement, with optional `VAR=x` prefixes and git global options (`-C`, `-c`,
`--git-dir=`, `--work-tree=`). A word in an `echo`, a comment, a heredoc body or
`$(git commit-tree …)` does not count. It is quiet when the push waits on the commit: an unbroken
`git commit … && … && git push` chain, `git commit … || exit`, the commit as an `if` condition,
`$?` read between the two, or `set -e`/`set -o errexit` beforehand. `case … esac` branches are
alternatives, not a sequence. Fix: `git commit … && git push`.

The rule has been narrowed twice, each time after replaying it over ~2,165 real commands that
contain a mutator. Blocking any mutator followed by anything hit 723, nearly all
`git commit …; git log -1`, whose output already shows the failure. Blocking a mutator followed by
another mutator hit 427: 402 were commit→push and the rest were idioms such as
`kubectl create ns x 2>/dev/null; kubectl apply` and `git tag -l; git push --tags`. Commit→push
alone hits 469. That is more than 402 because `git commit … && git log; git push` now counts too:
the `&&` chain breaks before the push.

`head`/`tail` were added to the rule after a **second** harness hit it independently: a lint gate
read `tail`'s exit status and printed "lint: clean" while ruff printed `7 fixable` two lines above.
Two harnesses, both authored by someone who knew about this trap, is the argument for the gate.

Not gated for `grep`, `test` or `cmp`: their exit status is the point of running them, so reading
`$?` after those is usually correct. The discriminator is whether the last stage can fail on the
content it is given.

Redirect and read the file (`cmd > out 2>&1; rc=$?`), use `${PIPESTATUS[0]}`, or set `pipefail`.

`[gate:zsh-pipestatus-in-bash]` **`${pipestatus[1]}` is zsh's array and the Bash tool's shell is now
bash, where it expands to the empty string.** Bash's is `${PIPESTATUS[0]}` — uppercase, 0-indexed.
While the shell was zsh this ran the other way: `echo "rc=${PIPESTATUS[0]}"` printed `rc=`, and a
rule blocked it. The switch inverted it, and months of `echo "push rc=${pipestatus[1]}"` habit now
print `rc=`. `zsh -c` and `ssh` (remote zsh) carry zsh semantics and are allowed. The rule matches
the **expansion**, not the word, so `grep -n 'pipestatus' <file>` is not blocked.

**The advice strings had to flip too.** The three formatter rules above recommend a status read in
their advice and treat its presence as an exemption from firing. In the zsh era they once
recommended `${PIPESTATUS[0]}` — the one construct that could not work there — so writing it bought
silence instead of a status. The same edit that changed the shell had to change the advice and the
exemption, or the gate would have sent you to `${pipestatus[1]}` and then fallen silent for it.

The general lesson, since it generalises past this rule: **a gate's advice string is part of the
gate.** Nothing tests it, it is read at exactly the moment someone is deciding what to do, and it is
the one part of a hook that can actively cause the trap it exists to prevent.

`[gate:tee-masks-exit-status]` A pipeline exits with its LAST command's status and `tee` essentially
always succeeds.

Hit on a 40-chunk discovery sweep over a document corpus. One model response contained an invalid JSON
escape, `json.loads` raised, `ThreadPoolExecutor.map` propagated it out of the iteration and abandoned
the 8 remaining chunks — and `| tee` turned the whole thing into `[exited with code 0]`. The harness
reported success.

**The compounding is what made it dangerous.** 32 chunk files existed, and their per-chunk yield was
consistent (10-18 themes each), so every surface check looked healthy. 20% of the corpus was never
read; because the chunks were contiguous by date, the missing fifth was the most recent slice;
and the taxonomy reduced from it was entirely plausible. Nothing in any artifact said "partial".

**Redirect and read the file** — `cmd > log 2>&1` — or add `set -o pipefail` if you genuinely need
the tee. And for any partitioned work, see the coverage-assertion note in `fanout-craft`: count the
items covered against the source population, because per-item success and consistent yield are both
healthy-looking while a fifth of the work is missing.

## `git commit …; git push` ships what was ALREADY committed when the commit fails

A real case: `git commit --only <new untracked files> -m …; …; git push origin HEAD:main`.
The commit failed (`--only` pathspecs did not match untracked files), the `;` ran the push anyway, and it
shipped nineteen earlier local commits that were each tested on their branches but never as a combination,
mid-way through an asset swap that had to land with them. Nothing in the output looked like a failure
except two `pathspec … did not match` lines above the push.

**Chain the push to the commit with `&&`, never `;`** — or push in a separate call after reading the
commit's result. A push in the same command as a commit should only ever run if the commit succeeded.
Gated by `commit-then-push-unguarded` (above).
