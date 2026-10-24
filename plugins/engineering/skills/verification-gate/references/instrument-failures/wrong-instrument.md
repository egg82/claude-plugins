# Wrong instrument: the probe measured something other than what runs

Part 1 of the [instrument-failure case files](../instrument-failures.md) (from `verify-dont-anchor`).
Load it when a probe gave a real, confident answer and you are about to trust it — a success line, a
hash match, a benchmark, a poll, a green local suite. Every case here measured correctly, but measured
a different configuration, process, transaction, workload or working tree from the one in question.

### A success message that names the wrong thing

The merge succeeded. The GitOps reconciler printed `✔ applied revision <rev>`. The deployed CronJob
image did not change.

An unrelated admission webhook was timing out, so the server-side dry-run of the *entire*
Kustomization failed and the apply was a silent no-op. The revision in that ✔ was the one already
applied two commits earlier. **The disproof was printed inside the success line**, and the checkmark
is what gets read.

What made it hard to catch is that nothing else looked wrong: the webhook pod was `Running`,
heartbeating a cert check every five minutes, reachable from inside the cluster, and a *different*
admission webhook served the API server correctly throughout. Every local signal said not-my-problem.
It then cleared on its own.

Two rules out of it:

- **Assert on the effect, not the operation.** The only tell was `kubectl get cronjob` showing an
  unchanged image after a merge that had reported success. No check was armed for that.
- **When a tool reports success with an identifier in it — a revision, a digest, a version — read
  the identifier.** A stale one inside green output is more convincing than any failure.

### "No cluster access" is not "cannot read the deployed source"

A peer reported a response header as missing from a proxied service; I traced it to a proxy plugin
discarding every upstream response header but `Content-Type`, and filed the finding with an explicit
caveat: read from the upstream source on GitHub, **not** out of the running image. The rule "read the
source out of the artifact actually deployed" was already resident, and I could not satisfy it — no
kubeconfig for that cluster.

The peer, who *did* have `kubectl`, went looking and reported back that the component was on no
cluster they could reach either. Two sessions, independently, concluded the caveat had to stay.

Both of us were wrong, and identically. **The deployed artifact lives in a registry, not in the
cluster.** The manifest pins an image by name; that image is pullable:

```bash
podman pull --platform linux/amd64 <registry>/<repo>:<tag>
cid=$(podman create <registry>/<repo>:<tag>)
podman cp "$cid":/path/inside/image ./local-copy
podman rm "$cid"
sha256sum upstream-copy local-copy      # then diff, and grep the LOCAL copy directly
```

Byte-identical, both files. The caveat came off the issue in one tool call.

- **`kubectl` is one instrument for "what is deployed", and the narrowest one.** The registry answers
  the same question without a cluster, without credentials to a control plane, and for an image that
  is not currently running anywhere.
- **Verify on the extracted copy, not on the hash alone.** Hash equality proves the files match; the
  claim was about what the code *does*, so `grep` the copy that came out of the image and let the
  matching hash be corroboration rather than the evidence.
- The generalisation is the resident rule's own last paragraph turned on its author: **before writing
  "cannot", name the wider instrument.** "I lack cluster access" felt like a fact about the world and
  was a fact about the one tool I had reached for. It cost a filed caveat, a peer's search, and very
  nearly a code change made on unconfirmed evidence.

### Copying a configuration: copy every field it HAS, not the fields you thought of

Duplicating a credential between two systems, the value was verified byte-identical by hash on both
sides — and it still did not work. The receiving system reported "invalid username/password", which
points squarely at the credential and not at the transport.

The value was right and the **configuration around it** was wrong: the CI system expands `$` inside
variable values unless a `raw` flag is set, so a password with `$Qx9` in the middle arrived
with those four characters missing. The copy had faithfully carried `masked` and `protected` — the two flags
that came to mind — out of four the API returns.

**Hashing the value proves you copied the value. It says nothing about the settings that decide how
the value is interpreted**, and those are exactly what differs between a working sibling and a new
instance. The fix is mechanical: enumerate the fields the *source object* actually has
(`{k: src[k] for k in SETTABLE if k in src}`) rather than listing the ones you remember. A named list
of fields is a list that goes stale the next time the API gains one.

### A polling loop inside one transaction samples a frozen snapshot

Trying to learn whether a bulk writer emits `COPY tbl (cols)` or writes positionally — the answer
decided whether `ALTER TABLE ADD COLUMN` was safe or would silently corrupt every write — I polled
`pg_stat_activity` for the statement text. Nothing. So I widened the filter from `COPY%` to *every
query from the writing user*, ran it for 90 seconds, and still got nothing, against a table that was
visibly taking bulk inserts the whole time.

Two escalating wrong conclusions were available and both are worse than the truth: that my pattern
was wrong, and that **ingest had stopped**.

The probe was a `DO $$ ... LOOP ... pg_sleep(0.1) ... END $$`, and a `DO` block is **one
transaction**. PostgreSQL's `stats_fetch_consistency` defaults to `cache`, so the statistics views
are materialised on first access and do not change for the rest of that transaction. The loop sampled
one frozen instant 900 times and reported it as 900 observations of an idle server.

**A loop is not a series of observations unless something between iterations makes the source
re-read.** The tell was available and I nearly talked past it: the *first* sample already showed a
plausible-looking empty result, and every later one agreed with it perfectly — N identical results
that could not have differed. Same family as "several checks agreeing is not corroboration", with the
multiplication happening inside a single snapshot.

What actually settled the question was abandoning the transient-observation approach entirely and
reading the format string out of the binary (`grep -aoE 'COPY [^"]{0,120}' <binary>` → `COPY %s ( `).
**When a probe has to catch something in flight, prefer an instrument that reads the thing at rest.**
The artifact was sitting on disk the whole time, and no amount of polling was going to beat one grep.

### An out-of-process probe races the in-process lock it cannot see

Two jobs in one service walked the same resource list, and the remote API allows exactly one
session per resource, so the loser got back a lock error. I added an `asyncio.Lock` inside the
shared call, shipped it, then wrote a probe to measure whether the fix had helped — ten resources,
run with `kubectl exec ... python -c` against the very pod running the service.

Every resource came back with the same contention error, and the conclusion sitting right there was
**"the lock did not work"**. The runner-up was worse: "these resources are unreachable", which I was
about to write into an architecture answer as a finding.

An `asyncio.Lock` is a **process-local** object. My probe was a second process. It shared the pod,
the credentials and the resource, and none of the mutual exclusion — so the probe *was* the contending
session it was measuring. Confirmed afterwards from the service's own logs: its
sweep was mid-flight throughout.

**A probe that contends for the same resource as the system under test measures the contention it
created.** The tell is a result uniformly bad across every subject, including ones that worked
minutes earlier. It is the same family as N identical results being the instrument rather than the
world — except here the instrument is not merely blind, it is an *actor*, so the system genuinely did
do the thing the probe reports. That makes it far more convincing than an empty result and much
harder to disbelieve.

Two rules. **Before probing a system that serialises anything internally, ask whether your probe
enters through the same door or a different one** — in-process locks, connection pools, per-target
sessions, single-writer files and API rate limits all share this shape. And **prefer reading what the
system already recorded to re-running the operation yourself**: the service writes its own poll
outcomes, with reasons, to a table. Waiting one scheduled cycle and reading that table would have
answered the question with no contention at all — the instrument that does not participate.

### "The suite passes" is scoped to a working tree, not to the project

I reported 489 green while an open MR of my own was red. It had added a parameter to a handler, 18
tests called that handler directly, and my suite run was on a branch that predated the change.
Nothing was wrong with the run; the SCOPE of the sentence was — a local "the whole suite passes" is a
claim about one working tree at one moment, and it is heard as a claim about the project. With
branches in flight the honest instrument is the pipeline list, not the tree in front of you.

### A benchmark that repeats ONE input cannot see a fault whose cause is the MIX

Adding a connection pool to a web service made one of its endpoints **25x slower**, and it shipped
past a check written specifically to catch that risk.

psycopg promotes a statement to a server-side `PREPARE` after five uses on one connection. Postgres
then chooses, per execution, between re-planning for the actual parameters (a *custom* plan) and
reusing one plan for all of them (a *generic* plan) — and it chooses by comparing the generic plan's
cost against the **average cost of the custom plans built so far**. The query returned a handful of
rows for one parameter and many thousands for another, so a few broad queries lifted that average
until the generic plan won, and every selective query afterwards was planned as though it were the
broad one. Permanently, for that connection. 43ms on the first round of a mixed workload, 960ms on
the second, 1,000–1,900ms thereafter.

**The pre-deploy check ran one query sixty times**, read `custom_plans=15, generic_plans=0`, and
recorded in a code comment that the risk "does not materialise here". That result is *unreachable* on
a single-query workload by construction: with one parameter the average custom cost never rises, so
the generic plan can never win. The probe could only ever return the reassuring answer.

Three things make it worth its own entry rather than filing under the convenient-instance rule:

- **The fault is a property of the WORKLOAD, not of any input.** Every individual query in the mix is
  fine, and each one tested alone passes. There is no single bad input to find, so "try a harder
  example" — the usual correction — does not help either.
- **The tell was flatness across *different* queries.** Selective and broad queries converging on one
  ~1s cost is the same uniform-value-is-the-instrument shape as elsewhere in these case files, except
  the instrument was the *database's planner* rather than anything in the probe.
- **It was found by comparing two servers.** A freshly started process in the same pod, against the
  same database, served the same request in 53ms while the long-running one took 950ms. Same code,
  same data — so the difference had to be accumulated process state, which is what pointed at the
  prepared statement. Standing a clean instance beside the sick one is a cheap discriminator for any
  "it gets slower the longer it runs" claim, and it needs no instrumentation.

**The rule: when testing whether reuse is safe — a cache, a prepared statement, a pooled connection,
a memoised plan — vary the input across the range the thing will really see.** A benchmark that
repeats one input measures the harness. And where the reuse is governed by an *adaptive* policy, that
policy's input is the history, so the history has to be realistic before the measurement means
anything at all.
