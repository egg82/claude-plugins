---
name: k8s-resource-sizing
description: "Decide CPU/memory requests and limits for Kubernetes workloads — before usage data exists and afterwards from Prometheus history. Use when writing or reviewing a `resources:` block, a pod is OOMKilled / CPU-throttled / Pending for resources, node memory is overcommitted, a KubeMemoryOvercommit / CPUThrottlingHigh alert fires, or asked to \"right-size\" a cluster."
---

# Kubernetes resource sizing

**If the repo has its own sizing policy doc, it wins** — it carries the cluster's node sizes and
exceptions. This is the method underneath it.

## The rule is asymmetric, because the failure modes are

| | CPU | Memory |
|---|---|---|
| exceeding the LIMIT means | throttling (latency) | OOM kill (death) |
| request | **p95 × 1.2** (floor ~5m) | **p95 × 1.2** (floor 32Mi) |
| limit | **none by default**; remove one that throttles | ≥ 1.5 × observed max; never lower one; don't add one where none exists |

- **The LIMIT absorbs the memory peak; the request doesn't need to.** A request is a scheduling
  reservation, not a cap. Going above it only makes a pod an eviction candidate once the *node*
  runs short. **Do not size requests to the window max across a fleet.** That rule (KRR's
  max + 15%, and this skill's own rule for a few hours) sums peaks that never coincide. Measured:
  every node of a small cluster hit nearly 100% requested while real use was well under 60%. Nothing new could
  schedule, the CephFS MDS stayed Pending, CephFS went down, and the ExternalSecrets admission
  webhook's own pods were Pending too, so every GitOps apply failed and the fix couldn't be
  delivered through GitOps. (VPA reportedly targets ~p90 plus a margin, which is the same idea.)
- **Before pushing a fleet-wide pass, compute the new total per node** and compare it with
  `kubectl top node`. Push it in slices, not all at once.
- **Circular dependency to know about:** if an admission webhook (external-secrets, cert-manager,
  kyverno) is itself unschedulable, any apply that touches its kind fails. Break it by applying
  only the Deployments/HelmReleases directly (`yq 'select(.kind=="Deployment" …)'`), which frees
  room for the webhook, and then let GitOps catch up.
- **No CPU limit by default.** CFS enforces a limit per 100 ms window *regardless of idle node CPU*,
  so a bursty, low-average workload is throttled while using a sliver of its limit — measured: a
  tunnel daemon at 200m limit throttled in 60% of periods while averaging 4m. Without a limit, CPU is
  shared under contention by weights derived from *requests*, which is proportional and fair. The
  widely-quoted practitioner position (attributed to Tim Hockin; Robusta/KRR default; Zalando) is
  "set memory limits, don't set CPU limits". Add a CPU limit only as a targeted guardrail after a
  specific app has actually starved neighbours.
- **A tiny CPU limit plus a liveness probe is a kill switch.** A 10m limit starved a job's startup
  until the probe (5s delay + 3 × 20s) killed it at exactly 65 s, about every other run — a failure
  that looks like flakiness. Duration-equals-probe-arithmetic is the tell.
- **Guaranteed QoS (request == limit)** for anything whose kill is costly — databases especially
  (CloudNativePG recommends it). Burstable (limit > request) for things with real variance.

## Before there is data

Size from what the app declares about itself, then correct from measurement within a week:

1. **It has its own memory ceiling → use it.** JVM (`-Xmx` / `MaxRAMPercentage`), Dragonfly/Redis
   `maxmemory`, Postgres `shared_buffers`: container memory = ceiling + 20–25% for the runtime.
   JVM default `MaxRAMPercentage=25` wastes most of a small container; 75–80% of the **limit** is the
   usual convention. Set JVM/Node heap flags against the limit, not the host (Node needs
   `--max-old-space-size` explicitly).
   **A ceiling can have a floor tied to CPU count.** Dragonfly needs ≥256MiB per io thread and
   defaults to one thread per *node* CPU, so `--maxmemory=512MiB` on a many-core node exits on
   start ("16 threads, so 4.00GiB are required"). Pin `--proactor_threads` along with the cap.
2. **Postgres (CNPG):** `shared_buffers` ≈ 25% of container memory (apply it without a write outage:
   `cnpg-postgres-ops`, `primaryUpdateMethod: switchover`). `work_mem` is not derivable from
   container size (× connections × concurrent sorts) — a tuning knob, not a sizing input.
3. **Idle Go daemons / sidecars / proxies / CSI plugins / operators:** 32–64Mi, 10–25m. Chart
   defaults on these run 5–10× high, and they are usually per-node DaemonSets, so the error
   multiplies by node count — **the biggest reclaims are defaults nobody chose, not app tuning.**
4. **Batch jobs:** guess memory 2–3× high; their peak is what monitoring can't see (below).
5. **Chart defaults are someone else's cluster** — many ship none at all (BestEffort by design),
   others are tuned to the author's environment. Placeholder, not sizing.

## Once there is data

- Measure per **workload**, not per pod — collapse ReplicaSet/Job/StatefulSet pod names to their
  owner and take the max across pods, or churned pods fragment the picture.
- Useful series (kube-prometheus recording rules):
  `node_namespace_pod_container:container_memory_working_set_bytes`,
  `node_namespace_pod_container:container_cpu_usage_seconds_total:sum_rate5m`,
  `kube_pod_container_resource_{requests,limits}`, and throttle ratio
  `increase(container_cpu_cfs_throttled_periods_total[w]) / increase(container_cpu_cfs_periods_total[w])`.
  Use `quantile_over_time(0.95, …[w])` and `max_over_time(…[w])` over the full retention window.
- **Filter to material changes** (e.g. >30% and >64Mi, or >2× and >25m) — a pass that touches every
  manifest by 10% is churn with restarts attached.
- **Re-check about weekly**; a 10-day retention window is about the longest view you get anyway.
- **VPA in `Off` mode + Goldilocks** (dashboard) or **KRR** (one-shot CLI) implement this without
  hand-written PromQL. If VPA is used, set `controlledValues: RequestsOnly` and consider
  `controlledResources: ["memory"]` so it never reintroduces a CPU limit.

**Before raising a memory limit for an app you own, ask whether that memory belongs on disk.** A limit raise
treats state the app chose to hold as a fixed cost. Measured: an image service's limit went from
512Mi to 768Mi to keep generated thumbnails (~150 KiB each, never changed once made) that a volume would
serve at near-memory speed, and nobody revisited the deployment's shape (an emptyDir or cache PVC kept out of
backups) until the owner asked. Inventory what is held, then pick memory, disk or recompute per store.

## Honest requests expose the real fill — plan for it

Right-sizing tends to *raise* total requests (the under-requested tail was hiding load), and
nodes that looked half-empty can read close to fully requested. Two follow-ups are then needed:

- **The descheduler's default `LowNodeUtilization` goes inert.** It uses ABSOLUTE thresholds
  (<20% under, >50% over); once every node is above 20% nothing counts as under-utilized and it
  never evicts. Set `useDeviationThresholds: true` (±10 points from the mean). Also check the
  chart's `PodsWithPVC` protection. It exempts most stateful apps even when their RBD/NFS volumes
  move freely. With `nodeFit: true`, pinned pods stay where they are anyway. And the descheduler
  never helps a **Pending** pod: it only rebalances running ones.
- **Pods pinned to one node (local PV + hostname nodeSelector) go Pending when that node fills.**
  Give them a PriorityClass above ordinary workloads (below storage daemons) so the scheduler
  *preempts* a movable pod instead of waiting for a human.

## Measurement traps (each produced a confident wrong number)

- **Short jobs are undersampled.** A 30 s scrape misses a peak shorter than a few samples, so the
  measured max is a floor, not the peak. **Never lower a Job's memory from scraped data.** Raise from
  OOM history, or read `memory.peak` from the cgroup during one real run.
  `container_memory_max_usage_bytes` is frequently zero on cgroup v2 (cadvisor #3515) — don't rely on it.
- **A crash-looping pod pollutes its own numbers** (repeated startup spikes). Size after the fix.
- **An aggregate max across a workload includes its sick replica.** A corrupt replica crash-looping
  inflated a database's measured memory; check per-pod before trusting an outlier.
- **Static control-plane pods** (kube-apiserver etc.) show up in the data but are set by the node OS
  config (Talos/kubeadm; `talos-ops`), not the GitOps repo — and their understated requests are often the largest
  single distortion in a node-overcommit alert. The apiserver commonly uses GBs on a node sized for
  far less.
- **`kube_pod_container_resource_*` is configuration, not usage.** Don't compare two config series
  and call it utilisation.
- **An overcommit alert that compares against "capacity minus the largest node"** is dominated by
  one oversized node; a cluster can be honestly sized and still fire it. Read what it computes before
  cutting requests to silence it.

## Sources

KRR recommender defaults — docs.robusta.dev (resource-recommender) and robusta-dev/krr README ·
"Stop using CPU limits" — home.robusta.dev/blog · QoS classes — kubernetes.io/docs/concepts/workloads/pods/pod-qos ·
CNPG resource management — cloudnative-pg.io/documentation/current/resource_management ·
VPA `controlledValues`/`controlledResources` — kubernetes/autoscaler docs/api.md, GKE VPA docs ·
JVM container awareness — developers.redhat.com · cadvisor issue #3515 · chart-default inconsistency — bitnami/charts #11555.
