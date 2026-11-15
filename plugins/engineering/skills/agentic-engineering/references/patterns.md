# Patterns, by fit

Load when a fit pass turns up a candidate pattern, when decoupling a shared system, or before proposing a new abstraction.
(SKILL.md §4.)

GoF and Nystrom's *Game Programming Patterns* (read the chapter, not a summary) apply far beyond games.
**Judging the fit matters more than the pattern.** Repo B planned a service locator, event queue,
observer and double buffer, and built none of them. It built Command, Type Object and a small state
machine, because those were what the work needed.

- **Command** for user actions: frozen records in one closed union behind one `decide()`. Replay,
  logging and automation come free.
- **Type Object and data files** for content: a new kind is data, not a class.
- **Service locator only for real systems** (sound, map, clock, catalogue), each behind one interface
  with a Null Object default; callers go through the locator and never import the implementation.
  **Every entry point must wire it, deploy checks and tools included.** A Null Object silently turns
  missing wiring into plausible wrong answers (repo A's deploy check reported failures the live app
  doesn't have).
- **Queues and double buffers** to decouple a producer from its consumers, worker pools draining a queue
  included. Leaf helpers stay plain imports.
- **Replace shape-sniffing with explicit fields** (Type Object or Specification). A frozen record with
  `source`/`kind`/`part` let a dozen code paths merge into one owner.
- **State that is a function of history plus a date** stays a pure query passed in, not a global
  service.
- **Template method plus per-variant strategy (an abstract updater class) needs a second extraction
  once variants converge.** Two 199-line updaters that differ in one enum argument should be one generic
  base.
- **Don't:** singletons or module globals for shared systems; god objects, or one object's fields shared
  across many mixins (that's coupling spread out, not decoupling); inheritance trees for content kinds.
- **Record rejected patterns with the reason**, and the "looked at, and fine" verdicts, so the next agent
  doesn't propose them again.
