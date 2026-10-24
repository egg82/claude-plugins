# A probe killed a healthy pod

The most-missed cause of restarts: the process was **fine**, and the kubelet killed it because a probe
timed out. `timeoutSeconds` defaults to **1 second**, and charts routinely leave it unset — so a
container that answers its health endpoint in 20ms normally has a 1s budget, and under node I/O
pressure it misses it. Everything about the symptom points at the application, which is why this gets
diagnosed as an app bug over and over.

**Establish which one it was before diagnosing anything else — the container either failed or it was
killed:**

- `exit 143` (SIGTERM), or `exit 0` with `Reason: Completed`, **plus** `Unhealthy … Timeout exceeded`
  in `kubectl describe pod` events → the **probe**. Stop reading application logs.
- A non-zero exit the app itself chose, with no `Unhealthy` events → the app. Carry on.

A generous `initialDelaySeconds` does not protect you and is not evidence either way. Exec probes are
not exempt from this either — a tight exec-probe budget can kill a slow-but-healthy exec just as
easily as an HTTP probe.

**The driver is per-node I/O pressure, not CPU or memory** — which is why the usual `describe node`
resource view looks fine. Read PSI, per cgroup slice:

    talosctl cgroups --preset psi          # Talos
    cat /proc/pressure/io                   # any node, whole-node view

Compare a suffering node against an idle one. When the kubelet itself starts failing its own health
check (`127.0.0.1:10248`), that is the same pressure, and it tends to track the source node's pod
restart counts closely.

**Check `status.qosClass` rather than the container spec.** A pod whose container declared both
requests and limits can still land in `BestEffort` if the resources weren't present at admission
time — the pod spec you read and the QoS class the kubelet enforces are two different facts, and
BestEffort gets no I/O protection at all.

**The fix is on the probe, not the app.** Set `timeoutSeconds` explicitly — around 10 for anything
sharing a node with I/O-heavy work — and only then look at whether the workload also needs requests it
is not getting. Raising the timeout is not papering over a problem: a 1s default is a claim that a
healthy response is always sub-second, which on a shared node is not true.
