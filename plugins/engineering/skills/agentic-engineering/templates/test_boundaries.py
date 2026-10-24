"""Which top-level modules of the package may import which. Every import counts,
including a lazy one inside a function, since a lazy import still couples the two. A
new edge fails until it is added to ALLOWED, and that is the moment to ask whether
the code belongs where it is. An entry nothing uses fails too, so the list stays what
the code is. `python tests/test_boundaries.py --write` prints today's edges as an
ALLOWED literal to seed it once.

Template from the agentic-engineering skill: set PKG, seed ALLOWED, then shrink it on
purpose."""

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "PACKAGE"  # set me: the package directory (its name is the import root)

# Top-level module or subpackage -> those it may import. Seed with --write, then
# cut edges deliberately.
ALLOWED: dict[str, set[str]] = {}

# Each import cycle ALLOWED contains, as the set of its modules. Only shrinks; adding
# the edge that closes a new cycle fails even after ALLOWED takes it.
CYCLES: list[set[str]] = []


def top(path: Path) -> str:
    rel = path.relative_to(PKG)
    return rel.parts[0] if len(rel.parts) > 1 else rel.stem


def units() -> set[str]:
    """The top-level modules and subpackages; `from pkg import __version__` names
    neither, so names that are not units are not edges."""
    return {top(p) for p in PKG.rglob("*.py")} - {"__init__"}


def edges_of(source: str, module: str, is_package: bool = False) -> set[str]:
    """The top-level siblings one module imports, given its dotted name
    (`pkg.sources.alpha`, or `pkg.sources` for a package's `__init__`): `import
    pkg.x`, `from pkg.x import y`, `from pkg import x`, and relative imports resolved
    against the module's own package, at any depth in the file."""
    parts = module.split(".")
    name, own = parts[0], parts[1] if len(parts) > 1 else ""
    out: set[str] = set()
    for n in ast.walk(ast.parse(source)):
        if isinstance(n, ast.Import):
            out |= {
                a.name.split(".")[1] for a in n.names if a.name.startswith(name + ".")
            }
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                # `.` is the module's own package: its parent for a module, itself for a
                # package __init__
                base = parts[: len(parts) - n.level + (1 if is_package else 0)]
                target = base + (n.module.split(".") if n.module else [])
            else:
                target = n.module.split(".") if n.module else []
            if not target or target[0] != name:
                continue
            out |= {target[1]} if len(target) > 1 else {a.name for a in n.names}
    return out - {own, "__init__"}


def dotted(path: Path) -> str:
    rel = path.relative_to(PKG.parent).with_suffix("")
    return ".".join(rel.parts[:-1] if rel.name == "__init__" else rel.parts)


def edges() -> dict[str, set[str]]:
    known = units()
    out: dict[str, set[str]] = {}
    for p in sorted(PKG.rglob("*.py")):
        if p.name == "__init__.py" and p.parent == PKG:
            continue
        found = edges_of(
            p.read_text(encoding="utf-8"), dotted(p), p.name == "__init__.py"
        )
        out.setdefault(top(p), set()).update(found & known)
    return {k: v for k, v in out.items() if v}


def cycles(graph: dict[str, set[str]]) -> list[set[str]]:
    """Every strongly connected component of more than one module (Tarjan), plus
    self-loops."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    out: list[set[str]] = []

    def visit(v: str) -> None:
        index[v] = low[v] = len(index)
        stack.append(v)
        for w in graph.get(v, set()):
            if w not in index:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in stack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            comp = set()
            while True:
                w = stack.pop()
                comp.add(w)
                if w == v:
                    break
            if len(comp) > 1 or v in graph.get(v, set()):
                out.append(comp)

    for v in sorted(graph):
        if v not in index:
            visit(v)
    return sorted(out, key=sorted)


def test_the_gate_sees_the_package():
    assert len(units()) > 1 and edges(), (
        f"no import edges under {PKG}: gate sees nothing"
    )


def test_the_held_cycles_are_what_allowed_is():
    found = cycles(ALLOWED)
    assert found == sorted(CYCLES, key=sorted), (
        f"import cycles in ALLOWED: {found}, held {CYCLES}; break the new one"
    )


def test_every_import_edge_is_allowed():
    new = sorted(
        f"{a} -> {b}" for a, bs in edges().items() for b in bs - ALLOWED.get(a, set())
    )
    assert not new, (
        "imports not in ALLOWED "
        "(decide whether the code belongs here, then add the edge):\n" + "\n".join(new)
    )


def test_every_allowed_edge_is_used():
    found = edges()
    stale = sorted(
        f"{a} -> {b}" for a, bs in ALLOWED.items() for b in bs - found.get(a, set())
    )
    assert not stale, "ALLOWED edges nothing uses (remove them):\n" + "\n".join(stale)


def test_this_test_can_fail():
    assert edges_of("from pkg.db import x\n", "pkg.api") == {"db"}
    assert edges_of("def f():\n    import pkg.views.page\n", "pkg.api") == {"views"}
    assert edges_of("from . import db, logs\n", "pkg.api") == {"db", "logs"}
    assert edges_of("from .db import conn\nimport os\n", "pkg.api") == {"db"}
    assert edges_of("from pkg import api\n", "pkg.api") == set()
    # inside a subpackage, `from . import base` is a sibling in the same top-level unit,
    # not a new edge
    assert edges_of("from . import base\n", "pkg.sources.alpha") == set()
    assert edges_of("from ..db import conn\n", "pkg.sources.alpha") == {"db"}
    assert (
        edges_of("from .base import x\n", "pkg.sources", is_package=True) == set()
    )  # a package __init__
    assert edges_of("from ..db import x\n", "pkg.sources", is_package=True) == {"db"}
    # cycles: none in a chain; a two-cycle and a self-loop are found
    assert cycles({"a": {"b"}, "b": {"c"}}) == []
    assert cycles({"a": {"b"}, "b": {"a"}, "c": {"c"}}) == [{"a", "b"}, {"c"}]


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        print("ALLOWED = {")
        for k, v in sorted(edges().items()):
            print(f"    {k!r}: {sorted(v)!r},".replace("[", "{").replace("]", "}"))
        print("}")
        held = ", ".join(
            "{" + ", ".join(repr(m) for m in sorted(c)) + "}" for c in cycles(edges())
        )
        print(f"CYCLES = [{held}]")
