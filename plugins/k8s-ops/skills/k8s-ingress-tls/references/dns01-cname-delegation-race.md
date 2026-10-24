# DNS-01 CNAME delegation race, and its renewal landmine

**The delegation CNAME wasn't published yet (a race, not a misconfiguration).** With CNAME-delegated
DNS-01 — `_acme-challenge.<host>.<zone>` CNAME'd to a delegated ACME zone — cert-manager follows that
CNAME to decide *where* to write the TXT. If external-dns publishes the delegation on its own
reconcile cycle while cert-manager presents the challenge seconds later, the CNAME doesn't exist yet,
so the TXT goes to the wrong place and the self-check waits forever. **On a new host this is close to
a 100% hit rate, so check it every time.**

Confirm it rather than guessing: the challenge says `Presented: true` with `Waiting for DNS-01
challenge propagation`, `dig +short TXT _acme-challenge.<host>.<acme-zone>` is **empty**, while
`dig +short CNAME _acme-challenge.<host>.<zone>` **does** resolve — and external-dns logs show it
adding that CNAME *after* cert-manager's Presented timestamp.

**Fix:** once the delegation resolves, delete the pending Order. cert-manager re-presents, now finds
the CNAME, writes the TXT to the right record, and LE validates in about a minute. Nothing needs
changing in the manifests.

**The race leaves a landmine that goes off at the first renewal, months later.** The TXT written
to the *undelegated* name (`_acme-challenge.<host>.<zone>`) is not always cleaned up, and some
DNS providers (Cloudflare, for one) will then serve both it and the delegation CNAME at that name. The
first issuance still succeeds. Every renewal fails with `403 unauthorized: Incorrect TXT record
"<old token>" found at _acme-challenge.<host>`, because a TXT query gets the stale record and
never follows the CNAME. The Certificate stays `Ready=True` on the old cert while
`failedIssuanceAttempts` climbs, so it looks healthy until the expiry alert fires.
Confirm with `dig +short TXT _acme-challenge.<host>.<zone> @<authoritative-ns>`: it should return
nothing when no challenge is live. **Fix:** delete every TXT sitting directly on an
`_acme-challenge.*` name outside the delegated zone (list them via the provider's API; one pass
catches the certs that haven't come due yet), then trigger a renewal. Without `cmctl`, add
`Issuing=True` to the Certificate's status conditions with `kubectl patch --subresource=status`,
which is exactly what `cmctl renew` does.
