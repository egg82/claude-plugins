#!/usr/bin/env python3
"""Pilot runner: one cell = (task, arm, rep). Collects only -- never grades.

Stamps the condition INSIDE each artifact (model-golf: two runs sharing an output dir with only the
directory name to tell them apart is unrecoverable). Refuses to start if another run is alive.
"""
import json, os, subprocess, sys, hashlib, argparse, concurrent.futures as cf

D = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(D, "pilot_runs")
LOCK = os.path.join(D, ".pilot.lock")
CFG = json.load(open(os.path.join(D, "tasks.json")))


def build_brief(task, arm):
    b = CFG["brief_template"]
    b = b.replace("{{ARM_LINE}}", CFG["arm_lines"][arm])
    b = b.replace("{{NEED}}", task["need"])
    assert "{{" not in b, "unsubstituted placeholder in brief"
    return b


def run_cell(task, arm, rep, timeout):
    brief = build_brief(task, arm)
    fp = hashlib.sha256(brief.encode()).hexdigest()[:12]
    name = f"{task['id']}_{arm}_r{rep}"
    path = os.path.join(OUT, name + ".json")
    if os.path.exists(path):
        return name, "skipped-exists"
    cmd = ["claude", "-p", brief, "--output-format", "stream-json", "--verbose",
           "--allowedTools", "WebSearch", "WebFetch", "Skill"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=OUT)
        raw = p.stdout
        err = p.stderr[-2000:]
        rc = p.returncode
    except subprocess.TimeoutExpired:
        raw, err, rc = "", "TIMEOUT", -9
    rec = {
        "cell": name, "task_id": task["id"], "task_kind": task["kind"],
        "arm": arm, "rep": rep,
        "brief_fingerprint": fp, "brief": brief,
        "returncode": rc, "stderr_tail": err,
        "stream": raw,
    }
    with open(path, "w") as f:
        json.dump(rec, f)
    return name, f"rc={rc} bytes={len(raw)}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--arms", default="A,B,C")
    ap.add_argument("--tasks", default="", help="comma ids, blank = all")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--concurrency", type=int, default=3)
    a = ap.parse_args()

    assert not os.path.exists(LOCK), f"another run may be alive: {LOCK} exists. Remove it if not."
    os.makedirs(OUT, exist_ok=True)
    open(LOCK, "w").write(str(os.getpid()))
    try:
        want = set(x for x in a.tasks.split(",") if x)
        tasks = [t for t in CFG["tasks"] if not want or t["id"] in want]
        arms = a.arms.split(",")
        cells = [(t, arm, r) for t in tasks for arm in arms for r in range(1, a.reps + 1)]
        print(f"{len(cells)} cells: {len(tasks)} tasks x {len(arms)} arms x {a.reps} reps")
        # all conditions of one task run concurrently -> cost is order-invariant re: prompt cache
        with cf.ThreadPoolExecutor(max_workers=a.concurrency) as ex:
            futs = {ex.submit(run_cell, t, arm, r, a.timeout): (t["id"], arm, r)
                    for (t, arm, r) in cells}
            for fut in cf.as_completed(futs):
                name, status = fut.result()
                print(f"  {name}: {status}", flush=True)
    finally:
        os.remove(LOCK)
    print("done ->", OUT)


if __name__ == "__main__":
    main()
