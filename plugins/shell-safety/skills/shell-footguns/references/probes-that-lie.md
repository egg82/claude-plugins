# Probes that lie

Catalog entries moved out of `SKILL.md`: commands that return a plausible, wrong answer. A
`[gate:<name>]` tag means `bash-footgun-gate.sh` enforces the entry; the rest are prose-only, usually
because no command string can tell the wrong use from the right one.

**`node --check file.js` passes an ES module with a real SyntaxError.** On a `.js` file that uses
`import`, it exits 0 even with a duplicate `const` (node 24, measured); the same source fed
as `node --input-type=module --check < file.js` fails correctly. A night of "syntax ok" reports on a
no-build client rested on the first form, and one broken file was caught only by a render. For ES
modules, always pipe the source in module mode, and give the check a control: append a duplicate
`const` to a copy and watch it fail.

**`2>/dev/null` on a probe converts a loud failure into a false zero, and you are the one who adds
it.** This is the most self-inflicted entry in the file. Suppressing stderr is a tidiness reflex —
you expect permission noise on a `find` across a tree, so you silence it — and it removes the single
signal that distinguishes "the answer is none" from "the command refused to run". Measured
Measured: two `find … -newermt '-3 hours' 2>/dev/null` calls, one piped to `wc -l`, printed `0` and
nothing else. **The conclusion drawn from that zero was the opposite of the truth** (32 files had
changed), and it was about to be reported as a finding.

**`find` on some machines is `bfs`, not GNU findutils, and it rejects relative timestamps.**
`-newermt '-3 hours'` and `-newermt '3 hours ago'` both error with *"Invalid timestamp"* and exit 1;
`bfs` accepts ISO 8601 only (`2026-01-02T22:40:36`). GNU's relative forms are muscle memory, so this
will be typed again. Either compute the timestamp first, or skip `find` for mtime questions
entirely — `os.walk` plus `os.path.getmtime` in a Python heredoc is fewer moving parts and its
failures raise.

Two rules, and the first is the general one:

- **Never silence stderr on a command whose output you are about to draw a conclusion from.** Let it
  be noisy. If the noise is genuinely unbearable, send it somewhere you then read
  (`2>/tmp/probe.err; … ; cat /tmp/probe.err`), never to `/dev/null`.
- **Check `$?`, and remember a pipeline reports the LAST stage.** `find … | wc -l` exits 0 because
  `wc` succeeded. This compounds with the gated pipeline-status trap elsewhere in this catalog: here the
  formatter is not just hiding the status, it is *manufacturing a plausible answer* from nothing.

**Deliberately NOT gated.** `2>/dev/null` is correct constantly — probing for a file that may not
exist, suppressing a tool's chatter on a path you do not control — so a hook firing on it would be
mostly false positives and would be switched off. The discriminator is not the redirect, it is
whether a conclusion rests on the output, and no command string knows that. What makes this
survivable instead is the control: [[verify-dont-anchor]]'s rule that a probe must first be shown
able to return non-zero. The corrected probe above found all three of its own known-present files
before its count was believed, which is the only reason the error was caught at all.

**`sed`'s greedy `.*` on single-line input returns the LAST match.** Ungated: a leading `.*` is usually
right. `bootc status --json` repeats `"image":` per deployment; identical on a never-updated host, the
rollback's image everywhere else. Anchor to the enclosing key
(`sed -n 's/.*"spec"://p' | grep -o '"image":"[^"]*"' | head -1`) and build a control where the values
DIFFER. Applies to any format naming the same thing once per generation.

**Prefer a loop of literal matches to one clever pattern.** **Deliberately NOT gated** — a regex is
not distinguishable from a correct one by inspection, so no command string can decide this. For any
"does every X appear in Y" or "what is still referenced" question, iterate the real files and test
each one literally (`grep -Fq "$name"`) instead of building a single generalized pattern. A pattern is
a *proxy* for the content, and a wrong proxy answers confidently: a character class missing `_`
reported an indexed file as missing, and a diff filter stripped the very lines that proved a change
was safe. A `count()` helper missing `re.M` made every `^`-anchored check return zero, which read as a
clean result. The loop has no regex to get wrong.

**`grep` parses a pattern beginning with `-` as an OPTION** —
which turns the loop idiom recommended immediately above into a probe that lies.
**Deliberately NOT gated** — the pattern arrives in a variable, so the command string cannot say
whether it may start with a dash, and firing on every `grep "$var"` would be almost entirely false
positives. `grep -Fq "$want"` over a list of wanted YAML lines reported 6 of 24 as MISSING; every one
of those 6 began `- ` because they were list items, and ugrep answered
`invalid option - 198.51.100.0/24` on stderr while the loop recorded a miss. The tell is that the
failures correlate with the *shape* of the pattern rather than with the file, and that stderr carries
`invalid option` — but a loop that only reports ok/MISS hides it, and the plausible-looking count of
misses reads as a finding. Always `grep -Fq -e "$want"` (or `-- "$want"`) when the pattern is a
variable.

Measured both sides, because the entry below this one notes that inline `grep` is a shell function
rather than `/usr/bin/grep` and the two do diverge: they do **not** diverge here. Inline (ugrep 7.8.4)
says `ugrep: invalid option - 198.51.100.0/24`; inside `bash script.sh` GNU grep says
`grep: invalid option -- ' '`. Different text, **same exit 2**, so `-e` is the habit everywhere and
writing the loop to a script file does not save you.

Corollary, and the reason this sits here rather than in a style guide: **when a probe contradicts
something you read with your own eyes, trust the reading and fix the probe.** Every probe failure seen
in this setup has been the probe's own bug.

**`grep` in the interactive shell is a shell FUNCTION from the harness snapshot, not `/usr/bin/grep`.** `[gate:grep-pcre-inline]`
A regex validated inline can behave differently inside `bash script.sh`. This cost a whole verification
pass: `(?i)` appeared to work inline but matches **nothing** under `grep -E` in a script — GNU grep has
no PCRE inline flags — so every `(?i)`-prefixed pattern was silently dead. A dead pattern is
indistinguishable from a clean result. Use `grep -i`, and **validate a probe in the context that will
actually run it.**

**A glob is expanded by the shell that TYPES it, not the one that gains privilege.**
**Deliberately NOT gated** — the string cannot say whether the path is readable to the caller, and
`sudo ls /var/log/*.log` is both fine and identical in shape. `sudo -n stat /var/lib/app/keys/*.pem`
expands the glob as *you*: against a `0700` directory owned by a service account it matches nothing, so either the
literal pattern is passed through (`No such file or directory`, at least visible) or — inside a
`for` loop guarded by `[ -e "$f" ]` — it matches nothing and prints **nothing, exit 0**. That is a
false zero about files you cannot read and it is indistinguishable from "those files don't exist."
Hit twice in one session, the second time after already knowing about the first. Put the whole loop inside the privileged shell (`sudo -n bash -c '...'`) so the glob expands
with the privilege that can read it.

**For anything with `Restart=`, EXISTENCE IS NOT HEALTH — measure duration.**
**Deliberately NOT gated** — `pgrep foo` is the correct probe for most things; only the restart
policy of the target makes it wrong, and that is not in the command string. A service that
crash-loops always has a live process at *some* instant, so a poller asking "is it running?" gets
`yes` on a machine that is comprehensively broken. Cost a false all-clear on a build runner:
a queue worker was dying and being restarted about once a second, a poll landed between two
deaths, and the verdict was reported as "fixed". The exit status, the process
list and the pid were all real — the *question* was wrong. Ask how long it has been up
(`ps -o etimes= -p <pid>`, or `systemctl show -p ActiveEnterTimestamp`) and require a threshold
comfortably longer than the restart interval; better, read the unit's own verdict
(`systemctl is-failed`, or `Result=` in the journal), which knows about the loop when a process
list cannot. Same shape as a healthy-looking count: a positive result gets far less scrutiny than
a zero, and this one is a positive.

**`~/.local/bin` tooling is invisible to non-interactive shells.** A `BatchMode` SSH command, a cron
job, or a spawned MCP server never reads the login profile that puts `~/.local/bin` on `PATH`, so a
CLI you use constantly at an interactive prompt reports "not installed" there. `command -v <tool>`
over `ssh -o BatchMode=yes` reported a correctly-installed tool as missing within a minute of the
memory saying it was there; on another machine the same shape nearly became a documented platform
limitation about `claude` not being installed, on a host where it sat in `~/.local/bin`.

**The ssh-wrapped form IS gated** `[gate:ssh-command-v-path]`, because over ssh the command string
*itself* proves the shell is non-interactive — that is the fact a bare `command -v` cannot supply.
A login shell (`ssh host 'bash -lc "command -v foo"'`) does read the profile, and an explicit
`source`/`.` of one does too, so both are excluded from the rule.

The `which` arm needs command position, because English "which" after a real ssh fired the rule. Known
gap: unquoted `ssh host which glab` passes.

**The BARE form stays deliberately NOT gated** — `command -v <tool>` is correct in an interactive
shell and only lies about one PATH entry, which the command string does not carry. This paragraph
used to say the trap as a whole was ungated; half of it now is, and that half is the half that bites.

**It over-fired on its own documentation within minutes of arriving, and was narrowed.**
A command that merely *mentioned* the rule — `ssh` inside an echo label, `command -v` inside a grep
pattern, no ssh invocation anywhere — was blocked. That is the shape `pgrep-f-self-match` already
solved on this side: a rule worth enforcing gets quoted in prose, so the ban and the explanation of
the ban are the same string, and grepping for a trap is not committing one. **Blanking quoted spans
is the wrong fix here**, because the real trap puts `command -v` in quotes too, as ssh's remote-command
argument. The asymmetry that does separate them: a real call has **`ssh` itself in command position,
bare and outside quotes**; a mention has it inside them. So the `ssh` test runs against the
quote-blanked string and the probe test against the raw one. Both directions are pinned as cases.

This is directly relevant to memory `check:` probes — write them against an explicit path
(`ls ~/.local/bin/<tool>`), never a bare name. **And when a probe fails, suspect the probe before the
claim.**

**A canary must put one token per line.** Several tokens on one line proves nothing: grep reports the
whole matching line, so one working pattern masks every broken pattern beside it.

**Before believing a zero, make the probe prove it can return non-zero.** Pair every "does X appear"
check with a control: a string you know is present (must return non-zero) and ideally one you know is
absent (must return zero). See [[verify-dont-anchor]].

**A JSON response can be well-formed, correctly keyed, and still carry EMPTY payload fields — so
searching it answers a question you did not ask.** **Deliberately NOT gated** — no command string
knows an endpoint's response shape, and searching a fetched document is the ordinary case. An API
returned 37KB and 106 correctly-named section nodes whose every `Content` field was `""`, because
that endpoint serves a table-of-contents chunk rather than text. A search across it reported
`<term>: 0`, which reads as *"the document says nothing about that"* when it actually meant *"I
searched 106 empty strings."* Nothing was missing, misspelled, or erroring. **Assert the payload is
non-empty before searching it** (`sum(len(d['Content'] or '') for d in docs) > 0`) and confirm one
known-present term — the same control the zero rule above asks for, aimed at the document instead of
the pattern.

**A fixed `-o` path reused across loop iterations leaves you inspecting the LAST file, not the one you
meant.** **Deliberately NOT gated** — one scratch path per loop is correct whenever the body consumes
the file before the next iteration, which is the common shape; the defect exists only when the
inspection happens *after* the loop, usually in a later tool call, and no single command string
carries that. Fetching four scripts in turn to `/tmp/app.js` and then grepping `/tmp/app.js` returned
**zero** hits for a token already seen in the intended bundle — the file held an unrelated library by
then, and a stale artifact reads exactly like a real absence. Sharper when the clobbered file still
**parses**: two different API endpoints written to the same `toc.json` left the smaller response in
place, and the analysis reported `total nodes: 1` — a plausible small number rather than an empty
result, so nothing looked broken enough to question. Name the output per iteration
(`-o "/tmp/dl-$i.js"`), or run the check inside the loop body.

Gating this was reconsidered after that hit and **rejected on measurement**: the session that hit it
also used a fixed `-o` in a loop *correctly* twice, consuming each response in the loop body, against
the one wrong use. A gate would have blocked two good commands out of three — past the point where it
gets switched off, which is strictly worse than this paragraph.

**`sort -u` silently merges lines that differ only by punctuation, unless the locale is C.**
**Deliberately NOT gated** — `sort -u` is overwhelmingly used on data with no punctuation-differing
near-duplicates, so a gate would fire constantly on correct commands and get switched off. It needs
the judgement that only prose can carry. Under
`en_US.UTF-8`, collation treats `-`, `.` and `_` as insignificant, so `sort -u` drops one of each
pair: `api-gateway.example.com`/`apigateway.example.com`, `log-store.example.net`/`logstore.example.net`.
Extracting a host list this way reported two entries as missing that were present — a confident,
wrong finding with no error anywhere. The locale is a property of **the container the command runs in**,
so the same pipeline is safe in one image and lossy in the next. Use `LC_ALL=C sort -u` whenever
`-u` is doing set semantics, and prefer a **literal per-item match** over a sorted diff for any
"is every X present in Y" question.

**Never infer a FORMAT from the head of a SORTED file — sorting guarantees the least
representative rows.** **Deliberately NOT gated:** `sort | head` is the correct idiom for top-N
and would fire constantly. A small sample is merely weak; a *sorted* sample is adversarially
biased, because whatever collates first is by definition the outlier — punctuation, digits, and
empty values all sort ahead of ordinary text.

Worked case, on a sensor-id join between two telemetry exports: `head -2` of a sorted list
showed `-TMP-0412-B`, so the delimiter was recorded as a hyphen and a normaliser written for
it. The file actually held a handful of hyphen-delimited rows and a few thousand
underscore-delimited ones — `-` sorts before `_`, so the two rows examined were the rarest in the
file. Almost every
row silently failed to normalise and the join under-reported by most of its input.

**The tell was arithmetic, and it was already on screen:** raw and normalised match counts came
back *identical*. That is impossible if the rows are being rewritten, and it was read as
confirmation rather than as a contradiction. Two numbers that cannot both be right are the same
instrument signal as two that visibly disagree — see the false-zero family above, which this
completes from the sampling end.

So: `shuf -n 20`, or count the shapes (`sed 's/[A-Za-z0-9]//g' | sort | uniq -c`) rather than
eyeballing any fixed end of the file. And when a normalisation step leaves a count unchanged,
that is a failed edit, not a clean one.

**`nc -zu` reports an open UDP port whenever nothing refuses it.** `[gate:nc-udp-zero-scan]` UDP has
no handshake, so nc concludes "open" from the *absence* of an ICMP port-unreachable — identical to a
filtered port, a dropped reply, or a service that simply never answers.

Hit while checking whether a StatsD port was reachable across a firewall. `nc -zuv host 8125` said
**open**; a real counter sent with `printf 'probe:1|c' | nc -u -w1 host 8125` never arrived in the collector, with a
same-host control proving the listener was fine. The firewall was dropping the datagrams, and nc could not
tell. Believing nc would have marked a broken path as working.

**Test UDP by speaking the protocol**: `logger --udp` and a look at the receiver, `dig @host` for DNS,
`curl tftp://…` for a real TFTP transfer. And pair it with a control on a path known to work, or a failure and a block look
the same.

**An unpaged list query's count returns the server's page cap, not the population.**
`[gate:ldap-unpaged-count]` A paginated REST API capped at 100 per page, or a directory server with a
size limit (`ldapsearch` reports "Size limit exceeded"), does not fail loudly: the truncation is
silenced by the idiom that consumes it. `2>/dev/null` swallows the
message, and piping into a counter replaces the tool's exit code with the counter's `0`.

Hit while counting items behind such an API: the unpaged count came back at exactly the
page cap, and the paged count (`-E pr=1000/noprompt` for `ldapsearch`, a loop over `next` links for REST) was well above it. The first number
is not an approximation of the second — it is the cap. A distribution built the same way
(`| awk | sort | uniq -c`) is truncated identically, and worse: the per-bucket counts summed to a
plausible-looking total, so nothing about the output looked short.

**Always page a directory query you intend to count**: `-E pr=1000/noprompt`. And treat a count that
lands on a round power of ten as unproven until a paged run agrees with it — the round number is the
only tell you get, and it reads as coincidence rather than as evidence.

**ffmpeg's `ebur128` filter prints `I: 0.0 LUFS` when it fails, and the failure is further down the
log.** On every OGG in a music pack it printed a well-formed summary of zeros, then "Error
reinitializing filters!". A levelling script took `0.0` as the reading and applied −20 dB to all 59
tracks; the after-measurement read `0.0` too, so before and after "agreed". Measure with
`loudnorm=print_format=json` (`input_i`, `input_tp`), reject anything outside −70…0 as a failed
reading, and print per-file before/after so a column of identical values is visible. Detail in the
`audio-curation` skill.

**A wait loop that checks for a container with `podman ps` sees none while its image is still being
pulled**, so "not running" fires before it ever started and the loop exits in seconds. Check the
`podman run` process (`pgrep -f "podman run --rm --name <n>"`) or the container's own output file
instead, and print the count you waited for beside the result.
