---
name: share-the-host
description: Several sessions share one machine's CPU, memory, CI runners and API quotas; check load and peers before heavy work
metadata:
  type: feedback
---

Several Claude sessions can run at once on one machine, in different repos. They share the host's CPU and memory,
the CI runners, the cluster's nodes and the model APIs' quotas. **Before heavy work — a test suite or container, a
multi-GB probe, a second writer agent, a CI pipeline, a burst against a rate-limited API — run `ListAgents` and look
at the load (`uptime`, `free -g`, running pipelines).** If another busy session's work competes for the same
resource, message it before you start and say when you're done. Never message an idle one: sessions that handed off
at their context limit linger in the list, and a message wakes them on a stale context. Otherwise just go: this is a
check, not a ritual, and no standing pairwise agreement replaces it.

**A CI job that is slow or times out on some runs and not others** may be landing on the slower runner nodes; pin a
long job to the fast ones if your runner setup allows it.

Method, what counts as heavy and who to tell: `fanout-craft`'s `references/shared-resources.md`. Cluster-side
sizing: [[size-test-workloads-to-node]]. Relates to [[skill-fanout-is-authorized]].
