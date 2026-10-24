#!/usr/bin/env python3
"""Does relocation actually save money, once prompt caching is accounted for?

THE CHALLENGE (from published cache pricing, vendor doc): a resident prefix bills at 0.1x on every
read. Move content down a tier and each just-in-time load is fresh input at 1.0x (1.25x as a cache
write). So relocation could cost MORE than residency. If true, the whole pass was misconceived.

THE ARITHMETIC, done honestly rather than argued:

  resident      = B tokens paid at 0.10x on every request, + 1.25x once per cold prefix
  relocated     = B tokens paid at 1.25x once in each session that loads it, then 0.10x for the
                  remaining requests of that session only, and NOTHING in sessions that never load it

So the saving turns entirely on **f**, the fraction of sessions that load the destination — and on
WHERE in the session it loads. This measures f from the real transcript store instead of assuming it.

The conclusion is not foregone: for content whose destination loads in most sessions and loads early,
relocation genuinely is a loss, and this will say so.
"""
import argparse, collections, glob, json, os, time

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("days", nargs="?", type=int, default=60,
                help="window of transcript history to measure (default 60)")
ap.add_argument("--dests", default="k8s-triage,fanout-craft,cc-tool-vet,headless-render,shell-footguns",
                help="comma-separated skills you moved content INTO. The default is this machine's "
                     "last pass; replace it with your own destinations.")
a = ap.parse_args()

DAYS = a.days
CUTOFF = time.time() - DAYS * 86400
DESTS = [d.strip() for d in a.dests.split(",") if d.strip()]

sessions = 0
loads = collections.Counter()          # sessions in which the dest loaded at least once
pos = collections.defaultdict(list)    # fractional position of first load within the session

for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    try:
        if os.path.getmtime(f) < CUTOFF:
            continue
    except OSError:
        continue
    lines = open(f, errors="replace").readlines()
    n = len(lines)
    if n < 5:
        continue
    sessions += 1
    first = {}
    for i, line in enumerate(lines):
        if '"tool_use"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        for blk in (d.get("message") or {}).get("content") or []:
            if not isinstance(blk, dict) or blk.get("type") != "tool_use":
                continue
            inp = blk.get("input") or {}
            name = str(inp.get("skill", "")).strip()
            path = str(inp.get("file_path", ""))
            for dst in DESTS:
                if dst in first:
                    continue
                if (blk.get("name") == "Skill" and name == dst) or \
                   (blk.get("name") == "Read" and f"/skills/{dst}/" in path):
                    first[dst] = i / n
    for dst, frac in first.items():
        loads[dst] += 1
        pos[dst].append(frac)

print(f"  corpus: {sessions} sessions over {DAYS}d\n")
print(f"  {'destination':18} {'f (sessions loading it)':>24}  {'median position':>16}  {'relocation saves':>17}")
for dst in DESTS:
    k = loads[dst]
    f = k / sessions if sessions else 0
    p = sorted(pos[dst])[len(pos[dst]) // 2] if pos[dst] else None
    # Fraction of the resident bill avoided. When it loads at position p, the content is absent for
    # the first p of that session's requests and present for (1-p) of them.
    saved = 1 - (f * (1 - p)) if p is not None else 1.0
    ppos = f"{p:.0%} in" if p is not None else "never loaded"
    print(f"  {dst:18} {k:>5}/{sessions} = {f:>7.1%}  {ppos:>16}  {saved:>16.1%}")

print("""
  Read the last column as: the share of this content's resident cost that relocation avoids.
  Relocation is a LOSS only if it goes negative — which needs f near 1 AND an early load, i.e.
  content wanted in almost every session from the start. That is the definition of something that
  should have stayed resident, so the lookup-moment test already selects against it.

  The caveat that survives: this counts TOKENS, not round-trips. A just-in-time load also costs a
  tool call and the latency of it, which no cache discount touches.""")
