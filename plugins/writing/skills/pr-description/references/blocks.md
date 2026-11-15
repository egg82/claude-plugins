# Blocks: when each earns its place

Load when a description might want a table, snippet, quoted output, `<details>` or checklist.

| Block | Use when | Skip when |
|---|---|---|
| Table | comparing before/after measurements, or options against a benchmark | there is one number (say it in the sentence) |
| Code snippet | the reader needs a new API shape, config key or command | it restates the diff |
| Quoted output | one or two lines are the evidence for a claim in Verified | it is a log dump |
| `<details>` | bulk the reader may want but needn't read: a long log, generated output, a group of screenshots, with a visible summary line above it | it would hide the why, the risk or the after-merge step |
| Checklist | the repo's template has one | never add one yourself. An author ticks their own boxes without reading them; a step that must happen goes under **After merge** as a sentence |
| Screenshots / recording | a visible change; see `screenshots.md` | the change isn't visible |
| Diagram | the test in `diagrams.md` passes | almost always |

Keep blank lines after `</summary>` and before `</details>`, or the Markdown inside won't render.
