# Traps that keep biting — promoting prose to a gate

Load when the SessionStart line from `mine-repeat-traps.py` appears, or when deciding where a
recurring trap should be enforced.

```
python3 mine-repeat-traps.py
```

`mine-repeat-traps.py` answers a question the other checks cannot: **which lessons are already
written down and still being hit?** A trap that recurs after being documented is proof the prose is
not working, and the fix is never to write it again more emphatically.

It runs weekly from the SessionStart hook (`--quiet`, one line, silent when clean) because a finding
that only lands in a log nobody opens does not exist. Run it in full when the line appears.

It reads the assistant's own admissions ("my probe was wrong", "clobbered", "same shape as"), NOT
error strings — deliberately, because the costliest failures here exit 0 and print nothing. An import
that adopted a downloaded file onto the wrong record and deleted the one already there produced no error at all; its
only symptom was a file size that looked wrong. Counts are therefore a **ranking signal, not a
measurement**: the miner only sees mistakes that were noticed and named.

It also reports **gate friction** — a gate blocking repeatedly across many sessions. This exists
because a gate block is a mistake the assistant never *admits*: being stopped by your own gate does
not feel like an error, you reissue and move on, so the admission-phrase list can never see it. A
block does leave a distinctive string in the transcript, and one gate turned out to have fired
dozens of times across many sessions with nobody looking. Read it as
"go look", not as a fault — a rule tripping constantly may be catching real bugs, or may be firing on
a shape nobody meant to write.

**The blind spot that remains is aggregation across sources, and it is not this tool's job.** The
miner reads *this* machine's transcripts, and that is the right scope: cross-domain evidence arrives
irregularly, as prose, in a hand-carried transfer, and building awareness of it into a scheduled
transcript miner would couple a routine check to a one-off event. **That cross-check belongs in
`claude-config-import`**, which is the skill that owns the crossing. What the miner cannot do — and
no automation here should pretend to — is notice that two occurrences reported by the sender plus
one local hit make three. That addition is a judgement call at import time.

## Routing what it surfaces

Judgement, and stays manual. This is the trap-specific form of the routing question in
`knowledge-organization.md`:

| the trap can be… | goes to |
|---|---|
| proven from the command string alone, no legitimate false positive | `bash-footgun-gate.sh` + a must-block AND must-allow case in `shell-footguns/test-gate.sh` |
| recognised only with task context | the owning skill, beside the procedure it breaks |
| about how work should be done at all | global memory |
| detected in live state after the fact | a check in the thing that already runs (a matcher pass, a cron report) |

The bar for the gate is both conditions, not either: frequent AND statically provable. A gate with
false positives gets switched off, which is strictly worse than the prose it replaced.
