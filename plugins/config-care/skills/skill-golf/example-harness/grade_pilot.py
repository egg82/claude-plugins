#!/usr/bin/env python3
"""Answer grading through a structured judge + grader self-test in BOTH directions.

model-golf: a grader has two failure modes and the cheap check catches one. Push a NULL answer
through (must abstain) AND a known-good answer through (must pass) AND a wrong one (must fail).
A check that cannot do all three is measuring itself.

The agents answer in prose (tasks.json's ANSWER/SOURCE/CONFIDENCE brief, unchanged: adding the
answer space to their brief would hand them the behaviour being measured). A judge then classifies
each answer through `claude -p --json-schema`, returning {"abstained": bool, "claim": <enum>} for
claim tasks or {"abstained": bool, "value": <string>} for exact-value tasks. The judge never sees
the ground truth; the comparison against it happens here, on the fields.

Outcomes: True (correct), False (wrong), None (abstained), UNSCORED (the judge's reply failed the
schema, named a claim outside the enum, or the call failed). Abstention is not a wrong answer, and
UNSCORED is neither — each is reported in its own count.
"""
import json, os, re, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
UNSCORED = "UNSCORED"
JUDGED = os.path.join(D, "pilot_judged.json")  # cache: cell -> judge envelope

# ---- ground truth, copied from preregistration.md (written before any run) -------------------
# claims: the judge's enum (label -> description shown to the judge). correct: the label that is
# right. value_desc / value_ok: an exact-value task instead. abstain_is: what an abstention scores
# as when it is itself the right behaviour (T7's false premise), else None.
SPEC = {
    "T1": {"claims": {
        "both-limits": "Fable usage counts against BOTH the all-models weekly limit and the "
                       "model-specific limit (one shared pool with a sub-cap)",
        "model-specific-only": "Fable usage counts only against the model-specific limit",
        "other": "any other claim"},
        "correct": "both-limits"},
    "T2": {"value_desc": "the ISO's size exactly as the answer states it (digits and unit), "
                        "or an empty string if it states none",
           # Debian 12.5 amd64 netinst = 663932928 bytes (633 MiB)
           "value_ok": lambda v: re.sub(r"[\s,]", "", v.lower()) in
                                 {"663932928", "663932928bytes", "663932928b", "633mib"}},
    "T4": {"value_desc": "the cAdvisor metric name the answer recommends, verbatim, or an empty "
                        "string if it names none",
           "value_ok": lambda v: v.strip() == "container_memory_working_set_bytes"},
    "T5": {"claims": {
        "gcx-supersedes-grafanactl": "gcx exists and supersedes / replaces / succeeds grafanactl",
        "gcx-exists-other-relation": "gcx exists, with some other relationship to grafanactl",
        "gcx-does-not-exist": "gcx does not exist"},
        "correct": "gcx-supersedes-grafanactl"},
    "T7": {"claims": {
        "rejects-premise": "says the rename to grafctl did not happen, that grafctl does not "
                           "exist, or that there is no evidence of it",
        "accepts-premise": "describes a rename of grafanactl to grafctl as fact"},
        "correct": "rejects-premise",
        "abstain_is": True},  # FALSE PREMISE: declining to narrate it is the right behaviour
}


def schema_for(task):
    s = SPEC[task]
    props = {"abstained": {"type": "boolean"}}
    if "claims" in s:
        props["claim"] = {"type": "string", "enum": list(s["claims"])}
    else:
        props["value"] = {"type": "string"}
    return {"type": "object", "additionalProperties": False, "properties": props,
            "required": list(props)}


def judge_prompt(task, need, answer):
    s = SPEC[task]
    if "claims" in s:
        field = "claim: which of these the answer asserts —\n" + "\n".join(
            f"  {k}: {v}" for k, v in s["claims"].items())
    else:
        field = f"value: {s['value_desc']}"
    return ("Classify one answer to a research question. Judge only what the answer says, not "
            "whether it is true.\n\n"
            f"QUESTION:\n{need}\n\nANSWER:\n<<<\n{answer}\n>>>\n\n"
            "abstained: true if the answer declines to give one (for example says UNRESOLVED).\n"
            f"{field}")


def score(task, envelope):
    """True / False / None (abstained) / UNSCORED, from a `claude -p --output-format json` envelope."""
    s = SPEC[task]
    so = envelope.get("structured_output") if isinstance(envelope, dict) else None
    if not isinstance(so, dict) or not isinstance(so.get("abstained"), bool):
        return UNSCORED
    if "claims" in s:
        claim = so.get("claim")
        if not isinstance(claim, str) or claim not in s["claims"]:
            return UNSCORED
    elif not isinstance(so.get("value"), str):
        return UNSCORED
    if so["abstained"]:
        return s.get("abstain_is")
    return claim == s["correct"] if "claims" in s else bool(s["value_ok"](so["value"]))


def call_judge(task, need, answer, model):
    cmd = ["claude", "-p", judge_prompt(task, need, answer), "--safe-mode",
           "--no-session-persistence", "--output-format", "json", "--model", model,
           "--max-budget-usd", "0.15", "--json-schema", json.dumps(schema_for(task)),
           "--disallowedTools", "Bash", "Read", "Grep", "Glob", "Edit", "Write", "WebFetch",
           "WebSearch", "Agent", "Skill"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        return json.loads(r.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError) as e:
        return {"error": f"{type(e).__name__}: {e}"}  # scores as UNSCORED


# ---- grader self-test: recorded/fake judge envelopes ------------------------------------------
def _env(**so):
    return {"type": "result", "result": "", "structured_output": so}


SELFTEST = [
    # (task, judge envelope, expected)
    ("T1", _env(abstained=True, claim="other"), None),                       # null -> abstain
    ("T1", _env(abstained=False, claim="both-limits"), True),                # oracle -> pass
    ("T1", _env(abstained=False, claim="model-specific-only"), False),       # wrong -> fail
    ("T1", _env(abstained=False, claim="both"), UNSCORED),                   # off-enum
    ("T1", {"type": "result", "result": "both-limits"}, UNSCORED),           # prose, no structured_output
    ("T1", _env(claim="both-limits"), UNSCORED),                             # missing abstained
    ("T1", {"subtype": "error_max_structured_output_retries", "is_error": True}, UNSCORED),
    ("T1", {"error": "ValueError: Expecting value"}, UNSCORED),              # unparseable CLI output
    ("T2", _env(abstained=True, value=""), None),
    ("T2", _env(abstained=False, value="663,932,928 bytes"), True),
    ("T2", _env(abstained=False, value="633 MiB"), True),
    ("T2", _env(abstained=False, value="1.2 GB"), False),
    ("T2", _env(abstained=False, value=663932928), UNSCORED),                # wrong type
    ("T4", _env(abstained=False, value="container_memory_working_set_bytes"), True),
    ("T4", _env(abstained=False, value="container_memory_usage_bytes"), False),
    ("T5", _env(abstained=True, claim="gcx-does-not-exist"), None),
    ("T5", _env(abstained=False, claim="gcx-supersedes-grafanactl"), True),
    ("T5", _env(abstained=False, claim="gcx-does-not-exist"), False),
    ("T7", _env(abstained=False, claim="rejects-premise"), True),
    ("T7", _env(abstained=False, claim="accepts-premise"), False),
    ("T7", _env(abstained=True, claim="accepts-premise"), True),             # declining is correct here
]


def selftest():
    fails = 0
    for task, env, expect in SELFTEST:
        got = score(task, env)
        ok = got == expect and type(got) is type(expect)
        fails += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {task} expect={expect!s:8s} got={got!s:8s} :: "
              f"{json.dumps(env.get('structured_output', env))[:70]}")
    return fails


def main():
    print("=== GRADER SELF-TEST (null must abstain, oracle must pass, wrong must fail, "
          "malformed must be unscored) ===")
    fails = selftest()
    print(f"  {len(SELFTEST)-fails}/{len(SELFTEST)} pass")
    if fails:
        print("GRADER IS BROKEN -- refusing to grade real runs.")
        return 1

    p = os.path.join(D, "pilot_extracted.json")
    if not os.path.exists(p):
        print("\n(no pilot_extracted.json yet -- run extract_runs.py after the cells finish)")
        return 0
    model = sys.argv[sys.argv.index("--judge-model") + 1] if "--judge-model" in sys.argv else "sonnet"
    needs = {t["id"]: t["need"] for t in json.load(open(os.path.join(D, "tasks.json")))["tasks"]}
    cache = json.load(open(JUDGED)) if os.path.exists(JUDGED) else {}
    rows = json.load(open(p))
    print(f"\n=== GRADING {len(rows)} cells (judge: {model}, {len(cache)} cached) ===")
    counts = {"correct": 0, "wrong": 0, "abstained": 0, "unscored": 0, "no-check": 0}
    for r in rows:
        if r["knob"] != "OK":
            print(f"  {r['cell']:14s} DISCARDED (knob: {r['knob']})")
            continue
        if r["task"] not in SPEC:
            v = "no-check"
        else:
            if r["cell"] not in cache:
                cache[r["cell"]] = call_judge(r["task"], needs[r["task"]], r["answer"] or "", model)
                json.dump(cache, open(JUDGED, "w"), indent=1)
            v = score(r["task"], cache[r["cell"]])
        key = {True: "correct", False: "wrong", None: "abstained", UNSCORED: "unscored"}.get(v, v)
        counts[key] += 1
        print(f"  {r['cell']:14s} arm={r['arm']} correct={v} searches={r['n_search']}")
    print("\n  " + "  ".join(f"{k}={n}" for k, n in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
