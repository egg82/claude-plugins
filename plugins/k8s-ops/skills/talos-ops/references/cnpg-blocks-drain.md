# A single-instance CNPG cluster blocks a drain

`talosctl upgrade` drains by default, and a **1-instance CNPG cluster can never be
drained**: CNPG creates a `postgres-primary` PDB with `minAvailable: 1`, so the sole
primary reports 0 allowed disruptions and eviction blocks until `--drain-timeout`
expires. Find them at drain time rather than from a list —
`kubectl get clusters.postgresql.cnpg.io -A -o jsonpath='{range .items[?(@.spec.instances==1)]}…'`
— because the set changes (a deleted one reschedules onto a not-yet-drained node, so it
moves once per remaining node in a rolling reboot).

**Why:** the failure is silent and expensive — the drain burns its whole timeout, the
upgrade never runs, and the node is left **cordoned**. That cordon then cascades: its
Rook OSD goes Pending (OSDs are node-pinned), and any RBD volume still mapped on the
node keeps its exclusive lock, stranding pods elsewhere in `ContainerCreating` with
Multi-Attach errors.

**How to apply:** before draining a node, delete any single-instance CNPG primary pod
sitting on it — deletion bypasses the PDB and CNPG rebuilds it on another node reusing
the same RBD PVC. Gate each node on *all pods Running*, not just `ceph pg stat` clean;
the PG check passes while pods are stranded. If an upgrade does abort, **uncordon the
node first** — that alone recovers the OSD and lets the leaked RBD map release. Never
force-delete a `VolumeAttachment` to clear a Multi-Attach error without checking
`rbd status <pool>/<image>` first: a live watcher/exclusive lock means the image is
still mapped and deleting the attachment risks corruption.

**Never put a "PGs active+clean" gate between drain and uncordon.** The drained node's own
OSD cannot run while it is cordoned, so the gate can never pass — it holds the cordon, and
on pools with a single replica that is a data outage (`stale` PGs, blocked client I/O) for the gate's whole
timeout. Measured: 22 minutes, from re-running a gated script against a node an earlier
failed attempt had left drained. Gate only before the cordon and after the uncordon, and
keep drain → reboot → uncordon back-to-back.
