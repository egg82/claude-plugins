---
name: k8s-secrets
description: Manages Kubernetes secrets in a GitOps repo. Use when managing Kubernetes secrets in git, a Flux Kustomization fails to decrypt, setting up SOPS/age, external-secrets, or sealed-secrets, rotating an age key, or verifying a decrypted secret landed in the cluster.
---

# Kubernetes Secrets in GitOps

## BLUF

You can't commit plaintext secrets, but GitOps wants everything in git. The fix is to commit
*encrypted* secrets and let the cluster decrypt them at apply time. Three homelab-grade options:

- **SOPS + age** — default for Flux homelabs. Encrypt values in-repo; Flux decrypts on apply.
- **External Secrets Operator (ESO)** — pull secrets from a real secret manager (Vault, Bitwarden, 1Password, cloud SM). Best when a store already exists.
- **Sealed Secrets (Bitnami)** — `kubeseal` encrypts to a cluster cert; simplest, but cert-bound to one cluster.

For Flux wiring see the **flux-gitops** skill; for general cluster debugging see **k8s-triage**.

## The #1 failure: Kustomization "decryption failed" / secret never created

Fix-first checklist (SOPS):

1. `kubectl describe kustomization <name> -n flux-system` — read the actual error under Status/Events.
2. Confirm the decryption key Secret exists: `kubectl get secret sops-age -n flux-system`.
3. Confirm it holds the **right** age key — a rotated/mismatched key is the usual cause. Compare the
   public recipient of the in-cluster private key against `.sops.yaml`.
4. Confirm `.sops.yaml`'s `age:` recipient matches the key you're decrypting with.
5. Confirm the Kustomization actually has `spec.decryption.provider: sops` + `secretRef` set — Flux
   won't decrypt without it, so the secret lands as ciphertext or fails schema validation.

ESO: `kubectl describe externalsecret <name>` and check `.status` conditions; verify the
`SecretStore`/`ClusterSecretStore` auth (token/creds) is valid and `.status` shows `Valid`.

Sealed Secrets: a secret sealed against a *different* cluster's cert will never decrypt — reseal it
against this cluster's controller cert.

## Setup: SOPS + age

```sh
age-keygen -o age.agekey                 # prints the public recipient (age1...) to stderr
```

`.sops.yaml` at repo root — creation rule so only secret values get encrypted:

```yaml
creation_rules:
  - path_regex: .*\.yaml$
    encrypted_regex: ^(data|stringData)$
    age: age1yourpublicrecipientkeyhere...
```

Encrypt / edit manifests:

```sh
sops --encrypt --in-place secret.yaml    # encrypt in place
sops secret.enc.yaml                      # decrypt-edit-reencrypt in $EDITOR
```

Create the cluster-side decryption Secret (from the private key file):

```sh
kubectl create secret generic sops-age -n flux-system \
  --from-file=age.agekey=age.agekey
```

Wire the Kustomization:

```yaml
spec:
  decryption:
    provider: sops
    secretRef:
      name: sops-age
```

## Ops hygiene

- **Never commit** the age private key or any plaintext secret. Only encrypted manifests and the
  public recipient (`.sops.yaml`) belong in git.
- **Back up the age private key out of band** (password manager / offline). Lose it and every secret
  in the repo is unrecoverable.
- Rotating recipients (`.sops.yaml`) does **not** re-encrypt existing files. After editing keys run
  `sops updatekeys secret.enc.yaml` on each file to add/remove recipients.

## Verify a decrypted secret landed

```sh
kubectl get secret <name> -n <ns> -o jsonpath='{.data.KEY}' | base64 -d
```

Empty/NotFound means Flux never applied it — go back to the decryption-failed checklist.
