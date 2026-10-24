---
name: k8s-triage
description: Diagnoses a broken Kubernetes cluster from kubectl. Use when a workload/pod/cluster problem is reported, something won't come up or start, a pod is crashing/pending/stuck (CrashLoopBackOff, ImagePullBackOff, OOMKilled, Pending, Terminating), a Service has no endpoints, storage is broken, or a node is NotReady.
---

# k8s-triage

BLUF: Find the not-healthy pods, read their state, and follow the state to its fix. Most homelab breakage is one of: a scheduling/storage blocker, a bad image ref, an app crash, or an unhealthy operator. Diagnose before touching anything.

If the cluster is Talos-based (node-level: kubelet down, etcd, machine config) see the **talos-ops** skill. If workloads are Flux/GitOps-managed, see **flux-gitops** — do NOT hand-edit live objects Flux owns; it will revert them (use suspend/apply/resume for temp changes).

## First-move loop

**Sweep on READY, not STATUS.** A pod can sit `Running` at `1/2` ready — the readiness failure
removes it from its Service's EndpointSlice, so the app is **completely unreachable** while every
status-based check reports it healthy. Filtering on `STATUS != Running` misses exactly the outages
that are hardest to spot.

```bash
# not-ready OR not-running — catches 1/2 Running, which the status filter hides
kubectl get pods -A --no-headers | awk '{split($3,r,"/"); if (($4=="Running" && r[1]!=r[2]) || ($4!="Running" && $4!="Completed")) print}'

kubectl get pods -A | grep -vE 'Running|Completed'          # status-only: use as a SECOND pass
kubectl describe pod <pod> -n <ns>                          # events + state, read bottom-up
kubectl logs <pod> -n <ns> [-c <container>]                 # app output
kubectl logs <pod> -n <ns> --previous                      # crashloop: the crash before the restart
kubectl get events -A --sort-by=.lastTimestamp | tail -40  # cluster-wide recent events
```

`describe` Events and `--previous` logs are where the answer usually is. Note the pod's STATUS column and jump to the matching section below.

**Column indices are per-resource-kind — re-check them, don't carry them over.** The awk idiom above
is correct for pods (`-A` → `$3`=READY, `$4`=STATUS), but jobs are laid out differently
(`$3`=STATUS, `$4`=COMPLETIONS), and dropping `-A` shifts every index by one again. Reusing the pod
indices on jobs silently matches the wrong column: it prints `Complete` rows as though they failed,
and the mirror case — a filter that *excludes* on the wrong column — reports a **false clean**.
Print one raw row and count the fields before trusting any positional filter.

**Sweep finished workloads separately; a failed CronJob is invisible in a pod sweep.** Its pods are
garbage-collected by the history limits, so backups can be broken for weeks with nothing not-Running
to show for it.

```bash
kubectl get jobs -A --no-headers | awk '$3=="Failed"'      # $3 is STATUS *for jobs*, see above
kubectl get cronjobs -A                                    # LAST SCHEDULE stale => not firing at all
```

A `Failed` job is only a live problem if the *latest* run also failed — check the history before
acting, since one-off failures self-resolve and their records linger:
`kubectl -n <ns> get jobs --no-headers --sort-by=.metadata.creationTimestamp | grep <name> | tail -4`.

## Pod states → meaning → fix direction

- **Pending** → unschedulable. `kubectl describe pod` shows why:
  - Insufficient cpu/memory → `kubectl describe node` (Allocatable vs Allocated), free capacity or lower requests.
  - No node matches → nodeSelector/affinity/taints; `kubectl get nodes --show-labels`, check taints vs pod tolerations.
  - Unbound PVC → storageclass missing, no provisioner, or storage backend down (see Storage).
- **ImagePullBackOff / ErrImagePull** → wrong image/tag, private registry needs an `imagePullSecret`, or registry unreachable. Confirm the exact image ref and pull it manually from a node.
- **CrashLoopBackOff** → app starts then exits. `logs --previous` first. Then: bad config/secret/env, a failing liveness probe restarting a healthy app (see **A probe killed a healthy pod** below), or a missing dependency (DB/cache not up yet).
- **CreateContainerConfigError** → a referenced ConfigMap or Secret (or a key in one) doesn't exist. `describe` names it; `kubectl get configmap,secret -n <ns>`.
- **Init:0/N or Init:CrashLoopBackOff** → an initContainer is failing or its dependency isn't ready (often waiting on a Service/DB). `kubectl logs <pod> -c <init-container> -n <ns>`.
- **An init container that "fixes" startup (removes a stale lock, repairs state) only runs when the pod is created.** A crash restarts just the app container, so the fix never runs again and the pod crash-loops indefinitely on exactly what the init container was meant to clear. Deleting the pod "fixes" it once. The durable fix is to run the cleanup in the app container's own `command` before `exec`-ing the image entrypoint.
- **OOMKilled** → `kubectl describe pod` → Last State: OOMKilled. Raise the memory limit or fix the leak; a limit far below real usage causes this.
- **Terminating (forever)** → stuck finalizer or the node is gone. Check the node; inspect `.metadata.finalizers`. Force delete only when you know the object is truly dead: `kubectl delete pod <pod> -n <ns> --grace-period=0 --force`.
- **ContainerCreating (stuck)** → usually volume mount (PVC not bound, CSI unhappy) or CNI failing to assign an IP; check `describe` events and the CNI/storage pods.

## Storage / PVC

```bash
kubectl get pvc,pv -A
kubectl describe pvc <pvc> -n <ns>
kubectl get storageclass
```

- Pending PVC → no StorageClass / no default / provisioner pod down. Everything stateful stalls until storage is healthy.
- `FileSystemResizePending` → expansion queued; often clears on pod restart if the SC allows expansion.
- The storage operator itself is the common root cause — Rook/Ceph, Longhorn, or local-path. If its pods are unhealthy, all stateful workloads are down; fix the operator first (see Operators). Past first triage, storage is `k8s-storage-ops`.

## Networking

- **Readiness without liveness turns a transient stall into an unbounded silent outage.** A pod with a readiness probe but *no* liveness probe is never restarted when it wedges — it just drops out of its Service forever, reporting `Running`. If you find a wedged pod that recovers on a delete, check whether it has a liveness probe at all; adding one is the actual fix, not the restart.
- **Service with no Endpoints** → selector doesn't match pod labels, or the pods aren't Ready (readiness probe failing). Check both:
  ```bash
  kubectl get endpoints <svc> -n <ns>
  kubectl get pods -n <ns> --show-labels        # compare to the Service .spec.selector
  ```
- **DNS** → CoreDNS. Check `kubectl get pods -n kube-system -l k8s-app=kube-dns` and its logs.
- **Ephemeral debug pod** (in-cluster resolution/connectivity):
  ```bash
  kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -- bash
  # then: nslookup <svc>.<ns>.svc.cluster.local ; curl <svc>.<ns>:<port>
  ```

## Node health

```bash
kubectl get nodes -o wide
kubectl describe node <node>        # Conditions + Allocated resources
```

- Conditions to watch: `DiskPressure`, `MemoryPressure`, `PIDPressure` (evictions/unschedulable), `NetworkUnavailable`.
- **NotReady** → kubelet, CNI, or container runtime on that node. On Talos, node-level debugging is talosctl territory — see **talos-ops**.

## A probe killed a healthy pod

The most-missed cause of restarts: the process was **fine**, and the kubelet killed it because a probe
timed out — `timeoutSeconds` defaults to 1s and charts routinely leave it unset. Establish which one
it was (probe vs. app exit) before diagnosing anything else: see
`references/probe-kills-healthy-pod.md`.

## OOMKilled: the container's own limit, or the whole node?

**Pod status cannot tell you which** — a node-level kill and a container hitting its own limit both
show `OOMKilled`, exit 137, and misattributing one as the other has already taken out unrelated pods
on the same node. Attribute via cgroup `memory.events` / node `SystemOOM` before diagnosing the app:
see `references/oomkilled-attribution.md`.

## Right-sizing requests and limits

When Pending-on-capacity or OOMKilled keeps recurring, stop guessing and size from measured usage —
this is a deep dive owned by the **k8s-resource-sizing** skill (the P95-request / asymmetric-limit
rule, PromQL gotchas, and the measurement traps). Load it rather than re-deriving numbers here.

## Operators / CRDs

Many homelab failures are an operator being unhealthy, not the workload: cert-manager, CloudNativePG (CNPG), external-secrets, ingress controllers, storage operators.

1. Check the operator's own pods/logs in its namespace.
2. Check the custom resource `.status` — that's where the operator reports why it's stuck:
   ```bash
   kubectl get <crd-kind> -A
   kubectl describe <crd-kind> <name> -n <ns>     # read .status conditions
   ```
   e.g. Certificate/CertificateRequest (cert-manager), Cluster (CNPG), ExternalSecret (external-secrets). A degraded operator cascades into confusing downstream pod failures — check it before chasing the symptom. Per operator: `cnpg-postgres-ops` (CNPG), `k8s-ingress-tls` (cert-manager, ingress), `k8s-secrets` (external-secrets, SOPS).

**`kubectl` itself refused** ("You must be logged in to the server", "certificate has expired") is an expired admin cert, not a cluster fault: `cluster-cert-renew`.

## GitOps caveat

If Flux manages the object, don't `kubectl edit` it — reconciliation reverts your change and hides the real state. Diagnose read-only here; make changes through the flux-gitops flow (suspend/apply/resume for temporary, git commit for permanent). See **flux-gitops**.
