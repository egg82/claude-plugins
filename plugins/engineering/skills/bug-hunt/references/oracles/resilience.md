# Resilience oracles — the world misbehaves on purpose

Load when the target talks to a network, runs unattended (a job, a worker, a sync, a CronJob), restarts, or keeps state
across restarts. Local harnesses run on a perfect machine — localhost never drops, the disk never fills, the process is
never killed mid-write — so every defect here is invisible to a hunt that doesn't inject the fault. The oracle is the
fault itself: inject it, then check the system returns to a correct state and says what happened. Proof is the
injected fault and the observed wrong state, scripted so it reruns.

## Faults to inject

- **Dropped and failed requests.** Fail one outright, time one out, cut the connection mid-response, go offline and
  come back, answer a 502 (a deploy gap) — on a write, a poll and a page load. The UI returns exactly to its prior state
  or retries, says so plainly, never shows an unsaved value as saved, never doubles a write on retry, and recovers
  without a manual reload. Tell: a `catch` that toasts but leaves optimistic state in place. Round trips under delay
  are `performance.md`.
- **Process killed mid-operation.** `kill -9` during a write, a migration, a batch, a file save. Is the state
  half-written (a truncated file not written to a temp and renamed, a batch committed per row with no resume
  marker)? Does the next start notice and repair, or build on the wreck?
- **Restart and replay.** Run the job twice, or restart it mid-run. A job that is not idempotent double-sends,
  double-charges or duplicates rows; a restart burst (every pod starting at once against one upstream) trips rate
  limits that a single start never sees. Tell: state that lives only in the process (an in-memory cursor, a dedupe
  set) for work that must survive the pod.
- **A dependency down or slow.** Database unreachable at boot, an upstream API hanging rather than refusing. Every
  outbound call has a timeout (the default in many HTTP clients is none); a retry has backoff, jitter and a cap; a
  circuit or fallback doesn't cache the failure as a value. Tell: a worker pool whose every thread is blocked on one
  dead upstream.
- **An upstream returns empty or garbage.** *(incident)* A metadata refresh pruned ~138 records when its upstream
  returned an empty list. Any sync that deletes what the source no longer lists needs
  a sanity floor; hunt for the ones without.
- **Resources run out.** Disk full during a write, a file-descriptor limit, memory at the container limit (an OOMKill
  reads exactly like the app's own ceiling — `k8s-triage`), a connection pool exhausted by one slow path.
- **The clock moves.** NTP steps backwards, DST, a host far ahead or behind its peers, a token expiry checked with wall
  time on one host and issued on another. Scheduled work across a DST change runs twice or not at all.
- **Shutdown.** `SIGTERM` handled: in-flight work drains or is handed back, the readiness probe fails before the
  listener closes, the job does not exit 0 having done half.

## Operability — does the system say what happened?

A failure nobody can see from the logs is a second defect on top of the first. After each
injected fault, read the logs as the person paged at 3 a.m. would.

- A run that leaves no start and finish line with counts and duration, or an empty log after a run, is a defect.
- A swallowed failure (fallback taken, retry, cache treated as a miss) that logs nothing.
- A log line that disagrees with the condition it sits under (the correctness differential, in the logs).
- Health checks that cannot fail: a liveness probe that returns 200 while the worker thread is dead, a readiness probe
  that passes before migrations finish.
- Alerts and dashboards that render a missing measurement as a healthy value: unknown must render differently from zero or OK (`grafana-dashboards`).

## Deploy configuration

For Kubernetes and Compose targets, the manifest is code with its own defects: no resource requests, or limits far
from measured use (`k8s-resource-sizing`); probes pointed at an endpoint that doesn't exercise the dependency; a single
replica with a PodDisruptionBudget that blocks every drain; a `latest` tag; a volume a restart wipes holding state the
app treats as durable; a CronJob with `concurrencyPolicy: Allow` for work that must not overlap.

## Backups

A backup is proven only by a restore. Find the backup job, restore its newest output into a scratch instance, and
compare row counts or hashes with the source. A backup job that has run green for months over an empty or wrong path
is a common, silent, high-impact find.
