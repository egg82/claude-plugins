---
name: bug-hunt
description: "Hunt real defects in a repo and root-cause them — correctness, performance and cost, security, resilience under faults, state that breaks over months, UI and accessibility, LLM features deciding behaviour in prose — proving each by execution, with file:line pointers. Use when the user wants bugs found, asks what's broken, slow or insecure here, wants a perf/security/accessibility hunt, or wants an issue reproduced, root-caused, confirmed or filed. NOT a diff (/code-review) or trust verdict (repo-vet); the standing multi-lane sweep is hunt-sweep."
---

# Hunt bugs in a repo at rest

You are after **defects that are real, whose cause you've located, and that you can prove.** Noticing something
suspicious is the easy part and not the job -- a suspicion you can't reproduce and haven't deduped is noise you're
about to publish under someone's name. Every finding clears four gates: **cause located, status honest (executed, or
labelled code-reading only), real-world impact assessed, not already reported.** There is no verdict to reach, unlike
`repo-vet`, so you run until the well is dry.

The work is one pipeline -- **lead → reproduce → root cause → kill → compose → impact → dedup → report** -- and it is
the same for a flipped condition, an N+1 query and an IDOR. What changes by domain is where leads come from and what
counts as proof; those live in `references/oracles/`. Two stages are adversarial passes you run *fresh*, and they fail
differently, so keep them apart: the **kill** is repo-bound ("is it true?"), the **impact** is world-bound ("does it
matter?").

## Decide these before you read any code

**0. Scale the machinery to the job -- most hunts are small.** The common case is a modest repo and a mundane bug, and
it collapses to a mostly-inline pass: read the suspect code, reproduce, a quick impact call, done. The large fan-out, a
dedicated impact interrogation, exploit-history research and the composition pass earn their cost only as the repo,
the bar or the blast radius grows. Reach for a subagent to force coverage you can't hold in one context, or for a
genuinely fresh adversarial pass -- not by reflex. The stages are the same at every scale; only the spend changes.

**1. Where is this going?**

- **A repo you maintain.** The deliverable is the diagnosis. Run the pipeline, write it up per *What goes in a
  finding*, and stop -- skip the contribution-policy check, the pre-draft cold read, disclosure and corrections, which
  protect a relationship with a maintainer who isn't you. Dedup still applies. If fixes follow, land them
  findings-first: a strict xfail asserting the wanted behaviour, then the fix that flips it (`agentic-engineering` §5).
- **Upstream, to someone else's project.** Everything applies, and the filing apparatus is the point.
- **A verify-then-file intermediary** -- a trusted human who confirms each finding and files it in their own words.
  Two artifacts (see *What goes in a finding*), and you still owe them a repro they can run.

**2. What's in scope?** For a **fork** whose value is patching upstream, a bug identical to upstream is **still in
scope** -- fixing inherited bugs is the fork's job. The `base`→`HEAD` differential *labels* origin
("fork-introduced" vs "inherited"); it doesn't gate scope. When vetting a repo to *adopt*, upstream bugs may genuinely
be out of scope. Decide per target, up front.

**3. Will this project accept what you're about to write?** *(Upstream only.)* Read `references/filing.md` now: it
fetches the repo's `CONTRIBUTING.md` **and the org-level `.github` repo's** (a 404 on the first is normal for an
inherited policy). Some projects ban AI-assisted contributions outright; then the deliverable is a repro and diagnosis
the user rewrites in their own words.

**4. Which domains are live?** Each domain is a stance the hunter holds -- "does this match its contract?", "what does
this cost?", "what do I control?" -- and a hunter holding all of them drops whichever it isn't already in. Pick from the
table in *Oracles* by what the target *has*, say which you skipped and why, and on a big target run each as its own
pass or lane (`hunt-sweep`). Correctness is always live; a domain whose surface is absent stays closed -- SSRF in a
pure-function library is how a hunt spends its budget and never runs the test suite.

## Oracles: how a defect proves itself

An **oracle** is a cheap, mechanical signal that something is wrong without needing a spec or an argument about
taste. You aren't saying a line looks bad; you're showing the system is inconsistent with itself, over a budget, across
a boundary, or broken by a fault it should survive. The shapes recur in every domain, roughly in order of yield --
start at the top:

- **The machinery the project and its ecosystem ship** -- test suite, type checker, linters, sanitizers, dependency and
  secret scanners, `EXPLAIN`, accessibility audits. Cheapest per minute and most often skipped. Prove the probe can
  fail before trusting its zero.
- **Self-consistency** -- N siblings that should agree and don't (the differential, highest yield of all), a rule the
  code follows everywhere but once, a doc sentence the code contradicts, a log line that disagrees with its condition.
- **Contract** -- tests written blind from the interface, properties, round trips, documented errors on hostile input.
- **Budget** -- a measured cost against the work needed: queries per row shown, bytes sent per byte used, CI minutes
  against the critical path. The tell is a cost that grows while the result does not.
- **Boundary** -- something an untrusted party controls reaches what it shouldn't.
- **Injected fault** -- drop, kill, restart, fill the disk, move the clock; check the system recovers and says so.
- **Simulated time** -- run months or years through the real code with a moving clock.
- **Rendered output** -- look at what the user actually gets, at the sizes, states and inputs nobody opened.

**Which oracle file:**

| The target has... | Load |
|---|---|
| Any code (always) -- siblings, docs, stated contracts, error paths, concurrency, config | `references/oracles/correctness.md` |
| Anything a person waits on or pays for: queries, an API, caches, page load, frame rate, paid APIs and LLM spend, bandwidth, CI time, image size | `references/oracles/performance.md` |
| A network boundary, untrusted input, tenants, plugins, stored credentials, rendered user content, CI that runs others' code | `references/oracles/security.md` |
| A network, unattended jobs, restarts, persisted state, deploy manifests, backups | `references/oracles/resilience.md` |
| State that accrues -- progress, ledgers, schedules, years of rows, unpruned logs, migrations | `references/oracles/state-over-time.md` |
| A front end a person uses | `references/oracles/ui-and-accessibility.md` |
| Runtime calls to a language model | `references/oracles/llm-features.md` |

In the oracle files, *(incident)* marks a rule that came from a real hunt or failure here, and the calibration cases
are incidents too; other unmarked tells are standard practice not yet tried in a hunt here -- leads, with unmeasured
yield.

**Lenses are where speculation lives.** Most oracle files list lenses or tells beyond the mechanical oracles; hold them to the
higher bar: if you can't write the concrete input that produces the wrong output, it isn't ready.

**Carry the history; don't rely on recall.** Read the target's closed bugs -- security, crash, perf and mundane alike --
before choosing lenses; the module that produced four timezone bugs will produce a fifth. Select lenses iteratively:
each finding asks "what class is this, and what else of this class exists?"

**The tracker is a lead source too.** Open issues are defects someone already confirmed, most never root-caused --
"here's the root cause of #27" closes something, where a twelfth new item adds to the pile. Read it early as a map,
not only at dedup. Recently merged PRs are fresh regressions; stale threads are bugs felt but never diagnosed.

## Cover everything: dealing out the read

A bug can be anywhere, and the ones left at the end are in the files nobody found interesting. A hunt can't prioritize
the way a vet or review does: attention drifts to the clever module, the dull adapter gets skimmed, and the hunt ends
having read a tenth of the tree while feeling done.

**Fan out to force the read, not just to go faster.** An agent handed twelve files reads twelve; handed the repo, it
reads the exciting tenth. Fan-out buys coverage, token economy (a context-free reader costs far less than your
accumulated context) and grounding (an agent with no stake tests what the finder rationalizes). So orchestrate --
build harnesses, delegate, keep your context lean.

**Tell the finder to execute, and don't assume the expensive model finds more.** Measured: every distinct real defect
was found by at least one cheap run, and one sentence in the brief took runs from **0 / 3** to **3 / 3** executing.
Scope the manifest tightly -- expensive models wander outside it. **Dedup by the claim, never by `file:line`** --
counting citations measures formatting. Evidence and cost anchors: `references/fanout-evidence.md`.

- **Partition, don't sample.** Fix the in-scope set first -- `git ls-files` minus vendored, generated, lockfiles and
  fixtures, named so the exclusion is a decision -- and put every file in exactly one slice.
- **Hand each agent a manifest file, not a directory.** A directory lets it quietly read the interesting half.
- **Partition by directory or subsystem, never by theme or domain.** Thematic slices let files fall through while
  sounding thorough. Domains and themes are cross-cutting passes *over* the partition -- among the highest-yield passes
  there are (every bare `except` read as one sweep surfaces what a file-by-file read normalizes) -- but each still
  deals its files out by directory, or by layer for performance, so the union closes.
- **Clone once** into a shared workspace; **write findings to `findings/<slice>.jsonl` incrementally**, one record per
  finding, so an interrupted fan-out leaves resumable state (not `.md`: the Write tool refuses report-shaped `.md`
  files from subagents -- `fanout-craft`).
- **Budget the fan-out to the quota**; serialize execution-heavy phases, and set up a resume where a long run can be
  interrupted.
- **Check the union closes.** Each agent reports what it covered; a remainder you didn't notice is a shipped blind spot.
- **Many independent targets** (a fleet, loose packages, third-party deps): order effort by prior probability of an
  undiscovered bug -- obscure, young, single-maintainer, forked, already-yielded first; widely audited last. This orders
  effort; it doesn't skip coverage.

Within a slice, tiering is fine -- a cheap pass over every file, then deep-read what earns it. Skipping is not tiering.
Track **sweep depth vs differential depth** separately: a file can be swept yet never read against its siblings. After
the first pass, *measure* the gap (`comm` against the manifests); a second fan-out targets the gap plus boring-value
density (numeric and boundary math, lifecycle and teardown, serialization), never a blanket re-read: re-reading covered
files is the token sink, and sweeping the skipped interface, enum and codegen files is nearly free coverage.

## Reproduce before you believe it

A finding you've only read is a hypothesis -- **gate 1**. **Gate 2 is execution**: the real code made to misbehave.
Most plausible findings die here, and you want them dying in your workspace, not on the tracker. One that survives the
reading kill but fails gate 2 is downgraded, not shipped: a "resource leak" a hunter and a bytecode-reading verifier
both believed showed zero leaks over ~1,550 triggers with forced GC. Ship the proof with every finding.

What counts as proof depends on the domain:

| Domain | Proof | The test that lands the fix asserts |
|---|---|---|
| Correctness | a failing test or repro script with the wrong value captured | the wanted behaviour |
| Performance | a count or plan the fix would change, or cost at two sizes | the count (queries, calls, bytes), never wall-clock |
| Security | the exploit run against your own instance | the attempt is refused |
| Resilience | the injected fault, scripted, and the wrong state after it | recovery from that fault |
| State over time | the simulation and the simulated day the wrong state appears | the state at that day |
| UI / accessibility | a screenshot, accessibility-tree dump or audit result from the real build | the element, name or state |
| LLM features | a rate over a fixed input set, from recorded or seeded calls | the structured field or the code-decided rate |

Reach for the smallest thing that executes the path. **The project's own test suite first**: a new case asserting the
correct behaviour, watched to fail, *is* the PoC in the form a maintainer wants. Check this before costing any
scaffolding -- "reproduction is expensive" assumes there's nothing to run, and on a repo with a working `pytest` or
`go test` that is simply false. Then a scratch harness calling the function directly. **Template the harness once** --
a dependency or classpath recipe, a standalone bootstrap, a booted instance for state PoCs, a raw socket for protocol
PoCs -- and cost it against the batch, not the first bug. Interactions through a real user surface (a UI gesture, an
interactive session) are the known hard case: they need a driving client or an in-process equivalent. **A property or
fuzz pass over public entrypoints** pays for itself where the contract is "hostile input produces a documented
error": mutate a valid input (flip a byte, truncate, extend, oversize a length field) and assert only documented
failures escape. An hour of scaffolding to upgrade *one* honestly-labelled code-reading finding is a bad trade; build it when a
subsystem's worth of findings waits on it. Anything needing a real service gets a throwaway with no real credentials
or data.

Capture the actual output -- the log line, the wrong value, the trace; a maintainer who sees their own program arguing
against them stops arguing. Keep the repro minimal. When you genuinely can't execute something,
report it as code-reading and **say so**; never let an unexecuted finding wear the language of a reproduced one.

Traps that make a reproduction lie, in `references/repro-traps.md`: several PoC agents against shared state (classify
by blast radius); a null result that couldn't have been anything else (a `.gitignore`-honouring grep, an SPA's
catch-all `200`, a fact from a sibling container); a live system cited for design intent; evidence crossed between
isolated environments. Measuring against production has its own traps, in `oracles/performance.md`.

## From symptom to root cause

A symptom names where the program *noticed* the damage, almost never where it was caused: "it crashes at
`parse.go:88`" when a field was left unset three layers up leads to a null check at line 88 that buries the bug. Keep
asking "and what made *that* true?" until the answer is a decision someone made. You've arrived when the next "why"
leaves the codebase and you can state the fix as a behaviour change, not a symptom suppression.

**Prove causality by intervention, not plausibility.** Codebases are full of second suspicious things that would also
explain the symptom. Change the suspected cause and watch the symptom follow -- flip the condition, force the value,
revert the commit. This also catches *a* real bug that isn't *the* bug reported, which deserves its own finding.

- **Bisect when there's history** -- a first-bad-commit names the change, the author and usually the intent.
- **Read the reporter's environment** -- version, config, platform. A bug under one config is a finding about it.
- **Not reproducing means "not present here", never "not real."** Match their version and config, and check whether
  it's fixed on `main` but unreleased.
- **Instrument rather than squint.** Logging at the suspected layers answers in one pass what reading argues for an
  hour.

## Kill your own findings

Run a pass whose job is to **destroy** each finding, in a context that didn't do the hunting. Spawn the verifier with
only the claim and file references, your reasoning withheld, so it re-derives rather than reviews. Output: CONFIRMED /
KILLED / DOWNGRADED.

- Does the cited code say what the finding claims? Re-read it; don't trust the excerpt.
- Is there a guard, caller or later branch that makes it harmless? Follow the call sites up.
- Is it intentional? Comments, tests, `git blame`, the tracker.
- Is the *severity, cause, contrast or scope* right? The usual outcome is a correction, not a kill -- a wrong blamed
  line, a fabricated "sibling does it right", "6 types" that was 5. One hunt called a plugin loader unsafe for writing
  bytes before checking their hash; it wrote to a `.tmp` and deleted it on mismatch -- a docs issue in a security
  issue's clothes. **Downgrade as readily as you drop.**

**Kills need evidence too.** A falsely killed finding is silently never reported. The trap is killing a *class* by
testing a *convenient instance*: one run killed a separator-validation lead by reasoning about `sep = b"a."` (harmless,
`.` never appears in base64) and never tried `b"__"`, every byte a base64 character, after which ~2% of tokens failed
to verify. Name the instance you tested and why it's the strongest; otherwise you tested an example, not the class.

## Compose the findings

The highest-value bugs in a mature codebase are often two minor ones that compose. Once everything is collected and
killed, read the **complete inventory, sub-bar and killed items included**, for chains: **A makes B reachable**, **A
amplifies B** (permanent, silent, larger), or **A + B jointly cross the bar**. A crossing pair re-enters verify and
impact, which is why the full inventory must stay navigable, not just archived. Chains cross domains: a retry that
swallows the terminal error plus a cache that stores the failure is permanent silent corruption; a sub-bar off-by-one
plus a sub-bar missing bound check is an out-of-range write; a missing timeout plus a worker pool is an outage. The sharper variant composes
*capabilities*, none of them a defect, across a trust boundary (`oracles/security.md`, capability composition).

## Impact: does the world get hurt? *(after the kill)*

KILL asks "is it TRUE?" from the repo; IMPACT asks "does the WORLD get hurt, and how do we say it?" -- so **impact is
the one stage licensed to leave the repo** (ecosystem and web search, deployment reality, precedent, field data), and
it runs *only on kill-survivors*, as a fresh pass. **When the target is deployed and reachable, a read-only query of
the live DB, config or logs usually resolves a "conditional" severity** instead of shipping it, in either direction.
Usually it demotes, occasionally it promotes; honest calibration, not reflexive skepticism. It's class-agnostic: a
corruption bug or a slow landing page needs it as much as an exploit.

Load `references/impact.md` for the pass: twelve questions (seven are the spine for every finding, five only for
security-shaped ones), the HIGH gate (exhibit a concrete scenario with real actors, or don't call it HIGH), named actors
as citations you must inspect, **realistic ≠ frequent**, and the supported-configuration gate. Upstream, the output per
finding is a severity plus **REPORT vs INVENTORY-only**, and few survive to REPORT: a stranger's tracker is a scarce
resource you're spending. On your own repo every real defect is recorded and the question
is priority.

## Dedup before you write

Read the tracker again before drafting, now as a filter -- by now you know the file names, functions and error strings
you didn't going in. A duplicate teaches a maintainer the reporter didn't look, and that judgment attaches to the whole
batch. Classify each survivor **NOVEL**, **REPORTED (#n)**, or **PARTIAL** -- felt in the wild but never diagnosed,
which *strengthens* the finding. Search **open and closed** issues, PRs, comment bodies and the web, by symptom *and*
identifier:

```bash
gh issue list -R <owner>/<repo> --state all --search "<symptom or identifier>" --limit 50
gh pr   list -R <owner>/<repo> --state all --search "<identifier>"
```

**Don't stop at the first hit**: a property closed three times over a decade is a settled position; one stale closure
may be an issue nobody got to. An open PR with your exact diagnosis makes the finding correct but not novel. `glab`
mirrors these commands for GitLab; elsewhere, search the web tracker by identifier. On a repo you can't file to, dedup
still decides whether a finding is worth the user's time. **Declining
to file usually means commenting** with what the thread lacks (`references/filing.md`).

## When to stop

**Stop when a round turns up nothing new** -- not at a target count. Bound the claim by the *measured* coverage gap:
**"swept X, deep-read Y, did not reach Z; domains run: …, skipped: … because …"**. "I found 5 bugs" and "I found the 5
bugs that exist" are different sentences, and only the first is ever true.

**A second hunt is a round, not a repeat.** Run it from fresh agents not shown the first one's findings (only its fixed
list), areas dealt differently, starting with what the first didn't reach. Measured on Bug Hunt Bench
(bughunt.productcompass.pm, `data/benchmark.json`): an IDENTICAL configuration re-run found a median 18% more planted
bugs over two runs than one, and 36% over three -- two runs overlap only about 60%. A hunt over code another agent is
still changing is wasted; run it after those merges land.

On the user's own repo, close with a **maintenance read**: does the shipped release predate the open bugs, and does
this batch change what should ship next?

## What goes in a finding

Rank by impact, not discovery order. Lead with what silently does the wrong thing to real data.

**For a verify-then-file intermediary, two artifacts:** a short **REPORT** of report-worthy findings ranked by severity,
each built for fast verification (`file:line`, what it should do, the offending line and the contrast, the one
realistic trigger, the small fix if any, a PoC pointer); and an exhaustive **INVENTORY** of every tier, which the
composition pass reads.

**Put the diagnosis in the title** -- the cause, not the symptom. "IV incorrectly decided from key in
crypto_utils.py", not "encryption produces wrong output". If the cause won't fit, you haven't finished
root-causing.

Then include **only what the maintainer can't derive themselves** -- a menu, not a checklist:

- **Evidence** -- `file:line` and the offending expression, pasted. Almost always.
- **The contrast** -- the sibling that does it right; turns "I think" into "these two disagree".
- **Repro** -- the failing invocation beside the working one, with real output; say whether you ran it. For
  performance, the count before and after.
- **The fix** -- when you can state it in a sentence ("add the missing `!`, matching `X:112`"). Larger, describe the
  shape and let them design it; a restructured function is unreviewable by inspection.
- **Root cause** -- when it's a distance from the symptom. If the title and line show it, don't restate it.
- **Impact** -- only when non-obvious or worse than it looks.

**Trust the maintainer to know their own code**; explaining it back to them is the commonest way a report reads as
machine-generated. **Length follows the bug, not your effort.** This is concretely what maintainers mean by AI slop: a
report that sprawls without landing on the defect, and a sweeping patch where a one-liner belongs -- both say the
reporter didn't finish the analysis. For every paragraph, would its absence leave them unable to act or likely to
misjudge? A title and two lines of evidence is a complete report when the defect is obvious at the line. Group findings
sharing a root cause (three inverted siblings of one feature are one fix); keep separate bugs separate.

### Never quote from memory

Every quotation -- README, doc, comment, error string -- is pasted from the file you just opened, with a line number.
Never reconstruct one from memory, and never tighten a paraphrase until it reads like a quote. A real run presented *"the file is not replaced when the hash matches"* as a README blockquote and built a verdict on
it; "hash" appeared nowhere in that README. A maintainer who catches one fabricated quote re-verifies every claim in
the batch. Likewise **mark what you observed and what you inferred**.

## Before it goes out *(upstream only)*

Read `references/filing.md` before sending anything: a blunt cold read by a fresh subagent playing the maintainer
(worth borrowing for any writeup someone else will read, own repo included), grepping out sentences true of every issue report, and how to correct after filing. **Confirm with the user before any
`gh`/`glab` write** -- issues are public, permanent and land under their name -- and raise AI disclosure in that same
decision.

## Voice for filed issues

**The per-person instance lives in `references/issue-voice.md` -- if one has been derived locally, load it before
drafting anything the user will file under their own name.** It is per-person and does not ship with the plugin; on a fresh install derive your own as below.

**To derive one for a new person:** collect their hand-written issues (not ones an LLM drafted for them -- that is
imitating an imitation), read for register, evidence conventions and structure, and write down the phrases to grep out
of a draft before filing. Evidence generous, scaffolding zero, register conversational; match the repo's template;
disclosure is per repo. Pairs with [[issue-writing-style]], and [[distill-dont-dump]].
