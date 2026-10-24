---
name: talos-ops
description: Operate, upgrade, and debug Talos Linux nodes and Talos-based Kubernetes clusters, and manage Talos machine config. Use when operating, upgrading, or debugging Talos Linux nodes / a Talos-based cluster, or managing Talos machine config.
---

# Talos Ops

## Mental model
Talos is an immutable, API-managed Linux for Kubernetes. There is **no shell, no SSH, no package manager, no login**. You never "fix a node from inside." Everything is done over the `talosctl` gRPC API against a **declarative machine config** (YAML). To change a node you **apply new machine config**; to change the OS you **upgrade the image**. Two separate credential files exist: `talosconfig` (machine/Talos API) vs `kubeconfig` (Kubernetes API) — don't confuse them.

Layering: Talos operates the **nodes and etcd**. Workloads on top are usually **Flux-managed** (see the `flux-gitops` skill), and general workload problems go through the `k8s-triage` skill. Reach for this skill only for the node/OS/etcd layer.

## talhelper (context for clusters that already use it — NOT a migration to recommend)
talhelper manages machine config from one `talconfig.yaml` plus a secrets file (`talsecret.yaml`, git-crypt/SOPS-encrypted), generating per-node configs and the `talosconfig`, keeping config DRY and living in git. Useful to know when you land in a cluster built that way.

**Check how the cluster at hand is actually built before suggesting talhelper.** A cluster managed as per-node YAML (`controlplane.yaml`, one file per node) applied with `talosctl`, with no `talconfig.yaml` anywhere, is a deliberate choice: do NOT recommend migrating it. An unconditional "recommend migrating to talhelper" in a skill points a migration at working infrastructure every time an agent loads it; method arriving as a skill is not checked the way a stated fact is.

Use the `talosctl` flow below. The talhelper flow applies only if you are in a cluster that already has a `talconfig.yaml`.

Typical talhelper flow (only where a `talconfig.yaml` already exists — not on a per-node-YAML cluster):
- Edit `talconfig.yaml`.
- `talhelper genconfig` → writes per-node `clusterconfig/*.yaml` + `talosconfig`.
- `talhelper gencommand apply` → prints the exact `talosctl apply-config` commands (or apply the generated files directly with `talosctl apply-config`).
- `talhelper gencommand upgrade` / `gencommand bootstrap` / `gencommand kubeconfig` exist too.

## Everyday talosctl
Every command needs a config + targets: `--talosconfig <file>` (or `TALOSCONFIG` env) and `--nodes/-n <ip>` `--endpoints/-e <ip>`.
- `talosctl health` — cluster health check.
- `talosctl get members` — discovered cluster members.
- `talosctl dashboard` — live TUI (logs, resources, load).
- `talosctl services` — service status; `talosctl service <name> status`.
- `talosctl logs <service>` — e.g. `kubelet`, `etcd`, `apid`, `containerd`, `machined`, `trustd`.
- `talosctl dmesg` — kernel log.
- `talosctl get <resource>` — COSI resources: `nodeaddresses`, `links`, `routes`, `mounts`, `disks`, `machineconfig`, `staticpods`, etc.
- `talosctl read <path>` — read a file from the node (e.g. `/etc/resolv.conf`).

## Config apply
- `talosctl apply-config -n <node> --file <machineconfig.yaml>` — apply config.
  - `--mode=auto` (default; reboots only if needed), `--mode=no-reboot`, `--mode=reboot`, `--mode=staged` (apply on next boot; use for a config that would break a running node).
- `talosctl edit machineconfig -n <node>` — interactive edit + apply.
- `talosctl get machineconfig -o yaml` — dump the currently applied config.
- A bad config that won't boot: apply the fix with `--mode=staged`, or recover via the **maintenance-mode** path (node boots into maintenance and accepts config over the API) / console access.

## Upgrades (one node at a time)
- **OS:** `talosctl upgrade -n <node> --image ghcr.io/siderolabs/installer:<ver>` — upgrades Talos itself. Do one node at a time; it respects etcd quorum. Upgrade control-plane nodes carefully. **If the node uses system extensions** (very common in a homelab — GPU, iscsi, util-linux-tools, etc.), you must upgrade to an **Image Factory** installer that bundles those exact extensions (`factory.talos.dev/installer/<schematic-id>:<ver>`), NOT the vanilla `siderolabs/installer` — upgrading to the plain image silently drops your extensions.
- **Kubernetes:** `talosctl upgrade-k8s --to <ver>` — upgrades k8s components (kubelet, API server, etc.) across the cluster.
- Watch `talosctl health` between nodes; never take down enough control-plane nodes to lose etcd quorum.
- **Recent talosctl's built-in drain fails on workers.** `upgrade`/`reboot` drain by fetching a kubeconfig *from the target node*, which only control planes serve (`kubeconfig is only available on control plane nodes`). The upgrade is already installed when this errors, so the node boots the new version on its next reboot anyway. Drain with `kubectl drain` yourself and pass `--drain=false`.
- **A reboot can hang with the VM never resetting, and only a hypervisor-level reset recovers it.** Two shapes seen, both on reboots through the kernel's reboot path (Talos upgrades got through): (1) *a small cluster with rook* — shutdown stops the mons/OSDs before the kernel RBD/CephFS mounts unmount, and the console fills with `libceph: mon… connect error` forever; (2) Talos logs every shutdown phase through `phase reboot (14/14)` ("kexec skipped as secure boot is enabled"), then silence. In both, apid is gone, so `talosctl` cannot help. Tell them apart from a slow boot with a console screenshot from your hypervisor: unchanged kernel uptime means it never reset. Root cause of (2) is unknown; bound every reboot with a "not back in N minutes" alarm rather than trusting `--wait`.

## System extensions, schematics, and Secure Boot

**Secure Boot and a hypervisor guest agent that needs raw I/O ports can be mutually exclusive** (the VMware tools extension is the example). On a node installed from a
**secureboot** installer image such an extension can crash-loop forever: Secure Boot enables kernel
lockdown, lockdown blocks `iopl()`, and `iopl()` is exactly what that agent needs to reach the hypervisor. It panics with `unable to change I/O privilege level` and Talos restarts it every few seconds,
indefinitely. **There is no config workaround** — the extension has to come out of the schematic. The
tell is `talosctl service ext-talos-vmtoolsd` reporting `Waiting` on every node; it is easy to miss for
months while restarting every ~5.5s and flooding the kernel log and audit subsystem. Pick one: Secure
Boot, or guest IP/heartbeat reporting and guest-initiated graceful shutdown in the hypervisor console.

**Editing a factory schematic — do not reconstruct the YAML from notes.** Extension *order* changes the
hash. `GET https://factory.talos.dev/schematics/<id>` returns the exact canonical content: edit that and
POST it back to register the new one. **Round-trip the original first** and confirm your method
reproduces the known ID, before trusting a new one.

## etcd / control-plane health (critical)
- `talosctl etcd status` / `talosctl etcd members` — check quorum and member health.
- On a **3-CP cluster, losing 2 members loses quorum** (the scary failure). A **single-node control plane has no HA** — any reboot/upgrade is an outage.
- `talosctl etcd snapshot <file>` — back up etcd. Do this before risky changes.
- `talosctl bootstrap` — runs etcd init. **ONLY ONCE, on first cluster init, on a single control-plane node. Never re-run on a live cluster** (it will corrupt/split the cluster). Cluster recovery uses `talosctl etcd recover` / snapshot restore procedures, not `bootstrap`.

## Reboot / reset / maintenance
- `talosctl reboot -n <node>` — reboot.
- `talosctl shutdown -n <node>` — power off.
- `talosctl reset -n <node>` — **wipes the node** (destructive; returns it to maintenance/fresh). Use only to rebuild.
- Maintenance mode: node boots with the API up but unconfigured; apply config to bring it in.

## kubeconfig
- `talosctl kubeconfig [path]` — fetch/merge the cluster kubeconfig from a control-plane node.
- Again: `talosconfig` (machine API) ≠ `kubeconfig` (k8s API). Node/etcd ops need `talosconfig`; workload ops (`kubectl`, Flux) need `kubeconfig`.

## A single-instance CNPG cluster blocks a drain

`talosctl upgrade` drains by default, and a **1-instance CNPG cluster can never be drained**
(its PDB reports 0 allowed disruptions), which leaves the node cordoned and can cascade into
stranded Rook OSDs and Multi-Attach errors elsewhere. Before draining, find and delete any
single-instance CNPG primary pod on that node — see `references/cnpg-blocks-drain.md`.

**"Applied configuration without a reboot" can mean "does nothing until the next boot".**
`SecurityProfileConfig` (workload isolation) is stored and reported applied, but `sandboxd`
only appears after a reboot. Check the thing the config is meant to change, not the apply
message.
