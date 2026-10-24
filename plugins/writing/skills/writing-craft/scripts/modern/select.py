#!/usr/bin/env python3
"""Pick one candidate per slot from the Gemini flagcheck results, and a seeded random pick.

usage: select.py {lines|paras} <flagcheck-out.jsonl of grade-candidates-*.jsonl>

Score = mean probability the grader called the candidate machine, over both presentation orders
(a verdict with confidence c counts c if machine, 1-c if human). The selected candidate has the lowest
score (ties broken by the seeded RNG); the random pick ignores the results. Writes
run-selected-<set>.jsonl and run-random-<set>.jsonl (human + pick, ids <slot> and <slot>-sel / <slot>-rnd)
and selection-<set>.json (slot -> chosen cand, scores).
"""
import json
import random
import sys
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
SEED = 7
HUMAN = {"lines": "human-lines.jsonl", "paras": "human-paras.jsonl"}
CANDS = {"lines": "line-candidates.jsonl", "paras": "para-candidates.jsonl"}


def jl(p: Path) -> "list[dict]":
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def p_machine(rec: dict) -> Optional[float]:
    ps = []
    for key in ("fwd", "rev"):
        v = rec.get(key)
        if not v or v.get("verdict") not in ("human", "machine"):
            continue
        c = v.get("confidence")
        c = 0.5 if c is None else float(c)
        ps.append(c if v["verdict"] == "machine" else 1 - c)
    return sum(ps) / len(ps) if ps else None


def main(argv: list[str]) -> int:
    kind, results = argv[1], Path(argv[2])
    assert kind in HUMAN, kind
    rng = random.Random(SEED)
    score = {r["id"]: p_machine(r) for r in jl(results)}
    human = jl(HERE / HUMAN[kind])
    cands = jl(HERE / CANDS[kind])
    sel_rows, rnd_rows, report = [], [], {}
    for h in human:
        slot = h["id"]
        cs = [c for c in cands if c["slot"] == slot]
        assert len(cs) == 5, slot
        sc = {c["cand"]: score.get(f"{slot}-c{c['cand']}") for c in cs}
        known = {k: v for k, v in sc.items() if v is not None}
        assert known, f"no graded candidate for {slot}"
        best = min(known.values())
        pick = rng.choice([k for k, v in known.items() if v == best])
        rnd = rng.choice([c["cand"] for c in cs])
        text = {c["cand"]: c["text"] for c in cs}
        base = {"label": "model", "register": "modern"}
        sel_rows.append({"id": f"{slot}-sel", "text": text[pick], **base})
        rnd_rows.append({"id": f"{slot}-rnd", "text": text[rnd], **base})
        report[slot] = {"selected": pick, "random": rnd, "p_machine": sc}
    hum = [{"id": h["id"], "text": h["text"], "label": "human", "register": "modern"} for h in human]
    for name, rows in (("selected", sel_rows), ("random", rnd_rows)):
        (HERE / f"run-{name}-{kind}.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in hum + rows))
    (HERE / f"selection-{kind}.json").write_text(json.dumps(report, indent=1))
    print(f"{kind}: wrote run-selected and run-random ({len(human)} slots)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
