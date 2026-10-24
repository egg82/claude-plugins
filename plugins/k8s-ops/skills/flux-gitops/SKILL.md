---
name: flux-gitops
description: Operate and debug a Flux (FluxCD v2) GitOps cluster. Use when operating or debugging a Flux-managed cluster, a Kustomization/HelmRelease won't reconcile, or making a temporary change to a GitOps-managed resource.
---

# Flux GitOps operations

**BLUF:** Git is the source of truth. Flux continuously reconciles the live cluster back to what's committed. So the two rules that govern everything: (1) never hand-edit a live object Flux owns — it gets reverted on the next reconcile; (2) for a *temporary* change, `suspend` first (don't commit throwaway state to git).

## Core model

- **Sources** — `GitRepository` (or `OCIRepository`) fetch the desired state. The root source is usually `flux-system`.
- **Appliers** — `Kustomization` objects apply plain manifests/kustomize overlays; `HelmRelease` objects render + install/upgrade a Helm chart. Both point at a source and reconcile on an interval.
- Every applier reports the **last-applied revision** in its status. If live ≠ git, Flux corrects live.
- **Never `kubectl edit` a Flux-owned Deployment/ConfigMap/etc.** to make a lasting change — it's clobbered on the next interval. Lasting changes go through git.

## The suspend/apply/resume rule (house preference — follow it)

For a **temporary / reversible** change (scale something down during recovery, a quick experiment), do **NOT** commit it — it clutters git history. Instead:

```bash
flux suspend kustomization <name>      # or: flux suspend helmrelease <name>
kubectl scale deploy/<x> --replicas=0  # make the live change, do the work
# ...
flux resume kustomization <name>       # reconciles back to committed desired state
```

Suspend pauses reconciliation so your live edits stick; resume throws them away and restores git. **Permanent changes always go through git** — never leave something suspended as a "fix".

## Reconcile order after a git push (real gotcha)

`resume`/reconcile alone re-applies the **last-fetched** revision, not your new commit. You must pull the new source first:

```bash
flux reconcile source git flux-system        # 1. fetch the new commit FIRST
flux reconcile kustomization flux-system     # 2. THEN apply it
```

Shortcut for a single applier: `flux reconcile kustomization <name> --with-source` (fetches its source, then applies).

## Everyday commands

```bash
flux get all -A                    # health + last-applied revision, everything
flux get kustomizations -A
flux get helmreleases -A           # (flux get hr -A)
flux logs -f                       # follow controller logs
flux logs --level=error           # just errors
flux check                         # controllers healthy / version drift
```

## Debugging a stuck Kustomization

```bash
kubectl describe kustomization <name> -n flux-system   # read .status conditions
```

Read the `Ready` / `Reconciling` conditions. Common causes:
- **Build error** — bad YAML, wrong `path`, missing kustomization.yaml.
- **Dependency not ready** — a `dependsOn` target hasn't gone Ready yet (fix that one first).
- **Health check failing** — declared `healthChecks` targets aren't Ready.
- **Prune/apply error** — RBAC, immutable field, or a resource it can't own.
- **Drift** — something out-of-band changed live; Flux keeps re-applying.

**One rejected resource blocks every other change in the same Kustomization.** Apply is
all-or-nothing per Kustomization, so a single resource failing server-side dry-run takes the whole
apply with it — every unrelated fix in that commit, across different apps and namespaces, silently
never reaches the cluster. The Kustomization just reads `Ready=False` naming the one offender. This
bites hardest in a **monorepo reconciled by a single Kustomization**, where the blast radius is the
entire cluster.

So after pushing, **don't assume the revision landed**:

```bash
kubectl -n flux-system get kustomization <name> \
  -o jsonpath='{.status.lastAppliedRevision}'      # compare against the pushed sha
```

If it lags, read the `Ready` condition message. **When the change touches a field on an operator
CR, suspect immutability first** — CNPG, mariadb-operator and k8up all mark chunks of spec
immutable, and Flux has no way to force through it. The CR must be deleted so Flux recreates it;
check what the CR actually owns before deleting (often just a CronJob or a Job template, with no
data of its own).

## Debugging a stuck HelmRelease

```bash
flux get hr -A                                    # see retries / failure message
flux reconcile helmrelease <name> --with-source   # re-fetch chart + retry
kubectl describe helmrelease <name> -n <ns>       # install/upgrade retries exhausted?
helm history <release> -n <ns>                     # underlying Helm revisions
```

- Status often shows **retries exhausted** after a failed upgrade — it stops trying.
- Check the underlying `HelmChart` and its source are healthy (`flux get sources chart -A`).
- A wedged release: fix the `values`, or `flux suspend helmrelease <name>` then `flux resume` to force a clean retry. If Helm itself is stuck, inspect/rollback via `helm history` / `helm rollback` in the namespace. `Stalled / RetriesExceeded` needs `flux reconcile hr <name> --reset` after the fix.
- **Switching a Deployment from RollingUpdate to Recreate fails every time**:
  `spec.strategy.rollingUpdate: Forbidden: may not be specified when strategy type is 'Recreate'`.
  Server-side apply keeps the old `rollingUpdate` block, because a different field manager owns
  it. One-time fix: `kubectl patch deploy <d> --type=json -p '[{"op":"replace","path":"/spec/strategy","value":{"type":"Recreate"}}]'`, then `--reset` the release.
- **An immutable PVC change** (storageClass, accessModes) can't be upgraded in place. Suspend the
  release, stop the workload, back up through a helper pod (distroless images have no `tar`; a
  0-byte backup looks like a success), set the old PV to `Retain`, delete the PVC, and recreate it
  under the same name *with the release's Helm labels and annotations* so Helm adopts it. Then
  restore, commit the values, and resume.

## Secrets

Secrets are **SOPS-encrypted in git** (age/PGP) or delivered by a controller (external-secrets / SealedSecrets) — **never plaintext in the repo**. If decryption fails the whole Kustomization won't apply:
- SOPS: check the age/PGP key the Kustomization references (`spec.decryption`) exists and is correct.
- external-secrets / SealedSecrets: check that controller's logs and its backing store/key.

## Drift, automation, and normal noise

- `flux check` — verify controllers and CRDs are healthy after any upgrade/bootstrap.
- If image automation is used, `image-reflector-controller` + `image-automation-controller` scan registries and commit tag bumps back to git — those commits are expected.
- Renovate/Dependabot version-bump PRs churn the repo constantly; that's normal noise, not a fault.
