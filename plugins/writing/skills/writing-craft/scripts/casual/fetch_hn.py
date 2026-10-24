#!/usr/bin/env python3
"""Fetch ~100 HN reply comments (2015-2019, 25-150 words, parent is a comment) via Algolia. Stdlib only."""
import html
import json
import random
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

API = "https://hn.algolia.com/api/v1"
SEED = 20261021
TARGET = 100


def get(url: str) -> Dict[str, Any]:
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # network retry
            print("retry", attempt, type(e).__name__, file=sys.stderr)
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("fetch failed: " + url)


def to_text(h: str) -> str:
    """HTML to plain text; keeps the writer's own characters."""
    h = re.sub(r"<p>", "\n\n", h)
    h = re.sub(r"<a [^>]*href=\"([^\"]*)\"[^>]*>.*?</a>", r"\1", h)
    h = re.sub(r"<[^>]+>", "", h)
    return html.unescape(h).strip()


def words(t: str) -> int:
    return len(t.split())


def main(out_path: str) -> None:
    rng = random.Random(SEED)
    cands: List[Dict[str, Any]] = []
    # 2015-01-01 .. 2019-12-31, 40 random one-hour windows
    lo, hi = 1420070400, 1577836799
    for _ in range(40):
        t0 = rng.randrange(lo, hi)
        q = urllib.parse.urlencode({
            "tags": "comment", "hitsPerPage": 100,
            "numericFilters": "created_at_i>%d,created_at_i<%d" % (t0, t0 + 3600)})
        d = get(API + "/search_by_date?" + q)
        for h in d["hits"]:
            if h.get("parent_id") == h.get("story_id"):
                continue  # top-level comment
            txt = to_text(h.get("comment_text") or "")
            if not (25 <= words(txt) <= 150) or "[dead]" in txt:
                continue
            cands.append({"id": str(h["objectID"]), "parent_id": h["parent_id"], "text": txt})
        time.sleep(0.3)
    rng.shuffle(cands)
    print("candidates", len(cands))
    seen = set()
    rows: List[Dict[str, str]] = []
    for c in cands:
        if len(rows) >= TARGET:
            break
        if c["parent_id"] in seen:
            continue
        p: Optional[Dict[str, Any]] = None
        try:
            p = get("%s/items/%s" % (API, c["parent_id"]))
        except RuntimeError:
            continue
        if p.get("type") != "comment" or not p.get("text"):
            continue
        seen.add(c["parent_id"])
        rows.append({"id": c["id"], "parent_text": to_text(p["text"]), "text": c["text"]})
        time.sleep(0.2)
    with open(out_path, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("wrote", len(rows), out_path)


if __name__ == "__main__":
    main(sys.argv[1])
