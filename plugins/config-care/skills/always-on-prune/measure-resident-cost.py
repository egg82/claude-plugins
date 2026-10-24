#!/usr/bin/env python3
"""What does a resident byte of always-on preference actually cost, on THIS machine's real traffic?

The question the prior pruning pass could not answer: was the difference measured, or inferred?

THE MODELLING TRAP, recorded because the first version of this script fell into it. Nearly every
request reports `cache_creation_input_tokens > 0` — 99.8% of them here — which looks like "the cache
is re-created every request" and inflates the answer ~12x. It is not: caching is incremental, so each
request creates an entry for the DELTA it appends (last turn's output, new tool results) while reading
the stable prefix it shares with its predecessor. The always-on prefs are in that stable prefix. They
are created once per cache EPOCH and read on every request thereafter.

So a request that creates the prefs is one that read nothing — a cold prefix. That is countable:

    creations = requests with cache_read_input_tokens == 0
    reads     = every other request

    cost(K bytes) = tokens(K) * ( creations * 1.25 + reads * 0.10 ) * input_price

Both counts are exact. `tokens(K)` is the only estimate — no tokenizer is installed — so it is
reported as a band, never a single confident figure.

Counts sessions AND subagents, because a subagent pays the same resident prefix and there are far
more of them. That multiplier is the point: resident bytes multiply by agents rather than adding.

BODY BYTES, NOT FILE BYTES. A `---` frontmatter block is stripped when a preference is expanded into
context, so file size overstates what is actually resident. This script measures each file minus a
leading frontmatter block and prints the file-byte total alongside, so the gap is visible rather than
silently corrected. Verify the stripping holds on your own machine before trusting either figure.
"""
import argparse, json, glob, os, re, sys, time, collections

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0],
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("days", nargs="?", type=int, default=30,
                help="window of transcript history to measure, in days (default 30)")
ap.add_argument("--prefs-dir", default="~/.claude/memory",
                help="directory of resident preference files (*.md). Default is this machine's "
                     "convention; a CLAUDE.md @import can point anywhere, so check yours.")
a = ap.parse_args()

DAYS = a.days
CUTOFF = time.time() - DAYS * 86400
# Per-request filter: a file touched in the window can hold days of older requests.
CUTOFF_ISO = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(CUTOFF))
seen = set()  # one response is logged as several lines carrying the same usage; count it once
MEM = os.path.expanduser(a.prefs_dir)

if not os.path.isdir(MEM):
    sys.exit(f"INCONCLUSIVE — preference directory does not exist: {MEM}\n"
             f"  Nothing was measured. Point --prefs-dir at the directory your CLAUDE.md @imports.")
pref_files = sorted(glob.glob(os.path.join(MEM, "*.md")))
if not pref_files:
    sys.exit(f"INCONCLUSIVE — no *.md files in {MEM}\n"
             f"  A zero here would be indistinguishable from a real empty tier, so nothing is "
             f"reported. Point --prefs-dir at the directory your CLAUDE.md @imports.")

# Published input prices, USD per 1M input tokens. Cache write 1.25x, cache read 0.10x except
# where CR_MULT says otherwise. bucket() takes the FIRST substring match, so specific ids
# precede their family (the `opus` alias resolves to 5.5; most history is Opus 5).
# `opus` alone is Opus 5 / 4.x; `haiku` alone is Haiku 4.5. Haiku 5.5's rate rises 5x past 100K-token
# prompts (not modelled). Keep in step with where-the-bar-goes.py.
PRICE = {"opus-5-5": 4.00, "opus": 5.00, "sonnet": 2.00, "haiku-5-5": 0.10, "haiku": 1.00, "fable": 10.00}
CR_MULT = {"opus-5-5": 0.05, "fable": 0.025}

def bucket(model):
    m = (model or "").lower()
    for k in PRICE:
        if k in m:
            return k
    return None

stats = collections.Counter()
per_model = collections.defaultdict(lambda: collections.Counter())

files = glob.glob(os.path.expanduser("~/.claude/projects/*/*.jsonl")) + \
        glob.glob(os.path.expanduser("~/.claude/projects/*/*/subagents/agent-*.jsonl"))

for f in files:
    try:
        if os.path.getmtime(f) < CUTOFF:
            continue
    except OSError:
        continue
    is_sub = "/subagents/" in f
    stats["sub_files" if is_sub else "session_files"] += 1
    for line in open(f, errors="replace"):
        if '"usage"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        msg = d.get("message") or {}
        u = msg.get("usage")
        if not isinstance(u, dict) or d.get("timestamp", "") < CUTOFF_ISO or msg.get("id") in seen:
            continue
        seen.add(msg.get("id"))
        b = bucket(msg.get("model"))
        if not b:
            continue
        stats["requests"] += 1
        stats["sub_requests" if is_sub else "session_requests"] += 1
        per_model[b]["requests"] += 1
        if (u.get("cache_read_input_tokens") or 0) == 0:
            per_model[b]["creations"] += 1     # cold prefix: the prefs are paid at write rate
            stats["creations"] += 1
        else:
            per_model[b]["reads"] += 1         # warm: the prefs are re-read at 0.10x
            stats["reads"] += 1

def body_bytes(path):
    """File size minus a leading `---` frontmatter block — frontmatter is not resident."""
    s = open(path, errors="replace").read()
    m = re.match(r"^---\n.*?\n---\n", s, re.S)
    return len(s) - (len(m.group(0)) if m else 0)

sizes = {os.path.basename(p): body_bytes(p) for p in pref_files}
total_bytes = sum(sizes.values())
file_total = sum(os.path.getsize(p) for p in pref_files)

print(f"=== measured over the last {DAYS} days, on real traffic ===")
print(f"  transcripts        : {stats['session_files']} session, {stats['sub_files']} subagent")
print(f"  requests (exact)   : {stats['requests']}  "
      f"({stats['session_requests']} session, {stats['sub_requests']} subagent)")
if stats["requests"]:
    print(f"  subagent share     : {stats['sub_requests']/stats['requests']:.0%} of all requests")
print(f"  cold-prefix (write): {stats['creations']}")
print(f"  warm  (0.10x read) : {stats['reads']}")
over = (file_total - total_bytes) / total_bytes if total_bytes else 0
print(f"\n  always-on tier     : {len(sizes)} files, {total_bytes} BODY bytes  ({MEM})")
print(f"  file bytes would be: {file_total}  (+{over:.1%}) — frontmatter, not resident; "
      f"a checker counting these overstates\n")

def cost_of(nbytes, cpt):
    tok = nbytes / cpt
    return sum(tok * (c["creations"] * 1.25 + c["reads"] * CR_MULT.get(b, 0.10)) * PRICE[b] / 1e6
               for b, c in per_model.items())

print("  ESTIMATED cost of keeping the tier resident over the window.")
print("  Request counts are exact; only chars-per-token is estimated, hence the band.")
for cpt in (3.5, 4.0, 4.5):
    print(f"    at {cpt} chars-per-tok ${cost_of(total_bytes, cpt):7.2f}   "
          f"(${cost_of(1000, cpt):5.2f} per resident KB)")

print("\n  per-file BODY bytes, at 4.0 chars/token — what cutting each would have saved over the window:")
for name, sz in sorted(sizes.items(), key=lambda kv: -kv[1]):
    print(f"    {sz:6}B  ${cost_of(sz, 4.0):6.2f}  {name}")
