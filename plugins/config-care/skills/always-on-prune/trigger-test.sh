#!/usr/bin/env bash
# Does a skill's description still make a fresh session load it?
#
# Usage: trigger-test.sh <prompts.jsonl> <outdir>
#   prompts.jsonl: one {"skill": "<name>", "prompt": "<how the user would actually say it>"} per line
#   env: MAXT=<max turns, default 2>   FIXTURE=<dir to run in, default a fresh empty dir per prompt>
#
# Each prompt runs in a new headless session with the action tools disallowed, so nothing executes
# and the only move left is to pick a skill. Prints HIT/MISS per line and appends to <outdir>/summary.tsv.
#
# Validate it before believing it: run one prompt that must hit and one that must not ("what is 17
# times 23?"). Three traps it was built through:
#   - `claude -p` reads stdin, so inside `while read` it eats the rest of the prompt file and a later
#     session answers an earlier prompt. Hence `< /dev/null`.
#   - `--allowedTools` does not restrict when settings.json already allows Bash; the session ran real
#     commands instead of choosing a skill. Hence `--disallowedTools`.
#   - A prompt that presumes a repo ("add tests to this script") gives up in an empty dir before it picks
#     a skill. Run those with FIXTURE pointing at a small fake repo. Then compare a MISS against the
#     pre-change description before calling it a regression.
# Each run leaves an empty project dir under ~/.claude/projects/-tmp-*; clear those afterwards.
set -u
export PATH="$HOME/.local/bin:$PATH"
IN=$1; OUT=$2; mkdir -p "$OUT"
CWD=$(mktemp -d)
i=0
while IFS= read -r line; do
  i=$((i+1))
  skill=$(printf '%s' "$line" | python3 -c 'import json,sys;print(json.load(sys.stdin)["skill"])')
  prompt=$(printf '%s' "$line" | python3 -c 'import json,sys;print(json.load(sys.stdin)["prompt"])')
  f="$OUT/$(printf '%02d' $i)-$skill.jsonl"
  RUNDIR=${FIXTURE:-$(mktemp -d -p "$CWD")}
  (cd "$RUNDIR" && timeout 240 claude -p --output-format stream-json --verbose --max-turns "${MAXT:-2}" \
      --disallowedTools Bash Edit Write NotebookEdit WebFetch WebSearch Agent Workflow \
      -- "$prompt" > "$f" 2>/dev/null < /dev/null)
  loaded=$(python3 - "$f" <<'PY'
import json,sys
s=set()
for l in open(sys.argv[1]):
    try: e=json.loads(l)
    except Exception: continue
    if e.get("type")!="assistant": continue
    for c in e.get("message",{}).get("content",[]):
        if c.get("type")=="tool_use" and c.get("name")=="Skill":
            s.add(c.get("input",{}).get("skill",""))
print(",".join(sorted(s)) or "-")
PY
)
  hit=MISS; case ",$loaded," in *",$skill,"*) hit=HIT;; esac
  printf '%s\t%s\tloaded=%s\n' "$hit" "$skill" "$loaded" | tee -a "$OUT/summary.tsv"
done < "$IN"
