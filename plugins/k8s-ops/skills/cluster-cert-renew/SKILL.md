---
name: cluster-cert-renew
description: "Check and renew the Talos/Kubernetes cluster admin certificates (kubeconfig client certs, talosconfig os:admin certs). Use when kubectl or talosctl says \"the server has asked for the client to provide credentials\" or \"certificate has expired\", to see how long the certs have left, to renew before expiry, to recover after the talosctl cert expired, or to rotate a cluster CA (`talosctl rotate-ca`)."
---

# Cluster cert renewal

Talos issues both admin certs with a **1-year TTL**, and because they are minted together at
cluster creation they expire together. Nothing rotates them automatically.

The failure looks like a connectivity problem and is not:

```
error: You must be logged in to the server (the server has asked for the client to provide credentials)
```

## Check

```bash
python3 certscan.py check                 # table of every cert found on this host
python3 certscan.py notify                # same, but POST anything needing attention to a webhook
python3 certscan.py --warn-days 60 check  # widen the window
```

It scans `$KUBECONFIG_PATH` (default `~/.kube/config`) and `$TALOS_GLOB` (default
`~/.talos/*/talosconfig`), and reports a source it cannot read as **UNKNOWN** rather than omitting
it — a host with no talosconfigs must not look identical to a host whose certs are healthy.
`notify` sends nothing when everything is clear; the webhook comes from `$CERT_ALERT_WEBHOOK`, or
from `$CERT_ALERT_WEBHOOK_CMD` if you keep it in a secret store such as Vault/OpenBao.

Run it weekly from cron or a DAG runner, on one host that holds every cluster's configs. Certs are
minted with a 1-year TTL, so a weekly check has plenty of margin.

## Renew — before expiry

Two commands per cluster, while the existing talosctl cert still works. Do the talosconfig
first: it is what authorises the kubeconfig pull. (General Talos operations: `talos-ops`.)

```bash
# 1. fresh os:admin cert.  -n is REQUIRED: `config new` refuses a multi-node target.
#    Use the control-plane endpoint already listed in that cluster's talosconfig.
talosctl --talosconfig <talos-dir>/<cluster>/talosconfig -n <cp-endpoint> config new /tmp/tc.new

# 2. node-issued kubeconfig, using the cert from step 1
talosctl --talosconfig /tmp/tc.new -n <cp-endpoint> kubeconfig /tmp/kc.new --force
```

**`config new` drops the `nodes` list and renames the context to `admin@<cluster>`.** Carry the
original `endpoints`/`nodes` across and keep the old context name, or every later `talosctl`
invocation against that file needs an explicit `-n`.

Then merge. The server URL and CA data are normally **identical** to what is already in
`~/.kube/config`, so the whole merge is swapping two fields on the `admin@<cluster>` user —
`client-certificate-data` and `client-key-data`. Assert the user exists exactly once and that the
context list is unchanged after writing; never replace the file wholesale, because per-host
kubeconfigs carry different context sets.

Verify against the live cluster, not the file. Then copy to the other admin hosts (same two-field
swap — do not copy the file) and update `<talos-dir>/<cluster>/{talosconfig,kubeconfig}`.

## Recover — after the talosctl cert has expired

Once the `os:admin` cert lapses, `talosctl` itself is locked out and the section above cannot run.
The way back in is the cluster's own controlplane machine config, which carries both CAs
**including their private keys**:

```bash
talosctl gen secrets --from-controlplane-config <talos-dir>/<cluster>/<cp-node>.yaml -o /tmp/secrets.yaml
talosctl gen config --with-secrets /tmp/secrets.yaml --output-types talosconfig \
         -o /tmp/tc.new <cluster> https://<endpoint>:6443
```

Then carry over `endpoints`/`nodes` as above and continue from step 2 of the normal path.

**Confirm the CAs in that file are still the live ones before trusting them** — a config on disk
can predate a CA rotation, and a cert minted from a stale CA fails in a way that looks identical
to the expiry you are fixing:

```bash
openssl s_client -connect <node>:6443 -CAfile cluster-ca.crt </dev/null   # expect: Verify return code: 0
openssl s_client -connect <node>:50000 -CAfile machine-ca.crt </dev/null  # apid, same
```

The new CA fingerprint must match the old one after minting. If it does not, stop — you have
generated a parallel PKI, not renewed anything.

Shred the secrets bundle afterwards; it holds every cluster secret and is regenerable on demand.

## Rotating a CA (not just renewing certs)

Replacing the Talos or Kubernetes **CA** — hygiene or suspected compromise — is a different job
with silent half-finished states. Method and checks: `references/ca-rotation.md`.

## Gotchas

- The base64 blob in a kube/talos config decodes to **PEM**, not DER. `openssl x509 -inform DER`
  fails on all of it, which reads as "every cert is corrupt".
- A **non-interactive SSH session gets none of the profile PATH** — `kubectl`, `talosctl` and any
  secret-store CLI are not found by bare name. Use absolute paths in anything a scheduler runs.
- The git key is **passphrase-protected**, so hosts without an ssh-agent cannot pull from
  the git host non-interactively. `<talos-dir>` reaches the config host by rsync, not `git pull`;
  re-sync it when you renew, or its copy will report expiry that has already been fixed.
