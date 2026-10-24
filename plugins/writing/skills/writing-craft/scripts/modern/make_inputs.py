#!/usr/bin/env python3
"""Build flagcheck inputs from the human items and the Claude files (run build_claude.py first).

Writes grade-candidates-{lines,paras}.jsonl (all candidates, label model, ids <slot>-c<n>) and
run-default-{lines,paras}.jsonl (human + default, ids <slot> and <slot>-d). Only id, text, label, register.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETS = {"lines": ("human-lines.jsonl", "claude-default-lines.jsonl", "line-candidates.jsonl"),
        "paras": ("human-paras.jsonl", "claude-default-paras.jsonl", "para-candidates.jsonl")}


def jl(p: Path) -> list[dict]:
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]


def row(i: str, text: str, label: str) -> dict:
    return {"id": i, "text": text, "label": label, "register": "modern"}


def dump(p: Path, rows: list[dict]) -> None:
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


def main() -> None:
    for name, (hf, df, cf) in SETS.items():
        human = [row(h["id"], h["text"], "human") for h in jl(HERE / hf)]
        default = [row(d["id"], d["text"], "model") for d in jl(HERE / df)]
        cands = [row(f"{c['slot']}-c{c['cand']}", c["text"], "model") for c in jl(HERE / cf)]
        dump(HERE / f"run-default-{name}.jsonl", human + default)
        dump(HERE / f"grade-candidates-{name}.jsonl", cands)
        print(f"{name}: run-default {len(human) + len(default)} rows, grade-candidates {len(cands)} rows")


if __name__ == "__main__":
    main()
