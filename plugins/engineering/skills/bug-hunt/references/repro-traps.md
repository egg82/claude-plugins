# Reproduction traps — isolation, false nulls, and probing the wrong source

Open this when running several PoC agents at once, when a probe returned "nothing there", when using a
live/deployed system as evidence, or when the target spans separate environments.

## Isolate concurrent execution agents by blast radius

When several PoC/repro agents run at once against shared mutable state (a test server, database,
shared fixture), classify each up front: **read-only / structural** (code analysis, `gh`, web, PoCs
with no boot) run freely concurrent; **state-mutating** (writes data, installs an extension, mutates a
fixture) gets its own instance dir / fresh dataset and cleans up; **destructive / crash** gets its own
*disposable* sandbox it may wedge -- tell it the restart command and to run the control case first,
crash case last. This runtime-state isolation is distinct from git-worktree isolation for parallel
code *edits*; a hunt may need both.

Measuring against production is a trap of its own: "read-only" probes of the slowest reads once
used up a shared database's connections and locked real users out of logging in. That case and the safe procedure are in `oracles/performance.md`.

## A null result is not a negative finding

A shell `grep` that honors `.gitignore` will *silently* skip a gitignored applied-patch tree and hand
you a false "no callers / dead code." Verify absence against the real binary with explicit paths, and
check the probe could actually have shown the thing. Two live-probe variants of the same trap: a
**catch-all `200`** -- an SPA/static server (or a proxy) that returns `index.html` for *every* path,
so a `200` on `/api`, `/debug`, `/metrics` is not a live endpoint (confirm by diffing the body against
`/`; identical = catch-all). And a **misattributed fact** -- an env var, config line, or process
detail can belong to a *sibling container/service*, not the one under test; verify which unit a fact
came from before building on it.

## A live system proves presence and state, not design intent

Verify against a source that actually encodes the claim. A box answers "a host is at this IP", "this
service failed", "this module is loaded"; it does *not* answer "this CIDR is the staging subnet" or
"this box is meant to run this role" -- those live in an address plan, a runbook, or a person's
head. Probing the wrong source launders a guess into a stated fact that reads exactly as confident as
a checked one, and can overwrite a correct hedge with false precision (a real miss: an
honestly-hedged site CIDR, "verified" against DHCP-observed host IPs and generalized to the wrong
prefix -- the original hedge had been right). Before citing a probe as proof, ask whether that source
*encodes* the claim or just something correlated; if it's a design/intent/ownership question, the
authority is the human or the system-of-record -- hedge and ask, don't manufacture precision. The same
trap in **impact evidence**: a tracker ticket cited as proof a bug bites must be confirmed to sit on
the affected environment first -- a ticket from a network the code doesn't even run on refutes the
whole finding in one reply, and takes the credible code bug down with it.

## When environments are isolated, don't cross-cite impact evidence

Many systems run separate networks or estates (prod/staging, separate environments) with
different code paths, package sets, and infra. A bug reproduced in one is not evidence it exists in
another, and a support ticket from one environment can't justify a finding about a different one.
Prove the bug in the *same* environment the report targets, or scope the claim to the environment you
actually observed -- an off-environment citation is trivially refuted and wastes the maintainer's
time.
