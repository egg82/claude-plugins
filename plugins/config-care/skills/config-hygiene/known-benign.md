# Known-benign scanner hits

Keyed by skill name. `hygiene.py skills` counts dates, IPs, MACs and numbers **without understanding
them**, so a hit is a prompt to look, not a verdict. This file records the looks already taken.

**Recording a "looked at it, it's fine" is the whole point.** That verdict writes nothing anywhere else —
git records changes, a config records what is, neither records what was considered and rejected — so it is
the one conclusion guaranteed to be re-derived from scratch every sweep, sometimes to a different and
wrong answer.

Start your own rows. The generic ones below are worth inheriting, because they recur everywhere:

| Hit | Verdict |
|---|---|
| A **hard cap or protocol constant** (`200 lines`, `25KB`, a port, a threshold) | **Benign — keep it.** These do not drift with the world; they *are* the world. |
| A CIDR or address in a **translation table or example** rather than a host reference | **Benign.** Note the scanner scores anything outside RFC1918 as "public", so a documentation CIDR just above the private range gets double-weighted. Correct by its own rule, wrong as a finding. |
| A number measuring a **past incident** (`52 agents over three levels`, `9 of 25 never loaded the skill`) | **Benign — keep it.** The rot test is whether the world can contradict it. A measurement of current state can; a measurement of something that already happened cannot, and it is usually the entire evidence for the rule it sits beside. Distinct from a "validated on `<date>`" line, which *claims* present-tense currency and does rot. |

What is *not* benign, and the reason the check exists: a measurement of current state (an item count, a
"validated on <date>", a fleet size) inside a skill body. That is a finding from one run, and it belongs in
a companion data file beside the skill, not in the method.

| `verification-gate` — the ~84% false-positive / ~96% false-negative figures, and the "one variant" count | **Benign — keep them.** Measurements of a published past result, not of current state; the world cannot contradict them, and they are the entire evidence for the rule they sit beside. |
| `shell-footguns` (`references/probes-that-lie.md`) — the count in the loop-of-literal-matches entry | **Benign.** A count of past incidents that motivated the rule. |
