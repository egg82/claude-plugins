#!/usr/bin/env python3
"""Report drift in a Claude Code config + docs setup. Reports only; changes nothing.

  hygiene.py memory [--memory-root DIR]   dangling bullets, orphan files, index size, fat files,
                                          plus the always-on prefs dir (import wiring + total weight)
  hygiene.py skills [--skills DIR]        SKILL.md content that goes stale independently
  hygiene.py probes [--memory-root DIR]   run each memory's `check:` (needs HYGIENE_RUN_PROBES=1)
  hygiene.py refs   [--skills DIR]        [[wiki-links]] in skills pointing at nothing
  hygiene.py imports [--memory-root DIR]  always-on prefs only: import wiring + session weight
  hygiene.py docs   REPO [REPO ...]       docs whose directory changed after they did
  hygiene.py doccontent REPO [REPO ...]   docs carrying content that decays, at any age
  hygiene.py hooks  [--memory-root DIR]   a hook present on disk but not registered, or vice versa
  hygiene.py numbering [--skills DIR]     duplicate section numbers — the grafted-section signature
  hygiene.py testiso [--memory-root DIR]  a test suite mutating the real $HOME it is supposed to test
  hygiene.py all    [REPO ...]            every periodic check (docs/doccontent need REPOs; says
                                          so if absent). NOT shareable — see below.
  hygiene.py shareable --share-root DIR [--names a,b]
                                          refuse-to-ship gates for a copy LEAVING this machine (a
                                          plugin, a bundle). Deliberately outside `all`: it is a
                                          pre-publish gate needing a target, not a periodic check.

A missing store is reported as UNCHECKED, never as clean — that distinction is the whole point.
"""
import argparse, json, re, stat, subprocess, sys, pathlib

HOME = pathlib.Path.home()
DEF_MEM = HOME / ".claude/projects"
DEF_SKILLS = HOME / ".claude/skills"
DATE = re.compile(r'20[0-9]{2}-[01][0-9]-[0-3][0-9]')
IPV4 = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
PRIVATE = re.compile(r'^(?:10\.|127\.|0\.|255\.|192\.168\.|172\.(?:1[6-9]|2[0-9]|3[01])\.)')
MAC = re.compile(r'\b(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b')
# An enumerated noun list cannot fire on a noun nobody listed, so a zero here describes the
# regex as much as the file — treat a clean result as weak evidence. Widened after a narrower
# version scored a skill 0 while it carried '4,600 lines', '11,000 lines' and '471 commits'.
COUNT = re.compile(r'\b[0-9]{2,}\s+(?:items|records|entries|files|rows|objects|hosts|domains|pages|lines|commits|tests|rules|skills|memories)\b', re.I)
FENCE = re.compile(r'^\s*```')

def _prose(text):
    """Yield (lineno, line_without_inline_code, raw_line) for lines outside fenced code blocks."""
    infence = False
    for i, line in enumerate(text.split('\n'), 1):
        if FENCE.match(line):
            infence = not infence
            continue
        if not infence:
            # A figure inside `backticks` is being DISCUSSED, not asserted — stripping inline code is
            # why this check does not flag its own documentation of a bad count. But an ADDRESS is
            # normally written in backticks, so yield both and let each caller score on the right one.
            yield i, re.sub(r'`[^`]*`', '', line), line

def check_memory(root):
    print("== memory ==")
    bad = 0
    if not pathlib.Path(root).is_dir():
        print(f"  clean — nothing to check ({root} absent)")   # no project memory yet is not a defect
        return 0
    for proj in sorted(pathlib.Path(root).glob("*/memory")):
        idx = proj / "MEMORY.md"
        if not idx.exists():
            continue
        files = {p.name for p in proj.glob("*.md")} - {"MEMORY.md"}
        linked = set(re.findall(r'\]\(([^)]+\.md)\)', idx.read_text(errors="replace")))
        dangling, orphan = linked - files, files - linked
        size = idx.stat().st_size
        fat = sorted(((p.stat().st_size, p.name) for p in proj.glob("*.md")
                      if p.stat().st_size > 8000 and p.name != "MEMORY.md"), reverse=True)
        flags = []
        if dangling: flags.append(f"{len(dangling)} dangling: {sorted(dangling)[:4]}")
        if orphan:   flags.append(f"{len(orphan)} orphan: {sorted(orphan)[:4]}")
        if size > 12000: flags.append(f"index {size}B (>12K — route new facts elsewhere)")
        if fat:      flags.append(f"{len(fat)} files >8K, largest {fat[0][1]} @ {fat[0][0]}B")
        if flags:
            bad += 1
            print(f"  {proj.parent.name}: " + "; ".join(flags))
    bad += check_prefs(pathlib.Path(root).parent / "memory")
    if not bad:
        print("  clean")
    return bad


def check_prefs(prefs):
    """The always-on prefs dir (~/.claude/memory) has no index — it is wired by @imports.

    Auditing it by index shape would report clean forever, which is the null-result trap:
    the checker cannot see the store the setup depends on most. What matters here instead is
    whether each file is actually LOADED (an un-imported pref is a dead button), whether an
    import points at nothing, and total always-on weight — imports expand inline at session
    start and count in full, so every byte is paid on every session.
    """
    if not prefs.is_dir():
        print(f"  clean — nothing to check ({prefs} absent)")   # no always-on prefs dir: nothing to audit
        return 0
    claude_md = prefs.parent / "CLAUDE.md"
    if not claude_md.exists():
        print(f"  {prefs.name}: no CLAUDE.md beside it — prefs are present but nothing imports them")
        return 1
    text = claude_md.read_text(errors="replace")
    # Resolve each @import: matching on basename alone lets a same-named file in another directory
    # count as loading this pref, so a dead button reads as wired.
    imported = set()
    for m in re.findall(r'^@(\S+\.md)\s*$', text, re.M):
        q = pathlib.Path(m.replace("~", str(pathlib.Path.home()), 1)) if m.startswith("~") \
            else (claude_md.parent / m)
        try:
            q = q.resolve()
        except OSError:
            pass
        if q.parent == prefs.resolve():
            imported.add(q.name)
    present = {p.name for p in prefs.glob("*.md")}
    flags = []
    unloaded = present - imported
    missing = imported - present

    # BODY bytes, not file bytes. The `---` frontmatter block is stripped when a pref is expanded
    # into context — verified by reading how these appear in a live session — so counting whole
    # files overstated the real resident cost by ~9.5% here. A checker that overstates gets
    # discounted, which costs more than the bytes it was trying to flag.
    def body_bytes(p):
        s = p.read_text(errors="replace")
        m = re.match(r"^---\n.*?\n---\n", s, re.S)
        return len(s) - (len(m.group(0)) if m else 0)

    total = sum(body_bytes(p) for p in prefs.glob("*.md") if p.name in imported)

    # The skill ROSTER is the other half of the always-on budget and nothing was counting it: every
    # skill's name + description sits in the system prompt on every request. Measured here it was
    # over half the size of the pref tier. A description's length is functional, but the listing has
    # a size budget: over it, the harness keeps names and drops descriptions from the least-used
    # skills, so one bloated description costs OTHER skills their triggering. Flagged on growth
    # against baseline.txt's second line, never against an absolute size.
    roster = 0
    skills_root = prefs.parent / "skills"
    for sp in skills_root.glob("*/SKILL.md") if skills_root.is_dir() else []:
        m = re.search(r"^---\n(.*?)\n---", sp.read_text(errors="replace")[:6000], re.S)
        if not m:
            continue
        d = re.search(r"^description:\s*(.*?)(?=\n[a-z_]+:|\Z)", m.group(1), re.S | re.M)
        if d:
            roster += len(" ".join(d.group(1).split()))

    print(f"  always-on: {len(imported)} imports, {total}B of pref bodies + {roster}B of skill "
          f"descriptions = {total + roster}B resident every request")
    if unloaded: flags.append(f"{len(unloaded)} never imported (dead weight): {sorted(unloaded)[:4]}")
    if missing:  flags.append(f"{len(missing)} imported but absent: {sorted(missing)[:4]}")

    # The third resident front, previously uncounted: each project's memory INDEX loads in full on
    # every request in that project. It is deliberately NOT added to `total`: the baseline delta below
    # compares against a recorded pref-body figure, so folding a new term in would make the ratchet
    # fire on your own change to the definition and read as growth that never happened.
    idx = []
    proj = prefs.parent / "projects"
    for ix in sorted(proj.glob("*/memory/MEMORY.md")) if proj.is_dir() else []:
        try:
            t = ix.read_text(errors="replace")
        except OSError:
            idx.append((ix.parent.parent.name, -1, -1))   # unreadable != absent, so say which
            continue
        idx.append((ix.parent.parent.name, len(t), t.count("\n") + 1))
    if idx:
        big = max(idx, key=lambda r: r[1])
        print(f"  always-on: + a project memory index, resident in that project only - "
              f"{len(idx)} indexes, largest {big[0]} at {big[1]}B / {big[2]} lines")
        # MEMORY.md loads only its first 200 lines and first 25KB; warn at 80% so there is room to move entries OUT
        for name, b, ln in idx:
            if b < 0:
                flags.append(f"project index {name} is unreadable - UNCHECKED, not clean")
            elif b > 20000 or ln > 160:
                flags.append(f"project index {name} at {b}B / {ln} lines is past 80% of the "
                             f"25KB / 200-line load cap - move entries out, do not compact the hooks")

    # GROWTH against a recorded baseline, not just an absolute ceiling. A one-off prune measurably
    # does not hold — the last one here went 43929B -> ~37669B -> 44869B within six days, i.e. net
    # growth against its own pre-trim baseline, because every individual addition was justified and
    # nothing summed them. An absolute threshold cannot catch that: once you sit near it, it fires
    # every run and becomes wallpaper. A delta fires when something changed, which is while someone
    # can still remember why. Baseline lives beside the skill that owns the procedure.
    # The baseline is per-user data: ~/.claude/local/always-on-prune/ first, then the flat-layout location.
    base_f = prefs.parent / "local" / "always-on-prune" / "baseline.txt"
    if not base_f.is_file():
        base_f = prefs.parent / "skills" / "always-on-prune" / "baseline.txt"
    if base_f.is_file():
        try:
            lines = base_f.read_text().splitlines()
            base = int(lines[0].split()[0])
            grown = total - base
            if grown > 2000:
                flags.append(f"pref bodies have grown {grown}B since the last prune ({base}B -> "
                             f"{total}B) — run the always-on-prune skill")
            if len(lines) > 1:
                rbase = int(lines[1].split()[0])
                if roster - rbase > 2000:
                    flags.append(f"skill descriptions have grown {roster - rbase}B since the last "
                                 f"prune ({rbase}B -> {roster}B) — the listing drops descriptions "
                                 f"when over budget; run the always-on-prune skill")
            else:
                flags.append(f"{base_f.name} has no roster line — skill-description growth is unwatched")
        except (ValueError, IndexError):
            flags.append(f"{base_f.name} is unreadable — the growth ratchet is INERT, not clean")
    # No baseline recorded: absent until always-on-prune writes one, so nothing to compare against.

    # Absolute ceiling, deliberately set well ABOVE the current floor so it stays a backstop for a
    # store that has never been pruned rather than a permanent nag. It was 32000 against file bytes;
    # after a prune that stopped at 37845B of bodies — because going lower meant cutting mechanism
    # rather than ceremony — a 32000 line would have fired on every run forever, and a check that is
    # always red is one nobody reads. The growth delta above is what does the real work now.
    # The claim is COST — paid on every request — not adherence: the factorial study in references/
    # tiers instruction-file size as an affirmative null for adherence (BF10 0.05-0.10), so "bloat
    # degrades adherence" is not something this project's evidence supports.
    if total > 60000:
        flags.append(f"{total}B of always-on pref bodies — paid on every request")
    if flags:
        print(f"  always-on prefs: " + "; ".join(flags))
        return 1
    return 0

def check_skills(root):
    print("== skills (content that goes stale independently of the method) ==")
    if not pathlib.Path(root).is_dir():
        print(f"  clean — nothing to check ({root} absent)")   # plugin-only installs have no flat skills dir
        return 0
    rows = []
    for sk in sorted(pathlib.Path(root).glob("*/SKILL.md")):
        text = sk.read_text(errors="replace")
        d = i = m = c = p = 0
        for _, line, raw in _prose(text):
            d += len(DATE.findall(line))        # discussed -> stripped
            c += len(COUNT.findall(line))       # discussed -> stripped
            m += len(MAC.findall(raw))          # written in backticks -> raw
            for ip in IPV4.findall(raw):
                if PRIVATE.match(ip): i += 1
                elif ip != "1.1.1.1":  p += 1
        tot = d + i + m + c + p * 2          # public IPs weighted: leak risk
        if tot:
            rows.append((tot, sk.parent.name, d, i, m, c, p))
    for tot, name, d, i, m, c, p in sorted(rows, reverse=True):
        extra = f" PUBLIC-IP:{p}" if p else ""
        print(f"  {name:<26} score {tot:<4} dates:{d} priv-ip:{i} mac:{m} counts:{c}{extra}")
    # Frontmatter a strict YAML parser rejects (an unquoted ": " in a description) went unnoticed in
    # four skills at once; the harness tolerates it, anything else that reads the file may not.
    # Long descriptions push other skills' descriptions out of the size-capped listing.
    fm_bad = 0
    try:
        import yaml
    except ImportError:
        yaml = None
        print("  frontmatter: PyYAML missing — UNCHECKED, not clean")
    for sk in sorted(pathlib.Path(root).glob("*/SKILL.md")) if yaml else []:
        mt = re.match(r"^---\n(.*?)\n---", sk.read_text(errors="replace"), re.S)
        try:
            desc = " ".join(str((yaml.safe_load(mt.group(1)) or {})["description"]).split())
        except Exception as e:
            fm_bad += 1
            print(f"  {sk.parent.name:<26} FRONTMATTER INVALID: {str(e).splitlines()[0][:70]}")
            continue
        if len(desc) > 1024:
            fm_bad += 1
            print(f"  {sk.parent.name:<26} description {len(desc)} chars > 1024 — crowds the skill listing")
    if not rows and not fm_bad:
        print("  clean")
    return len(rows) + fm_bad

def check_docs(repos):
    print("== docs older than the code beside them ==")
    hits = skipped = 0
    for repo in repos:
        repo = pathlib.Path(repo).expanduser()
        if not (repo / ".git").exists():
            skipped += 1
            print(f"  {repo}: not a git repo, skipped"); continue
        def git(*a):
            r = subprocess.run(["git", "-C", str(repo), *a],
                               capture_output=True, text=True)
            return r.stdout.strip()
        for doc in repo.rglob("*.md"):
            if ".git" in doc.parts or "node_modules" in doc.parts:
                continue
            rel = doc.relative_to(repo)
            dts = git("log", "-1", "--format=%at", "--", str(rel))
            if not dts:
                continue
            sibs = [str(p.relative_to(repo)) for p in doc.parent.iterdir()
                    if p.is_file() and p.suffix != ".md"]
            if not sibs:
                continue
            cts = git("log", "-1", "--format=%at", "--", *sibs)
            if not cts:
                continue
            lag = (int(cts) - int(dts)) // 86400
            if lag > 30:
                hits += 1
                print(f"  {repo.name}/{rel}: {lag}d behind its directory")
    if not hits:
        # "clean" after skipping every repo is the falsely-clean shape this tool exists to catch
        print("  clean" if not skipped else f"  {skipped} repo(s) skipped — those are UNCHECKED, not clean")
    return hits + skipped


def check_probes(root, timeout=20):
    """Run each memory's `check:` probe. A failing probe means the memory may be stale."""
    import subprocess, os
    print("== probes (memories whose `check:` command failed) ==")
    # SECURITY: a probe is arbitrary shell from file frontmatter. Safe when you authored
    # every memory; remote code execution the moment memories are shared or writable by
    # others. Opt in explicitly; never run a probe from a file you do not own.
    # MUST be an explicit "1". `not os.environ.get(...)` treated the string "0" as truthy, so
    # HYGIENE_RUN_PROBES=0 ENABLED arbitrary shell execution from memory frontmatter — and the sweep
    # defaulted the variable to "0", so the scheduled path ran every probe while its own report said
    # "probes did NOT run". Opt-in means one exact value, never "anything set".
    if os.environ.get("HYGIENE_RUN_PROBES") != "1":
        print("  SKIPPED — probes execute shell from memory frontmatter.")
        print("  Set HYGIENE_RUN_PROBES=1 only where every memory file is yours.")
        return 0
    if not pathlib.Path(root).is_dir():
        print(f"  clean — nothing to check ({root} absent)")
        return 0
    total = withp = failed = 0
    noprobe = []
    na = 0
    mem_dirs = sorted(pathlib.Path(root).glob("*/memory"))
    for md in sorted(m for d in mem_dirs for m in d.rglob("*.md")):
        if md.name == "MEMORY.md":
            continue
        # Open ONCE and fstat that descriptor: checking after the read leaves a window where the
        # content executed is not the content that was vetted.
        try:
            _fd = os.open(md, os.O_RDONLY)
        except OSError:
            continue
        try:
            _st = os.fstat(_fd)
            unsafe = (_st.st_uid != os.getuid()
                      or bool(_st.st_mode & (stat.S_IWGRP | stat.S_IWOTH)))
            with os.fdopen(_fd, "r", errors="replace") as _fh:
                head = _fh.read(1200)
        except OSError:
            continue
        try:
            _pst = md.parent.stat()
            if _pst.st_uid != os.getuid() or (_pst.st_mode & (stat.S_IWGRP | stat.S_IWOTH)):
                unsafe = True          # a writable parent means the file can be replaced wholesale
        except OSError:
            unsafe = True
        mt = re.search(r'^\s*type:\s*(\w+)', head, re.M)
        mtype = mt.group(1) if mt else "unset"
        # Only facts ABOUT A SYSTEM can be falsified. user/feedback memories are
        # preferences and physical facts — a probe on those would pass forever and
        # prove nothing, which is worse than none.
        if mtype in ("user", "feedback"):
            continue
        total += 1
        m = re.search(r'^\s*check:\s*(.+?)\s*$', head, re.M)
        if not m:
            noprobe.append(f"{md.parent.parent.name}/{md.name} [{mtype}]")
            continue
        if m.group(1).strip().strip('"\'').lower().startswith("n/a"):
            na += 1          # deliberately unprobeable, with a stated reason
            continue
        if unsafe:
            print(f"  SKIPPED (not owned by you, or group/world-writable, or in a writable "
                  f"directory): {md.parent.parent.name}/{md.name}")
            continue
        withp += 1          # counted only once we will actually run it
        broke = "error"
        cmd = m.group(1).strip()
        # Strip only a MATCHING outer pair, and decode it as YAML would: a double-quoted value keeps
        # `\"` literally otherwise, and the shell then runs a path with quote characters in it.
        if len(cmd) > 1 and cmd[0] == cmd[-1] == '"':
            try:
                cmd = json.loads(cmd)
            except ValueError:
                cmd = cmd[1:-1]
        elif len(cmd) > 1 and cmd[0] == cmd[-1] == "'":
            cmd = cmd[1:-1].replace("''", "'")
        # Popen, not run(): on timeout we need the CHILD's pid to kill its whole process group.
        # `TimeoutExpired.args[0]` is the command list, not a pid — deriving a pgid from it lands on
        # os.getpgid(0), i.e. THIS process's group, and SIGKILLs the scanner itself.
        r, proc = None, None
        try:
            proc = subprocess.Popen(["bash", "-c", cmd], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, text=True, start_new_session=True)
            out_s, err_s = proc.communicate(timeout=timeout)
            # The contract is the EXIT STATUS: a probe must exit non-zero when the fact is false.
            # Requiring output made correct silent probes (`test -f …`) report STALE.
            ok = proc.returncode == 0
            r = subprocess.CompletedProcess(cmd, proc.returncode, out_s, err_s)
        except subprocess.TimeoutExpired:
            # Killing bash alone leaves anything it backgrounded behind.
            try:
                os.killpg(os.getpgid(proc.pid), 9)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            try:
                proc.communicate(timeout=5)
            except Exception:
                pass
            ok, broke = False, f"timed out after {timeout}s"
        except Exception as e:
            ok, broke = False, f"the checker itself failed: {type(e).__name__}"
        if not ok:
            failed += 1
            # "the fact is false" and "the checker broke" are different problems; saying which is
            # the difference between fixing a memory and chasing one that was never wrong.
            why = f"exit {r.returncode}" if r else broke
            print(f"  STALE? {md.parent.parent.name}/{md.name}")
            print(f"         check: {cmd}")
            print(f"         -> {why}")
    print(f"  {withp}/{total} system-describing memories carry a probe; {failed} failed."
          + (f" {na} marked n/a with a reason." if na else ""))
    if noprobe:
        print(f"  {len(noprobe)} project/reference memories have NO probe — add one, or if the fact")
        print(f"  can't be falsified by a command, it belongs with its subject or is mistyped:")
        for n in noprobe:
            print(f"    - {n}")
    print("  (user/feedback memories are excluded — preferences have no falsifier by design)")
    return failed


def check_refs(skills_root, mem_root):
    """Wiki-links in skills/companions pointing at memories that no longer exist.

    Concatenating a memory body into a skill companion drags its [[links]] along;
    when the target is later moved or deleted the pointer silently dies, and a
    reader (or an agent) follows it to nothing."""
    if not pathlib.Path(skills_root).is_dir():
        print("== dangling [[refs]] in skills ==")
        print(f"  clean — nothing to check ({skills_root} absent)")
        return 0

    print("== dangling [[refs]] in skills ==")
    prefs_dir = pathlib.Path(mem_root).parent / "memory"
    if not pathlib.Path(mem_root).is_dir() and not prefs_dir.is_dir():
        print(f"  clean — nothing to check ({mem_root}, {prefs_dir} absent)")   # else every ref would look dangling
        return 0
    have = {p.stem for p in pathlib.Path(mem_root).rglob("*.md") if "memory" in p.parts}
    have |= {p.stem for p in (pathlib.Path(mem_root).parent / "memory").glob("*.md")}
    have |= {p.name for p in pathlib.Path(skills_root).glob("*") if p.is_dir()}
    # A companion file is a legitimate target: a note living at fleet-notes/foo.md satisfies
    # [[foo]]. Globbing one level deep both MISSED those files and reported every ref to them
    # as dangling — a check that invents findings gets ignored, which is worse than none.
    have |= {p.stem for p in pathlib.Path(skills_root).rglob("*.md")}
    bad = 0
    targets = [(p, str(p.relative_to(skills_root)))
               for p in sorted(set(pathlib.Path(skills_root).rglob("*.md")))]
    # The always-on prefs dir carries [[links]] too, and it is the store the setup depends on most.
    # Omitting it meant a dead pointer there was reported clean forever.
    prefs = pathlib.Path(mem_root).parent / "memory"
    if prefs.is_dir():
        targets += [(p, f"memory/{p.name}") for p in sorted(prefs.glob("*.md"))]
    for f, shown in targets:
        body = re.sub(r'`[^`]*`', '', f.read_text(errors="replace"))   # a ref inside `backticks` is being
        # discussed, not referenced — don't flag prose about wiki-links as a broken wiki-link
        for ref in sorted(set(re.findall(r'\[\[([a-z0-9][a-z0-9-]+)\]\]', body))):
            if ref not in have:
                bad += 1
                print(f"  {shown}: [[{ref}]] -> no such memory or skill")
    if not bad:
        print("  clean")
    return bad


def check_doc_content(repos):
    """Repo docs carrying content that decays: dates, run counts, status amendments.

    The `docs` check measures AGE. This measures CONTENT — a doc can be freshly
    committed and still assert something that stopped being true. Keep the mechanism
    of a failure; drop the measurements of the moment."""
    print("== docs carrying decaying content ==")
    STATUS = re.compile(r'\b(IN PROGRESS|PENDING|TODO|DONE|RESOLVED|FIXED|PROVEN|VALIDATED)\b')
    RUNCOUNT = re.compile(r'\b[0-9]{2,}\s*(items|files|records|entries|objects|instances)\b', re.I)
    hits = skipped = 0
    for repo in repos:
        rp = pathlib.Path(repo).expanduser()
        if not rp.is_dir():
            skipped += 1
            print(f"  {rp}: not a directory, skipped — UNCHECKED"); continue
        for f in sorted(rp.rglob("*.md")):
            if ".git" in f.parts or "node_modules" in f.parts:
                continue
            d = s = c = 0
            for _, line, _raw in _prose(f.read_text(errors="replace")):
                d += len(DATE.findall(line))
                s += len(STATUS.findall(line))
                c += len(RUNCOUNT.findall(line))
            if d + s + c:
                hits += 1
                print(f"  {f}: dates:{d} status-words:{s} run-counts:{c}")
    if not hits:
        print("  clean" if not skipped else f"  {skipped} path(s) skipped — UNCHECKED, not clean")
    else:
        print("  (a threshold or protocol constant belongs; a measurement of now does not)")
    return hits + skipped

def check_numbering(skills_root):
    """Duplicate SECTION NUMBERS in a skill -- the signature of a section grafted in from
    another copy. Keyed on (level, number), not the number alone: a bare-number check flags
    `## 1.` against `### 1.`, which is legitimate sub-numbering restarting under a new parent,
    and a gate with false positives gets switched off. A heading-STRING comparison misses this
    entirely, because the two colliding sections have different titles."""
    import collections
    root = pathlib.Path(skills_root)
    print("== skill section numbering ==")
    hits = 0
    for f in sorted(root.rglob("*.md")):
        txt = f.read_text(errors="replace")
        lv = re.findall(r"^(#{2,4}) (\d+)\. ", txt, re.M)
        c = collections.Counter(lv)
        dup = sorted({f"{h} {n}" for h, n in lv if c[(h, n)] > 1},
                     key=lambda x: (len(x.split()[0]), int(x.split()[1])))
        if dup:
            print(f"  {f.relative_to(root)}: duplicate section number(s) {dup}"); hits += 1
        # A graft appended at the END of a file produces no duplicate, it produces numbers OUT OF
        # ORDER (1,2,3,4,5,7,6). Per level, since sub-numbering under a new parent legitimately restarts.
        by_level = collections.defaultdict(list)
        for h, n in lv:
            by_level[h].append(int(n))
        for h, nums in sorted(by_level.items(), key=lambda kv: len(kv[0])):
            drops = [(nums[i], nums[i + 1]) for i in range(len(nums) - 1) if nums[i + 1] < nums[i]]
            # One descent is the graft signature; several usually means per-subsection restarts (a style).
            if len(drops) == 1 and not dup:
                a, b_ = drops[0]
                print(f"  {f.relative_to(root)}: '{h}' sections run out of order "
                      f"({a} then {b_}) - the signature of a section grafted in at the end")
                hits += 1
    if not hits:
        print("  clean")
    return hits


def check_hooks(claude_root):
    """A hook is only enforcement if it exists AND is registered. Either half alone is
    indistinguishable from a hook that ran and found nothing — same files on disk, same
    silence in the log. Found live on a multi-host setup: one gate absent, one present but
    referenced by no settings.json, while every other signal said the setup was healthy."""
    root = pathlib.Path(claude_root)
    hooks_dir, settings = root / "hooks", root / "settings.json"
    print("== hooks (registration <-> presence) ==")
    if not settings.is_file():
        print("  SKIPPED — no settings.json (UNCHECKED, not clean)"); return 1
    conf = settings.read_text(errors="replace")
    hits = 0
    # registered but missing: the hook silently never runs
    for m in re.finditer(r'"command"\s*:\s*"([^"]*?\.sh)[^"]*"', conf):
        cmd = m.group(1)
        path = pathlib.Path(re.sub(r"^.*?(?=/)", "", cmd) or cmd).expanduser()
        if not path.is_file():
            print(f"  REGISTERED BUT MISSING: {cmd}"); hits += 1
    # present but unregistered: looks installed, enforces nothing
    # `test-*.sh` beside a hook is that hook's regression suite, and is unregistered BY DESIGN —
    # registering one would run the test harness as a hook. Flagging them made this check report a
    # finding on every run, and a gate that cries wolf is one people stop reading. Narrow, not
    # blanket: any other unregistered .sh here is still a real finding.
    def is_suite(name):
        return name.startswith("test-")

    if hooks_dir.is_dir():
        for f in sorted(hooks_dir.glob("*.sh")):
            if f.name not in conf and not is_suite(f.name):
                print(f"  PRESENT BUT UNREGISTERED: {f.name}"); hits += 1
    if not hits:
        n = len([f for f in hooks_dir.glob("*.sh") if not is_suite(f.name)]) if hooks_dir.is_dir() else 0
        print(f"  clean — {n} hook script(s), all registered")
    return hits


NOSHIP   = re.compile(r'^[ \t]*(<!--[ \t]*)?NO-SHIP\b', re.M)
TYPEUSER = re.compile(r'^[ \t]*type:[ \t]*user\b', re.M)
TYPEOK   = re.compile(r'^[ \t]*type:[ \t]*(user|feedback)\b', re.M)
CHECKLN  = re.compile(r'^[ \t]*check:', re.M)
HEADING2 = re.compile(r'^##[^#].*$', re.M)
# Wreckage from generalizing a name with a blanket substitution instead of rewriting the sentence.
PRONOUN  = re.compile(r'\byou is\b|\bto you instead\b|\bsurfacing to you\b|\byou values\b', re.I)

# Commands where ANY real-$HOME argument is a write. A redirect is NOT in this set: `>` says nothing
# about which path it targets, so it is handled by _redirect_writes_home() below, the same way cp/mv
# are — see that function for the two false positives that forced the split.
_MUTATES = re.compile(r"\b(rm|rmdir|mkdir|touch|truncate|chmod|tee)\b")
# `cp` and `mv` are deliberately NOT in that set. They take a SOURCE and a DESTINATION and write only
# the destination, so word-presence conflated with argument-target reported `cp "$HOME/.claude/x"
# "$T/"` — staging a real installed file into a scratch dir, which is exactly what a suite needing a
# genuine file has to do — as a mutation of $HOME. That made the check permanently red on the tree it
# ships with, the cry-wolf failure it was tuned to avoid.
_SEG     = re.compile(r"\s(?:\|\||&&|[;|&])\s*")   # segment separators
_TRAIL   = re.compile(r"\s(?:\d?>|<|#)")            # a redirect or comment inside a segment
_COPYCMD = re.compile(r"^\s*(?:sudo\s+|xargs\s+)?(?:cp|mv)\b")


def _copy_writes_home(line):
    """True if a cp/mv on this line has the real home as its DESTINATION rather than its source.

    NOT "the last whitespace token on the line" — anything trailing the command displaces the
    destination, so `mv "$T/x" "$HOME/.claude/y" 2>/dev/null` and `cp a "$HOME/.claude/b" && echo ok`
    are real writes that would go unreported. Split into segments and take the last token of the
    cp/mv segment before any redirect. Anchoring to command position also stops `java -cp
    "$HOME/.claude/lib.jar"` matching, which a bare \b(cp|mv)\b does.

    Still not dataflow: segment boundaries and which token is the destination are facts a single line
    already carries, so this stays inside the line-oriented ceiling rather than pushing past it."""
    for seg in _SEG.split(line):
        if not _COPYCMD.match(seg):
            continue
        m = _TRAIL.search(seg)
        head = seg[:m.start()] if m else seg
        dest = head.rstrip().rsplit(None, 1)[-1] if head.split() else ""
        if _REAL_HOME.search(dest):
            return True
    return False
# `$HOME` in any form is a real-home reference. A bare `~/` is NOT: it shows up constantly inside
# test-case fixture STRINGS handed to a gate to judge and never executed (`cd ~/proj && nohup ...`),
# so the tilde form is narrowed to the config tree these suites live in. The first version flagged
# exactly such a fixture, and a check that cries wolf is the failure this one exists to prevent.
_REAL_HOME = re.compile(r'\$HOME|(?<![\w/])~/\.claude')


def _blank_quoted(s):
    """Replace the CONTENTS of quoted spans with filler, preserving length and the quotes.

    Offsets stay valid, so a match position in the blanked string indexes the raw string."""
    out, q = [], None
    for ch in s:
        if q:
            out.append(ch if ch == q else "\x00"); q = None if ch == q else q
        elif ch in "\"'":
            out.append(ch); q = ch
        else:
            out.append(ch)
    return "".join(out)


_REDIR = re.compile(r"\d?>>?")


def _redirect_writes_home(line):
    """True if a redirect on this line has the real home as its TARGET.

    Word-presence was conflating 'the line mentions $HOME' with 'the line writes to $HOME', which is
    the same mention-vs-use error `cp`/`mv` already have a carve-out for one function up. Two real
    false positives it produced, both in suites that are correct:

      { say "..."; route "$HOME/.claude/memory/foo.md"; } > "$TD/e.jsonl"
      t 2 "append to a skill" 'echo "- extra" >> ~/.claude/skills/repo-vet/SKILL.md'

    The first names a real-home path as an ARGUMENT (a helper that only prints it into a JSON
    fixture) and redirects to a temp dir. The second is a fixture STRING handed to a gate to judge
    and never executed. Neither writes anything under $HOME, and between them they made this check
    permanently red on the tree it ships with.

    Two things separate them from a real write, and both are needed:
      - the redirect operator must be OUTSIDE quotes (a `>` inside a fixture string is program text);
      - the real-home reference must be the redirect's TARGET, not merely somewhere on the line.

    Deliberately NOT done by blanking quotes and re-testing the whole line: that would also silence
    `cat > "$HOME/.claude/x"`, a genuine write whose target is quoted. Testing the target on the RAW
    line keeps that one caught."""
    blanked = _blank_quoted(line)
    for m in _REDIR.finditer(blanked):
        target = line[m.end():].lstrip().split()[:1]
        if target and _REAL_HOME.search(target[0]):
            return True
    return False


def check_test_isolation(claude_root):
    """A test must not mutate the state it tests. Written down as prose, hit anyway four times
    across two machines — a suite clearing the live `.detached-checked` stamps so the real gate
    re-nudged sessions it had already nudged, and a suite writing fixtures into the real
    `~/.claude/agents`. Prose that has already failed does not get another chance.

    The fix a finding here wants is not "put it back afterwards" — that still leaves a window where
    a concurrent live session reads the mutated state, and the damage does not announce itself.
    Override the location outright: a throwaway HOME, a --config flag, a chdir into a scratch dir."""
    root = pathlib.Path(claude_root)
    print("== test suites (must not mutate the state they test) ==")
    suites = sorted(list((root / "hooks").glob("test-*.sh")) +
                    list((root / "skills").glob("*/test-*.sh")))
    if not suites:
        print(f"  clean — no test suites under {root}"); return 0
    hits = 0
    for sp in suites:
        for i, line in enumerate(sp.read_text(errors="replace").splitlines(), 1):
            bare = line.strip()
            if bare.startswith("#"):
                continue
            if not _REAL_HOME.search(line):
                continue
            # Additive, NOT a chain of elif: a line can carry several of these at once, and the
            # first version made them exclusive. `mv "$T/x" "$HOME/.claude/y" 2>/dev/null` then went
            # down the redirect branch on the strength of its `2>`, found /dev/null, and returned
            # before the cp/mv destination was ever looked at — a real write silenced by an
            # unrelated stderr redirect on the same line.
            blanked = _blank_quoted(line)
            if not (_MUTATES.search(blanked)                                   # verb: any real-home arg is a write
                    or (_REDIR.search(blanked) and _redirect_writes_home(line))  # redirect TARGET is real home
                    or (re.search(r"\b(cp|mv)\b", line) and _copy_writes_home(line))):  # cp/mv DESTINATION
                continue
            print(f"  MUTATES REAL $HOME: {sp.relative_to(root)}:{i}: {bare[:88]}")
            hits += 1
    if not hits:
        print(f"  clean — {len(suites)} suite(s), none writing under the real $HOME")
    return hits


def check_shareable(root, names=(), pack="seed-memory"):
    """Refuse-to-ship gates for a copy of the setup that leaves this machine — a published
    plugin, a repo someone installs from, a transfer bundle. Blocks are refusals, not style
    preferences: each one shipped at least once.

    `pack` names the directory of memories that get COPIED into someone else's store (as
    opposed to files they read in place). Only the frontmatter gates apply inside it, because
    only a copied memory is loaded by an agent that believes it describes its own operator.

    Unreadable is not clean. Anything that cannot be read is reported as UNCHECKED, because an
    empty findings list and an unreadable tree must never look the same."""
    root = pathlib.Path(root)
    print("== refuse-to-ship gates ==")
    blocks = unchecked = 0

    for p in sorted(root.rglob("*")):
        if not p.is_file() or ".git" in p.parts:
            continue
        rel = p.relative_to(root)
        try:
            txt = p.read_text(errors="replace")
        except OSError as e:
            print(f"  {rel}: unreadable ({e}) — UNCHECKED, not clean"); unchecked += 1; continue

        # A NAME does not care what file it lands in. Scanning only *.md let a companion JSON
        # full of other people's names ship with every gate reporting clean. Whole word and
        # case-INSENSITIVE: an unanchored match hits substrings (`Ed` inside "fix**ed**"), and a
        # checker that cries wolf is one people learn to bypass; a case-SENSITIVE one once passed
        # a bundle whose only hit was a lowercase directory name.
        for n in names:
            if re.search(rf'\b{re.escape(n)}\b', txt, re.I):
                print(f"  BLOCK {rel}: contains {n!r} as a whole word"); blocks += 1

        if p.suffix != ".md":
            continue

        # The marker sits under the frontmatter. Prose saying "don't share this" is not
        # enforcement: the person packaging the copy is exactly the person who won't re-read it.
        if NOSHIP.search("\n".join(txt.split("\n")[:25])):
            print(f"  BLOCK {rel}: NO-SHIP marker — person-specific by declaration"); blocks += 1

        if pack in p.parts:
            if TYPEUSER.search(txt):
                print(f"  BLOCK {rel}: a `type: user` note describes the AUTHOR; a copy of it is "
                      "read by the installer's agent as a fact about themselves"); blocks += 1
            if CHECKLN.search(txt):
                print(f"  BLOCK {rel}: a `check:` line in a copied memory is arbitrary shell on a "
                      "machine belonging to someone who did not write it"); blocks += 1
            if p.name != "MEMORY.md" and not TYPEOK.search(txt):
                print(f"  BLOCK {rel}: neither `type: user|feedback` nor a `check:` — the memory "
                      "write gate travelling with it will refuse this very file"); blocks += 1

        # A SPECIMEN is not an instance. The bullet documenting this very check quotes `you is`
        # and `to you instead` as examples, so an unscoped scan blocks the file that defines the
        # rule — the same self-documentation failure NO-SHIP already hit, and the same reason it
        # is head-scoped. Blanking inline-code spans is the general form of that fix: it works
        # wherever a rule is written down, not only in the one file that happens to define it.
        # An allowlist entry would be the weaker option — instance data that does not travel.
        for m in PRONOUN.finditer(re.sub(r"`[^`\n]*`", lambda c: " " * len(c.group(0)), txt)):
            print(f"  BLOCK {rel}: {m.group(0)!r} — left by a blanket name substitution; "
                  "rewrite the sentence"); blocks += 1

        # The signature of a graft bounded at ONE end only. Complementary to check_numbering(),
        # not a replacement: the colliding sections there have different titles and the same
        # number, and here the same title. Neither finds the other's case.
        seen = HEADING2.findall(txt)
        dupes = sorted({h for h in seen if seen.count(h) > 1})
        if dupes:
            print(f"  BLOCK {rel}: repeated heading(s) {dupes[:3]}"); blocks += 1

    # Manifest parity — only meaningful if the copy is a plugin marketplace. A reader sees the
    # marketplace description while CHOOSING, so a promise there the plugin does not keep is the
    # one that actually misleads.
    mk = root / ".claude-plugin/marketplace.json"
    if mk.exists():
        import json
        try:
            listed = {e["name"]: e for e in json.loads(mk.read_text()).get("plugins", [])}
        except Exception as e:
            print(f"  marketplace.json: unparseable ({e}) — UNCHECKED"); listed = {}; unchecked += 1
        for d in sorted(p for p in (root / "plugins").glob("*") if p.is_dir()):
            pj = d / ".claude-plugin/plugin.json"
            if not pj.exists():
                print(f"  BLOCK plugins/{d.name}: no plugin.json"); blocks += 1; continue
            try:
                own = json.loads(pj.read_text())
            except Exception as e:
                print(f"  plugins/{d.name}/plugin.json: unparseable ({e}) — UNCHECKED")
                unchecked += 1; continue
            entry = listed.get(d.name)
            if entry is None:
                print(f"  BLOCK plugins/{d.name}: exists but marketplace.json does not list it")
                blocks += 1; continue
            for k in ("name", "version", "description", "keywords"):
                if own.get(k) != entry.get(k):
                    print(f"  BLOCK plugins/{d.name}: {k} differs between plugin.json and "
                          "marketplace.json"); blocks += 1
        for n in listed:
            if not (root / "plugins" / n).is_dir():
                print(f"  BLOCK {n}: listed in marketplace.json but the plugin is absent")
                blocks += 1

    if not blocks and not unchecked:
        print("  clean")
    elif unchecked:
        print(f"  {unchecked} path(s) UNCHECKED — not clean")
    return blocks + unchecked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["memory", "skills", "docs", "doccontent", "probes", "refs",
                                     "imports", "hooks", "numbering", "testiso", "shareable",
                                     "all"])
    ap.add_argument("repos", nargs="*")
    ap.add_argument("--memory-root", default=str(DEF_MEM))
    ap.add_argument("--skills", default=str(DEF_SKILLS))
    ap.add_argument("--names", default="", help="comma-separated names to refuse, matched as "
                                               "whole words, case-insensitively")
    ap.add_argument("--share-root", help="the copy to gate (a plugin repo, a bundle dir)")
    a = ap.parse_args()
    rc = 0
    # A mode that needs repos and got none must SAY so. Printing nothing and exiting 0 is
    # indistinguishable from "checked, clean".
    if a.mode in ("docs", "doccontent") and not a.repos:
        ap.error(f"mode '{a.mode}' needs one or more REPO paths")
    if a.mode == "all" and not a.repos:
        print("== docs / doccontent ==")
        print("  SKIPPED — no REPO paths given, so the two doc checks did not run (UNCHECKED, not clean)")
        rc += 1
    # `imports` audits ONLY the always-on prefs dir. It is part of `memory` too; kept as its own mode
    # because a session-start hook may want just this, and because removing a documented mode name
    # breaks every caller that already uses it.
    if a.mode == "imports":
        print("== always-on prefs (import wiring + session weight) ==")
        rc += check_prefs(pathlib.Path(a.memory_root).parent / "memory") or 0
    if a.mode in ("memory", "all"): rc += check_memory(a.memory_root) or 0
    if a.mode in ("skills", "all"): rc += check_skills(a.skills) or 0
    if a.mode in ("docs", "all") and a.repos: rc += check_docs(a.repos) or 0
    if a.mode in ("doccontent", "all") and a.repos: rc += check_doc_content(a.repos) or 0
    if a.mode in ("probes", "all"): rc += check_probes(a.memory_root) or 0
    if a.mode in ("refs", "all"): rc += check_refs(a.skills, a.memory_root) or 0
    if a.mode in ("hooks", "all"): rc += check_hooks(pathlib.Path(a.memory_root).parent) or 0
    if a.mode in ("numbering", "all"): rc += check_numbering(a.skills) or 0
    if a.mode in ("testiso", "all"): rc += check_test_isolation(pathlib.Path(a.memory_root).parent) or 0
    if a.mode == "shareable":
        rc += check_shareable(a.share_root or ".",
                              [n.strip() for n in a.names.split(",") if n.strip()])
    return 1 if rc else 0

if __name__ == "__main__":
    sys.exit(main())
