# False zeros: probes that could not have seen the thing

Part 1 of the [instrument-failure case files](../instrument-failures.md) (from `verify-dont-anchor`).
Load it when a probe returned nothing, "absent", "untracked", "ruled out" or a clean count, and that
empty result is about to become a finding. Every case here is a probe whose silence described the
instrument — a blind enumeration, a shared filter, a capped page, an unreachable branch — rather than
the world. The general rule and its short examples are in [probe-rules.md](probe-rules.md).

### A partially-blind enumeration cannot report what it was not allowed to see

Diagnosing a wedged daemon, the load-bearing claim was "the log stopped 15 minutes before my test
request, so the daemon is not servicing requests". That claim dies if the log merely *rotated*, so I
went to check for rotated copies:

```bash
for f in "$D"/*.log "$D"/*.log.* "$D"/*.dat; do
  [ -f "$f" ] && stat -c '%y %10s %n' "$f"
done | sort -r
find "$D" /var/log -newermt '...' -iname '*<svc>*'   # second opinion
```

Both came back showing only one file, and I read that as "no rotated logs exist". The directory was
mode `d-wxrw--wt` — for `other`, execute **without** read. I could `cat` any path I named, and could
not *list* the directory. So every glob failed to expand, `[ -f ]` discarded the literal, and `find`
was equally blind. Naming the candidates instead settled it in one call:

```bash
for n in svc.log svc.log.old svc.log.1 svc1.log svc_event.log; do
  [ -f "$D/$n" ] && stat -c '  %y %10s %n' "$D/$n" || echo "  (absent) $n"
done
ls "$D" >/dev/null 2>&1 && echo "dir IS listable" || echo "dir NOT listable"   # the control
```

No rotated copies existed, so the conclusion survived — by luck, not by method.

- **The idiom was correct; the inference was not.** `for f in "$D"/*.log; do [ -f "$f" ]` is the
  standard guard *against* an unexpanded glob, and it behaved exactly as designed. Nothing was
  misused, so nothing warned me — the defect was reading a silent non-result as a negative finding.
  This is why it is not gateable: the command string is fine, and no string can show the inference
  that is about to be drawn from it.
- **`x` without `r` splits reading from discovering, which is the most deceptive permission there
  is.** Opening a known path succeeds while enumeration returns nothing, so the probe looks alive. A
  directory you cannot list is not a directory you cannot read.
- **`find` is not a second instrument here.** It needs the same read bit, so running it felt like
  corroboration while sharing the single point of failure — the "several checks agreeing" trap in its
  filesystem costume.
- **The sharpest part: the enumeration was only PARTIALLY blind, so it returned a non-empty result.**
  One literal path in the list resolved, so the output looked like a working probe with a real
  finding. A wholly empty result would have prompted suspicion; a plausible one did not. When a probe
  mixes literal and discovered inputs, the literals can carry it past the moment of doubt.
- **The control is one command and answers it outright:** make the enumerator prove it can enumerate
  (`ls "$D" >/dev/null`) before believing any zero it reports.

### The sweep and its own verification shared a filter, so the check confirmed the blind spot

Renaming a project across three repos. The script did the replacement and then counted what was
left, both through the same `--include` list:

```sh
B=$(grep -ro 'old-name' --include="*.py" --include="*.toml" --include="*.yml" … . | wc -l)
grep -rl 'old-name' --include="*.py" --include="*.toml" --include="*.yml" … . | while read f; do sed -i …; done
A=$(grep -ro 'old-name' --include="*.py" --include="*.toml" --include="*.yml" … . | wc -l)
echo "old-name refs: $B -> $A"      # printed: 16 -> 0
```

It printed **16 → 0** with four live references still in `.gitlab-ci.yml`. The CI file was not
reached by the replacement *and not counted by the check*, because both consulted the same filter —
so the verification could not see the one thing it needed to see. The `Containerfile` in the same
run was correctly fixed, and it matched a literal `--include` rather than the `*.yml` glob.

The cost was not the stale string. CI then pushed the image to the old repository name while every
Kubernetes manifest referenced the new one, so the deploy would have pulled a tag that does not
exist. Three sibling failures in the same session had the identical shape — a rename that swept one
place and not another — and **none of them were caught by tests**; every one surfaced only when the
real thing ran.

- **A check that shares a blind spot with the thing it checks will always agree with it.** This is
  not the "several checks agreeing" trap (independent-looking probes with one shared dependency) —
  here there was only ever *one* instrument, used twice, and running it a second time felt like
  verification because the number changed.
- **So verify a sweep with a DIFFERENT instrument than the one that made it.** Walk the tree with no
  filter at all. It is three lines of Python and it is the only thing that can disagree with the
  filter.
- **Give the walk a control that proves it sees files** — count a term you know is everywhere. A
  zero from a walk that visited nothing reads exactly like a clean result.
- **Suspect this specifically when a rename spans repos.** The sweep is naturally scoped to the
  repo you are standing in, and the thing that breaks is in the other one — manifests, CI config,
  a sibling project's references. Enumerate the repos first, then sweep each.

### `git log -- <path>` walks HEAD, and I read its silence as "untracked"

A peer session left a documentation file in the shared checkout. Asked to deal with it, I ran
`git log --oneline -3 -- <path>`, got nothing, and concluded the file was untracked — then said so in
a commit message about to land on `main` ("It was untracked, so it was also its own best example"),
and deleted the file.

It was committed and pushed the whole time, on a branch that was not my HEAD. `git log` without
`--all` walks *the current HEAD's* history, and my HEAD was `main`. The probe answered its own
question correctly and I asked the wrong one.

- **The narrow instrument reporting its ceiling as the world's**, in git's costume. The rule is
  already resident in `verify-dont-anchor`; being resident did not stop me. `--all`, or
  `git branch -a --contains`, or `git log --all -- <path>`, is the whole fix.
- **A shared checkout is what made it plausible.** The file *was* untracked relative to `main`, so
  `rm` produced a clean `git status` and nothing contradicted me. Minutes later the peer switched the
  checkout to its own branch, the checkout restored the file as a tracked one, and `git status` was
  clean again for the opposite reason. Two clean statuses, two different worlds — and the second is
  the one that exposed it. `assume-the-checkout-is-shared` and the null-result trap compose: **on a
  shared checkout, "is this file in git" is not a question about the file.**
- **The damage was in the prose, not the delete.** The file came back on its own. What would have
  shipped was a false sentence about a colleague's work — the asymmetry `verify-dont-anchor` names: a
  wrong negative *about someone else's* output reads as "they never committed it".
- **The control is one flag.** Before writing "untracked", "never committed", or "not in git", run
  the same probe with `--all`. Cheaper than the commit amend it cost.

### An empty input passes a universal check, and a missing file hashes clean

`all([])` is `True` — "every entry is a GUID" over zero entries is true, and a fixture missing a
control exercises the reject path rather than the path meant to be tested. An empty input can also
yield a plausible *value*, not only a vacuous pass: `md5sum` on a missing file inside a command
substitution returns `d41d8cd98f00b204e9800998ecf8427e`, the digest of nothing, which reads as the
most concrete evidence a check can offer — and a hash is the last thing anyone re-reads. (`find` will
not descend a symlink without `-L` or a trailing slash, which is how the file went missing.) Guard a
digest with `[ -f ]` and print ABSENT rather than a digest.

Two examples from one evening: a peer read an env var out of a *distroless* pod with stderr
suppressed, got `""`, and their checker reported "all entries are GUIDs: True"; my own DOM fixture,
lacking the two date controls the real page renders, measured a page that had correctly *declined* to
filter and read exactly like a broken predicate. Both cases also had a second signal already
contradicting them: the pod's own startup gate FATALs on a blank group list, so a *Running* pod
disproved the empty read.

- **A broken probe returning nothing renders as a clean verdict, and a clean verdict is the one
  nobody re-reads.** Before believing a pass, check the collection it quantified over was non-empty.
- **Prefer a check that counts (`== 1`) to one that quantifies (`all`)** — a count cannot be satisfied
  by nothing.

### A keyword filter's reject pile is where the damage hides

A keyword filter for a second-hand marketplace's bicycles category fed both directions of the same
mistake: listings titled "Rear rack for a touring bike" were filed as bicycles, while actual bicycles
were dropped because their description said `helmet` — they *mention* a helmet, but the filter read
the string as meaning the item *was* one. The first is visible in the accept pile and was caught in a day; the second is
invisible there by construction, and was only found by enumerating what the filter rejected.

- **A keyword cannot tell a product from a feature that mentions one**, in both directions — a false
  match in the accept pile, a false drop in the reject pile.
- **Audit the reject pile, not just the accept pile** — and if a filter has no reject pile you can
  read, that is the defect. Same shape as a null result, one layer earlier: the absence is
  manufactured by your own instrument, and the output looks clean because the evidence was discarded
  before it could be inspected.

### A ruled-out finding travels only as far as its probe

I handed a peer *"memory pressure is ruled out — no OOM lines in dmesg"* as a closed question. The
probe could not have returned non-zero: that platform's OOM controller runs in userspace and never
emits the kernel string I was grepping for. Two independent sessions had to spend real effort
disproving a claim that had never actually been checked.

The same day, a guessed annotation key returned a clean `MISSING` on all ten namespaces I queried,
and that nearly got reported as a contradiction of a colleague's correct finding. **N identical
results across independent subjects is the instrument, not the world** — the key was wrong, not the
data.

A related trap aimed at a person rather than a fact: a peer said they had cited a backup in a shared
file; I ran `grep -c <filename>` for it and got `0`, and was mid-sentence on "they said they did it
and they didn't" before reading the paragraph instead — they had cited the same backup *by date*
rather than by path. The probe was sound and answered a question I had not meant to ask.

- **A negative finding travels with its probe, not just its verdict.** Say what was run and what
  would have shown the opposite, so the recipient can see the hole rather than inherit the
  conclusion — a positive claim invites a spot-check, but "X is ruled out" removes X from their
  search space entirely.
- **Probing for a specific FORM of a claim and getting zero tests the guess about the wording, not
  the presence of the claim.** Before a zero becomes "they never did this," reread the source
  directly — the accusation lands harder than the correction, so the check owes it more care, not
  less.

### A regex is a proxy for the content, and a wrong proxy answers confidently

Three near-misses in one sweep, all mine, from the same instinct to write one clever pattern instead
of iterating the real files: a character class missing `_` reported an indexed file as missing, an
unanchored personal name matched inside an unrelated word, and a case-sensitive grep passed a bundle
that a case-insensitive one caught.

- **Prefer a loop of literal matches to one clever pattern.** For any "does every X appear in Y" or
  "what is still referenced" question, iterate the real files and test each one literally (`grep -Fq
  "$name"`) — the loop has no regex to get wrong. When the question is "what does this file say,"
  read it, or hand it to an agent that will.

### An `except` clause for an exception the library never raises

A handler written for the wrong exception type is dead code, and the number it fails to produce reads
as a finding about the world.

A network probe classified hosts as "serves a web page" / "serves TLS but the certificate does not
verify" / "serves nothing", with `except ssl.SSLError` for the middle case. **urllib wraps a TLS
failure in `URLError`**, so that branch never executed once. Every self-signed host fell through to
the catch-all and was recorded as serving nothing, and the run's count of untrusted certificates came
out as **0** — a clean, plausible, entirely manufactured number.

Nothing errored. The taxonomy looked careful *because* it had three branches, and the count looked
like good news about certificate hygiene. The real figure, found by connecting with a raw socket
instead, was a substantial fraction of the apparently-dead hosts.

Two things make this worth its own entry rather than filing under "test your code":

- **A zero from an unreachable branch is the falsely-clean shape at its purest.** The other entries
  here are probes that returned a wrong answer; this one returned an answer about a category that the
  code could never place anything into.
- **The diagnosis was wrong first, and confidently.** The initial theory was a 6-second timeout;
  re-testing at 20 seconds produced the identical failure on all six samples, every one
  `CERTIFICATE_VERIFY_FAILED`. *Re-running the same probe with one parameter changed is what
  separated a guess from the cause* — see "a CONTROL is a change" in
  [controls-and-inference.md](controls-and-inference.md) for the mirror of this.

**So: for any exception branch that classifies rather than merely recovers, prove it can be
reached.** Raise the condition on purpose once, or assert the branch's counter is non-zero over a
population large enough that zero would be surprising. A `try/except` that has never fired is
indistinguishable from one that cannot.

### Truncating a response for DISPLAY, then parsing the truncated copy

A capability probe over five model endpoints behind one API, asking which of them can accept an
image. The fetch helper ended `return r.status, r.read().decode()[:600]` — a slice added for
transcript hygiene, so a large body could not dump itself into the terminal. The same string was then
handed to `json.loads`.

One model's envelope was ~700 bytes. It got cut mid-object, `json.loads` raised, and the probe
printed `UNPARSEABLE` beside that model's name. **That model was the only one of the five that could
actually see the image** — re-probed without the slice, it scored 4/4 on a two-colour-by-two-shape
control while every other endpoint failed it. Reporting the first run would have eliminated the right
answer and left the conclusion "nothing here can do this", which was the expected result and would
not have been questioned.

Three things make it worth its own entry:

- **The corrupting step was added for a good reason and reads as diligence.** Not printing whole
  response bodies into a permanent transcript is correct (see `print-names-not-values`). The defect
  is that the display path and the parse path were the same string — a caution in one dimension
  silently became a data loss in another.
- **It fails toward the hypothesis.** The probe was written expecting most models to refuse, so a
  model rendering as broken confirmed the prior. A false zero at least looks suspicious; an
  `UNPARSEABLE` on one row of five reads as that row's own fault.
- **`json.loads` raising is not evidence about the sender.** The exception is equally consistent with
  a malformed response and with a well-formed one the reader damaged, and nothing in the traceback
  distinguishes them.

**So: never parse a string you shortened for printing — keep the full body and slice only at the
`print`.** And when exactly one subject in a sweep fails to parse while its siblings succeed, suspect
the reader before the subject: re-fetch that one and look at the raw bytes. Same family as "your
probe is broken, so the zero describes your regex rather than the world", one layer earlier — here
the instrument damaged the evidence after collecting it correctly.

### A paginated LIST endpoint answers a different question than "does this exist?"

Asking a registry, an issue tracker or any paged API to *list* things, then filtering the list, is
the natural way to answer "is X there?" — and it is the wrong instrument, because the server
silently caps the page. The call returns 200 with a plausible body, the filter finds nothing, and
the zero reads as a fact about the world rather than about the page size.

Measured twice in one turn, on the same question. Looking for CloudNativePG image tags:
`GET https://ghcr.io/v2/cloudnative-pg/postgresql/tags/list` returned 100 entries (the default page)
and my version filter matched none — so I concluded Postgres 17/18 tags did not exist. Re-asking
with `?n=1000` returned exactly 1000, and `17-bookworm` was plainly in it. I fixed the page size,
believed the second answer, and filtered for `standard|system|minimal` variants: again zero, again
reported as absence. That list was *also* capped at exactly 1000 — ghcr.io's ceiling — and the
variants were simply past the cut. `17-standard-bookworm`, `17-system-bookworm` and
`18-standard-trixie` all existed the whole time.

Note the shape of the near-miss: the user remembered the image being larger, which is the only
reason the second false zero got caught at all. Two independent measurements had already
"established" the opposite, and I had written the wrong conclusion into a decisions file.

- **To ask whether one specific thing exists, address it directly and read the status code.**
  `GET /v2/<repo>/manifests/<tag>` returns 200 or 404 and cannot be truncated. Enumeration answers
  "what is on this page"; it never answers "what exists".
- **`len(results) == limit` is the tell, and it is exactly what a satisfied filter hides.** A body
  holding precisely 100 or 1000 items is a page, not a population. Check the returned count against
  the requested one *before* believing any filter run over it, and follow the `Link: rel="next"`
  header if you must enumerate.
- **A control proves the probe works; it does not prove the probe is COMPLETE.** My eventual
  `nonexistent-control-tag -> 404` control was genuinely useful and genuinely insufficient — it
  established that the manifest call discriminates, which is a different claim from the list call
  being exhaustive. A control on the fixed instrument says nothing about the broken one.
- Generalises past registries: GitHub/GitLab APIs (`per_page`, default 20-30), `kubectl` with a
  server-side chunk limit, S3 `ListObjectsV2` at 1000 keys, LDAP size limits. Any of them will hand
  you a truncated success and let you call it an absence.
