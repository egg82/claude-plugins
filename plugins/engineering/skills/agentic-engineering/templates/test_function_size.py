"""No function grows past LIMIT lines: large functions are where bugs hide. Functions
already over it are held in tools/held/function_size.json as `{file: {qualified name:
lines}}` through the shared ledger (tools/held_ledger.py). A new long function, or a
held one that grew, fails naming it. One that shrank or went fails as stale, so a
split in one place cannot pay for a new long function in another, even under the same
name. `python tests/test_function_size.py --write` rewrites the ledger; never run it
to let a longer function through.

Template from the agentic-engineering skill: set SRC to the package directories, then
seed with --write once."""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from held_ledger import Ledger, dump, load, problems, total  # noqa: E402

# Set me: the hand-written source packages (never tests or generated code).
SRC = [ROOT / "PACKAGE"]
HELD = ROOT / "tools" / "held" / "function_size.json"
LIMIT = 80


def sizes(source: str) -> dict[str, int]:
    """Lines of every function over LIMIT in one file, by qualified name
    (`Class.method`, `outer.inner`); a repeated name in one scope takes `#2`, `#3` in
    source order."""
    out: dict[str, int] = {}
    seen: set[str] = set()

    def walk(node: ast.AST, scope: str) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
                name = f"{scope}.{child.name}" if scope else child.name
                n = 1
                while name in seen:
                    n += 1
                    name = f"{scope}.{child.name}#{n}" if scope else f"{child.name}#{n}"
                seen.add(name)
                if not isinstance(child, ast.ClassDef):
                    lines = (child.end_lineno or child.lineno) - child.lineno + 1
                    if lines > LIMIT:
                        out[name] = lines
                walk(child, name)
            else:
                walk(child, scope)

    walk(ast.parse(source), "")
    return out


def files() -> list[Path]:
    return sorted(p for d in SRC for p in d.rglob("*.py"))


def counted() -> Ledger:
    ledger: Ledger = {}
    for p in files():
        found = sizes(p.read_text(encoding="utf-8"))
        if found:
            ledger[p.relative_to(ROOT).as_posix()] = found
    return ledger


FIX = f"over {LIMIT} lines and not held: split it"
WRITE = "python tests/test_function_size.py --write"


def test_the_gate_sees_the_code():
    assert files(), f"no .py files under {SRC}: the gate would pass on nothing"


def test_the_held_ledger_is_what_the_code_is():
    wrong = problems(counted(), load(HELD), FIX, WRITE)
    assert not wrong, "\n".join(wrong)


def test_this_test_can_fail():
    """Controls: a long function is found, twins get distinct names, a swap fails twice
    at an equal total, a shrink is stale."""
    body = "".join(f"    x = {i}\n" for i in range(LIMIT))
    assert list(sizes(f"def f():\n{body}")) == ["f"]
    assert sizes(f"def f():\n{body[: -len('    x = 0') - 2]}") == {}
    method_body = body.replace("    x", "        x")
    twin = f"def plan():\n{body}class V:\n    def plan(self):\n{method_body}"
    assert sorted(sizes(twin)) == ["V.plan", "plan"]
    assert sorted(sizes(f"def f():\n{body}def f():\n{body}")) == ["f", "f#2"]
    held = {"a.py": {"plan": LIMIT + 1}}
    assert problems(held, held, "", "") == []
    swapped = {"a.py": {"V.plan": LIMIT + 1}}
    assert len(problems(swapped, held, "", "")) == 2 and total(swapped) == total(held)
    assert "stale, lower it" in problems(held, {"a.py": {"plan": LIMIT + 9}}, "", "")[0]


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        HELD.parent.mkdir(parents=True, exist_ok=True)
        HELD.write_text(dump(counted()))
        print(
            f"wrote {HELD.relative_to(ROOT)}: "
            f"{len(counted())} files, {total(counted())} lines held"
        )
