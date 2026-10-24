#!/usr/bin/env python3
"""Turn model-{lines,paras}.txt (model-written continuations; id|key|text; key d = default, 1-5 = candidates) into the JSONL files.

Checks every item against its human item's word count (lines +-3, paragraphs +-10) and exits non-zero
on any miss or any missing slot/candidate. Run after extract.py.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETS = {"lines": ("human-lines.jsonl", "model-lines.txt", 3,
                  "claude-default-lines.jsonl", "line-candidates.jsonl"),
        "paras": ("human-paras.jsonl", "model-paras.txt", 10,
                  "claude-default-paras.jsonl", "para-candidates.jsonl")}


def jl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def main() -> int:
    bad = 0
    for name, (hf, af, tol, df, cf) in SETS.items():
        human = {r["id"]: r for r in jl(HERE / hf)}
        got: dict[str, dict[str, str]] = {}
        for ln in (HERE / af).read_text().splitlines():
            if ln.strip():
                slot, key, text = ln.split("|", 2)
                assert key not in got.setdefault(slot, {}), f"duplicate {slot}|{key}"
                got[slot][key] = text.strip()
        defaults, cands = [], []
        for slot, h in human.items():
            hw = h["words"]
            for key in ["d", "1", "2", "3", "4", "5"]:
                text = got.get(slot, {}).get(key)
                if text is None:
                    print(f"MISSING {slot}|{key}")
                    bad += 1
                    continue
                w = len(text.split())
                if abs(w - hw) > tol:
                    print(f"LENGTH {name} {slot}|{key}: {w} words, human {hw} (+-{tol})")
                    bad += 1
                if key == "d":
                    defaults.append({"id": f"{slot}-d", "slot": slot, "text": text, "words": w, "human_words": hw})
                else:
                    cands.append({"slot": slot, "cand": int(key), "text": text, "words": w, "human_words": hw})
        (HERE / df).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in defaults))
        (HERE / cf).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in cands))
        print(f"{name}: {len(defaults)} defaults, {len(cands)} candidates")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
