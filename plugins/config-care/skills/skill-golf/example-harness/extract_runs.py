#!/usr/bin/env python3
"""Parse pilot run artifacts -> per-cell facts. Extraction only; no grading, no judgement.

KNOB VERIFICATION lives here: arm A must load search-craft, B search-craft-v2, C nothing.
A cell failing knob verification is marked INVALID and must be discarded, not graded.
"""
import json, os, glob, sys, collections

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "pilot_runs")
EXPECT = {"A": "search-craft", "B": "search-craft-v2", "C": None}


def parse_stream(raw):
    """stream-json is one JSON object per line."""
    searches, fetches, skills, final, usage = [], [], [], None, {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        t = d.get("type")
        if t == "assistant":
            for b in (d.get("message") or {}).get("content", []) or []:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                inp = b.get("input") or {}
                if b.get("name") == "WebSearch":
                    searches.append(inp.get("query", ""))
                elif b.get("name") == "WebFetch":
                    fetches.append(inp.get("url", ""))
                elif b.get("name") == "Skill":
                    skills.append(inp.get("skill", ""))
        elif t == "result":
            final = d.get("result")
            usage = d.get("usage") or {}
            usage["total_cost_usd"] = d.get("total_cost_usd")
            usage["num_turns"] = d.get("num_turns")
    return searches, fetches, skills, final, usage


def main():
    files = sorted(glob.glob(os.path.join(OUT, "*.json")))
    if not files:
        print("no run artifacts in", OUT)
        return 1
    rows = []
    for f in files:
        rec = json.load(open(f))
        s, fe, sk, final, usage = parse_stream(rec.get("stream", ""))
        arm = rec["arm"]
        exp = EXPECT[arm]
        if exp is None:
            knob = "OK" if not sk else f"INVALID(loaded {sk})"
        else:
            knob = "OK" if exp in sk else f"INVALID(loaded {sk or 'nothing'})"
        rows.append({
            "cell": rec["cell"], "task": rec["task_id"], "kind": rec["task_kind"],
            "arm": arm, "rep": rec["rep"], "rc": rec["returncode"],
            "knob": knob, "skills": sk,
            "n_search": len(s), "n_fetch": len(fe),
            "queries": s, "fetches": fe,
            "answer": final, "usage": usage,
            "brief_fingerprint": rec["brief_fingerprint"],
        })
    json.dump(rows, open(os.path.join(D, "pilot_extracted.json"), "w"), indent=1)

    print(f"{'cell':16s} {'knob':28s} {'srch':>4s} {'ftch':>4s} {'cost$':>7s}  answer-head")
    for r in rows:
        c = r["usage"].get("total_cost_usd")
        cs = f"{c:.2f}" if isinstance(c, (int, float)) else "-"
        head = (r["answer"] or "").replace("\n", " ")[:60]
        print(f"{r['cell']:16s} {r['knob']:28s} {r['n_search']:4d} {r['n_fetch']:4d} {cs:>7s}  {head}")

    bad = [r for r in rows if r["knob"] != "OK"]
    print()
    print(f"KNOB VERIFICATION: {len(rows)-len(bad)}/{len(rows)} OK")
    for r in bad:
        print("  INVALID:", r["cell"], r["knob"])
    # fingerprint check: within a task, the 3 arms must differ ONLY by the arm line
    byt = collections.defaultdict(set)
    for r in rows:
        byt[r["task"]].add(r["brief_fingerprint"])
    for t, fps in sorted(byt.items()):
        print(f"  {t}: {len(fps)} distinct brief fingerprints (expect = number of arms run)")
    tot = sum(r["usage"].get("total_cost_usd") or 0 for r in rows)
    print(f"\nTOTAL api-equivalent cost: ${tot:.2f} over {len(rows)} cells")
    return 0


if __name__ == "__main__":
    sys.exit(main())
