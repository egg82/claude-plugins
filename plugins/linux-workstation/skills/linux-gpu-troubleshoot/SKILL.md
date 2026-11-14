---
name: linux-gpu-troubleshoot
description: Diagnoses NVIDIA GPU/driver failures on RHEL-family/Fedora/bootc desktops. Use when an NVIDIA Linux box crashes/freezes, boots with no GPU driver after a kernel update, hangs after the LUKS/boot prompt, or the whole machine hard-freezes running Chrome/VSCode/Electron apps.
---

# Linux NVIDIA GPU Troubleshooting

Scope: RHEL-family / Fedora / el9-like desktops and workstations with NVIDIA GPUs, including
bootc immutable variants. Match the symptom to a topic below; each is BLUF + fix-first.

Pick the topic:
- A "freeze" nobody has evidence for yet → **Topic 0** (establish what happened before blaming the GPU).
- New kernel crashes at/after boot, older kernel still works → **Topic 1** (DKMS build gap).
- Whole machine hard-freezes launching Chrome/VSCode/Electron/a media player → **Topic 2** (driver regression).
- Running kernel has no GPU drivers at all, dnf won't install modules → **Topic 3** (versionlock trap).
- A new-ish device (Wi-Fi, etc.) has no driver on a fresh kernel → **Topic 4** (firmware lag).
- Black screen at login (no panel/wallpaper) while the compositor responds, or a hard mid-session wedge on resize / fullscreen / tab switch with no panic in the log → **Topic 5** (shell dies in the GL stack). Do not stop at Topic 2 just because an Electron app was on screen.

---

## Topic 0 — Get the freeze evidence BEFORE blaming the GPU

**A reported "freeze" on an NVIDIA box is not yet a GPU finding.** The hardware being NVIDIA is a
coincidence until a log says otherwise. One case that matched Topic 2's hardware exactly — a low-end
discrete GPU alongside integrated graphics, nouveau loaded, no proprietary driver — turned out to be
a background service in a 5-second restart loop.

**`journalctl -b -1` is a trap on any host with a volatile journal.** With no `/var/log/journal`,
`journalctl --list-boots` shows exactly one boot and every previous-boot query returns empty. That zero
describes the journal's storage mode, not the machine's history.

```bash
journalctl --list-boots            # 1 boot only => volatile; prior kernel logs are GONE
last -x | head -30                 # 'crash' = no clean shutdown record (hard power-off)
ls -la /var/log/messages*          # where rsyslog is installed it IS persistent — the real evidence
```

- **`last -x` is the cheapest ground truth.** It separates a clean `shutdown` from a `crash`, timestamps
  each boot, names the kernel it booted, and shows which sessions were alive when it died — including
  whether the box was sitting at the GDM greeter (`gdm tty1 … - crash`) rather than in a user session. A
  remote session shows as `user :10 <src-ip>`, so it also tells you which sessions were really affected.
- **A hang that logs nothing is not evidence of a GPU wedge.** Absent an OOM kill, panic, soft lockup, or
  an `Xid`/`drm` error, "the log just stops" is equally consistent with someone holding the power button
  on a box that merely felt unresponsive. Check for those four explicitly, and say "mechanism unproven"
  rather than reaching for the familiar cause.
- **Correlate against the last update**, since a regression usually bites at the first reboot *after* the
  update, not on update day: `dnf history list` then `dnf history info <id>`; on bootc, the deployment
  list from `bootc status` / `rpm-ostree status`.
- **A noisy service buries the last real events.** Filter the flooders before reading a crash tail
  (`grep -vE 'noisy-daemon|audisp-syslog|irqbalance'`) or you will only see the noise.

**Then leave the box diagnosable** — the volatile journal is why the mechanism was unprovable in the
first place:
```bash
mkdir -p /var/log/journal && systemd-tmpfiles --create --prefix /var/log/journal
mkdir -p /etc/systemd/journald.conf.d
printf '[Journal]\nStorage=persistent\nSystemMaxUse=1G\n' > /etc/systemd/journald.conf.d/99-persistent.conf
systemctl restart systemd-journald && journalctl --flush   # --flush migrates /run -> /var
```
Without the `--flush`, journald keeps writing to `/run/log/journal` and the change looks applied but
isn't — verify with `journalctl --header | grep 'File path'`.

---

## Topic 1 — NVIDIA DKMS module fails to build against a newer kernel

**Symptom:** a kernel update lands; the NEW kernel crashes right after boot/LUKS ("kernel crash /
startup failed"); the OLDER kernel still boots fine.

**Root cause:** the NVIDIA DKMS driver branch is too old to compile against the new kernel's DRM
API (e.g. a changed `.fb_create` callback signature → `-Werror=incompatible-pointer-types`). DKMS
silently fails to build for the new kernel, so that kernel has NO nvidia module. With nouveau
blacklisted there is no GPU driver at all → boot dies after the kernel pivots.

**Diagnose:**
- `dkms status` — nvidia is built for the old kernel(s) but NOT the new one.
- `ls /lib/modules/<newkernel>/extra/nvidia*.ko` — missing.
- `rpm -V kernel*` — clean, ruling out package corruption.

**Fix** (RHEL-family with dnf module streams): move to a newer driver branch that supports the kernel.
On a bootc host the fix belongs in the image (`bootc-workstation`), and `bootc-version-scan`'s
`nvidia-dkms-check.sh` tests a kernel pin against the driver before the bump ships. The `dracut`
space gotcha is in `luks-tpm-recovery`.
```
dnf module reset -y nvidia-driver
dnf module install -y nvidia-driver:<newer>-dkms   # e.g. <branch>-dkms
```
This rebuilds DKMS for ALL installed kernels including the new one. Then verify and rebuild initramfs:
```
ls /lib/modules/<newkernel>/extra/nvidia*.ko   # now present
dracut -f
reboot
```

**Do NOT break the live session:** never swap the driver branch while a user is actively using the
GPU. Updating userspace libs to the new branch while the running kernel still has the OLD module
loaded glitches the live GL/CUDA session. Coordinate the userspace swap and the reboot together.

**bootc / immutable hosts:** the driver branch is pinned in the image, not changed on the host.
Bump it in the image build; don't `dnf module` on the running host.

---

## Topic 2 — Whole-machine HARD FREEZE running Chrome / VSCode / Electron / a media player

**Symptom:** the ENTIRE machine hard-locks (not just the app) when launching a GPU-accelerated
Electron/Chromium app. This is an NVIDIA driver regression interacting with the app's GPU compositing.
First rule out Topic 5: if the dGPU is on nouveau (`nvidia-smi` absent,
`/sys/class/drm/card*/device/driver` = `nouveau`) there is no driver branch to pin.

**Fix:** pin a known-good NVIDIA driver version/branch — do not float to latest.

**Workaround while pinning:** disable GPU acceleration in the offending app to stop the freeze:
- Chromium/Electron: launch with `--disable-gpu`.
- In-app: turn off "Use hardware acceleration when available".

---

## Topic 3 — Partial kernel update leaves drivers missing (versionlock trap)

**Symptom:** the box runs a kernel but has NO in-tree GPU drivers (`/sys/class/drm` empty, i915 /
nouveau absent) → Chrome/VSCode freeze the machine.

**Root cause:** a conflicting/duplicate dnf `versionlock` (two versions pinned across kernel /
kernel-core / kernel-modules) half-applied a kernel update — kernel-core advanced but
`kernel-modules-<ver>` was never installed.

**Diagnose:**
- `rpm -q kernel-modules-$(uname -r)` → "not installed" while running that kernel.
- `dnf install kernel-modules-$(uname -r)` → "All matches were filtered out by exclude filtering".
- `dnf versionlock list | grep -i kernel` → conflicting pins.

**Fix:** `--disableexcludes` does NOT bypass versionlock (wrong tool). Use the versionlock plugin
disable — installing modules for the already-running kernel is not a kernel change, so it's safe:
```
dnf install -y --disableplugin=versionlock kernel-modules-$(uname -r)
depmod -a
dracut -f
```
Mind `/boot` and `/var/tmp` space when rebuilding initramfs; if tight, point dracut elsewhere:
`dracut -f --tmpdir /path/on/a/roomy/fs`.

**Durable fix:** clean up the conflicting versionlock entries so future updates don't re-partial.

---

## Topic 4 — Kernel outran a firmware package (e.g. newer Wi-Fi chip)

**Symptom:** a distro kernel ships ahead of a vendored firmware RPM, so a new-ish device (a recently-released
Wi-Fi card is the usual one) loses its driver until firmware catches up.

**Fix:** sideload the newer firmware package (e.g. `iwlwifi` / `iwl*-firmware`) and reload the
module — often no reboot needed:
```
modprobe -r iwlwifi
modprobe iwlwifi
```

**Durable fix:** bump the firmware package in the base image.

---

## Topic 5 — Desktop shell dies in the GL stack (nouveau, NVK, zink)

**Cause:** a discrete NVIDIA GPU left on nouveau (no proprietary driver installed) makes Mesa drive
OpenGL through zink (GL-on-Vulkan) on the NVK Vulkan driver. A texture upload `memcpy`s into a mapped
Vulkan buffer and takes SIGBUS. The shell does constant uploads, so it dies first and repeatedly while the
compositor, not on that path, survives. That split is the tell.

- **Symptom A, black screen at login:** no panel or wallpaper, but a hot corner still opens the overview
  and the mouse moves. Reboots and clearing caches do not help (a clean disproof of a per-user cause); a
  different desktop on the same box is fine. The logs will not say why: you must get a core
  (`references/zink-shell-crash.md`).
- **Symptom B, hard wedge mid-session:** the desktop locks when the shell rebuilds a large surface
  (fullscreen toggle, un-maximise, tab switch); the user recovers with a long power hold. No panic, soft
  lockup or OOM; the last GPU events name the shell:
  `nouveau ...: gsp: mmu fault queued` / `...[gnome-shell[PID]] errored - disabling channel` /
  `ZINK: vkQueueSubmit failed (VK_ERROR_DEVICE_LOST)`, then `Power key pressed short` (the human, not the
  machine). **You can SSH in during the "freeze"** (`systemctl restart gdm`), which confirms it. `last -x`
  still shows `crash` and the journal simply stops; do not read that as a kernel lock-up.
- **Correlate with the kernel, not the app.** The fault can sit latent for months and go
  several-times-a-day on a kernel bump. Count per boot (`journalctl -b -N | grep -c 'mmu fault'`) against
  the kernel each boot ran: clean on the old kernel over days, nonzero on every boot of the new one, is the
  whole argument.

**Fix:** put the proprietary driver on the box (on bootc, the `-nvidia` image variant). Verify
`lsmod | grep -c '^nouveau'` is 0, the drm card's driver is `nvidia`, and the shell has tens of seconds of
`etimes`: a crash-looping shell always has a live process, so `pgrep` means nothing. This is indicated by
the reproducible crash, not a reason to default all NVIDIA hardware to that variant (it can stutter).
