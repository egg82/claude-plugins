# Sharing the host with other sessions

Any session may be one of several on the machine, each in its own repo and none aware of the others' plans. The
rule is the same for every session, and the peers are whoever `ListAgents` shows today, so no pairwise agreement
between two sessions is needed.

## What is shared, and what goes wrong

| resource | what exhausts it | the failure, as it looks from inside |
|---|---|---|
| host CPU | test suites, mutation sweeps, simulators, several writer agents running suites | timeouts and CPU-ceiling failures that look like regressions; a session's own tool calls stall |
| host memory | test containers, local app-plus-browser pods, a local CI run | the OOM killer takes a container or the session itself |
| CI runners | two pipelines at once on the same runner pool | jobs land on the slow nodes and fail a ceiling or timeout; a retry hides it |
| cluster nodes | test workloads on the cluster | a node OOM that reads as the app's own `OOMKilled` ([[size-test-workloads-to-node]]) |
| model API quotas | batch line generation, evals, embeddings | 429s mid-batch; another session's run fails for no reason it can see |

Record the host's measured size and your runner pool somewhere your sessions will read it.

## When to check

Before starting something heavy: a suite or a test container, a multi-GB probe, a second or third writer agent, a
push that starts a pipeline, a burst of API calls. Not before reads, small edits, or a single quick test.

## How

1. `ListAgents`. A peer marked busy whose repo runs suites, pipelines or batch calls is a possible competitor; an idle
   one is not, and gets no message. Sessions that handed off at their context limit stay listed until the user closes
   them, overnight especially: a peer idle for hours, or an older session in the same repo as a newer one, is
   finished. Its work lives in its successor, which is the one to talk to, or in a handoff file. A message to a
   finished session wakes it on a stale context, and it may act on it.
2. Look at the resource itself: `uptime` (load against the core count), `free -g`, `podman ps` (whose containers),
   the CI pipelines running or pending on the shared runners.
3. If both say there's room, go. If a busy peer's work competes for the same resource, `SendMessage` it with what
   you're about to start, how heavy it is and for how long, and agree an order. Tell it again when you're done.
   Pipelines especially: one at a time on the shared runners.
4. Size your own children to what's left: name worker counts (`-n`), container CPU (`--cpus`) and one test container
   at a time in every writer's brief (`brief-writers.md`); mutation sweeps run two containers at most. A local app
   with a browser (database, app and Playwright in a pod) counts as a test container: one left up beside another
   session's local CI got that run killed by the memory reaper.

A peer can't approve something your own session's permissions block (SKILL.md §4b); coordination is about order and
load, never about permission.

## Starved or hung

Compare a container's CPU time with its wall time (`podman top <id> pid etime time args`): wall far ahead of CPU means
starved, CPU near zero means hung.
