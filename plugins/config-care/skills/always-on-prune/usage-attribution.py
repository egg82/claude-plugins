#!/usr/bin/env python3
"""On a subscription, the thing being optimised is the WEEKLY USAGE BAR, not a dollar invoice.

So the right question is not "what does a resident KB cost" but "what share of consumed tokens is
the resident tier responsible for, against everything else in the context". This attributes real
consumption over the window and lets the prune be judged against the alternatives.

Resident tokens are re-sent on every request of every session AND every subagent, so their share is
    resident_tokens * total_requests / total_tokens_consumed
Everything else is conversation: tool results, file reads, prior turns, subagent reports.
"""
import argparse, collections, glob, json, os, re, time

_ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                              formatter_class=argparse.RawDescriptionHelpFormatter)
_ap.add_argument("days", nargs="?", type=int, default=30,
                 help="window to measure, in days (default 30)")
_ap.add_argument("--cut-bytes", type=int, default=None, metavar="B",
                 help="bytes a prune actually removed from pref BODIES on THIS machine; if given, "
                      "the run is scored against the measured window. Omitted by default because a "
                      "figure from someone else's prune is not a measurement of yours, and printed "
                      "unconditionally it reads exactly like one.")
_a = _ap.parse_args()
DAYS = _a.days
CUTOFF = time.time() - DAYS * 86400
# Per-request filter: a file touched in the window can hold days of older requests.
CUTOFF_ISO = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(CUTOFF))
CPT = 4.0  # chars per token, the one estimate; everything else is counted

def body_bytes(p):
    s = open(p, errors="replace").read()
    m = re.match(r"^---\n.*?\n---\n", s, re.S)
    return len(s) - (len(m.group(0)) if m else 0)

prefs = sum(body_bytes(p) for p in glob.glob(os.path.expanduser("~/.claude/memory/*.md")))
roster = 0
for p in glob.glob(os.path.expanduser("~/.claude/skills/*/SKILL.md")):
    m = re.search(r"^---\n(.*?)\n---", open(p, errors="replace").read(6000), re.S)
    if not m:
        continue
    d = re.search(r"^description:\s*(.*?)(?=\n[a-z_]+:|\Z)", m.group(1), re.S | re.M)
    if d:
        roster += len(" ".join(d.group(1).split()))
resident_tok = (prefs + roster) / CPT

tot = collections.Counter()
ctx_buckets = collections.Counter()
sub_tok = 0
seen = set()

files = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")) + \
        glob.glob(os.path.expanduser("~/.claude/projects/*/*/subagents/agent-*.jsonl"))

for f in files:
    try:
        if os.path.getmtime(f) < CUTOFF:
            continue
    except OSError:
        continue
    is_sub = "/subagents/" in f
    for line in open(f, errors="replace"):
        if '"usage"' not in line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        m = r.get("message") or {}
        u = m.get("usage")
        if not isinstance(u, dict) or r.get("timestamp", "") < CUTOFF_ISO:
            continue
        # One response is logged as several lines carrying the same usage; count it once.
        if m.get("id") in seen:
            continue
        seen.add(m.get("id"))
        cr = u.get("cache_read_input_tokens") or 0
        cw = u.get("cache_creation_input_tokens") or 0
        i, o = u.get("input_tokens") or 0, u.get("output_tokens") or 0
        ctx = cr + cw + i
        tot["requests"] += 1
        tot["cache_read"] += cr
        tot["cache_write"] += cw
        tot["input"] += i
        tot["output"] += o
        tot["context_tokens"] += ctx
        if is_sub:
            sub_tok += ctx + o
        # Effective billed-equivalent units, using published multipliers.
        tot["billed_units"] += cr * 0.10 + cw * 1.25 + i * 1.0
        ctx_buckets[">150k" if ctx > 150_000 else "<=150k"] += ctx + o

print(f"=== consumption over {DAYS}d, counted from the transcript store ===")
print(f"  requests                 : {tot['requests']:,}")
print(f"  cache READ tokens        : {tot['cache_read']:,}")
print(f"  cache WRITE tokens       : {tot['cache_write']:,}")
print(f"  fresh input tokens       : {tot['input']:,}")
print(f"  output tokens            : {tot['output']:,}")
print(f"  total context tokens     : {tot['context_tokens']:,}")
print()
print(f"  resident tier            : {prefs:,}B prefs + {roster:,}B roster = ~{resident_tok:,.0f} tokens/request")
res_ctx = resident_tok * tot["requests"]
print(f"  resident, summed         : {res_ctx:,.0f} tokens  =  "
      f"{res_ctx / tot['context_tokens']:.2%} of all context tokens")
print(f"  resident, billed-weighted: {resident_tok * tot['requests'] * 0.10:,.0f} units  =  "
      f"{resident_tok * tot['requests'] * 0.10 / tot['billed_units']:.2%} of billed input units")
print()
print(f"  share of consumption from SUBAGENTS : {sub_tok / (tot['context_tokens'] + tot['output']):.1%}")
for k, v in ctx_buckets.most_common():
    print(f"  share of consumption at {k:>7} context: {v / (tot['context_tokens'] + tot['output']):.1%}")
print()
# `is not None`, deliberately, NOT a truthiness test: a genuine measured 0 must score as a prune
# that cut nothing, not fall through to the not-given branch. Unknown, zero and a real value are
# three states and each needs its own rendering — silence here would be read as "the prune saved
# nothing", which is a different false claim.
if _a.cut_bytes is not None:
    cut = _a.cut_bytes / CPT
    print(f"  THIS PASS cut {_a.cut_bytes:,}B of prefs = ~{cut:,.0f} tokens/request")
    print(f"    -> {cut * tot['requests']:,.0f} context tokens over the window "
          f"({cut * tot['requests'] / tot['context_tokens']:.2%} of the total)")
    print(f"    -> billed-weighted, {cut * tot['requests'] * 0.10 / tot['billed_units']:.2%} of input units")
else:
    print("  no --cut-bytes given, so no prune is scored here "
          "(this is not 'a prune saved nothing')")
