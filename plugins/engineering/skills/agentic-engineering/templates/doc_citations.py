"""The citation extractor and checker behind tests/test_doc_citations.py; the rules are
in that test's docstring.

Template from the agentic-engineering skill: set PKG_NAME, PATH_PREFIXES and the SKIP_*
entries, and put this file in tests/ beside test_doc_citations.py."""
from __future__ import annotations

import importlib
import itertools
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# Set me: the importable package the docs cite, and the top-level directories a cited path
# may start with.
PKG_NAME = "PACKAGE"
PATH_PREFIXES = (f"{PKG_NAME}/", "tests/", "docs/", "tools/")
PKG = ROOT / PKG_NAME
PREFIX = PKG_NAME + "."

SPAN = re.compile(r"`([^`\n]+)`")
ROOT_DOC = re.compile(r"^[A-Z][A-Z_-]*\.md$")
SYMBOL = re.compile(rf"^(?:{re.escape(PREFIX)})?[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+(?:\(.*\))?$")
FILE_FUNC = re.compile(r"^([A-Za-z_]\w*\.py):([A-Za-z_]\w*)$")
EXTENSIONS = {"py", "js", "json", "md", "html", "yml", "yaml", "sh", "sql", "txt", "css", "toml",
              "jsonl", "ts", "tsx"}

#: Path-like spans that are not files in this repo, each with why. A span that looks like a path
#: (has a `/`, or a stem and a known extension) must resolve, be `planned:`, or match one of these;
#: an entry nothing matches fails (tests/test_doc_citations.py). A neighbouring repo's file is cited
#: by its `~/` path, never by a bare name, so it falls under "~".
SKIP_PREFIXES = {
    "~": "another repo or the home directory, not checkable from here",
    "/": "an HTTP route or an absolute path, not a repo file",
}
# Set me: exact spans that look like paths and are not (a Vault path, an owner/repo, an image).
SKIP_EXACT: dict[str, str] = {}
SKIP_REASONS = {**SKIP_PREFIXES, **SKIP_EXACT}


def _modules() -> tuple[set[str], dict[str, list[str]]]:
    """(top-level module names, nested module basename -> dotted module paths)."""
    top: set[str] = set()
    nested: dict[str, list[str]] = {}
    for p in PKG.rglob("*.py"):
        parts = list(p.relative_to(PKG).parts)
        parts[-1] = parts[-1][:-3]
        if parts[-1] == "__init__":
            parts.pop()
        if not parts:
            continue
        if len(parts) == 1:
            top.add(parts[0])
        else:
            nested.setdefault(parts[-1], []).append(PREFIX + ".".join(parts))
    return top, nested


TOP, NESTED = _modules()
assert TOP, f"found no {PKG_NAME} modules; the symbol rule would ignore everything"


def _expand(path: str) -> list[str]:
    m = re.search(r"\{([^{}]*)\}", path)
    if not m:
        return [path]
    return list(itertools.chain.from_iterable(
        _expand(path[:m.start()] + alt + path[m.end():]) for alt in m[1].split(",")))


def skip_entry(word: str) -> str | None:
    """The SKIP_PREFIXES / SKIP_EXACT key that excuses this path-like word, if any."""
    if word in SKIP_EXACT:
        return word
    return next((p for p in SKIP_PREFIXES if word.startswith(p)), None)


def looks_like_path(word: str) -> bool:
    """A `/` anywhere, or a stem plus a known file extension. Not `.na` (no stem)."""
    if "/" in word:
        return True
    stem, dot, ext = word.rpartition(".")
    return bool(stem and dot and ext in EXTENSIONS)


def _symbol(span: str) -> str | None:
    parts = span.removeprefix(PREFIX).split("(")[0].split(".")
    if parts[-1] in EXTENSIONS:
        return None
    if span.startswith(PREFIX) or parts[0] in TOP or len(NESTED.get(parts[0], [])) == 1:
        return span.split("(")[0]
    return None


def extract(text: str, live: bool = True) -> dict[str, list[str]]:
    """kind -> citations, where kind is path | symbol | file_func | planned | skipped. `skipped`
    holds the SKIP_* entry that excused each path-like span, so the test can report and audit
    them."""
    found: dict[str, list[str]] = {"path": [], "symbol": [], "file_func": [], "planned": [],
                                   "skipped": []}
    for span in SPAN.findall(text):
        span = span.strip()
        if span.startswith("planned:"):
            found["planned"].append(span.removeprefix("planned:").strip())
            continue
        first = span.split()[0] if span.split() else ""
        if first.startswith(PATH_PREFIXES) or ROOT_DOC.match(span):
            if "<" not in first:
                found["path"].append(first.split(":")[0])
            continue
        word = first.split(":")[0]
        if "(" not in word and not FILE_FUNC.match(span) and looks_like_path(word):
            if entry := skip_entry(word):
                found["skipped"].append(entry)
            elif "<" not in word:
                found["path"].append(word)
            continue
        if " " in span and not re.search(r"\(.*\)$", span):
            continue
        if live and FILE_FUNC.match(span):
            found["file_func"].append(span)
        elif SYMBOL.match(span) and (sym := _symbol(span)):
            found["symbol"].append(sym)
    return found


def check_path(path: str) -> str | None:
    for p in _expand(path):
        hit = list(ROOT.glob(p)) if "*" in p else ([ROOT / p] if (ROOT / p).exists() else [])
        if not hit:
            return f"path does not exist: {p}"
    return None


def _walk(base: str, rest: list[str], full: str) -> str | None:
    obj = importlib.import_module(base)
    for part in rest:
        if hasattr(obj, part):
            obj = getattr(obj, part)
            continue
        try:
            obj = importlib.import_module(f"{obj.__name__}.{part}")
        except (ImportError, AttributeError):
            where = getattr(obj, "__name__", obj)
            return f"symbol does not resolve: {full} (no {part!r} on {where})"
    return None


def check_symbol(sym: str) -> str | None:
    parts = sym.removeprefix(PREFIX).split(".")
    if parts[0] in TOP:
        base = PREFIX + parts[0]
    elif parts[0] in NESTED:
        base = NESTED[parts[0]][0]
    else:
        return f"symbol does not resolve: {sym} (no {PKG_NAME} module {parts[0]!r})"
    return _walk(base, parts[1:], sym)


def check_file_func(span: str) -> str | None:
    m = FILE_FUNC.match(span)
    assert m is not None
    fname, func = m.groups()
    hits = [PKG / fname] if (PKG / fname).is_file() else list(PKG.rglob(fname))
    if len(hits) != 1:
        return f"file not unique under {PKG_NAME}/: {fname} ({len(hits)} found)"
    dotted = PREFIX + ".".join(hits[0].relative_to(PKG).with_suffix("").parts)
    return _walk(dotted, [func], span)


def check_planned(target: str) -> str | None:
    """A planned target must not exist yet; the marker is dropped when it does."""
    if target.startswith(PATH_PREFIXES) or looks_like_path(target):
        built = check_path(target) is None
    else:
        parts = target.removeprefix(PREFIX).split(".")
        try:
            built = _walk(PREFIX + parts[0], parts[1:], target) is None
        except ImportError:
            built = False
    return f"planned {target} now exists: drop the marker" if built else None


def failures(text: str, live: bool = True) -> list[str]:
    found = extract(text, live)
    out = [check_path(p) for p in found["path"]]
    out += [check_symbol(s) for s in found["symbol"]]
    out += [check_file_func(s) for s in found["file_func"]]
    out += [check_planned(t) for t in found["planned"]]
    return [o for o in out if o]
