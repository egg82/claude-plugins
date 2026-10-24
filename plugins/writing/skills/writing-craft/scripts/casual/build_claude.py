#!/usr/bin/env python3
"""Join replies/r*.txt (### <index> then text) with human.jsonl parents into claude.jsonl; report length ratios."""
import glob
import json
import re
from typing import Dict, List

humans: List[Dict[str, str]] = [json.loads(line) for line in open("human.jsonl")]
replies: Dict[int, str] = {}
for p in sorted(glob.glob("replies/r*.txt")):
    for m in re.finditer(r"^### (\d+)\n(.*?)(?=^### |\Z)", open(p).read(), re.S | re.M):
        replies[int(m.group(1))] = m.group(2).strip()
assert sorted(replies) == list(range(len(humans))), "missing replies"
bad = 0
with open("claude.jsonl", "w") as f:
    for i, h in enumerate(humans):
        t = replies[i]
        r = len(t.split()) / len(h["text"].split())
        if not 0.8 <= r <= 1.2:
            bad += 1
            print("OUT", i, len(h["text"].split()), len(t.split()), round(r, 2))
        f.write(json.dumps({"id": "c-" + h["id"], "parent_text": h["parent_text"], "text": t}, ensure_ascii=False) + "\n")
print("out of range:", bad)
