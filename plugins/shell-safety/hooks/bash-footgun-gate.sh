#!/usr/bin/env bash
# PreToolUse(Bash): block the shell foot-guns that fail SILENTLY on a typical setup.
#
# WHY THIS EXISTS, and it is the whole justification: the same foot-guns were documented in an
# always-on memory for weeks and sessions kept hitting them anyway — including one that hit the
# unmatched-glob trap in the very session that was auditing the memory. Instruction text in context
# does not gate behaviour; a hook does, because the harness runs it rather than hoping a model
# remembers. Same lesson as the fan-out depth brake, which also changed nothing until it stopped
# being advice.
#
# SCOPE, deliberately narrow: only patterns that are ~always wrong AND fail quietly. A gate with
# false positives gets disabled, and a disabled gate protects nothing.
#
# THE SHELL IS BASH (CLAUDE_CODE_SHELL=/usr/bin/bash in settings.json). The rules that existed only
# because the local shell was zsh were removed; their traps still apply to commands sent to a remote
# zsh with `ssh host '...'` and are catalogued in the shell-footguns skill, ungated.
#
# Blocking is the point, not a side effect: exit 2 feeds the message back so the command can be
# reissued correctly. It is a correction, not a failure.
set -uo pipefail

payload=$(cat 2>/dev/null || true)
[ -n "$payload" ] || exit 0

# The payload goes in on stdin and the script on fd 3. An env var or argv caps at 128 KiB: past it
# exec fails with E2BIG and the gate exits 0, waving through exactly the commands too big to read.
printf '%s' "$payload" | python3 /dev/fd/3 3<<'PY'
import json, os, re, sys

try:
    d = json.loads(sys.stdin.read())
except Exception:
    sys.exit(0)

# Monitor takes a `command` that runs in this same shell, so every rule below applies to it word for
# word — but it was excluded here AND by the settings.json matcher, so it got none of them.
# Measured (zsh era): a Monitor watcher hit a gated word-splitting trap that the gate never saw,
# and the watch ran to its timeout on a rollout that had actually finished. It needed BOTH fixes — widening only the matcher
# invokes a hook that still exits right here, which is the dead-button shape this gate exists to
# catch.
if (d.get("tool_name") or "") not in ("Bash", "Monitor"):
    sys.exit(0)

cmd = ((d.get("tool_input") or {}).get("command") or "")
if not cmd:
    sys.exit(0)

# Strip heredoc BODIES before matching. Writing a file whose *content* mentions these patterns — a
# test, a doc, this gate itself — is not running them, and blocking it is the false positive that
# gets a gate switched off. Caught immediately: the first run blocked the script written to test it.
# `<<<` is a HERE-STRING, not a heredoc: `grep -q x <<< "hello world"` once made `hello` the
# "terminator" and dropped the rest of the command, blinding every rule below. HEREDOC_RE excludes it.
HEREDOC_RE = re.compile(r"(?<!<)<<(?!<)-?\s*[\"']?([A-Za-z_][A-Za-z0-9_]*)[\"']?")


def strip_heredocs(s):
    out, i = [], 0
    lines = s.split("\n")
    while i < len(lines):
        out.append(lines[i])
        m = HEREDOC_RE.search(lines[i])
        if m:
            term = m.group(1)
            i += 1
            while i < len(lines) and lines[i].strip() != term:
                i += 1  # body dropped
            if i < len(lines):
                out.append(lines[i])  # keep the terminator
        i += 1
    return "\n".join(out)

raw_cmd = cmd  # heredoc bodies intact; used by sudo-drains-heredoc-stdin,
               # pgrep-f-self-match and stdin-eater-in-read-loop (see those rules for why)
cmd = strip_heredocs(cmd)

findings = []

# Quoted spans blanked to equal-length spaces, for rules about what the shell sees UNquoted
# (a mutator named inside an echo, an exec flag). Rules about patterns look inside quotes instead.
def blank_quoted(s):
    out, i, n = [], 0, len(s)
    while i < n:
        c = s[i]
        if c in "\"'":
            j = i + 1
            while j < n and s[j] != c:
                j += 1
            out.append(" " * (j - i + 1))
            i = j + 1
        else:
            out.append(c)
            i += 1
    return "".join(out)

# RULE-ID: grep-pcre-inline
# 1. PCRE inline flags under a grep that is not -P. GNU grep -E/-F/basic have no (?i) syntax, so the
#    pattern matches NOTHING and the empty result is indistinguishable from a clean one. This cost a
#    whole verification pass once.
#    The flag must be inside THAT grep's own arguments (up to the next | ; & or newline). Matching
#    `grep` and `(?i)` anywhere in the command blocked a PromQL regex passed to a python script in
#    the same call as an unrelated grep.
_gi = [m.group(0) for m in re.finditer(r"\bgrep\b[^|;&\n]*", cmd)]
if any(re.search(r"\(\?[ims]+\)", g) for g in _gi):
    if not any(re.search(r"\(\?[ims]+\)", g) and re.search(r"\s-[a-zA-Z]*P", g) for g in _gi):
        findings.append(
            "grep with a PCRE inline flag ((?i)/(?s)/(?m)) but without -P. GNU grep -E has no inline "
            "flags: this matches NOTHING and returns a clean-looking zero. Use `grep -i`, or add -P."
        )

# RULE-ID: pgrep-f-self-match
# 2. pgrep -f / pkill -f match the harness's own wrapper, which runs your command inside a long
#    `<shell> -c 'source ... && eval ...'`. Observed: a dead script reported ALIVE, and a pkill that
#    killed the running command itself (exit 144), silently skipping the rest of the chain.
#    Tested against raw_cmd, NOT the heredoc-stripped cmd: writing a script with `cat > f <<EOF`
#    and running it in the SAME call leaves the whole heredoc body -- pattern included -- in the
#    outer wrapper's argv, so a `pkill -f` in the body still matches the wrapper and kills it.
#    That is exactly how this recurred AFTER the rule existed: the body was stripped before the
#    rule ever saw it, and heredoc'd scripts are the dominant shape here.
#    Reading raw_cmd introduced a false positive immediately: any command that DOCUMENTS this rule
#    quotes the offending form, and the ban and the explanation of the ban are then the same string.
#    It blocked the very edit that was adding this comment. Two guards, both required:
#      - inline-code / quoted spans are blanked, because prose about the rule lives in backticks;
#      - the token must be in COMMAND POSITION (line start, or after ; & | && ||), because prose
#        mentions it mid-sentence while a real invocation begins a line.
#    The `-f` test still sees the flag: only the PATTERN is usually quoted, never the flag.
_pg = re.sub(r"`[^`]*`", " ", raw_cmd)
_pg = re.sub(r"'[^']*'|\"[^\"]*\"", lambda m: " " * len(m.group(0)), _pg)
# `(?:!\s*)?`: a negated test (`until ... && ! pgrep -f x`) is still command position, and is the
# shape a wait loop takes; it slipped past without this and spun forever on its own wrapper.
if re.search(r"(?m)(?:^|[;&|])\s*(?:!\s*)?p(?:grep|kill)\b[^|;&]*\s-[a-zA-Z]*f\b", _pg):
    findings.append(
        "pgrep -f / pkill -f matches this command's OWN harness wrapper (bash -c 'source ... && eval "
        "...'), so it can report a dead process alive or kill the running command. Use "
        "`ps -eo pid,args | grep -E '<real invocation>' | grep -v grep`, then kill resolved PIDs."
    )

# RULE-ID: kubectl-exec-stdin
# 3. Large stdin into `kubectl exec -i` silently produced a 0-byte file while reporting success —
#    twice, and a one-line probe through the identical command worked, so it behaves at test size.
#    The flag test allows other letters on EITHER side of `i`: `\b` after `i` required it to end the
#    cluster, so `-it` / `-ti` — the spellings everyone actually types — were missed entirely.
#    The destination test requires kubectl to RECEIVE stdin (a pipe INTO it, or a `<`/heredoc on it).
#    Matching `cat >` or `tee` anywhere fired on `kubectl exec -i pod -- ls | tee out.txt`, where
#    kubectl is the SOURCE of the pipe and `tee` is ordinary local output capture.
#    AND the remote command must WRITE stdin to a file (`cat >`/`>>`, `tee`, `dd of=`), which was the
#    incident. Stdin consumed by a program (`psql <<EOF`, `sh < script`) is fine, and is exactly what
#    exec-stdin-without-i tells you to write — blocking it sent that advice into a second block.
#    The exec span runs to the first UNQUOTED `| ; & newline`, so a quoted `sh -c 'cat > f'` is in
#    it and a local `| tee out.txt` after kubectl is not.
def _exec_span(s, start):
    i, n, q = start, len(s), ""
    while i < n:
        c = s[i]
        if q:
            if c == q:
                q = ""
        elif c in "\"'":
            q = c
        elif c in "|;&\n":
            break
        i += 1
    return s[start:i]


_EXEC_WRITES = re.compile(r"\bcat\s*>>?|\btee\b|\bdd\b[^|;&]*\bof=")
# Any stdout redirect INSIDE a quoted remote script (`sh -c 'base64 -d >/tmp/x'`) is a file write in
# the pod. An unquoted `>` after the remote command is the LOCAL shell's redirect, so it is not.
# Not `2>`/`&>`-style fd redirects, and not `/dev/null`.
_REMOTE_REDIRECT = re.compile(r"(?<![0-9&<>])>>?(?!&)\s*(?!/dev/null)\S")
_ke_hit = False
for _ke in re.finditer(r"\bkubectl\s+exec\b", cmd):
    _span = _exec_span(cmd, _ke.start())
    if not re.search(r"\s-[a-zA-Z]*i[a-zA-Z]*\b", _span):
        continue
    _fed = re.search(r"\|\s*$", cmd[:_ke.start()]) or re.search(r"<", blank_quoted(_span))
    _remote = _span.split(" -- ", 1)[-1]
    _quoted = " ".join(a or b for a, b in re.findall(r"'([^']*)'|\"([^\"]*)\"", _remote))
    if _fed and (_EXEC_WRITES.search(_remote) or _REMOTE_REDIRECT.search(_quoted)):
        _ke_hit = True
        break
if _ke_hit:
    findings.append(
        "piping/redirecting stdin into `kubectl exec -i` to write a file has silently produced a "
        "0-byte file while reporting success. Use `kubectl cp`, and verify with `wc -c` rather "
        "than trusting the exit status."
    )

# RULE-ID: curl-writeout-prints-credentials
# `curl -u user:pass -w '%{redirect_url}'` (or url_effective / url / referer) prints the URL curl built,
# and curl puts the basic-auth credentials into it as userinfo: `http://admin:<password>@host/...`. A
# registry API call with an admin credential answered 201 with a relative Location, and `-w "%{http_code} %{redirect_url}"`
# printed the admin password to the terminal (the redaction hook caught it before context).
# There is no reason to print a URL from a credentialed request: print `%{http_code}` and read headers.
if re.search(r"\bcurl\b", cmd) and re.search(r"%\{(?:redirect_url|url_effective|url|referer)\}", cmd) \
        and re.search(r"(?:\s-[a-zA-Z]*u\b|\s--user\b|://[^/\s:@]+:[^/\s@]+@)", cmd):
    findings.append(
        "curl with credentials and a `-w` that prints a URL (%{redirect_url}/%{url_effective}/%{url}/"
        "%{referer}): curl writes the basic-auth user:password into that URL. Print %{http_code} "
        "and read the Location header (`-D -`) instead."
    )

# RULE-ID: container-rm-keeps-volume
# `podman rm -f <name>` (or docker) on a container whose image declares a VOLUME -- postgres does --
# leaves its anonymous volume behind, even when the container was started with `--rm`: `--rm` only
# cleans up on a normal exit, not on a forced removal. A day of throwaway-Postgres test runs left
# ~1,000 dangling volumes (~98 GB) and filled the home disk. `-v` removes anonymous
# volumes only, never named ones, so leaving it off is essentially never what's wanted. Command
# position on the quote-blanked string, so prose quoting this rule does not trip it.
_rm = re.search(r"(?m)(?:^|[;&|])\s*(?:podman|docker)\s+(?:container\s+)?rm\b([^|;&\n]*)", _pg)
if _rm and not re.search(r"(?:^|\s)(?:-[a-zA-Z]*v[a-zA-Z]*|--volumes)\b", _rm.group(1)):
    findings.append(
        "`podman rm` / `docker rm` without `-v` leaves the container's anonymous volumes behind (a "
        "postgres container's data dir is one), even for a `--rm` container removed with -f. This "
        "filled the home disk once. Add -v (named volumes are kept), or start the container with "
        "--tmpfs for its data dir."
    )

# RULE-ID: pipefail-grep-q
# 4. `set -o pipefail` plus a pipeline ending in `grep -q`. grep -q exits the moment it matches, the
#    upstream process takes SIGPIPE, and pipefail reports that as a FAILED pipeline — so the test
#    reads "not found" precisely when it DID find the thing. Worse than a plain bug because it is
#    size-dependent: if the producer finishes before grep exits there is no SIGPIPE, so it passes at
#    test size and fails on real data, exactly like the kubectl-exec trap above. Observed: a canary
#    guarding a registry probe reported PROBE BROKEN against a file that plainly contained the token.
if re.search(r"\bpipefail\b", cmd) and re.search(r"\|\s*grep\b[^|;&]*\s-[a-zA-Z]*q[a-zA-Z]*\b", cmd):
    findings.append(
        "`set -o pipefail` with a pipeline into `grep -q`: grep -q exits early, the producer gets "
        "SIGPIPE, and pipefail turns that into a non-zero status — so the check reports NOT FOUND "
        "when it did find it. Intermittent by output size. Use `[ \"$(cmd | grep -c X)\" -gt 0 ]`, "
        "or drop pipefail for that check."
    )

# RULE-ID: for-in-find-ls
# 5. `for f in $(find ...)` / `$(ls ...)`. The shell word-splits the output on whitespace, so every
#    filename containing a space becomes several loop iterations that are not paths. It fails
#    SILENTLY and at a scale that looks like a different bug: a per-file probe over a few hundred
#    files with spaces in their names produced many times more "files" than existed, every extracted
#    field empty — which read as "the probe tool found nothing" rather than "my loop is broken", and
#    cost three debugging rounds. There is no correct use of this
#    form: `find -print0 | while IFS= read -r -d ""` or `find -exec` always beats it.
if re.search(r"\bfor\s+\w+\s+in\s+[\$`]\(?\s*(?:find|ls)\b", cmd):
    findings.append(
        "`for X in $(find ...)` / `$(ls ...)` word-splits on whitespace, so any path containing a "
        "space becomes several bogus iterations — silently, and the wreckage looks like the TOOL "
        "returning nothing rather than the loop being wrong. Use "
        "`find ... -print0 | while IFS= read -r -d '' f; do ...; done`, or `find ... -exec`."
    )

# RULE-ID: read-d-posix-sh
# 6. `read -d` inside `sh -c`. `-d` is a bash extension; dash and busybox `read` do not support it,
#    so the loop reads nothing and the body never runs — producing zero rows with no error. Hit in a
#    container whose /bin/sh is busybox: the identical loop worked under the host's bash, so it
#    looked like the data was missing. `bash -c` is fine and is not gated.
if re.search(r"\bsh\s+-c\b", cmd) and not re.search(r"\b(?:ba|z|k)sh\s+-c\b", cmd):
    if re.search(r"\bread\b[^|;&\n]*\s-[a-zA-Z]*d\b", cmd):
        findings.append(
            "`read -d` inside `sh -c`: -d is a bash extension, so dash/busybox read rejects it and "
            "the loop body never runs — zero rows, no error. Use `bash -c`, or switch to "
            "newline-delimited `while IFS= read -r f` when the values cannot contain newlines."
        )

# RULE-ID: tty-in-command-substitution
# 11. `$(tty ...)` used as a value. When stdin is not a terminal, `tty` prints `not a tty` on
#     STDOUT, not stderr — so `2>/dev/null` suppresses nothing and the substitution yields the
#     literal string `not a tty`. With a `|| echo /dev/tty1` fallback it is worse: `tty` exits
#     non-zero, so BOTH run and the value becomes two lines, `not a tty\n/dev/tty1`. Any later
#     `exec 3<"$val"` then fails and, under `set -e`, kills the script. Hit in an installer
#     script, run as `curl … | bash`, that prompts for input — stdin is ALWAYS
#     a pipe and the broken branch was the only branch — every install would have died
#     at a prompt it never displayed. It survived testing because the harness ran it under
#     `script -qec`, which allocates a pty and makes `tty` succeed. Use `tty -s` for the test (exit
#     code only, prints nothing) and probe `/dev/tty` / `/dev/console` explicitly for the device.
if re.search(r"\$\(\s*tty\b(?![^)]*\s-s\b)", cmd):
    findings.append(
        "`$(tty)` prints `not a tty` on STDOUT when stdin is not a terminal, so `2>/dev/null` does "
        "not suppress it and the value becomes that literal string — or two lines if you added a "
        "`|| echo /dev/...` fallback, since both halves run. Using it as a path then fails and "
        "`set -e` kills the script. Use `tty -s` to TEST (exit code only), and probe `/dev/tty` "
        "then `/dev/console` explicitly to FIND a console device."
    )

# RULE-ID: nc-udp-zero-scan
# 12. `nc -zu` / `nc -uz` "port scanning" UDP. UDP has no handshake, so nc reports **open** whenever
#     no ICMP port-unreachable comes back — which is also what a filtered port, a dropped reply and a
#     silent service all look like. It is a coin flip reported as a fact. Hit while testing whether
#     a UDP port crossed a firewall: `nc -zuv host 5000` said "open", and an actual
#     datagram never arrived, because the firewall passed the request and dropped the
#     reply path. The nc result would have justified skipping a whole piece of
#     infrastructure. Test UDP by doing the protocol: fetch a real file, send a real query.
if re.search(r"\bnc\s+(?:-\w*\s+)*-\w*[zu]\w*[uz]\w*\b|\bnc\b[^|;]*\s-z[a-z]*u|\bnc\b[^|;]*\s-u[a-z]*z", cmd):
    findings.append(
        "`nc -zu` cannot tell an open UDP port from a filtered or silent one: with no handshake it "
        "reports success whenever no ICMP unreachable returns, so a firewall that passes the request "
        "and drops the reply reads as OPEN. Exercise the actual protocol instead — `logger --udp` "
        "for a log port, `dig @host` for DNS."
    )

# RULE-ID: ssh-bash-s-stdin
# A VALUE piped into `ssh host bash -s`. `-s` makes the remote shell read its SCRIPT from stdin, so
#     the value is not input to the remote command — it IS the remote command. The remote shell tries
#     to execute it and answers `<value>: command not found` on STDERR, which lands in whatever
#     captured the run: a results file, a log, the model's context. The real commands never execute,
#     so it presents as an ordinary failure while having disclosed the value. That makes this a
#     credential-leak shape as much as a correctness one — see [[print-names-not-values]].
#     Deliberately narrow: only `echo`/`printf` producers are gated. `cat script.sh | ssh host bash
#     -s`, `ssh host bash -s < script.sh` and the heredoc form are the CORRECT idioms and must keep
#     working — a gate with false positives gets switched off. The heredoc exclusion is also what
#     keeps this clear of sudo-drains-heredoc-stdin's must-allow cases, which are all heredocs.
if (re.search(r"\bssh\b[^|;&]*\b(?:ba)?sh\s+-s\b", cmd)
        and not re.search(r"<<-?\s*[\"']?[A-Za-z_]", cmd)
        and re.search(r"\b(?:echo|printf)\b[^|;&]*\|[^|;&]*\bssh\b", cmd)):
    findings.append(
        "piping a value into `ssh host bash -s`: `-s` reads the remote shell's SCRIPT from stdin, so "
        "the value is executed as a command and echoed back as `not found` on stderr — into your logs "
        "and context — while the intended commands never run. Send the command as the ssh argv string "
        "and let only a stdin-reading consumer take the value: "
        "`printf '%s\\n' \"$VAL\" | ssh host 'sudo -S -p \"\" <cmd>'`. To send a real script, use a "
        "heredoc or `< script.sh`."
    )

# RULE-ID: ldap-unpaged-count
# 13. `ldapsearch` piped into a counter, with no `-E pr=` paging. Directory servers cap a single
#     result set (a common default is **1000**), and returns LDAP result code 4 "Size limit
#     exceeded" — so the truncation DOES announce itself, and the idiom that counts results is
#     exactly the idiom that throws the announcement away: `2>/dev/null` eats the message and the
#     pipe replaces ldapsearch's exit code with the counter's 0. What lands is a clean, plausible,
#     WRONG number that is silently the cap rather than the population. Hit while counting entries
#     under a large base: the unpaged count came back at exactly the server's cap, and the
#     paged count was well above it. A round number IS the tell, but only if you already
#     suspect it. Add `-E pr=1000/noprompt` to page, and treat any count landing on a power of ten
#     as unproven.
if (re.search(r"\bldapsearch\b", cmd)
        and not re.search(r"-E\s+\S*pr=", cmd)
        and "|" in cmd
        and re.search(r"\bwc\s+(?:-\w+\s+)*-\w*l|\bgrep\s+(?:-\w+\s+)*-[a-zA-Z]*c|\buniq\s+(?:-\w+\s+)*-\w*c", cmd)):
    findings.append(
        "`ldapsearch` without `-E pr=.../noprompt` is truncated at the directory's server-side size "
        "limit (other directory servers' size limits differ — check yours, do not "
        "assume a number). The server says so via result code 4 'Size limit exceeded', but piping "
        "into `wc -l`/`grep -c`/`uniq -c` discards ldapsearch's exit status and `2>/dev/null` hides "
        "the message, so you get a clean number that is really the cap. Page it: "
        "`ldapsearch -E pr=1000/noprompt ...`. Distrust any count landing on a round power of ten."
    )

# RULE-ID: tee-masks-exit-status
# 14. Running a script and piping it through `tee`, without `pipefail`. A pipeline's exit status is
#     the LAST command's, and `tee` almost always succeeds — so a job that crashed reports 0 and the
#     harness, the `&&` after it, and any CI step all read it as a clean run. Hit on a 40-chunk
#     discovery sweep: one malformed model response raised, `ThreadPoolExecutor.map` abandoned the 8
#     remaining chunks, and `| tee` turned the crash into `[exited with code 0]`. 20% of the corpus
#     was never read, the missing fifth was the most recent slice because the chunks were
#     time-ordered, and the taxonomy built from it looked entirely plausible. Nothing anywhere said
#     "partial". Redirect instead (`cmd > log 2>&1`), or set `pipefail` if you genuinely need the tee.
_tee = re.search(r"^(.*?)\|\s*tee\b", cmd, re.S)
if (_tee and not re.search(r"\bpipefail\b", cmd)
        and re.search(r"\b(python3?|bash|sh|zsh|node|ruby|perl|make|cargo)\s+\S", _tee.group(1))):
    findings.append(
        "Piping a script through `tee` without `pipefail`: the pipeline reports TEE's exit status, "
        "so a crashed job exits 0 and reads as a clean run. This silently truncated a 40-chunk sweep "
        "to 32 with no error anywhere. Use `cmd > log 2>&1` and read the file, or add "
        "`set -o pipefail` if the tee is genuinely needed."
    )

# RULE-ID: zsh-pipestatus-in-bash
# `${pipestatus[1]}` is ZSH's array; the Bash tool's shell is bash, where lowercase `pipestatus` is
#     an unset variable and expands to the EMPTY STRING. Inverse of the retired
#     bash-pipestatus-in-zsh, and live because months of zsh-era habit (and this gate's own advice)
#     wrote `echo "rc=${pipestatus[1]}"`, which now prints `rc=` and silences any check on it.
#     Bash's array is uppercase and 0-indexed: `${PIPESTATUS[0]}`. A `zsh -c` or an `ssh` (remote
#     zsh login shell) carries zsh semantics and is allowed — as a COMMAND WORD only, so `~/.ssh` or
#     `id_ssh` does not exempt — and only for an expansion inside a quote opened after that word: one
#     `ssh` earlier in the string used to exempt a local `echo ${pipestatus[1]}` after it. Matches the
#     EXPANSION, not the word, and single-quoted grep/rg arguments are blanked first, so searching
#     for it (`grep -rn '${pipestatus[1]}'`) is allowed.
_PIPESTATUS_ZSH = re.compile(r"\$\{?pipestatus\b")
_ZSH_WORD = re.compile(r"(?<![\w./~-])(?:zsh|ssh)(?=\s)")
_ps_cmd = re.sub(r"\b(?:grep|rg)\b[^|;&\n]*",
                 lambda m: re.sub(r"'[^']*'", lambda q: " " * len(q.group(0)), m.group(0)), cmd)


def _remote_zsh(s, pos):
    """Is s[pos] inside a quoted argument that began after the last `zsh`/`ssh` word before it?"""
    words = list(_ZSH_WORD.finditer(s, 0, pos))
    if not words:
        return False
    q, i = "", words[-1].end()
    while i < pos:
        c = s[i]
        if c == "\\" and q != "'":
            i += 2; continue
        if q:
            if c == q:
                q = ""
        elif c in "'\"":
            q = c
        elif c in ";&|\n":
            return False        # the ssh/zsh statement ended before the expansion
        i += 1
    return bool(q)


if any(not _remote_zsh(_ps_cmd, m.start()) for m in _PIPESTATUS_ZSH.finditer(_ps_cmd)):
    findings.append(
        "`${pipestatus[1]}` is zsh's array and this shell is BASH, where it expands to the empty "
        "string — so a status check built on it silently reads nothing. Use bash's "
        "`${PIPESTATUS[0]}` (uppercase, 0-indexed) for the first stage, or `set -o pipefail`."
    )

# Does the command capture a pipeline's exit status in a way that WORKS IN THIS SHELL (bash)?
# Shared by the three formatter rules below so their exemption cannot drift apart.
_status_ok = bool(re.search(r"\bpipefail\b", cmd) or re.search(r"\$\{?PIPESTATUS\b", cmd))

# RULE-ID: formatter-masks-exit-status
# Reading `$?` after a pipeline whose LAST stage is a pure formatter. `sed`, `awk`, `cut`, `tr`,
#     `nl`, `column` and friends exit 0 on essentially any input, so `$?` describes the formatter and
#     never the command whose status you wanted. Distinct from the `tee` rule above: that one is about
#     a crash reading as success in a log pipeline, this one is about an explicit status CHECK that
#     cannot fail. Hit twice in one evening, both times on a check written specifically to avoid false
#     passes: `python3 check.py | sed 's/^/  /'; echo "exit=$?"` printed `exit=0` for a script
#     that had just correctly exited 1, and earlier a `rc=124` timeout was read as "writes are not
#     blocked". `head`/`tail` are in scope for the same reason and were added after a SECOND
#     harness hit the identical trap: a lint gate read `tail`'s status and printed "lint: clean"
#     while ruff was printing `7 fixable` two lines above it. Not gated for `grep`/`test`/`cmp`,
#     whose exit status is the point of running them.
#     `sort`/`uniq`/`wc` were added after a THIRD hit, this one on the gate's own author:
#     `curl -f ... && grep -o ... | sort -u; echo "rc=$?"` printed `rc=0` while grep had matched
#     NOTHING, and the zero was read as "the anchors I guessed are present". The enumeration above
#     was already reaching for completeness (`rev`, `fold`, `pr`, `expand`), so their absence was a
#     gap in this list rather than a new rule. `sort -c`/`-C` are CHECK modes whose status is the
#     point, so they are carved out by the negative lookahead -- without it this fires on correct
#     code, which is how a gate gets switched off.
#     Redirect to a file and read it, use `${PIPESTATUS[0]}`, or set `pipefail`.
# Scoped to ADJACENT statements. An earlier version matched `$?` anywhere after any formatter
# pipe in the whole string, and fired on a command whose `| sed` and `$?` were in unrelated
# statements several commands apart -- a false positive on its own author within the hour. A gate
# that cries wolf gets switched off, which is strictly worse than the prose it replaced.
def _blank_subst(s):
    """Blank the body of every `$( … )`, keeping offsets. A pipeline inside one is an argument:
    `bash -c "$(sed … | sed …)"; echo $?` reads bash's status, not sed's."""
    out, depth, i = list(s), 0, 0
    while i < len(s):
        if s.startswith("$(", i):
            depth += 1; i += 2; continue
        if depth and s[i] == "(":
            depth += 1
        elif depth and s[i] == ")":
            depth -= 1
            if not depth:
                i += 1; continue
        if depth:
            out[i] = " "
        i += 1
    return "".join(out)


_stmts = re.split(r"(?:;|\n|&&|\|\|)", cmd)
_stmts_b = re.split(r"(?:;|\n|&&|\|\|)", _blank_subst(cmd))
if len(_stmts_b) != len(_stmts):
    _stmts_b = _stmts       # a separator inside a substitution: keep the old behaviour
_FMT_TAIL = re.compile(r"\|\s*(sed|awk|cut|tr|nl|column|fmt|expand|unexpand|pr|rev|fold|head|tail"
                      r"|uniq|wc|sort(?!\s+-[A-Za-z]*[cC]))\b[^|]*$")
_ASSIGN_ONLY = re.compile(r"^\s*(?:(?:local\s+|export\s+)?[A-Za-z_]\w*=(?:\$\(\s*\)|\S)*\s*)+$")
_fmt = False
for _i, _st in enumerate(_stmts):
    if _i == 0 or not re.search(r"\$\?", _st):
        continue
    # A bare `n=$(cmd | wc -l)` takes the substitution's status, so its pipeline counts; anywhere
    # else a substitution is an argument and its pipeline does not.
    _prev = _stmts[_i - 1] if _ASSIGN_ONLY.match(_stmts_b[_i - 1]) else _stmts_b[_i - 1]
    if _FMT_TAIL.search(_prev.strip()):
        _fmt = True
        break
if _fmt and not _status_ok:
    findings.append(
        "Reading `$?` after a pipeline ending in a formatter (`sed`/`awk`/`cut`/...): the status is "
        "the FORMATTER's, which is 0 on almost any input, so the check can never fail. Redirect to a "
        "file and read it (`cmd > out 2>&1; rc=$?`), or use `${PIPESTATUS[0]}`, or set `pipefail`."
    )

# RULE-ID: prints-and-fails-fallback
# A command that PRINTS A USABLE ANSWER and STILL exits non-zero, wrapped in
#     `$(cmd || fallback)` — so BOTH branches run and the value is the two concatenated. Not a
#     status-masking rule like the formatter ones above; here the status is honoured correctly and
#     the OUTPUT is the casualty.
#     `grep -c` prints `0` and exits 1 when nothing matches, so `$(grep -c X f || echo 0)` yields
#     the two-LINE string "0\n0". `systemctl is-enabled` prints `masked`/`disabled` and exits
#     non-zero for both, so `$(systemctl is-enabled u || printf absent)` yields "maskedabsent".
#     Both shipped from one script in one session. The first put a raw newline inside a
#     hash-and-length-framed record, which arrived (lines - 1) bytes short and was rejected as
#     transport corruption — a bug three hundred lines from where it looked.
#     It cannot reproduce on a healthy input, because the fallback only fires on the EMPTY /
#     zero-match case, which is exactly the case a quick local test does not have.
#     Capture first, default second: `n="$(cmd)" || n=""; [ -n "$n" ] || n=0`.
_PRINTS_AND_FAILS = re.compile(
    # `-[A-Za-z]*c[A-Za-z]*`, not `-[A-Za-z]*c`: the count flag can be anywhere in a cluster, and
    # requiring it LAST missed the very common `grep -cE`. Caught by the must-block case rather
    # than by reading the pattern, which is the argument for writing both halves of the test.
    # `--color` cannot match, because the second `-` is not in [A-Za-z].
    r"\$\((?:[^()]*\b(?:grep\s+-[A-Za-z]*c[A-Za-z]*|systemctl\s+is-(?:enabled|active)|"
    r"git\s+describe|pkg-config\s+--modversion)\b[^()]*)\|\|[^()]*\)")
if _PRINTS_AND_FAILS.search(cmd):
    findings.append(
        "`$(cmd || fallback)` where cmd PRINTS a usable answer and still exits non-zero: both "
        "branches run and you get them concatenated. `grep -c` prints `0` and exits 1 on no "
        "match, so `$(grep -c X f || echo 0)` is the two-line string \"0\\n0\"; "
        "`systemctl is-enabled` prints `masked` and exits non-zero, giving \"maskedabsent\". "
        "It only fires on the zero/empty case, so a local test on real data will not show it. "
        "Capture first, default second: `n=\"$(cmd)\" || n=\"\"; [ -n \"$n\" ] || n=0`."
    )

# RULE-ID: formatter-as-condition
# A formatter-terminated pipeline used directly as an `if`/`while`/`until` CONDITION. Sibling of
#     formatter-masks-exit-status above, which only sees an explicit `$?` read in an adjacent
#     statement — this is the same defect with no `$?` anywhere, so that rule cannot fire. The
#     condition tests the FORMATTER, which succeeds on any input, so the branch is taken
#     unconditionally. Hit on a merge dry-run: `if git merge <branch> | tail -3; then echo CLEAN`
#     printed CLEAN for a merge that had aborted with `fatal: You have not concluded your merge`,
#     and the "clean" verdict was two lines above output visibly showing the merge had not applied.
#     `grep`/`test`/`cmp` are excluded, as above: their status is the reason you ran them.
#     Put the command on its own line and read `$?`/`${PIPESTATUS[0]}`, or set `pipefail`.
_COND_FMT = re.compile(
    r"(?:^|;|\n|&&|\|\||\bthen\b|\bdo\b)\s*(?:if|while|until)\s+"
    r"(?P<cond>[^;\n]+?)(?:;|\bthen\b|\bdo\b)"
)
_FMT_LAST = re.compile(
    r"\|\s*(sed|awk|cut|tr|nl|column|fmt|expand|unexpand|pr|rev|fold|head|tail|cat|tee)\b[^|]*$"
)
if not _status_ok:
    for _m in _COND_FMT.finditer(cmd):
        # A formatter inside $(...) or `...` feeds a real test (`[ -n "$(x | tail -1)" ]`),
        # so strip substitutions before asking what the pipeline's last stage is.
        _cond = re.sub(r"\$\([^()]*\)", "S", _m.group("cond"))
        _cond = re.sub(r"`[^`]*`", "S", _cond).strip()
        if _FMT_LAST.search(_cond):
            findings.append(
                "An `if`/`while` condition ending in a formatter (`tail`/`head`/`sed`/...): the "
                "condition tests the FORMATTER, which succeeds on almost any input, so the branch "
                "is taken even when the real command failed. This reported a merge as CLEAN when it "
                "had aborted. Run the command on its own line and test `$?` / `${PIPESTATUS[0]}`, "
                "or set `set -o pipefail`."
            )
            break

# RULE-ID: formatter-then-and
# THIRD sibling of formatter-masks-exit-status and formatter-as-condition, and the one that had no
#     rule: a formatter-terminated pipeline followed by `&&` or `||`. The operator tests the
#     FORMATTER, so the `&&` branch runs even when the real command failed, and the `||` branch
#     never runs at all. No `$?` appears and there is no `if`, so neither sibling can fire.
#     Hit on a push: `git push -q origin HEAD:main | tail -3 && echo "pushed to main"` printed a
#     confident "pushed to main" for a push git had REJECTED as non-fast-forward — with git's own
#     "use 'git pull' before pushing again" hint two lines above the claim. The false success is the
#     dangerous direction: it is what stops you looking.
#     grep/test/cmp are excluded, as in both siblings: their status is the reason you ran them.
#     Put the command on its own line and read `$?` / `${PIPESTATUS[0]}`, or set `set -o pipefail`.
#
#     MENTION VS USE, and note why neither obvious fix works. The first regex ran `[^|;&\n]*` from
#     the formatter to the operator, which cannot cross a `&` but happily matches one INSIDE the
#     formatter's own program: `| awk '$3 != "Running" && $3 != "Completed" {print $1}'` was blocked,
#     and a compound awk condition after a pipe is everyday shell, not an edge case.
#     Blanking quoted spans wholesale (`blank_quoted`) fixes that and breaks the other direction:
#     `sh -c "make build | tail -3 && echo ok"` is a REAL instance whose pipeline and operator are
#     both inside one quoted span, and it is caught today. Measured both, in both spellings.
#     What separates them is WHERE THE QUOTE OPENS. The false positive's quote opens *after* the
#     formatter name, so the operator is that formatter's program text. The nested-shell case's quote
#     opened before the pipe, so from the formatter's position the operator is bare. So the scan
#     starts fresh at the formatter token and tracks quote state from THERE — deliberately not from
#     the start of the command, which is the whole mechanism.
_FMT_TOK = re.compile(
    r"\|\s*(?:sed|awk|cut|tr|nl|column|fmt|expand|unexpand|pr|rev|fold|head|tail|tee)\b")


def _fmt_then_op(s):
    for m in _FMT_TOK.finditer(s):
        i, n, q = m.end(), len(s), ""
        while i < n:
            c = s[i]
            if q:                       # inside the formatter's own quoted program
                if c == q:
                    q = ""
                i += 1
                continue
            if c in "\"'":
                q = c
                i += 1
                continue
            nxt = s[i + 1] if i + 1 < n else ""
            if (c == "&" and nxt == "&") or (c == "|" and nxt == "|"):
                return True
            if c in "|;&\n":            # same stop set as the original character class
                break
            i += 1
    return False


if _fmt_then_op(cmd) and not _status_ok:
    findings.append(
        "A pipeline ending in a formatter (`tail`/`head`/`sed`/...) followed by `&&` or `||`: the "
        "operator tests the FORMATTER, which succeeds on almost any input, so the `&&` branch runs "
        "even when the real command failed and the `||` branch never runs. This printed "
        "\"pushed to main\" for a push git had rejected. Run the command on its own line and test "
        "`$?` / `${PIPESTATUS[0]}`, or set `set -o pipefail`."
    )

# RULE-ID: commit-then-push-unguarded
# A `git commit` and a LATER `git push` in one command, where nothing stops the push when the
#     commit fails. The incident: `git commit --only <untracked> -m …; …; git push origin HEAD:main`
#     — the commit failed, the `;` ran the push anyway, and it shipped nineteen earlier, untested
#     local commits. This is the only shape kept from a broader "mutator then anything" rule: a
#     read-only follower leaves the failure on screen, and "any mutator then any mutator" was mostly
#     idioms (`kubectl create ns x 2>/dev/null; kubectl apply`, `git tag -l; git push --tags`).
#     Both must be in COMMAND POSITION: the start of a top-level statement (after `;`, newline, `&&`,
#     `||`, `then`, `do`, `(`, `{`, or an `if`/`while`/`!` for the push), with optional `VAR=x`
#     prefixes and git global options (`-C dir`, `-c k=v`, `--git-dir=`, `--work-tree=`). A word in an
#     `echo`, a comment, a heredoc body or `$(git commit-tree …)` is not command position.
#     Guarded, so quiet: `git commit … && … && git push` (an unbroken `&&` chain), `git commit … ||
#     exit|return`, the commit as an `if`/`while` condition, `$?` read between the two, or
#     `set -e`/`set -o errexit` before the commit. `case … esac` is blanked first: its branches are
#     alternatives, and `;;` is not a sequence.
#     The splitter keeps a stack of quote/paren/brace contexts, so `"$(echo 'a"b')"`, `${x:-\}}`
#     and `$( … )` do not end a statement early or swallow the rest.
_SET_E = re.compile(r"^\s*set\s+(?:-[A-Za-z]*e[A-Za-z]*\b|.*-o\s+errexit\b)")
_LEAD = re.compile(r"^(?:\s*(?:then|do|else|fi|done|\{|\}|\()(?=\s|$|;|\())*\s*")
_COND = re.compile(r"^(?:if|elif|while|until|!)\s+")
_GIT_CMD = re.compile(
    r"^(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*git"
    r"(?:\s+(?:-C\s+\S+|-c\s+\S+|--git-dir=\S+|--work-tree=\S+|--no-pager|-P))*"
    r"\s+(commit|push)(?![\w-])"
)
_CASE = re.compile(r"(?s)(?<![\w-])case\s.*?(?<![\w-])esac(?![\w-])")


def _top_statements(s):
    """[(text, separator_after)] at top level; separator is ; \\n & && || | or '' at the end.
    Blank statements (blank lines, comment lines, a newline after `&&`) are dropped."""
    out, cur, i, n, st = [], [], 0, len(s), []
    while i < n:
        c = s[i]
        top = st[-1] if st else ""
        if top == "'":
            cur.append(c); i += 1
            if c == "'":
                st.pop()
            continue
        if c == "\\" and i + 1 < n:
            cur.append(s[i:i + 2]); i += 2; continue
        if top in ('"', "`"):
            if c == top:
                st.pop()
            elif top == '"' and s.startswith("$(", i):
                st.append("("); cur.append("$("); i += 2; continue
            elif top == '"' and c == "`":
                st.append("`")
            cur.append(c); i += 1; continue
        if c in "\"'`":
            st.append(c); cur.append(c); i += 1; continue
        if c == "#" and not st and (i == 0 or s[i - 1] in " \t\n;&|("):
            while i < n and s[i] != "\n":
                i += 1
            continue
        if c in "({":
            st.append(c); cur.append(c); i += 1; continue
        if (c == ")" and top == "(") or (c == "}" and top == "{"):
            st.pop(); cur.append(c); i += 1; continue
        if not st:
            two = s[i:i + 2]
            sep = ""
            if two in ("&&", "||"):
                sep = two
            elif c == "&" and ((i > 0 and s[i - 1] in "<>|") or s[i + 1:i + 2] == ">"):
                sep = ""  # 2>&1, &>, |& are redirects
            elif c in ";\n|&":
                sep = c
            if sep:
                if "".join(cur).strip():
                    out.append(("".join(cur), sep))
                cur = []; i += len(sep); continue
        cur.append(c); i += 1
    if "".join(cur).strip():
        out.append(("".join(cur), ""))
    return out


def _groups(s):
    """Inner text of each outermost unquoted ( ) or { } group in s: a function body, a subshell, a
    brace block. Their statements are not top level, so without this `f() { git commit; git push; }`
    went unchecked."""
    out, st, start, i, n = [], [], 0, 0, len(s)
    while i < n:
        c = s[i]
        top = st[-1] if st else ""
        if c == "\\" and top != "'":
            i += 2; continue
        if top in ("'", '"'):
            if c == top:
                st.pop()
        elif c in "'\"":
            st.append(c)
        elif c in "({":
            if not st:
                start = i + 1
            st.append(c)
        elif (c == ")" and top == "(") or (c == "}" and top == "{"):
            st.pop()
            if not st:
                out.append(s[start:i])
        i += 1
    return out


def _unguarded_push(text, errexit):
    stmts = _top_statements(_CASE.sub(lambda m: " " * len(m.group(0)), text))
    pending, chain = None, False
    for i, (st, sep) in enumerate(stmts):
        body = _LEAD.sub("", st)
        if _SET_E.match(body):
            errexit = True
        if any(_unguarded_push(g, errexit) for g in _groups(st)):
            return True
        if pending is not None:
            if "$?" in st:
                pending = None
            elif chain and stmts[i - 1][1] != "&&":
                chain = False      # the && chain broke: a later push no longer waits on the commit
        cond = _COND.match(body)
        m = _GIT_CMD.match(body[cond.end():] if cond else body)
        if not m:
            continue
        if m.group(1) == "push":
            if pending is not None and not chain:
                return True
            continue
        # a commit
        if errexit or cond or sep == "|":
            continue
        if sep == "||":
            nxt = _LEAD.sub("", stmts[i + 1][0]) if i + 1 < len(stmts) else ""
            if re.match(r"(?:exit|return)\b", nxt):
                continue
        pending, chain = i, sep == "&&"
    return False


if _unguarded_push(cmd, False):
    findings.append(
        "`git commit` and then `git push` in one command with nothing stopping the push when "
        "the commit fails, so it pushes whatever was ALREADY committed. This shipped nineteen "
        "untested commits once, after a commit failed on a pathspec. Chain them: "
        "`git commit … && git push`, or put `set -e` at the top."
    )

# RULE-ID: bash-file-underscore-arg
# 15. A bare `_` passed as the first argument to a script FILE. That placeholder belongs to
#     `bash -c 'body' _ arg1`, where `_` becomes `$0` so `arg1` lands in `$1`. Run the same body as a
#     file — `bash body.sh _ arg1` — and `_` IS `$1`, so every positional shifts by one and the script
#     reads the wrong values. It does not error: it does the wrong work quietly. Hit while testing a
#     file-moving helper by extracting its `bash -c` body to a file: the probe moved nothing, printed
#     nothing and exited 0, which is indistinguishable from a passing test. The fix is to keep the
#     `bash -c` form — `bash -c "$(cat body.sh)" _ arg1` — or drop the `_` and renumber.
# The lookbehind matters: without it the `sh` inside `body.sh` matches as the interpreter, so
# `bash body.sh real _ other` (a legitimate bare `_` in a later position) was blocked.
if re.search(r"(?<![\w.\-])(?:\S*/)?(?:bash|sh|zsh)\s+(?!-)[^\s;|&]+\s+_(?=\s|$)", cmd):
    findings.append(
        "A bare `_` as the first argument to a script FILE: that placeholder only works with "
        "`bash -c 'body' _ arg1`, where it becomes `$0`. Run as a file and `_` is `$1`, so every "
        "positional shifts by one and the script silently reads the wrong values — it exits 0 having "
        "done nothing. Use `bash -c \"$(cat body.sh)\" _ arg1`, or drop the `_` and renumber."
    )

# RULE-ID: backtick-in-prose-flag
# A markdown backtick inside a double-quoted value for a long-form TEXT flag
# (--description / --body / --message / --notes / -m). In bash (and zsh) a backtick inside double quotes is
# COMMAND SUBSTITUTION, so `400` runs the command 400, prints "command not found" to stderr, and
# substitutes empty — the flag still gets sent, just with holes where the code spans were. Nothing
# fails: the MR or commit is created and reads fine at a glance. Hit on a real MR description where
# `400`, `401` and `404` all vanished from a sentence explaining what those codes proved, leaving
# "the endpoint answers  rather than ". Write the text to a FILE and pass "$(cat file)", which is
# substituted once by the shell and never re-interpreted.
_m = re.search(r"(?:--description|--body|--message|--notes|(?<![\w-])-m)[= ]\s*\"([^\"]*)\"", cmd)
if _m and "`" in _m.group(1):
    findings.append(
        "A markdown backtick inside a double-quoted --description/--body/-m value: the shell treats "
        "backticks in double quotes as COMMAND SUBSTITUTION, so `400` runs `400`, substitutes empty "
        "and silently removes the code span. The flag still sends and the result reads fine at a "
        "glance. Write the body to a file and pass \"$(cat body.md)\", or single-quote the value."
    )


# RULE-ID: memory-write-via-bash
# Writing a memory or skill file from Bash bypasses `memory-write-gate.sh`, which is PreToolUse on
# Write|Edit|MultiEdit|NotebookEdit ONLY. The auto-mode instruction to prefer Bash over the Write/Edit
# tools for file changes steers straight through that hole: seven memory and skill files were once
# written through `python3 - <<'PY'` heredocs, none of them gated.
#
# A broad Bash gate would misfire on legitimate bulk `cp`/`mv`, so this rule is deliberately narrow:
# it fires only when a write VERB
# targets one of those paths. Reads (`cat`, `grep`, `sed -n`), `cp`/`mv` in either direction, and a
# redirect whose target is elsewhere are all untouched -- a gate with false positives gets switched
# off, which is worse than the prose it replaces.
#
# MATCHED AGAINST `raw_cmd`, NOT `cmd`, and that is the whole reason it works. `strip_heredocs`
# drops the body, and the dominant shape puts both the path and the `write_text()` INSIDE a python
# heredoc -- so against `cmd` this rule sees `python3 - <<'PY'` and nothing else, and would have
# missed all seven. Same opt-out as sudo-drains-heredoc-stdin and pgrep-f-self-match.
_MEMPATH = r"\.claude/(?:memory/|skills/|projects/[^/\s'\"]+/memory/)"
_memhits = re.findall(_MEMPATH + r"[^\s'\"();]*", raw_cmd)
# MEMORY.md is the index and appending to it is the documented idiom, so a command touching only
# the index is exempt. A command touching the index AND a real memory is not.
if [p for p in _memhits if not p.endswith("MEMORY.md")]:
    _how = None
    _pyw = False
    if re.search(r">>?\s*[^\s|;&]*" + _MEMPATH, raw_cmd):
        _how = "a `>` / `>>` redirect"
    elif re.search(r"\btee\b[^|;&\n]*" + _MEMPATH, raw_cmd):
        _how = "`tee`"
    elif re.search(r"\bsed\b[^|;&\n]*\s-i[^|;&\n]*" + _MEMPATH, raw_cmd):
        _how = "`sed -i`"
    elif re.search(r"write_text\s*\(|\.open\s*\(\s*['\"]w|open\s*\([^)]*,\s*['\"]w", raw_cmd):
        _pyw = True
    if _how:
        findings.append(
            "%s targeting a file under `.claude/memory/` or `.claude/skills/`. That path is gated "
            "by `memory-write-gate.sh`, which is PreToolUse on Write|Edit|MultiEdit only -- so "
            "authoring it from Bash silently skips the gate and the write looks fine. Seven were "
            "written this way in one session before anyone noticed. Use the Write or Edit tool for "
            "memory and skill files; Bash stays correct for reading them, and for bulk `cp`/`mv`."
            % _how
        )
    elif _pyw:
        # KNOWN OVER-TRIGGER, and the message says so rather than asserting a target it has not
        # established. The three branches above each prove the memory path is the write's TARGET.
        # This one cannot: the dominant real shape builds the path into a variable well away from
        # the `write_text()`, so any adjacency requirement would miss exactly the case the rule was
        # written for. It therefore fires on the CONJUNCTION, and a memory path present only as a
        # `cp` SOURCE satisfies it. Keeping the block and correcting the claim
        # is the trade: a false negative here loses an ungated memory write, a false positive costs
        # one split command.
        findings.append(
            "this command contains BOTH a `.claude/memory/` or `.claude/skills/` path AND a Python "
            "write (`write_text(`, `open(..., 'w')`). Unlike the redirect / `tee` / `sed -i` "
            "branches, this one CANNOT prove from the string that they are the same file -- so it "
            "blocks the pair rather than risk missing an ungated memory write. If the write does "
            "target a memory or skill file, use the Write or Edit tool. If it does not -- a `cp` "
            "whose SOURCE is a skill path is the common case -- split the copy and the `python3` "
            "into two Bash calls and neither will carry the pair."
        )

# NOT GATED, deliberately: `sort -u` collapsing punctuation under a UTF-8 locale
# (api-gateway.example.com vs apigateway.example.com — the hyphen is insignificant to the collator,
# so one of the pair is dropped). It fails silently and it has bitten here, but `sort -u` is
# overwhelmingly used on data with no punctuation-differing near-duplicates, so gating it would fire
# constantly on correct
# commands — and a gate with false positives gets switched off. It stays in the skill, where the
# judgement it needs can live with it.

# RULE-ID: cat-a-through-line-prefix
# `cat -A` exists to show the EXACT bytes of each line, leading whitespace included. Piping it
# through a line-prefixing sed (`s/^/  /`, to indent it for readability) destroys the one thing it
# was run for: every line gains two columns, and indentation read off that output is wrong by
# exactly the width of the prefix.
#
# Hit three times in one session on the same repo. Each time the misread indentation went straight
# into a scripted edit's anchor string, which then failed to match -- and a `str.replace` that
# matches nothing returns the string unchanged and exits 0, so the file was silently unedited. The
# assert caught it each time, but only after the wrong anchor had been written from the wrong read.
#
# Read byte-exact output raw. Indent it for display only when you are not going to write an anchor
# from it -- and the safe habit is simply never to prefix `cat -A`.
if re.search(r"\bcat\s+(?:-\w*\s+)*-\w*A\w*\b", cmd) and re.search(
    r"\bsed\b[^;&]*\bs\s*([/|#,~!])\^\1", cmd
):
    findings.append(
        "piping `cat -A` through a line-prefixing sed (`s/^/  /`) defeats the only reason to run it: "
        "every line gains the prefix's width, so indentation read from that output is wrong by that "
        "many columns. An anchor written from it then silently fails to match. Read `cat -A` raw."
    )

# RULE-ID: sudo-drains-heredoc-stdin
# `sudo` DRAINS STDIN. When the script itself arrived on stdin -- `ssh host 'bash -s' <<EOS` -- the
# first `sudo` swallows every remaining line, so the script stops there. It does not error: the
# lines before sudo ran, sudo ran, exit status is 0, and the output simply ends early. That reads as
# "the command produced less output than expected", not as "half my script never executed".
#
# Hit TWICE in one session (a triage session) by someone who knew the rule -- it is
# written down in a skill's notes, where it was found by reading, not by being
# prevented. Prose that has already failed gets escalated to something the harness runs.
#
# This is the ONE rule that reads heredoc BODIES (via raw_cmd). That is safe here precisely because
# the opener must feed a shell reading its script from stdin (`bash -s`) -- a heredoc written to a
# FILE never matches, which is the false positive the global strip_heredocs() exists to prevent.
def _stdin_shell_heredoc_bodies(s):
    """Yield bodies of TOP-LEVEL, properly terminated heredocs feeding a stdin-reading shell.

    Two narrowings, both added after this rule fired on commands that merely MENTIONED the pattern
    rather than running it -- the false-positive class the global strip_heredocs() exists to avoid,
    which this rule opts out of by reading raw_cmd:

    1. Consume EVERY heredoc's body, not just the interesting ones. Otherwise the scan walks on into
       an outer heredoc's body and matches a nested `ssh host 'bash -s' <<EOS` -- i.e. it blocks the
       commit that adds this rule's own test cases. It did exactly that.
    2. Require the terminator line to exist. A `<<WORD` with no terminator was never a heredoc, just
       text inside a quoted string (a printf format, a doc); treating the remainder of the command
       as its "body" made an unrelated later `sudo` look like a hit.
    """
    lines = s.split("\n")
    i = 0
    while i < len(lines):
        m = HEREDOC_RE.search(lines[i])
        if m:
            is_stdin_shell = bool(re.search(r"\b(?:ba)?sh\b[^<]*\s-s\b", lines[i]))
            term, i, body = m.group(1), i + 1, []
            while i < len(lines) and lines[i].strip() != term:
                body.append(lines[i]); i += 1
            if is_stdin_shell and i < len(lines):  # i < len => terminator found
                yield body
        i += 1

for _body in _stdin_shell_heredoc_bodies(raw_cmd):
    _hit = None
    for _n, _line in enumerate(_body):
        if re.search(r"\bsudo\b", _line) and not re.search(r"<\s*/dev/null", _line):
            _hit = _n; break
    # Only fire if something FOLLOWS the sudo -- a sudo on the last line drains nothing.
    if _hit is not None and any(
        l.strip() and not l.strip().startswith("#") for l in _body[_hit + 1:]
    ):
        findings.append(
            "`sudo` inside a heredoc piped into `bash -s` (e.g. `ssh host 'bash -s' <<EOS`): sudo "
            "reads from stdin, and stdin IS the rest of your script, so every line after the first "
            "sudo is swallowed and never runs. Exit status is 0 and the output just stops early. "
            "Write the script to a file and `scp` it, then `ssh host 'bash /tmp/x.sh'` -- or give "
            "every sudo `</dev/null`."
        )
        break

# RULE-ID: stdin-eater-in-read-loop
# 24. A `while ... read` loop fed from a file or pipe, whose BODY calls a command that itself reads
#     stdin, has its remaining input eaten by that command: the loop processes only the FIRST item
#     and still exits 0. Observed with `ssh` inside `while read -r ...` -- 12 hosts
#     queued, 1 checked, exit 0, no error printed anywhere. It renders as "only one
#     row matched", which is a plausible finding rather than a visible breakage, so nothing prompts a
#     re-check. Same family as sudo-drains-heredoc-stdin, one layer out.
#     Scoped to the text between `while ... read` and its `done` so an eater used OUTSIDE the loop
#     (the common "query to a file, then loop over the file" shape) is not a false positive.
#     Read from raw_cmd: these loops are nearly always written inside a heredoc'd script.
#     Like pgrep-f-self-match, reading raw_cmd means a command that DOCUMENTS or TESTS this rule
#     carries the offending form as data. Same discriminator, and it is the honest one: real code sits
#     in COMMAND POSITION (line start, or after ; & |), whereas a documented or test-case copy sits
#     inside a quoted string. Quoted spans are blanked with equal-length padding so the slice offsets
#     below stay aligned.
STDIN_EATERS = r"(?:ssh|az|kubectl|gh|docker|podman|mysql|psql|ffmpeg|openssl)\b"
_le = re.sub(r"'[^']*'|\"[^\"]*\"", lambda m: " " * len(m.group(0)), raw_cmd)
for _m in re.finditer(r"(?m)(?:^|[;&|])\s*while\b[^\n]*\bread\b", _le):
    _tail = _le[_m.end():]
    _dm = re.search(r"\bdone\b", _tail)
    _body = _tail[:_dm.start()] if _dm else _tail
    if re.search(r"(?m)(?:^|[;&|]|\bdo\b)\s*" + STDIN_EATERS, _body) and not re.search(r"<\s*/dev/null", _body):
        findings.append(
            "a `while ... read` loop whose body calls a stdin-reading command (ssh/az/kubectl/...) "
            "without `</dev/null`. That command consumes the loop's input, so the loop silently "
            "processes only the FIRST item and still exits 0. Add `< /dev/null` to the inner command."
        )
        break

# RULE-ID: vault-secret-to-stdout
# `vault token lookup` prints the token id in FULL, in every output format it has — the table, and
# `-format=json` too. There is no verbosity flag that omits it. So the command that feels like
# "check my auth" is unconditionally a credential write to the transcript, and a transcript is not
# somewhere a credential can be un-published.
#
# Same shape one step over, and this is the one with the real blast radius: bare `vault kv get
# <path>` and `vault read <path>` dump EVERY field's value as a table. That is the deny-list failure
# from `print-names-not-values` with no deny-list at all — whatever the path happens to hold is
# printed, including the coinage nobody thought to guard.
#
# BOTH fired in one session, opening work on a new project. The parent ran `vault token
# lookup` to confirm reach and put a long-lived admin token into permanent scrollback. Forty minutes
# later a SUBAGENT — briefed in writing to use `-field=` and never print a value — ran
# a bare `vault kv get <app-secrets>` and dumped every live credential at that path into its own
# transcript. The brief was correct, resident, and specific, and it did not hold. That is the whole
# argument for gating this rather than writing it down again: prose had already failed at the exact
# moment it was being followed everywhere else.
#
# GATED because it is provable from the string alone, unlike the `kubectl get secret` case that
# `print-names-not-values` deliberately leaves ungated: there the hazard is the DOWNSTREAM consumer
# (`| base64 -d` versus `| jq 'keys'`), which a command string cannot judge. Here the leak is in the
# vault invocation itself and needs no accomplice.
#
# The escapes are the idioms you should be using anyway, which is what keeps this from being the
# kind of false positive that gets a gate switched off:
#   -field=<name>   names the ONE field you decided to see, and assigns cleanly into a var
#   > file          it lands on disk rather than in the transcript
#
# A PIPE IS NOT AN ESCAPE, and the first version of this rule got that wrong. The reasoning that
# failed: "the gate cannot judge the downstream consumer, so defer." True for `kubectl get secret`,
# where the deny-worthy step is a decoder. False here — `vault kv get` has ALREADY rendered every
# value as plaintext by the time anything downstream runs, so the pipe target decides only how much
# of the dump you see, not whether it is a dump. `| head -30`, `| tail`, `| cat`, `| less` and
# `| grep <key>` all print secrets.
#
# Caught by checking the rule against the very leak that motivated it, which it would have ALLOWED:
# `vault kv get <app-secrets> 2>&1 | head -30` — every key, header included, under the
# 30-line cut. A gate written from the summary of an incident rather than from its
# command string is a gate that does not stop that incident.
_vault_sub = re.search(r"\bvault\s+(?:token\s+(?:lookup|create|renew)|print\s+token)\b", cmd)
_vault_get = re.search(r"\bvault\s+(?:kv\s+get|read)\b", cmd)
# The redirect escape must mean "stdout to a file", NOT any `>` in the string. A bare `>` test
# matches the `>` inside `2>&1`, which is a STDERR redirect and redirects no secret anywhere — so
# `vault kv get <path> 2>&1 | head -30`, the literal leak this rule exists for, sailed through a
# second time. Require a `>` that is neither preceded by a descriptor digit / `&` nor followed by
# `&`. Found by running the leak's own command string against the fixed rule instead of assuming
# the fix worked: the suite said FAIL on the two cases that mattered and PASS on everything else.
#
# AND THE ESCAPE ITSELF IS A HOLE, WHICH IS NOT THIS RULE'S TO CLOSE. A file is not the transcript,
# so exempting a redirect is right — and nothing here can see what the NEXT command does with the
# file. Measured: `vault kv get ... > f.json; python3 -c "...print(v)"` is this
# exemption working exactly as designed and a live credential in the transcript anyway. The
# backstop is `secret-redact.py`'s provenance pass, which redacts field VALUES in the output of any
# command that read a secret store (vault or bao), whatever the values look like — see its `_SECRET_STORE_READ_RE`
# block. Do not try to reproduce that here: it needs the output, and this hook only has the string.
if (_vault_sub or _vault_get) and not re.search(r"-field=|(?<![0-9&])>(?!&)", cmd):
    findings.append(
        "`%s` writes secret VALUES to stdout, and stdout here is a permanent transcript. "
        "`vault token lookup` prints the token id in every format including `-format=json`; a bare "
        "`vault kv get <path>` prints every field that path holds, guarding nothing. Name the one "
        "field you meant to see (`-field=ttl`), capture it "
        "(`X=\"$(vault kv get -field=FOO secret/p)\"`), redirect to a file, or pipe through a "
        "keys-only extractor."
        % (_vault_sub or _vault_get).group(0)
    )

# RULE-ID: glab-ci-list-b-is-a-date
# `glab ci list -b <branch>` reads as "branch" and is `--updated-before`, which wants ISO 8601.
# glab rejects it with `Parsing time "my-feature" as "2006-01-02T15:04:05Z"` — and inside a
# poll loop that error is swallowed by whatever greps the output. Measured: a watch
# loop ran 40 iterations printing `status=none`, which reads as "the pipeline has not appeared
# yet" rather than "this command has never once run", and spent ten minutes waiting on nothing.
# The branch flag is `-r` / `--ref`. `-b` reading as "branch" is the natural guess because that
# is what it means in git and in glab's own `mr`/`repo` subcommands.
#
# Fires ONLY on a literal that is not a date: a real `--updated-before 2026-01-01T00:00:00Z` and
# any `-b "$SINCE"` are left alone, because a gate with false positives gets switched off.
_gb = re.sub(r"`[^`]*`", " ", raw_cmd)
_gbm = re.search(
    r"(?m)(?:^|[;&|])\s*glab\s+(?:ci|pipeline)\s+list\b[^|;&]*?\s-b\s+['\"]?([^\s'\"]+)", _gb)
if _gbm and not re.match(r"^(?:\d{4}-\d{2}|\$|-)", _gbm.group(1)):
    findings.append(
        "`glab ci list -b %s` — `-b` is `--updated-before` (an ISO 8601 DATE), not a branch flag. "
        "glab fails with a time-parse error, and in a poll loop that error is swallowed by "
        "whatever reads the output, so every iteration reports a clean-looking nothing. The ref "
        "flag is `-r`: `glab ci list -r %s`." % (_gbm.group(1), _gbm.group(1))
    )

# RULE-ID: ssh-command-v-path
# `command -v <tool>` (or `which`) run over ssh. A non-interactive ssh shell never sources the
#     profile that puts ~/.local/bin on PATH, so a correctly-installed tool reports as MISSING — and
#     the caller reads that as "not installed" rather than "wrong probe". Hit repeatedly on a
#     second machine; most recently it produced a confident "claude is not installed on that host"
#     about a binary sitting at ~/.local/bin/claude, which nearly became a documented platform
#     limitation. Directly relevant: user-installed CLIs often live in ~/.local/bin, so the wrong answer is the one this probe gives by default.
#     A BARE `command -v` is correct in an interactive shell and stays ungated — the skill says so
#     deliberately. What is gateable is the ssh-wrapped form, where the string itself proves the
#     shell is non-interactive. A login shell (`bash -lc`, `zsh -lc`) DOES source the profile, and an
#     explicit `source`/`.` of a profile does too, so both are excluded.
#
#     MENTION VS USE, fixed on first contact: as imported this fired on
#     `echo "...about command -v / ssh..."; grep -n "command -v|which " SKILL.md` — documentation of
#     the rule, with no ssh invocation anywhere. Same shape `pgrep-f-self-match` already solved here:
#     a rule worth enforcing gets quoted in prose, so the ban and the explanation are one string.
#     The fix is NOT to blank quoted spans generally — the real trap puts `command -v` inside quotes
#     too, as ssh's remote-command argument. The asymmetry is that a real invocation has `ssh` itself
#     in COMMAND position: bare, outside quotes. A mention has it inside them. So the `ssh` test runs
#     against the quote-blanked string and the probe test against the raw one.
#
#     MENTION VS USE, SECOND SPELLING: the above fixed the mention of `ssh` and left
#     the mention of `which` — which is an ENGLISH RELATIVE PRONOUN, so any prose containing it fired
#     whenever a real ssh ran anywhere in the same command string. Caught on
#     `ssh host 'sha256sum …'; grep -c "trap 5, which sometimes wants" <file>` — a real ssh, a real
#     grep, and `which sometimes` matching `which\s+\S`. Note this is the WORSE half: the earlier bug
#     needed the whole command to be documentation, this one needs only one English clause anywhere
#     near an ssh, which is ordinary prose in an ordinary `echo` or `grep`.
#
#     The discriminator is COMMAND POSITION, the same asymmetry the `ssh` half already uses: shell
#     `which` opens a statement or is the first word of ssh's quoted remote command, so it follows a
#     separator or a quote. English `which` follows a comma or a word. `command -v` needs none of
#     this — it has no English sense — so that arm is left at a bare word-boundary match and keeps
#     full coverage.
#
#     KNOWN GAP, deliberate and documented rather than silently accepted: `ssh host which glab` with
#     the remote command UNQUOTED is no longer caught, because there `which` follows a hostname —
#     a bare word, indistinguishable from prose by this test. The quoted forms (both `"` and `'`),
#     which are how the trap has actually arrived every time, still block. Widening it back to catch
#     the unquoted form reinstates the false positive above, and a gate that fires on ordinary prose
#     gets switched off, which costs more than this gap.
_cmdv_bare = blank_quoted(cmd)
if (re.search(r"\bssh\b", _cmdv_bare)
        and (re.search(r"\bcommand\s+-v\s+\S", cmd)
             or re.search(r"""(?:^|[;&|(\n"'`]|\$\()\s*which\s+\S""", cmd))
        and not re.search(r"\b(?:ba|z)?sh\s+-[a-z]*l[a-z]*c?\b", cmd)
        and not re.search(r"""(^|[;&|\s"'])(?:source|\.)\s+\S*(?:profile|bashrc|zshrc|environment)""", cmd)):
    findings.append(
        "`command -v` / `which` over ssh: a non-interactive remote shell does not source the profile "
        "that adds ~/.local/bin to PATH, so an installed tool reports MISSING and the zero reads as a "
        "fact about the world. Test the real path instead (`test -x \"$HOME/.local/bin/<tool>\"`), or "
        "force a login shell (`ssh host 'bash -lc \"command -v <tool>\"'`)."
    )

# RULE-ID: talosctl-dryrun-context-secrets
# `talosctl apply-config/patch/edit --dry-run` prints a unified diff of the machine config, and a
# unified diff carries unchanged CONTEXT lines around each hunk. Machine config is where the cluster
# CAs live, keys included, so a hunk near them prints them: adding
# `cluster.etcd.extraArgs` put `cluster.etcd.ca.key` (a live etcd CA private key) on the
# terminal. The secret-redact hook removed it from the model's context; it did not remove it from the
# screen. `| grep -v WARNING`, the reflex filter, keeps every context line.
#
# Provable from the string: the leak needs no downstream accomplice, the diff itself is the dump. The
# escapes are what you want anyway — keep only changed lines (`| grep -E '^[+-][^+-]'`, which drops
# the `---`/`+++` headers too) or send it to a file. `--dry-run=false` is not a dry run. upgrade-k8s
# and rotate-ca are left ungated: their dry runs print manifests/summaries, not the machine config.
_talos_dry = re.search(
    r"\btalosctl\b[^\n|;&]*\b(?:apply-config|apply|patch|edit)\b[^\n|;&]*--dry-run(?!=false)\b", cmd
)
if _talos_dry and not re.search(r"\|\s*(?:grep|rg)\b[^\n|]*\^\[\+-\]|(?<![0-9&])>(?!&)", cmd[_talos_dry.end():]):
    findings.append(
        "`talosctl ... --dry-run` prints a unified diff of the machine config, and its unchanged "
        "CONTEXT lines include whatever sits near your hunk — CA private keys live in that config "
        "(an etcd patch printed `cluster.etcd.ca.key`). `| grep -v WARNING` keeps them. Filter to "
        "changed lines: `... --dry-run 2>&1 | grep -E '^[+-][^+-]'`, or redirect to a file."
    )

# RULE-ID: exec-stdin-without-i
# `kubectl exec` / `podman exec` / `docker exec` fed stdin (a heredoc, a `<` redirect, or a pipe)
#     without `-i`/`--stdin`. Stdin is never attached, so the remote command reads nothing, prints
#     nothing and exits 0 -- a psql heredoc of EXPLAINs "completed with no output" and
#     read as an empty result. Matched against the quote-blanked string so a quoted mention of the
#     shape does not fire; the heredoc line itself survives strip_heredocs (only bodies are dropped).
_exec_bare = blank_quoted(cmd)
for _seg_m in re.finditer(r"(\|\s*)?\b(?:kubectl|podman|docker)\b[^|;&\n]*?\bexec\b([^|;&\n]*)", _exec_bare):
    _piped_in, _rest = _seg_m.group(1), _seg_m.group(2)
    _flags = _rest.split(" -- ", 1)[0]
    if re.search(r"(?:^|\s)(?:-[a-zA-Z]*i[a-zA-Z]*|--stdin(?:=true)?)(?=\s|$)", _flags):
        continue
    if _piped_in or re.search(r"<<-?\s*\S|(?:^|\s)<\s*\S", _rest):
        findings.append(
            "`kubectl/podman/docker exec` fed stdin without `-i`: stdin is not attached, so the "
            "command inside reads nothing, prints nothing and exits 0. Add `-i` (`kubectl exec -i "
            "<pod> -- ...`)."
        )
        break

# RULE-ID: kill-every-container
# A mass kill/stop/rm of EVERY container (`podman ps -q | xargs podman kill`, `podman rm -f $(podman ps -aq)`)
# on a shared box takes out other sessions' and the operator's containers with no error — a bug-hunt finder
# cleaning up after itself did exactly this, and a container from outside the hunt was gone afterwards. Target
# your own: by name, or with `--filter` (name=, label=, id=) on the ps. A filter by image (`ancestor=`) or state
# selects everyone's too: an agent's `podman kill $(podman ps -q --filter ancestor=<image>)` killed
# other agents' runs of the shared test image.
_ctr = r"(?:podman|docker)"
_own = r"""(?:--filter|-f)[\s=]+['"]?(?:name|label|id)="""
_ps_unfiltered = r"%s\s+ps\b(?![^|;&)]*%s)[^|;&)]*\s-[a-zA-Z]*q" % (_ctr, _own)
if (re.search(_ps_unfiltered + r"[^|;&)]*\|\s*xargs\s+(?:-\S+\s+)*%s\s+(?:kill|stop|rm)\b" % _ctr, cmd)
        or re.search(r"%s\s+(?:kill|stop|rm)\b[^;&|]*\$\(\s*%s" % (_ctr, _ps_unfiltered), cmd)):
    findings.append(
        "kills/removes EVERY container: an unfiltered `ps -q` feeding kill/stop/rm takes out other sessions' "
        "containers too, silently. Target your own by name, or add `--filter name=<yours>` (or label=) to the ps."
    )

# RULE-ID: preprinted-empty-verdict
# A probe (`grep`, `dig`, `find`, `kubectl ...`) on one line, and a LATER statement in the SAME command
#     string that declares what an empty result would MEAN: `echo "(empty = not implemented)"`.
#     None of the echo/formatter rules see it: the command is read-only and asserts no success.
#
#     Being in the same command string is the whole proof: the interpretation was composed before
#     the output existed, so it can only encode the guess. When the probe happens to return what was
#     predicted, nothing downstream can tell the label from a measurement.
#
#     Measured in one session: four times in one session, the last three after the lesson had been
#     written into `no-fabricated-certainty`; twice the probe returned data and the label was false.
#
#     Deliberately narrow, because a gate with false positives gets switched off:
#       - the echo must name EMPTINESS (`empty`, `blank`, `nothing`, `no matches`...).
#       - it must also carry an INTERPRETATION connector (`=`, `means`, `indicates`, `->`).
#         `echo "no matches found"` is a report, not a pre-declared verdict, and stays allowed.
#       - `===` is excluded from the `=` connector, or every `=== header ===` would match.
#       - a probe must appear in an EARLIER statement; a bare echo on its own is not this trap.
#     Fix: run the probe, READ the output, then say what it showed. For a control, assert it
#     (`test -s out || echo "PROBE BROKEN"`) rather than glossing a blank in advance.
_PROBE_VERB = re.compile(
    r"\b(?:grep|rg|egrep|fgrep|dig|find|comm|diff|jq|az|kubectl\s+get|curl|host|nslookup"
    r"|git\s+(?:log|grep|diff|branch))\b"
)
_EMPTY_VERDICT = re.compile(
    r"^\s*echo\s+.*?"
    r"\b(?:empty|blank|nothing|none|"
    r"no\s+(?:files?|matches?|results?|output|hits?|rows?|lines?|entries|records?))\b"
    r"[^'\"]{0,40}?"
    r"(?:(?<!=)=(?!=)|\bmeans\b|\bindicates\b|->|→)",
    re.I,
)
_seq_pv = re.split(r"(?:;|\n|&&|\|\|)", cmd)
for _i, _st in enumerate(_seq_pv):
    if _EMPTY_VERDICT.match(_st) and any(_PROBE_VERB.search(_p) for _p in _seq_pv[:_i]):
        findings.append(
            "An `echo` in the SAME command string as the probe, pre-declaring what an EMPTY result "
            "would mean (`echo \"(empty = not implemented)\"`). The interpretation was written "
            "before the output existed, so it encodes your guess — and when the probe returns what "
            "you predicted, nothing downstream can tell that label from a measurement. Run the "
            "probe, READ the output, then state what it showed. For a control, assert it "
            "(`test -s out || echo \"PROBE BROKEN\"`) instead of glossing a blank in advance."
        )
        break

# RULE-ID: volume-prune-unfiltered
# `podman volume prune` (or `system prune --volumes`) deletes EVERY volume no container references, on the
# whole box: the operator's and other sessions' kept named volumes too, not the one you just orphaned. An agent
# ran `podman rm -f -v <its pg>; podman volume prune -f >/dev/null` to tidy up after a test database
# and could not say afterwards what it had deleted. `rm -v` already removes that container's anonymous volumes;
# anything else is `podman volume rm <name>`, or prune with `--filter label=<yours>`.
if (re.search(r"%s\s+volume\s+prune\b(?![^;&|]*--filter)" % _ctr, cmd)
        or re.search(r"%s\s+system\s+prune\b(?=[^;&|]*--volumes)(?![^;&|]*--filter)" % _ctr, cmd)):
    findings.append(
        "`volume prune` / `system prune --volumes` deletes every unreferenced volume on the box, other "
        "sessions' and the operator's included. `podman rm -v` already took your container's anonymous "
        "volumes; remove anything else by name (`podman volume rm <name>`) or prune with `--filter label=<yours>`."
    )

if not findings:
    sys.exit(0)

sys.stderr.write(
    "Blocked by bash-footgun-gate — these fail SILENTLY, so the result would look fine:\n\n"
    + "\n".join("  - " + f for f in findings)
    + "\n\nFull catalog: the `shell-footguns` skill. Reissue the command using the suggested form."
    # NOT a detection heuristic — detecting "this is a test" from the command string would cost
    # false positives, and a gate with those gets switched off. Printed unconditionally, because
    # by the time it matters the block has already fired: one line of stderr, landing exactly when
    # someone is stuck. This trap recurred across sessions with the remedy
    # sitting in a skill nobody had open — the definition of prose not working.
    + "\n\nTesting this gate? Then this block is expected — the pattern is in your command string,"
    + "\nso the gate fires on the harness rather than on the case. Put each case in a FILE and feed"
    + "\nit on stdin; that is why `test-gate.sh` is immune:"
    + "\n    printf '%s' '{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"<case>\"}}' > /tmp/c.json"
    + "\n    bash path/to/bash-footgun-gate.sh < /tmp/c.json; echo \"rc=$?\""
    + "\nOr just add the case to `test-gate.sh` and run that.\n"
)
sys.exit(2)
PY
rc=$?
# Propagate only the deliberate block; never fail a command because of a bug in this gate.
[ "$rc" -eq 2 ] && exit 2
exit 0
