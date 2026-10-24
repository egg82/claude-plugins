#!/usr/bin/env bash
# hook-version: 3   # bump on any behaviour change
# PreToolUse(Agent): refuse a spawn that does not name a model, and refuse a Fable tree.
#
# WHY: omitting `model` is a decision that does not feel like one. The spawn silently INHERITS the
# caller's model, costs nothing extra at the call site, and the consequence shows up only on a bill.
# Measured elsewhere: a 14-agent fan-out with `model` omitted on every call, all inheriting Opus —
# $227 and a 5-hour cap, with 98% of the spend attributed to subagents. Most of those agents were
# bounded single-source work that Sonnet clears at 94% of Opus's pass rate.
#
# The Fable case is the same failure with a worse multiplier. Fable-as-lead earns its 2x price only
# when the workers are cheaper — Anthropic's split benchmark puts Fable-lead + Sonnet-workers at 96%
# of all-Fable quality for 46% of the cost. Reported in the wild: a planned 8-agent review became 41
# Fable verifiers. Measured here: one Fable bug-hunt leaf cost ~$30 against haiku's ~$1 for the same
# task. So a Fable caller may not spawn Fable even when it names it explicitly.
#
# WHY A HOOK AND NOT THE SKILL: `fanout-craft` §1 is titled "Choose the model per agent" and carries
# the measured cost table. It was resident, loaded, and named by the memory that authorises fan-out —
# and the omission happened anyway, fourteen times in one session. Prose that has already failed does
# not get another chance; it gets a check the harness runs.
#
# THE RULES, in order:
#   1. not an Agent call                                  -> allow
#   2. subagent_type "fork"                               -> allow (a fork ignores `model` by design,
#                                                            so the rule cannot be satisfied)
#   3a. `opus` named without an `[opus: <why>]` in the    -> BLOCK (a subagent's cost is decided
#       prompt                                                 at the call site; make it deliberate)
#   3b. any other non-Fable model named explicitly       -> allow
#   4. `fable` named AND the caller is Fable              -> BLOCK
#   5. `fable` named and the caller is not Fable          -> allow
#   6. `model` omitted but the agent definition sets one  -> allow (the definition IS the choice)
#   7. `model` omitted                                    -> BLOCK
#
# FAILS OPEN throughout. An unparseable payload, an unreadable agent definition, or a caller model
# that cannot be determined allows the spawn — a cost control must never block real work on missing
# bookkeeping.
set -uo pipefail

payload=$(cat 2>/dev/null || true)
[ -n "$payload" ] || exit 0

HOOK_PAYLOAD="$payload" python3 - <<'PY'
import glob, json, os, re, sys

try:
    d = json.loads(os.environ["HOOK_PAYLOAD"])
except Exception:
    sys.exit(0)                      # fails open

if (d.get("tool_name") or "") != "Agent":
    sys.exit(0)                      # rule 1

ti = d.get("tool_input") or {}
model = (ti.get("model") or "").strip()
atype = (ti.get("subagent_type") or "").strip()

# Rule 2. A fork always inherits the parent and the override is ignored by design.
if atype == "fork":
    sys.exit(0)


def caller_is_fable():
    """True / False / None — None means undeterminable, which fails open."""
    agent_id = d.get("agent_id")
    if agent_id:
        for m in glob.glob(os.path.expanduser(
                f"~/.claude/projects/*/*/subagents/agent-{agent_id}.meta.json")):
            try:
                # A sidecar that records no model at all is UNDETERMINABLE, not "not fable".
                # Measured on this machine: only 50 of 375 sidecars carry a `model` key, so
                # collapsing the absent case to False would state a certainty this has not got.
                # Both answers currently fail open, but the docstring promises three states — and
                # the next rule to test the other branch inherits the lie.
                recorded = json.load(open(m)).get("model")
                return "fable" in recorded.lower() if recorded else None
            except Exception:
                return None
        return None
    # Root session: read the model off the most recent assistant turn in its transcript.
    tp = d.get("transcript_path") or ""
    if not (tp.endswith(".jsonl") and os.path.exists(tp)):
        return None
    try:
        with open(tp, errors="replace") as f:
            tail = f.readlines()[-400:]
    except OSError:
        return None
    for line in reversed(tail):
        if '"model"' not in line:
            continue
        try:
            rec = json.loads(line)
        except Exception:
            continue
        name = ((rec.get("message") or {}).get("model") or "")
        if name:
            return "fable" in name.lower()
    return None


if model:
    m = model.lower()
    # Rule 3a. Opus for a SUBAGENT has to be a stated choice, not merely a named model.
    #
    # THE RULE IS PERMANENT; THE NUMBERS ARE NOT, AND THEY ARE NOT KEPT HERE. This gate exists to
    # change the very distribution that motivated it, so any share-of-spend figure written into it
    # is one the gate is actively trying to falsify. A stale figure in an enforcement file is worse
    # than none: a reader either believes it or stops trusting the gate. The dated measurement and
    # the command that regenerates it belong beside the skill that owns model choice —
    # `fanout-craft` (record your own; none ships).
    #
    # What does not rot, and is the actual reason for the rule:
    #   - a subagent pays for its own context on every one of its requests, so the cost of a spawn
    #     is set at the call site and shows up nowhere near it;
    #   - `fanout-craft` §1 measures sonnet at 94% of opus's pass rate on BOUNDED single-source
    #     work — one file, one directory, a fixture to debug, a plan drafted from supplied context —
    #     which describes most of what gets delegated;
    #   - opus earns its rate on cross-source aggregation, open-ended search, and adversarial
    #     review, where the agent itself must decide what "done" means.
    #
    # A command string cannot tell those apart, so this does not try. It asks the caller to say
    # which it is, via a token in the prompt. That costs one edit and leaves a greppable audit trail.
    if "opus" in m and "[opus:" not in (ti.get("prompt") or "").lower():
        sys.stderr.write(
            "Blocked by spawn-model-gate: this spawn asks for `opus`, which needs a stated reason.\n\n"
            "A subagent pays for its own context on every request it makes, so the cost of this\n"
            "spawn is decided here and surfaces nowhere near here. Where measured, opus subagents\n"
            "have been the largest single line of usage by a wide margin; record your\n"
            "own figures beside `fanout-craft`.\n\n"
            "For BOUNDED single-source work — one file, one directory, a fixture to debug, a plan\n"
            "drafted from context you supplied — `fanout-craft` §1 measures sonnet at 94% of opus's\n"
            "pass rate for about a third of the cost. That describes most delegated work.\n\n"
            "So either:\n"
            "  - switch to `model: 'sonnet'` (or `haiku` for mechanical, well-specified work), or\n"
            "  - keep opus and put the reason in the prompt as `[opus: <why>]` — genuine cases are\n"
            "    cross-source aggregation, open-ended search, and adversarial review, where the\n"
            "    agent itself has to decide what \"done\" means.\n")
        sys.exit(2)
    # Rule 3b. Any other explicitly-named non-Fable worker is exactly the shape we want.
    if "fable" not in m:
        sys.exit(0)
    # Rules 4/5. Naming Fable is only a problem when the caller is already Fable — that is the
    # tree that compounds. A non-Fable lead deliberately reaching for Fable is a real choice.
    if caller_is_fable() is not True:
        sys.exit(0)
    sys.stderr.write(
        "Blocked by spawn-model-gate: you are running on Fable and this spawn names `fable`, so it\n"
        "would build a Fable tree.\n\n"
        "Fable-as-lead is worth its 2x price only when the workers are cheaper: Anthropic's own split\n"
        "benchmark puts Fable-lead + Sonnet-workers at 96% of all-Fable quality for 46% of the cost.\n"
        "One measured Fable leaf here cost ~$30 against ~$1 on haiku for the same task.\n\n"
        "Keep the planning, verification and synthesis on Fable; delegate the reading to a cheaper\n"
        "worker — `sonnet` unless you have a reason not to.\n")
    sys.exit(2)

# Rule 6. An agent definition may set the model itself, which IS a deliberate choice.
if atype:
    for root in (os.path.expanduser("~/.claude/agents"), ".claude/agents"):
        for p in glob.glob(os.path.join(root, f"{atype}.md")):
            try:
                head = open(p, errors="replace").read(4000)
            except OSError:
                sys.exit(0)          # cannot read the definition -> fail open
            if re.search(r"^model:\s*\S+", head, re.M):
                sys.exit(0)

# Rule 7. Omitted. Blocked either way; the Fable caller gets the sharper message.
label = atype or "general-purpose"
if caller_is_fable() is True:
    sys.stderr.write(
        f"Blocked by spawn-model-gate: this Agent call ({label}) omits `model`, and you are running\n"
        "on Fable — so the child would INHERIT Fable and build a Fable tree.\n\n"
        "Fable-lead + cheaper workers is the shape that pays: 96% of all-Fable quality for 46% of the\n"
        "cost. A Fable tree is the expensive failure — one measured leaf cost ~$30 against ~$1 on haiku.\n\n"
        "Set `model` explicitly: `sonnet` for bounded single-source work, `haiku` for mechanical\n"
        "well-specified work, `opus` when the worker itself must decide what \"done\" means.\n")
else:
    sys.stderr.write(
        f"Blocked by spawn-model-gate — this Agent call ({label}) does not name a `model`, so it "
        "inherits this session's.\n\n"
        "Inheriting is the failure mode, not a default: it is free at the call site and only shows up "
        "on a bill. One session spawned 14 agents with `model` omitted on every call, all inherited "
        "Opus, and it cost $227 against a 5-hour cap.\n\n"
        "Pick one, from `fanout-craft` §1 (tables in its references/model-choice-evidence.md):\n"
        "  model: 'sonnet'  — bounded single-source work: one file, one directory, one repo, a fixture\n"
        "                     to debug, a judgment call with the context supplied. 94% of opus's rate.\n"
        "  model: 'haiku'   — mechanical and well-specified: a rename sweep, a literal-match check.\n"
        "  model: 'opus'    — aggregation ACROSS many sources, open-ended search, adversarial review.\n"
        "                     This is a pass: the gate wants a deliberate choice, not a cheap one.\n\n"
        "Re-issue the call with `model` set. A fork, or an agent type whose own definition sets a "
        "model, is exempt and will not reach this message.\n")
sys.exit(2)
PY
rc=$?
[ "$rc" -eq 2 ] && exit 2
exit 0
