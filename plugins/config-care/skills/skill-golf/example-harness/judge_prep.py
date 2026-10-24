#!/usr/bin/env python3
"""Prepare the blind title-test judging set.

model-golf: blind the labels, score each item in BOTH orders, keep only order-agreement, and use a
judge that is not competing in the comparison. Arm labels are stripped and replaced by opaque ids so
the judge cannot infer the condition from the filename or an ordering convention.
"""
import json, os, hashlib

D = os.path.dirname(os.path.abspath(__file__))


def opaque(cell):
    return "q" + hashlib.sha256(cell.encode()).hexdigest()[:8]


def main():
    rows = json.load(open(os.path.join(D, "pilot_extracted.json")))
    items, key = [], {}
    for r in rows:
        if r["knob"] != "OK":
            continue
        for i, q in enumerate(r["queries"]):
            oid = opaque(f"{r['cell']}#{i}")
            key[oid] = {"cell": r["cell"], "arm": r["arm"], "task": r["task"], "idx": i, "query": q}
            items.append({"id": oid, "task_need": r["task"], "query": q})

    # deterministic shuffle that does not group by arm: sort by the opaque id
    items.sort(key=lambda x: x["id"])
    json.dump(items, open(os.path.join(D, "judge_items.json"), "w"), indent=1)
    json.dump(key, open(os.path.join(D, "judge_key.json"), "w"), indent=1)
    print(f"{len(items)} queries to judge, from {len(set(v['cell'] for v in key.values()))} cells")
    print("items -> judge_items.json   (NO arm labels)")
    print("key   -> judge_key.json     (do not show the judge)")

    arms = {}
    for v in key.values():
        arms.setdefault(v["arm"], 0)
        arms[v["arm"]] += 1
    print("queries per arm (for your eyes only):", arms)


if __name__ == "__main__":
    main()
