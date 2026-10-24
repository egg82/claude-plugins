# Pre-registered claim taxonomy — TEMPLATE

A worked example over an invented Java parsing package (`com.example.parse` — the class names, line
numbers and symptoms below are fictional filler), to show the shape. Copy it and replace the claims
with yours; the section structure and the scoring table are the reusable part.

Written **before** the A/B results were seen, so grading can't be rationalized after the fact. Derived
from the bug-hunt runs already completed (a couple per model, across the models under test).

**Grade findings by CLAIM, not by `file:line`.** The previous analysis compared extracted citations and
concluded Fable had found two unique defects; it hadn't — both were reported by opus and sonnet as prose
against an already-cited line. Counting pointers measures formatting, not coverage.

Two findings are the same claim when they describe the same defective behaviour, even if they cite
different lines, different files in the same call chain, or no line at all.

Each entry needs four parts and nothing more: an id + short slug, the pointer(s), what the defective
behaviour is, and **how the status was established** — hand-derivation, execution, or neither.

---

## Real defects (the coverage denominator)

**C1 · guard-always-true** — `WidgetParser.java:100` and `:104`
Two guards test a value that is constant by construction rather than the one that varies, so both are
always true and the error branch below them is unreachable. Downstream arithmetic then consumes a
sentinel as if it were data.
*Status:* **verified**, by hand-derivation and by execution — an ordinary well-formed input produces a
nonsensical negative total.
*Counts as C1 even if only the wrong-output symptom is described without naming the constant guard.*

**C2 · field-order-inverted** — `WidgetParser.java:96-108`
The captured fields are assigned to units in the wrong order, so conventionally-ordered input maps to
the wrong units.
*Status:* **verified** by execution — a four-field input round-trips with two units transposed.
*Distinct from C1: fixing the guards leaves this wrong.*

**C3 · accessor-throws** — `GadgetParser.java:200`
The value accessor raises an unchecked `FrobnicationException` for one input shape (a container where a
scalar was expected), breaking the never-throw/return-default contract every sibling parser funnels
through.
*Status:* **verified** by execution against the project's pinned dependency stack.

**C4 · silent-flag-not-forwarded** — `GizmoParser.java:300`, `DoodadParser.java:305,310`, `WidgetParser.java:120`
The 2-arg convenience overload of `ValueHelper.readLong/readInt` hardcodes the quiet flag to false, so
a caller that asked for silence still gets a WARN plus stack trace on bad input.
*Status:* **verified** by execution.

**C5 · negative-cache-never-populates** — `ThingumParser.java:400`
The memoizing call used to build the cache records nothing when the mapping function yields no value, so
the intended negative-result cache never caches; the expensive lookup and its ERROR log repeat on every
call.
*Status:* **verified** by execution.

---

## Known non-findings (report these and it's a false positive)

**N1 · wrong-receiver-emptiness-check** — `GadgetParser.java:196` tests emptiness on the container where
its siblings test the key. A real inconsistency, **behaviourally harmless** — the lookup returns false
for the empty key either way.
*A run that reports this as a defect scores a false positive. A run that names it and correctly
dismisses it scores a kill, which is a positive signal.*

## Unresolved (score separately; neither credit nor penalty)

**U1 · case-sensitive-unit-match** — `GizmoParser.java:308`, the unit dispatch is case-sensitive, so an
upper-case unit suffix is rejected. Claimed once, never executed by anyone.

**U2 · host-default-timezone** — `ThingumParser.java:404` resolves against the host's default timezone,
making date-only parses machine-dependent. Raised once with the trigger explicitly unconfirmed.

---

## Scoring per run

| metric | definition |
|---|---|
| coverage | how many of C1–C5 the run reports |
| false positives | N1 reported as a real defect, or any claim not in C1–C5/U1–U2 that doesn't hold |
| kills | non-findings explicitly checked and dismissed |
| executed | did the run actually run code and report observed output, or only reason |

**The hypothesis under test:** BRIEF_B (execute required) raises coverage and/or kills relative to
BRIEF_A (unconstrained), holding the model fixed. If it doesn't, the execution difference seen earlier
was model choice or luck, not the brief.
