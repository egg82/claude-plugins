---
name: headless-browser-in-a-container
description: Render HTML and LOOK at it before calling it done — and if this host has no browser, a headless one is a container run away — load the headless-render skill before calling any HTML work done
metadata:
  type: feedback
---

**When work produces HTML a human will look at, render it and look at it before calling it done** —
"the logic is verified" has missed defects a glance caught. "No browser on this host" is not a
stopping point: absence from `PATH` bounds what is installed, not what is reachable.

**Before any visual claim from an automated live browser, assert `document.visibilityState ===
"visible"`.** A backgrounded tab stops `requestAnimationFrame`, so canvas/WebGL/maps/charts silently
stop drawing while screenshots still return — this produced a published false defect report once.
Prefer a container render for anything about rendering; keep the live browser for interaction,
console and network.

**Load the `headless-render` skill for the method.**
