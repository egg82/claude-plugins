"""No source file grows past LIMIT lines: a file is a group of functions with one
purpose, not a feature's worth of everything. Files already over it are held in
tools/held/file_size.json as `{file: {"lines": n}}` through the shared ledger. A new
long file, or a held one that grew, fails; one that shrank fails as stale until the
ledger is rewritten. `python tests/test_file_size.py --write` rewrites the ledger;
never run it to let a longer file through.

Template from the agentic-engineering skill: set SRC and SUFFIXES, then seed with
--write once."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from held_ledger import Ledger, dump, load, problems, total  # noqa: E402

# Set me: hand-written source only; generated files live elsewhere.
SRC = [ROOT / "PACKAGE"]
SUFFIXES = {".py", ".js", ".ts", ".mjs"}
HELD = ROOT / "tools" / "held" / "file_size.json"
LIMIT = 400


def files() -> list[Path]:
    return sorted(
        p
        for d in SRC
        for p in d.rglob("*")
        if p.suffix in SUFFIXES and p.is_file() and "node_modules" not in p.parts
    )


def counted() -> Ledger:
    out: Ledger = {}
    for p in files():
        n = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        if n > LIMIT:
            out[p.relative_to(ROOT).as_posix()] = {"lines": n}
    return out


def test_the_gate_sees_the_code():
    assert files(), f"no source files under {SRC}: the gate would pass on nothing"


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
