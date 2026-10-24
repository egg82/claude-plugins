---
name: luks-tpm-recovery
description: Recover TPM2-backed LUKS auto-unlock on RHEL-family/Fedora/bootc hosts. Use when a LUKS+TPM auto-unlock machine stops unlocking automatically, prompts for a passphrase at every boot, hangs at the LUKS prompt on remote reboot, or after a Secure Boot / firmware / PCR change.
---

# LUKS + TPM2 auto-unlock recovery

Two distinct failures make a TPM2-sealed LUKS disk stop auto-unlocking. Diagnose which one before touching it — the fixes differ.

- **Intermittent** fall-through to the password prompt, worse on remote reboots → **Topic 1 (boot race)**. Fix in the initramfs; needs no secrets.
- **Every** boot suddenly needs the passphrase, after a BIOS/firmware update, a dbx/Secure-Boot-key change, or Secure Boot toggled off → **Topic 2 (PCR7 drift)**. Needs the LUKS passphrase / recovery key the operator holds.

First diagnostics (harmless): `clevis luks list -d <dev>` (is a tpm2 binding present, what `pcr_ids`), `mokutil --sb-state` (Secure Boot on/off), and check the journal for `clevis-luks-askpass` / `Esys_Unseal` messages.

## Topic 1 — clevis/TPM unlock race at boot

**Symptom:** auto-unlock *intermittently* falls through to the plymouth LUKS password prompt because `clevis-luks` runs before the TPM2 device is ready, fails, and hands off to the prompt. A remotely-triggered reboot then hangs at that prompt **forever** with nobody at the console.

**Fix — delay the password prompt so clevis wins the race:**

1. Override the ask-password unit:
   `/usr/lib/systemd/system/systemd-ask-password-plymouth.service.d/override.conf`
   ```ini
   [Service]
   ExecStartPre=/bin/sleep 10
   ```
   (On a *live*, non-image host the idiomatic way to create this drop-in is `systemctl edit
   systemd-ask-password-plymouth.service`, which writes it under `/etc`. On an image-baked/bootc
   host place it under `/usr/lib` as shown; the dracut `install_items` line below pulls it into the
   initramfs regardless of which location it lives in.)
2. Pull the override into the initramfs (early boot is where unlock happens):
   `/usr/lib/dracut/dracut.conf.d/60-systemd-ask-password-plymouth.conf`
   ```
   install_items+=" /usr/lib/systemd/system/systemd-ask-password-plymouth.service.d/override.conf "
   ```
3. Rebuild the initramfs. Back up first, then force-rebuild for the running kernel:
   ```sh
   cp /boot/initramfs-$(uname -r).img /boot/initramfs-$(uname -r).img.bak
   dracut --force --kver $(uname -r)
   ```

**Verify:** `lsinitrd /boot/initramfs-$(uname -r).img | grep ask-password-plymouth.service.d/override.conf` — the override must be present in the image.

**Space gotcha:** plain `dracut` stages in `/var/tmp`; on a small/near-full filesystem it dies with `No space left on device`. Point it elsewhere with `--tmpdir /path/on/a/roomy/fs`. An in-place initramfs rewrite in `/boot` is the same size as the existing image, so a ~85%-full `/boot` is usually fine — but prune old kernels if genuinely tight.

**Safe by design:** worst case boot just falls back to the prompt after 10s — it cannot make boot *worse*. A failed dracut build leaves the old initramfs intact, so it won't brick boot.

**bootc / immutable hosts:** this override belongs in the image build, not hand-applied to a live root (it won't survive an update). Apply live only as a stopgap and fold it into the image (`bootc-workstation`).

## Topic 2 — PCR7 / Secure Boot drift kills auto-unlock (and TPM-sealed credentials)

**Trigger:** PCR 7 (Secure Boot state) changes out-of-band — a vendor BIOS/firmware update, a dbx/Secure-Boot-key update, or Secure Boot toggled off. This invalidates the clevis tpm2 binding (typically `pcr_ids=7`), so the disk no longer auto-unlocks (passphrase needed *every* boot), **and** invalidates any systemd-creds / TPM2-sealed secret that was PCR-bound.

**Symptoms:** `clevis-luks-askpass` logs `Esys_Unseal(...) policy check failed`; a PCR-sealed credential fails to unseal even live (`Failed to unseal secret using TPM2: Operation not permitted`); `inLockout:0` (it is the *policy*, not a dictionary-attack lockout); `mokutil --sb-state` shows `disabled` if SB-off was the trigger.

**Recovery — needs the LUKS passphrase / recovery key the operator holds.** Re-bind to the *current* PCR state:

- clevis:
  ```sh
  clevis luks unbind -d <dev> -s <slot>
  clevis luks bind   -d <dev> -s <slot> tpm2 '{"pcr_ids":"7"}'   # prompts for an existing passphrase
  ```
- or systemd-cryptenroll:
  ```sh
  systemd-cryptenroll --wipe-slot=tpm2 <dev>
  systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 <dev>
  ```

The recovery reboot itself still prompts for the passphrase **once** (the rebind lands during that boot); auto-unlock returns from the *next* boot.

**Decision when Secure Boot was turned off:** re-enable Secure Boot in BIOS **first** (restores the hardened, measured state), **then** rebind — rebinding against the current SB-off state works but bakes in a hardening regression. Prefer re-enable, then rebind.

**Robustness tradeoff:** sealing a boot credential with *no* PCR binding (`systemd-creds encrypt --tpm2-pcrs=` empty) makes PCR7 drift stop killing it — self-healing at the cost of weaker measured-boot assurance. Choose deliberately.

**Ordering trap on immutable/bootc hosts:** do **not** run teardown-then-reinstall repair flows before the credential is resealed. If a repair removes services first and then fails at the credential step, the box is left worse off than when you started. Check credential health first:
```sh
systemd-creds decrypt --name=<name> <cred> - >/dev/null 2>&1 && echo OK || echo FAIL
```
Do **not** pipe through `head -c 0` — the `&&` would read `head`'s exit code and report a false `OK`.
