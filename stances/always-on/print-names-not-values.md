---
name: print-names-not-values
description: When inspecting config, env or secrets, print field NAMES plus a hash or length — never values; redact by allow-list because a deny-list of secret-ish substrings always misses one
metadata:
  type: feedback
---

When dumping config, env or secret material, print **names plus `<set>`/`<empty>`/`sha256[:12]`/length,
never values**; name in advance any single field you genuinely must see. A transcript cannot be
un-published, and one leaked OIDC secret cost a rotation across several secret-store paths, derived
Secrets in more than one namespace, restarts and a monitoring rule — count that chain before printing.

- **Allow-list, never deny-list.** A guard of `'pass' in f or 'user' in f` missed `client_secret`;
  the set of words meaning "secret" is open. Print fields you decided are safe; reduce the rest.
- Hashes answer the real questions (set? changed? same in two places?) — comparing a credential
  across two namespaces by hash beat seeing it.
- **A hash cannot tell you the probe failed.** A redacted `len=20` was the literal string
  `(Property not found)`. Test the raw value against the API's not-found/null/error shape BEFORE
  reducing it, and give the probe a control field known to exist and one known not to.
- **A `ps` listing is a credential surface** — `podman exec` / `distrobox enter` put the whole
  environment in argv. It has leaked a key here twice.
- **Backstop, not primary control:** the secret-guard plugin's secret-redact hook (PostToolUse, `Bash|Read`)
  gitleaks-redacts values before they reach context. The command has already run, it covers only the
  matched tools, and a redaction banner's count is findings acted on, not proof the output is clean.
  **It also blinds you:** fetch a secret in a separate command from the probe that uses it, or every
  error line gets redacted too.
- **Diffing near-duplicate configs prints exactly what differs — the secret.** Mask values on both
  sides (`sed -E 's/[A-Za-z0-9]{24,}/<v>/g'`) or compare per-line hashes.

**If a value does escape, say so first, before anything else in the message** — rotation is cheap and
only starts once someone knows. Rotate by adding the new credential, verifying it, then deleting the old.

Incidents and why the hook exists: `~/.claude/memory/evidence/print-names-not-values.md`. Relates to
[[verify-dont-anchor]], [[preserve-before-destroying]].
