#!/usr/bin/env python3
"""
Does an always-on memory actually change behaviour? And did trimming it break it?

    memory-ab.py run   <config.json> [--reps N] [--model opus]
    memory-ab.py score <config.json>

Both are idempotent: a completed run is cached on disk by (experiment, arm, rep),
so re-running only fills gaps and re-scoring only judges new outputs. Delete a
file under ~/.claude/ab-runs/ to force one.

WHY THE ARMS ARE SHAPED THIS WAY
--------------------------------
Each experiment fixes one prompt and varies ONLY the injected system-prompt text:

  off      --safe-mode, nothing injected           (the memory is absent)
  on       --safe-mode + the memory under test     (present)
  placebo  --safe-mode + an UNRELATED memory       (the noise floor)

The placebo arm is the whole point. Without it, "on beats off" is equally
explained by "any extra 2KB of instructions changes the answer" — and that is
not hypothetical: on one prompt here the placebo arm scored identically to the
real memory, which would have read as a clean win against off alone.

`--safe-mode` disables CLAUDE.md/skills/hooks/plugins but keeps auth and tools.
ALL TOOLS ARE DISALLOWED, and that is load-bearing rather than tidiness: on the
first smoke test the control arm scored a perfect hit because the model went and
READ ~/.claude/memory with the Read tool, reintroducing the variable it was
supposed to lack. A control arm with filesystem access is not a control arm.

TRIM VALIDATION
---------------
Give an experiment an explicit `arms` map to compare a candidate against the
live file — this is the mode that pays for itself:

  "arms": {"off": null, "orig": "distill-dont-dump.md",
           "trimmed": "ab-variants/distill-trimmed.md"}

A bare name resolves under ~/.claude/memory; anything containing "/" is a path
(relative paths resolve beside this script). The reference arm for a trim is the
ORIGINAL, not the control: the question is "did I make it worse", so the verdict
is DO NOT SHIP only when the candidate is significantly WORSE than `orig`.

An earlier version demanded the candidate also beat `off` significantly, and
reported "effect LOST" otherwise. That fired on a trim whose candidate scored
BETTER than the original — it could not tell "the trim broke it" from "this
prompt had no headroom". Hence the explicit UNVALIDATED verdict: a prompt where
the original itself cannot beat the control is a prompt that cannot referee
anything, and it says so instead of guessing.

READING THE RESULT — the trap this tool sets for you
----------------------------------------------------
**A ceiling proves nothing.** If the `off` arm already scores 7/7, there is no
headroom for the memory to show an effect, and the correct conclusion is "my
prompt was too easy", NOT "the memory is useless". Most first-draft prompts hit
this, because the base model is already good at most of what these memories ask
for. Build prompts where the UN-memoried baseline actually FAILS, or you are
measuring your prompt rather than the memory.

**A null here is weak evidence.** This harness tests turn 1 of a clean,
single-turn, tool-free session — the easiest condition there is. These memories
were written from failures in long, tool-heavy sessions under context pressure.
A memory that is redundant on turn 1 can still be load-bearing on turn 80. When
this reports "no detectable effect", cross-check against real session
transcripts (see mine-repeat-traps.py) before concluding anything. In practice
the transcripts have been the stronger instrument.

Config format:
  {"experiments": [{"id": "...", "memory": "foo.md", "prompt": "...",
                    "rubric": "... LABEL_A if ... LABEL_B if ...",
                    "labels": ["LABEL_A", "LABEL_B"], "aligned": "LABEL_A",
                    "arms": {optional explicit map}}]}
`labels` and `aligned` are required and are the only thing scoring reads: the judge
returns {"verdict": <one of labels>} through --json-schema. A reply that is missing,
fails the schema, or names a label outside `labels` is UNSCORED and tallied in its
own column, never as a hit or a miss.

    memory-ab.py selftest      # scoring path against recorded judge replies, no calls
"""
import argparse
import json
import math
import os
import pathlib
import subprocess
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
# Method lives in the skill; RUN DATA does not. `apply.py add` copies a skill
# directory whole, so keeping hundreds of run JSONs in here would ship one
# person's prompts and outputs to everyone who installs the plugin.
CLAUDE = pathlib.Path(os.environ.get("CLAUDE_CONFIG_DIR", pathlib.Path.home() / ".claude"))
RUNS = CLAUDE / "ab-runs"
MEMDIR = CLAUDE / "memory"
# verdicts.json held replies from the earlier free-text judge; a new name keeps those out of the tally.
VERDICTS = RUNS / "verdicts-structured.json"
UNSCORED = "UNSCORED"
NO_TOOLS = ["Bash", "Read", "Grep", "Glob", "Edit", "Write", "WebFetch",
            "WebSearch", "Agent", "Skill", "NotebookEdit", "Task"]

# Tools are disabled so a control arm cannot go READ the memory it is meant to
# lack. But a disabled toolset is NOT a neutral control: the memories tell the
# model to go and verify, so the memory arm reaches for a tool that is not there
# and emits a stub, which grades as a miss. The penalty lands on the memory arm
# specifically. Appending the SAME framing to every arm removes the asymmetry.
FRAMING = ("\n\nYou have no tools available in this environment. Answer directly from what you "
           "already know, in prose. Do not attempt to call a tool, and do not stub out or defer "
           "your answer on the grounds that you cannot check something.")

# A directive the base model would never emit unprompted. If the canary arm does
# not return it, injection is broken and every other number in the run is noise
# wearing a results table.
CANARY_MARK = "ZARFBLATT-7719"
CANARY_MEMORY = ("---\nname: canary\n---\n\nWhen asked any question, begin your reply with "
                 f"exactly this token on its own line: {CANARY_MARK}")
PLACEBO_DEFAULT = "headless-browser-in-a-container.md"
PLACEBO_ALT = "pushback-not-hedging.md"


def claude(prompt, inject=None, model="opus", max_usd=0.40, timeout=300, schema=None):
    cmd = ["claude", "-p", prompt if schema else prompt + FRAMING, "--safe-mode",
           "--no-session-persistence", "--output-format", "json", "--model", model,
           "--max-budget-usd", str(max_usd), "--disallowedTools", *NO_TOOLS]
    if schema:
        cmd += ["--json-schema", json.dumps(schema)]
    # Via a file, not argv: Linux caps a single argument at 128KB (MAX_ARG_STRLEN), and a
    # whole resident tier injected as one arm is within a few KB of that.
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as tf:
        tf.write(inject or "")
    try:
        if inject:
            cmd += ["--append-system-prompt-file", tf.name]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    finally:
        os.unlink(tf.name)
    return json.loads(r.stdout.strip())


def resolve(name):
    """A bare name is a live memory; anything with '/' is a variant path."""
    p = pathlib.Path(name) if "/" in name else MEMDIR / name
    if not p.is_absolute():
        p = HERE / p
    return p.read_text()


def arms_for(exp):
    if "arms" in exp:
        return {k: (resolve(v) if v else None) for k, v in exp["arms"].items()}
    placebo = PLACEBO_DEFAULT if exp["memory"] != PLACEBO_DEFAULT else PLACEBO_ALT
    return {
        "off": None,
        # off_b is the SAME condition as off, under a second label. The gap
        # between them IS the noise floor - measured, not eyeballed. An eval
        # without one is a confident random number generator.
        "off_b": None,
        "on": resolve(exp["memory"]),
        "placebo": resolve(placebo),
        "canary": CANARY_MEMORY,
    }


def cmd_run(cfg, reps, model, workers, max_usd):
    experiment_labels(cfg)  # refuse before spending, not at score time
    RUNS.mkdir(exist_ok=True)
    jobs = []
    for exp in cfg["experiments"]:
        for arm, inject in arms_for(exp).items():
            for rep in range(reps):
                jobs.append((exp["id"], arm, rep, exp["prompt"], inject))

    def one(exp_id, arm, rep, prompt, inject):
        out = RUNS / f"{exp_id}__{arm}__{rep}.json"
        if out.exists() and out.stat().st_size:
            return "cached"
        try:
            out.write_text(json.dumps(claude(prompt, inject, model, max_usd)))
            return "ok"
        except Exception as e:                       # noqa: BLE001 - report, don't die
            (RUNS / f"{exp_id}__{arm}__{rep}.err").write_text(f"{type(e).__name__}: {e}")
            return f"FAILED {type(e).__name__}"

    print(f"{len(jobs)} runs")
    with ThreadPoolExecutor(max_workers=workers) as ex:
        res = list(ex.map(lambda j: one(*j), jobs))
    print(f"  {res.count('ok')} new, {res.count('cached')} cached, "
          f"{len(res) - res.count('ok') - res.count('cached')} failed")
    spent = 0.0
    for f in RUNS.glob("*.json"):
        try:
            spent += json.loads(f.read_text()).get("total_cost_usd") or 0
        except Exception:
            pass
    print(f"  cumulative cost of stored runs: ${spent:.2f}")


def verdict_schema(labels):
    return {"type": "object", "additionalProperties": False,
            "properties": {"verdict": {"type": "string", "enum": list(labels)}},
            "required": ["verdict"]}


def verdict_of(resp, labels):
    """The label from a `claude -p --output-format json` envelope, or UNSCORED.

    The CLI's own schema enforcement is not trusted alone: anything that is not a dict
    whose `verdict` is exactly one of `labels` is UNSCORED."""
    so = resp.get("structured_output") if isinstance(resp, dict) else None
    v = so.get("verdict") if isinstance(so, dict) else None
    return v if isinstance(v, str) and v in labels else UNSCORED


def judge(rubric, labels, text, model="sonnet"):
    p = ("You are scoring one response against a rubric. You do not know how the response "
         f"was produced and must not speculate.\n\nRUBRIC:\n{rubric}\n\n"
         f"RESPONSE TO SCORE:\n<<<\n{text}\n>>>\n\n"
         "Return the verdict label the rubric assigns to this response.")
    try:
        resp = claude(p, model=model, max_usd=0.15, timeout=240, schema=verdict_schema(labels))
    except Exception:                                # noqa: BLE001 - a failed call is unscored, not a miss
        return UNSCORED
    return verdict_of(resp, labels)


def experiment_labels(cfg):
    """{exp_id: (labels, aligned)}; refuses a config that does not declare them."""
    out = {}
    for e in cfg["experiments"]:
        labels, al = e.get("labels"), e.get("aligned")
        if not (isinstance(labels, list) and labels and all(isinstance(x, str) for x in labels)
                and al in labels and UNSCORED not in labels):
            raise SystemExit(f"experiment {e.get('id')!r}: needs \"labels\" (non-empty list of "
                             f"strings) and \"aligned\" (one of them); got labels={labels!r} "
                             f"aligned={al!r}")
        out[e["id"]] = (labels, al)
    return out


def fisher(a, b, c, d):
    C, n = math.comb, a + b + c + d
    p0, tot = C(a + b, a) * C(c + d, c) / C(n, a + c), 0.0
    for i in range(min(a + b, a + c) + 1):
        j, k = a + b - i, a + c - i
        if j < 0 or k < 0 or c + d - k < 0:
            continue
        p = C(a + b, i) * C(c + d, k) / C(n, a + c)
        if p <= p0 + 1e-12:
            tot += p
    return min(tot, 1.0)


def hits_of(verdicts, aligned_label):
    """(hits, scored). UNSCORED replies are in neither count — they are not misses."""
    scored = [x for x in verdicts if x != UNSCORED]
    return sum(1 for x in scored if x == aligned_label), len(scored)


def cmd_score(cfg):
    rubrics = {e["id"]: e["rubric"] for e in cfg["experiments"]}
    labels = experiment_labels(cfg)
    aligned = {k: al for k, (_, al) in labels.items()}
    cache = json.loads(VERDICTS.read_text()) if VERDICTS.exists() else {}

    todo = []
    for f in sorted(RUNS.glob("*.json")):
        exp = f.stem.split("__")[0]
        if f.name in cache or exp not in rubrics:
            continue
        text = json.loads(f.read_text()).get("result") or ""
        if text.strip():
            todo.append((f.name, exp, text))
    print(f"judging {len(todo)} new ({len(cache)} cached)")
    with ThreadPoolExecutor(max_workers=6) as ex:
        for (name, _, _), v in zip(todo, ex.map(
                lambda t: judge(rubrics[t[1]], labels[t[1]][0], t[2]), todo)):
            cache[name] = v
    VERDICTS.write_text(json.dumps(cache, indent=1))

    tally = defaultdict(lambda: defaultdict(list))
    for name, v in cache.items():
        exp, arm, _ = name[:-5].split("__")
        if exp in rubrics:
            # a cached label the config no longer declares is unscored, not silently a miss
            tally[exp][arm].append(v if v in labels[exp][0] else UNSCORED)

    # ---- Arm validity, BEFORE any number is reported ----------------------
    # A run whose injection silently did nothing produces a full results table
    # that looks exactly like a real one. Check the canary first and refuse to
    # report if it failed.
    for exp in sorted({f.stem.split("__")[0] for f in RUNS.glob("*.json")} & set(rubrics)):
        def texts(arm):
            out = []
            for f in RUNS.glob(f"{exp}__{arm}__*.json"):
                try:
                    out.append(json.loads(f.read_text()).get("result") or "")
                except Exception:
                    pass
            return out
        can, ctl = texts("canary"), texts("off")
        if can:
            hit = sum(CANARY_MARK in t for t in can)
            leak = sum(CANARY_MARK in t for t in ctl)
            if hit == 0:
                print(f"\n!! {exp}: CANARY NOT RETURNED ({hit}/{len(can)}) — injection is not "
                      f"reaching the model. Every number below is noise; fix before reading.")
            elif leak:
                print(f"\n!! {exp}: CANARY LEAKED INTO CONTROL ({leak}/{len(ctl)}) — arms are "
                      f"not isolated.")
            else:
                print(f"\n   {exp}: injection verified (canary {hit}/{len(can)}, control clean)")

    for exp in sorted(tally):
        al = aligned[exp]
        # canary is a wiring check, not a behavioural arm - keep it out of the tally
        arms = [a for a in tally[exp] if a != "canary"]
        base = "off" if "off" in arms else arms[0]
        print(f"\n== {exp}  (aligned verdict: {al})")
        for arm in arms:
            v = tally[exp][arm]
            h, n = hits_of(v, al)
            print(f"   {arm:<9}{h}/{n}  unscored {len(v) - n}   {sorted(v)}")
        # Measured noise floor: two labels, one condition. Any effect smaller
        # than this gap is indistinguishable from run-to-run variance.
        if "off" in arms and "off_b" in arms:
            ha, na = hits_of(tally[exp]["off"], al)
            hb, nb = hits_of(tally[exp]["off_b"], al)
            print(f"   noise floor (off vs off_b): {ha}/{na} vs {hb}/{nb}  "
                  f"p={fisher(ha, na - ha, hb, nb - hb):.3f}")

        # Full pairwise, not just each-arm-vs-off. Trim validation needs
        # candidate-vs-original ("did my edit break it?"), which a comparison
        # against the control alone cannot answer.
        def hits(arm):
            return hits_of(tally[exp][arm], al)

        for i, x in enumerate(arms):
            for y in arms[i + 1:]:
                hx, nx = hits(x)
                hy, ny = hits(y)
                p = fisher(hx, nx - hx, hy, ny - hy)
                note = ("  <- NO SCORED REPLIES on one side" if not (nx and ny) else
                        "  <- CEILING: no headroom, proves nothing" if hx == nx and hy == ny else "")
                print(f"   p({x} vs {y}) = {p:.3f}{note}")

        # Trim verdict. The question a trim actually asks is "did I make it WORSE",
        # so the reference arm is the original, not the control.
        #
        # An earlier version required `trimmed` to beat `off` significantly and
        # called anything else "effect LOST". That conflates "the trim broke it"
        # with "this prompt had no headroom / too few reps" — and it fired on a
        # trim whose candidate scored BETTER than the original. A gate whose
        # failure mode is indistinguishable from its pass mode is not a gate.
        if base in arms and len(arms) >= 3:
            cand = [a for a in arms if a not in (base, "orig", "on", "placebo")]
            ref = "orig" if "orig" in arms else ("on" if "on" in arms else None)
            if cand and ref:
                hc, nc = hits(cand[0])
                hb2, nb2 = hits(base)
                hr, nr = hits(ref)
                if not (nc and nb2 and nr):
                    print(f"   TRIM VERDICT: UNVALIDATED — an arm has no scored replies "
                          f"({cand[0]} {nc}, {base} {nb2}, {ref} {nr}); read the unscored column")
                    continue
                rate_c, rate_r = hc / nc, hr / nr
                degraded = fisher(hc, nc - hc, hr, nr - hr) < 0.05 and rate_c < rate_r
                no_headroom = hb2 == nb2                  # control already perfect
                ref_shows_effect = fisher(hr, nr - hr, hb2, nb2 - hb2) < 0.05

                if degraded:
                    v = "DO NOT SHIP — candidate is significantly worse than the original"
                elif no_headroom:
                    v = ("UNVALIDATED — control scored full marks, so this prompt cannot detect "
                         "any effect. Not evidence the trim is safe; build a harder prompt or "
                         "decide on other grounds")
                elif not ref_shows_effect:
                    v = (f"UNVALIDATED — the ORIGINAL does not measurably beat {base} here either, "
                         f"so this prompt cannot referee the trim. No evidence of harm: "
                         f"{cand[0]} {hc}/{nc} vs orig {hr}/{nr}")
                else:
                    v = (f"SHIP — effect preserved ({cand[0]} {hc}/{nc} vs orig {hr}/{nr}, "
                         f"no significant degradation)")
                print(f"   TRIM VERDICT: {v}")


def selftest():
    """Recorded/fake `claude -p --output-format json` envelopes through the scoring path. No calls."""
    labels = ["COLD-AWARE", "ANCHORED"]
    cases = [  # (envelope, expected)
        ({"result": "", "structured_output": {"verdict": "COLD-AWARE"}}, "COLD-AWARE"),
        ({"result": "", "structured_output": {"verdict": "ANCHORED"}}, "ANCHORED"),
        # the old free-text path would have scored these; none is a schema-valid verdict
        ({"result": "COLD-AWARE"}, UNSCORED),                                     # prose, no structured_output
        ({"structured_output": {"verdict": "cold-aware"}}, UNSCORED),             # case drift, off-enum
        ({"structured_output": {"verdict": "COLD"}}, UNSCORED),                   # truncated label
        ({"structured_output": {"label": "COLD-AWARE"}}, UNSCORED),               # wrong field
        ({"structured_output": "COLD-AWARE"}, UNSCORED),                          # not an object
        ({"subtype": "error_max_structured_output_retries", "is_error": True}, UNSCORED),
        ("not json at all", UNSCORED),
    ]
    fails = 0
    for env, want in cases:
        got = verdict_of(env, labels)
        fails += got != want
        print(f"  [{'ok' if got == want else 'FAIL'}] want={want:<10} got={got:<10} {str(env)[:70]}")
    # tally: unscored is excluded from both numerator and denominator
    h, n = hits_of(["COLD-AWARE", "ANCHORED", UNSCORED, UNSCORED], "COLD-AWARE")
    ok = (h, n) == (1, 2)
    fails += not ok
    print(f"  [{'ok' if ok else 'FAIL'}] hits_of with 2 unscored -> {h}/{n} (want 1/2)")
    # config without declared labels is refused
    try:
        experiment_labels({"experiments": [{"id": "x", "rubric": "Answer FOO if ..."}]})
        print("  [FAIL] config without labels/aligned was accepted")
        fails += 1
    except SystemExit:
        print("  [ok] config without labels/aligned refused")
    print(f"selftest: {'PASS' if not fails else f'{fails} FAILED'}")
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("verb", choices=["run", "score", "selftest"])
    ap.add_argument("config", nargs="?")
    ap.add_argument("--reps", type=int, default=7)
    ap.add_argument("--model", default="opus")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--max-usd", type=float, default=0.40)
    a = ap.parse_args()
    if a.verb == "selftest":
        raise SystemExit(selftest())
    if not a.config:
        ap.error("config is required for run/score")
    cfg = json.loads(pathlib.Path(a.config).read_text())
    if a.verb == "run":
        cmd_run(cfg, a.reps, a.model, a.workers, a.max_usd)
    else:
        cmd_score(cfg)


if __name__ == "__main__":
    main()
