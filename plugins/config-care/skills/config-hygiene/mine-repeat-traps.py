#!/usr/bin/env python3
"""Find traps that keep biting ACROSS sessions — especially ones already written down.

Companion to `mine-failures.py` in the shell-footguns skill, which ranks shell ERROR strings.
This one exists because the worst failures in this setup produce no error at all: a sync job that
adopted an incoming file onto the wrong record and deleted the one already there exited 0, printed
nothing, and was visible only as a file size that looked wrong. Grepping for error text cannot see
that class.

What it can see is the moment the mistake is NOTICED. When a documented trap is hit, the transcript
says so in the assistant's own words — "that's my bug", "the probe is broken", "exactly the trap the
skill documents", "same failure shape as". Those phrases mark *recognised* mistakes, which is
precisely the population worth gating, and they are stable enough to match.

The load-bearing output is the DOCUMENTED-AND-STILL-HIT list: a trap written into a skill or memory
that still recurs is proof the prose is not working, and that it needs a gate instead. That is the
whole argument of the shell-footguns rewrite, applied generically.

    python3 mine-repeat-traps.py             # ranked, with the documented-anyway set first
    python3 mine-repeat-traps.py --days 30   # window
    python3 mine-repeat-traps.py --quiet     # one summary line, for a SessionStart nudge

LIMITS, stated because a checker that overstates itself is worse than none:
  - It only sees mistakes that were noticed and named. A silent failure nobody caught leaves nothing.
  - Phrase matching is a proxy for "a mistake happened"; it will miss rewordings and catch the odd
    quotation. Treat counts as a ranking signal, not a measurement.
"""
import argparse
import collections
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.expanduser("~/.claude/projects")
SKILLS = os.path.expanduser("~/.claude/skills")
# The gate ships in the shell-safety plugin; also accept a copy installed into ~/.claude/hooks/.
HOOK = next(iter(sorted(glob.glob(os.path.expanduser("~/.claude/plugins/cache/*/shell-safety/*/hooks/bash-footgun-gate.sh")))),
            os.path.expanduser("~/.claude/hooks/bash-footgun-gate.sh"))

# Phrases that mark a RECOGNISED mistake in the assistant's own output. Deliberately narrow:
# these should not fire on ordinary hedging, only on an admission that something went wrong.
MISTAKE = [
    # Qualifiers are the common miss: "my ps probe was simply wrong" / "the probe was the wrong
    # instrument" both read as admissions and both slipped a tighter version of this pattern.
    # Two shapes, because the copula form misses the commonest phrasing. "my probe WAS broken" is
    # someone stopping to state it; "my own broken probe" is someone referring to it in passing
    # while moving on — and the passing mention is the frequent one, precisely because it is not
    # being dwelt on. The pattern was blind to the low-ceremony half of the signal.
    ("self-inflicted probe error", r"\b(my) (?:\w+ ){0,2}(probe|regex|filter|loop|check|command|script|parser|parsing) (?:\w+ ){0,2}(?:was|is|were|being) (?:\w+ ){0,2}(broken|wrong|bad)|\b(?:my|our) (?:own )?(?:\w+ )?(?:broken|bad|wrong|faulty|buggy|busted) (?:probe|regex|filter|loop|check|command|script|parser|grep|pattern|query|canary|measurement)\b"),
    ("bug in my own command",      r"\bthat(?:'s| is|'s) my (own )?bug\b|\bmy (own )?(bug|mistake|error)\b|\b(bug|mistake|error|flaw) in my own?\b"),
    # Measured on the stored corpus: the bare keyword list fired 22 times and exactly ONE was the
    # assistant admitting its own destructive edit. The other 21 were ordinary technical prose —
    # "the spinner tick doesn't re-clobber the clipboard", "the working install is destroyed" —
    # because a substring probe cannot tell a violation from a description of one. The lookahead
    # requires an i/my in the same sentence, which separated 1 from 21 cleanly.
    # DELIBERATE LOSS: "the edit clobbered the good copy" no longer matches. That phrasing never
    # occurred in the corpus as a genuine admission; 21 lookalikes did. self_test pins it as a
    # negative so the tradeoff stays visible instead of looking like an oversight.
    ("wrong-side / wrong-target",  r"(?=[^.\n]*\b(?:i|my)\b)[^.\n]*\b(clobber|clobbered|overwr(?:ote|itten)|destroyed|deleted what was there)\b"),
    ("repeat of a known trap",     r"\b(same (failure )?shape as|exactly the trap|the trap the skill|as the skill (warns|documents)|hit (it )?again)\b"),
    ("documented yet hit",         r"\b(documented|written down|already in the skill|already recorded)\b[^.\n]{0,60}\b(anyway|still|and (?:it )?still)\b"),
    # "I was wrong" is the rarest phrasing of this. The admission is usually attached to the THING
    # rather than the speaker — "my explanation was wrong", "that read was wrong" — which was the
    # single largest miss in the corpus.
    #
    # EVERY LITERAL HERE MUST BE LOWERCASE. Patterns are matched against text.lower() (see main()),
    # so a capital "I" makes that alternative unmatchable
    # — silently. Nothing errors; a label with other branches keeps firing, so the output looks
    # healthy while a signature is dead. "should have checked first" had exactly ONE alternative
    # and was therefore entirely dead, reporting zero forever, which is indistinguishable from a
    # trap you don't have. self_test() checks this mechanically.
    ("correcting a stated fact",   r"\bcorrect(?:ing|ion) to what i (said|reported)\b|\bthat corrects\b|\bi was wrong\b|\bmy(?: \w+){0,2} (?:was|were) wrong\b|\bi (?:overstated|understated)\b|\bcorrecting myself\b"),
    ("should have checked first",  r"\bi should have (read|checked|looked|used|verified|asked|run)\b"),
    ("silent/empty-result trap",   r"\b(returned|read as|looked like) (?:a )?(?:clean )?(zero|nothing|empty)\b[^.\n]{0,50}\b(but|when|rather than)\b"),
]

# Traps already committed to somewhere. A hit on one of these is the high-value signal — but only
# if the reference is SPECIFIC. Bare memory/skill FILENAMES were tried and dropped: they matched
# whenever a session merely discussed a memory by name, reporting "documented and still hit" for
# `knowledge-routing` and `distill-dont-dump` when nothing had been hit at all. A checker that cries
# wolf trains you to ignore it, so only distinctive strings qualify — a gate RULE-ID, or a skill
# heading long enough to be quoted rather than coincidental.
def known_traps():
    out = {}
    for r in re.findall(r"# RULE-ID: (\S+)", _read(HOOK)):
        out[r] = "gated"
    for f in glob.glob(SKILLS + "/*/SKILL.md"):
        name = os.path.basename(os.path.dirname(f))
        for h in re.findall(r"^\*\*(.{25,90}?)\.\*\*", _read(f), re.M):
            h = re.sub(r"[`*_]", "", h).strip().lower()
            if len(h.split()) >= 5:          # a phrase, not a label
                out.setdefault(h[:70], f"skill:{name}")
    return out


def _read(p):
    try:
        with open(p, encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def transcripts(days):
    cutoff = time.time() - days * 86400
    for p in glob.glob(ROOT + "/**/*.jsonl", recursive=True):
        try:
            if os.path.getmtime(p) >= cutoff:
                yield p
        except OSError:
            continue


def assistant_text(path):
    """Yield assistant text blocks; that is where an admission of a mistake lives."""
    with open(path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or '"assistant"' not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            msg = d.get("message") or {}
            for c in (msg.get("content") or []) if isinstance(msg.get("content"), list) else []:
                if isinstance(c, dict) and c.get("type") == "text":
                    yield c.get("text") or ""


# A gate BLOCK is a mistake the assistant never admits, because being stopped by your own
# gate does not feel like an error -- you reissue and move on. So the phrase list above can
# never see this class, and the one trap that recurred across sessions
# went unsurfaced until a human noticed. A block leaves a distinctive string in the transcript;
# that is the signal. Repeated blocks of the SAME rule across many sessions mean the gate is
# generating friction rather than only catching bugs -- worth a look, not automatically bad.
GATE_BLOCK = re.compile(r"Blocked by ([a-z0-9-]+gate[a-z0-9-]*)", re.I)


def gate_friction(days):
    per_gate = collections.Counter()
    sess = collections.defaultdict(set)
    for p in transcripts(days):
        sid = os.path.basename(p)
        try:
            body = _read(p)
        except Exception:
            continue
        for m in GATE_BLOCK.finditer(body):
            g = m.group(1).lower()
            per_gate[g] += 1
            sess[g].add(sid)
    return per_gate, sess


def self_test():
    """Prove the patterns can fire. Run with --self-test; exits 1 on any failure.

    Exists because this list has silently lost alternatives the same way more than once: patterns
    are matched against text.lower(), so a capital letter in a literal makes that alternative
    unmatchable. Nothing errors, and a label with other branches keeps firing — so the output
    looks healthy while a signature is dead. A comment saying "keep literals lowercase" is the
    shape that already failed, which is why this is executable instead.
    """
    bad = 0

    # 1. Mechanical: no uppercase literal in any pattern (bracket expressions like [A-Z] exempt).
    for label, pat in MISTAKE:
        stripped = re.sub(r"\[[^\]]*\]", "", pat)
        ups = [c for c in stripped if c.isupper()]
        if ups:
            print(f"  FAIL [{label}]: uppercase literal(s) {''.join(sorted(set(ups)))} "
                  f"— unmatchable against text.lower()")
            bad = 1

    # 2. Behavioural: each label must fire on a phrase, and NOT on its near-miss control.
    #    The negatives are the load-bearing half — a pattern rewritten to match everything would
    #    satisfy every positive and the uppercase check while destroying the signal.
    cases = [
        ("self-inflicted probe error", "my own broken probe returned zero",              True),
        ("self-inflicted probe error", "my regex was wrong",                             True),
        ("self-inflicted probe error", "the probe ran and the result was clean",         False),
        ("should have checked first",  "I should have checked the file first",           True),
        ("should have checked first",  "you should have the file already",               False),
        ("correcting a stated fact",   "I was wrong about that",                         True),
        ("correcting a stated fact",   "my earlier heuristic was wrong",                 True),
        ("correcting a stated fact",   "the report was accurate",                        False),
        ("bug in my own command",      "that was my own bug",                            True),
        ("bug in my own command",      "the upstream bug in their parser bit us",        False),
        ("documented yet hit",         "it was written down and it still fired",         True),
        ("documented yet hit",         "this is documented in the skill and works",      False),
        ("wrong-side / wrong-target",  "the edit clobbered the good copy",               False),
        ("wrong-side / wrong-target",  "the edit landed on the intended file",           False),
        # Positives proving the narrowed pattern still fires on a genuine admission.
        ("wrong-side / wrong-target",  "i overwrote my own notes file",                  True),
        ("wrong-side / wrong-target",  "my script clobbered the good copy",              True),
        # Verbatim shapes from real firings that were NOT admissions. These are the load-bearing
        # half: every pattern they guard still passes all of the positives above.
        ("wrong-side / wrong-target",  "the spinner tick doesn't re-clobber the clipboard", False),
        ("wrong-side / wrong-target",  "the working install is destroyed, rc=0",         False),
        ("wrong-side / wrong-target",  "i.e. the destroyed file was rebuilt",            False),
        ("correcting a stated fact",   "the two suspects were wrong suspects",           False),
        ("self-inflicted probe error", "the documented podman command is broken",        False),
        ("repeat of a known trap",     "that is the same shape as the earlier failure",  True),
        ("repeat of a known trap",     "this is a different failure mode entirely",      False),
        ("silent/empty-result trap",   "the probe returned zero but the file was there", True),
        ("silent/empty-result trap",   "the probe returned zero and that was correct",   False),
    ]
    pats = dict(MISTAKE)
    for label, text, want in cases:
        got = bool(re.search(pats[label], text.lower()))
        if got != want:
            print(f"  FAIL [{label}]: {'expected a match' if want else 'false positive'} "
                  f"on {text!r}")
            bad = 1

    # Every label must have at least one behavioural case, or the harness is not watching it.
    covered = {l for l, _, _ in cases}
    uncovered = [l for l, _ in MISTAKE if l not in covered]
    if uncovered:
        print(f"  FAIL: no behavioural case for {uncovered} — add one, or the self-test "
              f"reports green over a label it never exercised")
        bad = 1

    print("self-test:", "FAIL" if bad else f"ok — {len(MISTAKE)} patterns, {len(cases)} cases")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true",
                    help="verify the pattern list can actually fire, then exit")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())

    per_label = collections.Counter()
    sessions_per_label = collections.defaultdict(set)
    examples = collections.defaultdict(list)
    known = known_traps()
    doc_hits = collections.Counter()
    doc_sessions = collections.defaultdict(set)

    n_files = 0
    for p in transcripts(a.days):
        n_files += 1
        sid = os.path.basename(p)
        for text in assistant_text(p):
            low = text.lower()
            for label, pat in MISTAKE:
                if re.search(pat, low):
                    per_label[label] += 1
                    sessions_per_label[label].add(sid)
                    if len(examples[label]) < 3:
                        m = re.search(pat, low)
                        s = max(0, m.start() - 70)
                        examples[label].append(text[s:m.end() + 90].replace("\n", " ").strip())
            # a named trap mentioned in the same breath as a mistake marker
            if any(re.search(pat, low) for _, pat in MISTAKE):
                for trap, where in known.items():
                    if len(trap) >= 12 and trap in low:
                        doc_hits[(trap, where)] += 1
                        doc_sessions[(trap, where)].add(sid)

    gate_hits, gate_sess = gate_friction(a.days)
    repeats = {k: v for k, v in per_label.items() if len(sessions_per_label[k]) >= 2}
    docrepeat = {k: v for k, v in doc_hits.items() if len(doc_sessions[k]) >= 2}

    if a.quiet:
        if repeats or docrepeat:
            print(f"── repeat traps ── {len(repeats)} mistake signature(s) recurring across sessions"
                  f"{f', {len(docrepeat)} on ALREADY-DOCUMENTED traps' if docrepeat else ''}"
                  f" (last {a.days}d). Review: python3 {os.path.abspath(__file__)}")
        return

    print(f"scanned {n_files} transcript(s) over {a.days}d\n")
    if docrepeat:
        print("=== DOCUMENTED AND STILL HIT — prose is not working; gate these ===")
        for (trap, where), n in sorted(docrepeat.items(), key=lambda x: -x[1]):
            print(f"  {n:>3}x in {len(doc_sessions[(trap, where)])} session(s)  [{where}]  {trap[:70]}")
        print()
    print("=== recognised-mistake signatures, ranked by recurrence ===")
    for label, n in per_label.most_common():
        s = len(sessions_per_label[label])
        mark = "  <-- recurring" if s >= 2 else ""
        print(f"  {n:>3}x across {s:>2} session(s)  {label}{mark}")
        for ex in examples[label][:1]:
            print(f"        e.g. …{ex[:150]}…")
    gate_rep = {g: n for g, n in gate_hits.items() if len(gate_sess[g]) >= 3}
    if gate_rep:
        print("\n=== GATE FRICTION — a gate blocking repeatedly across sessions ===")
        print("    Not automatically bad: a gate that fires is usually a gate working. Read it as")
        print("    'go look' — a rule tripping constantly may be catching real bugs, may be firing")
        print("    on a shape nobody meant to write (e.g. your own test harness), or may have a")
        print("    block message that is not teaching the fix.")
        for g, n in sorted(gate_rep.items(), key=lambda kv: -kv[1]):
            print(f"  {n:>4}x across {len(gate_sess[g]):>3} session(s)  {g}")
    print("\nRouting (judgement, not automatable): a trap a command string can PROVE goes in "
          "bash-footgun-gate.sh with a test; one needing context goes in the owning skill; one about "
          "how you want work done goes in memory. See the knowledge-routing memory.")


if __name__ == "__main__":
    main()
