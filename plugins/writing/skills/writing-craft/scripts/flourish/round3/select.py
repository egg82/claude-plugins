#!/usr/bin/env python3
"""Round 3 selection: from five candidates per slot, keep the one a grader judged most human, and one at random.

  select.py lines --graded <flagcheck-out>.jsonl
  select.py paras --graded <flagcheck-out>.jsonl

--graded is the <out>.jsonl that scripts/flagcheck.py wrote for grade-candidates-<kind>.jsonl (records with
id, grader, and fwd/rev: {verdict, confidence}). Machine probability of one verdict = confidence if the verdict
is "machine", else 1 - confidence; a candidate's score is the mean over the orders that gave a usable answer.
The lowest score in a slot wins (ties: the seeded generator picks). A candidate with no usable verdict is
unmeasured and cannot win; a slot with none measured stops the run rather than guessing.

Writes, beside this script: selected-<kind>.jsonl, random-<kind>.jsonl, run-selected-<kind>.jsonl,
run-random-<kind>.jsonl. The run files pair each set with the human set, ready for flagcheck or Pangram.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
FLOURISH = HERE.parent

# kind -> (candidates file, human file, id prefix for the chosen model rows, register)
KINDS: dict[str, tuple[str, Path, str, str]] = {
    "lines": ("line-candidates.jsonl", FLOURISH / "human-test.jsonl", "c", "flourish"),
    "paras": ("para-candidates.jsonl", FLOURISH / "paragraphs" / "human.jsonl", "cp", "flourish-paragraph"),
}
RUN_FIELDS = ("id", "text", "label", "register")


@dataclass
class Candidate:
    cid: str
    slot: str
    cand: int
    text: str
    words: int
    human_words: int
    score: Optional[float] = None  # mean machine probability; None = unmeasured


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")


def machine_prob(verdict: Optional[str], confidence: Optional[float]) -> Optional[float]:
    if verdict not in ("human", "machine") or confidence is None:
        return None
    return confidence if verdict == "machine" else 1.0 - confidence


def mean_machine_prob(rec: dict) -> Optional[float]:
    probs: list[float] = []
    for key in ("fwd", "rev"):
        side = rec.get(key)
        if isinstance(side, dict):
            p = machine_prob(side.get("verdict"), side.get("confidence"))
            if p is not None:
                probs.append(p)
    return sum(probs) / len(probs) if probs else None


def load_candidates(path: Path) -> list[Candidate]:
    return [Candidate(r["id"], r["slot"], r["cand"], r["text"], r["words"], r["human_words"])
            for r in read_jsonl(path)]


def attach_scores(cands: list[Candidate], graded: list[dict], grader: Optional[str]) -> None:
    by_id = {r["id"]: r for r in graded if grader is None or r.get("grader") == grader}
    for c in cands:
        if c.cid in by_id:
            c.score = mean_machine_prob(by_id[c.cid])


def by_slot(cands: list[Candidate]) -> dict[str, list[Candidate]]:
    out: dict[str, list[Candidate]] = {}
    for c in cands:
        out.setdefault(c.slot, []).append(c)
    return dict(sorted(out.items()))


def pick_best(group: list[Candidate], rng: random.Random) -> Candidate:
    scored = [(c.score, c) for c in group if c.score is not None]
    if not scored:
        raise SystemExit(f"slot {group[0].slot}: none of {len(group)} candidates has a usable verdict")
    low = min(s for s, _ in scored)
    return rng.choice([c for s, c in scored if s == low])


def model_row(c: Candidate, prefix: str, slot_digits: str, register: str, strategy: str) -> dict:
    return {"id": f"{prefix}{slot_digits}", "text": c.text, "label": "model", "register": register,
            "slot": c.slot, "cand": c.cand, "words": c.words, "human_words": c.human_words,
            "strategy": strategy, "mean_machine_prob": c.score}


def mean_score(rows: list[dict]) -> float:
    vals = [r["mean_machine_prob"] for r in rows if r["mean_machine_prob"] is not None]
    return sum(vals) / len(vals) if vals else float("nan")


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=sorted(KINDS))
    ap.add_argument("--graded", type=Path, required=True, help="flagcheck <out>.jsonl for grade-candidates-<kind>.jsonl")
    ap.add_argument("--grader", help="only records from this grader (gemini, openai, fake...); default all")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out-dir", type=Path, default=HERE)
    a = ap.parse_args(argv)

    cand_file, human_file, prefix, register = KINDS[a.kind]
    cands = load_candidates(HERE / cand_file)
    attach_scores(cands, read_jsonl(a.graded), a.grader)
    unmeasured = [c.cid for c in cands if c.score is None]
    if unmeasured:
        print(f"warning: {len(unmeasured)} of {len(cands)} candidates have no usable verdict: {unmeasured[:8]}",
              file=sys.stderr)

    rng_rand = random.Random(a.seed)
    rng_tie = random.Random(a.seed + 1)
    selected: list[dict] = []
    chosen_random: list[dict] = []
    for slot, group in by_slot(cands).items():
        digits = "".join(ch for ch in slot if ch.isdigit())
        selected.append(model_row(pick_best(group, rng_tie), prefix, digits, register, "selected"))
        chosen_random.append(model_row(rng_rand.choice(group), prefix, digits, register, "random"))

    human = [{k: r[k] for k in RUN_FIELDS} for r in read_jsonl(human_file)]
    d = a.out_dir
    write_jsonl(d / f"selected-{a.kind}.jsonl", selected)
    write_jsonl(d / f"random-{a.kind}.jsonl", chosen_random)
    write_jsonl(d / f"run-selected-{a.kind}.jsonl", human + [{k: r[k] for k in RUN_FIELDS} for r in selected])
    write_jsonl(d / f"run-random-{a.kind}.jsonl", human + [{k: r[k] for k in RUN_FIELDS} for r in chosen_random])

    same = sum(s["cand"] == r["cand"] for s, r in zip(selected, chosen_random))
    print(f"{a.kind}: {len(selected)} slots; mean machine prob selected {mean_score(selected):.3f}, "
          f"random-pick {mean_score(chosen_random):.3f}; same candidate in {same} slots; wrote to {d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
