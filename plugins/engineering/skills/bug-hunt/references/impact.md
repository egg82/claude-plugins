# Impact stage — the questions and the gates

Open this for the impact pass on any finding that survived the kill: the twelve questions, the HIGH
gate, and the reasoning behind both.

## The questions

**1, 2, 3, 4, 6, 8 and 12 are the general spine — answer them for every finding, whatever its
domain.** They are the mechanism → who → where → ceiling → real callers → whose fault → honest floor
chain, and each does real work on a mundane bug. **5, 7, 9, 10 and 11 are conditional on the finding
being security-shaped.** On a defect with no attacker and no trust boundary they return degenerate
answers, and forcing a one-line bug through them is how it inflates into a page.

1. **MEAN, not DO** — trace mechanism → observable/trigger → reach → real consequence → violated expectation; "returns the wrong value" is never the answer.
2. **WHO / HOW / HOW OFTEN** — unprivileged user? which dependent, and is it widely used? a migration every deployment runs? Prevalence *is* severity. For performance, cost × frequency on real paths (`oracles/performance.md`).
3. **WHERE it bites** — catastrophic where state persists and compounds, negligible where it's discarded each run; name the environment.
4. **WORST CASE, then BOUND it** — push to the ceiling, then honestly cut back to what's reachable; state both.
5. **UNANTICIPATED USE** — can intended capabilities compose into harm across a seam, not just defect chains?
6. **REAL CONSUMERS** — who calls this, what do they store in it? Decides hazard-today vs proactive-hardening; don't assume.
7. **PRECEDENT** — same class as a known-abused exploit, or as a failure mode this domain keeps re-growing? Name the property that matches, not a shared umbrella.
8. **FAULT** — platform mishandling reasonable use (in) vs consumer misuse (out); the differential labels origin, doesn't gate scope.
9. **PRIVILEGE GATE** — reachable only behind an admin/elevated gate defaults to **LOW** (handing out privilege is the operator's fault), unless severe *despite* the gate — takes down the service, or corrupts/leaks *other* unprivileged users' data at scale.
10. **STRUCTURAL AXES** — integrity vs confidentiality (forge vs only read); client-stored vs server-authoritative (forgeable vs merely readable). The same token is safe held server-side, dangerous handed to the client.
11. **EXPECTATION ANCHOR** — the leak/side-channel tie-breaker: if the affected party would learn it anyway through normal use, it's not a vuln however clean the mechanism.
12. **DEMOTE readily and SAY SO** — most findings are smaller than their mechanism looks; the honest LOW protects the credibility of the few that are real.

## The HIGH gate

Applies to any domain — a headline data-corruption or "10× slower" claim earns the same scrutiny as a
headline exploit. Apply Q4 hardest on anything you're about to call HIGH, because a HIGH that turns
out to be a nothingburger poisons the whole batch. To call a finding HIGH you must **exhibit a
concrete scenario** with real actors, config and deployment producing the harm, and rate on *that*;
the theoretical maximum is context, not the rating. Reject **contrivance** (six unlikely things lining
up, or a chain whose middle link requires the actor to already have the outcome) and **unproven
prevalence** ("assume a caller misuses X" — go check, and until shown, cap the rating).

## Why impact is its own stage

This is the biggest lever, and it is **not** a second skeptic re-doing the kill. The kill already did
the code-bound severity check ("real, but oversold"); don't repeat it. Impact differs by **axis and
inputs** -- KILL asks "is it TRUE?" (**repo-bound**: claim + code + tracker); IMPACT asks "does the
WORLD get hurt, and how do we say it?" (**world-bound**: a kill-certified finding + the real world).

The load-bearing point: the highest-value impact questions **cannot be answered from inside the
repo** -- how prevalent the trigger is, what environment it runs in, whether real consumers use the
surface dangerously, whether it matches a precedent that actually burned people. Those answers live in
the ecosystem, in how systems are really deployed, and in exploit history. So **impact is the one
stage licensed to leave the repo** (ecosystem/web search, deployment reality, precedent) -- and it runs
*only on kill-survivors*, so no world-research is spent on false findings.

**This stage is class-agnostic, and that's the point.** "Who is actually impacted, through what
vector, how often, and does it matter?" is the question that separates a reportable defect from a
thing that *could* be a problem -- and it is exactly as load-bearing for a data-corruption bug, a
silent-truncation bug, or a wrong default as it is for an exploit. A hunt that skips it ships a pile
of maybes and makes the reader do the triage. The vocabulary leans security because that's where it
was sharpened; the reasoning is not security's.

## The running system as a severity-resolver

**When the target is deployed and you can reach it, the running system is another source to leave the
repo for** -- and often *the* one that settles severity. A finding whose severity is "conditional"
(depends on how many users exist, whether a flag is set, whether a default was changed, whether a
credential is strong, whether that dangerous permission was delegated) can usually be *resolved* by a
read-only query of the live DB / config / state, instead of shipping the conditional. This cuts both
ways: it downgrades (the exploit needs a non-admin account and there are none) and it confirms (the
backup annotation really is missing, the delegated permission really is granted) -- so it's a
severity-*resolver*, not a severity-inflator. Relatedly, **state a chain's terminus precisely and
don't reflexively extend it**: "app-admin takeover" and "fleet compromise" differ, and the second
needs a code-exec (or equivalent) primitive the first doesn't -- name the exact stopping point.

## Named actors are citations

The subtle trap inside prevalence: **naming a specific real actor as evidence is a citation, and a
citation you haven't inspected is fabricated.** "Rides library X", "every deployment does this" --
naming it is *not* checking it; only reading its code or docs turns the guess into evidence. This is
the impact-layer form of *never quote from memory*. If a severity depends on such a claim, verify the
named actor -- that's what leaving the repo is *for* -- or state it unverified and cap the rating. The
case that produced this rule is in `oracles/security.md`; the failure was rating a finding HIGH on two
named dependents, one of which exempted the trigger and the other of which made it impossible.

## Realistic is not frequent

A rare-but-genuine catastrophic scenario is still high *impact* -- demote it on incidence, not by
pretending it isn't severe. A rare input that permanently locks a user out of their own data is
high-impact / low-incidence, not dismissed. The gate kills contrived and unproven claims, not
rare-but-real ones.

## The supported-configuration gate (reportability, not severity)

Before a finding earns REPORT, ask whether *every* configuration that triggers it is one the project
officially **supports and defends**. A defect reachable only in an unsupported mode, or only in an
operator-misconfigured deployment, is **not reportable** however clean the mechanism or PoC -- the
boundary is threat model, not proof, so a PoC won't move it across the line. This is distinct from Q9:
Q9 *demotes* an in-scope bug to LOW because the operator handed out privilege; this *excludes* the
finding because the triggering deployment is outside what the platform backs. Know the project's
supported-config / threat-model boundary before you rate -- where one exists it is often *the* line
between REPORT and INVENTORY. Worked case in `oracles/security.md`.

**Two limits on this gate, or it eats real bugs.** It is a *threat-model* instrument: it answers "does
the project undertake to defend this configuration against an adversary," and most projects
articulate that boundary only for security. Where the project has stated no such boundary, the default
is **include, not exclude** -- an unarticulated threat model is an absence of evidence, not a
declaration that nothing is defended. And "unsupported" means *documented as unsupported*, never
merely non-default: a corruption bug that only fires under `--parallel`, or on a config the docs
actively recommend, is a plain defect and this gate has no opinion on it. Ask the gate only when a real
stated boundary exists to consult.
