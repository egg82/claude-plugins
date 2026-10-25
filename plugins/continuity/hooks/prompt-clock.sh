#!/usr/bin/env bash
# hook-version: 5   # bump on any behaviour change
# UserPromptSubmit: stamp the wall clock and the gap since the operator's previous message, and nudge
# once per threshold when the context grows past 300k / 450k tokens (see the context section below).
#
# WHY THIS EXISTS: the model has NO clock. The system prompt injects a bare date ("Today's date is
# <YYYY-MM-DD>") once, with no time of day and no refresh, and nothing that wakes the session carries a
# timestamp. So a reply sent 20 seconds later and one sent the next morning are the same observation,
# and any sentence about elapsed time ("that was hours ago") is a guess rendered as an observation.
# Operator's observation: the model is poor at judging elapsed time (it says "that was hours ago"
# when it was 15 minutes).
#
# WHY NOT PROSE: it already was prose and it already failed. `verify-dont-anchor.md` has carried
# "'latest' or 'still happening' need the wall clock, not an assumption" for months; `date` was still
# never run, because the model does not FEEL the absence of a clock — nothing errors, the guess just
# looks like a fact. A rule that must fire on every turn belongs in something the harness executes.
#
# WHY A STATE FILE rather than reading the transcript: whether the incoming prompt has already been
# appended at hook time is a harness-internal ordering detail, so a transcript-derived gap would be
# right or off-by-one-turn depending on a thing that can change without notice. Two writes to our own
# file cannot be ambiguous.
#
# LIMIT, stated so it is not over-trusted: this covers HUMAN input only. Monitor fires, background
# shell completions and task notifications have no corresponding hook, so those wakes still arrive
# unstamped — that half needs Anthropic and is filed as feedback. The gap reported is prompt-to-
# prompt, which includes however long the previous turn's own work took; it is an upper bound on
# idle time, not a measurement of it.
set -uo pipefail

payload=$(cat 2>/dev/null || true)
[ -z "$payload" ] && exit 0

PAYLOAD="$payload" python3 - <<'PY'
import json, os, sys, time, pathlib

try:
    d = json.loads(os.environ.get("PAYLOAD") or "{}")
except ValueError:
    sys.exit(0)

sid = str(d.get("session_id") or "").strip()
if not sid or "/" in sid:
    sys.exit(0)

now = time.time()
state = pathlib.Path.home() / ".claude" / "state" / "prompt-clock"
try:
    state.mkdir(parents=True, exist_ok=True)
except OSError:
    sys.exit(0)

f = state / sid
prev = None
try:
    prev = float(f.read_text().strip())
except (OSError, ValueError):
    prev = None

try:
    f.write_text("%.3f\n" % now)
except OSError:
    pass  # a missing gap next turn beats failing the prompt

# Sweep our own droppings; sessions are many and short.
try:
    for old in state.iterdir():
        if old.is_file() and now - old.stat().st_mtime > 7 * 86400:
            old.unlink()
except OSError:
    pass


def human(sec):
    sec = int(sec)
    if sec < 90:
        return "%ds" % sec
    if sec < 5400:
        return "%dm" % round(sec / 60)
    if sec < 86400:
        h, m = divmod(round(sec / 60), 60)
        return "%dh" % h if not m else "%dh%dm" % (h, m)
    dd, h = divmod(round(sec / 3600), 24)
    return "%dd" % dd if not h else "%dd%dh" % (dd, h)


stamp = time.strftime("%Y-%m-%d %H:%M %Z (%a)", time.localtime(now))
if prev is None:
    gap = "first message of this session"
else:
    gap = "%s since your previous message" % human(max(0.0, now - prev))
    if time.localtime(prev).tm_yday != time.localtime(now).tm_yday:
        gap += " — different calendar day"

clock = "[clock] %s · %s" % (stamp, gap)

# ---- context size: the other thing the model cannot feel ------------------------------------------
# Every API call re-reads the whole context (cached, but billed), so a session at 450k costs ~10x a
# fresh one per turn, and compaction only partly resets it. Operator's observation: a large
# context uses far more tokens than starting a new session. The size is a number in the
# transcript (the last assistant record's usage), never a guess. One nudge per threshold per session.
# 200k fired at a fifth of a 1M window, too early; 500k/800k let overnight sessions run hundreds of
# millions of input tokens a day. This hook only runs on human prompts:
# postcompact-handoff.sh carries the hard mark across compactions (the harness also compacts sessions
# idle ~55min, before the cache expires) and resets the per-session state below. Keep HARD in sync there.
TIERS = (300_000, 450_000)
ctx = 0
try:
    with open(d.get("transcript_path") or "", encoding="utf-8", errors="ignore") as t:
        for line in t:
            if '"compact_boundary"' in line:  # usage before it is the old context, not this one
                try:
                    ctx = int((json.loads(line).get("compactMetadata") or {}).get("postTokens") or 0)
                except ValueError:
                    pass
                continue
            if '"usage"' not in line or '"assistant"' not in line:
                continue
            try:
                u = (json.loads(line).get("message") or {}).get("usage") or {}
            except ValueError:
                continue
            n = sum(int(u.get(k) or 0) for k in
                    ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens"))
            if n:
                ctx = n
except OSError:
    ctx = 0

tier = sum(1 for x in TIERS if ctx >= x)
tf = state / (sid + ".ctx")
try:
    told = int(tf.read_text().strip())
except (OSError, ValueError):
    told = 0

if tier > told:
    try:
        tf.write_text("%d\n" % tier)
    except OSError:
        pass
    k = "%dk" % round(ctx / 1000)
    mark = TIERS[tier - 1] // 1000
    if tier == 1:  # soft: an economy note, not a stop — the same handoff text here made every session quit at 500k
        shown = "Context is ~%s tokens; every turn re-reads all of it. Claude keeps working, more compactly." % k
        told_model = ("\n[context] ~%s tokens, past the %dk mark (soft). Keep working on the current task; "
            "this is not a reason to stop or hand off. Be economical: read files in ranges, filter command "
            "output, delegate wide sweeps to subagents. The hard mark at %dk is where to wrap up."
            % (k, mark, TIERS[-1] // 1000))
    else:
        shown = ("Context is ~%s tokens; every turn re-reads all of it. Claude will wrap up with a handoff "
                 "and continue in a fresh session." % k)
        told_model = ("\n[context] ~%s tokens, past the %dk mark (hard). At the next natural stopping point "
            "write the open state to ~/.claude/HANDOFF-<topic>.md and do not start new large work in this "
            "one. A handoff holds only what dies with this session: branches, worktrees, running or paused "
            "agents, half-done steps, agreements with peer sessions. The queue stays in the repo's own queue "
            "file (docs/open-work.md, NEXT.md...): update that and point to it, never copy it; carry a queue "
            "in the handoff only when the repo has none, and say so. If this harness can start a tracked session and work remains, start the fresh session "
            "yourself in a new labelled tab, briefed with the handoff, confirm it reached "
            "`working`, and tell the operator its name. Otherwise recommend a fresh session." % (k, mark))
    print(json.dumps({
        "systemMessage": shown,
        "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": clock + told_model},
    }))
else:
    print(clock)
PY
exit 0
