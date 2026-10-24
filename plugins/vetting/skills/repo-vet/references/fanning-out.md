# Fanning out a vet

Open this before spawning subagents on a sizeable repo.

On anything sizeable, fan out -- but **give each subagent a disjoint slice** (claims-vs-reality,
credentials/auth, data-integrity write paths, test quality, maintenance history; or by subsystem).
One agent owning "all security" beats three splitting it by synonym: a real pass once spawned
"Security audit", "Security and credential audit", and "Injection and log leakage audit" against the
same repo and paid three times for one answer. Depth is worth paying for; redundancy isn't.

Clone the repo **once** into a shared workspace and point every subagent at that tree. The expensive
repeatable work -- clone, dependency install, a test run, GitHub API pulls -- should happen once and
be readable by all of them. Have them write raw artifacts (test output, coverage numbers, grep
results) into the workspace so a sibling can *read the artifact* instead of regenerating it; nothing
is lost by sharing a test log, and a lot is wasted by running the suite twice.

Have each subagent write findings to `findings/<slice>.jsonl` (not `.md`, which the Write tool refuses
from subagents) **as it goes** rather than holding them to
return at the end. Long fan-outs get interrupted, and a vet whose children died still has their work
on disk -- one run lost four complete vets because every finding lived only in agent context.

Independence is the part to protect: subagents share *evidence*, never *conclusions*. When two of
them disagree, that's a finding -- go back to the evidence and say which read won and why. In one run
an agent inferred that a forked project had surely inherited its parent's unauthenticated endpoints;
plausible, and wrong -- a sibling had already tested it live and found auth enforced. Handing over
the conclusion would have propagated the error instead of catching it.

Standing an instance up is the expensive part, so **share the observation and isolate the mutation**.
One instance in a known state serves every read-only probe concurrently --
does this endpoint 401 unauthenticated, what are the file permissions, does this route 404, what does
the page render. But anything that *writes* needs its own throwaway: completing the setup wizard,
planting canary credentials to test masking, changing settings, exercising an auth flow. Otherwise
agents silently corrupt each other's evidence and you can't tell which reading was real. First-run
setup especially happens exactly once, so whoever tests "can setup be replayed?" burns the pristine
state for everyone. Own the shared instance's lifecycle yourself and write down what state it's in --
a probe result means nothing if the reader doesn't know what was configured when it ran.
