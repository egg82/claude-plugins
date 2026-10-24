---
name: log-what-happened
description: Services, jobs and CronJobs the user runs must log what they did to stdout (Loki + Alloy collect it), not only HTTP access lines
metadata:
  type: feedback
---

The user runs Loki and Alloy on their clusters, so a pod's stdout is the history they go back to when something broke. The user's
ask: unattended jobs and containers should log what happened, for failures and bugs, because the only
pod logs were request lines; and logging should improve wherever it is needed, not just in pods.

**How to apply**, when building or touching anything that runs unattended (a CronJob, a worker, a sync, a script on a
timer, an init container):
- Log each run's start and finish with counts and duration, and every failure with its traceback — especially the
  ones the code deliberately swallows (a fallback taken, a cache treated as a miss, a retry): those are what you want
  afterwards, and they are silent by design.
- One line per event, `key=value` (logfmt) so Loki filters on fields without a parser; drop health-probe noise from
  access logs.
- Ids, counts, kinds, durations and status codes — never secrets, tokens, raw client addresses or other people's
  content (a hashed prefix where a key must be told apart). Same rule as [[print-names-not-values]].
- A job whose log is empty after a run is a defect to fix, not a quiet success.
- **Stdout is one home of three; pick by who reads it back** (file and database logs exist too; use each
  where appropriate): stdout → Loki for operational events; a **database** table for records the app itself reads or
  that must outlive log retention and be queried (job run history shown in an admin page, a security audit trail,
  spend); a persistent **file** for local tools and timers nothing collects (never `/tmp`, which a reboot empties).
- **Anything not stdout/stderr gets rotation and retention when it's built**, to avoid ballooning: a stated
  limit (age and/or size), enforced by the code that writes it rather than a separate cron, with a test that past-limit
  rows/files go and in-limit ones stay. Logs are pruned; earned history (a game's taps, a ledger) is not a log.
