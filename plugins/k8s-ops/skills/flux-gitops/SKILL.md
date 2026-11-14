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

**After an image bump, pick the pod by image.** A `Running` pod is not evidence it is the pod you mean:
during a rolling update both ReplicaSets have Running pods, so `kubectl get pods | awk '/^api-/ && /Running/ {print $1; exit}'`
can hand back an old one, and a one-shot command then fails (`invalid choice: <new subcommand>`) in a way
that reads as a bad build.

```bash
POD=$(kubectl -n ns get pods \
  -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.containers[0].image}{"\n"}{end}' \
  | grep -E '^api-' | grep "$TAG" | awk '{print $1; exit}')
```

When waiting for a roll, wait for every pod to be off the old image
(`... | grep -E '^api-' | grep -vc "$TAG"` reaches 0), not for the Deployment's own status.

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

## Cold bootstrap: a CR and the chart that owns its CRD cannot share a Kustomization

On an established cluster this is invisible. On a cold one it is a hard deadlock that looks like a
transient waiting to resolve itself. The all-or-nothing apply above is the cause: a `ClusterIssuer` beside
the cert-manager `HelmRelease` that installs its CRD fails the dry-run, so the HelmRelease is never
created, the CRD never appears, and the Kustomization retries forever on `no matches for kind`. Nothing
self-heals, because the fix is in the set that was rejected.

**`no matches for kind X` plus zero HelmReleases is the deadlock, not a race.** Check `flux get hr -A`: if
the release that provides the CRD does not exist at all, waiting will not help.

- **Break it once by hand**: apply the CRD-providing `HelmRepository` + `HelmRelease` directly, wait for
  the CRD, then `flux reconcile`. Record the ordering in the cluster's bootstrap script, or it is
  re-derived on every rebuild.
- **Split the Kustomization** and use `spec.dependsOn`, so the CRs apply only after the operator is
  healthy. Right if clusters get rebuilt often.

A circular chart dependency (cert-manager mounting a ConfigMap that trust-manager generates, while
trust-manager needs a certificate cert-manager must issue) is the nastier sibling and no ordering fixes
it: one controller sits in `ContainerCreating` on `configmap ... not found`, the other in `Init:0/1`.
Seed the artifact by hand once (copy it from a working cluster) and the operator takes ownership from
then on. Look for `FailedMount` in events; a Helm timeout reported against a Deployment does not say
which side of the cycle you are on.

## A HelmRelease that succeeds and is still wrong

Helm values are a permissive merge: a key you got wrong is not an error, it is ignored and the chart's
default ships in its place. `helm template` exits 0, Flux reports `Ready=True`, and the release does
something you did not ask for. Four shapes:

- **Wrong key.** The chart took a list (`volume.dataDirs`); a scalar `volume.data` was written. The
  chart's `hostPath` default stayed and the namespace's PodSecurity `baseline` rejected it at admission,
  far from the cause.
- **Duplicate YAML key.** Two `webhook:` blocks in one values map; YAML keeps the last, so the first
  block's probe timeouts and `replicaCount` were silently dropped.
- **Un-set sub-key.** One sub-tree was never specified and kept a `hostPath` default while its siblings
  became PVCs.
- **"Removed" by omission.** Deleting a key never removes a chart default; the merge puts it back. A
  comment saying "no CPU limit" beside an omitted `limits.cpu` still rendered the chart's `500m`. Only an
  explicit `cpu: null` deletes a default key.

The discriminator is not "did it render". Render, then assert on the output for the property you meant
to change, and grep for **the default you were trying to displace**:

```bash
helm template <rel> <chart> -f values.yaml > r.yaml   # rc=0 proves nothing
grep -c hostPath r.yaml                                # the default being replaced: expect 0
```

Read the chart's own `values.yaml` for the key's real shape, and `templates/` for how it is consumed
(`tpl .Values.x.tolerations` means that key is a string, not a list), rather than inferring it from
surrounding comments.

## A file in the repo is not a file in the render

Sweeping a GitOps tree for a defect by reading manifests can report a hit in a file nothing applies.
A manifest is live only if something references it: a kustomization's `resources:`, or a chart template
reachable under the values in force. A file commented out of `resources:` sits in the tree looking like
its siblings (valid YAML, right `kind`, a real object name, a real defect inside). A scan flagged Service
ports missing `protocol` in two files that had been commented out since the app was added; the live
Services came from the HelmRelease and were correct. The finding was true about the bytes and false about
the cluster.

**Scan the render, not the tree**: `kustomize build <dir>` or `flux build kustomization`, and assert on
that output. An excluded file is simply absent there, so the class disappears by construction. Where a
tree scan is all you have, resolve the reference before the finding becomes a claim: check the owning
`kustomization.yaml` lists the filename and it is not behind a `#`.

## Secrets

Secrets are **SOPS-encrypted in git** (age/PGP) or delivered by a controller (external-secrets / SealedSecrets) — **never plaintext in the repo**. If decryption fails the whole Kustomization won't apply:
- SOPS: check the age/PGP key the Kustomization references (`spec.decryption`) exists and is correct.
- external-secrets / SealedSecrets: check that controller's logs and its backing store/key.

## Drift, automation, and normal noise

- `flux check` — verify controllers and CRDs are healthy after any upgrade/bootstrap.
- If image automation is used, `image-reflector-controller` + `image-automation-controller` scan registries and commit tag bumps back to git — those commits are expected.
- **A merged build that never rolls out:** `kubectl get imagerepository,imagepolicy -A` first. `failed to open gzip tags:
  EOF` (ImageRepository and ImagePolicy both `False`, the policy stuck on the old tag) is a corrupt tag-cache entry,
  typically left by a controller container restart mid-write. Its database is an `emptyDir`, so deleting the
  `image-reflector-controller` pod clears it; then annotate the ImageRepository and ImagePolicy with
  `reconcile.fluxcd.io/requestedAt` and the policy resolves the new tag. Nothing else alerts on this: it stalls silently.
- Renovate/Dependabot version-bump PRs churn the repo constantly; that's normal noise, not a fault.
- **`kubectl rollout restart` on a Flux-managed Deployment can be two rollouts.** The next
  kustomize-controller apply can remove the `restartedAt` template annotation, rolling the Deployment
  back to the previous ReplicaSet (tells: no annotation left, the old RS newest again, a
  `kustomize-controller Apply` managedFields entry at that minute). The exact field-manager rule was not
  checked. To bounce one pod, delete the pod; to restart for real, change the template in git. A watcher
  keyed on `metadata.generation` fires on the revert too; key it on the image.
