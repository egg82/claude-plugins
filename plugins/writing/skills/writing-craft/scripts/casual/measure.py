#!/usr/bin/env python3
"""Casual-register measurements: HN human replies vs Claude replies.

usage: python3 -I measure.py [--sample] > results_body.txt
Stdlib only. The data files are not shipped: regenerate human.jsonl with fetch_hn.py and claude.jsonl with
build_claude.py (you write the replies it joins). Reads human.jsonl, claude.jsonl, optional typo_handcheck.json.
--sample prints flagged tokens with context.
"""
import json
import math
import os
import random
import re
import sys
from collections import Counter
from typing import Callable, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
DICT = "/usr/share/dict/words"
SEED = 7
NBOOT = 1000
WINDOW = 25

Rec = Dict[str, Optional[float]]

# Measured LLM-overused words from references/llm-tells.md (Reinhart, Antislop, slop-forensics, Kobak).
LLM_WORDS = set("""camaraderie tapestry intricate underscore underscores underscored underscoring amidst palpable
solace unease delve delves delving showcase showcases showcasing crucial pivotal testament vibrant whispered
lingered faintly acrid bustling cacophony flickered unsettlingly shimmered stammered dependable boasts""".split())
LLM_PHRASES = ["serves as", "stands as", "this matters", "rather than simply", "adds another layer"]

# Small embedded common-word list (function words + very frequent words), unioned with parent-comment frequency.
COMMON = set("""the be to of and a in that have i it for not on with he as you do at this but his by from they we say her she
or an will my one all would there their what so up out if about who get which go me when make can like time no just him
know take people into year your good some could them see other than then now look only come its over think also back after
use two how our work first well way even new want because any these give day most us is are was were been has had did
does done am being very more much many such too really thing things something anything everything need needs should may
might must where why while still own same those through before between each both off down never always here let put
right going made said say says used using find found tell told ask asked seem seems feel feels try tried call called
keep kept start started show shown help old big small long little great high different large end few part place case
point fact sure yes yeah okay ok maybe actually probably already enough though however another again away against
without within during under until since often every almost ever less least whether either quite rather lot lots bit
person man woman child children world life hand home house money company business problem question answer idea
reason example number system data web site page code software language program computer internet game video
dont cant im ive id ill youre theyre thats whats isnt wasnt arent doesnt didnt wont couldnt shouldnt wouldnt hasnt
havent lets""".split())

CONTRACTION_RE = re.compile(r"\b[A-Za-z]+(?:n['’]t|['’](?:re|ve|ll|d|m))\b|\b(?:it|that|he|she|there|what|who|let|here|where)['’]s\b", re.I)
DROP_RE = re.compile(r"\b(?:dont|cant|im|wont|isnt|doesnt|didnt|youre|thats|ive|wasnt|arent|couldnt|shouldnt|wouldnt|hasnt|havent|theyre|whats|lets)\b", re.I)
URL_RE = re.compile(r"https?://\S+|www\.\S+")
TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'’]*")


def load(path: str) -> List[Dict[str, str]]:
    return [json.loads(line) for line in open(path)]


def clean(text: str) -> str:
    """Drop quoted-parent lines (start with >) and URLs; keep everything else exactly."""
    lines = [ln for ln in text.split("\n") if not ln.lstrip().startswith(">")]
    return URL_RE.sub(" ", "\n".join(lines)).strip()


def split_sentences(text: str) -> List[str]:
    out: List[str] = []
    for ln in text.split("\n"):
        ln = re.sub(r"^\s*[*\-•\d.)]+\s+", "", ln).strip()
        if not ln:
            continue
        out.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", ln) if s.strip())
    return out


def first_alpha(s: str) -> str:
    m = re.search(r"[A-Za-z]", s)
    return m.group(0) if m else ""


def starts_lower(s: str) -> Optional[bool]:
    """True/False for a clear lower/upper start; None when not a prose start (digit, code, mixed-case name)."""
    s2 = s.lstrip("\"'“‘([ ")
    if not s2 or not s2[0].isalpha():
        return None
    first = re.match(r"[A-Za-z][A-Za-z'’]*", s2)
    if not first or any(c.isupper() for c in first.group(0)[1:]):
        return None
    return s2[0].islower()


def terminal(s: str) -> bool:
    return bool(re.search(r"[.!?][\"'”’)\]]*$", s.rstrip()))


def mattr(tokens: List[str]) -> Optional[float]:
    if len(tokens) < WINDOW:
        return None
    vals = [len(set(tokens[i:i + WINDOW])) / WINDOW for i in range(len(tokens) - WINDOW + 1)]
    return sum(vals) / len(vals)


def sd(xs: List[float]) -> Optional[float]:
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def base(tok: str) -> str:
    t = tok.lower().replace("’", "'")
    return re.sub(r"'(s|re|ve|ll|d|m|t)$", "", t)


def record(raw: str, common: set, dic: set) -> Rec:
    text = clean(raw)
    toks = TOKEN_RE.findall(text)
    low = [t.lower().replace("’", "'") for t in toks]
    n = len(toks)
    sents = split_sentences(text)
    starts = [starts_lower(s) for s in sents]
    starts = [x for x in starts if x is not None]
    lens = [float(len(s.split())) for s in sents]
    low_text = text.lower()
    acro = 0
    for t in set(toks):
        if t.isupper() and 2 <= len(t) <= 6 and re.search(r"\b%s\b" % re.escape(t.lower()), text):
            acro = 1
    typo = checked = 0
    for t in toks:
        if "'" in t or "’" in t or len(t) < 3 or t.isupper():
            continue
        checked += 1
        if t.lower() not in dic:
            typo += 1
    drift: Optional[float] = None
    if len(sents) >= 3:
        def formal(s: str) -> int:
            return int(first_alpha(s).isupper()) + int(terminal(s))
        drift = float(formal(sents[0]) - formal(sents[-1]))
    r: Rec = {
        "words": float(n),
        "mattr": mattr(low),
        "rare": float(sum(1 for t in low if base(t) not in common)),
        "llm": float(sum(1 for t in low if t in LLM_WORDS) + sum(low_text.count(p) for p in LLM_PHRASES)),
        "sent": float(len(starts)),
        "sent_lower": float(sum(starts)),
        "any_lower": float(any(starts)) if starts else None,
        "i_lower": float(bool(re.search(r"(?<![A-Za-z.'])i(?![A-Za-z.'’])", text))),
        "acro_both": float(acro),
        "no_term": float(not terminal(text)) if text else None,
        "emdash": float(text.count("—")),
        "semi": float(text.count(";")),
        "colon": float(len(re.findall(r":(?!//)", text))),
        "drops": float(len(DROP_RE.findall(text))),
        "contr": float(len(CONTRACTION_RE.findall(text))),
        "drift": drift,
        "drift_pos": None if drift is None else float(drift > 0),
        "sdlen": sd(lens),
        "typo": float(typo),
        "checked": float(checked),
    }
    return r


Metric = Tuple[str, Callable[[List[Rec]], Optional[float]], str]


def per100(key: str) -> Callable[[List[Rec]], Optional[float]]:
    def f(rs: List[Rec]) -> Optional[float]:
        w = sum(r["words"] or 0 for r in rs)
        return 100 * sum(r[key] or 0 for r in rs) / w if w else None
    return f


def mean_of(key: str) -> Callable[[List[Rec]], Optional[float]]:
    def f(rs: List[Rec]) -> Optional[float]:
        v = [r[key] for r in rs if r[key] is not None]
        return sum(v) / len(v) if v else None  # type: ignore[arg-type]
    return f


def share_sent_lower(rs: List[Rec]) -> Optional[float]:
    s = sum(r["sent"] or 0 for r in rs)
    return 100 * sum(r["sent_lower"] or 0 for r in rs) / s if s else None


def rare_share(rs: List[Rec]) -> Optional[float]:
    w = sum(r["words"] or 0 for r in rs)
    return 100 * sum(r["rare"] or 0 for r in rs) / w if w else None


def typo_rate(rs: List[Rec]) -> Optional[float]:
    return per100("typo")(rs)


METRICS: List[Metric] = [
    ("MATTR-25 (msgs with >=25 words)", mean_of("mattr"), "mean"),
    ("words outside common set, % of words", rare_share, "%"),
    ("LLM-list words per 100 words", per100("llm"), "/100w"),
    ("sentences starting lowercase, %", share_sent_lower, "%"),
    ("msgs with any lowercase sentence start, %", lambda rs: None if not rs else 100 * (mean_of("any_lower")(rs) or 0), "%"),
    ("msgs with lowercase 'i', %", lambda rs: 100 * (mean_of("i_lower")(rs) or 0), "%"),
    ("msgs with acronym in both cases, %", lambda rs: 100 * (mean_of("acro_both")(rs) or 0), "%"),
    ("msgs ending without . ! ?, %", lambda rs: 100 * (mean_of("no_term")(rs) or 0), "%"),
    ("em dashes per 100 words", per100("emdash"), "/100w"),
    ("semicolons per 100 words", per100("semi"), "/100w"),
    ("colons per 100 words", per100("colon"), "/100w"),
    ("apostrophe drops per 100 words", per100("drops"), "/100w"),
    ("contractions per 100 words", per100("contr"), "/100w"),
    ("drift: first minus last sentence formality (0-2), msgs with 3+ sentences", mean_of("drift"), "mean"),
    ("drift: msgs where first more formal than last, %", lambda rs: 100 * (mean_of("drift_pos")(rs) or 0), "%"),
    ("non-dictionary words per 100 words (not hand-corrected)", typo_rate, "/100w"),
    ("sentence-length SD within msg (msgs with 2+ sentences)", mean_of("sdlen"), "mean"),
]


def boot_ci(fn: Callable[[List[Rec]], Optional[float]], a: List[Rec], b: List[Rec], paired: bool,
            rng: random.Random) -> Tuple[Optional[float], Optional[float]]:
    diffs: List[float] = []
    for _ in range(NBOOT):
        ia = [rng.randrange(len(a)) for _ in a]
        ib = ia if paired else [rng.randrange(len(b)) for _ in b]
        va, vb = fn([a[i] for i in ia]), fn([b[i] for i in ib])
        if va is not None and vb is not None:
            diffs.append(va - vb)
    if len(diffs) < NBOOT * 0.9:
        return None, None
    diffs.sort()
    return diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]


def fmt(x: Optional[float]) -> str:
    return "n/a" if x is None else "%.2f" % x


def verdict(lo: Optional[float], hi: Optional[float]) -> str:
    if lo is None or hi is None:
        return "n/a"
    return "CLEAR" if lo > 0 or hi < 0 else "not clear"


def sample_tokens(recs: List[Dict[str, str]], dic: set, k: int, rng: random.Random, context: bool) -> List[str]:
    found: List[str] = []
    for r in recs:
        text = clean(r["text"])
        ws = text.split()
        for i, w in enumerate(ws):
            t = re.sub(r"^[^A-Za-z]+|[^A-Za-z'’]+$", "", w)
            if len(t) >= 3 and "'" not in t and "’" not in t and not t.isupper() and t.isalpha() and t.lower() not in dic:
                found.append(t if not context else "%s   [...%s...]" % (t, " ".join(ws[max(0, i - 3):i + 4])))
    rng.shuffle(found)
    return found[:k]


def main() -> None:
    sample = "--sample" in sys.argv
    human = load(os.path.join(HERE, "human.jsonl"))
    claude = load(os.path.join(HERE, "claude.jsonl"))
    dic = {w.strip().lower() for w in open(DICT, errors="ignore")} if os.path.exists(DICT) else set()
    # common set: embedded list + words seen >=2 times in the HN PARENT comments (human text outside the compared
    # sample), capped to 2,000 words by frequency.
    cnt = Counter(base(t) for r in human for t in TOKEN_RE.findall(clean(r["parent_text"])))
    from_parents = [w for w, c in cnt.most_common() if c >= 2 and w not in COMMON]
    common = set(COMMON) | set(from_parents[: max(0, 2000 - len(COMMON))])
    rng = random.Random(SEED)
    if sample:
        print("HN human flagged tokens:"); [print("  ", s) for s in sample_tokens(human, dic, 20, rng, True)]
        print("Claude flagged tokens:"); [print("  ", s) for s in sample_tokens(claude, dic, 20, rng, True)]
        return
    H = [record(r["text"], common, dic) for r in human]
    C = [record(r["text"], common, dic) for r in claude]
    print("N messages: HN human %d, Claude %d" % (len(H), len(C)))
    for nm, rs in (("HN human", H), ("Claude", C)):
        w = [r["words"] or 0 for r in rs]
        print("  %-12s words/msg mean %.1f median %.0f; MATTR defined for %d msgs; drift defined for %d msgs"
              % (nm, sum(w) / len(w), sorted(w)[len(w) // 2], sum(r["mattr"] is not None for r in rs),
                 sum(r["drift"] is not None for r in rs)))
    print("common-word set: %d words (%d embedded + %d from HN parent comments seen 2+ times); target 2,000, "
          "so the HN-parent part is smaller than a true top-2,000 list and the rare-word share is relative to it."
          % (len(common), len(COMMON), len(common) - len(COMMON)))
    print("dictionary: %s (%d words)%s" % (DICT, len(dic), "" if dic else " MISSING"))
    print("Quoted lines (starting >) and URLs are removed before measuring. Intervals: bootstrap 95%%, %d resamples, seed %d;"
          " HN-vs-Claude resamples pairs together." % (NBOOT, SEED))
    print()
    hdr = "%-62s %8s %8s | %-22s %-9s"
    print(hdr % ("metric", "HN", "Claude", "Claude-HN [95%]", "verdict"))
    rows: List[Tuple[str, str]] = []
    for name, fn, _ in METRICS:
        h, c = fn(H), fn(C)
        lo1, hi1 = boot_ci(fn, C, H, True, rng)
        d1 = None if h is None or c is None else c - h
        v1 = verdict(lo1, hi1)
        print(hdr % (name[:62], fmt(h), fmt(c), "%s [%s, %s]" % (fmt(d1), fmt(lo1), fmt(hi1)), v1))
        rows.append((name, v1))
    hc = os.path.join(HERE, "typo_handcheck.json")
    if os.path.exists(hc):
        print("\nHand check of non-dictionary tokens (20 sampled per side, seed %d; classified by reading each token):" % SEED)
        for k, v in json.load(open(hc)).items():
            print("  %s" % k + ": " + v)


def write_results() -> None:
    """results.txt = results_head.txt + this run's table + results_tail.txt (head and tail are fixed text this script does not generate)."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main()
    parts = [open(os.path.join(HERE, n)).read() for n in ("results_head.txt",)]
    parts.append(buf.getvalue())
    parts.append(open(os.path.join(HERE, "results_tail.txt")).read())
    out = os.path.join(HERE, "results.txt")
    with open(out, "w") as f:
        f.write("\n".join(parts))
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    if "--results" in sys.argv:
        write_results()
    else:
        main()
