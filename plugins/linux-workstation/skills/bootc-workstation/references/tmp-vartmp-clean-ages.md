# /tmp and /var/tmp clean ages: don't trust the vendor default

Measured on one workstation. The vendor defaults in `/usr/lib/tmpfiles.d/` are
`q /tmp … 10d` and `q /var/tmp … 30d`. Both halves turned out wrong here:
- **`/tmp` is cleared at 1 day, not 10** — `/etc/tmpfiles.d/tmp.conf` carries a local override
  (`D! /tmp … 0` plus `D /tmp … 1d`) that wins over the vendor file. Nothing at all in `/tmp` was
  older than 10 days.
- **`/var/tmp` had 58 entries older than 30 days**, the oldest from February — mostly
  `flatpak-cache-*`. The 30d line exists and is plainly not emptying it.

`systemd-tmpfiles-clean.timer` reads as `static`, which looks like "not enabled" and is not — it is
pulled in by `timers.target` and was `active (waiting)`, having last run three days earlier. So
neither "the timer is disabled" nor "the vendor age applies" is safe to assert. **Read
`/etc/tmpfiles.d/` before `/usr/lib/tmpfiles.d/`, and confirm with
`find /var/tmp -maxdepth 1 -mtime +30 | wc -l` rather than with the config.** A second host
reported the same claim not holding, by a different route — which is the signal
that the claim was about a distribution when it should have been about a host.
