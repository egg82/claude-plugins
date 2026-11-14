"""Citations resolve in both directions: every code path and symbol the docs cite exists, and
every `docs/*.md` the code cites exists. A comment cannot 404: split a module and a dozen
citations point at nothing while every test stays green. This is the drift check that replaces
"remember to update the docs". The extractor is tests/doc_citations.py.

The docs are every `docs/*.md` and every root `*.md`, found on disk. What counts as a citation (a
backticked span; everything else is prose, and ignored):

- **A repo path**: the first word starts with one of PATH_PREFIXES, is a root document in
  capitals (`README.md`), or looks like a path anywhere else (a `/`, or a stem and a known
  extension: `pyproject.toml`). It must exist; a `*` glob must match something; `{a,b}` is
  expanded; a trailing `:name` is dropped. A span with a `<placeholder>` is a pattern.
- **A skipped path**: a path-like span that is not a file here and matches an entry in
  `SKIP_PREFIXES` or `SKIP_EXACT`, each with its reason. `~/...` is a neighbouring repo, so
  another repo's file is cited by its `~/` path, never a bare name. Skipped spans are counted by
  reason in the test output, and an entry nothing matches fails.
- **A dotted symbol**: `module.attr[.attr]` or `<package>.module.attr`, optionally with a trailing
  call `(...)`, whose first part names a module of the package. `import` plus `getattr` must
  reach every part.
- **A `file.py:function` pair**, where `file.py` is unique under the package.
- **A planned citation**: `planned: <target>` inside the backticks, where the target is a repo
  path or a symbol. It names code that is not built yet: skipped while the target is missing,
  and FAILS once it exists ("drop the marker"), so the marker cannot outlive the code. Dropping
  the backticks instead opts the citation out of checking, which is the dodge this form exists
  to make unnecessary. Only the docs in PLANNED_IN may use it: the queue, the systems inventory
  and the rulebook, which describe what the build is heading for.

Not citations: a span with spaces whose first word is not path-like (a command, a SQL fragment),
an extension with no stem (`.na`), and a bare word.

Code to docs: the code cites a doc by path (`see docs/search.md`), so a renamed doc must fail
here, and nothing may cite a queue position (`open-work.md item 3`): items get done and
renumbered, and the citation silently points at something else. Cite the subject.

Template from the agentic-engineering skill: set the doc_citations.py settings, PLANNED_IN,
FLOOR (today's total less a margin) and the REAL_* citations below.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT))
from doc_citations import PKG, PKG_NAME, SKIP_REASONS, extract, failures  # noqa: E402

DOCS = sorted([*(ROOT / "docs").glob("*.md"), *ROOT.glob("*.md")])
PLANNED_IN = {"docs/open-work.md", "docs/systems.md", "docs/engineering.md"}
#: Today's total less a margin, so a broken extractor fails rather than finding nothing.
FLOOR = 50
# Set me: citations that exist in this repo, so the resolving controls test something real.
REAL_SYMBOL = f"{PKG_NAME}.module.attr"
REAL_FILE_FUNC = "module.py:function"

DOC_CITATION = re.compile(r"(?<![\w/~.-])docs/[A-Za-z0-9_.-]+\.md")
QUEUE_POSITION = re.compile(r"open-work\.md item|\bitem \d+[a-z]?\b", re.IGNORECASE)


def _rel(doc: Path) -> str:
    return doc.relative_to(ROOT).as_posix()


def _code() -> list[Path]:
    return [p for p in PKG.rglob("*") if p.suffix in {".py", ".sql", ".html", ".js", ".ts"}]


def misplaced_planned(doc: str, found: dict[str, list[str]]) -> list[str]:
    if doc in PLANNED_IN:
        return []
    return [f"planned {t} cited outside {sorted(PLANNED_IN)}" for t in found["planned"]]


def test_the_gate_sees_the_docs():
    total = sum(len(v) for d in DOCS for k, v in extract(d.read_text(encoding="utf-8")).items()
                if k != "skipped")
    assert {"docs/systems.md", "docs/engineering.md", "CLAUDE.md"} <= {_rel(d) for d in DOCS}
    assert total >= FLOOR, f"found only {total} citations in {len(DOCS)} docs: extractor broken"


@pytest.mark.parametrize("doc", DOCS, ids=_rel)
def test_every_cited_path_and_symbol_exists(doc: Path):
    text = doc.read_text(encoding="utf-8")
    found = extract(text)
    kinds = dict(Counter({k: len(v) for k, v in found.items()}))
    cited = sum(n for k, n in kinds.items() if k != "skipped")
    assert cited >= 1, f"{_rel(doc)}: no citations at all ({kinds})"
    bad = failures(text) + misplaced_planned(_rel(doc), found)
    assert not bad, f"{_rel(doc)} cites code that is not there:\n  " + "\n  ".join(bad)


def _skipped() -> Counter[str]:
    return Counter(e for d in DOCS for e in extract(d.read_text(encoding="utf-8"))["skipped"])


def test_every_skip_entry_matches_a_span_and_is_reported(capsys: pytest.CaptureFixture[str]):
    used = _skipped()
    unused = sorted(set(SKIP_REASONS) - set(used))
    assert not unused, f"skip entries no doc span matches (remove them): {unused}"
    with capsys.disabled():
        print("\ncitation spans skipped, by reason:")
        for entry, n in sorted(used.items()):
            print(f"  {n:3d}  {entry!r}: {SKIP_REASONS[entry]}")


def test_every_doc_the_code_cites_exists():
    cited: dict[str, set[str]] = {}
    for path in _code():
        for hit in DOC_CITATION.findall(path.read_text(encoding="utf-8", errors="replace")):
            cited.setdefault(hit, set()).add(_rel(path))
    missing = {doc: who for doc, who in cited.items() if not (ROOT / doc).is_file()}
    assert not missing, "cited but absent: " + "; ".join(
        f"{doc} (from {', '.join(sorted(who))})" for doc, who in sorted(missing.items()))


def test_nothing_cites_a_queue_position():
    offenders = [
        f"{_rel(path)}:{n}"
        for path in _code()
        for n, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1)
        if QUEUE_POSITION.search(line)
    ]
    assert not offenders, "citations to a queue position: " + ", ".join(offenders)


# Controls: the gate must be able to fail, and must not fire on prose.

def test_the_code_scan_sees_code():
    assert _code(), f"no code under {PKG_NAME}/: the code-to-docs checks would pass on nothing"
    assert DOC_CITATION.findall("see docs/search.md, not ~/other/docs/x.md") == ["docs/search.md"]
    assert QUEUE_POSITION.search("# blocked on open-work.md item 3")


def test_a_planned_citation_outside_the_allowed_docs_fails():
    found = extract(f"`planned: {PKG_NAME}/nonesuch.py`")
    assert misplaced_planned("CLAUDE.md", found)
    assert not misplaced_planned("docs/systems.md", found)


def test_catches_a_missing_path_and_a_missing_symbol():
    text = f"See `{PKG_NAME}/nonesuch.py` and `{REAL_SYMBOL}_nope`."
    assert len(failures(text)) == 2


def test_catches_a_missing_path_without_a_known_prefix():
    assert failures("`scripts/nope.jsonl`") == ["path does not exist: scripts/nope.jsonl"]
    assert failures("`nope.toml`") == ["path does not exist: nope.toml"]


def test_skipped_spans_are_not_checked_and_are_reported():
    found = extract("`~/other/repo/nope.py` `/api/me` `nope/dir`")
    assert found["skipped"] == ["~", "/"]
    assert found["path"] == ["nope/dir"]


def test_catches_a_missing_root_document_and_resolves_a_live_one():
    assert failures("`NONESUCH.md`") == ["path does not exist: NONESUCH.md"]
    assert not failures("`CLAUDE.md`")


def test_catches_a_missing_brace_member_and_empty_glob():
    assert failures("`tests/test_doc_citations.py` `tests/test_no_such_{a,b}.py`")
    assert failures(f"`{PKG_NAME}/*.nothing`")


def test_catches_a_stale_file_function_pair_only_in_live_docs():
    stale = REAL_FILE_FUNC + "_nope"
    assert failures(f"`{stale}`", live=True)
    assert not failures(f"`{stale}`", live=False)


def test_resolves_real_citations():
    text = (f"`{REAL_SYMBOL}` `{REAL_FILE_FUNC}` "
            "`tests/test_doc_citations.py` `tests/{doc_citations,test_doc_citations}.py`")
    found = extract(text)
    assert found["symbol"] and found["file_func"] and not failures(text)


def test_planned_citation_whose_target_exists_fails():
    bad = failures(f"`planned: tests/test_doc_citations.py` `planned: {REAL_SYMBOL}`")
    assert len(bad) == 2 and all("drop the marker" in b for b in bad)


def test_planned_citation_whose_target_is_missing_passes():
    text = f"`planned: {PKG_NAME}/nonesuch/` `planned: {PKG_NAME}.nonesuch.run`"
    assert extract(text)["planned"] and not failures(text)


def test_unmarked_missing_target_still_fails():
    assert failures(f"`{PKG_NAME}/nonesuch.py` `{PKG_NAME}.nonesuch.run`")


def test_ignores_what_is_not_a_citation():
    prose = ("`kubectl -n ns get pods` `SELECT count(*) FROM item WHERE a.b = 1` "
             "`~/other/repo/x.py` `.na` `docs/<name>.md` `main` `tests/test_doc_citations.py -q`")
    found = extract(prose)
    assert found["symbol"] == [] and found["file_func"] == []
    assert found["path"] == ["tests/test_doc_citations.py"]
