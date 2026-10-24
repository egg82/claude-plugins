---
name: selfhosted-options
description: "Research and recommend a self-hosted app for a job — \"I want something that does X, what are my options?\" or \"is there something better than X?\" Use whenever the user is choosing between self-hosted tools, asking what exists for a homelab need, thinking of switching away from something they run, or evaluating an arr-stack or Docker/Kubernetes app. Vetting one known repo is repo-vet."
---

# Choosing a self-hosted app

Two question shapes, one pipeline:

- **Greenfield** — "I want something that does X, what's out there?"
- **Incumbent** — "I run X, is there better?" (X is often assumed broken; frequently it isn't)

The pipeline: elicit requirements → *(incumbent only)* diagnose what's actually wrong → landscape sweep → community sentiment → cold repo-vet on the shortlist → one recommendation with named gaps.

The value isn't listing projects — the user can find a GitHub topic page themselves. It's telling them which ones survive contact with evidence, and which of their assumptions didn't.

## Step 1 — Ask everything up front

Do this before any research. The failure this prevents: the user drip-feeds context ("oh, and I need it automatic", "oh, and it has to read from a service I already run") *after* you've searched, and each reveal invalidates work already done. One round of questions at the start is cheaper than three rounds of rework, and the user usually knows all of it on turn one — they just don't know which parts matter to you.

Use `AskUserQuestion` with concrete options rather than open prose. People choose faster than they compose, and options surface constraints they wouldn't have volunteered.

Cover these — trim to what's genuinely unknown, and infer what you safely can from the repo, the running system, or the conversation rather than asking:

- **The actual job.** What must it produce or do? Not the category — the outcome. "Watch a folder and file new documents into the right place, searchable" beats "document tool."
- **Automatic or interactive?** Unattended on a schedule, or a thing they open and drive? This eliminates more candidates than any other question, and tools rarely advertise which they are.
- **What already exists that it must plug into.** Existing apps, accounts, data sources, listening/watch history, APIs, auth. Data they already produce is leverage — it can make a whole class of tool viable or pointless.
- **Deployment constraints.** Kubernetes or Docker? Tolerance for backing services (a DB? a queue? Redis?)? Non-root, read-only-rootfs, or other posture requirements? Is a nightly/experimental branch acceptable?
- **The must-keep feature.** Especially in incumbent mode: what would they actually miss? A recommendation that silently drops the one feature they named is a failed recommendation regardless of how much better the replacement is on paper.
- **Dealbreakers.** Mandatory paid API key, telemetry, a specific license, cloud dependency.
- **Cost of being wrong.** A tool that writes to an existing library is a different risk class than one that only reads. Ask what it's allowed to touch.
- **Who has to use this, and what do they already know?** The adoption question — see below. Ask it here, not after the recommendation.

For **incumbent** mode, also ask: what specifically prompted this, when did it start, and what changed around then. That last one matters more than it sounds — see Step 2.

**Weigh whether the safer option will actually be USED, and say so out loud — a paved path nobody walks is worth zero.** Risk findings are legible: CVE counts, advisory cadence, bus factor, a `failurePolicy: Fail` webhook. Adoption friction is not — it lives in whether the people who must use the thing know git, will read a second page, or will open a merge request. So the legible number wins by default, and a recommendation lands that is safer *and never adopted*, which is strictly worse than the risk it avoided.

One vet's ten-advisories "don't adopt" reversed in a single reply because the users didn't know the tool the safe path depended on — nothing in the vet could have surfaced that (full case: `references/adoption-worked-case.md`).

When the recommendation turns on it, **name the trade in the report** — *this is riskier and people will use it* is a legitimate verdict, but only when stated as a choice rather than smuggled in. And be ready to reverse: if you already recommended on risk alone and the adoption answer arrives afterwards, say plainly that it changed the call.

## Step 2 — Incumbent mode: diagnose before you shop

**Do not accept "X is broken" as a premise.** Reproduce it against the running system first.

This is the step that earns the skill its keep. A user asks to replace a tool because it's been failing for weeks; the failure turns out to be a crashing dependency, a misconfiguration, or an upstream API change — and the tool they were about to spend a weekend migrating away from was never the problem. Migrating on a misdiagnosis costs the weekend *and* leaves the real fault in place to break the replacement too.

Work from the actual system, not the symptom description:

- Read the logs — and don't stop at the top-level error. A generic "failed to add" often wraps a specific cause the app discarded.
- Check where the app *stores* failure reasons. Many surface a red badge in the UI while writing the real error to a database column. Query it.
- Check the dependencies' health, not just the app's: restart counts, OOM kills, segfaults, exit codes, resource limits. An app is often the victim.
- Confirm connectivity and latency to the things it integrates with, rather than assuming a network cause. Measure it.
- Compare against siblings. If five apps share a base config and only one misbehaves, the base is fine and the difference is the lead.

Then state plainly which component is at fault. If the incumbent is healthy and something underneath it is broken, say so and offer the fix — the honest answer to "should I switch?" is sometimes "no, and here's the one-line change." The user asked for a recommendation, not permission to migrate.

Note the errors the incumbent *swallowed* along the way. A tool that hides its own failure reasons is a genuine mark against it even when the root cause is elsewhere, because it's why the problem went undiagnosed for weeks — and that belongs in the final report as a real finding.

## Step 3 — Landscape sweep

Delegate to a subagent, and tell it in the brief to load `search-craft` before searching (steps 3 and 4 both). Ask it to find genuine candidates and, crucially, to **exclude adjacent tools that solve a different problem** rather than padding the list. In most niches half the apparent options do something related but not the thing — downloaders where you need discovery, sync where you need recommendation. List those separately under "different problem, don't confuse these" so the user can see they were considered and rejected.

Have it report per candidate: what it actually does, how much of the job it covers, last release, contributor count, deployment shape, and whether it looks maintained, abandoned, or vibe-coded.

Also make it check whether the **incumbent's own platform already does the job natively**, or whether a small amount of glue would. "Run less software" is a legitimate winning answer and deserves honest evaluation rather than dismissal for being unexciting. Equally, verify it actually works before recommending it — platform features get advertised in docs long before, or long after, they function.

If the field is genuinely thin, the right answer is "nothing here beats what you have." Say that instead of inventing contenders.

## Step 4 — Community sentiment

Stars measure how well a launch post did. They say nothing about whether anyone still runs the thing. Sentiment is where you find out that the maintainer deletes inconvenient issues, or that a "1,000-star" project has one actual user.

Run this as its own subagent, and have it read `repo-vet`'s `references/community-sources.md` first (in the vetting plugin) — it records which sources work, which are blocked, and which return convincing garbage. That file lives with repo-vet because vetting any single repo needs the same outside view; it's shared, not duplicated. It exists because a frozen search index silently returned zero results for a project that hadn't been created yet when the index stopped updating, which reads exactly like "nobody discusses this."

What to extract:

- **Runners vs upvoters.** How many people describe actually operating it, versus "looks cool, will try"? These numbers differ by an order of magnitude and only the first one predicts anything.
- **Concrete complaints.** What breaks, what got abandoned, what people migrated to and why.
- **Maintainer conduct.** Responsive? Hostile? Do they delete issues or block reporters? This is decision-relevant in a way star counts aren't — a maintainer who curates the defect list makes the issue tracker useless as a health signal.
- **Slop accusations**, and whether anyone actually investigated them or just repeated them.

Weigh volume honestly. In small niches two comments is not a consensus, and one loud critic is not a verdict. Say "one person said X" when that's what happened.

## Step 5 — Repo-vet the shortlist

Vet the top 3–4 with the `repo-vet` skill, one **fresh agent per repo, launched in parallel**.

Cold matters. An agent carrying your accumulated opinion tends to confirm it, and the whole point of the vet is an independent read. Write each prompt self-contained: the repo URL, the user's requirements from Step 1, and the specific questions that candidate raises. Do not include your verdicts about it, or the other candidates' results.

Give each vet the questions that actually decide this choice — generic vetting produces generic findings. Worth directing attention at:

- **Claims vs reality** for the specific integrations the user needs, not the feature list in general.
- **Bus factor** for a project you'd depend on daily, not in the abstract.
- **Data-integrity risk**: can it delete or modify existing data, or is it add-only? Trace the write paths.
- **Credential handling** — plaintext at rest is common in this space, and it makes the user's backups secret material.
- **Automation**: is there a real scheduler, or does it need a human?
- Any **adoption cost** unique to it — an experimental branch, a mandatory paid API key, a heavy stack.

How each vet organizes itself — coverage tiering, its own subagent fan-out, live instances, what counts as a health signal — is `repo-vet`'s job and it handles that. Don't re-teach it. Your responsibility is what it can't see: **keeping the vets sealed off from each other.** Each candidate gets its own agent and its own workspace, and no vet learns another's verdict. That isolation is what makes the comparison worth anything — independent reads catch each other's errors, and today's clearest example was one agent's reasonable inference about a forked project being overturned by another agent that had actually tested it. **You are the only place candidates get compared.**

One selection-specific signal repo-vet doesn't cover: **membership in curated directories** (awesome-selfhosted and similar). Presence means someone vetted it; absence is weak evidence for anything under a year old, since inclusion requires a human to open a PR. Grep the raw list rather than the rendered page, and run a control probe (a tool you know is listed) so a failed download can't masquerade as "not listed."

## Step 6 — Report

Deliver in conversation. Lead with the verdict and defend it; the user wants a call, not a survey.

Structure loosely as:

- **The recommendation**, stated plainly, with the strongest reason first.
- **Why the runners-up lost** — one or two lines each. This is what makes the recommendation trustworthy.
- **What it costs** — migration effort, features given up, new risks taken on.
- **Coverage gaps**, explicitly. Which sources you couldn't reach, which claims are secondhand, which conclusions rest on one person's comment.

Distinguish three things throughout, and never let them blur: **verified** (you read the code or ran the command), **secondhand** (someone reported it), and **unreached** (you couldn't check). A blocked fetch is not evidence of absence — before writing "no reports exist," confirm the probe pointed somewhere real and could have returned a hit. Run a control query that you know should match; if it comes back empty too, your probe is broken, not the world.

**Apply that to your own agents' reports, which is the easiest place to forget it.** A subagent's report is a *primary* source for what it did — the command it ran, the endpoint it probed, the file it read — and a *secondhand* source for everything it merely read somewhere. Both arrive in the same confident register, so a forum claim an agent relayed can get promoted to "finding" on its way through you. That has produced concrete errors: a hardware requirement quoted from community comments turned out to be misattributed to the wrong project and wrong by 4x in the reassuring direction, and a "this project has no real users" read collapsed when someone actually counted distinct issue filers. Before passing a striking claim to the user, check whether the agent *verified* it or *heard* it — and if it's load-bearing for the recommendation, send someone to confirm it rather than attributing it with more confidence than its source earned.

Correct yourself out loud when the evidence turns. If you recommended something earlier in the conversation and a vet undercuts it, say so directly — a reversal with reasoning is worth more than a consistent story, and burying it costs the user the thing they're paying you for.

If the honest answer is "keep what you have," give that answer. It's frequently correct in incumbent mode, and it's the one a recommendation engine is structurally biased against producing.

**Past evaluations live in `~/.claude/local/selfhosted-options/verdicts.md` — check it first and append new ones.** A completed sweep is expensive; don't repeat one that only needs a freshness check.
