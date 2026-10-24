#!/usr/bin/env python3
"""Mine real subagent prompts to derive benchmark categories from the actual workload.

Descriptions live in the meta.json sidecars; full prompts live in the spawning
transcript's toolUseResult. Cluster by keyword so the benchmark reflects what these
agents were really asked to do, not what I imagine subagent work looks like.

TEMPLATE — CATS (the category regexes) are tuned to one workload. Retune for yours.
Keyword clustering is coarse: it will file a research-over-code task under code. Use the
output to weight a task set, not as an exact taxonomy.
"""
import json, glob, os, re, collections

# Coarse categories, matched against description + prompt opening.
CATS = [
    ("research/web",     r"\b(research|search|sentiment|landscape|competitor|review|find out|news|forum|reddit|community)\b"),
    ("code/repo",        r"\b(repo|code|bug|refactor|implement|patch|diff|function|module|class|test|lint|compile)\b"),
    ("infra/ops",        r"\b(cluster|kube|k8s|terraform|ansible|node|pod|deploy|dns|host|ssh|disk|systemd|container|backup)\b"),
    ("data/extract",     r"\b(extract|parse|tally|count|list all|inventory|enumerate|scan|audit|metadata|catalog)\b"),
    ("verify/judge",     r"\b(verify|validate|confirm|check|adversarial|refute|judge|assess|cold.read|critique)\b"),
    ("docs/write",       r"\b(write|draft|document|readme|summar|report|explain|describe)\b"),
]


def spawn_records():
    """(description, prompt, model, depth) for every recorded spawn."""
    for path in glob.glob(os.path.expanduser("~/.claude/projects/**/*.jsonl"), recursive=True):
        for line in open(path, errors="replace"):
            if '"agentId"' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            t = d.get("toolUseResult")
            if not isinstance(t, dict) or not t.get("agentId"):
                continue
            if "prompt" not in t and "description" not in t:
                continue
            yield (t.get("description") or "", t.get("prompt") or "",
                   t.get("resolvedModel") or "?", t.get("agentId"))


def categorize(text):
    hits = [name for name, rx in CATS if re.search(rx, text, re.I)]
    return hits[0] if hits else "other"


recs = list(spawn_records())
seen, uniq = set(), []
for desc, prompt, model, aid in recs:
    if aid in seen:
        continue
    seen.add(aid)
    uniq.append((desc, prompt, model))

print(f"unique spawn records with prompts: {len(uniq)}\n")

cats = collections.Counter()
lens = collections.defaultdict(list)
samples = collections.defaultdict(list)
for desc, prompt, model in uniq:
    c = categorize(desc + " " + prompt[:400])
    cats[c] += 1
    lens[c].append(len(prompt))
    if len(samples[c]) < 4 and len(prompt) > 200:
        samples[c].append((desc, prompt))

print(f"{'category':16} {'count':>6} {'share':>7} {'median prompt chars':>20}")
tot = sum(cats.values())
for c, n in cats.most_common():
    med = sorted(lens[c])[len(lens[c]) // 2] if lens[c] else 0
    print(f"{c:16} {n:>6} {n/tot:>6.1%} {med:>20,}")

print("\n\n=== representative descriptions per category ===")
for c, _ in cats.most_common():
    print(f"\n### {c}")
    for desc, _p in samples[c]:
        print(f"   - {desc[:78]}")

print("\n\n=== one full sample prompt from the largest category ===")
top = cats.most_common(1)[0][0]
if samples[top]:
    d, p = samples[top][0]
    print(f"[{d}]\n{p[:1400]}")
