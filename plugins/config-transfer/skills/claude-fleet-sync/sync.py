#!/usr/bin/env python3
"""
claude-fleet-sync toolbox — MECHANICAL primitives for mirroring Claude Code config
across a fleet. This script is intentionally NOT an auto-merger of natural-language
content: deciding what a memory/skill file should say, what's a real conflict, and
what should or shouldn't sync is JUDGMENT WORK that the agent does by reading the
files (see SKILL.md). The script only does the parts that are mechanical, tedious, or
error-prone to do by hand:

  ping        establish one SSH ControlMaster per peer; report reachable/skipped
  backup      per-host pre-sync tarball of {skills, settings*.json, */memory}
  inventory   per-host listing of skills/memory/plugins/perms/aliases/toolkits, with
              cross-host DIVERGENCES (same path, different content) called out so the
              agent can read+reconcile them — does NOT pick a winner
  pull        copy specific path(s) from ONE host into the hub (tar over ssh; banner-safe)
  push        copy specific hub path(s) out to peers (default all)
  rsync-tree  union a purely-mechanical tree (plugin cache/marketplaces, toolkit dirs)
              both directions, newest-wins — use ONLY for non-natural-language trees
  jsonmerge   deterministic union of plugin registries + enabledPlugins +
              extraKnownMarketplaces + permissions.allow; preserves host-specific keys
  aliases     union ssh `Host` blocks across the fleet (append-only, never overwrite)
  creds       delegate to creds-sync.sh (systemd-creds; host/TPM-bound, needs root)
  verify      parity table across hosts (skills, memory, plugins, allow rules, settings)

Usage:
  python3 sync.py <command> [--dry-run] [--hosts h1,h2,...] [command args...]
Hosts default to FLEET below; `--hosts` overrides it per run, so you can leave FLEET
as the placeholder and never persist a host list in the file.
Unreachable hosts are skipped with a warning.
Requires: ssh (key auth) + rsync + tar on every host; identical $HOME across hosts.
"""
import hashlib, json, re, shlex, socket, subprocess, sys, tempfile
from datetime import datetime
from pathlib import Path

# PLACEHOLDERS — replace with your own hostnames, or leave them and pass
# `--hosts a,b` on every run (the override applies to every subcommand).
FLEET = [
    "<host-a>",
    "<host-b>",
]

# Top-level $HOME dirs never auto-discovered as toolkits even if a skill references
# them (system/cache/personal dirs). Dotdirs are skipped wholesale.
DENY_TOP = {
    ".claude", ".ssh", ".config", ".cache", ".local", ".gnupg", ".aws", ".kube",
    ".npm", ".cargo", ".rustup", ".terraform.d", ".vscode", ".mozilla", "go",
    "Downloads", "Documents", "Desktop", "Pictures", "Music", "Videos", "tmp",
}

# Skill decision-ledgers: keyed maps of conclusions a skill reached that changed nothing
# in the world (e.g. a curation skill's "reviewed and kept"), so nothing else reconstructs them.
# Union-merged by jsonmerge, NOT rsync-tree'd — newest-mtime-wins would silently drop the
# other host's verdicts. Living under a DENY_TOP dir is what keeps rsync-tree off them.
# Per-skill decision logs worth mirroring. Add your own; these are paths under $HOME.
LEDGERS = []

# Per-host files that live inside synced trees but must never cross hosts: the harness's own
# claude.ai skill-sync state and trash under skills/, and any installer-generated hook whose
# content is tied to that host's binary (add its file name to "names"). Left in, they flag a
# divergence every night — which halts the autonomous run before its mirror — and a push would
# clobber peer state.
PER_HOST = {"dirs": ["synced", ".trash"], "names": []}

# Local plugin marketplace floor (kept so jsonmerge never drops a known-good one).
LOCAL_MARKETPLACE = {
    "<local-marketplace>": {"source": {"source": "directory",
                             "path": str(Path.home() / ".claude/local-marketplaces/<name>")}}
}

HOME = Path.home()
# One shared SSH ControlMaster connection per peer — fast, and friendly to hosts behind an
# auth step that rate-limits logins, where rapid back-to-back logins get dropped. Persists 5 min after use.
CP = str(HOME / ".ssh/cm-%r@%h:%p")
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ControlMaster=auto",
            "-o", f"ControlPath={CP}", "-o", "ControlPersist=300",
            "-o", "ConnectTimeout=10", "-o", "LogLevel=ERROR"]
RSH = "ssh " + " ".join(SSH_OPTS)  # for rsync -e (ControlPath has no spaces here)


def log(*a):
    print("[fleet-sync]", *a, file=sys.stderr, flush=True)


def short(h):
    return h.split(".")[0]


def is_local(host):
    me = {socket.gethostname(), socket.getfqdn()}
    return short(host) in {short(x) for x in me}


def _hooks_to_mirror(host_hooks, hub):
    """Decide what every host's settings.json `hooks` block should become.

    Returns (hooks_or_None, orphans, drifted). `None` means DO NOT TOUCH hooks on any host:
    some host registers a command the hub does not, and mirroring would delete it. Union sync
    never drops content silently, so that case reports and defers to the operator.
    """
    if hub is None:
        return None, [], []
    hooks = host_hooks.get(hub) or {}
    hub_cmds = _hook_cmds(hooks)
    orphans = sorted({c for hk in host_hooks.values() for c in _hook_cmds(hk)
                      if c not in hub_cmds})
    if orphans:
        return None, orphans, []
    return hooks, [], [h for h, hk in host_hooks.items() if hk != hooks]


def _hook_cmds(hooks):
    """The set of hook commands a settings.json `hooks` block actually registers.
    Identity is the command, not the matcher — the same script under two matchers is one
    hook registered two ways, which is drift to correct, not two hooks to keep."""
    out = set()
    for entries in (hooks or {}).values():
        for e in entries or []:
            for hk in e.get("hooks") or []:
                if hk.get("command"):
                    out.add(hk["command"])
    return out


def run(argv, check=True, capture=True, **kw):
    r = subprocess.run(argv, text=True, capture_output=capture, **kw)
    if check and r.returncode != 0:
        raise RuntimeError(f"failed: {' '.join(argv)}\n{r.stderr}")
    return r.stdout or ""


def remote(host, cmd, check=True):
    """Run a shell command on host (local => bash -lc, else ssh over ControlMaster)."""
    if is_local(host):
        return run(["bash", "-lc", cmd], check=check)
    return run(["ssh", *SSH_OPTS, host, cmd], check=check)


def reachable(host):
    if is_local(host):
        return True
    # First contact also establishes the ControlMaster for everything that follows.
    r = subprocess.run(["ssh", *SSH_OPTS, host, "true"], capture_output=True, text=True)
    return r.returncode == 0


def rsync(src, dst, update=False, extra=None, dry=False):
    """src/dst are 'host:path' or local path. Union copy; never deletes."""
    flags = ["-a", "-e", RSH, "--exclude=__pycache__", "--exclude=*.pyc"]
    flags += [f"--exclude=/{d}/" for d in PER_HOST["dirs"]]
    flags += [f"--exclude={n}" for n in PER_HOST["names"]]
    if update:
        flags.append("--update")
    if dry:
        flags.append("-n")
    flags += extra or []
    r = subprocess.run(["rsync", *flags, src, dst], text=True, capture_output=True)
    if r.returncode != 0:
        log(f"  rsync rc={r.returncode} {src} -> {dst}: {r.stderr.strip()[-300:]}")
    return r.returncode == 0


def hub_path(rel):
    # str(Path / rel) strips a trailing slash; rsync needs it preserved so a dir's
    # *contents* (not the dir itself) are copied. Re-append it.
    p = str(HOME / rel)
    return p + "/" if rel.endswith("/") else p


def read_remote_file(host, rel):
    try:
        return remote(host, f"cat ~/{shlex.quote(rel)} 2>/dev/null", check=False)
    except Exception:
        return ""


def write_remote_file(host, rel, text, mode=None):
    if is_local(host):
        p = HOME / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        if mode is not None:
            p.chmod(mode)
        return
    parent = str(Path(rel).parent)
    cmd = f"mkdir -p ~/{shlex.quote(parent)}; cat > ~/{shlex.quote(rel)}"
    if mode is not None:
        cmd += f"; chmod {oct(mode)[2:]} ~/{shlex.quote(rel)}"
    subprocess.run(["ssh", *SSH_OPTS, host, cmd], input=text, text=True, check=True)


# ---------------------------------------------------------------- live-host setup
def resolve_hosts(argv_hosts):
    hosts = argv_hosts or FLEET
    if any("<" in h for h in hosts):
        log("ERROR: FLEET is still the placeholder roster — edit FLEET in sync.py or pass "
            "--hosts a,b (otherwise every host below is unreachable for the wrong reason).")
        sys.exit(1)
    live = [h for h in hosts if reachable(h)]
    skipped = [h for h in hosts if h not in live]
    if not any(is_local(h) for h in live):
        log("ERROR: this machine is not in the host list; run from a fleet member.")
        sys.exit(1)
    if skipped:
        log("WARNING: unreachable, skipping:", ", ".join(skipped))
    return live, skipped


def discover_projects(live):
    projects = set()
    for h in live:
        out = remote(h, "ls -d ~/.claude/projects/*/memory 2>/dev/null || true", check=False)
        for ln in out.split():
            if "/projects/" in ln and ln.endswith("/memory"):
                projects.add(ln.split("/projects/")[1][:-len("/memory")])
    return sorted(projects)


# ------------------------------------------------------- discover toolkit dirs
_HOMEPATH_RE = re.compile(r'(?:~|\$HOME|\$\{HOME\})/([A-Za-z0-9._-]+)')


def discover_extra_dirs(live):
    """$HOME-relative dirs a skill references that really exist and aren't system/git
    dirs (a toolkit dir holding the helpers/creds a skill drives). These are MECHANICAL
    trees (binaries, secrets, helpers) — synced verbatim by rsync-tree, not reconciled
    as natural language.

    A dir that *contains* git working copies is skipped too, not just one that IS a
    repo: a plain dir like ~/src or ~/projects merely holds repos, so the
    is-it-a-repo test passed it through and rsync-tree would have merged 82k files
    of working-tree state across hosts — without --delete, so deletions reverse."""
    found, skipped = set(), set()
    for h in live:
        raw = remote(h, r"grep -rhoE '(~|[$]HOME|[$][{]HOME[}])/[A-Za-z0-9._/-]+' "
                        r"~/.claude/skills 2>/dev/null", check=False)
        cands = set()
        for m in _HOMEPATH_RE.finditer(raw):
            seg = m.group(1)
            if seg.startswith(".") or seg in DENY_TOP:
                continue
            cands.add(seg)
        if not cands:
            continue
        # Keep real toolkit dirs; SKIP git working copies AND dirs that merely hold them
        # (they belong to git, not to sync). depth 2 catches ~/<dir>/<repo>/.git.
        # A skip on ANY host wins: a stub of the dir on a peer (just a logs/ some job made)
        # holds no .git, so judged per host it read as a toolkit and pulled a large set of
        # worktrees from the host where it is one.
        chk = remote(h, "for d in " + " ".join(shlex.quote(c) for c in sorted(cands)) +
                     '; do [ -d "$HOME/$d" ] || continue; '
                     '[ -n "$(find "$HOME/$d" -maxdepth 2 -name .git -print -quit 2>/dev/null)" ] '
                     '&& { echo "SKIP $d"; continue; }; echo "KEEP $d"; done',
                     check=False)
        for verdict, d in (ln.split(" ", 1) for ln in chk.splitlines() if " " in ln):
            (skipped if verdict == "SKIP" else found).add(d)
    return sorted(d + "/" for d in found - skipped)


# ---------------------------------------------------------------- content listing
def host_listing(host, root):
    """{relpath: (mtime_float, md5)} for every file under $HOME/<root> (minus MEMORY.md).
    Used to spot cross-host divergences in natural-language trees so the agent can read
    and reconcile them — NOT to auto-pick a winner."""
    skip = "".join(f" ! -path './{d}/*'" for d in PER_HOST["dirs"])
    skip += "".join(f" ! -name {n}" for n in PER_HOST["names"])
    cmd = (
        f"cd ~/{shlex.quote(root)} 2>/dev/null && "
        r"find . -type f ! -name MEMORY.md ! -path '*/__pycache__/*'" + skip +
        r" -printf '%T@ %p\n' 2>/dev/null | "
        r"while IFS= read -r line; do t=${line%% *}; f=${line#* }; "
        r'h=$(md5sum "$f" 2>/dev/null | cut -c1-32); printf "%s %s %s\n" "$t" "$h" "$f"; done'
    )
    out = remote(host, cmd, check=False)
    listing = {}
    for ln in out.splitlines():
        parts = ln.split(None, 2)
        if len(parts) != 3:
            continue
        mt, h, rel = parts
        try:
            listing[rel.lstrip("./")] = (float(mt), h)
        except ValueError:
            continue
    return listing


def divergences(live, root):
    """List of (rel, {host: (mtime, md5)}) where >1 distinct hash exists across hosts."""
    per = {h: host_listing(h, root) for h in live}
    rels = set().union(*[set(d) for d in per.values()]) if per else set()
    out = []
    for rel in sorted(rels):
        present = {h: per[h][rel] for h in live if rel in per[h]}
        hashes = {v[1] for v in present.values()}
        if len(hashes) > 1:
            out.append((rel, present))
    return out, per


def subset_files(per, live):
    """[(rel, [hosts that HAVE it])] for files present on SOME but not ALL live hosts.
    These are peer-unique files that must be ABSORBED into the hub before a mirror, or
    they'd be lost on the hosts that lack them — the data-loss case the skill guards."""
    if len(live) < 2 or not per:
        return []
    rels = set().union(*[set(d) for d in per.values()])
    out = []
    for rel in sorted(rels):
        have = [h for h in live if rel in per.get(h, {})]
        if len(have) < len(live):
            out.append((rel, have))
    return out


# ---------------------------------------------------------------- index helpers
def merge_index_draft(texts):
    """Line-union of MEMORY.md bullets keyed by link target — a DRAFT only. The agent
    curates hooks, adds bullets for orphan files, and drops stale ones by hand."""
    seen, order = {}, []
    for t in texts:
        for line in t.splitlines():
            s = line.strip()
            if s.startswith("- [") and "](" in s:
                target = s.split("](", 1)[1].split(")", 1)[0]
                if target not in seen:
                    seen[target] = line.rstrip()
                    order.append(target)
    body = "\n".join(seen[t] for t in order)
    return "# Memory Index\n\n" + body + "\n", set(seen)


# ---------------------------------------------------------- ssh Host-block union
def parse_ssh_blocks(text):
    preamble, blocks, order = [], {}, []
    key, cur = None, []
    for line in text.splitlines():
        if line.strip().lower().startswith("host "):
            if key is None:
                preamble = cur
            else:
                blocks[key] = "\n".join(cur)
            key, cur = line.strip(), [line]
            if key not in order:
                order.append(key)
        else:
            cur.append(line)
    if key is None:
        preamble = cur
    else:
        blocks[key] = "\n".join(cur)
    return preamble, blocks, order


# ---------------------------------------------------------------- JSON union
def union_json_map(host_files):
    merged = {}
    for host, rel in host_files:
        txt = read_remote_file(host, rel)
        if not txt.strip():
            continue
        try:
            d = json.loads(txt)
        except Exception:
            continue
        for k, v in d.items():
            merged.setdefault(k, v)
    return merged


def json_quote(s):
    return "'" + s.replace("'", "'\\''") + "'"


# ================================================================= COMMANDS
def cmd_ping(live, skipped, args, dry):
    log("hub:", socket.gethostname())
    for h in live:
        log(f"  reachable: {short(h)}" + ("  (this host)" if is_local(h) else ""))
    for h in skipped:
        log(f"  SKIPPED (unreachable): {short(h)}")


def cmd_backup(live, skipped, args, dry):
    """Per-host pre-sync tarball of config + memory (work-style: back up before writes)."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    rel = f".claude/backups/reconcile-pre-{ts}.tgz"
    for h in live:
        c = ("cd ~/.claude && mkdir -p backups && "
             "shopt -s nullglob 2>/dev/null; "
             f"tar czf ~/{rel} skills settings.json settings.local.json "
             "CLAUDE.md memory projects/*/memory 2>/dev/null; "
             f"ls -lh ~/{rel} 2>/dev/null")
        if dry:
            log(f"  {short(h)}: would write ~/{rel}")
            continue
        out = remote(h, c, check=False).strip()
        log(f"  {short(h)}: {out or 'backup written'}")


def cmd_inventory(live, skipped, args, dry):
    """Hand the agent the facts: what each host has, and where hosts DIVERGE."""
    projects = discover_projects(live)
    extra = discover_extra_dirs(live)
    print("=" * 70)
    print("FLEET INVENTORY  (hub:", socket.gethostname(), ")")
    print("hosts:", ", ".join(short(h) for h in live),
          ("| skipped: " + ", ".join(short(h) for h in skipped)) if skipped else "")
    print("=" * 70)

    # skills divergences (natural-language — agent reconciles)
    print("\n## skills/  (per host: count)")
    for h in live:
        n = remote(h, "ls -d ~/.claude/skills/*/ 2>/dev/null | wc -l", check=False).strip()
        names = remote(h, "ls ~/.claude/skills 2>/dev/null | tr '\\n' ' '", check=False).strip()
        print(f"  {short(h):14} {n:>3}  {names}")
    sk_div, sk_per = divergences(live, ".claude/skills")
    sk_uniq = subset_files(sk_per, live)
    if sk_div:
        print("  ⚠ DIVERGING skill files (READ BOTH, reconcile by hand — do NOT blind-copy):")
        for rel, present in sk_div:
            who = "  ".join(f"{short(h)}@{datetime.fromtimestamp(mt):%Y-%m-%d %H:%M}"
                            for h, (mt, _) in sorted(present.items(), key=lambda x: -x[1][0]))
            print(f"      {rel}\n        {who}")
    if sk_uniq:
        print("  ⚠ skill files NOT on every host (absorb into hub before mirroring):")
        for rel, have in sk_uniq:
            print(f"      {rel}  — only on: {', '.join(short(h) for h in have)}")
    if not (sk_div or sk_uniq):
        print("  (no skill-file divergences or gaps)")

    # memory divergences + index health (natural-language — agent reconciles)
    print("\n## projects/*/memory/  (natural language — YOU reconcile)")
    for proj in projects:
        root = f".claude/projects/{proj}/memory"
        files = set()
        for h in live:
            files |= set(host_listing(h, root))
        idx_texts = [read_remote_file(h, root + "/MEMORY.md") for h in live]
        draft, indexed = merge_index_draft([t for t in idx_texts if t.strip()])
        orphans = sorted(f for f in files if f not in indexed)  # file present, no bullet
        stale = sorted(t for t in indexed if t not in files)    # bullet, no file
        mem_div, mem_per = divergences(live, root)
        mem_uniq = subset_files(mem_per, live)
        print(f"  project {proj}:  {len(files)} memory files, {len(indexed)} index bullets")
        if mem_div:
            print("    ⚠ DIVERGING memory files (read+merge content yourself):")
            for rel, present in mem_div:
                who = "  ".join(f"{short(h)}@{datetime.fromtimestamp(mt):%Y-%m-%d %H:%M}"
                                for h, (mt, _) in sorted(present.items(), key=lambda x: -x[1][0]))
                print(f"        {rel}: {who}")
        if mem_uniq:
            print("    ⚠ memory files NOT on every host (absorb into hub before mirroring):")
            for rel, have in mem_uniq:
                print(f"        {rel}  — only on: {', '.join(short(h) for h in have)}")
        if orphans:
            print("    ⚠ files with NO index bullet (add a curated hook):", ", ".join(orphans))
        if stale:
            print("    ⚠ index bullets with NO file (drop or fix):", ", ".join(stale))
        if not (mem_div or mem_uniq or orphans or stale):
            print("    (index healthy, no divergences or gaps)")

    # path-scoped rules (~/.claude/rules) — prose, same treatment as global memory.
    # Added because this dir postdates the tool: a new rules file was silently never
    # mirrored, so an instruction that exists on the hub simply did not apply anywhere else.
    # hooks are ENFORCEMENT, not prose — a host missing one silently loses the gate,
    # which is worse than a prose divergence because nothing reports it.
    print("\n## ~/.claude/hooks/  (enforcement — a missing hook is a silent gap)")
    hroot = ".claude/hooks"
    hfiles = set()
    for h in live:
        hfiles |= set(host_listing(h, hroot))
    h_div, h_per = divergences(live, hroot)
    h_uniq = subset_files(h_per, live)
    print(f"  hooks: {len(hfiles)} files across the fleet")
    for rel, _ in h_div:
        print(f"    \u26a0 DIVERGING hook: {rel}")
    for rel in sorted(h_uniq):
        print(f"    \u26a0 {rel} NOT on every host — that host has no gate")
    if not (h_div or h_uniq):
        print("    (hooks in parity)")

    print("\n## ~/.claude/rules/  (path-scoped instructions — prose, YOU reconcile)")
    rroot = ".claude/rules"
    rfiles = set()
    for h in live:
        rfiles |= set(host_listing(h, rroot))
    r_div, r_per = divergences(live, rroot)
    r_uniq = subset_files(r_per, live)
    print(f"  rules: {len(rfiles)} files across the fleet")
    for rel, present in r_div:
        print(f"    \u26a0 DIVERGING rule (read+merge yourself): {rel}")
    for rel in sorted(r_uniq):
        print(f"    \u26a0 {rel} NOT on every host (absorb into hub before mirroring)")
    if not (r_div or r_uniq):
        print("    (rules in parity)")

    # global ~/.claude/memory + user CLAUDE.md (natural language — agent reconciles)
    print("\n## global ~/.claude/memory/ + CLAUDE.md  (natural language — YOU reconcile)")
    groot = ".claude/memory"
    gfiles = set()
    for h in live:
        gfiles |= set(host_listing(h, groot))
    g_div, g_per = divergences(live, groot)
    g_uniq = subset_files(g_per, live)
    print(f"  global memory: {len(gfiles)} files across the fleet")
    if g_div:
        print("    ⚠ DIVERGING global memory files (read+merge yourself):")
        for rel, present in g_div:
            who = "  ".join(f"{short(h)}@{datetime.fromtimestamp(mt):%Y-%m-%d %H:%M}"
                            for h, (mt, _) in sorted(present.items(), key=lambda x: -x[1][0]))
            print(f"        {rel}: {who}")
    if g_uniq:
        print("    ⚠ global memory NOT on every host (absorb into hub before mirroring):")
        for rel, have in g_uniq:
            print(f"        {rel}  — only on: {', '.join(short(h) for h in have)}")
    if not (g_div or g_uniq):
        print("    (global memory in parity)")
    # CLAUDE.md is a single-file full mirror (one winner; it @imports the global memory)
    cl = {h: (read_remote_file(h, ".claude/CLAUDE.md") or "") for h in live}
    if len({hashlib.md5(v.encode()).hexdigest() for v in cl.values()}) > 1:
        print("    ⚠ CLAUDE.md DIFFERS across hosts — full-mirror the intended one:")
        for h in live:
            print(f"        {short(h)}: {len(cl[h])} bytes")
    else:
        print("    CLAUDE.md: identical across hosts")

    # plugins / permissions / aliases / toolkits (mechanical — jsonmerge/aliases/rsync-tree)
    print("\n## plugins / permissions  (mechanical — `jsonmerge`)")
    for h in live:
        try:
            ip = json.loads(read_remote_file(h, ".claude/plugins/installed_plugins.json") or "{}")
            np = len(ip.get("plugins", {}))
        except Exception:
            np = "?"
        try:
            s = json.loads(read_remote_file(h, ".claude/settings.json") or "{}")
            ne = len(s.get("enabledPlugins", {}))
        except Exception:
            ne = "?"
        try:
            sl = json.loads(read_remote_file(h, ".claude/settings.local.json") or "{}")
            na = len(sl.get("permissions", {}).get("allow", []))
        except Exception:
            na = "?"
        print(f"  {short(h):14} installed={np}  enabled={ne}  allow-rules={na}")

    print("\n## ssh Host aliases  (mechanical — `aliases`)")
    for h in live:
        _, blocks, order = parse_ssh_blocks(read_remote_file(h, ".ssh/config"))
        print(f"  {short(h):14} {len(order)}: {', '.join(k.split()[1] if len(k.split())>1 else k for k in order)}")

    print("\n## toolkit dirs  (mechanical, verbatim+secrets — `rsync-tree`)")
    print("  " + (", ".join(d.rstrip("/") for d in extra) or "(none discovered)"))
    print("\n(See SKILL.md: reconcile the ⚠ natural-language items by hand, then run the"
          " mechanical commands.)")


def cmd_pull(live, skipped, args, dry):
    """pull <host> <relpath...>  — copy specific path(s) from ONE host into the hub."""
    if len(args) < 2:
        log("usage: pull <host> <relpath...>")
        sys.exit(2)
    host, paths = args[0], args[1:]
    # accept a short name
    host = next((h for h in live if short(h) == short(host)), host)
    if is_local(host):
        log("pull source is the hub itself — nothing to do")
        return
    quoted = " ".join(shlex.quote(p) for p in paths)
    log(f"pull from {short(host)}: {', '.join(paths)}")
    if dry:
        return
    # tar over the ControlMaster connection: binary stdin is banner-immune.
    tar_cmd = ["ssh", *SSH_OPTS, host, f"cd ~ && tar cf - {quoted} 2>/dev/null"]
    p1 = subprocess.Popen(tar_cmd, stdout=subprocess.PIPE)
    subprocess.run(["tar", "xf", "-", "-C", str(HOME)], stdin=p1.stdout, check=True)
    p1.wait()


def cmd_push(live, skipped, args, dry):
    """push <relpath...> [--to h1,h2] — copy hub path(s) out to peers (default all)."""
    to = None
    rest = []
    i = 0
    while i < len(args):
        if args[i] == "--to" and i + 1 < len(args):
            to = args[i + 1].split(","); i += 2
        else:
            rest.append(args[i]); i += 1
    if not rest:
        log("usage: push <relpath...> [--to h1,h2]")
        sys.exit(2)
    targets = [h for h in live if not is_local(h)]
    if to:
        targets = [h for h in targets if short(h) in {short(t) for t in to}]
    failed = False
    for h in targets:
        for rel in rest:
            parent = str(Path(rel).parent)
            remote(h, f"mkdir -p ~/{shlex.quote(parent)}", check=False)
            ok = rsync(hub_path(rel), f"{h}:{rel}", dry=dry)
            failed |= not ok
            log(f"  push {rel} -> {short(h)}" + ("" if ok else "  FAILED") + ("  (dry)" if dry else ""))
    if failed:
        sys.exit(1)


def cmd_rsync_tree(live, skipped, args, dry):
    """rsync-tree <relpath...> — union a MECHANICAL tree both ways (newest-wins).
    With no args, syncs the standard mechanical set: plugin caches/marketplaces,
    local-marketplaces, and discovered toolkit dirs. Never use on skills/ or memory/."""
    peers = [h for h in live if not is_local(h)]
    trees = args
    if not trees:
        trees = [".claude/plugins/cache/", ".claude/plugins/marketplaces/",
                 ".claude/local-marketplaces/"]
        trees += discover_extra_dirs(live)
    log("mechanical trees:", ", ".join(t.rstrip("/") for t in trees))
    # pull union into hub (newest wins), then push hub back out
    failed = []
    for h in peers:
        for t in trees:
            Path(hub_path(t if t.endswith("/") else t + "/")).mkdir(parents=True, exist_ok=True)
            if not rsync(f"{h}:{t}", hub_path(t), update=True, dry=dry):
                failed.append(f"{short(h)}:{t} -> hub")
    for h in peers:
        for t in trees:
            remote(h, f"mkdir -p ~/{shlex.quote(t.rstrip('/'))}", check=False)
            if not rsync(hub_path(t), f"{h}:{t}", dry=dry):
                failed.append(f"hub -> {short(h)}:{t}")
    if failed:
        log("rsync-tree FAILED (partial copy):", ", ".join(failed))
        sys.exit(1)
    log("rsync-tree done" + (" (dry)" if dry else ""))


def cmd_jsonmerge(live, skipped, args, dry):
    """Deterministic union of plugin registries + enabledPlugins + extraKnownMarketplaces
    + permissions.allow + skill decision-ledgers; host-specific settings keys (theme, ...)
    are preserved."""
    inst_plugins = {}
    for h in live:
        try:
            inst_plugins.update(json.loads(
                read_remote_file(h, ".claude/plugins/installed_plugins.json")).get("plugins", {}))
        except Exception:
            pass
    installed = {"version": 2, "plugins": inst_plugins}
    known_mkts = union_json_map([(h, ".claude/plugins/known_marketplaces.json") for h in live])

    enabled, extra_mkts = {}, dict(LOCAL_MARKETPLACE)
    host_hooks = {}
    for h in live:
        try:
            s = json.loads(read_remote_file(h, ".claude/settings.json") or "{}")
        except Exception:
            s = {}
        enabled.update({k: True for k in s.get("enabledPlugins", {})})
        extra_mkts.update(s.get("extraKnownMarketplaces", {}))
        host_hooks[h] = s.get("hooks") or {}
    enabled.update({k: True for k in inst_plugins})

    # Hook REGISTRATION, which is the half that does not travel with the hook script. `push
    # .claude/hooks/` copies the file; without this a host holds the script and never runs it,
    # and an unarmed gate is indistinguishable from a gate that found nothing.
    #
    # Mirrored from the hub, not unioned entry-by-entry: two hosts registering the same command
    # under different matchers (`Write|Edit` vs `Write|Edit|MultiEdit|NotebookEdit`) would both
    # survive a union, and the hook would then fire twice on every matching write. A union is
    # the wrong shape for a key whose entries are not independent.
    hub = next((h for h in live if is_local(h)), None)
    hooks, orphans, drifted = _hooks_to_mirror(host_hooks, hub)
    if orphans:
        log("⚠ hooks NOT mirrored — registered on a peer but absent from the hub:")
        for c in orphans:
            log(f"    {c}")
        log("    add it to the hub's settings.json (or remove it there) and re-run jsonmerge")
    else:
        drifted = [short(h) for h in drifted]
        log(f"hooks: {len(_hook_cmds(hooks))} registered command(s) from hub"
            + (f" | correcting: {', '.join(drifted)}" if drifted else " | all hosts already agree"))

    allow = []
    for h in live:
        try:
            s = json.loads(read_remote_file(h, ".claude/settings.local.json") or "{}")
        except Exception:
            s = {}
        for a in s.get("permissions", {}).get("allow", []):
            if a not in allow:
                allow.append(a)
    log(f"plugins: {len(inst_plugins)} | enabled: {len(enabled)} | allow rules: {len(allow)}")
    ledgers = {}
    for rel in LEDGERS:
        merged = union_json_map([(h, rel) for h in live])
        if merged:
            ledgers[rel] = merged
            log(f"ledger {rel}: {len(merged)} entries across {len(live)} host(s)")

    if dry:
        log("(dry) would write registries + ledgers + apply settings on every host")
        return

    Path(hub_path(".claude/plugins/installed_plugins.json")).write_text(
        json.dumps(installed, indent=2) + "\n")
    if known_mkts:
        Path(hub_path(".claude/plugins/known_marketplaces.json")).write_text(
            json.dumps(known_mkts, indent=2) + "\n")

    bundle = {"enabledPlugins": enabled, "extraKnownMarketplaces": extra_mkts, "allow": allow,
              "hooks": hooks}
    for h in live:
        if not is_local(h):
            rsync(hub_path(".claude/plugins/installed_plugins.json"),
                  f"{h}:.claude/plugins/installed_plugins.json")
            if known_mkts:
                rsync(hub_path(".claude/plugins/known_marketplaces.json"),
                      f"{h}:.claude/plugins/known_marketplaces.json")
        apply_settings(h, bundle)
    for rel, merged in ledgers.items():
        text = json.dumps(merged, indent=2, sort_keys=True) + "\n"
        for h in live:
            write_remote_file(h, rel, text)
    log("jsonmerge applied on all hosts")


def apply_settings(host, bundle):
    payload = json.dumps(bundle)
    script = (
        "import json,sys,pathlib;"
        "b=json.loads(sys.stdin.read());"
        "base=pathlib.Path.home()/'.claude';"
        "sp=base/'settings.json';"
        "s=json.loads(sp.read_text()) if sp.exists() else {};"
        # A host-local opt-out (explicit False) WINS over the fleet union. Without this the
        # union -- built as {k: True for every key seen anywhere} -- re-enables a plugin that a
        # host deliberately disabled, e.g. a GUI-only plugin on the headless builder whose hook
        # then fails on every event. Absent keys still get added, so new plugins travel normally.
        "ep=s.setdefault('enabledPlugins',{});"
        "[ep.__setitem__(k,v) for k,v in b['enabledPlugins'].items() if ep.get(k) is not False];"
        "km=s.setdefault('extraKnownMarketplaces',{});km.update(b['extraKnownMarketplaces']);"
        # None means the caller found a host-only hook and refused to mirror; leave hooks alone.
        "hk=b.get('hooks');"
        "s.update({'hooks':hk}) if hk is not None else None;"
        "sp.write_text(json.dumps(s,indent=2)+chr(10));"
        "lp=base/'settings.local.json';"
        "l=json.loads(lp.read_text()) if lp.exists() else {};"
        "al=l.setdefault('permissions',{}).setdefault('allow',[]);"
        "[al.append(x) for x in b['allow'] if x not in al];"
        "lp.write_text(json.dumps(l,indent=2)+chr(10))"
    )
    if is_local(host):
        subprocess.run(["python3", "-c", script], input=payload, text=True, check=True)
    else:
        subprocess.run(["ssh", *SSH_OPTS, host, "python3 -c " + json_quote(script)],
                       input=payload, text=True, check=True)


def cmd_aliases(live, skipped, args, dry):
    """Union all ssh `Host` blocks across the fleet; append any a host is missing.
    Never overwrites a host's own version of a block or its global preamble."""
    union, union_order = {}, []
    for h in live:
        _, blocks, order = parse_ssh_blocks(read_remote_file(h, ".ssh/config"))
        for k in order:
            if k not in union:
                union[k] = blocks[k]
                union_order.append(k)
    log(f"ssh aliases in fleet union: {len(union_order)}")
    for h in live:
        txt = read_remote_file(h, ".ssh/config")
        _, blocks, _ = parse_ssh_blocks(txt)
        missing = [k for k in union_order if k not in blocks]
        if not missing:
            continue
        if dry:
            log(f"  {short(h)}: would add {len(missing)}: {', '.join(missing)}")
            continue
        addition = "\n\n".join(union[k].rstrip() for k in missing)
        new_text = (txt.rstrip() + "\n\n" + addition + "\n") if txt.strip() else addition + "\n"
        write_remote_file(h, ".ssh/config", new_text, mode=0o600)
        log(f"  {short(h)}: added {len(missing)}: {', '.join(missing)}")


def cmd_creds(live, skipped, args, dry):
    script = str(Path(__file__).resolve().parent / "creds-sync.sh")
    argv = ["bash", script] + ([] if dry else ["--apply"]) + list(live)
    log("creds-sync.sh" + (" (dry-run)" if dry else " --apply"))
    subprocess.run(argv, check=False)


# One `find` per host, globally sorted. `__pycache__` is excluded: .pyc files are legitimately
# per-host build artifacts and every host has different ones, so leaving them in makes this report
# permanently noisy — the cry-wolf failure.
_LISTING = (
    "cd ~ && { find .claude/skills .claude/hooks .claude/memory .claude/rules -type f 2>/dev/null; "
    "find .claude/projects -path '*/memory/*' -type f 2>/dev/null; "
    "[ -f .claude/CLAUDE.md ] && echo .claude/CLAUDE.md; } "
    "| grep -v __pycache__ "
    + "".join(f"| grep -v '^.claude/skills/{d}/' " for d in PER_HOST["dirs"])
    + "".join(f"| grep -v '/{n}$' " for n in PER_HOST["names"])
    + "| LC_ALL=C sort -u"
)


def check_file_sets(live):
    """Compare the SET of synced files across hosts, not just the counts.

    `push` is a union copy and never deletes, so a file removed or renamed on one host is not
    removed anywhere else — and the next absorb resurrects it onto the host that deleted it. The
    counts in the parity table cannot see this: a deletion on one host and an addition on another
    net out to the same number, and a rename shows up as no change at all. A count is a proxy for
    the set, and this is the case where the proxy is wrong.

    Reports both directions because they need opposite fixes: a peer-only file is a ZOMBIE (delete
    it on every host in one pass, or it comes back), while a hub-only file is a PUSH GAP (re-push)."""
    listings = {}
    for h in live:
        out = remote(h, _LISTING, check=False) or ""
        listings[h] = set(out.split())
    if len(listings) < 2:
        print("\n  file sets: only one host reachable — UNCHECKED, not clean")
        return
    hub = next((h for h in live if is_local(h)), live[0])
    problems = 0
    for h in [h for h in live if h != hub]:
        zombies = sorted(listings[h] - listings[hub])
        gaps = sorted(listings[hub] - listings[h])
        for rel in zombies[:10]:
            print(f"  ZOMBIE  on {short(h)} but not {short(hub)}: {rel}")
        if len(zombies) > 10:
            print(f"          (+{len(zombies) - 10} more)")
        for rel in gaps[:10]:
            print(f"  GAP     on {short(hub)} but not {short(h)}: {rel}")
        if len(gaps) > 10:
            print(f"          (+{len(gaps) - 10} more)")
        problems += len(zombies) + len(gaps)
    if problems:
        print(f"\n  ⚠ {problems} file-set difference(s). A ZOMBIE was deleted somewhere and will be "
              f"resurrected by the next absorb — delete it on EVERY host in one pass. A GAP just "
              f"needs a re-push.")
    else:
        n = len(listings[hub])
        print(f"\n  ✓ file sets identical across hosts ({n} synced files) — no zombies, no gaps")


def cmd_verify(live, skipped, args, dry):
    """Parity table: counts must match across hosts; settings must parse."""
    projects = discover_projects(live)
    rows = []
    for h in live:
        sk = remote(h, "ls -d ~/.claude/skills/*/ 2>/dev/null | wc -l", check=False).strip()
        mem = remote(h, "find ~/.claude/projects/*/memory -name '*.md' ! -name MEMORY.md "
                        "2>/dev/null | wc -l", check=False).strip()
        try:
            ip = json.loads(read_remote_file(h, ".claude/plugins/installed_plugins.json") or "{}")
            pl = len(ip.get("plugins", {}))
        except Exception:
            pl = "?"
        try:
            sl = json.loads(read_remote_file(h, ".claude/settings.local.json") or "{}")
            al = len(sl.get("permissions", {}).get("allow", []))
        except Exception:
            al = "ERR"
        try:
            json.loads(read_remote_file(h, ".claude/settings.json") or "{}")
            sj = "ok"
        except Exception:
            sj = "PARSE-ERR"
        gm = remote(h, "find ~/.claude/memory -maxdepth 1 -name '*.md' 2>/dev/null | wc -l",
                    check=False).strip()
        cl = hashlib.md5((read_remote_file(h, ".claude/CLAUDE.md") or "").encode()).hexdigest()
        rows.append((short(h), sk, mem, gm, pl, al, sj, cl))
    print(f"\n{'host':14} {'skills':>7} {'memory':>7} {'gmem':>6} {'plugins':>8} {'allow':>6} {'settings':>9}")
    print("-" * 63)
    for r in rows:
        print(f"{r[0]:14} {r[1]:>7} {r[2]:>7} {str(r[3]):>6} {str(r[4]):>8} {str(r[5]):>6} {r[6]:>9}")

    def col(i):
        return {r[i] for r in rows}
    mism = [name for i, name in [(1, "skills"), (2, "memory"), (3, "gmem"), (4, "plugins"), (5, "allow")]
            if len(col(i)) > 1]
    if len({r[7] for r in rows}) > 1:
        mism.append("CLAUDE.md")
    if mism:
        print("\n⚠ MISMATCH across hosts:", ", ".join(mism),
              "— reconcile (some may be legit host-specific; check inventory).")
    else:
        print("\n✓ all hosts agree on skills / memory / gmem / plugins / allow / CLAUDE.md")
    check_file_sets(live)
    if skipped:
        print("note: did not include unreachable host(s):", ", ".join(short(h) for h in skipped))


COMMANDS = {
    "ping": cmd_ping, "backup": cmd_backup, "inventory": cmd_inventory,
    "pull": cmd_pull, "push": cmd_push, "rsync-tree": cmd_rsync_tree,
    "jsonmerge": cmd_jsonmerge, "aliases": cmd_aliases, "creds": cmd_creds,
    "verify": cmd_verify,
}


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        print("commands:", ", ".join(COMMANDS))
        return
    cmd = argv[0]
    if cmd not in COMMANDS:
        log(f"unknown command: {cmd}\ncommands: {', '.join(COMMANDS)}")
        sys.exit(2)
    rest = argv[1:]
    dry = "--dry-run" in rest
    rest = [a for a in rest if a != "--dry-run"]
    hosts = None
    if "--hosts" in rest:
        i = rest.index("--hosts")
        hosts = rest[i + 1].split(",")
        del rest[i:i + 2]
    if dry:
        log("DRY RUN — no writes, transfers simulated")
    live, skipped = resolve_hosts(hosts)
    peers = [h for h in live if not is_local(h)]
    log(f"{cmd}: hub={socket.gethostname()} peers={', '.join(short(p) for p in peers) or '(none)'}")
    COMMANDS[cmd](live, skipped, rest, dry)


if __name__ == "__main__":
    main()
