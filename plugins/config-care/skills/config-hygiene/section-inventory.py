#!/usr/bin/env python3
"""
Section inventory of a markdown file — run it BEFORE and AFTER a graft and diff.

    python3 section-inventory.py <file>            # print the inventory
    python3 section-inventory.py <a.md> <b.md>     # diff two files' inventories

WHY THIS EXISTS
---------------
Porting a section between two copies of a skill produced three boundary errors in
one exchange, each caught by a human or a peer rather than by anything here:

  1. a `### 10` grafted beside an existing `### 10` — two sections, same number
  2. a function grafted without its dispatcher line — a dead button, then reported
     wrongly blamed on the receiving copy, which had in fact dispatched correctly
  3. a section inserted mid-list, orphaning the tail of the PREVIOUS section under
     the new heading — the surviving tell was that the orphaned bullets wrapped at
     the previous section's width, not the new one's

All three come from one mistake: **anchoring on a single string and assuming it is
the section boundary.** It isn't, if the section has more content below the anchor.

`hygiene.py numbering` catches shape 1. This catches shape 3, which is the one that
leaves no trace in the numbering: the numbers stay valid while the CONTENT moved.
Shape 2 needs no tool — graft the wiring with the function, in one edit.

HOW TO USE IT
-------------
    python3 section-inventory.py SKILL.md > /tmp/before
    # ...do the graft...
    python3 section-inventory.py SKILL.md > /tmp/after
    diff /tmp/before /tmp/after

**A section you did not intend to touch must not change.** If one lost bullets or
lines, its tail moved under your new heading. The wrap column is the corroborating
signal — a block whose median width matches its NEIGHBOUR rather than its own
section was written elsewhere and landed here.

This reports; it never edits. It has no false positives to switch off, because it
makes no judgement — it is a before/after diff of your own edit.
"""
import re
import statistics
import sys
import pathlib


def inventory(path):
    lines = pathlib.Path(path).read_text(encoding="utf-8", errors="replace").split("\n")
    heads = [(i, l) for i, l in enumerate(lines) if re.match(r"^#{2,4} ", l)]
    rows = []
    for n, (i, h) in enumerate(heads):
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        body = lines[i + 1:end]
        widths = [len(l) for l in body if l.strip()]
        rows.append({
            "heading": h.strip(),
            "lines": sum(1 for l in body if l.strip()),
            "bullets": sum(1 for l in body if re.match(r"^\s*[-*] ", l)),
            "wrap": int(statistics.median(widths)) if widths else 0,
        })
    return rows


def render(rows):
    out = []
    for r in rows:
        out.append(f"{r['lines']:>4} lines {r['bullets']:>3} bullets  wrap {r['wrap']:>3}  {r['heading']}")
    return out


def main():
    if len(sys.argv) == 2:
        print("\n".join(render(inventory(sys.argv[1]))))
        return 0
    if len(sys.argv) == 3:
        a, b = inventory(sys.argv[1]), inventory(sys.argv[2])
        ka = {r["heading"]: r for r in a}
        kb = {r["heading"]: r for r in b}
        changed = 0
        for h in [r["heading"] for r in a] + [r["heading"] for r in b if r["heading"] not in ka]:
            ra, rb = ka.get(h), kb.get(h)
            if ra and not rb:
                print(f"  GONE      {h}"); changed += 1
            elif rb and not ra:
                print(f"  NEW       {h}  ({rb['lines']} lines, {rb['bullets']} bullets)")
            elif ra != rb:
                d = lambda k: f"{ra[k]}->{rb[k]}" if ra[k] != rb[k] else str(ra[k])
                print(f"  CHANGED   {h}  lines {d('lines')}  bullets {d('bullets')}  wrap {d('wrap')}")
                changed += 1
        if not changed:
            print("  no pre-existing section changed")
        else:
            print("\n  Any section you did not mean to edit that lost lines or bullets had its tail\n"
                  "  moved under an adjacent heading. Check the boundary you grafted at.")
        return 1 if changed else 0
    print(__doc__.strip().split("\n\n")[1])
    return 2


if __name__ == "__main__":
    sys.exit(main())
