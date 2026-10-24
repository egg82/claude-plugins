"""The per-location ledger the held-count gates share: `{file: {kind: count}}`, never a
line number, so a change that fixes one finding and adds another elsewhere fails
instead of netting out. `problems` names each file and kind that is over or under its
held count; `dump` writes the ledger sorted, so `--write` after a merge is
deterministic.

Setup: the gates expect this file in `tools/` and their ledgers in `tools/held/`.
In a repo with no `tools/`, put both beside the tests and change the `sys.path`
line in each gate. Run the repo's own linter on the copies (these are ruff-clean
at 88 columns, Python 3.11+)."""

import json
from pathlib import Path

Ledger = dict[str, dict[str, int]]


def tally(items: list[tuple[str, str]]) -> Ledger:
    """One (file, kind) pair per finding, folded into a ledger."""
    out: Ledger = {}
    for file, kind in items:
        out.setdefault(file, {}).setdefault(kind, 0)
        out[file][kind] += 1
    return out


def problems(found: Ledger, held: Ledger, fix: str, write: str) -> list[str]:
    """Every (file, kind) over its held count, or new, then every one under it: `fix`
    says what to do about the first kind, `write` the command that lowers the second."""
    rows = sorted(
        {(f, k) for led in (found, held) for f, kinds in led.items() for k in kinds}
    )
    out = []
    for f, k in rows:
        n, h = found.get(f, {}).get(k, 0), held.get(f, {}).get(k, 0)
        if n > h:
            out.append(f"{f} {k}: {n}, held {h}; {fix}")
        elif n < h:
            out.append(f"{f} {k}: {n}, held {h}; stale, lower it ({write})")
    return out


def dump(ledger: Ledger) -> str:
    return (
        json.dumps(
            {f: dict(sorted(k.items())) for f, k in sorted(ledger.items())},
            indent=1,
            sort_keys=True,
        )
        + "\n"
    )


def load(path: Path) -> Ledger:
    return json.loads(path.read_text())


def total(ledger: Ledger) -> int:
    return sum(n for kinds in ledger.values() for n in kinds.values())
