"""Score blind-quiz responses against the flourish sets.

    python3 -I quiz_score.py <response.json | dir of them> [--code <results code> ...]

A response holds {rater, chatbot, answers: [{id, answer}]}; ids are h* (human), s* (Claude under the skill),
d* (Claude default) from scripts/flourish/. Prints per rater and pooled: accuracy per condition, and a majority vote
per item once several raters have seen it.
"""
import argparse
import base64
import json
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent / "flourish"
SETS = {"h": ("human-test.jsonl", "human"), "s": ("claude-skill.jsonl", "skill"), "d": ("claude-default.jsonl", "default")}


def load_conds() -> dict[str, str]:
    conds: dict[str, str] = {}
    for prefix, (fname, cond) in SETS.items():
        for line in (HERE / fname).read_text().splitlines():
            if line.strip():
                conds[json.loads(line)["id"]] = cond
    return conds


def load_responses(paths: list[str], codes: list[str]) -> list[dict[str, object]]:
    out: list[dict[str, object]] = []
    for p in paths:
        files = sorted(Path(p).rglob("*.json")) if Path(p).is_dir() else [Path(p)]
        for f in files:
            doc = json.loads(f.read_text())
            out.append(doc.get("data", doc))
    for c in codes:
        doc = json.loads(base64.b64decode(c + "=" * (-len(c) % 4)))
        if "a" in doc:  # the end screen's compact code: {r, c, a: [[id, "h" | "m"]]}
            doc = {"rater": doc.get("r"), "chatbot": doc.get("c"), "exposure": doc.get("e"),
                   "answers": [{"id": i, "answer": "human" if v == "h" else "machine"} for i, v in doc["a"]]}
        out.append(doc)
    return out


def score(resp: dict[str, object], conds: dict[str, str]) -> dict[str, tuple[int, int]]:
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for a in resp["answers"]:  # type: ignore[union-attr]
        cond = conds[a["id"]]
        truth = "human" if cond == "human" else "machine"
        tally[cond][0] += int(a["answer"] == truth)
        tally[cond][1] += 1
    return {k: (v[0], v[1]) for k, v in tally.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="*")
    ap.add_argument("--code", action="append", default=[])
    args = ap.parse_args()
    conds = load_conds()
    resps = load_responses(args.paths, args.code)
    if not resps:
        sys.exit("no responses")
    pooled: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    votes: dict[str, list[str]] = defaultdict(list)
    for r in resps:
        s = score(r, conds)
        total = sum(c for c, _ in s.values()), sum(n for _, n in s.values())
        parts = "  ".join(f"{k} {c}/{n}" for k, (c, n) in sorted(s.items()))
        print(f"rater {str(r.get('rater'))[:8]} chatbot={r.get('chatbot')} reads-AI={r.get('exposure')}  correct {total[0]}/{total[1]}  {parts}")
        for k, (c, n) in s.items():
            pooled[k][0] += c
            pooled[k][1] += n
        for a in r["answers"]:  # type: ignore[union-attr]
            votes[a["id"]].append(a["answer"])
    print("pooled: " + "  ".join(f"{k} {c}/{n} ({c / n:.0%})" for k, (c, n) in sorted(pooled.items())))
    multi = {i: v for i, v in votes.items() if len(v) >= 3}
    if multi:
        right = sum(1 for i, v in multi.items()
                    if max(set(v), key=v.count) == ("human" if conds[i] == "human" else "machine"))
        print(f"majority vote on items seen by 3+ raters: {right}/{len(multi)} correct")


if __name__ == "__main__":
    main()
