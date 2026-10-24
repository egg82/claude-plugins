# Brief rules — the incidents behind them

Worked cases for rules stated in `SKILL.md` §2 and the `brief-*.md` references beside this file. Read
when a rule sounds arguable or you are about to skip it.

## Briefing against a summary instead of the artifact

Measured once. I had side-by-side screenshots of a reference build and a reviewer's write-up of
what differed. I briefed against the write-up: thirteen ranked presentation items, each concrete and
correct. The agent fixed nine and reported honestly. The user looked and said it still did not
resemble the reference — because the review had scoped itself to *presentation* and said so, so its
list never mentioned that the reference's main panel is always open and on the other side, that a
sub-panel is folded inside it, or that a status pill carries a count rather than a word. **Structure
was never on the list, and the list was what I optimised.** The picture had been in my hands the whole
time and contained every one of those facts.

## Briefing from your own memory of the reference

Measured once. Asked to build a UI in the style of some well-known reference sites, I
described them from memory — a confident, accurate-sounding paragraph about layout and density —
and briefed an agent on that. It optimised my paragraph faithfully and produced a table with
charts bolted on. The user's verdict: it still looked like a generic coding-assistant table. The sites
were a URL away the entire time. The user's correction is the method: **actually look at them, generalize
the design, then conform it to the app.** Capturing three of them and writing down what they share
was the step I skipped, and it is the step that distinguishes a derived system from a copied look.

## Two writer agents on one test database

Handing two writer agents one database URL is the same defect as a shared scratch directory wearing
different clothes: the suite's DB-backed tests `TRUNCATE`, so two agents running pytest concurrently
delete each other's fixtures mid-run. Measured once: both children reported intermittent
failures in files they had never touched, and **both independently concluded "pre-existing flakiness
in the shared test suite"** — a conclusion that is plausible, unfalsifiable from inside a single
child, and would have been believed if the parent had not re-run the suite serially afterwards
(deterministic green, three times). One of them spent a `git worktree` checkout of an older commit
trying to prove the flakiness pre-dated its own work.

## A child denied on permission-gated work

Measured once. A child was asked to create an app registration on a live auth server. It
was denied by the classifier as `[Credential Exploration]` on ordinary **read-only** lookups — listing
signing keys and settings — and spent **35 minutes and 80k tokens** re-approaching the wall.
The parent then ran the identical `curl` calls in its own context, got them immediately, and finished
the whole task in about four minutes. The user's explanation is the rule: permissions granted to the parent do not reach a subagent, even
if the parent approves them; that work has to be done wherever the user gives approval.

## Partition seam, and a measurement in a deploy's wake

Partition seam: one slice root-caused an API route returning 500 in production; a second owned the page that calls it; a third, asked whether the 500 mattered, said correctly that none of its four files called that route, a true statement about its own manifest received as a statement about the app. The consumer sat in the second slice's directory swallowing the failure with a bare `.catch(() => {})` and rendering nothing.

Deploy wake: a deploy rolled the pods, the restart kicked off a full ingest cycle, and an endpoint timed sixty seconds later read absurdly slow; `pg_stat_activity` showed the cycle still running. The fan-out-keyed rule was resident and did not fire because nobody was fanning out.
