# Controls that could not discriminate, and conclusions the evidence did not license

Part 1 of the [instrument-failure case files](../instrument-failures.md) (from `verify-dont-anchor`).
Load it when you are choosing a control, when a discriminator "agreed" on the case you tried, or when
you are about to attribute an observed state to a cause, a history or a population. Every case here
had real evidence in hand; the control tested the wrong axis, the sample was thinned by the fault, or
the inference went further than the data.

### The control I added to remove a confound became the confound

Scoring twelve models on one task. Five returned JSON that stopped mid-object, so I added
`max_tokens: 16384` on the next pass — a *control*, to rule out a low default output cap as the
cause. A model that had swept every arm clean then scored 1 of 4, truncating at 10,066 and 10,437
completion tokens, and once at **639**.

639 is not a 16,384-token cap being reached. **The number could not be explained by the thing it was
blamed on**, and that is the whole tell. Removing the cap and changing nothing else: 4 of 4 clean,
12,661 to 13,100 tokens per call. Sending `max_tokens` on those routes makes them stop *below* the
figure given; omitting it lets the upstream use its own larger budget.

Had I not run that control-of-the-control, I would have reported a model as flaky on the strength of
a flaw I introduced — and reported it *more* confidently, because I had "controlled for" the obvious
confound.

The same session produced the same shape from the other direction. A scorer asserted
`expect_merges: 8` on an arm containing eight byte-identical duplicates. Correct behaviour reports
`merged_from: ["X", "X"]`; the scorer built that as a **set**, collapsing it to one name and counting
no merge. The expectation was unsatisfiable by construction, and two models were recorded as failures
by it. The result line was `out=42/42 merges=0/8` — fifty entries in and forty-two out means eight
things merged, so **the line contradicted itself and the count was the honest half.**

Three rules, and the first two are the same rule:

- **A control is a change, and a change can be the cause.** Before believing a result that a control
  produced, run the control's own control: remove it and nothing else.
- **When two numbers in one result disagree, one of them is your instrument.** Not the world.
  Reconcile them before attributing either.
- **A number that cannot be explained by the cause you assign it is the cheapest bug signal you will
  get.** 639 against a cap of 16,384 needed no further investigation to be suspicious — only
  arithmetic. Do that arithmetic on every number before it becomes a finding.

### A control PAIR, both halves testing an axis the question was not on

Registering an outbound webhook on a self-hosted chat server with a bot token from the secret store. I
wrote the probe with two controls, deliberately, because this skill says to — one that must succeed
and one that must fail:

```
control ok  (public room directory) : 200
control bad (nonexistent endpoint)  : 404
FAILED 401 {"ok":false,"error":"invalid_auth"}
```

The pair is symmetric, both halves behaved exactly as written, and the conclusion I was about to
draw — "the API works, so the 401 means webhooks are forbidden to this bot" — was wrong.
**The chat server lists its public rooms without any credential at all.** That 200 proved the host
was up and the path routed. It said nothing whatever about whether my `Authorization` header was
being accepted, which was the only thing in doubt.

Replacing it with `GET /auth/whoami` — an endpoint that 401s anonymously — took one call and
inverted the answer. Anonymous: 401, as required. The value under the secret's `token` key: 401.
**The value under its `token_next` key: 200, the bot's own id.** The `token` key still held the
value from before the last rotation; nothing was forbidden, I was simply never authenticated. The original probe would have had me file a permissions problem that did not
exist, or go asking for access I already had.

**Having two controls is what made it feel sufficient.** One pass, one fail, on the same instrument
— that is the shape of rigour, and it is why neither got re-examined. But a success/failure pair
tells you only that the probe can move; it does not tell you it moves *along the axis you are asking
about*. Both of mine measured routing. The question was authentication. Zero coverage, presented as
two-for-two.

- **When the property in doubt is "do I have permission X", the control is the same call without X,
  and it MUST fail.** If the control still succeeds without the credential, it is not a control for
  the credential. Name the property first, then pick the control from the property.
- **A control's job is to discriminate, so ask what result would distinguish the two hypotheses.**
  "Endpoint is reachable" and "endpoint accepts my credential" both predict 200 on a public route,
  so that route cannot separate them and is worthless here however many times it is run.
- **A 401 on the operation is not evidence about the operation.** Authentication failures surface at
  whichever call you happened to make, so the first thing to rule out is that the credential never
  worked anywhere — cheaper than reasoning about an endpoint's permission model, and it was the
  answer.

### The disproof was in the row I had already fetched

I found a column already converted to `text` after triggering a render, and reported that the render
had done it. It had not: the migration record's applied-at timestamp said **four days earlier**, and
that column was in the same table, in the same query I had already run, two columns from the one I
read. The migration in question had ridden along inside a deploy — that mechanism was real, and I had
just verified it in the code — so the instance felt checked because the *mechanism* was checked.

It got worse before it got better: a peer wrote my attribution into a repo comment as fact, and from
there into two more files. **A wrong worked example is more durable than a wrong claim**, because the
example is the part readers trust and check the mechanism against, so it gets copied rather than
challenged.

Three things generalise:

- **"Most recent plausible cause" is an inference wearing a measurement's clothes.** When you can see
  a state and want to know what produced it, ask what would be true if something *else* had, and go
  look for that. Here it was a timestamp.
- **A verified mechanism licenses the class, never the instance.** "A deploy can silently apply a
  migration" was true and remains true; "*this* migration was applied by *that* deploy" was a
  separate claim with its own evidence, and I never asked for it. Keep the general lesson, throw out
  the example — do not repair the example to save the lesson.
- **Widen after a hit.** Having found one file edited after being applied, I compared all thirteen
  rather than patching the one. One instance is a sample of one, and the cheap moment to ask "are
  there others" is immediately after finding the first.

### The failure removed its own evidence from the sample

A build runner could not schedule; the CI system **skipped** the dependent `test` and `build-push`
jobs, and the pipeline went red having executed nothing. The obvious fix was to cut the runner's
memory request, and there was a measurement to justify it: peak working set across runner job pods
over 7d was a small fraction of what was requested. Seven times over-requested, apparently.

The measurement was real, the query was correct, and the conclusion was wrong. Only **two** distinct
job pods appeared in the series — and the heavy jobs, the ones carrying a much larger limit, were
*precisely the ones that had been skipped*. They never ran, so they never produced a metric, so they
were absent from the sample. **The population was thinned by the very failure the measurement was
meant to fix**, and it was thinned of exactly its heavy tail.

This is the denominator trap ([Part 2](false-confidence.md)) with a nastier mechanism: not a
denominator you supplied yourself, but one that **self-selected out**, and in the direction that
flatters the change you were already minded to make. A sample biased by an unrelated accident is
noise; a sample biased by the subject under investigation points the wrong way *reliably*.

Two questions that catch it, neither of which is "is n large enough":

- **Which members of the population could not have appeared here, and why?** If the answer names the
  failure being diagnosed, the sample cannot speak to it at all.
- **Does the bias run toward or against the change I want?** Toward is the dangerous direction, and
  it is the one that feels like corroboration.

### A file's current content is not evidence of when it acquired that content

I read a rule in my own resident memory, found it correct, and concluded it had been correct all
along — so the peer who had just walked into the trap must have ignored resident guidance. The
opposite was true: they had written that rule fifteen minutes earlier, *because* they walked into it.
A dated backup settled it — the copy from four days before carried `assert old in s` above
`replace(old, new, 1)` and no uniqueness check at all, meaning **the memory I was crediting with
pre-empting the incident had been teaching the bug.**

There was no missing check, no null result, no broken probe here — the read was accurate and the
inference from it was invented.

- **Observing a state tells you nothing about its history, and nothing in the state announces that.**
  Before writing "the guidance was already there," "this has always been," or "they ignored X" — go
  date it: `stat -c %y`, `git log -1 --format=%ci -- <path>`, or a dated snapshot. Incidental backup
  copies are sparse rather than a real history, so they answer "was this present on *that* date" and
  nothing finer. mtime dies easily — mine showed my own revert, so the peer's timestamp evidence was
  actually my write, not theirs. A snapshot nobody has touched outranks it.
- **A history invented about a file is a claim about whoever edited it.** Getting it wrong converts
  "the guidance exists because someone hit this" into "the guidance was resident and got ignored" —
  same sentence about the file, opposite verdict on the person.

### The fault being diagnosed had flattened the evidence the diagnostic reads

A peer proposed telling "13 items genuinely decommissioned" from "the source is reporting less" by
whether their `last_seen` timestamps were staggered or clustered. Sound reasoning, and the data
showed all 13 sharing one timestamp — which reads as *simultaneous, therefore upstream*, and actually
meant "that was the last sync that succeeded". Five days of failed syncs had collapsed every item's
history onto one value, so thirteen changes spread over those days would have looked byte-identical.
The check is only ever consulted after the outage, and the outage is what makes it lie — so it would
have answered confidently, wrongly, every time.

What survived was a status value recorded *while the system still worked* plus a distribution across
sources that no single-row comparison could show. **Prefer evidence written before the fault to
evidence written by it.**

Note also how it nearly shipped: the test asserted the timestamp was PRESENT in the message, which it
would have been. **A check on the shape of a diagnostic is not a check on its soundness.**

### A broken discriminator that AGREES on the one case you tested reads as validated

Writing a classifier to sort ebook files into "the browser reader can open this" and "needs the
publisher's desktop app". I picked three signals, one of them `chapter_bytes` from the parsing
library's body accessor, on the theory that a locked book has nothing readable in its chapters. Ran
it on the real book: `drm=True, nav_entries=0, chapter_bytes=0` → *desktop only*. Correct verdict.
Ran a control — an empty one-chapter book I generated — and it landed in the "plain ebook" bucket,
also correct. Two for two, so I committed it to the repo and cited it in a README.

It was broken. The accessor returns falsy for **both** files, and for a long unlocked novel too —
one whose first chapter extracts thousands of characters of text. On the next input the classifier
called an ordinary, unlocked book unreadable.

Two things kept it hidden, and the first is the one worth carrying:

- **The broken metric agreed with the right answer on the case I tested.** `page_content_bytes=0` was
  *true* of that book, and it *supported* the correct verdict — for a reason that had nothing to do
  with the book needing the desktop app. A signal that is right by coincidence is
  indistinguishable from a working one on a single case, and it reads as confirmation, which is worse
  than reading as nothing.
- **My control exercised a different branch.** An empty book cannot fail the way a content-bearing one
  fails, so it could never have caught this — it is the generic-broken-input control again, in a
  costume that looks especially convincing because the classifier *did* sort it correctly.

**A classifier needs one REAL input per output class, not one input plus a null.** The bug surfaced
the instant a second genuine book went through, and it surfaced as a contradiction I could check
against something I already knew — thousands of characters of extractable text against a metric
claiming zero content.

**And the arithmetic tell from the `max_tokens` case applies here unchanged:** a number that cannot
be explained by the cause you assign it is the cheapest bug signal available. Zero content bytes on a
long, visibly text-bearing novel needed no investigation to be suspicious.

The fix was to drop the metric rather than patch it, and rebuild the check on signals that can be
shown to differ across classes — the navigation entry count and the presence of an encryption
manifest. Then re-run all three inputs and assert they land in three *different* buckets, which is the
assertion the original pass never made.

### Reachability is not content, so "not in origin" over-reports by the squash-merge rate

Clearing a few hundred stale local branches before deleting everything not on the remote,
`git rev-list --count --branches --not --remotes=origin` reported **29 branches holding unique
commits**. The real number of branches holding unique *work* was **one**.

**A squash merge can never make the source branch an ancestor**, so every squash-merged branch shows
up as unique forever — the commit object genuinely is absent from origin while every line it added is
already there. Reachability is a proxy for content, and here it was wrong 28 times out of 29. Read in
the deletion direction it is the safe error; read as "origin is missing 29 branches of work" it
manufactures a fake preservation problem, and had I pushed all 29 to satisfy it I would have
re-cluttered the remote I was cleaning with 28 branches of nothing.

**Two instruments in sequence collapse it, and the second is the one that gets skipped.**
`git cherry origin/main <branch>` compares *patch-ids* and marked 26 of the 29 as already upstream.
That leaves the residue where patch-id also fails — a change that landed **reworked**, so its patch
differs while its effect is identical. For those, compare the FILE at both tips:
`git diff --quiet <branch>:<path> origin/main:<path>`, or count branch-only lines with
`diff <(git show origin/main:$f) <(git show $br:$f) | grep -c '^>'`. Two of the three survivors came
out at **zero branch-only lines** — one byte-identical, one where main's file was a superset with
extra comments. Only the third was real.

So the escalation is **reachability → patch-id → file content at both tips**, and each step is
strictly more expensive and strictly more truthful. Stopping at step one is what makes a cleanup
either lossy or pointless.

**And the diff that shows you this can lie about direction.** Reaching for
`git diff origin/main..<branch>` on a branch ~1200 commits behind rendered **all of main's advances
as deletions** — a 7MB payload announcing that the branch removes half the repository. The two-dot
form asks "what turns main's tip into this branch's tip", which on a stale branch is mostly "undo
everything since". The merge-base form (`origin/main...<branch>`, three dots) asks what the branch
*added*, which is the question. But note the trap in the honest form too: three-dot diffs against the
**merge base**, so its `-` side is ancestral content, not main's current file — which is exactly why
the file-level check above has to name both tips explicitly rather than trusting either diff.

The shape it shares with the rest of Part 1 ([probe-rules.md](probe-rules.md)): **the cheap check was
almost the right check**, and it was already computed. `--not --remotes` is one command, it is the
command every cleanup guide reaches for, and it answers a question adjacent to the one being asked.

## My "old code" control ran the new code

To prove a new test fails without the fix, I copied the package with the old files into a scratch dir
and ran pytest from the repo with `PYTHONPATH` pointing at the copy. The test passed, which the logic
said was impossible. The repo's `pyproject.toml` had `[tool.pytest.ini_options] pythonpath = ["src"]`,
which pytest puts ahead of `PYTHONPATH`, so both runs imported the fix. `python -c "import pkg;
print(pkg.__file__)"` printed the copy, because that check runs without pytest's ini.

- **Prove which code the control runs from inside the runner that runs it**, not with a separate
  interpreter. The other ways a build ignores `PYTHONPATH` (editable installs, `conftest.py` path
  inserts, `go.work`, cargo path overrides) fail the same way.
- **The robust control is a whole tree of the old commit** (`git archive <base> | tar -x -C <dir>`),
  with the new tests copied in, run from that dir. Then nothing in the repo can import the new code.
- **"Passes on old code, impossible by the logic" is the tell.** Suspect the control before
  concluding the test is weak.
