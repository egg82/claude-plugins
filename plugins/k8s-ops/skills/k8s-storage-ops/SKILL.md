---
name: k8s-storage-ops
description: Diagnoses and fixes homelab Kubernetes persistent storage. Use when a PVC won't bind, a pod is stuck ContainerCreating on a volume, a storage operator (Rook-Ceph/Longhorn) is unhealthy, volume expansion is stuck, or stateful workloads are down.
---

# k8s-storage-ops

BLUF: If anything stateful is broken, **check the storage operator/CSI health FIRST** — a sick provisioner takes down every PVC-backed workload at once. Fix the operator, then the PVCs, then the pods. This is the deep dive the [k8s-triage] skill defers to. For Postgres-specific volume issues see [cnpg-postgres-ops].

## The storage stack
`StorageClass` → **provisioner (CSI driver)** → `PV` dynamically provisioned + **bound** to a `PVC` → **mounted** into a pod. In a homelab the provisioner is usually one of:
- **Rook-Ceph** — distributed; block (`rbd`), shared filesystem (`cephfs`), and object. Replicated across nodes/disks. Most moving parts.
- **Longhorn** — replicated block, per-volume replicas across nodes, has a UI.
- **local-path** (Rancher) — single-node, data pinned to one node's disk, no replication. Fine for non-critical; not HA.

## PVC / PV triage
```
kubectl get pvc,pv -A
kubectl describe pvc <name> -n <ns>     # provisioner events live here
kubectl describe pod <name> -n <ns>     # FailedMount / FailedAttachVolume
```
- **PVC Pending** = no matching StorageClass, no default StorageClass set, provisioner pod not running, or backend out of capacity. `describe pvc` shows the provisioner's event/error.
- **Pod ContainerCreating** with `FailedMount` / `FailedAttachVolume` = CSI attach/mount problem, not a binding problem. The PV is bound but the node can't attach/mount it → read the **CSI node plugin (nodeplugin) logs** on that node's DaemonSet pod.
- No default StorageClass? A PVC with no `storageClassName` stays Pending forever. Check `kubectl get sc` for the `(default)` marker.

## Volume expansion (grow only)
1. StorageClass must have `allowVolumeExpansion: true` (can't be added retroactively to already-provisioned volumes on some drivers — verify).
2. Edit the PVC's `spec.resources.requests.storage` **up**.
3. Watch `kubectl describe pvc` for `FileSystemResizePending`. Online resize completes when a **running pod has the volume mounted** — a PVC with no consumer pod gets stuck in `FileSystemResizePending`; briefly mount it in a throwaway pod to finish the filesystem grow.
- **Shrinking is not supported.** Migrate to a smaller volume manually instead.

## A rollout that never completes — check the access mode first

**A single-replica Deployment with a ReadWriteOnce PVC and the default `RollingUpdate` strategy
can never roll.** The surge pod schedules onto another node and waits for a volume the outgoing
pod still holds; the outgoing pod waits for the new one to become Ready. It sits there
indefinitely. The fix is `strategy.type: Recreate` (Helm charts usually expose this, e.g.
`grafana.deploymentStrategy.type`); clearing an existing jam needs the old pod deleted once.

Two things make this hide. A Helm upgrade fails with `timeout waiting for … status: 'InProgress'`,
which reads like slowness rather than a deadlock. And if anything `dependsOn` the stuck release,
**that** dependent is what shows as broken — the real fault can be two hops from the error you're
looking at. An otherwise-identical cluster whose PVC happens to be RWX is unaffected, which makes
it look environment-specific rather than structural.

On any stuck rollout, check `spec.strategy.type` against the PVC's `accessModes` before anything
else, and confirm with `kubectl get volumeattachment` — one attachment, pinned to the *old* pod's
node.

## StatefulSet volumeClaimTemplates: immutable, and silently ignored

**Editing the template does nothing to existing PVCs, and nothing errors.** A repo can declare
`10Gi`/`fast-class` while the live PVCs remain `5Gi`/`some-older-class` from months earlier. The
drift surfaces much later as `no space left on device` in whatever the volume backs. Whenever a
StatefulSet's storage is edited, **check the live PVCs against the declared template**, not just
the template.

**And `volumeClaimTemplates` is immutable on an existing StatefulSet** — any edit, even adding a
PVC annotation, fails with `updates to statefulset spec for fields other than 'replicas',
'ordinals', 'template', … are forbidden`, and that single failure fails the whole HelmRelease.
Converge with `kubectl delete sts <name> --cascade=orphan` (leaves the pods running), then force a
reconcile — the release goes `Stalled` and won't retry on its own. The recreated StatefulSet adopts
the running pods by label, so there's no restart.

## Rook-Ceph
Everything lives in the `rook-ceph` namespace: operator, mons, OSDs, mgr, and the CSI provisioner + nodeplugin pods.
```
kubectl -n rook-ceph get pods
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph osd status
kubectl -n rook-ceph exec deploy/rook-ceph-tools -- ceph health detail
```
Common outages:
- **OSD down** (disk failed / host gone) → `HEALTH_WARN`/`HEALTH_ERR`, PGs degraded. Cluster keeps serving if replication survives; replace the disk/host and let it backfill.
- **Mon quorum lost** → cluster hangs. Need a majority of mons up.
- **mgr OOMKilled** → bump the mgr memory limit in the CephCluster resource.
- **CSI driver pods crashlooping after an upgrade** (real gotcha): `csi-cephfsplugin` / `csi-rbdplugin` nodeplugin or provisioner pods fail because a partial CRD/RBAC upgrade left a **missing or renamed per-driver ServiceAccount / Role / RoleBinding**. Symptom: RBAC `forbidden` / `cannot get/list/watch` errors in the nodeplugin logs. Fix: restore the ServiceAccount + Role/RoleBinding the driver expects. Rook is version-sensitive — never do a half-applied upgrade; the CRDs, RBAC, and images must move together.

Reading ceph health **without creds** — execing `ceph` in the mgr pod can hit cephx keyring errors after
a restart, so prefer the CR's own status:
```
kubectl -n rook-ceph get cephcluster -o jsonpath='{.items[0].status.ceph.health}'   # plus .status.ceph.details
```

### Single node: what's normal, and the one real wedge

A single-node cluster with a few OSDs on one host **permanently** reports `TOO_FEW_OSDS` /
`HEALTH_WARN` and sits in near-constant backfill. That is normal, not a fault — don't chase it.

**The real failure mode shows up after a node reboot:** OSDs stick at `Init:0/4` for hours because
`ceph-volume raw activate` wedges in kernel **D-state** (uninterruptible — e.g. blocked in
`folio_wait_bit_common`), even though plain `dd` reads of the underlying block devices succeed. D-state
processes **cannot be killed**, so deleting or force-deleting the OSD pods does nothing except stack
another stuck process holding the device. Confirm it, then reboot:
```
kubectl -n rook-ceph exec <osd-pod> -c activate -- ps -eo pid,stat,wchan:24,args   # look for STAT=D
```
**The fix is a clean reboot of the node** — go straight there instead of bouncing pods.

## Longhorn
Namespace `longhorn-system` + UI. Each volume has replicas spread across nodes.
```
kubectl -n longhorn-system get pods
kubectl -n longhorn-system get volumes.longhorn.io
```
- **Volume Degraded** = a replica sits on a down/cordoned node. Check the `longhorn-manager` DaemonSet pods and the volume's robustness (Healthy/Degraded/Faulted) in the UI.
- Node **disk pressure** or a node marked unschedulable stops replica scheduling — Longhorn won't rebuild replicas onto a cordoned node.

## local-path
Dead simple: hostPath-style, data physically on one node's disk. A pod rescheduled to another node **loses access to its data** (a fresh empty PV, or Pending if node-affinity pins it). Acceptable for single-node / throwaway workloads; never for anything needing HA or that survives a node loss.

## Backups (not optional)
Operator replication is **not a backup** — it protects against disk/node loss, not deletion, corruption, or a bad `kubectl delete pvc`. PV data needs its own backup: Velero, VolSync, k8up, or the operator's own snapshots (Ceph RBD snaps / Longhorn backups to an S3/NFS target).

Where an app has native backups (a database operator's WAL + base backups), prefer those over volume
snapshots — a volume snapshot of a live database is a crash image, not a clean backup.

**Cluster state needs backing up too, not just git.** Git holds desired state; etcd holds the live
data (CRs, secrets, current state) that isn't in git. Snapshot it before risky operations —
`talosctl etcd snapshot` on Talos, `etcdctl snapshot save` otherwise — kept **off-cluster**, same as
the PV backups above. etcd + PV data + the repo is a complete recovery set.

**Test a restore at least once.** An untested backup is a guess.

### k8up under `restricted` PodSecurity fails silently

k8up's backup/prune/restore runner pods are rejected at admission by PodSecurity `restricted` — every
schedule fires, the Job fails `BackoffLimitExceeded`, no pod is ever created, and nothing looks
obviously broken until a restore is needed. If backups have gone quiet with no clear error, see
`references/k8up-podsecurity-restricted.md`.
