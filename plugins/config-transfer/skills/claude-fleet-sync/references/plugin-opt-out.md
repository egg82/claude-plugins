# Opting one host out of a unioned plugin

Open this when a plugin misbehaves on only one host (typically a GUI-only plugin on the headless
host), or when `inventory`/`jsonmerge` shows an explicit `false` in `enabledPlugins`.

**A GUI-only plugin unions onto the headless host and breaks there.** `gitkraken-hooks`
registers **all eight** hook events pointing at an absolute flatpak path
(`~/.var/app/com.axosoft.GitKraken/…/gk`). That binary exists on the desktop hosts and
**never on the headless build host**, so every hook event there emitted
`gk: No such file or directory` — found in a scheduled job's logs, where
it had been failing unnoticed. Uniting `enabledPlugins` is what carries it across.

**Disable it in that host's `~/.claude/settings.json`** (`"<plugin>@<marketplace>": false`).
The union in `jsonmerge` now preserves an explicit `false` per host, so the opt-out survives
the next sync while new plugins still propagate normally.

**`claude plugin disable -s local` does NOT work here, and it reports that it did.** It writes
`enabledPlugins` into `~/.claude/settings.local.json` and `claude plugin list` then shows the
plugin as `✘ disabled` — but the runtime still loads and fires its hooks, because at user level
only `settings.json` is consulted for `enabledPlugins`. Measured on the headless host:
`plugin list` said disabled, and `claude -p "say hi"` still emitted the `gk: No such file or
directory` hook error. **`claude plugin list` is not a test of this — run `claude -p` and look
for the hook error.**
