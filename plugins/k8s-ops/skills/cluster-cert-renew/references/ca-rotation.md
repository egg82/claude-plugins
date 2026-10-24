# Rotating a Talos cluster's CAs

Renewal (the rest of this skill) re-issues *leaf* certs from the same CA. Rotation replaces the
**CA itself** — for scheduled hygiene or a suspected key compromise. Every failure mode is silent,
which is why the checks below matter more than the commands.

Each cluster has two independent CAs:

| `rotate-ca` flag | CA | Impact |
|---|---|---|
| `--talos=true` | Talos API (talosconfig) | no reboot, no workload interruption |
| `--kubernetes=true` | Kubernetes (kubeconfig) | restarts control-plane components; invalidates every kubeconfig and every client that cached the old CA |

Do the Talos CA first. Rehearse both on the least important cluster.

## 0. Before rotating: find every out-of-band copy of the OUTGOING CA

After rotation there is nothing left to search for, and each stray copy fails later, somewhere else,
looking like an unrelated outage. Do this for both CAs, from the cluster's own files (`--minify`,
because a merged kubeconfig's `clusters[0]` may be a different cluster):

```bash
K8S_CA=$(kubectl --kubeconfig kubeconfig config view --raw --minify \
  -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
TALOS_CA=$(python3 -c 'import yaml; c=yaml.safe_load(open("talosconfig")); print(c["contexts"][c["context"]]["ca"])')
for CA in "$K8S_CA" "$TALOS_CA"; do
  FP=$(printf '%s' "$CA" | cut -c201-260)   # from the body: the first ~40 base64 chars are the PEM header, same for every cert
  grep -rlF "$FP" ~ /etc 2>/dev/null        # prints file names only
done
cp talosconfig talosconfig.old; cp kubeconfig kubeconfig.old   # step 4 proves these stop working
```

Then the copies held as **data** rather than files: CI variables, pasted docs, OIDC/SSO clients
trusting the apiserver CA, and — **a secret store's Kubernetes-auth config (e.g. Vault/OpenBao `kubernetes_ca_cert`)**. Updating that config is a *replace*, not a patch: read
the whole config, change the CA, write it all back, and confirm `token_reviewer_jwt_set` is still
true afterwards — writing only the CA clears the reviewer JWT, and every client that logs in
through that auth method then fails.

## 1. Rotate, one CA at a time, naming every node

`--dry-run` defaults to **true**: run once as-is to read the plan, then again with `--dry-run=false`.

```bash
talosctl -n <cp> rotate-ca --talos=true --kubernetes=false \
  --control-plane-nodes <cps> --worker-nodes <workers> --output talosconfig.new --dry-run=false
talosctl --talosconfig talosconfig.new -n <cp> rotate-ca --talos=false --kubernetes=true \
  --control-plane-nodes <cps> --worker-nodes <workers> \
  --k8s-endpoint https://<control-plane endpoint>:6443 --dry-run=false
talosctl --talosconfig talosconfig.new -n <cp> kubeconfig kubeconfig.new   # --output writes only a talosconfig
```

## 2. Check every node finished — the last step can fail and look healthy

`rotate-ca` can fail on its final step, dropping the old CA from the accepted list, and still leave a
healthy-looking cluster: one connection reset once left most of the nodes still **trusting the old CA**.
Only a per-node read shows it. Finished means `0` and `0` on every node:

```bash
for n in <every node IP>; do
  printf '%s ' "$n"
  talosctl -n "$n" get machineconfig -o yaml | python3 -c '
import sys,yaml
for d in yaml.safe_load_all(sys.stdin):
  s = (d or {}).get("spec")
  for doc in (yaml.safe_load_all(s) if isinstance(s, str) else []):
    if doc and "machine" in doc:
      print("machine.acceptedCAs:", len(doc["machine"].get("acceptedCAs") or []),
            "cluster.acceptedCAs:", len((doc.get("cluster") or {}).get("acceptedCAs") or []))'
done
```

Re-run the rotation against any node still listing an accepted CA.

## 3. Restore all endpoints in the new talosconfig

It is written with **one** endpoint. On a multi-control-plane cluster, put the rest back, or the next
outage of that node reads as a credential failure:

```bash
talosctl --talosconfig talosconfig.new config endpoint <cp1> <cp2> <cp3>
```

## 4. Prove the old credentials are rejected, not merely superseded

```bash
talosctl --talosconfig talosconfig.old -n <cp> version   # must fail (x509)
kubectl  --kubeconfig  kubeconfig.old  get nodes          # must fail (x509)
```

## 5. After a Kubernetes-CA rotation: restart only what the evidence names

```bash
kubectl get pods -A -o name | while read -r p; do
  kubectl logs "$p" --all-containers --since=10m 2>/dev/null \
    | grep -qiE 'x509|certificate signed by unknown authority' && echo "$p"
done
```

**Roll every CNPG cluster** (`kubectl cnpg restart <cluster> -n <ns>`) regardless: instance
managers silently fall back to a cached cluster definition and keep reporting "Cluster in healthy
state" while failover and backup scheduling are broken and Postgres keeps serving.

## 6. Store the new talosconfig/kubeconfig durably

Talos has no SSH — losing the only talosconfig means losing the cluster. Commit or store them the way
the renewal section above does.
