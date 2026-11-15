# When a diagram earns its place

Load when the PR changes control flow across several components and you are deciding whether to draw it.

Draw one only when the PR changes **control flow the reviewer would otherwise rebuild in their head
from several files**: new or reordered branches across three or more components, a retry or fallback
loop, a state machine, or two paths whose difference is the point (write vs read). Skip it for a change
inside one function, a straight sequence (a numbered list says it), a single decision, UI layout,
config, dependencies, renames, docs and test-only changes. If the flow fits in one sentence, write the
sentence. A diagram that restates the How bullets one for one is the commonest failure.

Draw **the behaviour this PR changes**, not the system. A Mermaid `flowchart TD`: plain rectangular
boxes with short verb-led labels, conditions on the edges, the real branches and loops and no invented
ones. Put independent paths side by side (`subgraph`) when comparing them is the point. Put it under a
`## Diagram` heading after `## How`, with one sentence first on what the reviewer should notice.

**Render it and look at it before publishing**, because Mermaid silently produces unreadable layouts:

```bash
podman run --rm -v "$dir":/data:Z ghcr.io/mermaid-js/mermaid-cli/mermaid-cli:11.4.2 \
  -i /data/flow.mmd -o /data/flow.png -b white
```

(`$dir` must be writable by the container user; `chmod 777` a scratch dir. Use `mmdc` directly where
it is installed.) Then Read the PNG and check labels, clipping and that it matches the final code.

**Embedding:** GitHub and GitLab both render a ` ```mermaid ` block in descriptions. Use that by
default; it stays editable and needs no upload. Upload the PNG only when readers mostly see the PR
somewhere that won't render it (email notifications, some mobile apps). Never send private architecture
to a public diagram-rendering service; render locally.
