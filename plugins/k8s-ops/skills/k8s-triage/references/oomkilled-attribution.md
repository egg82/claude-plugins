# OOMKilled: the container's own limit, or the whole node?

**Pod status cannot tell you which.** A node-level kill and a container hitting its own limit both
appear as `lastState.terminated.reason: OOMKilled`, exit 137. That ambiguity has already produced a
wrong conclusion here: four probe pods of one JVM app, memory limits varied 1/2/4/8 GiB to test
heap-ceiling behaviour, exhausted a worker. The kernel OOM-killer fired
(`SystemOOM ... victim process: java`), the node went NotReady for ~5 minutes, and it took unrelated
pods with it (six unrelated apps all restarted). The exit-137s were
nearly reported as proof the app had filled an 8 GiB ceiling — the surviving cgroup read `oom_kill 0`
in `/sys/fs/cgroup/memory.events`, so it was node pressure all along.

**Your own `kubectl exec` runs inside the container's cgroup, so it spends that container's
limit.** A one-off batch command exec'd into a serving pod adds its peak to the server's resident
memory, and when the sum crosses the limit the kernel may kill the *server*, not your command.
Measured: an ~80 MiB simulation exec'd into a 256 MiB API container already holding ~133 MiB
restarted that replica. Run one-offs as a Job with their own limit (`kubectl create job --from=cronjob/…`,
or a standalone Job that reports its own peak RSS), never inside a serving pod.

**Attribute it before diagnosing the app:**

- `/sys/fs/cgroup/memory.events` in a surviving container of the same workload — `oom_kill 0` means
  the cgroup path never fired.
- The node's `SystemOOM` events.

**Nothing warns first, and the monitoring goes blind exactly when you need it:** `kubectl top nodes`
reports `<unknown>` for a node whose kubelet has already stopped posting.

**On Talos, `SystemOOM` is real signal when present but not when absent.** A fast or severe exhaustion
still goes through the kernel OOM-killer and emits `SystemOOM` — that is what the incident above saw.
But Talos also runs its own userspace `runtime.OOMController`, which can act on cgroup memory pressure
*before* the kernel path ever fires, and a kill from that path emits no `SystemOOM` at all. So an empty
`SystemOOM` list does not rule out a node-level OOM — check `talosctl dmesg` for OOM lines and
`talosctl cgroups --preset memory` too before concluding it was a plain cgroup limit.

**`kubectl describe node` understates real usage on Talos**, since the static control-plane pods
declare almost no memory requests: the requests-vs-allocatable view can show headroom that is not
there. Read it with that caveat:

```bash
kubectl describe node | awk '/Allocated resources/,/Events/'
```
