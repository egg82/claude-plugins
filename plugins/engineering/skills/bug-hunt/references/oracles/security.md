# Security oracles — something untrusted reaches what it shouldn't

Load only when the target has the surface: a network boundary, untrusted input, multiple tenants, a plugin or extension
host, stored credentials, a rendered document, a CI system that runs other people's code. None of this applies to a
library with one caller and no I/O; running it there is how a hunt spends its budget on SSRF in a pure signing library
and never runs the test suite.

The oracle is a boundary. Name what an attacker (or a hostile host, plugin or tenant) controls, name what sits on the
other side, and the finding is a path from one to the other that the design did not intend. The stance differs from
correctness — "what do I control?" rather than "does this match the contract?" — which is why `hunt-sweep` runs it as
its own lane. Proof is the exploit executed against your own instance, never a live one.

## Run what the ecosystem ships, first

- **Dependencies:** `osv-scanner` over the lockfiles, or the ecosystem's own (`pip-audit`, `npm audit`,
  `govulncheck`, `cargo audit`). A CVE in a dependency is a lead, not a finding, until the vulnerable function is
  reachable from this code; `govulncheck` checks reachability for you, the others do not.
- **Secrets:** `gitleaks` over the whole history, not the tip — a key deleted in a later commit is still published.
  Image layers too: a secret `COPY`'d then `rm`'d in a later layer is still in the image.
- **Static:** `semgrep` with the language's ruleset, `bandit` (Python), `gosec` (Go); `trivy` over the built image;
  `zizmor` over GitHub Actions workflows.
- These run noisy. Treat each hit as a lead for the kill pass, and never report a scanner's severity as yours.

## Lenses

**Authorization by differential.** List every route or handler that touches a protected resource and line up their
guards: the one route of twelve that skips the ownership check is an IDOR you can point at, the correctness
differential applied at a trust boundary. Check the object lookup too: a guard that checks "logged in" and then fetches
by an id from the request has checked the wrong thing.

**Guards that match by name.** A check that inspects identifiers rather than resolving them is bypassable by renaming.
*(incident)* Probing a read-only SQL guard found an aliased import, `getattr` with a constant and a bound method each
writing past it (`agentic-engineering`'s `references/cases.md`). Same family: a type-checker silence that switches off
a safety check — *(incident)* `cast(LiteralString, f"…")` silenced pyright by defeating psycopg's type-level
SQL-injection guard.
Grep for casts, `# type: ignore` and `noqa` next to query, shell and template calls.

**Injection sinks.** SQL built by string formatting, `shell=True` or a shell string with interpolation, a path joined
from user input without normalizing and re-checking the prefix, template rendering of user content (SSTI), unsafe
deserialization (`pickle`, `yaml.load` without a safe loader, Java native serialization), XML parsers with external
entities on. Enumerate the sinks, then trace back to sources; reading forward from inputs misses the second-order case
where stored data reaches a sink later.

**Packet / trust-the-client.** A client-controlled field (index, count, length, position, state) used without
validation, or a packet processed in the wrong protocol state. On a target with no protocol states the second half is
inert but the first generalizes to any deserialized input.

**Session and credential lifecycle.** Tokens not invalidated on logout or password change, a session id kept across
login (fixation), JWT algorithm confusion or `none` accepted, no rate limit on login or reset, a reset token that
doesn't expire or is reusable, comparison of secrets with `==` instead of a constant-time compare.

**Secrets and data in the wrong place.** Credentials in logs, error pages, URLs (they land in proxy logs and `Referer`),
`ps` listings via an environment passed in argv, client bundles, image layers. Personal data in logs or analytics.
Stack traces and internal hostnames in error responses.

**CI and supply chain.** `pull_request_target` or `workflow_run` that checks out the PR's head and runs it with
secrets; `${{ github.event.* }}` interpolated into a `run:` script (title and branch names are attacker-controlled);
actions and base images pinned by mutable tag rather than digest; `curl | sh` in a Dockerfile; secrets exposed to fork
builds.

**Container and deploy.** Runs as root, writable root filesystem, added capabilities, `privileged`, `hostPath` or the
Docker socket mounted, a service-account token auto-mounted into a pod that needs no API access, no NetworkPolicy
between tenants.

**Side-channel.** A client-observable outcome (timing, presence, broadcast, error-vs-success, ordering) that varies
with state the client shouldn't see. Apply the expectation anchor (impact Q11): if the affected party would learn it
anyway through normal use, it isn't a vuln however clean the mechanism.

**Capability composition (seams).** Intended behaviours that each work as designed but compose across a trust or data
boundary into harm no single feature owner's threat model spans. A pass that only chains flagged defects can't find
these, because none of the pieces is a defect. Anchor on a boundary — client↔server, plugin↔core, tenant↔tenant,
persistence/transfer — enumerate the intended capabilities that cross it, and ask whether their composition moves data
or authority across in a way no single feature intended. The canonical shape: a company laptop may download company
data + a user may sign into personal iCloud + iCloud backs up the device → company data in a personal cloud, every
piece working as designed. Discipline: every step via *intended* APIs only, harm crosses a real boundary, a concrete
scenario or it isn't a finding.

**GUI leakproof.** For a protective GUI, enumerate *every* item-moving interaction (newer mechanics included) and
confirm each fires a cancellable event the platform honours — can the GUI be made leakproof at all? Generalizes to any
container UI that claims to constrain what moves through it.

**SSRF exfil ceiling.** For any server-side fetch, "blind" is an assumption to *disprove*: does the fetched content come
back via an error that echoes it, a stored or rendered artifact (screenshot, thumbnail, cached body), a returned body,
or a timing or length oracle? Test the guard against the target's *actual* internal ranges, not the textbook set — a
guard that blocks the three RFC 1918 blocks still lets through a pod network on the shared-address
range `100.64.0.0/10`, and the link-local metadata address `169.254.169.254`.

**XSS → session.** Token-in-`httpOnly`-cookie is not a clean negative: a same-origin JS exec (a `javascript:`
`window.open`/`location`, or an injected fetch) *acts as* the victim through the auto-sent cookie even when it can't
read it. URL-scheme sinks bypass HTML sanitizers — DOMPurify in front of a raw-HTML sink (`v-html`,
`dangerouslySetInnerHTML`) covers element injection, but an unvalidated `javascript:` in an attribute binding (`:href`,
`window.open(url)`) is a sink it never sees. Framework protection varies (Angular sanitizes URL bindings, React warns on
or blocks `javascript:` hrefs by version, Vue does neither) and none covers `window.open`. Enumerate URL sinks separately and check server-side scheme validation
of every *stored* URL.

**Prompt injection** where untrusted text reaches an LLM that can act: `llm-features.md`.

## Seed catalogs — carry the exploit history

Experts recall war stories associatively mid-hunt, not on demand, and often there's no expert at all. So carry a seed
catalog per domain, and **research the target's own exploit history** — closed security, dupe and crash issues,
"patched exploit" PRs, community lore — before starting. For a domain not listed, build its catalog from that history
rather than from memory.

- **Game server / plugin host:** location-disclosing side-channels (finding hidden player bases), chunk-overload → reinit or crash, item dupe
  farms, remote server crash, x-ray and loot disclosure, cross-server auth/cookie leaks, packet trust-the-client.
- **Web service:** SSRF into cloud metadata, stored XSS → session ride, IDOR across tenants, auth bypass via a parser
  differential (proxy vs app), path traversal in upload/download, SSTI in templated user content, cache poisoning via
  unkeyed headers.
- **Library / protocol:** an exception outside the documented error hierarchy escaping a public entrypoint on hostile
  input, algorithm confusion, non-constant-time comparison on secret-derived material, decompression and allocation
  bombs, round-trip infidelity across a format migration.
- **Self-hosted app:** default credentials left on, an admin UI exposed past the reverse proxy, an
  `X-Forwarded-For` trusted from any hop, an API key in a query string, a webhook endpoint with no signature check.

## Severity-calibration cases *(incidents)*

The worked evidence behind impact rules (`../impact.md`); they live here because they're game-server-specific, not
because the rules are.

**Unverified prevalence inflated a HIGH.** A run rated a dupe HIGH and "#1 economic threat" because it "rides popular
third-party plugins", naming two of them. Inspection showed one *exempts* the trigger and the other
re-implements the transform so the dupe never occurs. Naming a real actor is a citation, and a citation you haven't
inspected is fabricated.

**An unsupported configuration excluded a real mechanism.** A run found a fixed-budget login-starvation seam that only
bites with authentication disabled. That is officially unsupported, an exposed unauthenticated backend is operator
misconfiguration, and the authenticated mode, the supported config, was immune → mechanism-real, INVENTORY-only, not PoC'd. Same
category as trusting a documented insecure-by-design mode: inherent to a mode the operator opted into, not a
platform defect.
