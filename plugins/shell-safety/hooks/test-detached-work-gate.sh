#!/usr/bin/env bash
# Cases for detached-work-gate.sh. Every rule needs a MUST-BLOCK and a MUST-ALLOW case, or the
# gate is only ever proven in one direction — and a gate that cannot be shown to stay quiet is the
# kind that gets switched off.
#
# Do not read a green `pass=N` as N independent proofs the gate works: only the must-BLOCK cases and
# the INERT case can tell a working gate from a dead one — every must-allow passes against a gate
# stubbed out to `exit 0`. To see which cases are load-bearing right now, run the suite against such
# a stub via the GATE override; whatever fails is the real coverage.
set -uo pipefail
GATE="${GATE:-$(dirname "$0")/detached-work-gate.sh}"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT
pass=0; fail=0

tu() {  # tu <name> <json-input>  -> one assistant tool_use transcript line
  printf '{"message":{"content":[{"type":"tool_use","name":"%s","input":%s}]}}\n' "$1" "$2"
}

# The gate's once-per-session stamp lives under $HOME, and its ONLY use of HOME is that stamp. So
# every invocation here runs with HOME pointed at a throwaway dir. Previously the suite instead did
# `rm -rf "$HOME/.claude/.detached-checked"` — which wiped the stamps of EVERY live session, so
# running the tests made the real gate re-nudge a session it had already nudged. A test must not
# mutate the state of the thing it is testing.
FAKEHOME="$TMP/home"; mkdir -p "$FAKEHOME/.claude"

run() {  # run <expect-rc> <label> <transcript-file>
  local want="$1" label="$2" tf="$3"
  local out rc
  out=$(printf '{"transcript_path":"%s","session_id":"t-%s"}' "$tf" "$RANDOM" \
        | HOME="$FAKEHOME" bash "$GATE" 2>&1); rc=$?
  if [ "$rc" -eq "$want" ]; then
    echo "  PASS  (rc=$rc) $label"; pass=$((pass+1))
  else
    echo "  FAIL  (rc=$rc, want $want) $label"; echo "        $out" | head -2; fail=$((fail+1))
  fi
}

echo "MUST BLOCK (rc=2) — detached real work, no waiter:"
f=$TMP/a.jsonl
tu Bash '{"command":"cd ~/project && nohup ./build.sh > /tmp/build.log 2>&1 &"}' > "$f"
run 2 "nohup a build, nothing armed" "$f"

f=$TMP/b.jsonl
tu Bash '{"command":"kubectl exec pod -- sh -c \"nohup /tmp/job.sh > /tmp/j.log 2>&1 &\""}' > "$f"
tu Read '{"file_path":"/tmp/x"}' >> "$f"
run 2 "nohup inside a pod, only unrelated tools after" "$f"

f=$TMP/c.jsonl
tu Bash '{"command":"setsid long-running-thing &"}' > "$f"
run 2 "setsid counts too" "$f"

echo "MUST ALLOW (rc=0) — a waiter exists, or it is fire-and-forget:"
f=$TMP/d.jsonl
tu Bash '{"command":"nohup ./longjob.sh > /tmp/longjob.log 2>&1 &"}' > "$f"
tu Monitor '{"command":"tail -f /tmp/longjob.log"}' >> "$f"
run 0 "Monitor armed after the detach" "$f"

f=$TMP/e.jsonl
tu Bash '{"command":"nohup ./longjob.sh > /tmp/longjob.log 2>&1 &"}' > "$f"
tu Bash '{"command":"until grep -q done /tmp/longjob.log; do sleep 30; done","run_in_background":true}' >> "$f"
run 0 "run_in_background waiter armed" "$f"

f=$TMP/g.jsonl
tu Bash '{"command":"nohup kubectl port-forward svc/example 18080:80 > /tmp/pf.log 2>&1 &"}' > "$f"
run 0 "port-forward is fire-and-forget, not a job" "$f"

f=$TMP/h.jsonl
tu Bash '{"command":"nohup ssh -N -L 5432:localhost:5432 dbhost &"}' > "$f"
run 0 "ssh tunnel likewise" "$f"

f=$TMP/i.jsonl
tu Bash '{"command":"ls -la && echo done 2>&1"}' > "$f"
run 0 "no detach at all" "$f"

f=$TMP/j.jsonl
tu Bash '{"command":"echo the word nohup appears in this doc text"}' > "$f"
tu Monitor '{"command":"x"}' >> "$f"
run 0 "waiter present even though nohup appears literally" "$f"

echo "A MENTION IS NOT A USE — the word inside a comment line:"
# The existing "appears literally" case above passes only because a waiter is ALSO present, so it
# never covered the literal-mention-with-no-waiter path. The second case is the one that matters:
# it proves the comment stripping does not open a hole under a real detach.
f=$TMP/n.jsonl
tu Bash '{"command":"cat > x.py <<EOF\n# nohup is the word this rule looks for, written into a source comment\nprint(1)\nEOF"}' > "$f"
run 0 "detach keyword only inside a COMMENT line, no waiter" "$f"

f=$TMP/o.jsonl
tu Bash '{"command":"# launching the long job below\nnohup ./longjob.sh > /tmp/b.log 2>&1 &"}' > "$f"
run 2 "a comment line must not mask a REAL detach beneath it" "$f"

# The real one, kept verbatim: this is the heredoc that actually tripped the gate, writing a
# findings DOCUMENT whose prose named the keyword. Comment-line stripping did not cover it.
f=$TMP/p.jsonl
tu Bash '{"command":"cat > FINDINGS.md <<EOF\n  the `nohup`-in-a-comment fix, four occurrences now\nEOF"}' > "$f"
run 0 "keyword in PROSE inside a heredoc, nothing backgrounded" "$f"

f=$TMP/q.jsonl
tu Bash '{"command":"nohup ./build.sh > /tmp/b.log 2>&1"}' > "$f"
run 0 "FOREGROUND nohup — the harness waits for it, so it is not the failure this gate catches" "$f"

f=$TMP/r.jsonl
tu Bash '{"command":"nohup kubectl port-forward svc/x 18080:80 &\nnohup ./longjob.sh > /tmp/b.log 2>&1 &"}' > "$f"
run 2 "a tunnel on one line must not mask a real detach on another" "$f"

# A line continuation is a LEXICAL artifact; the backgrounding predicate is a SEMANTIC claim. Per
# PHYSICAL line, the keyword sits on one line and the `&` on the next, so neither carries both and
# the gate goes silent on real detached work. Found in real traffic on both machines.
f=$TMP/s.jsonl
tu Bash '{"command":"nohup ffmpeg -hide_banner -f pulse -i default -t 30 \\\n  -af astats=metadata=1 \\\n  -f null - >/dev/null 2>&1 &"}' > "$f"
run 2 "a detach split across a line CONTINUATION is still a detach" "$f"

echo "MUST WARN (rc=1) — the gate cannot see anything, which is not the same as clean:"
f=$TMP/k.jsonl
printf '{"message":{"content":"plain string, no tool_use"}}\n' > "$f"
run 1 "no tool_use parsed -> reports itself INERT" "$f"

echo "LOOP SAFETY:"
f=$TMP/l.jsonl
tu Bash '{"command":"nohup ./longjob.sh &"}' > "$f"
printf '{"transcript_path":"%s","session_id":"loop","stop_hook_active":true}' "$f" \
  | HOME="$FAKEHOME" bash "$GATE" >/dev/null 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then echo "  PASS  (rc=0) stop_hook_active suppresses"; pass=$((pass+1))
else echo "  FAIL  (rc=$rc, want 0) stop_hook_active suppresses"; fail=$((fail+1)); fi

printf '{"transcript_path":"%s","session_id":"once"}' "$f" | HOME="$FAKEHOME" bash "$GATE" >/dev/null 2>&1
printf '{"transcript_path":"%s","session_id":"once"}' "$f" | HOME="$FAKEHOME" bash "$GATE" >/dev/null 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then echo "  PASS  (rc=0) second fire in same session suppressed"; pass=$((pass+1))
else echo "  FAIL  (rc=$rc, want 0) fires more than once"; fail=$((fail+1)); fi

echo "INERT BRANCH — 'no tool calls' is not the same as 'nothing parsed':"
# A brand-new session, or one that only ever answered in prose, legitimately has zero tool_use
# entries. Reporting INERT there fired falsely on a freshly-created peer session that had replied
# to a single "test" — a false alarm on the operator's screen, which is the cry-wolf failure this
# gate is otherwise careful to avoid. Only a transcript from which NOTHING parses is evidence of a
# dead parser, and that is the only case that may claim INERT.
printf '%s\n' '{"type":"assistant","message":{"role":"assistant","content":[{"type":"text","text":"hello"}]}}' > "$TMP/prose.jsonl"
printf 'not json at all\nstill not json\n' > "$TMP/garbage.jsonl"
run 0 "assistant turns but no tool calls -> silent" "$TMP/prose.jsonl"
run 1 "nothing parses at all -> INERT"              "$TMP/garbage.jsonl"

echo; echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]
