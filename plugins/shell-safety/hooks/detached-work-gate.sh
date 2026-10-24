#!/usr/bin/env bash
# hook-version: 4   # bump on any behaviour change
# Stop: if this session detached work and never armed a waiter, say so before it ends.
#
# WHY THIS EXISTS: `nohup`/`setsid` returns instantly, so unless the HARNESS is tracking something —
# a `run_in_background` shell, or a `Monitor` — nothing will ever wake the session. The job finishes
# into a log nobody reads and the turn just stops with the work half-done. The operator has had to
# come back and ask "is that finished?" across more than one machine, which is exactly the prompting
# a hook is supposed to remove.
#
# MEASURED, on the two machines that hit it (1711 transcripts): 56 sessions detached with
# nohup/setsid; 33 armed neither waiter; 25 of those were real long-running work rather than
# tunnels — an image build, media transcodes, fan-out harvesters, a node reboot.
#
# WHY NOT A PreToolUse GATE: `nohup kubectl port-forward &` is correct and you never want waking for
# it, so no command string separates the good case from the bad one. The distinction is intent, and
# intent is only legible at the END — which is precisely when a Stop hook runs. Tunnel-style commands
# are excluded outright so the common legitimate detach never nags.
#
# LOOP SAFETY: honours stop_hook_active and fires at most once per session.
#
# LIMIT, stated so it is not over-trusted: "a waiter exists" is session-wide, not matched to the
# specific job. A session that backgrounds anything at all satisfies it. That errs toward silence on
# purpose — a gate that nags gets switched off, and a switched-off gate protects nothing.
set -uo pipefail

payload=$(cat 2>/dev/null || true)
[ -z "$payload" ] && exit 0

PAYLOAD="$payload" python3 - <<'PY'
import json, os, re, sys, pathlib

try:
    d = json.loads(os.environ.get("PAYLOAD") or "{}")
except ValueError:
    sys.exit(0)

# Never re-fire into our own continuation: that is how a Stop hook loops.
if d.get("stop_hook_active"):
    sys.exit(0)

tp = d.get("transcript_path") or ""
if not tp or not os.path.exists(tp):
    sys.exit(0)

session = d.get("session_id") or os.path.basename(tp)
stamp = pathlib.Path(os.path.expanduser("~/.claude/.detached-checked")) / f"{session}"
stamp.parent.mkdir(parents=True, exist_ok=True)
if stamp.exists():          # one nudge per session, then never again
    sys.exit(0)

DETACH = re.compile(r'\bnohup\b|\bsetsid\b|\bdisown\b')
# A backgrounding `&`, once the things that only LOOK like one are removed: `&&`, and fd dups such
# as `2>&1` / `<&3`.
_BG = re.compile(r'&&|\d*>&\d*|\d*<&\d*')


def _continues(ln):
    """True only if the line ends in an ODD number of backslashes immediately before the newline.
    `foo \\ ` is an escaped SPACE and `foo \\\\` an escaped backslash — neither continues the line, and
    the obvious `ln.rstrip().endswith(chr(92))` gets both wrong: rstrip() deletes the significant
    trailing space and endswith cannot count. Getting it wrong makes the splice OVER-join, which
    manufactures exactly the false positive the backgrounding predicate removed."""
    ln = ln.rstrip("\r")          # CRLF only — a trailing SPACE is significant
    return (len(ln) - len(ln.rstrip("\\"))) % 2 == 1


def logical_lines(cmd):
    """Split on newlines, but SPLICE shell line-continuations first.

    Per-line evaluation is what makes the backgrounding predicate work, and it is also what breaks a
    real detach written across a continuation — keyword on one physical line, `&` on the next, so
    neither line carries both and the gate goes silent on genuinely detached work. A continuation is
    a LEXICAL artifact of how the command was typed; the predicate is a SEMANTIC claim about what it
    does. Evaluating the second at the granularity of the first is the defect. This adds nothing to
    any ignore-list.

    Does NOT track quote state: a plain embedded newline inside a quoted string can still split a
    keyword from its `&` with no backslash at all. Untested and unfixed — full quote tracking needs a
    real lexer, which is disproportionate for a gate whose failure mode is a missed nudge."""
    out, buf = [], ""
    for ln in cmd.splitlines():
        if _continues(ln):
            buf += ln.rstrip("\r")[:-1] + " "
        else:
            out.append(buf + ln.rstrip("\r")); buf = ""
    if buf:
        out.append(buf)
    return out


def backgrounds(line):
    """The keyword alone was never the signal. `nohup foo` in the FOREGROUND blocks the tool call,
    so the harness tracks it and it is not the failure this gate exists to catch; the failure is
    specifically detached-AND-unwaited, which always carries a `&`. Requiring one is therefore not a
    false-positive filter bolted on — it is the rule the gate should have had. It is also what
    separates a command from a MENTION of one: prose, docs and fixtures name the keyword, they do
    not background anything."""
    return "&" in _BG.sub(" ", line)
# Legitimate fire-and-forget: a tunnel is used immediately, never waited on.
TUNNEL = re.compile(r'port-forward|kubectl proxy|ssh +-[NfLD]')

detached, waited, saw_any_tool = [], False, False
saw_any_assistant = False
try:
    lines = pathlib.Path(tp).read_text(errors="replace").splitlines()
except OSError:
    sys.exit(0)

for ln in lines:
    try:
        m = json.loads(ln)
    except ValueError:
        continue
    content = (m.get("message") or {}).get("content")
    if not isinstance(content, list):
        continue
    saw_any_assistant = True
    for c in content:
        if not isinstance(c, dict) or c.get("type") != "tool_use":
            continue
        saw_any_tool = True
        name, inp = c.get("name", ""), (c.get("input") or {})
        if name == "Monitor":
            waited = True
            continue
        if name != "Bash":
            continue
        if inp.get("run_in_background"):
            waited = True
            continue
        cmd = inp.get("command", "") or ""
        # A SPECIMEN is not an instance. Stripping `#` comment lines was the first attempt at
        # this and was too narrow by half: it caught `# nohup ...` and then fired, the same day, on
        # an ordinary heredoc writing a DOCUMENT whose prose named the keyword — the document
        # describing this very trap. Prose is not a comment line, and no amount of comment-detection
        # would have covered it.
        #
        # Both are handled by asking the right question instead: not "does the word appear" but
        # "is anything actually backgrounded on that line". Evaluated per line, so a real detach
        # sitting under a comment, or beside a tunnel, is still caught.
        for ln in logical_lines(cmd):
            if ln.lstrip().startswith("#"):
                continue
            if DETACH.search(ln) and backgrounds(ln) and not TUNNEL.search(ln):
                detached.append(cmd)
                break

if not saw_any_tool and not saw_any_assistant:
    # NOTHING parsed — not even an assistant turn with a content list. That means the parser
    # matched nothing at all, which a transcript format change would also cause, and inert reads
    # exactly like clean. Say it once, non-blocking.
    #
    # Deliberately NOT triggered by "parsed fine, but there were no tool calls". A brand-new
    # session, or one that only ever answered in prose, legitimately has zero tool_use entries and
    # is not evidence of a broken gate. Reporting INERT there fired on a freshly-created peer
    # session that had replied to a single "test" — a false alarm on the operator's screen, which
    # is the cry-wolf failure this gate is otherwise careful to avoid. If assistant turns parsed,
    # the parser demonstrably works; no tool calls simply means no tool calls.
    stamp.write_text("inert\n")
    sys.stderr.write("── detached-work gate ── nothing parsed from the transcript at all "
                     "(not even an assistant turn); this gate is INERT, not clean.\n")
    sys.exit(3)

if waited or not detached:
    sys.exit(0)

stamp.write_text("fired\n")
sys.stderr.write(
    "This session detached %d command(s) with nohup/setsid but never armed a waiter — no "
    "Monitor, and no Bash call with run_in_background. Nothing will wake you when they finish.\n\n"
    "  …%s…\n\n"
    "Before finishing: confirm the work actually completed (read its log / check the output file), "
    "or arm a waiter now — `run_in_background` on a polling loop, or a `Monitor`. The waiter is a "
    "SEPARATE call from the launch; the nohup exec itself returns instantly and must not be the "
    "thing you background. If it was fire-and-forget and you do not care, say so explicitly. "
    "One nudge per session; this will not fire again.\n"
    % (len(detached), detached[-1][:200].replace("\n", " ").strip())
)
sys.exit(2)
PY
rc=$?
# Only the deliberate nudge propagates; a bug in this hook must never wedge a session.
[ "$rc" -eq 2 ] && exit 2
# 3 = the gate is inert. Non-blocking, but exit 1 is what puts the line in front of the operator —
# on exit 0 the harness discards stderr and the warning would be invisible.
[ "$rc" -eq 3 ] && exit 1
exit 0
