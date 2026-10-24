#!/usr/bin/env python3
"""Mine every session transcript for shell-level failures, ranked by recurrence.

This is how a new foot-gun earns a place in `bash-footgun-gate.sh`: not by someone remembering to
add it, but by showing up here often enough to be worth gating. The transcripts already record
every failure, so no extra logging hook is needed — the evidence accumulates for free.

    python3 mine-failures.py            # ranked signatures + examples
    python3 mine-failures.py globs      # break the top offender down by shape

Gate a signature when it is BOTH frequent AND statically detectable from the command string with no
legitimate false positive. `--include=*.py` qualifies: a flag value is never meant to be expanded.
A bare path glob (`/sys/block/sd*`) does not: sometimes you do want expansion.
"""
import json, glob, os, re, collections, sys

ROOT = os.path.expanduser("~/.claude/projects")

SIGS = [
    ("zsh: no matches found (unquoted glob)", r"no matches found"),
    ("command not found",                     r"command not found"),
    ("parameter not set / unbound",           r"(parameter not set|unbound variable)"),
    ("bad substitution",                      r"bad substitution|bad pattern"),
    ("zsh: event not found (! in dquotes)",   r"event not found"),
    ("bad math expression",                   r"bad math"),
    ("permission denied",                     r"[Pp]ermission denied"),
    ("no such file or directory",             r"[Nn]o such file or directory"),
    ("syntax error near unexpected",          r"syntax error near"),
    ("unexpected EOF / unmatched quote",      r"unexpected EOF|unmatched [\"']"),
    ("grep: invalid/unknown option",          r"grep: (invalid|unrecognized|unknown)"),
    ("argument list too long",                r"[Aa]rgument list too long"),
    ("heredoc delimiter",                     r"here-document|delimited by end-of-file"),
]


def results():
    """Yield (session_id, text) for every tool result carrying output."""
    for path in glob.glob(ROOT + "/**/*.jsonl", recursive=True):
        sid = path.rsplit("/", 1)[-1][:8]
        try:
            fh = open(path, errors="replace")
        except OSError:
            continue
        with fh:
            for line in fh:
                if '"toolUseResult"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except Exception:
                    continue
                tur = d.get("toolUseResult")
                if isinstance(tur, dict):
                    text = (tur.get("stderr") or "") + "\n" + (tur.get("stdout") or "")
                elif isinstance(tur, str):
                    text = tur
                else:
                    continue
                if text.strip():
                    yield sid, text


def rank():
    compiled = [(n, re.compile(rx)) for n, rx in SIGS]
    counts, sessions, examples = collections.Counter(), collections.defaultdict(set), collections.defaultdict(list)
    total = 0
    for sid, text in results():
        total += 1
        for name, rx in compiled:
            m = rx.search(text)
            if m:
                counts[name] += 1
                sessions[name].add(sid)
                if len(examples[name]) < 3:
                    s = max(0, m.start() - 60)
                    examples[name].append(re.sub(r"\s+", " ", text[s:m.end() + 70]).strip())
    print(f"scanned {total:,} tool results with output\n")
    print(f"{'signature':42} {'hits':>6} {'sessions':>9}")
    for name, n in counts.most_common():
        print(f"{name:42} {n:>6} {len(sessions[name]):>9}")
    print("\n--- examples (recurring only) ---")
    for name, n in counts.most_common():
        if n < 3:
            continue
        print(f"\n### {name}  ({n} hits / {len(sessions[name])} sessions)")
        for ex in examples[name]:
            print("   ", ex[:190])


def globs():
    rx = re.compile(r"no matches found:\s*(\S+)")
    vals = collections.Counter()
    for _sid, text in results():
        for m in rx.finditer(text):
            vals[m.group(1)] += 1
    total = sum(vals.values())
    if not total:
        # `or 1` here printed a total of 1 and a 0% breakdown — a missing measurement rendered as
        # an ordinary one. With no denominator there are no percentages, so say there is no data,
        # and say which of the two zeros it is.
        print("total 'no matches found': none in the scanned transcripts —")
        print("  no breakdown to report (this is an EMPTY sample, not a clean result;")
        print("  check that ROOT points at real transcripts before reading it as good news).")
        return
    flagval = sum(n for v, n in vals.items() if v.startswith("-") and "=" in v)
    print(f"total 'no matches found': {total}")
    print(f"  flag-value glob (gateable)   {flagval:>5}  ({flagval/total:.0%})")
    print(f"  other/path glob (not safely) {total-flagval:>5}  ({(total-flagval)/total:.0%})\n")
    for v, n in vals.most_common(20):
        kind = "FLAGVAL" if (v.startswith("-") and "=" in v) else "path"
        print(f"  {n:>4}x  [{kind:7}] {v[:70]}")


if __name__ == "__main__":
    (globs if len(sys.argv) > 1 and sys.argv[1] == "globs" else rank)()
