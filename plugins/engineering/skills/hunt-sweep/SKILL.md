---
name: hunt-sweep
description: "Run the standing whole-stack hunt over a repo — correctness, performance and (with an attack surface) security lanes, each as duplicate hunters in waves across every layer — then dedupe and land each confirmed finding test-first. Use when the user asks to \"run the bug hunts\", \"hunt for bugs and optimizations\", \"a bug hunt and a perf hunt\", \"add a security hunt\", or repeats that standing instruction. Hunter method is bug-hunt."
---

# Hunt sweep

The standing instruction this encodes: **two or three lanes, every layer, duplicated, proven,
landed.** The
hunter's own method lives in `bug-hunt`; how to brief and size agents lives in `fanout-craft`; how
findings land lives in `agentic-engineering` ("Bug hunts land findings-first"). Load all three before
dispatching. This file is only the shape of the run.

**Check `repo-llm-stance` first.** In a repo whose owner hand-writes the code and wants the LLM as advisor only, stop at the
confirmed-findings report (issue text for the owner to file), dispatch no writers.

## Defaults (use unless the user says otherwise)

- **Lanes:** `correctness` (bugs and requirement gaps against the repo's own stated contracts),
  `performance` (optimizations a count, plan or measurement proves), and `security` **only when the
  repo has the surface** (auth/identity, untrusted input, writes to an external system — the trigger
  in `bug-hunt`'s `references/oracles/security.md`). Security is its own lane, not a row in the correctness brief: it
  asks "what do I control?" rather than "does this match the contract?", and a hunter holding every
  layer drops whichever stance it isn't already in. Each lane's method is its `bug-hunt` oracle file
  (`references/oracles/<lane>.md`), loaded up front; every hunter also reads `correctness.md`. The
  other domains there (resilience, state over time, UI and accessibility, LLM features) ride in the
  correctness lane's brief when the repo has their surface, and become lanes of their own only when
  the user asks.
- **Scope, every lane:** every layer — DB queries, indexes and migrations; the API; the frontend;
  CI config, gates and their controls; the Dockerfile/image; scripts and jobs; and the seams between
  them. Name these in the brief; a brief that names only the backend gets a backend hunt.
- **Width and waves:** 2 waves of one hunter per lane (4 hunters, 6 with security), with **byte-identical briefs**
  apart from resource names and the base ref. **Wave 2 hunts wave 1's fixes**, not the old code: on
  old code it spends budget re-finding known bugs, and on fixed code it also cold-reviews the fixes.
  The fixes live on an integration branch (`hunt/<date>-wave1`) cut from `origin/main`, never merged
  first where merging deploys. Do not show wave 2 wave 1's findings list; a seeded hunter re-finds
  the seed. The cost: wave 1/wave 2 overlap becomes unmeasurable, so don't quote a yield for the
  second wave from such a run.
- **Every hunter loads `bug-hunt` then `agentic-engineering`**, named in the brief's first line.
  **Layer skills load when the hunter reaches that layer, not up front.** Every loaded skill is
  re-read on every turn, so name the trigger rather than preloading:

  | Layer | Skill | Lanes |
  |---|---|---|
  | API routes, response models, OpenAPI; clients forced to poll or over-fetch | `api-contract-first` | all |
  | Tests, CI gates and their controls, a check that may pass for the wrong reason | `verification-gate` | correctness |
  | Proving a frontend defect by rendering it; timing a page load | `headless-render` | correctness, performance |
  | Frontend showing unknown as a value, unlabelled figures (honesty rules, not taste) | `ui-craft` | correctness |
  | Shell scripts, CI script steps, Dockerfile `RUN` lines | `shell-footguns` | all |

  The security lane does not use the built-in `security-review`, which is meant for a branch's pending diff (unverified) and a hunter's
  clean checkout has none. Its brief names the repo's actual surface: the auth header and roles, the
  permitted writes and their guard, where untrusted input enters.
- **Model:** per `fanout-craft` §1 and `bug-hunt`'s `references/fanout-evidence.md` (the execute
  instruction matters more than the model). State the choice and its reason when reporting.

## Before dispatch

1. **Read the repo's rules for the outside world**: CLAUDE.md, README "working on it", deployment
   notes. Write into the brief exactly which commands reach production, a vendor API, a cluster or a
   live site, and forbid them by name. Hunters get no credentials.
   **For a live app, read-only access to its deployment is allowed when the user grants it** (the
   cluster, its database, a copy of production data on this machine). It pays most in the
   performance lane (real row counts and plans) and the impact pass (real prevalence, real
   consumers). Find the access path yourself first and hand over exact commands: read-only kubectl
   verbs only, never Secrets; database queries on a **replica in recovery** (`pg_is_in_recovery()`
   = t), never the primary, each bounded with `statement_timeout`; heavy plans run on a local
   restore of a `pg_dump` taken from that replica, never on production. **The grant lives in your
   context, not the children's**: measured on one app, both the impact pass and the performance
   hunter were denied ("Production Reads") on kubectl and `pg_dump` even with the grant in the brief.
   So take the production steps yourself before dispatch — the dump (restore it into each consumer's
   own container as a second database, then check row counts against the replica) and the bounded
   prevalence counts the impact pass will need — and hand children the local copy.
2. **One isolated set of resources per hunter**, created by you, recorded in an assignment table:
   - a worktree on persistent disk, detached at the wave's base after a fetch — `origin/main` for
     wave 1, the integration branch's tip for wave 2 (`~/wt/<repo>-hunt-<id>`);
   - its own test database/container on its own port (never one already running — those belong to
     other sessions; check `podman ps` and `ss -ltn`);
   - if the repo's venv has an editable install, `PYTHONPATH=<worktree>` plus a proof line
     (`python -c "import pkg; print(pkg.__file__)"` prints a worktree path);
   - a findings file `<scratch>/hunts/<id>-findings.jsonl` and a scripts dir `<scratch>/hunts/<id>/`.
3. **Measurement hygiene for the performance lane** is in `bug-hunt`'s `references/oracles/performance.md`
   (proof by counts and plans, the podman-port stall, concurrent load); the brief's hygiene block
   carries the part about the sibling hunter.
   **Run commands from inside the hunter's worktree**: in one app's venv, `PYTHONPATH` alone still
   imported the main checkout from another cwd; the import-path proof line is what caught it.

Brief templates: `references/briefs.md`. Fill every `<placeholder>`; leave nothing to "the repo's
usual setup".

## While it runs

- A scope change from the user reaches running hunters only by `SendMessage`, the same turn.
- When a wave's last hunter reports, read each report and its findings file (a `completed` status is not
  delivery), run "After a wave" steps 1–4 below onto the integration branch, then create wave 2's
  resources on that branch and dispatch it in the same turn as the last fix lands.
- **Don't wait for the whole wave to start fixing.** Lanes rarely find the same defect, so verify and
  dispatch writers for one lane's findings as soon as it reports; dedupe across lanes again before the
  integration branch is handed over. Each writer you start loads the host under the performance hunter —
  tell it, the same turn.
- A hunter that reports far inside its budget with a "not reached" list gets resumed into that list,
  not accepted.
- Tear down a hunter's container and worktree only after its report is read and you will not resume it.

## After a wave (steps 1–4), and after the last (all)

1. **Dedupe the union by claim, never by `file:line`** (`bug-hunt`). Record which hunters found each:
   a finding all hunters found and one only a single hunter found are both real, but the single-hunter
   ones show what the second draw bought.
2. **Re-verify each survivor yourself** on a clean worktree of the wave's base — a hunter's repro can
   lean on a file it added. Drop what does not reproduce; keep the reason. This proves the repro
   runs, NOT that it tests the right thing or that the behaviour is a bug — it is not the kill pass.
3. **Kill, compose and impact pass by a FRESH agent** (opus; `bug-hunt`'s "Kill your own findings",
   "Compose", "Impact"): given only the claims and `file:line`, the hunter's reasoning withheld, its own
   clean worktree and database, read access to known consumer repos. Verdict per claim CONFIRMED /
   KILLED / DOWNGRADED with evidence, plus what a fix must preserve. A hunter's own killed list is
   self-review and does not count. Writers start after this, and their brief carries its
   "must preserve" lines.
4. **Hunt findings get FIXED; design decisions get DOC updates.** A confirmed defect is fixed this
   session, not queued. A finding whose fix is a design choice (a storage trade-off, reopening a
   recorded decision) goes to the user once as a recommendation; whatever they choose, the outcome
   this session is the doc made true (the false design claim corrected, the queue item written with the
   measured figures), not the build.
   **Land findings-first** on the integration branch, via writer agents (2–3 max, each in its own
   worktree and database, per `fanout-craft`): a strict `xfail` test asserting the wanted behaviour,
   committed alone; the fix is a separate commit that flips it. Run the agentic-engineering
   conformance review on each writer's commits before they join the branch. Performance fixes follow
   `references/oracles/performance.md`'s *Proof* and *a fix can move cost* rules (count-asserting tests,
   the most-opened path timed before and after); put both in the writer's brief.
   **A fix to a scheduled job's write path gets a multi-run simulation by a fresh agent** before the
   MR: three consecutive runs through the real pass, state persisted between them, counting writes per
   run. A single-run test can't see a loop. In one hunt, an undo-on-rejection fix restored the state that
   had selected the item, so every run re-sent the same write and clobbered an unrecoverable user-uploaded file; its
   own tests were green.
   **Before the MR, verify the merged tree in CI's own image**, not the local venv: a 3.11 venv
   hid that 3.12 ships no setuptools, and a workstation's jq let tests labelled "with jq" pass
   while CI silently ran the fallback. One `podman run` of the CI image over a `git ls-files` copy,
   against its Postgres version, run once per job's tool set, is the whole cost.
5. **Before a release's out-of-band step, ask what ELSE it changes.** A push that uploads every body
   can also unblock work queued against a body that matches the image (in one case, queued installs were
   held, refused on a body mismatch; had the image carried their queued body, the push would have released
   them). Hash the bodies the step will write against what the target holds, run its dry-run mode
   (`--check`) first, and do the real step only when the diff is exactly your change.
6. **Respect the repo's release model.** If merging deploys, merge only on the user's go-ahead, then
   watch the release through (pipeline, rollout, migrations, the out-of-band step, the first run on
   the new code). Never file issues or open MRs from a hunter.
7. **Report**: one table per lane (finding, `file:line`, proof, found-by), the killed hypotheses
   worth keeping, and what was not covered.
