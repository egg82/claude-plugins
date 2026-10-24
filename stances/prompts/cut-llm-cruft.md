# Prompt: scan a repo and cut LLM cruft

Paste into a fresh Claude Code session opened in the target repo. (The global memories
`prefer-subtraction` + `verify-dont-anchor` already tilt it this way; this spells out the
coverage / verify-before-cut / propose-don't-delete guarantees explicitly for safety.)

---

Scan this **entire** repo for LLM-generated cruft that'll be a maintenance burden -- over-engineered
abstractions with one caller, redundant guardrails/fallbacks for cases already handled, dead
code/config/flags, duplicated or stale docs, and ceremony (ADRs/comments that restate the obvious).
**Enumerate the whole tree (`git ls-files`)** so you cover it, not a sample. For each candidate,
**verify it's genuinely safe to remove** -- grep for references, run the repo's linters/dead-code
tools, check the tests -- *before* proposing it. Give me a **ranked list, highest-confidence
first**: what to cut, why it's safe, what's lost if anything. **Propose only; don't delete until I
approve.**
