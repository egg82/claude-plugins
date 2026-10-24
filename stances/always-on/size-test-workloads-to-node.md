---
name: size-test-workloads-to-node
description: Size throwaway test workloads against k8s NODE headroom, not the container limit; a node OOM masquerades as a cgroup OOM
metadata:
  type: feedback
  check: "n/a — a stance on how to size test workloads, with no live system to probe"
---

Before spinning up test workloads on a shared Kubernetes cluster, size them against **node
headroom**, not just each pod's container limit. Where the workers are modest and already carry real
services, a handful of deliberately-oversized probes fits every individual limit and still kills the
node — that has happened, taking six unrelated apps down with it.

**A node-level OOM is indistinguishable from a cgroup OOM in pod status** — both are `OOMKilled`,
exit 137 — so a node you exhausted reads as the app hitting its own ceiling. **Load `k8s-triage`**
before believing either: it carries the incident, the `memory.events` / `SystemOOM` attribution, and
the Talos qualifications.

**How to apply:** sum what you are about to add and compare against *measured* headroom — a
remembered incident tells you the failure mode exists, not today's numbers ([[verify-dont-anchor]]).
Run big probes one at a time, tear down the moment the measurement is taken, and move anything
wanting multiple GB onto a machine whose breakage costs nothing — a workstation or a throwaway VM —
rather than onto shared capacity other people are using. Ask for one; it is usually offered.

**Bound it: this is a caution about multi-GB probes, not a veto on small workloads.** Over-applied it
becomes a wrong refusal.
