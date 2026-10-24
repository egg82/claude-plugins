---
name: bootc-workstation
description: "How a bootc / immutable-OSTree RHEL workstation works and how to install software on it. Use for installing on an immutable host, dnf or sudo not working, where files persist, podman vs docker, scripts wanting root, Flatpak or GLIBCXX errors, rpm-ostree layering, image rebuilds, upgrades, rollback, min-free-space errors, or running Kubernetes locally."
---

# bootc / immutable workstation

## Mental model

The OS is a versioned OCI container image, deployed as an immutable OSTree tree. There is no live
package manager on the host: `/usr` is read-only and reset to the image on every update. You do not
`dnf install` on the host. To change the base OS you build a *new image* — a `Containerfile`
`FROM` the base bootc image — push it somewhere, then `bootc switch <ref>` (or `bootc upgrade` if
the same ref moved) and reboot onto it.

Inspect and control deployments:
- `bootc status` / `rpm-ostree status` — current + staged + rolled-back deployments.
- `bootc upgrade` — pull + stage the newer image; applies on next reboot.
- `bootc switch <image-ref>` — rebase to a different image.
- `bootc rollback` — boot the previous deployment (it stays on disk; nothing is downloaded).

A healthy box keeps ~2 deployments; staging a 3rd during an upgrade is normal and prunes on reboot.

## Where state lives

- `/home` and `/var` **persist** across upgrades — keep your work, data, and containers here.
- `/etc` **persists** and is **3-way merged** on upgrade (your edits kept, image defaults updated).
- Everything under `/usr` (and anything else in the image tree) is **ephemeral** — it is thrown
  away and replaced by the image on every update. Never keep anything you care about in `/usr` or
  `/usr/local`.

## Installing software (in order of preference)

Do NOT reach for host-level installs. On an immutable host the right layer is almost always per-user
or a container.

1. **Per-user in `$HOME`.** `pip install --user`, npm local installs, and version managers
   (pyenv, nvm, sdkman, rustup/cargo, `go install`), or Homebrew on Linux. Nothing touches the OS
   and it survives every upgrade because it lives in `/home`.
2. **Containers.** `podman` runs rootless as your user; `docker` is typically an alias to podman.
   For a full mutable dev userspace, run a **distrobox** (or toolbox) container: it shares `$HOME`
   but gives you a normal Linux with working `apt`/`dnf` inside. This is where you do "I just need
   to `dnf install` a thing" — you do it *inside the box*, not on the host.
3. **Flatpak for GUI apps.** Each Flatpak bundles its own runtime. This is also the fix for
   self-built Electron/AppImage apps that fail with `GLIBCXX_...`/glibc-too-old errors — the host
   libc is fixed by the image, so bundle the runtime instead of fighting it.
4. **Layer an RPM into the image — last resort.** `rpm-ostree install <pkg>` persists across reboots
   but rebuilds the deployment and is silently **undone by any image rebase**. Only use it for
   something that genuinely must be in the base OS, and prefer putting it in the Containerfile so
   it survives rebases.

## "It wants root / sudo"

Most root friction is a signal you're at the wrong layer:
- Script wants the **docker daemon as root** → use rootless `podman` (or the docker→podman alias).
- Something writes to `/usr/local` or `/opt` → redirect it into `$HOME` (prefix, `--user`, or a
  distrobox).
- It truly belongs in the base OS (a kernel module, a system service, a system-wide binary) → add
  it to the image `Containerfile` and rebuild, don't hand-modify the running host.

## Upgrades and rollback

`bootc upgrade` pulls and stages the newer image; it applies on reboot. Auto-upgrade timers may
already be running (check `systemctl list-timers | grep -i bootc`). If an upgrade misbehaves,
`bootc rollback` + reboot returns you to the previous deployment — it's still on disk.

## Disk hygiene

The OSTree repo lives in `/sysroot`. Accumulated pkgcache and old deployments bloat it, and a full
`/sysroot` causes `min-free-space` errors on upgrade. Reclaim space with `rpm-ostree cleanup -bm`
(drops base-metadata and pending/rollback cruft) — that's the right tool on an rpm-ostree-managed
host. Avoid hand-running `ostree prune` on the sysroot: it rarely reclaims more and can desync
rpm-ostree's view of its deployments.

`min-free-space` on upgrade almost always means the disk is genuinely too full — clean up or grow it.

## Local Kubernetes (homelab)

For a cluster on the box itself, run **kind / minikube / k3d rootless inside podman** — they live in
`/home` and need no host changes. Or point `kubectl` at an external cluster. Don't try to install a
system-level container runtime or kubelet onto the immutable host.

## Traps that cost real time

- **`/tmp` is cleared aggressively and `/var/tmp` is not cleared reliably at all — check the host
  rather than quoting a distribution default.** Scratch state, a half-finished download, a script's
  working directory can vanish with no event to blame, so don't leave anything you care about there;
  use a path under `/home` or `/var/lib`. The vendor-default clean ages (10d / 30d) do not reliably
  hold on a real host — measured details and the local-override tell in
  `references/tmp-vartmp-clean-ages.md`.

- **Docker 25+ keeps image layers in `/var/lib/containerd`, not `/var/lib/docker`.** With the
  containerd image store enabled, a dedicated `/var/lib/docker` LV holds almost nothing while the
  filesystem behind `/var/lib/containerd` quietly fills. Size and monitor the right one, and don't
  conclude "images aren't taking space" from a small `/var/lib/docker`.

- **`docker.sock` is `root:root` for a moment at boot**, before the group ownership resolves. A
  service that starts in that window gets permission-denied on a socket that looks correct
  afterwards, which makes it read as an intermittent fault. Ordering the unit `After=` the socket
  does **not** fix it — the socket exists, it's the ownership that's late. Use a local group, or a
  oneshot that re-groups the socket and order against that.

- **A rootless podman service (a CI runner, say) needs the rootless socket path.** DinD-style workloads that fail
  `permission denied` on the docker socket are usually pointed at the *rootful* socket. Use
  `/run/user/<uid>/podman/podman.sock` and enable **linger** for that user so the socket survives
  logout.

- **Host GPU or unlock failures** (driver missing after a kernel bump, freezes, TPM auto-unlock lost) are
  `linux-gpu-troubleshoot` and `luks-tpm-recovery`; the fix still lands in the image here.
- **GPU in a container: probe by running it, not by looking for the CDI file.** The image's
  `nvidia-cdi-refresh` writes the spec to `/var/run/cdi/nvidia.yaml` at every boot, not
  `/etc/cdi`, so an `/etc/cdi` check reads "not configured" on a box where it works. The probe
  that can fail honestly: `podman run --rm --device nvidia.com/gpu=all --security-opt=label=disable
  <image> nvidia-smi -L` as the user. For torch with no container, a uv venv (pip `torch` with its
  CUDA wheels) sees the GPU directly; the host's own Python has none.

- **Postgres bind-mount data directories must be owned by uid 999**, whatever the host user is. The
  failure mode is a misleading `mkdir` error naming a directory that already exists — it's the
  ownership check failing, not creation.

- **Never create a systemd ordering cycle — systemd resolves one by silently deleting a start job**,
  so a unit just never starts and nothing reports an error. The classic version is trying to make
  an early-boot or socket unit wait on a late multi-user service (the `docker.sock` case above).
  The cycle-free fix is a separate post-boot oneshot ordered after the late service, never
  reordering the early unit itself. Prefer `systemctl edit <unit>` drop-ins under
  `/etc/systemd/system/<unit>.d/` over editing vendor unit files so changes survive package
  updates; `systemctl cat <unit>` shows the merged result. `After=`/`Before=` (sequencing) and
  `Wants=`/`Requires=` (dependency) are orthogonal — you usually want both. Check with
  `systemd-analyze verify <unit>` before trusting it.

- **SELinux permissive-mode desktop noise** isn't a fault to chase. Kill the popups by disabling
  the `seapplet` autostart and `pkill -KILL` it. A NetworkManager denial that keeps returning needs
  a small local policy module rather than another round of investigation.
