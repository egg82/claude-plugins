#!/usr/bin/env python3
"""Refuse to seal a bundle whose staged copy was made from an OLDER version of its source.

WHY: a repeat bundle inherits the previous bundle's scrubbed copies so the scrub and the cold-read
fixes survive. Whether a copy may be inherited cannot be read off the copy: mtime says "newer"
forever (the copy is stamped when made), and a diff is meaningless because scrubbing changes content
on purpose. So the fact is recorded where it is known — at copy time — as the sha256 of the SOURCE
file, in the bundle's MANIFEST.json. The gate then compares that hash with the source's hash now:

    equal     -> fresh
    different -> STALE: the source moved on; update the staged copy (re-scrub), then `record`
    no record -> UNKNOWN: nothing says what it was copied from; stage it, or record it once checked
    source gone -> STALE: the file it was copied from no longer exists

    freshness-gate.py <bundle> [--claude-root ~/.claude]                   check (run by scrub-sweep.sh)
    freshness-gate.py stage  <bundle> <source> <bundle-path> [--claude-root]  copy file/dir + record
    freshness-gate.py record <bundle> <source> <bundle-path> [--claude-root]  record only, no copy

`record` is for a staged copy you updated by hand to match the current source; running it without
that is how a stale copy gets marked fresh. Only files under hooks/, skills/ and memory/ are checked;
READMEs, FINDINGS and hunks are authored for the bundle and have no source.
"""
import argparse, hashlib, json, pathlib, shutil, sys

TREES = ("hooks/", "skills/", "memory/", "plugins/", "stances/")  # last two: the public marketplace layout
SKIP_PARTS = {"__pycache__", "evals"}
MANIFEST = "MANIFEST.json"


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def source_key(src, root):
    """The source path as stored: relative to the claude root, with a project dir as `*`.

    A project dir name encodes the home path (and so the username), which must not ship.
    """
    rel = src.resolve().relative_to(root).as_posix()
    parts = rel.split("/")
    if parts[0] == "projects" and len(parts) > 2:
        parts[1] = "*"
    return "/".join(parts)


def resolve_source(key, root):
    """Path for a stored key, or None. A `*` must resolve to exactly one file, else None."""
    hits = [p for p in root.glob(key) if p.is_file()] if "*" in key else \
           ([root / key] if (root / key).is_file() else [])
    return hits[0] if len(hits) == 1 else None


def load_manifest(bundle):
    p = bundle / MANIFEST
    return json.loads(p.read_text()) if p.is_file() else {}


def save_manifest(bundle, m):
    (bundle / MANIFEST).write_text(json.dumps(m, indent=1, sort_keys=True) + "\n")


def pin(bundle, root, src, dest, m, copy):
    if copy:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    key = source_key(src, root)
    if resolve_source(key, root) != src.resolve():
        raise SystemExit(f"FAIL: {key} does not resolve back to {src} uniquely — cannot record it")
    m[dest.relative_to(bundle).as_posix()] = {"source": key, "sha256": sha256(src)}


def cmd_pin(a, root, copy):
    bundle = pathlib.Path(a.bundle).expanduser().resolve()
    src = pathlib.Path(a.source).expanduser().resolve()
    dest = bundle / a.dest
    if not src.exists():
        print(f"FAIL: source {src} does not exist"); return 2
    try:
        src.relative_to(root)
    except ValueError:
        print(f"FAIL: source {src} is not under {root}"); return 2
    bundle.mkdir(parents=True, exist_ok=True)
    m = load_manifest(bundle)
    if src.is_dir():
        files = [f for f in sorted(src.rglob("*")) if f.is_file()
                 and not SKIP_PARTS & set(f.relative_to(src).parts) and f.suffix != ".pyc"]
        for f in files:
            pin(bundle, root, f, dest / f.relative_to(src), m, copy)
    else:
        files = [src]
        pin(bundle, root, src, dest, m, copy)
    save_manifest(bundle, m)
    print(f"  {'staged' if copy else 'recorded'} {len(files)} file(s) under {a.dest}")
    return 0


def authored(rel):
    """Marketplace wiring written for the repo itself, so it has no source to be stale against."""
    return ("/.claude-plugin/" in rel or rel.endswith("/hooks/hooks.json")
            or rel in ("stances/README.md", "stances/install.sh", "stances/test-install.sh"))


def check(bundle, root):
    if not bundle.is_dir():
        print(f"FAIL: {bundle} is not a directory"); return 2
    if not root.is_dir():
        print(f"FAIL: {root} is not a directory — cannot hash the sources"); return 2
    m = load_manifest(bundle)
    staged = [sp.relative_to(bundle).as_posix() for sp in sorted(bundle.rglob("*")) if sp.is_file()]
    staged = [r for r in staged if r.startswith(TREES) and not authored(r)]
    if not staged:
        print("  n/a — nothing staged under hooks/, skills/ or memory/")
        return 0
    stale, unknown = [], []
    for rel in staged:
        rec = m.get(rel)
        if not rec:
            unknown.append(rel); continue
        src = resolve_source(rec["source"], root)
        if src is None:
            stale.append(f"{rel}  (source {rec['source']} not found)")
        elif sha256(src) != rec["sha256"]:
            stale.append(f"{rel}  (source {rec['source']} changed since staged)")
    for label, rows, fix in (
            ("STALE", stale, "update the staged copy from the source and re-scrub, then `record` it"),
            ("UNKNOWN — no source hash recorded", unknown, "`stage` it, or `record` it once checked")):
        if rows:
            print(f"  {label}: {len(rows)} file(s) — {fix}:")
            for r in rows[:12]:
                print(f"      {r}")
            if len(rows) > 12:
                print(f"      (+{len(rows) - 12} more not listed)")
    if stale or unknown:
        print(f"\nFAIL: {len(stale)} stale, {len(unknown)} unknown of {len(staged)} staged file(s).")
        return 1
    print(f"  clean — {len(staged)} staged file(s), each source unchanged since it was staged")
    return 0


def main():
    argv = sys.argv[1:]
    ap = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    if argv and argv[0] in ("stage", "record"):
        ap.add_argument("cmd")
        ap.add_argument("bundle"); ap.add_argument("source"); ap.add_argument("dest")
    else:
        ap.add_argument("bundle")
    ap.add_argument("--claude-root", default="~/.claude")
    a = ap.parse_args(argv)
    root = pathlib.Path(a.claude_root).expanduser().resolve()
    if getattr(a, "cmd", None):
        return cmd_pin(a, root, copy=a.cmd == "stage")
    return check(pathlib.Path(a.bundle).expanduser().resolve(), root)


if __name__ == "__main__":
    sys.exit(main())
