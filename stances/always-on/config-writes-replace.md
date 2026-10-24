---
name: config-writes-replace
description: A config write usually REPLACES the whole object, so it silently deletes every field you did not send — read-modify-write, then read back and count the fields
metadata:
  type: feedback
---

Most config APIs take the whole object, not a patch — `vault kv put`, `vault write
auth/<mount>/config`, a cloud CLI's update command that replaces a whole list, an identity provider's app-config `PATCH`,
`kubectl apply` of a partial spec. Each **deletes the fields you didn't mention**, reports success, and
leaves the field you meant to change correct — so spot-checking your change confirms it, and the
breakage surfaces hours later as someone else's outage. A CA rotation once cleared Vault's
`token_reviewer_jwt` and every namespace-scoped `SecretStore` began failing `namespace not authorized`.

**Read the object, change one field, write it all back — then read back and COUNT**: field count
unchanged, untouched values still hash the same. Before writing to an unfamiliar endpoint, ask
whether it merges or replaces; prefer per-field APIs (`kubectl patch --type=json`, a CLI's `--add` form).
The replacing commands are usually the older, plainer ones that feel safest to type.

Relates to
[[preserve-before-destroying]], [[verify-dont-anchor]].
