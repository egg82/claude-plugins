#!/usr/bin/env python3
"""Cross-reference table for this marketplace: which items mention which.

Items are skills, hooks and stances. An item "mentions" another when its files contain
the other's name as a whole word (hyphens count as word characters, so `search-craft`
does not match inside `search-craft-gate`). Backticks need no special handling.

  python3 -B tools/xref.py                  print the markdown tables
  python3 -B tools/xref.py --check FILE     exit 1 if FILE's block between
                                            <!-- xref:begin --> and <!-- xref:end -->
                                            differs from fresh output
"""
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = {".md", ".sh", ".py", ".json", ".txt", ".toml", ".mjs", ".service", ".timer"}
BEGIN, END = "<!-- xref:begin -->", "<!-- xref:end -->"


def read_all(paths):
    return "\n".join(p.read_text(errors="ignore") for p in sorted(paths) if p.suffix in TEXT)


def collect():
    """Return {(kind, name): text} for every skill, hook and stance."""
    items = {}
    for sk in sorted(ROOT.glob("plugins/*/skills/*/")):
        items[("skill", sk.name)] = read_all(p for p in sk.rglob("*") if p.is_file())
    hooks = {}
    for h in sorted(ROOT.glob("plugins/*/hooks/*")):
        if h.suffix in (".sh", ".py") and not h.name.startswith("test-"):
            hooks.setdefault(h.stem, []).append(h)
    for name, files in hooks.items():
        items[("hook", name)] = read_all(files)
    for st in sorted(ROOT.glob("stances/*/*.md")):
        items[("stance", st.stem)] = read_all([st])
    return items


def mentions(items):
    """Return {item: [other items whose text mentions it]}."""
    pats = {k: re.compile(r"(?<![\w-])" + re.escape(k[1]) + r"(?![\w-])") for k in items}
    return {k: [o for o, text in items.items() if o != k and pats[k].search(text)] for k in items}


def label(k):
    return f"{k[0]}:{k[1]}"


def render():
    items = collect()
    by = mentions(items)
    out = []
    for kind, plural in (("skill", "Skills"), ("hook", "Hooks"), ("stance", "Stances")):
        cols = "| {} | Mentioned by |".format(kind.capitalize())
        sep = "|---|---|"
        if kind == "skill":
            cols += " Hooks it mentions |"
            sep += "---|"
        out += [f"#### {plural}", "", cols, sep]
        for k in sorted(k for k in items if k[0] == kind):
            cell = ", ".join(f"`{label(o)}`" for o in sorted(by[k])) or "-"
            row = f"| `{k[1]}` | {cell} |"
            if kind == "skill":
                hk = sorted(o for o in items if o[0] == "hook" and k in by[o])
                row += " " + (", ".join(f"`{o[1]}`" for o in hk) or "-") + " |"
            out.append(row)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def check(path):
    text = Path(path).read_text()
    if BEGIN not in text or END not in text:
        print(f"{path}: xref markers missing", file=sys.stderr)
        return 1
    have = text.split(BEGIN, 1)[1].split(END, 1)[0].strip() + "\n"
    want = render()
    if have == want:
        return 0
    sys.stdout.writelines(difflib.unified_diff(have.splitlines(1), want.splitlines(1), "CATALOG", "fresh"))
    print(f"{path}: xref block is stale; regenerate with tools/xref.py", file=sys.stderr)
    return 1


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--check":
        sys.exit(check(sys.argv[2]))
    if len(sys.argv) != 1:
        sys.exit(__doc__)
    sys.stdout.write(render())
