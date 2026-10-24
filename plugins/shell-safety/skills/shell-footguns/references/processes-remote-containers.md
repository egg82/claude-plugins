# Processes, remote shells, containers, secrets

Catalog entries moved out of `SKILL.md`. A `[gate:<name>]` tag means `bash-footgun-gate.sh` enforces
the entry.

## Process matching

**`pgrep -f` / `pkill -f` match the Bash tool's OWN wrapper.** `[gate:pgrep-f-self-match]` The harness runs each command as a long
`bash -c 'source …snapshot… && eval …'` (zsh before the shell switch), so the pattern you search for sits in the searching process's
own argv.

Two observed failures, both bad:

- `pgrep -af monitor.sh` reported a background script **ALIVE** when it was already dead — it matched
  the wrapper.
- `pkill -f monitor.sh` **killed the running command itself** (exit 144), so the rest of that chained
  command — a patch plus a restart — silently never ran.
- It happened a **third** time with the rule already in place: the kill sat inside a `cat > f <<'EOF'`
  body, and the gate evaluated a heredoc-**stripped** copy, so the body was discarded before the rule
  saw it — while the wrapper's argv still held every line. The general lesson outlasts the fix:
  **a check that strips heredocs is blind to the shape nearly every script here is written in.**
- Making it read heredocs then blocked the edit that was *documenting* it, because the ban and the
  explanation of the ban are the same string. Both this rule and the one below therefore blank
  quoted/inline-code spans and require **command position** — real code starts a line (or follows
  `;` `&` `|` `do`); a documented or test-case copy sits inside quotes.

**`pgrep -x` / `pkill -x` is the one legitimate escape**, and it is the gate's must-allow case. `-x`
matches the process's exact `comm` name rather than its full argv, so the wrapper — whose `comm` is
`bash` — cannot match. It only helps when you know the exact executable name, which is why it is an
escape rather than a replacement for the guidance below.

Match the real invocation instead:

```bash
ps -eo pid,args | grep -E 'bash monitor\.sh' | grep -v grep
```

To kill, resolve PIDs that way first and `kill "$pid"`. Check `sid`/`ppid` to tell a background script
apart from its own command-substitution forks.

## Killing a parallel job

**Kill the parent before the children, or you accomplish nothing.** **Deliberately NOT gated** — the
command string is a perfectly ordinary `kill`, and only the process tree says whether it is futile.
Killing the workers of a `xargs -P` / `parallel` / `make -j` run while the dispatcher is still alive
makes it immediately spawn replacements, so the count never drops and the cleanup reads as a failure
to kill anything. Resolve and kill the dispatcher first, then sweep the remaining children:

```bash
ps -eo pid,ppid,args | grep -E 'xargs -P|parallel' | grep -v grep      # find the dispatcher
kill -9 <dispatcher-pid>
ps -eo pid,args | grep -E '<the real worker invocation>' | grep -v grep | awk '{print $1}' | xargs -r kill -9
```

The tell that you got the order wrong: you kill N processes, wait, and count N again.

## Killing EVERY container on a shared box [gate:kill-every-container]

`podman ps -q | xargs podman kill` or `podman rm -f $(podman ps -aq)` takes out every container on the machine,
other sessions' and the operator's included, and reports nothing unusual. A bug-hunt finder tidied up after
itself this way once, and a container from outside the hunt was gone afterwards. Kill your own by name, or filter the
ps (`podman ps -q --filter name=<yours> | xargs podman kill`, or a `label=` you set at `run`). A filtered ps is
allowed by the gate.

**`podman volume prune` is box-wide.** `[gate:volume-prune-unfiltered]` It (and `system prune
--volumes`) deletes EVERY volume no container references — the operator's and other sessions' kept named
volumes too, not just the one you orphaned. An agent ran `podman rm -f -v <its pg>;
podman volume prune -f >/dev/null` to tidy up after a test database and could not say afterwards what
it had deleted. `rm -v` already removes that container's anonymous volumes; remove anything else by
name (`podman volume rm <name>`), or prune with `--filter label=<yours>`.

## stdin never attached: `exec` without `-i` [gate:exec-stdin-without-i]

`kubectl exec` / `podman exec` / `docker exec` attach stdin only with `-i`. Fed a heredoc, a `<`
redirect or a pipe without it, the command inside reads nothing, prints nothing and exits 0 — a psql
heredoc of EXPLAINs "completed with no output" and read as an empty result. Always `exec -i` when
anything is on stdin.

## stdin eaten by the wrong process

**`sudo` reads STDIN, so a script piped into a shell is EATEN from the first `sudo` onward.**
**Deliberately NOT gated** — `bash -s` with redirected stdin is overwhelmingly legitimate, and whether
the piped script contains `sudo` is not in the command string. `ssh host 'bash -s' < probe.sh` runs
normally until the first `sudo`, which consumes the *remainder of the script* as its own stdin.
Everything after that line silently never executes, and the exit status is 0. The output simply stops,
which reads as "the command returned nothing" rather than "most of my script was swallowed" — a probe
whose first section printed and whose next three did not, diagnosed as a broken host before it was
diagnosed as a broken probe. Redirect per call (`sudo -n cmd </dev/null`), or better, don't put the
script on stdin at all: base64 it into an *argument*, write it out remotely, then run it — immune by
construction.

`sudo` is only the commonest reader: **any command that falls back to stdin when it is not a terminal**
does the same. `ausearch` is the sharp one — with no `-if` and a non-tty stdin it reads *stdin* as its
log, so it eats the script and also returns no records, which looks like "no AVC denials" (measured: probe runs
truncated at the ausearch line until `--input-logs … </dev/null` fixed it
and the denials appeared). `mysql`, `psql`, `ssh` and `read` behave the same way.

**`sudo` inside a heredoc fed to `bash -s` swallows the rest of your script.** `[gate:sudo-drains-heredoc-stdin]`
`sudo` reads from stdin, and with `ssh host 'bash -s' <<EOS` the script *is* stdin — so the first
`sudo` consumes every line after it. Nothing errors: the lines before it ran, sudo ran, exit status
is 0, and the output simply stops early. That reads as "it printed less than I expected", not as
"half my script never executed". Hit twice in one session by someone who already knew the rule,
because it lived only in prose (a skill's notes) — found there by reading, never by
being prevented. Fix: write the script to a file, `scp` it, run `ssh host 'bash /tmp/x.sh'`; or give
every `sudo` a `</dev/null`.

**A VALUE piped into `ssh host bash -s` is executed as the remote script, and echoed to stderr.**
`[gate:ssh-bash-s-stdin]` Same `-s` as the rule above, arrived at from the other end: `-s` means
*read the script from stdin*, so a value piped in is not input to the remote command — it **is** the
command. The remote shell answers `<value>: command not found` on stderr, which lands in whatever
wrapped the call (a results file, a log, the model's context), while none of the intended commands
run. So it presents as an ordinary failure to debug rather than as a disclosure, and the value has
already travelled. Where the value is a credential this is a leak, not a bug — see
`print-names-not-values`.

Send the command as the ssh **argv** string, and arrange for the only process reading stdin to be the
one that should: `sudo -S -p ''` consumes exactly one line, prompts silently and echoes nothing.

```sh
printf '%s\n' "$VAL" | ssh host 'sudo -S -p "" systemctl restart foo'
```

Run any host or identity guard **before** the stdin-reading process, so an abort never leaves a value
sitting in a pipe aimed at something else. Sending a real *script* is not the trap and stays allowed:
a heredoc, `cat script.sh | ssh host bash -s`, or `ssh host bash -s < script.sh` — which is also what
keeps this rule clear of the must-allow cases belonging to the `sudo` rule above.

**A `while read` loop whose body calls `ssh`, `az` or `kubectl` processes only the FIRST line.**
`[gate:stdin-eater-in-read-loop]` The same defect as the one above, one layer out: the loop's input
*is* stdin, so any command in the body that reads stdin drains the rest of it. The loop then exits 0
having run a single iteration. Caught with `ssh` inside a `while read` loop over a host list — 12 hosts queued,
1 checked, exit 0, nothing warned. The danger is in how it renders: **"one row
matched" is a plausible answer**, so it reads as a finding rather than as a broken loop, and a
plausible number is the one nobody re-reads. Fix: `< /dev/null` on the inner command — harmless even
where it was not needed, which is why requiring it costs nothing.

This is the one rule that inspects heredoc *bodies* (the gate otherwise strips them, so that writing
a file whose content mentions a pattern is never blocked). It is only safe because it requires a
top-level, properly-terminated heredoc whose opener feeds a stdin-reading shell. Both narrowings
were added *after* the rule fired on commands that merely mentioned the pattern — once on the edit
adding its own test cases, once on a `printf` containing an unterminated `<<EOS`.

## Removing containers

**`podman rm -f` left every throwaway Postgres's data volume behind, and filled the disk.**
`[gate:container-rm-keeps-volume]` postgres:17-alpine declares its data dir a VOLUME, so each container
gets an anonymous volume. Starting with `--rm` does not save you: `--rm` cleans up on a normal exit,
and a forced `podman rm -f` of the running container skips it. One day of fresh-database test runs
left ~1,000 dangling volumes (~98 GB) until the home disk hit 100%. Remove with `-v` (anonymous volumes
only; named ones are kept), or better, give the container no volume at all: `--tmpfs` over its data
dir.

**A debug pod cloned from a Deployment's pod spec runs its init containers too.** Copying
`spec.template.spec` to replay an old image also copied a `migrate` init
container, which ran that image's migrations against the live database before the app started.
It was harmless only because the old image carried the same migration set. Strip `initContainers`
(and the probes, and the labels a Service selects on) before applying, and read the result's
`initContainers` field back before `kubectl apply`.

## Moving data into containers

**Piping more than a few KB into `kubectl exec -i` silently produced an EMPTY file.** `[gate:kubectl-exec-stdin]` Writing ~93KB via
`kubectl exec -i <pod> -- sh -c 'cat > f'` created a **0-byte** file and reported success — twice, with
both `< file` and a `cat |` pipe — while a one-line probe through the identical command worked fine.
That is what makes it dangerous: it behaves correctly at the size you would test it at.

Not root-caused — it may be kubectl, the harness's stdin handling, or busybox `cat` — so treat it as
observed behaviour rather than a documented limit. **Use `kubectl cp` for anything beyond a couple of
lines, and re-read what landed (`wc -c`) rather than trusting the exit status.** Appending to a log
this way is the sharp case: a silently truncated append looks identical to a successful one.
The gate fires only when the remote command writes stdin to a file: `cat >`/`>>`, `tee`, `dd of=`,
or any `>`/`>>` inside the quoted remote script (`sh -c 'base64 -d >/tmp/x'`). It is allowed when
stdin goes to a program (`kubectl exec -i pod -- psql <<EOF`). An unquoted `>` after the remote
command is the local shell's redirect, not a write inside the pod.

**`echo "$var" | cmd` in zsh (an `ssh host '...'` body) rewrites the data.** Ungated: most `echo "$x"` is harmless, so a rule would
cry wolf. zsh's `echo` interprets backslash escapes, so a captured `kubectl kustomize` render containing a
literal `\n` reached `kubectl apply -f -` as broken YAML ("could not find expected :"), and all seven
documents were clean from a file. Write the data to a file and pass the path, or use `printf '%s' "$var"`.
A parse error on piped data is a claim about the pipe, not the data.

**A podman bind mount with `:Z` relabels the HOST directory, privately, and it persists.** `:Z` gives
the directory an SELinux label that only that one container may use, so any other container or
service reading the same source directory is locked out once SELinux enforces — and nothing says so
at mount time. On a permissive host it does nothing visible, which is how a README instruction to
mount a shared asset folder with `:ro,Z` survived for weeks. For a directory anything else reads, use
lowercase `:z` (shared label), `--security-opt label=disable`, or mount a copy; keep `:Z` for a
throwaway directory only that container uses (`$(mktemp -d)`, a scratch copy).

**A long-running command under `kubectl exec` dies with its stream.** **Deliberately NOT gated** —
no command string separates a two-second `cp` from a forty-minute one, so a rule here would fire on
every exec. An API blip (`error reading from error stream: … i/o timeout`) drops the exec session,
and the remote process loses its parent: sometimes killed outright, sometimes orphaned and left to
stall part-way. A 74GB `cp` stopped dead at 44.5GB this way.

**The exit code describes the stream, not the work.** `kubectl` returns 1 on the timeout whether the
command died, finished, or is still running — so never read that 1 as "the operation failed" and act
on it. Two probes tell you which actually happened, and only one of them works: **an output file
that is still growing across two reads proves the process is alive**, while `ps` inside the container
reported nothing for a `cp` that was demonstrably running. Trust the growing file.

Launch anything slow detached and let it own its own status:

```sh
kubectl exec -n ns pod -- sh -c 'nohup /tmp/job.sh > /tmp/job.log 2>&1 < /dev/null &'
```

then poll `/tmp/job.log` for a terminal line the script writes itself, rather than inferring state
from `stat`/`ls` output. **Have the job write to `dst.partial` and rename only after verifying byte
size** — an interrupted copy under the final name is indistinguishable from a finished one, and the
rename is what makes "present" mean "complete".

**Detaching without arming a waiter is how a session silently ends mid-job.** **Deliberately NOT
gated at PreToolUse** — `nohup kubectl port-forward &` is correct and you never want waking for it, so
no command string separates the two; the distinction is intent, and intent is only legible at the end,
which is where `detached-work-gate.sh` (a Stop hook) picks it up instead. The poll above is not
optional decoration: `nohup` returns instantly, so unless *the harness* is tracking something, nothing
will ever wake you and the session just stops with the work half-done. Measured across session transcripts: of the sessions that detached with `nohup`/`setsid`, over half armed neither
a `run_in_background` shell nor a `Monitor`, and most of those were real long-running work rather than
tunnels.

So detaching is two steps, always: launch it detached, **then** arm a harness-tracked waiter —
`run_in_background` on a polling loop, or `Monitor` — in the same turn. Note the waiter is a
*separate* call from the launch: the `nohup` exec itself should return immediately and must not be the
thing you background.

## Secrets and gated file writes

**curl writes basic-auth credentials into the URLs it prints.** `[gate:curl-writeout-prints-credentials]`
With `-u user:pass` (or `--user`, or `user:pass@` in the URL), `-w '%{redirect_url}'`, `%{url_effective}`,
`%{url}` and `%{referer}` print the URL with the credentials as userinfo. A registry API call with an admin credential answered 201 with a
relative Location, and `-w "%{http_code} %{redirect_url}"` printed the password. Print
`%{http_code}`; for a Location, read the headers with `-D -`, which curl does not rewrite.

**Vault prints secret VALUES to stdout, and stdout is a permanent transcript.** `[gate:vault-secret-to-stdout]`
`vault token lookup` prints the token id in full in *every* output format it has, `-format=json`
included — there is no flag that omits it, so the command that feels like "check my auth" is
unconditionally a credential leak. Bare `vault kv get <path>` and `vault read <path>` are worse:
they dump every field the path holds, so whatever is stored there gets printed, including the
secret-ish name nobody thought to guard.

Both fired in one session. The parent ran `vault token lookup` to confirm reach and put
a long-lived admin token into scrollback. Forty minutes later a **subagent — briefed in writing
to use `-field=` and never print a value** — ran a bare `vault kv get <app-secrets>` and
dumped every live credential at that path into its own transcript, forcing a real rotation. The instruction was
resident, specific, and being followed correctly everywhere else in the same run. **That is the
argument for the gate: prose had already failed at the exact moment it was being obeyed.**

Use `-field=<name>` to name the one field you decided to see, capture it with
`X="$(vault kv get -field=FOO secret/p)"`, or redirect to a file.

**A pipe is not an escape, and the first version of this rule got that wrong.** It deferred on any
`|`, reasoning that a downstream consumer cannot be judged from the command string. That reasoning
is sound for `kubectl get secret`, where the deny-worthy step is a decoder — which is why
`print-names-not-values` leaves that one ungated. It fails here, because `vault kv get` has already
rendered every value as plaintext before anything downstream runs. The pipe target decides only how
much of the dump you see, not whether it is a dump: `| head`, `| tail`, `| cat`, `| less` and
`| grep <key>` all print secrets.

**Caught by testing the rule against the command string of the very leak that motivated it — which
it would have allowed:** `vault kv get <app-secrets> 2>&1 | head -30`, whose
keys all sat inside the 30-line cut. So: **write the gate from the literal command, not from the
incident's summary**, and make that exact string a must-block case. A summary says "a secret was
printed"; only the command string says which escape hatch let it happen.

**A `talosctl` dry-run diff prints the CA keys beside your hunk.** `[gate:talosctl-dryrun-context-secrets]`
Its unchanged context lines are machine config, which holds the cluster CAs; an etcd patch put
`cluster.etcd.ca.key` on a terminal, and `| grep -v WARNING` keeps it. Filter to changed lines
(`| grep -E '^[+-][^+-]'`) or redirect to a file. `upgrade-k8s`/`rotate-ca` dry runs are ungated.

**Writing a memory or skill file from Bash silently skips the gate that checks it.**
`[gate:memory-write-via-bash]` `memory-write-gate.sh` is PreToolUse on `Write|Edit|MultiEdit|
NotebookEdit` only, so `cat > mem.md`, `sed -i`, or a `python3 - <<'PY'` heredoc calling
`write_text()` is never checked. Its header calls that hole deliberate and rests it partly on
Bash-authored memories being rare — a premise measured true here once and **falsified later,
when one session wrote seven that way** because the auto-mode harness instruction prefers Bash over
the Write/Edit tools for file changes. Nothing errors and the file looks right, which is why it ran
seven times. The gate rule is narrow on purpose — only a write VERB aimed at those paths — because
reads and bulk `cp`/`mv` are legitimate and a gate with false positives gets switched off. It is
also the one rule that matches `raw_cmd`: `strip_heredocs` would otherwise drop the path and the
`write_text()` together, which is exactly where all seven lived.

**KNOWN FALSE POSITIVE, diagnosed and deliberately NOT patched.** A command carrying a
`~/.claude/skills/...` path as a **`cp` SOURCE**, alongside a `python3 - <<PY` writing to a scratch
path, is blocked — the write never touched a skill file. The redirect, `tee` and `sed -i` branches
each prove the memory path is the write's *target*; the Python branch cannot, so it fires on the
**conjunction** of "a memory path appears" and "a Python write appears".

**Why not narrow it.** Any adjacency test — path near the `write_text()` — misses the dominant real
shape, where the path is built into a variable well away from the call, and that is exactly the case
the rule exists for. A false negative here loses an ungated memory write; the false positive costs
one split command. Same trade the `detached-work-gate` specimen case records: keep the real catch,
accept the specimen.

**What DID change is the message**, because the old one asserted "a Python write targeting a file
under `.claude/memory/`" — a claim it had not established, and which was simply false in the case
above. It now says it cannot prove the two refer to one file, and names both exits. A gate may
over-trigger; it may not lie about why. **To proceed: split the `cp` and the `python3` into two Bash
calls** — neither then carries the pair. All three shapes (the conjunction, and each half alone) are
pinned as cases so the verdict is executable rather than only written down.
