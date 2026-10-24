---
name: k8s-ingress-tls
description: Exposes cluster services externally with working TLS. Use when exposing a service outside the cluster, debugging ingress/Gateway routing, TLS certificates not issuing (cert-manager), or getting external traffic in.
---

# k8s-ingress-tls

BLUF: getting traffic in is a chain — **DNS → entrypoint (LoadBalancer IP / tunnel / NodePort) → ingress controller or Gateway → Service → Pod**. TLS is a parallel chain owned by cert-manager. Debug by walking the path top-down and naming the hop that breaks. If the Service has no Endpoints, stop here and use **k8s-triage** — that's a pod/selector problem, not an ingress problem.

## The request path (walk it top-down)
1. **External DNS** — does the hostname resolve to your entrypoint IP? `dig +short host`. Wrong/missing A record = nothing else matters.
2. **Entrypoint** — the public/LAN IP where traffic lands: a LoadBalancer Service IP (MetalLB), a cloud LB, a Cloudflare Tunnel, or a NodePort. See "external IP" below.
3. **Ingress controller / Gateway** — routes by host+path to a backend Service. Breaks on wrong class, wrong host/path, or a controller that isn't running.
4. **Service** — must have `ENDPOINTS` (ready pods matching the selector). No endpoints → k8s-triage.
5. **Pod** — actually serving on the target port.

Each hop has a distinct symptom: DNS fails = NXDOMAIN; entrypoint fails = connection refused/timeout; ingress fails = 404/503 from the controller; service fails = 503 with empty upstream.

## Ingress controllers vs Gateway API
- **ingress-nginx / Traefik** use the `Ingress` kind. An Ingress needs: `spec.ingressClassName` (matching an installed controller), correct `host` + `path`, and a backend Service **with Endpoints**.
- **Gateway API** (newer) uses `Gateway` + `HTTPRoute`. An HTTPRoute needs a `parentRefs` Gateway whose `gatewayClassName` matches an installed controller, plus `hostnames` + rules pointing at a backend Service.
- Inspect: `kubectl get ingress,svc -A` / `kubectl get gateway,httproute -A`; `kubectl describe ingress <n>` (or `describe httproute <n>`) — check the Address, backend, and events.
- The controller does the actual routing — **read its own pod logs**: `kubectl -n <ns> logs deploy/ingress-nginx-controller` (or the traefik/gateway controller). 404s and cert errors show up here.

## Getting an external IP in a homelab
- **MetalLB** hands LoadBalancer Services a LAN IP (L2 or BGP). Check `kubectl get ipaddresspool,l2advertisement -A` and confirm the Service actually got one: `kubectl get svc -A | grep LoadBalancer` — look for a real `EXTERNAL-IP`.
- **Service stuck `<pending>` EXTERNAL-IP = no LB provider** answered the request. Either MetalLB isn't installed/healthy, the `IPAddressPool` is exhausted/misscoped, or (bare metal) there's no cloud LB at all. This is the #1 homelab ingress gotcha.
- **Cloudflare Tunnel / cloudflared** exposes services with **no inbound ports** (outbound-only from the cluster) — ideal behind CGNAT or a locked-down router. Routing config lives in the tunnel, not an Ingress.
- **NodePort / hostPort** = crude fallback: reachable at `<nodeIP>:<30000-32767>`. Fine for testing, ugly for real use.

## cert-manager (the TLS half)
Chain: `Issuer`/`ClusterIssuer` → `Certificate` → `CertificateRequest` → `Order` → `Challenge` → issued Secret.
- **ClusterIssuer** is cluster-wide; **Issuer** is namespaced. Types: ACME (Let's Encrypt) for public certs; self-signed or a CA issuer for internal-only.
- **DNS-01** is the common homelab choice: works for internal hosts and **wildcards**, needs no inbound ports (proves control via a DNS TXT record). **HTTP-01** needs port 80 reachable from Let's Encrypt — often not possible at home.
- **Ingress-shim**: put `cert-manager.io/cluster-issuer: <name>` as an annotation on the Ingress (with a `tls:` block naming the secret) and cert-manager auto-creates the `Certificate`. No manual Certificate object needed.
- The issued cert lands in a TLS Secret the Ingress/Gateway references. Managing/inspecting that Secret → **k8s-secrets**.

## cert-manager failure playbook (cert stuck not-Ready)
Walk the chain in order — the block is at whichever object is not Ready:
```
kubectl get certificate,certificaterequest,order,challenge -A
kubectl describe certificate <n>          # -> points to the CertificateRequest
kubectl describe certificaterequest <n>   # -> points to the Order
kubectl describe order <n>                # -> points to the Challenge
kubectl describe challenge <n>            # the real error is usually here
```
Common causes:
- **Wrong/missing `issuerRef`** — Certificate can't find the (Cluster)Issuer, or names an Issuer in the wrong namespace.
- **DNS-01 provider creds/permissions wrong** — challenge stuck `pending`; the TXT record never gets created (bad API token/zone scope).
- **HTTP-01 challenge not reachable** — port 80 not exposed to the internet.
- **Rate-limited by Let's Encrypt** — use the **staging** ClusterIssuer while testing, switch to prod once it works (prod has tight weekly limits).
- **Clock skew** on nodes — ACME/TLS validation fails on bad time.

  **Both of these leave no trace on the chain above.** A clean walk through
  Certificate/CertificateRequest/Order/Challenge is what you'd also see if the request had never
  reached the issuer — so a clean walk when the cert still isn't issuing is a false negative, not an
  exoneration. When the walk comes back clean, check the issuer's own rate-limit state next (Let's
  Encrypt's rate-limit page for the account) and the nodes' clocks (`chronyc tracking` /
  `timedatectl`), rather than re-walking the same objects.
- **CNAME-delegated DNS-01 has a startup race and a renewal landmine.** On a new host, a clean
  Certificate/CertificateRequest/Order/Challenge walk that still isn't issuing is close to a 100% hit
  rate for this — and months later the same setup can fail every renewal while `Ready=True` still
  shows the old cert. See `references/dns01-cname-delegation-race.md` for the fix (delete the pending
  Order; or purge stale TXTs outside the delegated zone).

## Quick sanity tests
- LB Services + their IPs: `kubectl get svc -A | grep LoadBalancer`
- Hit the ingress bypassing DNS: `curl -k -H 'Host: app.example.com' --resolve app.example.com:443:<entrypoint-ip> https://app.example.com/`
- See the served cert (issuer, SAN, dates): `openssl s_client -connect <host>:443 -servername <host> </dev/null 2>/dev/null | openssl x509 -noout -subject -issuer -dates`
- Confirm endpoints exist before blaming ingress: `kubectl get endpoints <svc> -n <ns>` (empty → k8s-triage).
