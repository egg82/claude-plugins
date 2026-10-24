#!/usr/bin/env python3
"""TEMPLATE — carries constants from the run it came from. Replace before reuse:
  FINGERPRINT  task-identifying substrings of YOUR prompts
  EXPECT       per task: the JSON shape the prompt asks for, and the check on that field
  PRICE        $/MTok per model; every model you run MUST have an entry (a missing
               one silently halves that model's reported cost)
Grade the golf matrix from transcripts, independent of any agent's self-report.

Identification is by the PROMPT recorded in the spawn record (which task) and the model
recorded in the sidecar (which condition) — never by an agent's description or its own
summary of what happened. Benchmark runners are excluded from the graded set, identified
structurally: an agent that spawned agents (another sidecar names it as parentAgentId,
or its transcript holds an Agent tool call) is a runner.

Answers are read from a structured field, never from prose. Every task prompt ends with
answer_instruction(task): the agent's final reply must end with a fenced ```json block
holding {"answer": <value of the stated type>}. The check compares that field. A reply
with no such block, unparseable JSON, or a value of the wrong type is UNSCORED and
reported in its own column — never a pass, never a fail.

    grade.py             grade the runs on disk
    grade.py --selftest  push recorded good/wrong/malformed answers through every check
"""
import json, glob, os, re, sys, collections

ROOT = os.path.expanduser("~/.claude/projects")
GOLF = os.environ.get("GOLF_DIR", "/tmp/golf")   # where the run artifacts landed

# Fingerprint -> task id. Distinctive substring of each task's prompt.
FINGERPRINT = {
    "strip heredoc BODIES": "T1_retrieval",
    "Run `python3 tally.py`. It crashes.": "T2_rootcause",
    "total capacity of zero is skipped": "T3_multistep",
    "spawnDepth of exactly 2": "S1_count",
    "MOST agents, across every session": "S2_toolloop",
    "block any command containing the string": "T6_judgment",
    "List every hook EVENT configured": "S3_hooks",
    "contain the most files": "S4_skilldirs",
    "Find up to THREE real defects": "R1_bughunt",
    "failure state": "R2_research",
}

PASS, FAIL, UNSCORED, JUDGE = "pass", "fail", "UNSCORED", "judge"


class Unscored(Exception):
    """The answer is not in the shape the prompt asked for."""


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _str_list(v):
    if not (isinstance(v, list) and all(isinstance(x, str) for x in v)):
        raise Unscored("expected a list of strings")
    return v


def _obj(v, **types):
    if not isinstance(v, dict):
        raise Unscored("expected an object")
    for k, t in types.items():
        if k not in v or not t(v[k]):
            raise Unscored(f"field {k!r} missing or wrong type")
    return v


_s = lambda x: isinstance(x, str)


def _check_T1(a):
    a = _obj(a, file=_s, function=_s)
    return os.path.basename(a["file"]) == "bash-footgun-gate.sh" and a["function"] == "strip_heredocs"


def _check_T2(a):
    a = _obj(a, exception=_s, culprit=_s)
    return a["exception"] == "ZeroDivisionError" and a["culprit"] in ("host1", "c.json")


def _check_T3(a):
    if not _is_num(a):
        raise Unscored("expected a number")
    return abs(a - 48.3) <= 0.05


def _check_S1(a):
    if not _is_int(a):
        raise Unscored("expected an integer")
    return a == 15


def _check_S2(a):
    # MOVING TARGET: this benchmark spawns depth-1 agents while it runs, so the true
    # depth-1 count drifted from 430 to 446 during the window. Any value in that band is
    # correct; anything outside it is a genuine error, not staleness.
    if not _is_int(a):
        raise Unscored("expected an integer")
    return 425 <= a <= 455


def _check_S3(a):
    a = _obj(a, events=lambda v: isinstance(v, list) and all(_s(x) for x in v),
             pretooluse_count=_is_int)
    want = {"PostCompact", "PreCompact", "PreToolUse", "SessionStart", "SubagentStop"}
    return set(a["events"]) == want and a["pretooluse_count"] == 3


def _check_S4(a):
    # Pre-registered criterion: all three named; extra entries are not penalised.
    return {"skill-a", "skill-b", "skill-c"} <= set(_str_list(a))


# task -> (shape the prompt asks for, check). check is None where a script cannot decide:
# those rows are JUDGE — graded by a judge returning an enum, or (R1/R2) by resolving
# citations with verify-citations.py — and are left out of pass rates here.
EXPECT = {
    "T1_retrieval": ('{"file": "<file name>", "function": "<function name>"}', _check_T1),
    "T2_rootcause": ('{"exception": "<exception class name>", "culprit": "<host or file that '
                     'triggers it>"}', _check_T2),
    "T3_multistep": ("<number>", _check_T3),
    "S1_count": ("<integer>", _check_S1),
    "S2_toolloop": ("<integer>", _check_S2),
    "S3_hooks": ('{"events": ["<event name>", ...], "pretooluse_count": <integer>}', _check_S3),
    "S4_skilldirs": ('["<directory name>", ...]', _check_S4),
    "T6_judgment": ("<your answer as a string>", None),
    "R1_bughunt": ("<your findings as a string>", None),
    "R2_research": ("<your findings as a string>", None),
}


def answer_instruction(task):
    """The sentence appended to a task's prompt. Its byte-identity across arms matters."""
    return ("\n\nEnd your reply with a fenced ```json code block containing exactly one JSON "
            f'object of the form {{"answer": {EXPECT[task][0]}}}. Nothing after the block.')


FENCE = re.compile(r"```json[ \t]*\n(.*?)\n[ \t]*```", re.S)


def extract_answer(text):
    """The `answer` field of the LAST ```json block in the reply. Raises Unscored."""
    blocks = FENCE.findall(text or "")
    if not blocks:
        raise Unscored("no ```json block")
    try:
        obj = json.loads(blocks[-1])
    except ValueError as e:
        raise Unscored(f"json: {e}")
    if not isinstance(obj, dict) or "answer" not in obj:
        raise Unscored('block is not an object with an "answer" field')
    return obj["answer"]


def grade(task, text):
    """(status, detail): status is PASS / FAIL / UNSCORED / JUDGE."""
    shape, check = EXPECT.get(task, (None, None))
    if check is None:
        return JUDGE, ""
    try:
        return (PASS if check(extract_answer(text)) else FAIL), ""
    except Unscored as e:
        return UNSCORED, str(e)


# ----------------------------------------------------------------------------- self-test

def _reply(answer_json):
    return f"Here is what I found.\n\n```json\n{answer_json}\n```\n"


SELFTEST = [  # (task, reply, expected status)
    ("S1_count", _reply('{"answer": 15}'), PASS),
    ("S1_count", _reply('{"answer": 16}'), FAIL),
    ("S1_count", "There are 15 such agents.", UNSCORED),                      # prose, no block
    ("S1_count", _reply('{"answer": "15"}'), UNSCORED),                       # wrong type
    ("S1_count", _reply('{"answer": 15,}'), UNSCORED),                        # malformed JSON
    # the old path passed this on "15 appears anywhere"; the field says 12
    ("S1_count", "Of 15 sessions checked:\n" + _reply('{"answer": 12}'), FAIL),
    ("S2_toolloop", _reply('{"answer": 446}'), PASS),
    ("S2_toolloop", "depth 1, 430 agents\n" + _reply('{"answer": 12}'), FAIL),
    ("T3_multistep", _reply('{"answer": 48.3}'), PASS),
    ("T3_multistep", _reply('{"answer": 48.0}'), FAIL),
    ("T1_retrieval", _reply('{"answer": {"file": "hooks/bash-footgun-gate.sh", '
                            '"function": "strip_heredocs"}}'), PASS),
    ("T1_retrieval", _reply('{"answer": {"file": "bash-footgun-gate.sh"}}'), UNSCORED),
    ("T2_rootcause", _reply('{"answer": {"exception": "ZeroDivisionError", "culprit": "host1"}}'),
     PASS),
    ("T2_rootcause", _reply('{"answer": {"exception": "KeyError", "culprit": "host1"}}'), FAIL),
    ("S3_hooks", _reply('{"answer": {"events": ["PreToolUse", "PostCompact", "PreCompact", '
                        '"SessionStart", "SubagentStop"], "pretooluse_count": 3}}'), PASS),
    ("S3_hooks", _reply('{"answer": {"events": ["PreToolUse"], "pretooluse_count": 3}}'), FAIL),
    ("S4_skilldirs", _reply('{"answer": ["skill-a", "skill-b", '
                            '"skill-c"]}'), PASS),
    ("S4_skilldirs", _reply('{"answer": "skill-a"}'), UNSCORED),
    ("T6_judgment", _reply('{"answer": "anything"}'), JUDGE),
    # the LAST block is the answer, not an example quoted earlier
    ("S1_count", _reply('{"answer": 3}') + "Final:\n" + _reply('{"answer": 15}'), PASS),
]


def _selftest_runner():
    """Structural runner detection against fake sidecars/transcripts."""
    metas = [{"agentId": "leaf2", "spawnDepth": 2, "parentAgentId": "run1",
              "description": "golf runner leaf"},     # words in a description must not matter
             {"agentId": "run1", "spawnDepth": 1, "description": "S1 count"},
             {"agentId": "solo", "spawnDepth": 1, "description": "matrix runner"}]
    parents = {m["parentAgentId"] for m in metas if m.get("parentAgentId")}
    cases = [("run1", False, True), ("leaf2", False, False), ("solo", False, False),
             ("solo", True, True)]  # (agent, transcript has an Agent call, expected)
    return [(f"is_runner({a}, spawned={s})", is_runner(a, parents, s) == want)
            for a, s, want in cases]


def selftest():
    fails = 0
    for task, reply, want in SELFTEST:
        got, why = grade(task, reply)
        fails += got != want
        print(f"  [{'ok' if got == want else 'FAIL'}] {task:13} want={want:<8} got={got:<8} {why}")
    for name, ok in _selftest_runner():
        fails += not ok
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    print(f"selftest: {'PASS' if not fails else f'{fails} FAILED'}")
    return 1 if fails else 0


# ----------------------------------------------------------------------------- transcripts

def spawn_prompts():
    """agentId -> task from spawn records anywhere in the tree."""
    out = {}
    for path in glob.glob(ROOT + "/**/*.jsonl", recursive=True):
        for line in open(path, errors="replace"):
            if '"agentId"' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            t = d.get("toolUseResult")
            if not isinstance(t, dict) or not t.get("agentId") or "prompt" not in t:
                continue
            p = t["prompt"] or ""
            for fp, task in FINGERPRINT.items():
                if fp in p:
                    out[t["agentId"]] = task
                    break
    return out


def transcript(agent_id):
    hits = glob.glob(f"{ROOT}/*/*/subagents/agent-{agent_id}.jsonl")
    if not hits:
        return None
    final, usage, calls, resolved, handback, spawned = "", collections.Counter(), 0, None, None, False
    for line in open(hits[0], errors="replace"):
        if '"usage"' not in line and '"tool_use"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        m = d.get("message") or {}
        if m.get("role") == "assistant":
            if (m.get("model") or "").startswith("claude-"):  # skip "<synthetic>" error turns
                resolved = m["model"]  # the API's answer, not the alias asked for
            txt = "".join(b.get("text", "") for b in (m.get("content") or [])
                          if isinstance(b, dict) and b.get("type") == "text")
            if txt.strip():
                final = txt
            # Agents that return via SubagentHandback put the answer in the tool call and
            # end on a sign-off ("Report delivered."), so the last text block is not the answer.
            for b in m.get("content") or []:
                if not isinstance(b, dict) or b.get("type") != "tool_use":
                    continue
                if b.get("name") == "SubagentHandback":
                    handback = (b.get("input") or {}).get("message") or handback
                if b.get("name") == "Agent":
                    spawned = True
            calls += sum(1 for b in (m.get("content") or [])
                         if isinstance(b, dict) and b.get("type") == "tool_use")
        u = m.get("usage") or {}
        for k, f in (("in", "input_tokens"), ("out", "output_tokens"),
                     ("cr", "cache_read_input_tokens"), ("cw", "cache_creation_input_tokens")):
            usage[k] += u.get(f, 0)
    return handback or final, usage, calls, resolved, spawned


def model_of(agent_id):
    hits = glob.glob(f"{ROOT}/*/*/subagents/agent-{agent_id}.meta.json")
    if not hits:
        return "?"
    try:
        return json.load(open(hits[0])).get("model") or "inherited(opus)"
    except Exception:
        return "?"


# Keyed by substring of the RESOLVED model id, first match wins, so specific ids precede their
# family. The sidecar records only the alias, and `opus` has meant both 5 and 5.5.
PRICE = {"opus-5-5": (4, 20), "opus": (5, 25), "sonnet": (2, 10), "haiku": (1, 5),
         "fable": (10, 50)}  # fable is 2x opus — omitting it silently priced fable as opus

def price_of(model):
    return next((v for k, v in PRICE.items() if k in model), None)


def parent_ids():
    """Every agentId some sidecar names as its parentAgentId (the harness writes it at depth >= 2)."""
    out = set()
    for f in glob.glob(f"{ROOT}/*/*/subagents/agent-*.meta.json"):
        try:
            p = json.load(open(f)).get("parentAgentId")
        except Exception:
            continue
        if p:
            out.add(p)
    return out


def is_runner(aid, parents, spawned_agents):
    """Benchmark runners quote the task prompts, so they match the fingerprints too.
    Only leaves are graded; a runner's preamble is not an answer. A runner is an agent that
    spawned agents — read from harness-written structure, never from its description."""
    return aid in parents or spawned_agents


def main():
    if "--selftest" in sys.argv[1:]:
        return selftest()
    spawned = spawn_prompts()
    parents = parent_ids()
    rows, n_runner, n_no_transcript = [], 0, 0
    for aid, task in spawned.items():
        tr = transcript(aid)
        if is_runner(aid, parents, bool(tr and tr[4])):
            n_runner += 1
            continue
        if not tr:
            n_no_transcript += 1
            continue
        final, u, calls, resolved, _ = tr
        model = resolved or model_of(aid)
        price = price_of(model)
        if price is None:
            # Never default: a fallback prices an unknown model at some other model's rate and the
            # table still looks fine. "?" means the sidecar was missing or unparseable, i.e. the run
            # is unattributable — that is a data problem to fix, not a row to price.
            raise SystemExit(
                f"PRICE has no entry for model {model!r} (agent {aid[:12]}, task {task}).\n"
                f"  Add it to PRICE, or — if the model is '?' — the sidecar for that agent is "
                f"missing/unparseable and the run cannot be attributed.")
        pin, pout = price
        # Cold-equivalent: price cache reads at full input rate. Order-invariant.
        cold = (u["in"] + u["cw"] + u["cr"]) * pin / 1e6 + u["out"] * pout / 1e6
        status, why = grade(task, final)
        rows.append({
            "task": task, "model": model, "agent": aid[:12], "status": status, "why": why,
            "calls": calls, "tokens": u["in"] + u["cw"] + u["cr"] + u["out"], "cold_usd": cold,
            "answer": re.sub(r"\s+", " ", final)[-70:],
        })

    # Refuse on an empty run set rather than printing an empty table. With no rows this script printed
    # its headers and exited 0, which on a grading tool is indistinguishable from "graded, and nothing
    # passed" — the falsely-clean shape, where a broken extractor and a genuinely empty result look the
    # same. The check has to sit BEFORE the first print: once a table is on screen the run reads as
    # having happened. verify-citations.py refuses the same way; this is that convention, applied here.
    if not rows:
        raise SystemExit(
            f"REFUSING: no gradeable runs found under {ROOT}.\n"
            f"  Nothing was graded — this is NOT 'graded, nothing passed'.\n"
            f"  spawn records matching a FINGERPRINT: {len(spawned)}"
            f"  (excluded as runners: {n_runner}; no transcript on disk: {n_no_transcript})\n"
            f"  Read those three numbers rather than guessing: 0 matches means FINGERPRINT does not\n"
            f"  match the prompts actually run (task-name drift) or ROOT points at a store that does\n"
            f"  not hold this run; a non-zero match with 0 rows means the transcripts are missing.\n"
            f"  Check which before reading anything into a zero.")

    rows.sort(key=lambda r: (r["task"], r["model"]))
    print(f"{'task':14} {'model':16} {'status':>8} {'calls':>5} {'tokens':>9} {'cold$':>8}  answer tail")
    for r in rows:
        why = f"  [{r['why']}]" if r["why"] else ""
        print(f"{r['task']:14} {r['model']:16} {r['status']:>8} {r['calls']:>5} "
              f"{r['tokens']:>9,} {r['cold_usd']:>8.4f}  {r['answer']}{why}")

    print("\n=== per-model aggregate ===  (pass rate is over pass+fail only; unscored and judge rows "
          "are counted, not folded in)")
    agg = collections.defaultdict(list)
    for r in rows:
        agg[r["model"]].append(r)
    print(f"{'model':16} {'n':>3} {'pass rate':>10} {'unscored':>9} {'judge':>6} {'med calls':>10} "
          f"{'med tokens':>11} {'med cold$':>10}")
    for m, rs in sorted(agg.items()):
        c = collections.Counter(r["status"] for r in rs)
        scored = c[PASS] + c[FAIL]
        pr = f"{c[PASS] / scored:.0%}" if scored else "—"
        med = lambda k: sorted(r[k] for r in rs)[len(rs) // 2]
        print(f"{m:16} {len(rs):>3} {pr:>10} {c[UNSCORED]:>9} {c[JUDGE]:>6} {med('calls'):>10} "
              f"{med('tokens'):>11,} {med('cold_usd'):>10.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
