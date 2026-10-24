# Case files

These are the repositories the method was distilled from. Names and domains are generalized and most
details and figures altered, so treat every number as indicative. Each is a lead, not a citation.

## Repo A (an agent-built app): the repo that learned it the hard way

Repo A has hundreds of commits from a couple of weeks of agent work and was still mid-rewrite to these rules, so check its
open-work list before copying one of its files as an example.

- **House rule plus an immediate split:** the small-files rule was added, then the entry-point file went from
  several hundred lines to a handful, and two JS files were split the same evening. Late exception: a
  generator script grew past a thousand lines and was split byte-identically into a package (its baked
  output files hashing the same).
- **Re-plan instead of patching:** about a dozen patches to one pricing-rules module, then a decision to
  write a second rules engine rather than patch a thirteenth time. The old module was deleted, and its bug
  detectors became the new engine's acceptance tests.
- **Held ledgers:** a held-ledger helper, a function-size test, a held-SQL test, a pyright gate and a
  boundaries test. A planted swap showed that a global count could be gamed.
- **Never raise a held count:** agents raised them twice.
- **Word-matching gates over prose:** an audit found dozens of them, and they were banned in CLAUDE.md.
- **Null Object hid missing wiring.**
- **Findings-first bug hunts:** a strict xfail, then the fix.
- **Fix chains that ended in deletion:** two features whose repeated fixes ended with the feature removed.
- **Weak self-written tests:** about thirty surviving mutants; a blind property test found an undo bug.
- **Rates in code, not prompts:** an LLM drafting customer follow-up emails was told in prose how often to offer
  a discount; the choice moved to a seeded roll with its rate in a config file, and each prompt now states whether
  this email gets one.

## Repo B (a spreadsheet-import tool): the rules applied from the first line

Repo B has a few hundred commits from about three days. Its engineering doc is the distilled rulebook, framed as a
list of things repo A had done the other way first and then had to reverse. Its CLAUDE.md is 31 lines.

- Gates: a function-size test (60 lines, an empty held list), a conftest time gate (a 1.5-second per-test
  ceiling), and an engine purity test (the core package imports only stdlib and itself, with 9 planted bad
  imports).
- Staged agent work: interface first, then an implementer and a blind contract-test writer in separate
  worktrees, with gap and question files settled in a design doc. A mutants file records the planted
  wrong implementations. What this showed: the parsers suite logged 17 contract gaps before
  integration, and planted mutants drove eight new tests. **It was never compared against one agent doing
  everything.** The planned "who implements" experiment (two implementers given the designer's
  rationale against two given the interface alone) was deferred twice and never produced a result.
  Don't cite this setup as measured.
- A suite that silently stopped collecting: about 90 contract tests.
- A scripted run is a lower bound: a test script cleared the import wizard in 9 s against about two minutes for
  first-time users.
- **Patterns planned but not built:** the locator, event queue, observer and double buffer. Command,
  Type Object and a small state machine were built.

## An existing repo, reviewed MR by MR

One agent-built app was reworked overnight by an orchestrating session, with every MR reviewed
against this skill.

- **Ledgers emptied:** over-long functions, over-long files and the pyright errors all went to 0
  under held gates. No count was ever raised.
- **Untested code found by pinning before splitting:** the verdict functions killed few of their
  planted mutants (one function 1 of 30, five others 23 of 73). A guard that stops a bad fetch from
  mass-deleting records had no test at all.
- **A split that passed as structure and failed as design:** a byte-identical JS split turned
  one closure's state into a 30-field object written from 10 of 15 files. The owner that followed
  was mostly per-field setters, and one generic `set(key, value)` bypassed its own gate.
  A test-time Proxy then caught writes through aliases, and adopting setter arguments
  found a render function writing into stored state.
- **Measurement scope is part of the claim:** a review count of "40 single-use exported members"
  scanned only one directory and missed the re-export through a `window.*` global. Only 6 were dead.
- **Ledger gaming without a raise:** an agent appended a needed `ORDER BY` in Python to avoid
  spending one line of a held SQL file. The orchestrator sent it back.
- **A cast that removed a safety check:** `cast(LiteralString, f"…")` silenced pyright by
  switching off psycopg's SQL-injection guard. It was replaced by `LiteralString` fragments plus a bind
  parameter.
- **Name-matched security rules are bypassable:** probing a read-only SQL check found an aliased import,
  `getattr` with a constant, and a bound method each writing past it. The fix resolves imports per file.

## A hand-written Java service: the human baseline

A Java service built mostly by hand with a little browser chat help, and the decoupling is sound:
an abstract updater (a template method), interfaces in an API module with `*Impl` classes in an app
module (one-way `Lib ← API ← App/Webhook`), cancellable pre/post events on a bus, a Null Object API
instance, and a plugin `URLClassLoader`. **Its gaps are tests (none) and duplication across services:**
two updaters are 199-line copies that differ only in an enum argument and log wording, and `Main` has
five near-identical `setupX` methods. The interface-first API makes blind contract tests cheap there.
