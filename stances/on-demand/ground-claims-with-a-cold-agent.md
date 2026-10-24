---
name: ground-claims-with-a-cold-agent
description: "Spinning up a fresh delegated agent to ground a claim or judgment against the actual artifacts is usually worth its cheap cost — the delegated, anti-anchoring complement to verifying before you assert. Highest payoff on a skip/dismiss, a root-cause guess, or a completeness claim."
metadata:
  type: feedback
---

Before acting on a non-trivial **claim or judgment**, delegate a **cold agent** to ground it against
the real artifacts. It's cheap and it repeatedly catches things the acting context misses, because
the same reasoning that produced the claim is anchored to it — a fresh agent checks against reality
instead of inheriting the anchor.

The moments it pays off most:

- **A skip / dismiss** — "these are duplicates", "nothing new here", "already covered". This is where
  a wholesale eyeball-pass quietly drops real content.
- **A root-cause guess** — send an agent to prove or refute it against the code/logs before you build
  on it.
- **A completeness claim** — "that's everything", "all handled". Have an agent enumerate what's
  actually there.
- **A trust/fit verdict — run `repo-vet` / `cc-tool-vet` in a fresh agent, never inline.** Prompt =
  the skill + the target, no word on whose repo it is or the expected verdict; hold a sealed prior and
  grade against it. A cold run can't be swayed by earlier favourable discussion (sycophancy risk,
  worst on the owner's own projects), and one that actually clones and runs the repo sees what an inline
  read cannot. This is an invocation-time decision, which is why it lives here and not in the skill.

**How to apply:** give the cold agent the *real source* (the repos, files, both sets) so it grounds
against reality, not vibes — and do **not** prime it with your conclusion (that invites a
rubber-stamp). Example, reconciling a shared-lineage set (two copies of a config set, a merge, a dedup): one
agent per tier diffs incoming vs local **by function**, classifying FULLY_COVERED / NET_NEW / NO_TWIN
with exact snippets. It reliably surfaces diverged twins (a common-lineage note still picks up a
caveat the other copy lacks) and net-new items misfiled as duplicates — both of which a skip-by-eye
loses. Pairs with judging by actual content rather than name/size proxies
([[content-is-king-not-proxies]]) and with opaque run labels ([[subagent-paths-prime-results]]).
