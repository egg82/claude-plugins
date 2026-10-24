# State-over-time oracles — run the clock forward

Load for anything whose state accrues: a game's progress, a subscription, a ledger, a scheduler, a database that has
been in production for years, a cache or log that is never pruned. These defects live in *sequences*, not lines, so
reading finds few. The oracle is simulated time through the real code: run months or years with a moving clock and
compare what happens with what was intended. Proof is the simulation script plus the day the wrong state appears.

## Simulated lifetimes — a behaviour matrix

Write a matrix of actor shapes — one actor doing one thing daily; bursts and long gaps; stopping early; many actors with
uneven effort; joining, leaving, rejoining — crossed with every ordinary action: create, rename, move between
categories, resize, retire, re-add, undo at each boundary, idle for a year. Simulate each row through the real code.
Measure paces against the intended ones; look for states progress never leaves (softlocks), counts the docs say only
grow going down, caps quietly spent by duplicates, content pools that run dry.

Deal finders out by *system*, each owning its system across every row, over one shared matrix file. Tell: a rule
evaluated against the *current* actors, or a value *fixed at a start* — a rate measured during the honeymoon, a
threshold never re-judged after someone leaves. *(incident)* On a long-running app, system finders over one matrix found
a sign-up path that 500'd for invited users, reminders scheduled but never sent, a fixed set of tips that began repeating
after about five months, and a savings goal sized from the busiest months that never completed once income slowed.

Keep the simulation fast — carry state forward rather than re-simulating from time zero for every sample (the usual
agent-made quadratic; `agentic-engineering` §6).

## Growth without a bound

- **Unbounded storage:** a table, log file, cache, queue or retry buffer with no retention. Ask what its size is after
  five years at today's rate, and what reads it scan. Anything not stdout needs a stated limit enforced by the code
  that writes it, with a test that past-limit rows go and in-limit ones stay.
- **Leaks over hours:** heap, file descriptors, goroutines or threads, listeners, timers, open connections. Run the
  process for an hour under a steady load and sample; a line that only goes up is the finding. A leak claim needs that
  curve — *(incident)* a "resource leak" two agents were confident in showed zero leaks over ~1,550 triggers with forced
  GC.
- **Counters and ids:** a 32-bit id or counter at today's rate, a sequence that wraps, a timestamp stored at a
  precision that collides.

## Accumulated data meets new code

- **Migrations against production's shape.** A migration tested on an empty database meets years of rows: legacy enum
  values the new constraint rejects, nulls in a column now `NOT NULL`, duplicates a new unique index refuses, a table
  rewrite that holds a lock for minutes. Run every pending migration against a restored copy of production
  (`performance.md` for taking one safely) and time it.
- **Old records through new readers.** Rows and files written by every past version must still load: a renamed field,
  a changed default, a format version the reader no longer knows. Keep one fixture per historical format, captured from
  real data, not authored.

## The calendar

Leap day, the last day of a month, a year boundary, DST in both directions, a week numbered 53, a user in a timezone
ahead of the server's, a "daily" job that runs on a 23- or 25-hour day. Advance a fake clock across each edge with the
simulation above rather than reasoning about them one at a time.
