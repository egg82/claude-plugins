# Probe rules: the general shapes behind Part 1

Part 1 of the [instrument-failure case files](../instrument-failures.md) (from `verify-dont-anchor`):
the rules stated across many incidents rather than one, each with its short worked example. Load it
when a probe's result is about to become a finding and you want the whole family of ways it can lie;
the per-kind case files beside this one carry the long single incidents.

**A null result is not a negative finding.** Empty output proves absence only if the probe *could*
have shown the thing. A job that hasn't fired has no history; a file added yesterday has no git log.
The ways a zero lies: probing for **side-effects** instead of the **definition** (an empty log
directory read as "the job doesn't exist"); reading meaning into a command that **errored** (a wrong
path returns empty for reasons unrelated to the question); and — easiest to miss — **your probe is
broken, so the zero describes your regex rather than the world** (`grep -E "a\|b"` matches a literal
pipe and returns 0 for everything; a search for a *phrase* misses the same fact worded differently; a
write-detector matching `>` also matches `2>/dev/null`; a `count()` helper missing `re.M` made every
`^`-anchored check return zero, which read as a clean result; and **a defensive default in the probe
itself** — `getattr(res, "items", None) or []` against an object whose attribute was spelled
differently, so every result read as "matched nothing", which is a *plausible finding* rather than an
obvious bug. On your own codebase's object a `getattr` default has nothing to defend against: direct
access would have raised on the first call. **Reach for the attribute, not a fallback, when a miss
means your probe is wrong rather than the data being sparse.**); and — the one that looks least like
a bug at all — **your probe works fine but is the narrow instrument, and you report its ceiling as
the world's**. Before believing a zero, make the probe prove it can return non-zero — and make the
control **the bug you are hunting**, not a generic broken input, because a probe that can fail *some*
way is not thereby proven to fail *this* way. A markup checker written to hunt an unclosed `<details>`
detected stray end tags fine and reported every page "balanced"; its control —
`<div><details><summary>x</summary></div>` — came back clean, because the checker popped its stack on
any matching outer close, which is exactly how that bug hides. A looser control would have passed and
the green result would have shipped.

The same rule in its other costume, which is easier to fall for: **a control whose expected value
coincides with what the bug produces certifies the bug.** Counting rendered documents, I ran
`find /site/current -name "*.html"` and got **0** — `find` does not traverse a symlink and
`/site/current` is one. My control was "a pattern that must return 0", and it duly returned 0, so a
completely broken probe came back with a clean bill. The discriminating control was `find` against
`find -L` **on the same path**: zero versus the real count, because only one of those can be wrong
for that reason. So the test for a control is not "is it rigorous" but **"does it return a different
value under the bug than under success"** — the must-differ companion to making a term that must
match prove the probe is alive.

**And that test is not only for controls. Apply it to any number you are about to report.** Written
as a rule about controls, it did not fire twelve hours later when the same author quoted a count of
rows "at the newest version" as evidence a re-processing pass was progressing. The rows already
existed and the job UPDATEs them in place, so that figure is the same before the pass, during it, and
after — identical under every state it was offered as evidence for. The discriminating figure was a
comparison of each row's updated-at timestamp against the pass's own start time, which moved while
the reported number sat still. **Before quoting a figure as evidence, ask what it would read if the
claim were false**; if the answer is "the same", it is describing something else.

The mirror of that also bites: a probe returning plenty of hits, none of them the thing — searching
every rendered page for a feature that renders on a handful buried it under matching *titles*, and
only reading the real ids out of the source of truth first made the check discriminate. **Prove the
probe can return non-zero, and prove you are looking where the signal is; a wrong scope answers as
confidently as a wrong regex.** And note the asymmetry in how the two failures are received: **a zero
prompts suspicion, a healthy count reads as a finding.** Grepping rendered pages for a handful of
record ids put one of them on *nine* category pages where the database said one — the probe could not
tell "classified into this category" from "listed as its example" from "merely linked here" — and
nine was interesting enough that the instinct was to explain it rather than to distrust it. The
number that needs the second look is the plausible one.

**And several checks agreeing is not corroboration unless they could have failed differently.** I
concluded a shipped feature was missing on the strength of three zeros — and they were one wrong
page, one wrong artefact (checking for a directory when the thing was a section), and one broken
shell quoting that grepped a literal `"$i"`. Same target class, same shell, same guessed strings, so
they shared their failure mode and each felt like independent confirmation of the last. What broke it
was a **control in the same command** — a term that had to match, returning a healthy count when
three zeros said it could not. **When checks agree, ask what they share before believing them; when
you want independence, change the instrument, not the wording.** And the exact mirror, because both
halves get broken the same evening: **when you want a COMPARISON, hold the instrument fixed.** A peer
compared a manifest digest against an image ID — `podman image inspect` for one side, a `podman pull`
fallback for the other, each the cheapest thing available at that point — and got a mismatch that was
two rulers, not two values. Independence needs different instruments; comparison needs one.

**The root of both, and of most instrument failures: the cheapest available check is almost the right
check, and a proxy you have ALREADY computed costs nothing, so nothing in the moment argues against
using it.** Asked whether a branch was safe to pin, I offered a file list — because I had already
computed it for another purpose. It correctly proved my changes did not touch the classifier prompt
and was silent on the branch being based on a pre-version-bump `main`, which was the actual risk. Six
instrument failures across three sessions in one night and not one was a lapse in rigour; every one
was something cheap and adjacent standing in for the thing asked. So when a check is free because you
ran it already, that is the moment to re-read the question — **cheap and adjacent is what a wrong
proxy feels like from the inside.** **Two agents agreeing is this trap in a second costume:** a peer
session told me a crash "reproduced on X11", I repeated it back as the justification for my own
recommendation, and we each then read the other's restatement as support. Neither had checked. **A
restatement is not a second source** — when a plan rests on a fact you were handed, ask who measured
it, not who else repeats it. And the constructive form, for two derivations that *should* agree:
**test the condition under which they could differ, not their outputs.** Two counts matching is weak
— they can match for the wrong reason; zero rows in the divergence case is proof. Asked whether a
caption's count and the number of rendered pages described the same set, the answer was not comparing
the numbers but querying the one combination that could appear in one and not the other, and getting
zero. When a probe contradicts something you read with your own eyes, trust the reading and fix the
probe. The asymmetry repeats elsewhere: reproducing proves a problem is general, but *failing* to
reproduce proves nothing unless you matched the setup — and "latest" or "still happening" need the
wall clock, not an assumption.

**A substring probe cannot tell a violation from an explanation of the violation, and the better the
code is commented the more this bites.** Four times in one day, all mine: a test for "no assignee
filter" failed on the comment forbidding one; a test for "the theme preference never reaches the URL"
matched `data-theme-id`; a contract test for a required attribute PASSED with the attribute deleted,
because the comment above it named the attribute; and a test for "no interpretive label on this rate"
failed on the comment explaining why a label would be wrong. **The mechanism is not carelessness: a
rule worth enforcing is worth a comment, and the comment quotes the rule.** So the ban and the reason
for the ban are the same string. Strip comments before asserting, scope the match to a tag or an
identifier rather than the bare word, and prefer asserting on rendered output over source. Then
mutate: remove the thing and watch it fail, because three of those four looked green.

**And a match proves a REFERENCE, not a BEHAVIOUR.** `strings <lib>.so | grep <ENV_VAR>` returned a
hit, and I published "the library checks that variable, so no crash handler is installed" — a claim
about which branch runs, drawn from evidence that only showed the name exists. The neighbouring
symbols said the variable gated *whether a reporter launches*, not *whether a handler installs*, and
a journal line reading `code=exited, status=1` — a process that plainly caught the signal — had been
sitting in a peer's output disproving me for hours. Note the shape: the false-zero family (`false-zeros.md`) is a
probe that under-reports, this is a probe that answers correctly and gets over-read. **A symbol table
is not a control-flow graph: to claim behaviour, find the call site or observe the running thing.**

**Verifying that a component WORKS is not evidence it is the component being USED.** Told a job's
re-run guard was inert, I read the SQL out of the image, found `IS DISTINCT FROM`, ran it against the
live table, watched it match every row — correct, and irrelevant. The gate was a Python check
elsewhere against a row that did not exist. I had verified a real thing and then let its correctness
stand in for a claim about a different thing, which cost two more pinned images before I read the
call site. The same shape without any code: a CronJob's `lastSuccessfulTime` was populated while
`lastScheduleTime` was empty — the field that reads as "the nightly worked" set entirely by manual
runs. The same failure by *position* rather than component: I tested whether a debug server was
exposed by fetching its routable IP instead of `127.0.0.1` — from the host itself, where traffic to
its own address bypasses the firewall. It answered 200; from another machine, with `ssh` as a control
proving the route, it was closed. **Using the right address does not make the test external; leaving
the host does** — same rule as querying a database through the service name the application uses.
**Before trusting a green check, confirm the path under test is the path in use: find the caller, not
just the callee** — and read the source out of the artifact actually deployed, not the repo you think
it was built from. **A real check on the wrong code path is more convincing than a guess, and just as
wrong.** Its sibling is the value that is right about what it measured and wrong about what it is
presented as meaning ([[no-fabricated-certainty]]).

**And the reason "find the caller" so often does not fire: you believe you ARE testing the caller,
because you retyped it — and the idioms your fingers add are exactly where the bug is.** A background
worker failed on every file it processed. The cause was a `pathlib.Path` from the ORM handed to a
library that needs a `str`. Every diagnostic probe I wrote against the live pod reproduced the
caller's body by hand and wrote `str(path)` — because converting a path before a library call is
hygiene, not a decision. So each probe **repaired the defect in the act of observing it**: the
library processed the file fine under my probe, while the worker beside it failed on every file in
the same minute.

Note how it renders, because it is the opposite of a false zero: the probe returns a **true
positive** about a component that genuinely works, which reads as having exonerated the component
and localised the fault elsewhere. Four probes ran before one called the real function.

**So reproduce by CALLING, never by RETYPING.** Invoke the actual function with the actual value and
stub only at a boundary you name; where you must hand-roll, diff your probe against the source line
by line before believing it. The tell is a probe that succeeds where production fails **on the same
target in the same minute** — that is not evidence the target is fine, it is evidence your probe and
your code differ, and the difference is the bug. The corresponding test asserts the TYPE crossing
the stub seam, since a stub that accepts anything cannot catch this.

**"Shipped" is a claim about the artifact people touch, and the branch is not it.** I reported a page
had gone from 1.4 MB to 219 KB. True of `main`, true of the served page too — but only because
someone else had moved the deployment pin, which I did not know had happened, so the sentence was
right by luck and would have read as a fix arriving with the tag I was handing over. **I described
the state of my own work and let it stand for the state of the deployment.** The chain is merge →
build → pin → run → publish, every link has been the broken one at least once, and a moved pin still
ships nothing until a run renders with it. So before saying a fix is live: name which link you
checked, or say "merged" and let whoever owns the pin say "shipped".

**And one link earlier: a green pipeline says the branch is internally consistent, not that it is
current.** "Safe to deploy" is a claim about the branch's *base*, and nothing in CI checks it. I
offered a branch for a deadline-critical image having verified that my own changes could not affect
the classifier's prompt — true, and the wrong question. The branch was based on `main` from before a
config version bump, so its config named one version while the database was on the next; pinning it
would have rendered an artifact with zero members in every category, exit 0, no warning. **A diff
shows what you added and is silent about what you are behind on.** So before handing over a sha:
`git log <branch>..origin/main`, and check the version of whatever config the artifact carries. The
catch also argues for hashing the *rendered* artifact over comparing file lists — the prompt digest
would have caught the stale base on its own, because a different number of definitions renders a
different prompt, while the file list could not have.

**"Verified" without a commit reference becomes a false assurance the moment the code moves.** I
closed a client-side filter check — "10 of 10 assertions pass, verified" — and the *next* commit
broke the page: a block reading `activeFacets.length` above its own declaration, so every keystroke
threw and the reader was shown "could not load index.json". A page-breaking defect presented as a
network problem, sitting under a note saying the thing was verified. **The test was not wrong; it
passed against the commit it ran on.** What was wrong was a claim with no validity bound. So: pin a
verification to a sha, or re-run it as a test rather than recording it as a conclusion — a one-off
check that passes becomes a lie on someone else's schedule, and the stale note is worse than no note,
because it stops the next person looking.

**And a check's sufficiency is relative to the KIND of change, so re-running last time's check is not
the same as verifying.** Two image swaps, same question — will this trigger an expensive re-run? For
the first, hashing the config file settled it. For the second the change made a previously-ignored
key *read*, which alters the rendered prompt while barely touching the file — so the file hash proved
much less, and the decisive comparison was hashing the **rendered** block, the thing actually
consumed. **Hash what is consumed, not what is stored** — and do not decide case-by-case whether the
check is needed, because the answer you EXPECT keeps changing. Three deployments in a row, the same
one-command comparison, and the expected verdict went must-match, must-differ, must-match: identical
config, then a deliberate bump, then identical again. Any run where you predict the answer instead of
computing it is one wrong prediction away from shipping a no-op as an upgrade — which had already
happened once. **When a check is cheap enough that you could argue about whether to run it, the
argument costs more than the check.**

**A transient failure and a permanent one look identical, so retry before diagnosing.** A CI job
failed against a container registry with `invalid username/password`; I established that the branch
was protected, that the secret was therefore injected, and was one command from writing up the
credential as expired. A retry pushed fine — and a pipeline eleven minutes earlier had also pushed
fine, which I had already seen. **Cheapest discriminator first: re-run it once.** The corollary for
reporting, since a red build invites a story: check whether the *same* job failed the *same* way
twice before attributing it to anything.

**A probe you launched and never collected is worse than one you never ran** — it buys the feeling of
having checked without the information, and nothing marks the gap. A `jcmd GC.run` + heap read on a
live pod timed out into the background; I moved on and later published "the collector never returns
committed heap." That exact command had already disproved it — 706 MB returned and sustained — and
the result sat unread in a task file for hours. **Anything that times out into the background is an
open question, not a closed one: list what you have outstanding before you assert anything it bears
on, and never let a claim rest on a check whose output you did not read.**

**Whatever tool you settled into early becomes the only one you reach for, and its refusals start
reading as facts.** The fast path wins on the first ten questions and then silently answers the
eleventh, which it cannot. An API said an item was unmovable and that became "it cannot be moved" —
while the logged-in UI, open the whole time, had a button for it. **So before writing "cannot",
"unavailable", or "cannot explain", name the wider instrument you still have and go use it**: the web
UI behind an MCP server, the admin panel behind the API, SSH behind a remote-management agent, a
rendered page behind a headless container. A capability you stopped using is invisible from the
inside — nothing errors, the narrow answer just looks final.

### Rules from `verify-dont-anchor` kept here rather than resident

- **A mechanism is not evidence, and it is what stops you asking for any.** Claims that arrive with
  an explanation attached (yours or a peer's) read as already-checked; across one day of sessions
  checking each other, those were reliably the ones that failed. Ask what result would look
  different if the story were wrong, and go get that result.
- **Measuring repeatedly destroys the state you were asked about.** The second iteration is warm
  because the first ran (7-17 ms looped against 854 ms - 7.1 s spaced like a person). Space samples
  like the real caller and report cold and warm as two facts. And ask what you just started: a
  deploy, restart, migration or fan-out is load, and one `pg_stat_activity` or `top` names it.
- **Some checks expire.** Before a long-running job, answer first the questions only answerable
  mid-flight (does it log at start or at completion?). A discriminator can be sound except in the
  circumstance it is read, when the fault flattens its input: prefer evidence written before the
  fault (case in [controls-and-inference.md](controls-and-inference.md), "The fault being diagnosed
  had flattened the evidence").
- **A new CAPABILITY strands every sentence saying it is impossible.** Grep the repo for the claim
  when you add one; it is the fourth blast-radius shape beside a fix's siblings (the SHAPE grep), an
  addition's untouched readers (widening a value set) and a move's two ends — all three in
  [blast-radius.md](blast-radius.md).
- **A comparison that errors on both sides "matches."** Report "could not compute", never equal.
- **A zero from a guessed filename, key or format tests your guess**, which is the ruled-out case
  in [false-zeros.md](false-zeros.md) seen from the sender's side.
