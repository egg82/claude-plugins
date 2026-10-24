---
name: repo-orient
description: "Orient yourself in an unfamiliar repository fast — a triage map of which few files are load-bearing, which are padding or generated, where the real logic and surprises live, and the architecture in one picture. Use before contributing to, modifying or deeply understanding an unfamiliar or LLM-bloated codebase. NOT trust/adopt decisions (repo-vet)."
---

# Orient fast in an unfamiliar repo

You are going to **change or deeply understand** this code. You need the mental model and a map of
where the load-bearing parts are, fast -- so your reading goes where it matters instead of wading
through everything at uniform density. The output is a **map that directs your reading**, not a
summary that replaces it. Distinct from `/init` (agent manual) and a generic summarizer.

## Coverage is the product (non-negotiable)

The failure mode is reading a handful of files and generalizing to the whole repo -- a triage map
that anchors will miss the one file that was the point. So traversal is **deterministic, not a
judgment call** -- but tiered, so it scales:

- Enumerate the full file list first (`git ls-files`), don't eyeball a sample.
- **Classify every file cheaply** (path, size, a glance) into load-bearing / boilerplate /
  generated / vendored -- so nothing is silently skipped. Fan out one reader per chunk (parallel
  subagents, or the Workflow tool) on a big repo; `fanout-craft` for the briefs.
- **Deep-read only the load-bearing set;** whole buckets (generated, vendored, boilerplate) are
  covered *as buckets*, not file-by-file.
- Coverage is of the **input, not the output**: you classified everything, but the map stays short --
  it names the files to read and buckets the rest ("everything under `vendor/`: skip"), never a
  400-line inventory. If an area went uncovered, say so.

## The pass

1. **50k-foot** -- what the repo is, its module/component boundaries, the data/build flow, and the
   build/run/test entry points. One picture before any file list.
2. **Rank by load-bearing-ness** -- separate the core logic, the real extension points, and the
   config that actually drives behavior from generated code, vendored deps, boilerplate, and
   padding. Rank by information density, not line count.
3. **The map** -- "read these N first (and why)", "skim these", "skip these (generated/boilerplate)",
   and where the **signal-spikes** are (the clever bit, the load-bearing function, the surprising
   coupling).

## Output

A lean reading map, ordered by where to spend attention. It **directs** the human to ground truth;
they still read the load-bearing files themselves -- don't let the map become the thing they trust
instead of the code (bound claims to what you covered). And keep the map itself short: if reading
the map costs as much as reading the repo, it failed its one job.
