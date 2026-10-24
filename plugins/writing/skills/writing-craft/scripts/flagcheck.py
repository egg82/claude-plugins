#!/usr/bin/env python3
"""Measure whether a model can tell human-written short lines from model-written ones.

Input JSONL: {"id", "text", "label"} with label human | model | unknown.
Lines are shuffled (seeded), cut into batches of ~20, and sent to a grader with no labels.
Each batch is graded twice, in forward and reversed order, to expose position effects.
Report: per-grader TPR (model lines called machine), FPR (human lines called machine),
confusion counts, per-line verdicts with the quoted phrase, and the most-quoted phrases.
Keys are read in-process from systemd-creds; they are never printed or placed in argv.
The pangram and sapling graders are paid detectors that score one text per request, forward order only;
they print a cost estimate and need --yes. See README.txt beside this file.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
LABELS = ("human", "model", "unknown")

PROMPT = (
    "Below are numbered short pieces of text. Some were written by "
    "people and some by an AI language model. For EVERY line decide whether it reads as "
    "written by a human or by a machine. Give: n (the line's number), verdict "
    "(\"human\" or \"machine\"), confidence (0 to 1, your confidence in that verdict), and "
    "phrase (the exact words copied from the line that give it away, or \"none\"). "
    "Judge only from the text. Return one entry for every line.\n\nLines:\n"
)

Item = tuple[int, str]  # (batch-local number, text)


@dataclass
class Verdict:
    verdict: Optional[str]  # "human" | "machine" | None (grader gave no usable answer)
    confidence: Optional[float]
    phrase: str


Grader = Callable[[list[Item]], dict[int, Verdict]]


# ----------------------------------------------------------------------------- keys

def load_instance() -> dict:
    return json.loads((HERE / "instance.json").read_text())


def get_key(provider: str) -> str:
    cfg = load_instance()[provider]
    cred = str(Path(cfg["cred"]).expanduser())
    r = subprocess.run(
        ["sudo", "-n", "systemd-creds", "decrypt", "--name=api-key", cred, "-"],
        capture_output=True,
    )
    if r.returncode != 0:
        # stderr deliberately not echoed
        raise SystemExit(f"{provider}: could not decrypt credential (exit {r.returncode}); path configured in instance.json")
    key = r.stdout.decode().strip()
    if not key:
        raise SystemExit(f"{provider}: credential decrypted to empty")
    return key


# ----------------------------------------------------------------------------- http

def post_json(url: str, headers: dict[str, str], body: dict, tries: int = 4) -> dict:
    data = json.dumps(body).encode()
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", **headers})
        try:
            with urllib.request.urlopen(req, timeout=540) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"HTTP {e.code} from {url.split('?')[0]}: {e.read()[:300].decode(errors='replace')}")
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise SystemExit(f"network error from {url.split('?')[0]}: {type(e).__name__}")
    raise SystemExit("unreachable")


def http_json(method: str, url: str, headers: dict[str, str], body: Optional[dict] = None, tries: int = 3) -> dict:
    """One JSON request; raises RuntimeError (never SystemExit) so a paid run can keep its earlier results."""
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {"Content-Type": "application/json", **headers}
    where = url.split("?")[0]
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"HTTP {e.code} from {where}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            if attempt < tries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"{type(e).__name__} from {where}")
    raise RuntimeError("unreachable")


def numbered(items: list[Item]) -> str:
    return "\n".join(f"{n}. {t}" for n, t in items)


def parse_results(text: str) -> dict[int, Verdict]:
    try:
        arr = json.loads(text)["results"]
    except (json.JSONDecodeError, KeyError, TypeError):
        return {}
    out: dict[int, Verdict] = {}
    for e in arr:
        try:
            n = int(e["n"])
            v = str(e["verdict"]).strip().lower()
            if v not in ("human", "machine"):
                continue
            c = e.get("confidence")
            out[n] = Verdict(v, float(c) if c is not None else None, str(e.get("phrase", "none")))
        except (KeyError, TypeError, ValueError):
            continue
    return out


# ----------------------------------------------------------------------------- graders

def make_gemini(model: str) -> Grader:
    key = get_key("gemini")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    schema = {
        "type": "OBJECT",
        "properties": {"results": {"type": "ARRAY", "items": {
            "type": "OBJECT",
            "properties": {
                "n": {"type": "INTEGER"},
                "verdict": {"type": "STRING", "enum": ["human", "machine"]},
                "confidence": {"type": "NUMBER"},
                "phrase": {"type": "STRING"},
            },
            "required": ["n", "verdict", "confidence", "phrase"],
        }}},
        "required": ["results"],
    }

    def grade(items: list[Item]) -> dict[int, Verdict]:
        body = {
            "contents": [{"parts": [{"text": PROMPT + numbered(items)}]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json", "responseSchema": schema},
        }
        resp = post_json(url, {"x-goog-api-key": key}, body)
        try:
            parts = resp["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts)
        except (KeyError, IndexError):
            return {}
        return parse_results(text)

    return grade


def make_openai(model: str) -> Grader:
    key = get_key("openai")
    url = "https://api.openai.com/v1/chat/completions"
    schema = {
        "name": "verdicts",
        "strict": True,
        "schema": {
            "type": "object",
            "additionalProperties": False,
            "properties": {"results": {"type": "array", "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "n": {"type": "integer"},
                    "verdict": {"type": "string", "enum": ["human", "machine"]},
                    "confidence": {"type": "number"},
                    "phrase": {"type": "string"},
                },
                "required": ["n", "verdict", "confidence", "phrase"],
            }}},
            "required": ["results"],
        },
    }

    def grade(items: list[Item]) -> dict[int, Verdict]:
        body = {
            "model": model,
            "messages": [{"role": "user", "content": PROMPT + numbered(items)}],
            "response_format": {"type": "json_schema", "json_schema": schema},
        }
        resp = post_json(url, {"Authorization": f"Bearer {key}"}, body)
        try:
            text = resp["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            return {}
        return parse_results(text)

    return grade


# Paid detectors: one text per request, forward order only. Value = dollars per word, None where not set here.
SINGLE_PRICE: dict[str, Optional[float]] = {"pangram": 0.0005, "sapling": None}
PANGRAM_URL = "https://text.external-api.pangram.com/task"
SAPLING_URL = "https://api.sapling.ai/api/v1/aidetect"
Http = Callable[..., dict]


def find_field(resp: dict, name: str) -> object:
    """A field at the top of the response or one dict level down."""
    if name in resp:
        return resp[name]
    for v in resp.values():
        if isinstance(v, dict) and name in v:
            return v[name]
    return None


def parse_pangram(resp: dict) -> Verdict:
    pred = find_field(resp, "prediction_short")
    if pred is None:
        return Verdict(None, None, "response had no prediction_short")
    frac = find_field(resp, "fraction_ai")
    machine = str(pred).strip().lower() in ("ai", "mixed")
    return Verdict("machine" if machine else "human", float(frac) if isinstance(frac, (int, float)) else None, "none")


def parse_sapling(resp: dict) -> Verdict:
    score = resp.get("score")
    if not isinstance(score, (int, float)):
        return Verdict(None, None, "response had no score")
    return Verdict("machine" if score >= 0.5 else "human", float(score), "none")


def make_pangram(key: str, http: Http = http_json, sleep: Callable[[float], None] = time.sleep,
                 interval: float = 2.0, give_up: float = 60.0) -> Grader:
    headers = {"x-api-key": key}

    def grade(items: list[Item]) -> dict[int, Verdict]:
        (n, text), = items
        try:
            task_id = http("POST", PANGRAM_URL, headers, {"text": text}).get("task_id")
            if not task_id:
                raise RuntimeError("submit response had no task_id")
            waited = 0.0
            while True:
                resp = http("GET", f"{PANGRAM_URL}/{task_id}", headers)
                stage = find_field(resp, "stage")
                if stage == "STAGE_SUCCESS":
                    return {n: parse_pangram(resp)}
                if stage == "STAGE_FAILED":
                    raise RuntimeError("task ended STAGE_FAILED")
                if waited >= give_up:
                    raise RuntimeError(f"no STAGE_SUCCESS after {give_up:.0f}s (last stage {stage!r})")
                sleep(interval)
                waited += interval
        except RuntimeError as e:
            print(f"  pangram: line {n}: {e}", file=sys.stderr)
            return {n: Verdict(None, None, f"error: {e}")}

    return grade


def make_sapling(key: str, http: Http = http_json) -> Grader:
    def grade(items: list[Item]) -> dict[int, Verdict]:
        (n, text), = items
        try:
            return {n: parse_sapling(http("POST", SAPLING_URL, {}, {"key": key, "text": text}))}
        except RuntimeError as e:
            print(f"  sapling: line {n}: {e}", file=sys.stderr)
            return {n: Verdict(None, None, f"error: {e}")}

    return grade


def dry_http(provider: str) -> Http:
    """Stand-in transport with the real request shapes, for --dry-run: checks headers/body and the poll loop."""
    texts: dict[str, str] = {}
    polls: dict[str, int] = {}

    def machine(text: str) -> bool:
        return fake_grader([(1, text)])[1].verdict == "machine"

    def http(method: str, url: str, headers: dict[str, str], body: Optional[dict] = None, tries: int = 3) -> dict:
        if provider == "pangram":
            assert headers.get("x-api-key"), "pangram request without x-api-key"
            if method == "POST":
                assert url == PANGRAM_URL and body and body.get("text"), "bad pangram submit"
                tid = str(len(texts))
                texts[tid], polls[tid] = body["text"], 0
                return {"task_id": tid}
            assert method == "GET" and url.startswith(PANGRAM_URL + "/"), "bad pangram poll"
            tid = url.rsplit("/", 1)[1]
            polls[tid] += 1
            if polls[tid] < 2:
                return {"stage": "STAGE_PROCESSING"}
            ai = machine(texts[tid])
            return {"stage": "STAGE_SUCCESS", "prediction_short": "AI" if ai else "Human", "fraction_ai": 0.9 if ai else 0.05}
        assert method == "POST" and url == SAPLING_URL and body and body.get("key") and body.get("text"), "bad sapling request"
        assert not headers.get("x-api-key"), "sapling takes its key in the body"
        return {"score": 0.9 if machine(body["text"]) else 0.1, "sentence_scores": []}

    return http


def fake_grader(items: list[Item]) -> dict[int, Verdict]:
    """Deterministic: machine if the line has an em dash or 'not just'."""
    out: dict[int, Verdict] = {}
    for n, t in items:
        if "—" in t:
            out[n] = Verdict("machine", 0.9, "—")
        elif "not just" in t.lower():
            out[n] = Verdict("machine", 0.9, "not just")
        else:
            out[n] = Verdict("human", 0.6, "none")
    return out


def build_grader(name: str, model: str, dry: bool = False) -> Grader:
    if name == "fake" or (dry and name in ("gemini", "openai")):
        return fake_grader
    if name == "pangram":
        return make_pangram("dry-key", dry_http(name), lambda s: None) if dry else make_pangram(get_key(name))
    if name == "sapling":
        return make_sapling("dry-key", dry_http(name)) if dry else make_sapling(get_key(name))
    if name == "gemini":
        return make_gemini(model)
    if name == "openai":
        return make_openai(model)
    raise SystemExit(f"unknown grader {name}")


# ----------------------------------------------------------------------------- pipeline

def load_lines(path: Path) -> list[dict]:
    rows = []
    for ln in path.read_text().splitlines():
        if not ln.strip():
            continue
        r = json.loads(ln)
        if r.get("label") not in LABELS:
            raise SystemExit(f"bad label on {r.get('id')}: {r.get('label')!r}")
        rows.append(r)
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise SystemExit("duplicate ids in input")
    return rows


def make_batches(rows: list[dict], seed: int, size: int) -> list[list[dict]]:
    rows = rows[:]
    random.Random(seed).shuffle(rows)
    nb = max(1, math.ceil(len(rows) / size))
    base, extra = divmod(len(rows), nb)
    out, i = [], 0
    for b in range(nb):
        k = base + (1 if b < extra else 0)
        out.append(rows[i:i + k])
        i += k
    return out


def flatten_surface(t: str) -> str:
    """Drop capital first letter and final period, so casing and punctuation cannot give a line away."""
    t = t[:1].lower() + t[1:]
    return t[:-1] if t.endswith(".") and not t.endswith("...") else t


def grade_batch(grader: Grader, batch: list[dict], reverse: bool, flat: bool = False) -> dict[str, Verdict]:
    order = batch[::-1] if reverse else batch
    items: list[Item] = [(i + 1, flatten_surface(r["text"]) if flat else r["text"]) for i, r in enumerate(order)]
    got = grader(items)
    return {r["id"]: got.get(i + 1, Verdict(None, None, "")) for i, r in enumerate(order)}


def run_grader(name: str, grader: Grader, batches: list[list[dict]], flat: bool = False,
               both_orders: bool = True) -> list[dict]:
    recs: dict[str, dict] = {}
    for bi, batch in enumerate(batches):
        for rev in ((False, True) if both_orders else (False,)):
            res = grade_batch(grader, batch, rev, flat)
            key = "rev" if rev else "fwd"
            for r in batch:
                rec = recs.setdefault(r["id"], {"grader": name, "id": r["id"], "label": r["label"],
                                                "text": r["text"], "batch": bi,
                                                "register": r.get("register")})
                v = res[r["id"]]
                rec[key] = {"verdict": v.verdict, "confidence": v.confidence, "phrase": v.phrase,
                            "phrase_in_text": bool(v.phrase) and v.phrase.lower() != "none"
                            and v.phrase.lower() in r["text"].lower()}
        if (bi + 1) % 10 == 0 or bi + 1 == len(batches):
            print(f"  {name}: batch {bi + 1}/{len(batches)} done", file=sys.stderr)
    return list(recs.values())


# ----------------------------------------------------------------------------- metrics

def rate(num: int, den: int) -> str:
    return f"{num / den:.2f} ({num}/{den})" if den else "n/a (0 lines)"


def confusion(recs: list[dict], orders: tuple[str, ...]) -> dict[str, int]:
    c = {"tp": 0, "fn": 0, "fp": 0, "tn": 0, "no_answer": 0}
    for r in recs:
        for o in orders:
            v = r[o]["verdict"]
            if r["label"] == "unknown":
                continue
            if v is None:
                c["no_answer"] += 1
            elif r["label"] == "model":
                c["tp" if v == "machine" else "fn"] += 1
            else:
                c["fp" if v == "machine" else "tn"] += 1
    return c


def summarize(name: str, model: str, recs: list[dict]) -> str:
    L = [f"=== grader: {name} ({model}) ===", ""]
    both_orders = all("rev" in r for r in recs)
    ords: tuple[str, ...] = ("fwd", "rev") if both_orders else ("fwd",)
    sections = ((("forward order", ("fwd",)), ("reversed order", ("rev",)), ("both orders pooled", ("fwd", "rev")))
                if both_orders else (("forward order only (one text per request)", ("fwd",)),))
    for title, orders in sections:
        c = confusion(recs, orders)
        tpr = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else None
        fpr = c["fp"] / (c["fp"] + c["tn"]) if c["fp"] + c["tn"] else None
        gap = f"{tpr - fpr:+.2f}" if tpr is not None and fpr is not None else "n/a"
        L.append(f"{title}:")
        L.append(f"  TPR (model lines called machine): {rate(c['tp'], c['tp'] + c['fn'])}")
        L.append(f"  FPR (human lines called machine): {rate(c['fp'], c['fp'] + c['tn'])}")
        L.append(f"  TPR - FPR: {gap}")
        L.append(f"  confusion: tp={c['tp']} fn={c['fn']} fp={c['fp']} tn={c['tn']} no_answer={c['no_answer']}")
    if both_orders:
        both = [r for r in recs if r["fwd"]["verdict"] and r["rev"]["verdict"]]
        agree = sum(r["fwd"]["verdict"] == r["rev"]["verdict"] for r in both)
        L.append(f"order agreement: {rate(agree, len(both))} of lines answered in both orders")
    regs = sorted({r["register"] for r in recs if r.get("register")})
    if regs:
        L.append("")
        L.append("per register (" + ("both orders pooled" if both_orders else "forward order") + "):")
        for g in regs:
            c = confusion([r for r in recs if r.get("register") == g], ords)
            tpr = c["tp"] / (c["tp"] + c["fn"]) if c["tp"] + c["fn"] else None
            fpr = c["fp"] / (c["fp"] + c["tn"]) if c["fp"] + c["tn"] else None
            gap = f"{tpr - fpr:+.2f}" if tpr is not None and fpr is not None else "n/a"
            L.append(f"  {g:<8} TPR {rate(c['tp'], c['tp'] + c['fn'])}  FPR {rate(c['fp'], c['fp'] + c['tn'])}  TPR-FPR {gap}")
    L.append("")
    L.append("per line (" + ("fwd / rev verdict" if both_orders else "verdict") + ", confidence, quoted phrase):")
    for r in sorted(recs, key=lambda r: (r["label"], r["id"])):
        xs = [r[o] for o in ords]
        ph = next((x["phrase"] for x in xs if x["verdict"] == "machine"), "")
        ph = ph if ph and ph.lower() != "none" else "-"
        conf = "/".join("?" if x["confidence"] is None else f"{x['confidence']:.2f}" for x in xs)
        verd = "/".join(f"{x['verdict'] or 'NONE':<7}" for x in xs)
        L.append(f"  [{r['label']:<7}] {r['id']:<12} {verd} {conf:<9} {ph!r}  | {r['text'][:60]!r}")
    phr: Counter[str] = Counter()
    by_label: dict[str, Counter[str]] = {"human": Counter(), "model": Counter(), "unknown": Counter()}
    unverbatim = 0
    for r in recs:
        for o in ords:
            x = r[o]
            if x["verdict"] == "machine" and x["phrase"] and x["phrase"].lower() != "none":
                p = x["phrase"].strip().lower()
                phr[p] += 1
                by_label[r["label"]][p] += 1
                if not x["phrase_in_text"]:
                    unverbatim += 1
    L.append("")
    L.append("most-quoted giveaway phrases (count over both orders; counts on human / model lines):")
    if not phr:
        L.append("  (none quoted)")
    for p, n in phr.most_common(15):
        L.append(f"  {n:>3}  {p!r}  human={by_label['human'][p]} model={by_label['model'][p]}")
    L.append(f"quoted phrases not found verbatim in their line: {unverbatim}")
    L.append("")
    return "\n".join(L)


# ----------------------------------------------------------------------------- main

def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", type=Path, help="JSONL of {id,text,label}")
    ap.add_argument("--grader", action="append", choices=["gemini", "openai", "pangram", "sapling"], default=[],
                    help="repeatable; with --dry-run gemini/openai use the fake grader and pangram/sapling a stand-in transport")
    ap.add_argument("--yes", action="store_true",
                    help="confirm the cost estimate; required before pangram or sapling make live requests")
    ap.add_argument("--gemini-model", default="gemini-pro-latest")
    ap.add_argument("--openai-model", default="gpt-5")
    ap.add_argument("--dry-run", action="store_true", help="use the fake grader; no credential, no network")
    ap.add_argument("--flatten", action="store_true",
                    help="send lines with first letter lowercased and final period dropped (removes casing/punctuation cues)")
    ap.add_argument("--register", help="only grade lines whose register field equals this")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=20)
    ap.add_argument("--out", type=Path, default=Path("flagcheck-out"),
                    help="output prefix; writes <out>.jsonl and <out>.txt")
    a = ap.parse_args(argv)

    rows = load_lines(a.input)
    if a.register:
        rows = [r for r in rows if r.get("register") == a.register]
        if not rows:
            raise SystemExit(f"no lines with register {a.register!r}")
    batches = make_batches(rows, a.seed, a.batch_size)
    models = {"gemini": a.gemini_model, "openai": a.openai_model, "pangram": "pangram api", "sapling": "sapling api"}
    if a.dry_run and not a.grader:
        plan: list[tuple[str, str]] = [("fake", "deterministic em-dash / 'not just' rule")]
    elif a.grader:
        plan = [(g, models[g]) for g in a.grader]
    else:
        raise SystemExit("give --grader or --dry-run")

    words = sum(len(r["text"].split()) for r in rows)
    units = sum(-(-len(r["text"].split()) // 100) for r in rows)  # billed per request in whole 100-word units
    paid = [g for g, _ in plan if g in SINGLE_PRICE]
    for g in paid:
        price = SINGLE_PRICE[g]
        est = f"about ${units * 100 * price:.2f} ({units} units of 100 words, rounded up per request)" if price is not None else \
            f"{words} words; no per-word price is set in this script, check the plan before running"
        print(f"cost estimate, {g}: {len(rows)} requests, {est}" + ("  [dry run: no requests sent]" if a.dry_run else ""),
              file=sys.stderr)
    if paid and not a.dry_run and not a.yes:
        raise SystemExit("paid grader(s) " + ", ".join(paid) + ": re-run with --yes to accept the estimate above")

    all_recs: list[dict] = []
    text_parts = [f"input: {a.input.name}  lines: {len(rows)}  batches: {len(batches)}  seed: {a.seed}  flatten: {a.flatten}",
                  "labels: " + ", ".join(f"{l}={sum(r['label'] == l for r in rows)}" for l in LABELS), ""]
    singles = [[r] for b in batches for r in b]
    for name, model in plan:
        one = name in SINGLE_PRICE
        grader = build_grader(name, model, a.dry_run)
        recs = run_grader(name, grader, singles if one else batches, a.flatten, both_orders=not one)
        for r in recs:
            r["model"] = model
        all_recs.extend(recs)
        text_parts.append(summarize(name, model, recs))

    jsonl = a.out.with_suffix(".jsonl")
    txt = a.out.with_suffix(".txt")
    jsonl.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in all_recs))
    txt.write_text("\n".join(text_parts))
    print("\n".join(text_parts))
    print(f"wrote {jsonl} and {txt}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
