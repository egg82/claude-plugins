# Shell traps when scripting the remote side

Open this before writing any loop or script that runs on peers (deleting zombies, batch fetches).

The project directories are named for the encoded path (`-home-user-proj`), so they **begin
with a hyphen** — `rm -f "-home-.../file"` makes `rm` parse the name as an option bundle and fail,
while `[ -f ... ]` on the same string succeeds. A naive loop then reports deletions that never
happened. Always use absolute paths or `--`, and check the exit status rather than counting attempts.
Likewise, `ssh` inside a `while read` loop consumes the loop's stdin (use a single batched script),
and `ssh -n` cannot be combined with feeding a script on stdin.
