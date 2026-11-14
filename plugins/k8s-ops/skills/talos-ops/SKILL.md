---
name: talos-ops
description: Operate, upgrade, and debug Talos Linux nodes and Talos-based Kubernetes clusters, and manage Talos machine config. Use when operating, upgrading, or debugging Talos Linux nodes / a Talos-based cluster, or managing Talos machine config, finding new-cluster defaults an upgraded cluster lacks, rebooting nodes after a VM CPU/memory resize, or a node that can't reach DNS/NTP or flaps reachability (a static node IP leased out by DHCP).
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
- **`talosctl get` answers for every node in the talosconfig unless `-n` narrows it**, so a "per-node"
  grep matches rows from other nodes. Filter on the NODE column and grep for values rather than indexing
  columns with `awk`: sizes like `1.0 TB` span two fields.

## Config apply
- `talosctl apply-config -n <node> --file <machineconfig.yaml>` — apply config.
  - `--mode=auto` (default; reboots only if needed), `--mode=no-reboot`, `--mode=reboot`, `--mode=staged` (apply on next boot; use for a config that would break a running node).
- `talosctl edit machineconfig -n <node>` — interactive edit + apply.
- `talosctl get machineconfig -o yaml` — dump the currently applied config.
- **`--dry-run` diffs print unchanged CONTEXT lines, including CA private keys** sitting near the field
  you touched (an etcd patch put `cluster.etcd.ca.key` on a terminal). Filter to changed lines:
  `... --dry-run 2>&1 | grep -E '^[+-][^+-]'`.
- **A patch merges lists and cannot remove an entry** (e.g. one `extraManifests` URL). Removing one needs
  a full `apply-config` built from the live config: fetch it into a mode-600 temp file, delete the line
  by text edit asserting exactly one match, dry-run, apply, read back, shred. Map keys can be removed by
  patch: `key: {$patch: delete}`.
- A bad config that won't boot: apply the fix with `--mode=staged`, or recover via the **maintenance-mode** path (node boots into maintenance and accepts config over the API) / console access.

## Upgrades (one node at a time)
- **OS:** `talosctl upgrade -n <node> --image ghcr.io/siderolabs/installer:<ver>` — upgrades Talos itself. Do one node at a time; it respects etcd quorum. Upgrade control-plane nodes carefully. **If the node uses system extensions** (very common in a homelab — GPU, iscsi, util-linux-tools, etc.), you must upgrade to an **Image Factory** installer that bundles those exact extensions (`factory.talos.dev/installer/<schematic-id>:<ver>`), NOT the vanilla `siderolabs/installer` — upgrading to the plain image silently drops your extensions.
  The first pull of a schematic+version the factory has not built yet waits while it builds (minutes in
  `talosctl upgrade`, or it fails with `i/o timeout` on the manifest HEAD with nothing installed). Warm it:
  `curl -I --max-time 900 https://factory.talos.dev/v2/<installer>/<id>/manifests/<ver>`. Canary one node
  before rolling a new extension: "loaded" in `get extensions` and a runtime handler in `/etc/cri/conf.d`
  do not prove it works. **`siderolabs/gvisor` also needs `machine.sysctls: user.max_user_namespaces` > 0**
  (Talos defaults it to 0), otherwise every runsc sandbox fails with
  `cannot create gofer process: fork/exec /proc/self/exe: no space left on device`.
- **Kubernetes:** `talosctl upgrade-k8s --to <ver>` — upgrades k8s components (kubelet, API server, etc.) across the cluster. **It also syncs bootstrap manifests and prunes anything in `talos-bootstrap-manifests-inventory` no longer declared** — on one cluster that included a kubelet-serving-cert-approver long since handed to Flux but still inventoried. Run `--dry-run` and grep `< Pruned` first; `--manifests-no-prune` skips it. The lasting fix is deleting those objects' keys from the `kube-system/talos-bootstrap-manifests-inventory` ConfigMap — the prune set comes from that ConfigMap, so stripping the objects' `owning-inventory` annotation does **not** stop it. Then bump the kubelet/component tags in the repo's base `controlplane.yaml`/`worker.yaml`, or the next `apply-config` rolls them back (a dry-run should then say "No changes").
- **`upgrade-k8s` rewrites each node's STORED config, not your generated base files.** Afterwards
  `apply-config --file worker.yaml -p @node.yaml` silently downgrades the kubelet and control plane to
  whatever the base still says (seen two minors behind). Bump the base's image tags after every
  `upgrade-k8s`, or apply changes as `talosctl patch machineconfig` deltas onto the live config.
- Watch `talosctl health` between nodes; never take down enough control-plane nodes to lose etcd quorum.
- **Recent talosctl's built-in drain fails on workers.** `upgrade`/`reboot` drain by fetching a kubeconfig *from the target node*, which only control planes serve (`kubeconfig is only available on control plane nodes`). The upgrade is already installed when this errors, so the node boots the new version on its next reboot anyway. Drain with `kubectl drain` yourself and pass `--drain=false`.
- **Point `-e` at a control plane even when upgrading a worker.** The drain fetches its kubeconfig from
  the endpoint, and only control planes serve one. With `-e <worker>` it installs the image to the
  inactive slot, fails to drain, and never reboots: the node runs the old version with the new one
  staged for its next boot.
- **A config patch that restarts a control plane's apiserver races the upgrade.** If that node holds the
  VIP, the upgrade's cordon call hits a refusing apiserver and aborts. Wait for `/readyz` between them.
- **`talosctl reboot` does not cordon; `upgrade` does.** During graceful shutdown the scheduler can keep
  placing a Deployment's replacement pod back on the dying node (dozens of `NodeShutdown` pods in
  seconds). `kubectl cordon` before a bare reboot.
- **With Rook, set `noout` before the reboot and clear it only once that node's OSDs are up AND every
  PG is `active+clean`.** OSDs can take minutes to start after a boot; clearing on a timer marked two
  out while they were still starting, and PGs without another replica went unknown for many minutes.
- **A scripted "all PGs clean" gate must count every `active+clean*` state.** Matching the exact
  string fails the moment a PG starts scrubbing (`active+clean+scrubbing`), so the gate flakes on a
  healthy cluster. Wait on a wall-clock deadline, not an iteration count: each `kubectl exec` adds
  seconds, and a "30 min" loop of 180 x 10s ran out at ~20.
- **A "no new stuck pods" baseline must catch crashloopers by `ready==false && restartCount>=3`**, not
  only `waiting.reason==CrashLoopBackOff`: between back-offs the container is briefly running, so the
  snapshot misses an already-broken pod and the post-node gate blames the upgrade.
- **Keep the rolling-upgrade script with the cluster config**, not in a scratchpad that a reboot empties.
- **A reboot can hang with the VM never resetting, and only a hypervisor-level reset recovers it.** Two shapes seen: (1) *rook* — shutdown stops the mons/OSDs before the kernel RBD/CephFS mounts unmount, and libceph retries forever. Seen on a single-node cluster via `talosctl reboot`, then on a multi-worker cluster during `talosctl upgrade` (console stops after `stopAllServices` with `libceph … osdN weight 0x0 (out)`): two of the OSD-holding nodes in one roll hung while the others upgraded fine, so it is not deterministic — budget for it; (2) Talos logs every shutdown phase through `phase reboot (14/14)` ("kexec skipped as secure boot is enabled"), then silence. In both, apid is gone, so `talosctl` cannot help. Tell them apart from a slow boot with a console screenshot from your hypervisor: unchanged kernel uptime means it never reset. Root cause of (2) is unknown; bound every reboot with a "not back in N minutes" alarm rather than trusting `--wait`: `talosctl upgrade --wait --timeout 20m` was seen still retrying past 21 minutes, so `--timeout` does not bound it. Ping answering while port 50000 refuses is the hang's signature.

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
- **A hypervisor memory increase needs a VM power cycle; `talosctl reboot` does not apply it.** With
  memory hot-plug on, the hypervisor hot-adds RAM live but Talos never onlines it, and a guest reboot
  keeps the VM's boot-time memory map: the node came back at its old size (e820 summed to the old
  amount, every `/sys/devices/system/memory` block online, none offline). The CPU increase did apply on
  the same reboot. Drain, `talosctl shutdown`, power on from the hypervisor, then check
  `status.capacity.memory`.
- `talosctl reset -n <node>` — **wipes the node** (destructive; returns it to maintenance/fresh). Use only to rebuild.
- Maintenance mode: node boots with the API up but unconfigured; apply config to bring it in.

## kubeconfig
- `talosctl kubeconfig [path]` — fetch/merge the cluster kubeconfig from a control-plane node.
- Again: `talosconfig` (machine API) ≠ `kubeconfig` (k8s API). Node/etcd ops need `talosconfig`; workload ops (`kubectl`, Flux) need `kubeconfig`.

## A single-instance CNPG cluster blocks a drain

`talosctl upgrade` drains by default, and a **1-instance CNPG cluster can never be drained**
(its PDB reports 0 allowed disruptions), which leaves the node cordoned and can cascade into
stranded Rook OSDs and Multi-Attach errors elsewhere. Before draining, find and delete any
single-instance CNPG primary pod on that node — and any CNPG primary there with no Ready instance on
another node (both instances on one node blocks the same way) — see `references/cnpg-blocks-drain.md`.

**"Applied configuration without a reboot" can mean "does nothing until the next boot".**
`SecurityProfileConfig` (workload isolation) is stored and reported applied, but `sandboxd`
only appears after a reboot. Check the thing the config is meant to change, not the apply
message.

## An upgraded cluster never gets new defaults: diff against a fresh config

`talosctl upgrade` changes the OS, never the stored config, so defaults Talos adds for new clusters never
reach one born on an older release. Find them all at once:
`talosctl gen config fresh https://127.0.0.1:6443 --kubernetes-version <ver> -o <dir>`, then compare by
document kind and field path against your generated bases (newer releases write separate documents that
mostly restate v1alpha1 fields; look for settings with no equivalent).

**Not every default is hardening: measure before adopting.** One release's authentication config
*enabled* anonymous access to `/livez`/`/readyz`/`/healthz` (so a load balancer can probe), while legacy
configs run `--anonymous-auth=false` and return 401, so adopting it loosens an upgraded cluster. It also
becomes `--authentication-config`, which kube-apiserver refuses to start alongside any `--oidc-*` flag;
`talosctl validate` does not catch that.

## Static node IPs inside a DHCP scope get leased to someone else

Node IPs set statically but inside a DHCP scope with no reservation are free as far as DHCP knows. While
the nodes are down (a rebuild), conflict detection's ping goes unanswered and the address is leased out;
the other client then renews it indefinitely without being pinged again. **Symptoms:** one node cannot
reach DNS/NTP (replies go to the other host), reachability to it flaps from off-subnet, and a freshly
rebooted peer (empty ARP cache) cannot reach it while older peers still can, which reads like something
the reboot broke. **Probe:** compare each node's real `eth0` MAC (`talosctl get links eth0`) with every
peer's `/proc/net/arp`, with a control (a node whose real MAC you could not fetch is silently skipped).
**Fix:** a MAC reservation per node on the DHCP server, and move any client already reserved on a node IP.
A reverse-DNS PTR naming someone else's host is a quick tell but can be stale.
