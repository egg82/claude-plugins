"""No source file grows past LIMIT lines: a file is a group of functions with one
purpose, not a feature's worth of everything. Files already over it are held in
tools/held/file_size.json as `{file: {"lines": n}}` through the shared ledger. A new
long file, or a held one that grew, fails; one that shrank fails as stale until the
ledger is rewritten. `python tests/test_file_size.py --write` rewrites the ledger;
never run it to let a longer file through.

Generated files are named one by one in EXCLUDE_FILES, so a new generated file is counted
until someone excludes it on purpose.

Template from the agentic-engineering skill: set SRC, SUFFIXES and EXCLUDE_FILES, then seed
with --write once."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from held_ledger import Ledger, dump, load, problems, total  # noqa: E402

# Set me: hand-written source AND tests; generated files live elsewhere.
SRC = [ROOT / "PACKAGE"]
SUFFIXES = {".py", ".js", ".ts", ".mjs"}
SKIP_DIRS = {"node_modules", "dist"}
EXCLUDE_FILES: set[str] = set()  # repo-relative generated files, e.g. a `wrangler types` output
HELD = ROOT / "tools" / "held" / "file_size.json"
LIMIT = 400


def files() -> list[Path]:
    return sorted(
        p
        for d in SRC
        for p in d.rglob("*")
        if p.suffix in SUFFIXES
        and p.is_file()
        and not SKIP_DIRS & set(p.relative_to(ROOT).parts)
        and p.relative_to(ROOT).as_posix() not in EXCLUDE_FILES
    )


def counted() -> Ledger:
    out: Ledger = {}
    for p in files():
        n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        if n > LIMIT:
            out[p.relative_to(ROOT).as_posix()] = {"lines": n}
    return out


def test_the_gate_sees_the_code():
    found = files()
    for d in SRC:  # per root: one root scanning nothing hides behind the others
        assert any(d in p.parents for p in found), f"nothing scanned under {d}"


def test_every_exclusion_exists():
    missing = [f for f in EXCLUDE_FILES if not (ROOT / f).is_file()]
    assert not missing, f"excluded files that do not exist: {missing}"


def test_the_held_ledger_is_what_the_code_is():
    wrong = problems(
        counted(),
        load(HELD),
        f"over {LIMIT} lines and not held: split it",
        "python tests/test_file_size.py --write",
    )
    assert not wrong, "\n".join(wrong)


def test_this_test_can_fail():
    held = {"a.py": {"lines": LIMIT + 50}}
    assert problems(held, held, "", "") == []
    assert problems({"a.py": {"lines": LIMIT + 51}}, held, "grew", "")[0].endswith(
        "grew"
    )
    assert "stale" in problems({"a.py": {"lines": LIMIT + 1}}, held, "", "")[0]
    assert len(problems({"b.py": {"lines": LIMIT + 50}}, held, "", "")) == 2


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        HELD.parent.mkdir(parents=True, exist_ok=True)
        HELD.write_text(dump(counted()))
        print(
            f"wrote {HELD.relative_to(ROOT)}: "
            f"{len(counted())} files, {total(counted())} lines held"
        )
