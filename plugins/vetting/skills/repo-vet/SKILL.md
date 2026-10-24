---
name: repo-vet
description: "Vet a third-party repo before you adopt, depend on, or self-host it — a go/no-go \"should I trust this?\" pass: maintenance health, claims vs reality, footguns, AI-slop, redundant systems. Use when evaluating an OSS project, a dependency, or a tool someone proposes to rely on (often vibe-coded). NOT a repo you'll contribute to (repo-orient), its bugs (bug-hunt), or Claude Code tool fit (cc-tool-vet)."
---

# Vet a repo before you depend on it

You are deciding whether to **trust and adopt** this code, not change it. The output is a
**go/no-go verdict plus the evidence**, and it must point at ground truth (the stale commit, the
unwired button) so the user can confirm -- it is not a summary they take on faith. Distinct from
`/init` (which writes an agent manual) and from a generic summarizer.

**If you loaded this inline, in the conversation that raised the question, stop and hand the whole
vet to a fresh subagent** (repo + this skill, no priming about whose it is or the expected verdict) —
see *Run this skill from a COLD agent* below.

## What to check

1. **What it actually is and does** -- the honest 50k-foot view, with the README's marketing
   stripped off. What does it build/run, and what problem does it really solve?
2. **Maintenance health** -- commit recency and cadence, open-issue/PR responsiveness, last
   release, bus factor (is it one person?), and abandonment signals. A capable-but-solo,
   high-burst, recently-started repo is a *risk signal* for anything you'll depend on. **Place it on
   a spectrum with a real top end:** the gold standard is a long-lived, genuinely multi-maintainer
   project where major issues are rare and fixed fast; say where this repo
   lands relative to that. A solo, freshly-started repo is a categorically weaker bet than a
   battle-tested multi-dev one *even when its code is clean* -- one person's attention is the single
   point of failure. But don't make the gold standard a rejection machine: **scale the maturity you
   demand to the blast radius.** A stateless helper you can rip out in minutes needs far less than
   something custodying your data or holding your credentials. **Read the
   commit shape** (suggestive, never definitive): a single "materialized fully-formed" genesis
   commit, vague messages ("add feature", "update"), no iterative build→test→fix story, or the
   opposite -- one maintainer with a superhuman commit mountain / commits each churning a boatload
   of files -- all smell machine-authored. **And check the person behind it:** their other repos,
   their PR merge-ratio, whether this pattern repeats -- a serial fast-scaffold-then-abandon author
   is the risk, not any one repo.

   **Then the outside view -- and read `references/community-sources.md` first, every time.** Search
   issues/discussions and forums (reddit, lemmy, HN, the project's chat) for what real users report --
   "the config page does nothing", silent data loss, abandonment, security threads. Others have often
   already hit the footgun you're about to. But several of these sources block outright, and one
   returns confident, well-formed garbage; the reference records what actually works and what only
   looks like it does. Skipping it is why vets report "Reddit unreachable" as their largest gap when
   the content was one flag away -- and a null from a blocked fetch is a fabricated negative, not a
   finding.

   **Measure health, don't eyeball it** -- contributor count, stars, `pushed_at` and "0 open issues"
   each mislead in a specific, checkable way; `references/health-signals.md` says how. Read it before
   writing the health read.
3. **Claims-vs-reality (the core check)** -- verify features against the code **both directions**.
   *Top-down:* take each README headline feature/config claim and trace it to a handler -- does the
   advertised setting/flag/button actually reach code, or is it decorative? *Bottom-up:* enumerate
   the actual surfaces (routes, buttons, config keys, env vars) and check each reaches something --
   the deadest buttons are often ones the README never bragged about. **Wired + unit-tested is NOT
   "works well."** A handler that exists can 404 or throw at runtime -- but worse, it can *run* and
   still be half-baked: a feature bolted on without integration, janky UX, a flow that technically
   completes but is broken in practice. Green unit tests don't catch this; only driving the real
   flow does. So don't stop at "it traces to a handler and has a test." **Stand it up and drive it**
   -- load the UI, click the surfaces, render the frontend headless (a browser in a distrobox /
   flatpak / throwaway container is cheap and almost always available; "I couldn't render it" is
   rarely a real excuse when there's a UI), walk the actual user journey end-to-end, hit the
   endpoints. This is the step you must NOT sample: cite `file:line`, and list what doesn't hold.
4. **Footguns and red flags** -- secrets committed, eval/exec of untrusted input, **auth omitted on
   specific sensitive endpoints** (setup/admin/2FA routes reachable unauthenticated -- a per-route
   omission, not just a missing login page -- and config/settings endpoints that *echo secrets back*
   in the response: the canonical vibe-code CVE class), data-loss paths, telemetry, license
   problems, heavy or unpinned dependencies. Vet
   the dependency list specifically for **hallucinated or slopsquatted packages** -- imports of
   names that don't resolve, or newly-registered lookalikes of a real package (a supply-chain tell
   unique to AI-written code); a single planted dep is worse than any dead button.
5. **AI-slop / bloat signal** -- is this learning-in-public with no editor? Flag it as a
   maintenance-risk signal, but don't discount the project wholesale -- the substance can be real
   even when the surface is bloated. Say which it is. Watch specifically for **process residue**:
   stray debug/`console.log` lines that only make sense mid-session, hardcoded author-machine paths,
   leftover TODO/placeholder text or conversation artifacts, and large commented-out dead blocks --
   cheap high-signal tells that code was generated and shipped without a verifying pass. **Green
   tests prove nothing until you read them:** AI slop ships suites that pass because they assert
   almost nothing (mocked-to-tautology, no real edge cases) -- a passing CI badge over hollow tests
   is false confidence, not verification. The sharpest mechanical check is **whether a test file
   imports the source it claims to cover** -- a suite that mocks the module, calls the mock, and
   asserts the mock was called is testing the test framework, and deleting the real implementation
   would leave it green. Check where those cluster: hollow tests concentrated in auth and
   permissions are a different finding than one vestigial file. Verify before you condemn, though --
   testing through a barrel, a registry, or an injected app factory looks identical to this grep and
   is perfectly legitimate, so confirm the module really is untouched. And **run the suite** rather
   than trusting the badge: it may be a build, the failures may be environmental (a missing runtime
   on your box, not their bug), and coverage on the paths that matter -- the write paths into
   *your* data -- is worth measuring separately from the repo-wide number. **Scope creep is its own red flag:** a tool that explodes
   past its original job -- a focused fetcher that becomes a kitchen-sink "platform" in weeks,
   shipping features on-by-default you have to keep *disabling* -- is both a slop tell and a security
   one. Every bolted-on default-on feature is attack surface the solo author isn't auditing; runaway
   scope with no editor is the exact profile that ends in an abandoned repo and a CVE.
6. **Redundant systems -- one fact with two homes.** A dead button has NO wiring; this has TWO, both working, and nothing notices divergence. Shapes: the **write-only mirror** (grep the READ side for a `select`, not the table name), a **constant dressed as a variable** (compare a field's DOMAIN to its actual DISTRIBUTION; tests cannot catch it), **built and never exercised** (ask the owner, not the code, and record the answer), and:
   - **Superseded, not abandoned: the fossil left by its own replacement.** Code that was live; a second mechanism was added because the first fell short, and the first was never removed. The comment justifying the addition is the camouflage ("the old check cannot see X, the new one can" reads as considered design and is proof one is strictly weaker). Ask of any two checks answering one question: does the newer SUBSUME the older, or merely extend it? Two corrections, both asserted wrongly at first: a fossil is usually *reachable* (trace the fall-through, not the condition; "dead code" is the more satisfying finding, which is why you reach for it); and do not retire the old mechanism on "strictly stronger" alone, check whether the new one fails OPEN anywhere, where the old guard is the only cover. Worked case: `references/superseded-worked-case.md`. Detail on the other shapes: `references/redundant-systems.md`.

## Coverage is the point (non-negotiable)

A vet you can trust cannot come from the README and a handful of files -- the dead feature and the
committed secret are precisely in the files you didn't open. So coverage is deterministic, not a
lucky sample -- but *tiered*, so it scales to a big repo instead of drowning in it:

- Enumerate the whole tree first (`git ls-files`); don't eyeball a subset.
- **Cheap pass over every file:** a fast signal scan (grep for secret / `eval` / `exec` / auth
  patterns; lean on the repo's own linters and secret-scanners) so no file goes wholly unlooked-at.
  Fan out parallel readers by area on a large repo.
- **Deep-read only what earns it:** every headline claim traced to its handler, plus every file the
  cheap pass flagged. "Most seem wired" is not a verdict.
- **Never fake coverage.** If the repo is too big to cover even cheaply, say so and bound the
  verdict ("swept X, deep-read Y, did NOT reach Z") -- that beats a confident verdict over a blind spot.

## How to run it

Non-destructive. Find the real entry points (build/run files, the main module); for each advertised
feature, trace it to the code (grep the handler, confirm the callback exists, run a
`--help`/`--dry-run` where safe). Static tracing first to map it, then *drive* it: for anything with
a UI, standing it up headless (distrobox / flatpak / a throwaway podman container, no real
credentials or data) is the default, not a luxury -- runtime is where the 404, the broken render,
and the bolted-on-but-janky feature show up, and none of them survive contact with the actual flow.

**Stand up what it talks to, as well.** "I can't test this, it needs $OTHER_SERVICE" is where a vet
quietly loses its entire runtime layer. Reach for the container first: run the real dependency in a
throwaway (most of these tools integrate with things that ship an image), or stand up a mock matching
the API's actual schema where you can't. Either beats not driving the integration, which is usually
the whole point of the tool and the likeliest place for a dead button.

Say which one you used -- a schema-matching mock proves the request is well-formed, only the real
service proves the other end accepts it, and that gap deserves a sentence rather than a silent
equivalence. And if you genuinely can't test it, **saying so is the right answer** -- an honest
"did not reach X" beats both a fabricated pass and a verdict quietly resting on an untested
assumption. Just make it the conclusion you arrive at after trying, not the one you open with.

### Fanning out

On anything sizeable, fan out with **disjoint slices**, one shared clone, findings written to
`findings/<slice>.jsonl` as they go, evidence shared but never conclusions, and one shared instance for
read-only probes with a throwaway for anything that writes. The reasons and the incidents are in
`references/fanning-out.md`; read it before spawning, and `fanout-craft` for briefs and model choice. Name
`search-craft` in the brief of any agent that searches the web for the outside view.

**Host constraints** (container-only stand-up, how to record a blocked source, nothing sent to a
third-party analyser) belong in `~/.claude/local/repo-vet/instance.md`; record your own (none ships).

## Output

A verdict the user can act on: **what it is**, a **health read**, the **claims that DON'T hold
up** (with `file:line`), the **footguns**, and a **go / caution / no-go** recommendation. Lead with
the verdict.

**Scale the evidence you demand to the direction of the verdict.** A no-go resting on a code-verified
structural defect -- there is no scheduler, the automation path never reaches the write call, the
stable release carries an unpatched pre-auth hole -- is already over-determined; more corroboration
can't make the missing scheduler appear, so gaps in the outside view barely matter. A **go** is the
one the user acts on, so it earns the extra pass: that's where a thin community footprint, an
unexercised integration, or an untested upgrade path should send you back for more before you sign
off. Verifying hardest where you're about to recommend action is the opposite of the natural pull,
which is to keep digging on the thing you already dislike. Cite the evidence next to each claim so the user can verify it -- never assert
"looks maintained / works" from the README or a handful of files. Bound every claim to what you
actually checked ("of the 6 headline features, 4 are wired, 2 are dead: ...").

## Run this skill from a COLD agent, not the context that raised the question

Delegate the whole vet to a fresh subagent rather than doing it inline. Two reasons, and the second
is the one that surprises people: a context that has already been arguing for or against the repo
carries that bias into the evidence-gathering — and, empirically, the cold agent also **covers more
ground**, because it isn't economising on reads it thinks it already did. Inline vetting returns a
thinner answer that still reads as complete.
