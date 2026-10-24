---
name: cnpg-postgres-ops
description: Operates and recovers a CloudNativePG (CNPG) PostgreSQL cluster. Use when operating or recovering a CloudNativePG PostgreSQL cluster — a CNPG cluster is down, degraded, out of disk, or needs backup/restore/replica work.
---

# CNPG PostgreSQL Operations & Recovery

CNPG runs PostgreSQL as a `Cluster` CR: one primary + N replicas, each instance backed by its own PVC.
Install the `cnpg` kubectl krew plugin (`kubectl krew install cnpg`) — it is the main operational tool.

## First move: inspect

- `kubectl cnpg status <cluster> -n <ns>` — instances, roles (primary/replica), health. Add `--verbose`.
- `kubectl get cluster -n <ns>` — high-level ready count and phase.
- `kubectl cnpg report cluster <cluster> -n <ns>` — full dump for deep triage.
- `kubectl cnpg logs cluster <cluster> -n <ns>` — aggregated instance logs.

## THE classic homelab failure: WAL archiver → full PVC

Symptom: instances `0/N` ready, primary `CrashLoopBackOff` with "Not enough disk space",
`pg_stat_archiver.failed_count` climbing.

Cause: a WAL archiver (barman-cloud / barman-cloud-plugin) points at an object-store endpoint that
does not exist yet or is down. Archiving fails silently for days, so Postgres never recycles WAL,
`pg_wal` fills the instance PVC, and CNPG **halts Postgres on low disk to protect data. Data is NOT lost.**

Recovery (in order):
1. **Disable/fix the WAL archiver** so WAL recycles again. With no archiver plugin configured, CNPG's
   `wal-archive` no-ops and returns success, so `failed_count` drops to 0 and WAL is freed.
2. **Expand the PVC** — requires a StorageClass with `allowVolumeExpansion: true`. Bump the cluster's
   `storage.size` (via git if GitOps-managed, see below). **If the cluster is already in the
   disk-full phase, bumping `storage.size` alone does nothing:** the operator's
   `ensure_sufficient_disk_space` check returns early ("cannot proceed until the PVC group is
   enlarged") before the step that would enlarge it. Patch each instance PVC's
   `spec.resources.requests.storage` to the new `storage.size` yourself; the instance starts once
   the filesystem grows.

Disk-full is not always WAL. Before blaming the archiver, `du` `pg_wal` against `base/`; if `base/`
holds the space, it is table growth (e.g. date partitions that something should drop and doesn't),
and a bigger disk only resets the clock.

### CRITICAL PVC-resize gotcha
Do **not** delete a CNPG pod while its PVC is mid-resize. It strands the PVC in
`FileSystemResizePending` with no mount; CNPG logs "PVC resizing without a pod, classifying as
dangling" and refuses to attach a pod.
Fix: briefly mount the stranded PVC in a throwaway `sleep` pod so the CSI driver completes the online
filesystem grow, delete the throwaway pod, then let CNPG reconcile and reattach.

## Stuck replica blocking reconcile

A replica that never finishes its base backup can monopolize CNPG's reconcile loop and block primary
recreation. Remove the specific dead instance:

```
kubectl cnpg destroy <cluster> <instance-number> -n <ns>
```

**DESTRUCTIVE — confirm the instance number first.** CNPG then recreates the instance / primary and
performs clean crash recovery. (Plugin flags go after the plugin name: `kubectl cnpg destroy ...
--context <ctx>`. Putting `--context` before `cnpg` is rejected.)

**Set `primaryUpdateMethod: switchover` on every multi-instance cluster.** The default is `restart`:
any spec change (resources, parameters, image) updates the replicas, then restarts the primary *in
place*, so there's no writer for minutes (measured ~3 min). `switchover` promotes an updated replica
first. Put it in the shared base before a fleet-wide resource change, or that change becomes a
fleet-wide write outage. What the resources should be (`shared_buffers` against container memory) is
`k8s-resource-sizing`.

**A switchover swaps which POD is primary, so never address an instance by pod name.** A read-only
"query the replica" helper that exec'd into `postgres-1` by name kept working after a switchover,
silently, against the new PRIMARY: full-table scans meant for the replica ran on the database
serving production traffic for an hour before anyone noticed. Select by label
(`-l cnpg.io/cluster=<c>,cnpg.io/instanceRole=replica`), refuse to run if none matches, and assert
`pg_is_in_recovery()` is true before trusting that a probe is off the primary.

**A Postgres parameter is only validated by Postgres, at the next restart.** Render, server-side
dry-run and a CI gate all accept `wal_compression: lz4` on a cluster still on an older Postgres major. That major wants a boolean
(lz4/zstd arrived in 15), so each instance refuses to start at its next restart ("requires a
Boolean value" → `custom.conf contains errors`), not when the change is applied. Before changing
a shared-base parameter, check it against the OLDEST major version among the consumers, and read
it back with `show <param>` on a restarted instance of that version.

**Failed Backup objects are never deleted.** The barman-cloud plugin's `retentionPolicy` deletes
completed Backup objects along with their data, but failed ones stay until the Cluster is deleted.
An hourly schedule (six-field cron is seconds-first: `"0 10 * * * *"` is hourly) that fails for a
while leaves thousands in the apiserver. Deleting a Backup object doesn't touch object-store data,
since they carry no finalizer.

**Scaling `instances` down removes the highest-numbered replica, not the broken one.** With a
crash-looping replica present, lowering `instances` would delete a healthy one and keep the broken
one. The operator may also refuse to reconcile at all ("error while interacting with plugins").
Destroy the broken instance first, and the cluster then settles at the new count. A replica
crash-looping on `PANIC: could not locate a valid checkpoint` has a corrupt data directory. It will
never recover on its own, so destroy it.

## Temporary recovery levers vs. permanent changes

- Temporary levers during recovery (e.g. `spec.instances: 1` to isolate the primary): if the cluster
  is Flux/GitOps-managed, do **not** commit the temp change. Suspend Flux, apply the change live,
  resume Flux afterward (see the flux-gitops skill).
- Permanent changes (PVC `storage.size` bump, archiver config) go through **git**, not live edits.

## Backups — the right posture

- Use a `ScheduledBackup` + an object store (barman-cloud / barman-cloud-plugin) or a tool like k8up.
- Keep backup/archiver config **dormant or suspended until the backup target actually exists.**
  Pointing WAL archiving at a nonexistent endpoint is exactly what causes the WAL-fill failure above.
- Restore is a fresh `Cluster` with `bootstrap.recovery` sourced from a backup or the object store.
  With the barman-cloud plugin: `externalClusters` gets a plugin entry (`barman-cloud.cloudnative-pg.io`,
  `barmanObjectName`, and `serverName` = the live cluster's archive name, which may differ from its
  `metadata.name`); pin `recovery.backupID` to the backup you mean.
- **A restore straight after an on-demand backup taken on a replica can fail** with `WAL ends before end of
  online backup`: a replica can't force a WAL switch, so the backup's `endWal` isn't archived yet. Before
  restoring, check `pg_stat_archiver.last_archived_wal` on the primary is at or past the Backup's
  `status.endWal`; if behind, wait (or `SELECT pg_switch_wal()` on the primary).
- Say `backups.postgresql.cnpg.io` / `clusters.postgresql.cnpg.io` in full: a bare `kubectl get backup`
  can resolve to another operator's CRD (e.g. MariaDB's).
- Prove a backup by restoring it: counts per table, live vs restored, and the app's own consistency check
  run against the restored `-rw` service from a one-off pod. Delete the drill Cluster and its PVCs after.

## After a bulk delete: verify the batch jobs, not just the endpoints

A mass delete plus `ANALYZE` (or `VACUUM`/`REINDEX`) re-plans every query on the table. After
purging about 40% of an events table, every API endpoint timed the same or faster — and that weekend's
billing export died on a statement timeout, because a once-a-run aggregate flipped from seconds to minutes.
Endpoints get timed because users see them; a job's queries run once a day and nobody times them.
`EXPLAIN` each CronJob's heavy statements on a replica, or trigger each job once, before calling it done.

## Other ops

- Switchover / promote a replica: `kubectl cnpg promote <cluster> <instance> -n <ns>`.
- Connect via the generated services: `<cluster>-rw` (read-write / primary), `<cluster>-ro`
  (read-only replicas), `<cluster>-r` (any instance).
