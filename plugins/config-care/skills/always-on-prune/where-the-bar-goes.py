#!/usr/bin/env python3
"""Where does the weekly usage bar actually go? Two questions the fix depends on.

Q1. The >150k-context share — is it a few monster sessions, or many medium ones? Those need
    different remedies: "split the task" vs "/clear between tasks".
Q2. What did model choice cost on SUBAGENTS specifically? Not list price — the realised
    billed-equivalent per agent, by model, so the gate's default can be set from evidence.

Billed-equivalent units use the published multipliers (cache read 0.10x unless CR_MULT says
otherwise, cache write 1.25x, fresh input 1.0x) times each model's input rate, plus output at its own rate. Output matters here:
it is never cached and it is the expensive column.
"""
import argparse, collections, glob, json, os, time

_ap = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                              formatter_class=argparse.RawDescriptionHelpFormatter)
_ap.add_argument("days", nargs="?", type=int, default=30,
                 help="window to measure, in days (default 30)")
_a = _ap.parse_args()
DAYS = _a.days
CUTOFF = time.time() - DAYS * 86400
# Per-request filter: a file touched in the window can hold days of older requests.
CUTOFF_ISO = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(CUTOFF))
seen = set()  # one response is logged as several lines carrying the same usage; count it once


def fresh(d):
    """The message of a usage line inside the window not yet counted, else None."""
    msg = d.get("message") or {}
    if d.get("timestamp", "") < CUTOFF_ISO or msg.get("id") in seen:
        return None
    seen.add(msg.get("id"))
    return msg
# bucket() takes the FIRST substring match, so specific ids precede their family: the `opus`
# alias resolves to 5.5 while most history is Opus 5, and the two are priced differently.
# `opus` alone is Opus 5 / 4.x, and `haiku` alone is Haiku 4.5. Sonnet 5 and 5.5 share a rate;
# Sonnet 4.6 ($3/$15) would be under-priced here. Haiku 5.5's rates rise past 100K-token prompts
# (to $0.50 / $2.50, 5x); not modelled.
IN_RATE = {"opus-5-5": 4.00, "opus": 5.00, "sonnet": 2.00, "haiku-5-5": 0.10, "haiku": 1.00, "fable": 10.00}
OUT_RATE = {"opus-5-5": 20.00, "opus": 25.00, "sonnet": 10.00, "haiku-5-5": 0.50, "haiku": 5.00, "fable": 50.00}
CR_MULT = {"opus-5-5": 0.05, "fable": 0.025}  # cache-read multiplier where not 0.10x

def bucket(m):
    m = (m or "").lower()
    for k in IN_RATE:
        if k in m:
            return k
    return None

def cost(b, cr, cw, i, o):
    return (cr * CR_MULT.get(b, 0.10) + cw * 1.25 + i) * IN_RATE[b] / 1e6 + o * OUT_RATE[b] / 1e6

# ---------- Q1: session-level totals ----------
sess = []
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")):
    try:
        if os.path.getmtime(f) < CUTOFF:
            continue
    except OSError:
        continue
    tot = 0.0; peak = 0; n = 0
    for line in open(f, errors="replace"):
        if '"usage"' not in line:
            continue
        try:
            msg = fresh(json.loads(line))
        except Exception:
            continue
        if msg is None:
            continue
        u = msg.get("usage")
        b = bucket(msg.get("model"))
        if not isinstance(u, dict) or not b:
            continue
        cr = u.get("cache_read_input_tokens") or 0; cw = u.get("cache_creation_input_tokens") or 0
        i = u.get("input_tokens") or 0; o = u.get("output_tokens") or 0
        tot += cost(b, cr, cw, i, o); peak = max(peak, cr + cw + i); n += 1
    if n:
        sess.append((tot, peak, n, os.path.basename(f)[:8]))

sess.sort(reverse=True)
grand = sum(s[0] for s in sess)
print(f"=== Q1: {len(sess)} sessions over {DAYS}d, {grand:,.0f} billed-equivalent units ===")
for label, lo, hi in [("peak <50k", 0, 50_000), ("50-150k", 50_000, 150_000),
                      ("150-300k", 150_000, 300_000), (">300k", 300_000, 10**12)]:
    grp = [s for s in sess if lo <= s[1] < hi]
    if grp:
        print(f"  {label:>10}: {len(grp):>3} sessions  {sum(g[0] for g in grp)/grand:>6.1%} of spend")
print("\n  the ten most expensive sessions:")
cum = 0
for tot, peak, n, sid in sess[:10]:
    cum += tot
    print(f"    {sid}  {tot:>8,.0f} units  peak ctx {peak/1000:>6.0f}k  {n:>4} requests")
print(f"  those ten alone = {cum/grand:.1%} of all spend")
top10pct = max(1, len(sess) // 10)
print(f"  the top {top10pct} sessions ({top10pct/len(sess):.0%}) = "
      f"{sum(s[0] for s in sess[:top10pct])/grand:.1%} of all spend")

# ---------- Q2: subagents by model ----------
per = collections.defaultdict(lambda: collections.Counter())
agents = collections.defaultdict(lambda: collections.defaultdict(float))
for f in glob.glob(os.path.expanduser("~/.claude/projects/*/*/subagents/agent-*.jsonl")):
    try:
        if os.path.getmtime(f) < CUTOFF:
            continue
    except OSError:
        continue
    aid = os.path.basename(f)
    for line in open(f, errors="replace"):
        if '"usage"' not in line:
            continue
        try:
            msg = fresh(json.loads(line))
        except Exception:
            continue
        if msg is None:
            continue
        u = msg.get("usage"); b = bucket(msg.get("model"))
        if not isinstance(u, dict) or not b:
            continue
        cr = u.get("cache_read_input_tokens") or 0; cw = u.get("cache_creation_input_tokens") or 0
        i = u.get("input_tokens") or 0; o = u.get("output_tokens") or 0
        per[b]["units"] += cost(b, cr, cw, i, o); per[b]["req"] += 1
        agents[b][aid] += cost(b, cr, cw, i, o)

print(f"\n=== Q2: subagent spend by model, {DAYS}d ===")
sub_total = sum(p["units"] for p in per.values())
print(f"  {'model':8} {'agents':>7} {'requests':>9} {'units':>12} {'share':>7} {'median/agent':>13}")
for b, p in sorted(per.items(), key=lambda kv: -kv[1]["units"]):
    vals = sorted(agents[b].values())
    med = vals[len(vals)//2] if vals else 0
    print(f"  {b:8} {len(agents[b]):>7} {p['req']:>9} {p['units']:>12,.0f} "
          f"{p['units']/sub_total:>6.1%} {med:>13,.1f}")
print(f"\n  subagents total {sub_total:,.0f} units = {sub_total/(sub_total + grand):.1%} of all spend"
      f" (Q1's shares above are of main-session spend only)")
