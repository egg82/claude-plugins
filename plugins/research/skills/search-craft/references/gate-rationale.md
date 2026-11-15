# Why this skill is gated

**What routes you here:** `hooks/search-craft-gate.sh`, a PreToolUse gate on `WebSearch`. It blocks
the session's first search, and a fourth search taken without loading this skill, then stands aside.
It exists because an always-on memory pointing here was measured at **0 loads across 112 sessions in
30 days** — resident rent on every request for a trigger that never once fired. So if you are reading
this because a search was blocked, that is the mechanism working; extend the gate rather than adding
prose. The `search-read-the-failure` memory is kept as well, deliberately: the hook only covers runs
on a machine where it is installed.
