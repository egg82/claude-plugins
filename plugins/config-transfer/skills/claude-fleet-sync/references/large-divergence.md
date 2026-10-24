# Step 3 helpers for a large divergence

Open this when step 3 has many diverging files — more than you would `pull` one at a time.

To fetch MANY peer copies side-by-side without touching the hub at all, batch them into
one `tar` over the ControlMaster `sync.py` already opened — and use the **FQDN plus the
same `ControlPath`**, not the short ssh alias. `ssh <short-alias>` is a *different* connection
as far as the master socket is concerned, so it re-authenticates from scratch and fails
`Permission denied (publickey…)` on a fleet that only ever authenticates through the
master. That reads like a broken host; it is the wrong socket.

```bash
CP="$HOME/.ssh/cm-%r@%h:%p"
SSHO=(-o BatchMode=yes -o ControlMaster=auto -o "ControlPath=$CP" -o ControlPersist=300)
ssh "${SSHO[@]}" <host>.<fqdn> "cd ~ && tar czf - -T -" < paths.list > /tmp/peer.tgz
```

**Triage a large divergence by ancestry before reading anything.** Hash each diverging peer
copy and look it up in the hub's own backup history (`~/.claude/backups/reconcile-pre-*.tgz`,
nightly): a peer copy byte-identical to something the hub once held is a stale ancestor, so the
hub's edits since are deliberate and it needs no reading. One run cleared 91 of 133 this way.
The tarballs are rooted at `.claude/` (`skills/…`, not `.claude/skills/…`) — key the lookup
wrongly and every file reads NOVEL, so check that a known-stale file comes back ANCESTOR.
`hooks/` and `rules/` are not in the backup, so they always read NOVEL; diff those by hand.

**Sort a cross-host hash manifest by path with `LC_ALL=C sort -k2` on both sides before comparing.**
`find … | sort` collates by the host's locale, so identical trees on two hosts list files in a
different order and every directory diffs as DIFFERS with the same hashes on both sides of the diff.
