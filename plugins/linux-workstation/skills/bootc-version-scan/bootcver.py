#!/usr/bin/env python3
"""Deterministic I/O for the bootc-version-scan skill (pinned-dependency drift).

  sync    ensure each configured repo is on its default branch and ff-pull (skips a dirty repo)
  scan    extract the PINNED versions from those repos as JSON (the LLM checks each upstream)
  notify  POST a message to a webhook (URL from $PINSCAN_WEBHOOK)

The LLM does the judgment: resolve each pin's upstream, fetch the latest, compare, decide what's
worth flagging, then call `notify`. `scan` only extracts — it never decides what's outdated.

Configuration (all optional except the repos):
  --repo NAME=PATH            repeatable; overrides REPOS entirely
  $PINSCAN_REPOS              same thing as one string: "images=~/a,provisioning=~/b"
  $PINSCAN_BRANCH             default branch to sync to (default: main)
  $PINSCAN_INTERNAL_REGISTRIES  comma-separated registry hosts to IGNORE as base images
                              (images you build yourself have no upstream to check)
  $PINSCAN_WEBHOOK            webhook URL for `notify`
  $PINSCAN_WEBHOOK_FIELD      JSON field the webhook expects (default: text; some chat
                              webhooks want "content" instead)
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

# PLACEHOLDERS — point these at your own checkouts, or set $PINSCAN_REPOS / pass --repo.
# The names are arbitrary labels used in the output; the paths are what matters.
REPOS = {
    "images": os.path.expanduser("~/<image-repo>"),
    "provisioning": os.path.expanduser("~/<provisioning-repo>"),
}

BRANCH = os.environ.get("PINSCAN_BRANCH", "main")
INTERNAL_REGISTRIES = [r.strip() for r in
                       os.environ.get("PINSCAN_INTERNAL_REGISTRIES", "").split(",") if r.strip()]


def load_repos(pairs):
    """--repo NAME=PATH (repeatable) > $PINSCAN_REPOS > the REPOS placeholders above."""
    spec = list(pairs or [])
    if not spec and os.environ.get("PINSCAN_REPOS"):
        spec = [s for s in os.environ["PINSCAN_REPOS"].split(",") if s.strip()]
    if not spec:
        return
    REPOS.clear()
    for item in spec:
        if "=" not in item:
            sys.exit(f"--repo expects NAME=PATH, got: {item}")
        name, path = item.split("=", 1)
        REPOS[name.strip()] = os.path.expanduser(path.strip())


def check_configured():
    bad = [f"{n}={p}" for n, p in REPOS.items() if "<" in p or not os.path.isdir(p)]
    if len(bad) == len(REPOS):
        sys.exit("no usable repos configured — pass --repo NAME=PATH or set $PINSCAN_REPOS "
                 f"(current: {', '.join(bad) or 'none'})")


# ---------------------------------------------------------------- git hygiene
def git(repo, *args, check=True):
    return subprocess.run(["git", "-C", repo, *args], text=True,
                          capture_output=True, check=check)


def cmd_sync():
    check_configured()
    for name, path in REPOS.items():
        if not os.path.isdir(os.path.join(path, ".git")):
            print(f"[sync] {name}: MISSING at {path}", file=sys.stderr)
            continue
        branch = git(path, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        dirty = bool(git(path, "status", "--porcelain").stdout.strip())
        if dirty:
            print(f"[sync] {name}: on {branch}, DIRTY — leaving as-is (won't pull over local changes)")
            continue
        if branch != BRANCH:
            git(path, "checkout", BRANCH)
            print(f"[sync] {name}: switched {branch} -> {BRANCH}")
        out = git(path, "pull", "--ff-only", check=False)
        tail = (out.stdout + out.stderr).strip().splitlines()[-1:] or [""]
        if out.returncode != 0:
            # Don't let this pass as an ordinary line: a failed pull leaves the scan
            # reading a stale checkout, which reports identically to an up-to-date one.
            print(f"[sync] {name}: PULL FAILED — scanning a STALE checkout: {tail[0]}",
                  file=sys.stderr)
        else:
            print(f"[sync] {name}: {BRANCH}, pull: {tail[0]}")


# ---------------------------------------------------------------- pin extraction
ARG_RE = re.compile(r'^\s*ARG\s+([A-Z0-9_]*(?:VERSION|VER))\s*=\s*"?([^"\s]+)"?', re.M)
GH_RE = re.compile(r'github\.com/([\w.-]+/[\w.-]+)')
FROM_RE = re.compile(r'^\s*FROM\s+(\S+)', re.M | re.I)
TEMPLATED = re.compile(r'(\$\{|__[A-Z0-9_]+__)')   # a tag filled in at build time


def _is_containerfile(fn):
    low = fn.lower()
    return low.startswith("containerfile") or low.startswith("dockerfile")


def scan_containerfiles():
    """Every Containerfile/Dockerfile in every configured repo: base-image refs and
    ARG *_VERSION pins."""
    pins = []
    for repo_name, root in REPOS.items():
        if not os.path.isdir(root):
            continue
        for dirpath, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d != ".git"]
            for fn in files:
                if not _is_containerfile(fn):
                    continue
                fp = os.path.join(dirpath, fn)
                try:
                    text = open(fp, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                rel = f"{repo_name}:{os.path.relpath(fp, root)}"
                gh_repos = sorted(set(GH_RE.findall(text)))
                # base images: external registries only. Skip build-time-templated tags,
                # floating :latest, stage aliases, and any registry you publish to yourself
                # (an image you build has no upstream release to compare against).
                for ref in FROM_RE.findall(text):
                    if TEMPLATED.search(ref) or ref.endswith(":latest") or " AS " in ref:
                        continue
                    host = ref.split("/")[0]
                    if any(reg and reg in ref for reg in INTERNAL_REGISTRIES) or host in INTERNAL_REGISTRIES:
                        continue
                    if ":" in ref.rsplit("/", 1)[-1]:
                        pins.append({"kind": "base-image", "file": rel, "ref": ref})
                # ARG *_VERSION pins (LLM maps each to one of gh_repos via the download URL)
                for name, ver in ARG_RE.findall(text):
                    if ver in ("HEAD", "latest", "main") or TEMPLATED.search(ver):
                        continue  # tracks-latest or build-time arg: nothing to check
                    kind = "kernel" if "KERNEL" in name else "github-or-other"
                    pins.append({"kind": kind, "file": rel, "name": name, "current": ver,
                                 "github_candidates": gh_repos})
    return pins


def scan_requirements():
    """Ansible Galaxy `requirements.yml` at the root of any configured repo."""
    pins = []
    for repo_name, root in REPOS.items():
        fp = os.path.join(root, "requirements.yml")
        if not os.path.exists(fp):
            continue
        section = None
        start = len(pins)
        for line in open(fp, encoding="utf-8", errors="replace"):
            s = line.strip()
            if s.startswith("collections:"):
                section = "galaxy-collection"
            elif s.startswith("roles:"):
                section = "galaxy-role"
            elif s.startswith("- name:") and section:
                name = s.split(":", 1)[1].strip().strip('"')
                pins.append({"kind": section, "file": f"{repo_name}:requirements.yml",
                             "name": name, "current": None})
            elif s.startswith("version:") and len(pins) > start and pins[-1].get("current") is None:
                pins[-1]["current"] = s.split(":", 1)[1].strip().strip('"')
    return pins


def scan_role_vars():
    """`<tool>_version:` pins in Ansible role vars files (roles/*/vars/*.yml)."""
    pins = []
    vre = re.compile(r'^\s*([\w]+)_version:\s*"?([^"\s]+)"?', re.M)
    for repo_name, root in REPOS.items():
        rroot = os.path.join(root, "roles")
        if not os.path.isdir(rroot):
            continue
        for dirpath, _, files in os.walk(rroot):
            for fn in files:
                if not fn.endswith((".yaml", ".yml")) or "vars" not in dirpath:
                    continue
                fp = os.path.join(dirpath, fn)
                rel = f"{repo_name}:{os.path.relpath(fp, root)}"
                for name, ver in vre.findall(open(fp, encoding="utf-8", errors="replace").read()):
                    if ver in ("HEAD", "latest", "main"):
                        continue  # tracks-latest, nothing to check
                    pins.append({"kind": "github-or-other", "file": rel,
                                 "name": f"{name}_version", "current": ver})
    return pins


def cmd_scan():
    check_configured()
    # Report an absent repo, the way cmd_sync() does. Without this a scan over a repo that is not
    # on disk returns empty results and exits 0, which renders identically to "scanned it,
    # everything is current".
    missing = [name for name, path in REPOS.items() if not os.path.isdir(os.path.join(path, ".git"))]
    for name in missing:
        print(f"[scan] {name}: MISSING at {REPOS[name]} — NOT scanned; this is not 'up to date'",
              file=sys.stderr)
    out = {"containerfiles": scan_containerfiles(),
           "requirements": scan_requirements(),
           "role_vars": scan_role_vars()}
    if missing:
        # In the payload too, not only stderr: a consumer of the JSON sees stdout only.
        out["missing_repos"] = missing
    print(json.dumps(out, indent=2))


# ---------------------------------------------------------------- notify
def cmd_notify(message):
    url = os.environ.get("PINSCAN_WEBHOOK", "").strip()
    field = os.environ.get("PINSCAN_WEBHOOK_FIELD", "text")
    if not url:
        print("[notify] no webhook configured (set $PINSCAN_WEBHOOK) — message NOT sent:\n"
              + message, file=sys.stderr)
        sys.exit(3)
    data = json.dumps({field: message[:1900]}).encode()
    # Many chat webhooks sit behind a CDN/WAF that 403s the default Python-urllib
    # User-Agent, so send an explicit one.
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json", "User-Agent": "pin-version-scan/1.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        print(f"[notify] webhook {resp.status}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", action="append", metavar="NAME=PATH",
                   help="repo to scan (repeatable); overrides $PINSCAN_REPOS and the defaults")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("sync")
    sub.add_parser("scan")
    n = sub.add_parser("notify")
    n.add_argument("message")
    args = p.parse_args()
    load_repos(args.repo)
    {"sync": lambda: cmd_sync(), "scan": lambda: cmd_scan(),
     "notify": lambda: cmd_notify(args.message)}[args.cmd]()


if __name__ == "__main__":
    main()
