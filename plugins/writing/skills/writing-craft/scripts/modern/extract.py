#!/usr/bin/env python3
"""Pull WritingPrompts stories, clean them, and select figurative lines and paragraphs.

Writes human-lines.jsonl, human-paras.jsonl and offsets-used.json beside this file.
Raw API pages are cached in .cache/ (personal research use only, never redistribute).
Reproducible: fixed seed, fixed offsets (recorded in offsets-used.json).
"""
import json
import random
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache"
API = "https://datasets-server.huggingface.co/rows"
DATASET = "euclaise/writingprompts"
SEED = 20261021
N_PAGES = 30          # x100 rows = 3000 stories
TOTAL_ROWS = 272600   # train split size; pages are drawn from evenly spread slots

MARKERS = [" like a ", " like an ", " like the ", " like some ", " as if ", " as though ",
            " as a ", " was a ", " were a "]
FIG_STRICT = [" like a ", " like an ", " like the ", " as if ", " as though "]
BAD_WORDS = set("""fuck fucking fucked shit bitch bitches cock cocks dick dicks pussy cum cumming sex sexual rape raped
raping nude naked penis vagina boobs breasts tits nipples orgasm erection masturbate whore slut cunt ass asshole damn
semen horny porn molest genitals thrust moan moaned moaning kill killed""".split())
# "kill" words stay out of the control set only to keep the register mild; dropped from list if too strict
BAD_WORDS -= {"kill", "killed"}


def fetch_page(offset: int) -> list[dict]:
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"rows-{offset}.json"
    if f.exists():
        return json.loads(f.read_text())
    q = urllib.parse.urlencode({"dataset": DATASET, "config": "default", "split": "train",
                                "offset": offset, "length": 100})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(f"{API}?{q}", timeout=60) as r:
                data = json.load(r)
            rows = [x["row"] for x in data["rows"]]
            f.write_text(json.dumps(rows))
            return rows
        except Exception as e:  # noqa: BLE001 - retry any network error
            print(f"  offset {offset} attempt {attempt}: {type(e).__name__} {e}", flush=True)
            time.sleep(3 * (attempt + 1))
    raise SystemExit(f"could not fetch offset {offset}")


def clean(story: str) -> str:
    s = story.replace("<newline>", "\n")
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)           # markdown links
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"\s+(n't|'s|'re|'ve|'ll|'d|'m)\b", r"\1", s)       # undo tokenizer spacing
    s = re.sub(r"\s+[’']\s*(s|t|re|ve|ll|d|m)\b", r"'\1", s)
    s = s.replace("``", '"').replace("''", '"').replace("’", "'")
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    s = re.sub(r"[*_~^]{1,3}", "", s)                         # emphasis markers
    s = re.sub(r"^\s*>+\s*", "", s, flags=re.M)
    lines = []
    for ln in s.split("\n"):
        t = ln.strip()
        if not t:
            continue
        if re.match(r"^(edit|eta|update|ps|p\.s\.|thanks for|thank you for|wow,? thanks|/r/|r/)", t, re.I):
            continue
        if re.search(r"\b(edit\s*\d*:|\/r\/|subreddit|upvote|gold|gilded|my first post|first time posting)", t, re.I):
            continue
        lines.append(t)
    return "\n".join(lines)


def sentences(text: str) -> list[str]:
    out: list[str] = []
    for para in text.split("\n"):
        parts = re.split(r"(?<=[.!?])[\"')\]]*\s+(?=[\"'(A-Z])", para)
        out += [p.strip() for p in parts if p.strip()]
    return out


def words(s: str) -> int:
    return len(s.split())


def clean_ok(s: str) -> bool:
    toks = set(re.findall(r"[a-z']+", s.lower()))
    if toks & BAD_WORDS:
        return False
    if re.search(r"[\"“”]", s):          # dialogue / quoted speech
        return False
    if re.search(r"\b(you|your|you're|yours)\b", s, re.I):   # second person
        return False
    if re.search(r"\(|\)|\[|\]|&|#|http", s):
        return False
    return s[:1].isupper() and s[-1:] in ".!?"


VERB_LIKE = re.compile(r"\b(would|'d|do|did|don't|didn't|to|i|you|we|they|he|she|really|might|may|"
                       r"could|should|will|just|also|not|never|always|people|who|that|which|particularly|for|felt|feel|feels|seemed|seems|what|something) like (a|an|the)\b", re.I)


def figurative(s: str) -> bool:
    if VERB_LIKE.search(s):
        return False
    low = " " + s.lower() + " "
    return any(m in low for m in FIG_STRICT)


def main() -> None:
    rng = random.Random(SEED)
    stride = TOTAL_ROWS // N_PAGES
    offsets = sorted(rng.randrange(i * stride, (i + 1) * stride - 100) for i in range(N_PAGES))
    stories: list[dict] = []
    for off in offsets:
        rows = fetch_page(off)
        for i, r in enumerate(rows):
            stories.append({"offset": off + i, "story": clean(r["story"])})
    print(f"fetched {len(stories)} stories from {len(offsets)} pages")

    line_cands: list[tuple[int, int, str, str]] = []   # (story_offset, idx, text, frame)
    para_cands: list[tuple[int, str, str]] = []
    for st in stories:
        sents = sentences(st["story"])
        if len(sents) < 8:
            continue
        for i in range(2, len(sents)):
            s = sents[i]
            if 12 <= words(s) <= 40 and clean_ok(s) and figurative(s):
                fr = sents[i - 2:i]
                if all(clean_ok(x) and words(x) >= 5 for x in fr):
                    if not re.search(r"\b(sex|naked|nude|rape)\b", " ".join(fr), re.I):
                        line_cands.append((st["offset"], i, s, " ".join(fr)))
        # paragraphs: accumulate consecutive sentences within one source paragraph block
        paras = [p for p in st["story"].split("\n")]
        for pi in range(1, len(paras)):
            p = paras[pi]
            if 80 <= words(p) <= 120 and clean_ok(p.replace("\n", " ")) and figurative(p):
                prev = sentences("\n".join(paras[:pi]))
                if len(prev) >= 2 and all(clean_ok(x) and words(x) >= 5 for x in prev[-2:]):
                    para_cands.append((st["offset"], p, " ".join(prev[-2:])))
    print(f"line candidates {len(line_cands)}; para candidates {len(para_cands)}")

    rng.shuffle(line_cands)
    rng.shuffle(para_cands)
    used: set[int] = set()
    lines = []
    for so, _i, text, frame in line_cands:
        if so in used:
            continue
        used.add(so)
        lines.append({"id": f"mh{len(lines)+1:02d}", "text": text, "frame": frame,
                      "story_offset": so, "words": words(text)})
        if len(lines) == 40:
            break
    paras = []
    for so, text, frame in para_cands:
        if so in used:
            continue
        used.add(so)
        paras.append({"id": f"mp{len(paras)+1:02d}", "text": text, "frame": frame,
                      "story_offset": so, "words": words(text)})
        if len(paras) == 15:
            break
    assert len(lines) == 40 and len(paras) == 15, (len(lines), len(paras))
    for name, rows in (("human-lines.jsonl", lines), ("human-paras.jsonl", paras)):
        (HERE / name).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    (HERE / "offsets-used.json").write_text(json.dumps(
        {"seed": SEED, "dataset": DATASET, "page_offsets": offsets,
         "line_story_offsets": [r["story_offset"] for r in lines],
         "para_story_offsets": [r["story_offset"] for r in paras]}, indent=1))
    print("wrote", len(lines), "lines,", len(paras), "paras")


if __name__ == "__main__":
    main()
