---
name: claude-fleet-sync
description: Mirror Claude Code config (skills, project + global memory, user CLAUDE.md, plugins, permission allowlist, ssh aliases, toolkit dirs, systemd-creds) across machines you fully control, so every host holds the union. Use when the user asks to sync, mirror, or reconcile their Claude config / setup / skills / memory between their own machines (laptop, workstation, build VM) — e.g. "sync my claude config", "mirror my setup to the other box", "my skills have drifted between machines", "keep my skills and memory in sync" — or after adding a skill/memory/plugin/CLAUDE.md change on one box that should exist on the others.
---

# Claude fleet config sync

Reconcile `~/.claude` (and the toolkits it depends on) across several machines **one
person fully controls** — a laptop and a build VM, say — so each ends with the
**union** of all hosts' content. Use this when your skills and memory have drifted
between your own boxes.

Not the same job as `claude-config-export` / `claude-config-import`: those cross a
**trust boundary** (different environment, different rules, scrub + judge on arrival).
This one assumes a single trust domain, so it moves content verbatim — including
secrets — and its problem is *reconciliation*, not sanitization. If the other machine isn't
yours or has a different security posture, use the export/import pair.

This is a **hybrid** skill:

- **You (the agent) reconcile the natural-language content by reading it** — memory
  `.md` files, the `MEMORY.md` index, skill prose. Deciding what a note should say,
  what's a real conflict, and what should or shouldn't sync is *judgment*, not a
  newest-mtime coin-flip. Never blind-copy a diverging natural-language file.
- **`sync.py` does the mechanical parts** — SSH ControlMaster, backups, inventory +
  divergence detection, file transport, deterministic JSON/ssh-alias unions, and
  `creds-sync.sh`. It hands you the facts; it does **not** pick winners on prose.

Model: **absorb → reconcile → mirror.** The machine you run on is the **hub**. First
absorb everything (so nothing is ever lost), reconcile the prose by hand, then mirror
the union back out. Idempotent — safe to re-run.

## Autonomous scheduled mode (report-first)

When invoked non-interactively by a scheduler (the prompt says `--auto` / "autonomous scheduled run"): there's no human to resolve prose conflicts, so take the **Quick path** only and never guess a natural-language winner.

1. `backup`, then `inventory`.
2. **No ⚠ divergences and no index problems** → run the full mechanical mirror: `push` skills, each project's memory tree, **`.claude/memory/` (global), `.claude/CLAUDE.md`, and the step-4 hooks line**, then `rsync-tree`, `jsonmerge`, `aliases`, `creds`, `verify`. Print the verify table.
3. **Any ⚠ divergence or index problem** → absorb peer-unique files (safe — loses nothing) and run the mechanical unions, but **STOP before mirroring diverging prose**. Emit a report of each divergence (path, which hosts, one-line diff summary) to stdout for a human to reconcile interactively later. Skipping the prose mirror is the safe default.

The model is union (nothing is ever lost), so a conservative autonomous run is safe; a human runs the full interactive flow to merge any diverging prose.

## Configuring the roster

`FLEET` near the top of `sync.py` is a **placeholder** (`<host-a>`, `<host-b>`, …) —
set it to your own hostnames, or don't touch it at all and pass the roster per run:

```bash
python3 sync.py inventory --hosts laptop.example.internal,build-vm.example.internal
```

`--hosts` overrides `FLEET` for every subcommand, so the file can stay unedited on a
machine where you'd rather not persist a host list. `creds-sync.sh` takes its hosts as
positional arguments the same way (`sync.py creds` forwards the live set to it).

Requires key-based SSH + `rsync` + `tar` on every host, and an **identical `$HOME`
path** across hosts (the transports are `$HOME`-relative). Preview any command with
`--dry-run`.

## What gets reconciled
**You reconcile (natural language — read the content):**
- **skills/** — skill dirs; on a diverging `SKILL.md`/script, read both and merge.
- **projects/\*/memory/** — memory `.md` files; merge diverging bodies by hand. Curate
  each `MEMORY.md`: union the bullets, **preserve curated hooks**, ensure every `.md`
  has exactly one bullet (add a hook for orphans, drop stale ones).
- **~/.claude/memory/ (global)** — cross-project behavioral notes; absorb/merge like
  project memory. Its "index" is the `@import` list in `CLAUDE.md` (not a `MEMORY.md`),
  so ensure every global note has a matching `@~/.claude/memory/<file>` line in CLAUDE.md.
- **~/.claude/CLAUDE.md** — user-level instructions; a single-file **full mirror** (one
  winner — run from the host whose CLAUDE.md should win). It @imports the global memory,
  so always mirror it together with `~/.claude/memory/`.

**The script reconciles (mechanical — deterministic):**
- **plugins/** — `installed_plugins.json`, caches, marketplaces, `enabledPlugins`,
  `extraKnownMarketplaces` (host-specific settings keys like `theme` are preserved).

  **A GUI-only plugin unions onto the headless host and breaks there.** To opt one host out, set
  `"<plugin>@<marketplace>": false` in **that host's `~/.claude/settings.json`** — `jsonmerge`
  preserves an explicit `false` per host. **`claude plugin disable -s local` does NOT work and
  reports that it did**; test with `claude -p`, never with `claude plugin list`. Details:
  `references/plugin-opt-out.md`.
- **settings.local.json** — `permissions.allow` rules unioned.
- **hook registration** — `settings.json` `hooks`, mirrored from the hub. `push .claude/hooks/`
  carries the *scripts*; the registration lives here, and a host holding an unregistered hook
  looks exactly like one whose hook found nothing. Mirrored, not unioned: the same command under
  two matchers would both survive a union and fire twice. A hook registered on a peer but not on
  the hub — or under an event/matcher the hub lacks — stops the mirror and is reported rather than
  deleted. **A peer whose hook scripts are newer usually re-registered something too**: carry its
  `hooks` block to the hub before mirroring.
- **ssh `Host` aliases** — union of `Host` blocks; missing ones appended (own blocks
  and global preamble never overwritten).
- **toolkit dirs** — auto-discovered `~/<dir>` a skill references (a helper/creds dir a
  skill drives), synced **verbatim incl. secrets** (the toolkit is useless without them).
  Git working copies are skipped — and so is a plain dir that merely *holds* repos
  (`~/src`, `~/projects`), which the is-it-a-repo test used to wave through.
- **systemd-creds secrets** — via `creds-sync.sh`; host/TPM-bound, so decrypted on the
  newest source and re-encrypted per target. Needs passwordless **sudo** on every host.

Never synced: history, sessions, transcripts, file-history, `.credentials.json`.

## Procedure

Run these from any fleet member. Each step is a `sync.py` subcommand; the **reconcile**
step in the middle is yours to do by reading files.

### 1. Connect + back up (always first)
```bash
# run from this skill's directory (where sync.py lives)
python3 sync.py ping          # opens one ControlMaster per peer; shows reachable/skipped
python3 sync.py backup        # per-host tarball: skills + settings*.json + */memory
```
`backup` writes `~/.claude/backups/reconcile-pre-<TS>.tgz` on **every live host** before
anything is modified. If a host is unreachable it's skipped — note it and continue.

### 2. Inventory — get the facts
```bash
python3 sync.py inventory
```
Read the output. It lists per-host skills/memory/plugins/aliases/toolkits and flags, with
a ⚠, every **divergence** (same path, different content) and every **index problem**
(memory file with no bullet, or bullet with no file). The ⚠ natural-language items are
**your** work in step 3. The mechanical sections map to steps 4–6.

### 3. Reconcile the natural-language content (YOU — by reading)
For each ⚠ item from the inventory:

- **Diverging memory `.md` or skill file** — read both versions, then merge. Don't let
  mtime decide; merge the *content*.
  > ⚠️ **`pull` extracts into `$HOME` and OVERWRITES the hub's copy in place** — it is
  > not a side-by-side fetch. If you `pull` a diverging file straight away, the hub's own
  > (often newer) version is clobbered by the peer's. So **stash the hub's copy first**,
  > then pull the peer's over it and diff against the stash:
  > ```bash
  > cp ~/<relpath> /tmp/hub-<file>            # stash the hub's version
  > python3 sync.py pull <host> <relpath>     # now hub path holds the PEER version
  > diff -u /tmp/hub-<file> ~/<relpath>       # hub-orig vs peer
  > ```
  > (If you already pulled without stashing, the hub original is in this run's
  > `~/.claude/backups/reconcile-pre-<TS>.tgz` — extract it from there to compare.)
  >
  > **Many diverging files?** Read `references/large-divergence.md` first: fetch peer copies in
  > one `tar` over the existing ControlMaster (FQDN + same `ControlPath`, never the short alias —
  > that fails `Permission denied` and looks like a broken host), and triage by ancestry against
  > the hub's backups before reading anything (one run cleared 91 of 133 this way).
  Edit the hub's copy to the correct merged result. If two hosts genuinely conflict and
  you can't tell which is right, **ask the user** — don't guess.
- **Peer-unique file** (exists on a peer, not the hub) — absorb it into the hub:
  `python3 sync.py pull <host> <relpath>`.
- **`MEMORY.md` curation** — for each project, build the union of bullet lines by hand:
  dedupe by link target, **keep the curated hook wording**, add a one-line hook for any
  orphan `.md`, and drop/fix any stale bullet. Write the result to the hub's `MEMORY.md`.
  (The script deliberately does **not** auto-write this — it would clobber curated hooks.)

After this step the **hub** holds the correct, merged union of all prose. Re-run
`python3 sync.py inventory --hosts <thishost>` if you want to confirm the hub looks right
before mirroring.

### 4. Mirror the reconciled prose out
Push the hub's now-correct skills + memory to the peers:
```bash
python3 sync.py push .claude/skills/
python3 sync.py push .claude/projects/<proj>/memory/    # repeat per project, incl. MEMORY.md
python3 sync.py push .claude/memory/                    # global cross-project notes
python3 sync.py push .claude/CLAUDE.md                  # user-level instructions (full mirror; @imports global memory)
python3 sync.py push .claude/hooks/ .claude/rules/ .claude/gitleaks-extra.toml .local/bin/gitleaks
```
Hook scripts and their dependencies ride here, not in `jsonmerge` — that only mirrors the
*registration*. A redaction hook needs its scanner binary and fails **open** without it, so a
peer missing the binary registers the gate and redacts nothing. Prove a peer's gates work by running
the hook's own `test-*.sh` there, not by `claude -p` staying quiet.
`push` distributes hub → all peers (or `--to host`). It copies exactly what you curated.

### 5. Mechanical unions
```bash
python3 sync.py rsync-tree     # plugin caches/marketplaces, local-marketplaces, toolkit dirs
python3 sync.py jsonmerge      # plugins + enabledPlugins + extraKnownMarketplaces + allow rules + skill ledgers
python3 sync.py aliases        # union ssh Host blocks
python3 sync.py creds          # systemd-creds equalize (needs sudo; --dry-run = inventory only)
```
`jsonmerge` preserves each host's own `theme`/posture keys — it only unions the shared
blocks. If a pushed `settings.local.json` loosens permissions, the harness may block the
first write; approve it deliberately.

**Skill decision-ledgers** (`LEDGERS` in `sync.py`, empty by default — add the path of any
keyed decision log your skills keep) ride here rather than on `rsync-tree` for a reason: a
ledger records conclusions a skill reached that *changed nothing else* — a "looked at it,
it's fine" verdict — so nothing can reconstruct it, and `rsync-tree`'s newest-mtime-wins
would drop whichever host recorded fewer, more recently. The union is keyed and additive,
so a verdict written on the laptop survives a later merge from the build VM. On a key both
hosts decided, the first host in the run's order wins; both verdicts agree on the *call* by
construction, so only the note differs. Adding a ledger is one line — keep it under a
`DENY_TOP` dir so `rsync-tree` stays off it.

> ⚠️ **`systemd-creds` convention: a cred's embedded name must match its filename.**
> `creds-sync` derives the name from the filename (`foo.cred` → `foo`) when re-encrypting
> on each target. A cred encrypted with a *different* embedded name (e.g. file
> `api-key.cred` but `--name=service-api-key`) makes `systemd-creds decrypt` **refuse**.
> The script now decrypts the source with `--name=` (empty, bypassing the label check),
> re-encrypts each target as `--name=<filename>`, checks **both** pipe stages, and
> verifies the installed cred — so a refused decrypt can no longer write a bogus empty
> cred. If you add a new cred, **encrypt it with `--name` equal to its filename** so the
> consumer's `decrypt --name=<filename>` and the sync agree. (Creds are TPM/host-bound:
> ciphertext isn't portable — every host is re-encrypted from the source plaintext.)

### 6. Verify parity
```bash
python3 sync.py verify
```
Prints a table (skills / memory / plugins / allow-rules / settings-parse) across hosts and
flags any mismatch. All hosts should agree; a remaining mismatch is either something you
still need to reconcile or a legitimately host-specific value — confirm which. Report the
final table to the user, plus anything you skipped (unreachable host, a conflict you
escalated, a permission write you approved).

## Quick path
If `inventory` shows **no ⚠ items** (no prose divergences, indexes healthy), there's
nothing to hand-reconcile — run `backup`, `push` the trees, then the step-5 mechanical
commands and `verify`. The hand-reconcile step only matters when content actually diverged.

## Guardrails
- **Back up first, every time** (step 1). The mirror is only safe after absorb + backup.
- **Never blind-copy a diverging natural-language file**, and never let the script pick a
  prose winner by mtime. Read both, merge, or ask.
- **Never delete** a memory file or skill that exists on only one host without absorbing
  it into the hub first.
- **"The hub is newer" is not evidence the hub is a superset.** A rewrite is a deletion you did not
  notice: condensing a note drops detail, and the peer's older copy is then the only record of what
  went, even when every divergence is a same-day hub edit and the mirror looks safe. So before pushing, diff each
  diverging file against the peer and **read the lines that would disappear**, not just the ones you
  added: `diff peer hub | grep '^<'`. Every line should be one you deliberately replaced. Restore
  anything else. This is cheap and it is the only check that catches your own edits.
- **Deletions don't propagate.** `push` is a union copy and never deletes, so a note or skill you
  *intend* to remove is resurrected from a peer on the next absorb unless you delete it on **every**
  host first. A **rename or move is a delete plus an add**, so it leaves the old path behind on every
  other host — same trap, and easier to miss because nothing looks removed locally.
  **`verify` reports this**: it compares the file SET across hosts, not just the counts, and
  names each difference as a ZOMBIE (peer-only — delete everywhere in one pass) or a GAP (hub-only —
  re-push). The counts alone could never catch it: a deletion on one host and an addition on another
  net out to the same number, and a rename shows as no change at all.
- Toolkit dirs and creds **do** carry secrets by design (hot-swappable machines) — only
  ever run this across fully-trusted hosts you own. Never point it at a shared/prod host,
  and never at a host on the other side of a trust boundary (that's the export/import pair).
- **Deleting anything means deleting it on every host in one pass** — and the same trap applies
  to `ssh` config, since `aliases` unions Host blocks: a stanza removed on one host is
  re-appended from any peer that still has it. **Never pin a `HostName` IP for a fleet host**;
  the DNS name is authoritative, and a pin turns a healthy host into a phantom unreachable one
  the moment its lease moves.
- **One SSH per host, not one per item.** A burst of fresh connections trips sshd's `MaxStartups`
  and the host starts dropping them — which presents as `Connection timed out during banner
  exchange` and reads exactly like a wedged or powered-off machine. It is self-inflicted and it
  clears on its own once the burst stops. Batch the work into a single remote script rather than
  looping `ssh` per file, and if a host suddenly goes unreachable mid-run, **wait before
  concluding anything about the host** — re-storming it is what keeps it down.
- **`creds` needs ≥2 SSH-reachable hosts and never counts the host it runs on** (it ssh's to
  every host including local, so the hub always fails its own probe). With one peer down the
  fleet drops to a single live peer and creds aborts before doing anything — a clean skip, not a
  partial apply. A per-target miss also does **not** fail the exit code, so confirm with a
  follow-up `creds --dry-run` and check for `[create]` lines; `refresh(identical-or-overwrite)`
  lines are no-ops that always print.

- **Scripting the remote side?** Project dirs begin with a hyphen (`-home-user-proj`), so use
  absolute paths or `--` and check exit status; never `ssh` inside `while read`. Read
  `references/remote-shell-traps.md` before writing the loop.
- `creds` needs passwordless sudo on every live host; `--dry-run` inventories by name only.
- Not a daemon. Re-run after meaningful changes, or wrap step-by-step in `/loop`.
