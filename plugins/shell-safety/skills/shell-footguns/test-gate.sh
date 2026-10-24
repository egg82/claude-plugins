#!/usr/bin/env bash
# Regression suite for the gate, including the new flag-value-glob rule.
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# GATE defaults to the plugin's hooks/bash-footgun-gate.sh (the copy shipped beside this skill), not
# whatever is installed under $HOME. Pass GATE=<path> to test a specific copy, and prove
# the path took effect with a control (GATE=/nonexistent must fail every case).
GATE="${GATE:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../hooks/bash-footgun-gate.sh}"
SKILL_MD="${SKILL_MD:-$HERE/SKILL.md}"
export GATE SKILL_MD
pass=0; fail=0
mkjson() { python3 -c 'import json,sys; print(json.dumps({"tool_name":sys.argv[1],"tool_input":{"command":sys.argv[2]}}))' "${TOOL:-Bash}" "$1"; }
t() {
  exp="$1"; label="$2"; cmd="$3"
  out=$(mkjson "$cmd" | bash "$GATE" 2>&1); rc=$?
  if [ "$rc" -eq "$exp" ]; then printf '  PASS  (rc=%s) %s\n' "$rc" "$label"; pass=$((pass+1))
  else printf '  FAIL  (rc=%s want=%s) %s\n        %s\n' "$rc" "$exp" "$label" "${out:0:110}"; fail=$((fail+1)); fi
}
# Same case, asserted for a different tool_name. Monitor's `command` runs in this same zsh, so the
# rules apply identically — but the gate ignored every non-Bash tool, so none of them ran for it.
tm() { TOOL=Monitor t "$@"; }

echo "COVERAGE — Monitor gets the same rules as Bash MUST BLOCK:"
# The watcher that exposed the hole, verbatim in shape: zsh does not split, so $2/$3 were empty and
# the completion test could never fire. Rule 10 names this exact construct and never saw it, because
# the gate short-circuited on tool_name and the settings.json matcher said "Bash" alone.
tm 2 "Monitor: for over \$(find) word-splits"      'for f in $(find /data -name "*.log"); do tail -1 "$f"; done'
tm 2 "Monitor: reading \$? after a formatter"       'kubectl get pods | tail -3; echo "rc=$?"'
tm 2 "Monitor: grep (?i) without -P"                "tail -f app.log | grep -E '(?i)error'"
echo "MUST ALLOW — ordinary watchers are not blocked (a gate that fires on these gets switched off):"
tm 0 "Monitor: tail piped to a line-buffered grep"  'tail -f app.log | grep -E --line-buffered "ERROR|Traceback|FAILED"'
tm 0 "Monitor: poll loop with an explicit read"     'while true; do read -r a b c <<<"$(stat_line)"; echo "$a $b $c"; sleep 30; done'
tm 0 "Monitor: inotifywait stream"                  'inotifywait -m --format "%e %f" /watched/dir'

echo "kill-every-container MUST BLOCK:"
t 2 "ps -q | xargs podman kill"          'podman ps -q | xargs podman kill'
t 2 "ps -aq | xargs -r docker rm -f"     'docker ps -aq | xargs -r docker rm -f'
t 2 "rm -f \$(podman ps -aq)"             'podman rm -f $(podman ps -aq)'
t 2 "filtered by image is everyone's"    'podman kill $(podman ps -q --filter ancestor=localhost/myapp-test)'
t 2 "status filter is everyone's"        'podman ps -q --filter status=running | xargs podman stop'
echo "curl-writeout-prints-credentials MUST BLOCK:"
t 2 "-u with redirect_url"               'curl -s -o /dev/null -w "%{http_code} %{redirect_url}" -u "admin:$P" http://h/api'
t 2 "--user with url_effective"          'curl -s --user a:b -w "%{url_effective}" http://h/'
t 2 "userinfo in URL with url"           'curl -s -w "%{url}" http://admin:secret@h/x'
echo "curl-writeout-prints-credentials MUST ALLOW:"
t 0 "-u with http_code only"             'curl -s -o /dev/null -w "%{http_code}" -u "admin:$P" http://h/api'
t 0 "redirect_url without credentials"   'curl -s -w "%{redirect_url}" http://h/x'
echo "kill-every-container MUST ALLOW:"
t 0 "filtered by name"                   'podman ps -q --filter name=job- | xargs podman kill'
t 0 "filtered by label"                  'podman rm -fv $(podman ps -aq --filter label=agent=a1)'
t 0 "-f name= short form"                'podman ps -q -f name=tmp- | xargs podman kill'
t 0 "one container by name"              'podman kill job-a'
t 0 "just listing"                       'podman ps -q'

echo "backtick-in-prose-flag MUST BLOCK:"
t 2 "backtick in --description"    'glab mr create --description "answers `400` rather than `404`"'
t 2 "backtick in -m"               'git commit -m "fixes the `foo` case"'
echo "backtick-in-prose-flag MUST ALLOW:"
t 0 "description from a file"      'glab mr create --description "$(cat body.md)"'
t 0 "single-quoted backticks"      "glab mr create --description 'answers \`400\` here'"
t 0 "no backticks at all"          'glab mr create --description "answers 400 rather than 404"'

# The zsh-only rules (flag-value-glob, mapfile-in-zsh, zsh-var-colon-modifier, zsh-scalar-for-in,
# set-dashdash-unquoted-zsh, zsh-scalar-as-command, multios-redirect-then-pipe) were removed when
# the Bash tool moved to bash. Under bash each of these is correct or harmless, so they must pass.
echo "RETIRED zsh-only rules MUST ALLOW under bash:"
t 0 "unquoted flag-value glob"                "grep -rn foo . --include=*.py"
t 0 "mapfile"                                 'mapfile -t ARR < <(kubectl get pods -o name)'
t 0 "\$img:latest"                            'podman pull $img:latest'
t 0 "scalar in a for-list"                    'PATHS="a b c"; for p in $PATHS; do echo $p; done'
t 0 "set -- \$var"                            'set -- $line; echo "$2"'
t 0 "scalar in command position"              'CMD="ssh -o BatchMode=yes"; $CMD host uptime'
t 0 "redirect then pipe"                      'cmd > out.txt 2>&1 | head -5'

# container-rm-keeps-volume: the literal incident, then the forms that must stay allowed
t 2 "podman rm -f without -v (the incident)"   "podman rm -f app-pg"
t 2 "docker rm without -v"                     "docker rm old-container"
t 2 "after a chain"                            "true && podman rm -f app-pg-x"
t 0 "podman rm -f -v"                          "podman rm -f -v app-pg"
t 0 "podman rm -fv cluster"                    "podman rm -fv app-pg"
t 0 "podman rm --volumes"                      "podman rm --volumes -f app-pg"
t 0 "podman rmi is images"                     "podman rmi old-image"
t 0 "podman volume rm"                         "podman volume rm some-volume"
t 0 "quoted in prose"                          "echo 'run podman rm -f x to clean up'"

echo "NEW RULE — bare _ as argv1 to a script FILE MUST BLOCK:"
t 2 "bash file _ arg (the shape that bit)"    'bash /tmp/movebody.sh _ "$HOME" "$HOLD"'
t 2 "relative path"                           "bash body.sh _ a b"
t 2 "sh instead of bash"                      "sh body.sh _ a"
t 2 "zsh instead of bash"                     "zsh body.sh _ a"
t 2 "quoted path with a variable"             'bash "$S/t.sh" _ "$F"'
t 2 "absolute interpreter path"               "/usr/bin/bash body.sh _ a"

echo "MUST ALLOW — the correct -c form, and _ that is not argv1:"
t 0 "bash -c body _ arg (correct usage)"       'bash -c "$(cat body.sh)" _ "$HOME"'
t 0 "bash -c inline _ arg"                     "bash -c 'echo $1' _ hello"
t 0 "script with no _ at all"                  "bash body.sh /home/x /tmp/y"
t 0 "_ later in the args, not argv1"           "bash body.sh real _ other"
t 0 "an argument merely starting with _"       "bash body.sh _myarg b"
t 0 "underscore in a path, not a bare token"   "bash my_body.sh a b"
t 0 "unrelated command containing sh"          "publish body.sh real _ other"

echo "NEW RULE — pipefail + grep -q MUST BLOCK:"
t 2 "pipefail then | grep -q"                 "set -o pipefail; cat f | grep -q token"
t 2 "set -uo pipefail, grep -qi"              "set -uo pipefail; git show HEAD:f | grep -qi warning"
t 2 "pipefail with grep -sq"                  "set -o pipefail; cmd | grep -sq needle"
t 2 "pipefail with grep -qE"                  "set -o pipefail; cmd | grep -qE 'a|b'"

echo "MUST ALLOW — no pipefail, or not -q:"
t 0 "grep -q without pipefail"                "cat f | grep -q token"
t 0 "pipefail with grep -c (the fix)"         "set -o pipefail; [ \"\$(cat f | grep -c token)\" -gt 0 ]"
t 0 "pipefail with plain grep"                "set -o pipefail; cat f | grep token"
t 0 "pipefail alone"                          "set -o pipefail; make build"
t 0 "sort -u stays allowed (not gateable)"    "cut -d, -f1 in.csv | sort -u > out.txt"

echo "NEW RULE — for-in-find/ls word-splitting MUST BLOCK:"
t 2 "for f in \$(find ...)"                    'for f in $(find /data -name "*.csv"); do echo "$f"; done'
t 2 "for f in \$(ls ...)"                      'for f in $(ls /data); do echo "$f"; done'
t 2 "backtick find"                           'for f in `find . -type f`; do echo "$f"; done'
t 2 "for inside kubectl exec sh -c"           'kubectl exec pod -- sh -c '"'"'for f in $(find /m -name "*.csv"); do wc -l "$f"; done'"'"''

echo "MUST ALLOW — safe iteration and unrelated loops:"
t 0 "find -print0 into while read -d (bash)"  'find . -type f -print0 | while IFS= read -r -d "" f; do echo "$f"; done'
t 0 "find -exec"                              'find . -type f -exec wc -l {} \;'
t 0 "for i in \$(seq 1 10)"                    'for i in $(seq 1 10); do echo $i; done'
t 0 "for over a literal list"                 'for x in a b c; do echo $x; done'
t 0 "plain find, no loop"                     'find /data -name "*.csv" | head'

echo "NEW RULE — read -d under POSIX sh MUST BLOCK:"
t 2 "sh -c with read -r -d"                   'kubectl exec pod -- sh -c '"'"'find /m -print0 | while IFS= read -r -d "" f; do echo "$f"; done'"'"''
t 2 "plain sh -c read -d"                     'sh -c '"'"'while read -d "" x; do echo $x; done'"'"''

echo "MUST ALLOW — bash -c, or no -d:"
t 0 "bash -c with read -d is fine"            'bash -c '"'"'while IFS= read -r -d "" f; do echo "$f"; done'"'"''
t 0 "sh -c with plain read"                   'kubectl exec pod -- sh -c '"'"'while IFS= read -r f; do echo "$f"; done'"'"''
t 0 "sh -c doing something else"              'kubectl exec pod -- sh -c "ls -la /tmp"'

echo "PRE-EXISTING RULES still hold:"
t 2 "grep (?i) without -P"                    "grep -E '(?i)error' file.log"
t 2 "pgrep -af"                               "pgrep -af monitor.sh"
t 2 "negated pgrep -f in a wait loop"         "until test -s f && ! pgrep -f job.sh; do sleep 5; done"
t 0 "negated pgrep -x"                        "until ! pgrep -x job; do sleep 5; done"
t 0 "pgrep -x avoids the self-match (no -f)"  "pgrep -x monitor.sh"
t 2 "kubectl exec -i writing a file"          "cat b | kubectl exec -i pod -- sh -c 'cat > /tmp/f'"
t 2 "-it form writing into the pod"           "cat big.txt | kubectl exec -it pod -- tee /tmp/f"
t 2 "-ti form, flags reversed"                "cat big.txt | kubectl exec -ti pod -- tee /tmp/f"
t 2 "canonical -i still blocks"               "cat big.txt | kubectl exec -i pod -- tee /tmp/f"
t 0 "tee is LOCAL, kubectl is the source"     "kubectl exec -i pod -- ls | tee out.txt"
t 2 "dd of= fed by a redirect"                "kubectl exec -i pod -- dd of=/tmp/f < big.bin"
t 2 "cat >> fed by a heredoc"                 $'kubectl exec -i pod -- sh -c \'cat >> /tmp/f\' <<EOF\ndata\nEOF'
# stdin consumed by a program, not written to a file: the fix exec-stdin-without-i asks for must pass.
t 0 "psql fed by a heredoc"                   $'kubectl exec -i pod -- psql -U app <<EOF\nEXPLAIN SELECT 1;\nEOF'
t 0 "psql fed by a redirect"                  "kubectl exec -i pod -- psql -U app < q.sql"
t 0 "a script piped into sh"                  "cat check.sh | kubectl exec -i pod -- sh"
t 2 "any redirect in the remote command"      "base64 big | kubectl exec -i pg-0 -- sh -c 'base64 -d >/tmp/x'"
t 0 "remote stderr to /dev/null is no file"   "cat q.sql | kubectl exec -i pg-0 -- sh -c 'psql 2>/dev/null'"
t 0 "an unquoted > is a LOCAL redirect"       "kubectl exec -i pod -- psql -U app < q.sql > out.txt"
t 0 "exec with no stdin plumbing"             "kubectl exec pod -- ls -la"
t 0 "grep -P with (?i)"                       "grep -P '(?i)error' file.log"
t 0 "(?i) in another command than the grep"   "python3 q.py 'x{a=~\"(?i)s.*\"}'; grep -c y f"
t 2 "(?i) grep after an unrelated command"    "ls; grep -E '(?i)error' file.log"
t 2 "(?i) grep downstream of a -P grep"       "grep -P 'a' f | grep '(?i)b'"
t 0 "kubectl cp"                              "kubectl cp big.txt pod:/tmp/f"
t 0 "ordinary command"                        "ls -la /tmp"

echo
echo "NEW RULE — \$(tty) as a value MUST BLOCK: [gate:tty-in-command-substitution]"
t 2 "tty with stderr redirect and fallback"    'iotty="$(tty 2>/dev/null || echo /dev/tty1)"; exec 3<"$iotty"'
t 2 "bare tty substitution"                    'dev=$(tty); echo "$dev"'
t 2 "tty substitution with only a redirect"    'x="$(tty 2>/dev/null)"'

echo "MUST ALLOW — tty -s as a test, or no substitution:"
t 0 "tty -s used as a condition"               'tty -s && echo interactive'
t 0 "tty -s in an if"                          'if tty -s; then echo yes; fi'
t 0 "tty -s inside a substitution"             'x=$(tty -s && echo yes)'
t 0 "explicit device probe"                    'for d in /dev/tty /dev/console; do [ -w "$d" ] && exec 3>"$d" && break; done'

echo
echo "NEW RULE — nc UDP zero-scan MUST BLOCK: [gate:nc-udp-zero-scan]"
t 2 "nc -zuv udp probe"                        'nc -zuv 192.0.2.10 69'
t 2 "nc -uz flag order swapped"                'nc -uz host 161'
t 2 "nc -zu inside a larger check"             'echo start; nc -zu 192.0.2.11 69 && echo open'

echo "MUST ALLOW — tcp scans, and actually speaking the protocol:"
t 0 "nc -z on TCP is fine"                     'nc -z host 22'
t 0 "real syslog message"                       'logger --udp -n host -P 514 test message'
t 0 "nc -u without -z (interactive udp)"       'printf x | nc -u -w1 host 514'

# The SYNC check and the summary MUST stay last. A case placed below the summary is excluded from
# the counts AND makes the script's exit status that case's rc, so the suite reports green no
# matter what — that has actually happened, stranding 8 cases below the summary on the copy this
# was merged from.
echo "NEW RULE — unpaged ldapsearch counts MUST BLOCK:"
t 2 "grep -c dn on unpaged search"            'ldapsearch -Q -LLL -H ldap://ldap1.example.test -b dc=example,dc=test "(objectClass=device)" cn | grep -c "^cn:"'
t 2 "wc -l on unpaged search"                 'ldapsearch -Q -LLL -H ldap://ldap1.example.test -b dc=example,dc=test "(objectClass=device)" cn | wc -l'
t 2 "uniq -c distribution, unpaged"           'ldapsearch -Q -LLL -H ldap://ldap1.example.test -b dc=example,dc=test "(objectClass=device)" l | awk -F": " "/^l:/{print \$2}" | sort | uniq -c'

echo "MUST ALLOW — paged, or not counting:"
t 0 "paged with -E pr=1000/noprompt"          'ldapsearch -Q -LLL -E pr=1000/noprompt -H ldap://ldap1.example.test -b dc=example,dc=test "(objectClass=device)" cn | grep -c "^cn:"'
t 0 "single-object lookup, no count"          'ldapsearch -Q -LLL -H ldap://ldap1.example.test -b dc=example,dc=test "(cn=host1)" l'
t 0 "unpaged but only inspected"              'ldapsearch -Q -LLL -H ldap://ldap1.example.test -b dc=example,dc=test "(objectClass=device)" cn | head -40'
t 0 "counting an ldif FILE, no ldapsearch"    'grep -c "^cn:" export.ldif'

echo "NEW RULE — tee masking a script's exit status MUST BLOCK:"
t 2 "python piped to tee"                     'python3 discover.py 2>&1 | tee discover.log'
t 2 "bash script piped to tee"                'bash run.sh | tee out.log'
t 2 "python -u with tee -a"                   'python3 -u job.py 2>&1 | tee -a log.txt'

echo "MUST ALLOW — pipefail set, or not a script:"
t 0 "pipefail makes it honest"                'set -o pipefail; python3 x.py | tee log'
t 0 "plain ls into tee"                       'ls -la | tee out.txt'
t 0 "echo into tee"                           'echo hi | tee f'
t 0 "redirect instead of tee (the fix)"       'python3 x.py > log 2>&1'
t 0 "cat into tee"                            'cat file | tee copy'

echo
echo
echo "NEW RULE — \$? after a formatter pipeline MUST BLOCK: [gate:formatter-masks-exit-status]"
t 2 "the real case: sed then exit=\$?"        'python3 check.py | sed "s/^/  /"; echo "exit=$?"'
t 2 "awk as the last stage"                   'make test | awk "{print}"; rc=$?; exit $rc'
t 2 "cut, status read later in the line"      'kubectl get po | cut -c1-40; [ $? -eq 0 ] && echo ok'
t 2 "the second harness: tail masks ruff"      'ruff check . | tail -3; if [ $? -eq 0 ]; then echo "lint: clean"; fi'
t 2 "head is the same shape"                   'pytest -q | head -5; echo "rc=$?"'
t 2 "third hit: sort -u masks a zero-match grep" 'grep -o "id=" f.html | sort -u; echo "rc=$?"'
t 2 "uniq as the last stage"                   'kubectl get po | uniq; echo "rc=$?"'
t 2 "wc, the count read as a status"           'grep -c foo f.txt | wc -l; echo "rc=$?"'
echo "MUST ALLOW — status-bearing filters, PIPESTATUS, pipefail, or no \$? read:"
t 0 "grep IS the test being made"             'kubectl get po | grep -q Running; echo $?'
t 0 "sort -c is a CHECK, its status is the point" 'cat f | sort -c; echo "rc=$?"'
t 0 "sort -C likewise"                        'cat f | sort -C; echo "rc=$?"'
t 0 "sort -u under pipefail"                  'set -o pipefail; grep -o x f | sort -u; echo "rc=$?"'
t 0 "sort -u with no \$? read at all"          'grep -o "id=" f.html | sort -u'
# The shell is bash now, so these two swapped: PIPESTATUS reads the real stage, and zsh's
# lowercase array expands to nothing (`exit` with no argument exits with sed's 0).
t 0 "bash PIPESTATUS reads the right stage"   'python3 check.py | sed "s/^/  /"; exit ${PIPESTATUS[0]}'
t 2 "zsh pipestatus is empty in bash"         'python3 check.py | sed "s/^/  /"; exit ${pipestatus[1]}'
t 2 "an earlier ssh does not exempt a local one" 'ssh h true; python3 c.py | sed "s/^/ /"; echo "rc=${pipestatus[1]}"'
t 0 "pipestatus inside the ssh argument"      "ssh h 'python3 c.py | sed s/^/x/; echo rc=\${pipestatus[1]}'"
t 0 "multi-line ssh argument"                 $'ssh h \'\npython3 c.py | sed s/^/x/\necho rc=${pipestatus[1]}\''
t 0 "zsh -c double-quoted"                    'zsh -c "python3 c.py | sed s/^/x/; echo \${pipestatus[1]}"'
t 0 "pipefail makes the status meaningful"    'set -o pipefail; python3 check.py | sed "s/^/ /"; echo $?'
t 0 "formatter with no status read at all"    'kubectl get po | sed "s/^/  /"'
t 0 "\$? before the pipeline, not after"      'python3 check.py; rc=$?; echo "$rc" | sed "s/^/  /"'
t 0 "formatter and \$? in unrelated statements" 'ls dir | sed "s/^/  /"; echo "---"; python3 c.py > o 2>&1; echo "exit=$?"'
t 0 "redirect, not a pipe, immediately before"  'python3 c.py > out.txt 2>&1; echo "rc=$?"'
t 0 "formatter inside a \$( ) argument"          'bash -c "$(sed -n 1p f | sed s/a/b/)" > /dev/null; echo "rc=$?"'
t 2 "assignment takes the substitution's status" 'n=$(python3 c.py | wc -l); echo "rc=$?"'

echo "NEW RULE — prints a usable answer AND fails, so both branches run: [gate:prints-and-fails-fallback]"
t 2 "the real case: grep -c with a fallback"    'N="$(grep -c foo file || echo 0)"'
t 2 "systemctl is-enabled, same shape"          's="$(systemctl is-enabled f.timer || printf absent)"'
t 2 "grep -cE counts too"                       'n="$(grep -cE "^ERROR" app.log 2>/dev/null || echo 0)"'
t 2 "is-active is the same command family"      'a="$(systemctl is-active svc || echo unknown)"'
echo "MUST ALLOW — the correct form, or a command printing nothing usable on failure:"
t 0 "capture first, default second"             'n="$(grep -c foo file)" || n=0'
t 0 "a bare grep -c with no fallback"           'grep -c foo file'
t 0 "cat prints nothing usable on failure"      'x="$(cat file || echo missing)"'
t 0 "ls likewise"                               'x="$(ls dir || echo none)"'
t 0 "grep -c as a condition, no fallback"       'if grep -c foo f; then echo yes; fi'
t 0 "prose about the trap is not the trap"      'echo "grep -c X || echo 0 is a trap"'

echo "NEW RULE — formatter pipeline used as a CONDITION MUST BLOCK: [gate:formatter-as-condition]"
t 2 "the real case: merge status via tail"     'if git merge fix/x 2>&1 | tail -3; then echo CLEAN; fi'
t 2 "head as the last condition stage"         'if pytest -q | head -5; then echo passed; fi'
t 2 "negation does not change the trap"        'if ! make build | sed "s/^/  /"; then echo failed; fi'
t 2 "while condition, same shape"              'while curl -s http://x | tail -1; do sleep 1; done'
echo "MUST ALLOW — substitution feeds a real test, status-bearing filter, or not a condition:"
t 0 "formatter inside \$(...) feeds a test"     'if [ -n "$(rpm -qa | tail -1)" ]; then echo yes; fi'
t 0 "backtick substitution, same shape"        'if [ "`ls | head -1`" = a ]; then echo yes; fi'
t 0 "grep carries the status wanted"           'if kubectl get po | grep -c Running; then echo up; fi'
t 0 "formatter in the body, not the condition" 'while read -r l; do echo "$l" | sed s/a/b/; done < f'
t 0 "no pipeline in the condition at all"      'if git merge fix/x; then echo CLEAN; fi'

echo "NEW RULE — formatter pipeline then && / || MUST BLOCK: [gate:formatter-then-and]"
t 2 "the real case: a rejected push read as pushed" 'git push -q origin HEAD:main | tail -3 && echo "pushed to main"'
t 2 "|| never fires either"                    'make build | tail -5 || echo "build FAILED"'
t 2 "head, same shape"                         'pytest -q | head -3 && echo "tests passed"'
t 2 "sed added only to indent"                 'terraform apply | sed "s/^/  /" && echo applied'
t 2 "tee is a formatter here too"              'helm upgrade x . | tee log && echo deployed'
echo "MUST ALLOW — status-bearing filter, pipefail set, or the pipe is not before the operator:"
t 0 "grep -q carries the status wanted"        'kubectl get po | grep -q Running && echo up'
t 0 "grep -c likewise"                         'ls | grep -c foo && echo present'
t 0 "pipefail makes the status real"           'set -o pipefail; make build | tail -5 && echo ok'
# Under bash, PIPESTATUS is the working status read and earns the exemption (it did not under zsh).
t 0 "bash PIPESTATUS is the working form"      'make build | tail -5; [ "${PIPESTATUS[0]}" -eq 0 ] && echo ok'
# MENTION VS USE, fixed after this rule blocked an ordinary `awk` on real traffic. An
# operator inside the formatter's OWN program is program text, not a shell operator. `awk` with a
# compound condition after a pipe is everyday shell, so this was a nag on correct commands.
t 0 "&& inside the awk program"                'kubectl get po -A | awk '"'"'$3 != "Running" && $3 != "Completed" {print $1}'"'"''
t 0 "|| inside the awk program"                'ps aux | awk '"'"'$3 > 50 || $4 > 50 {print $11}'"'"''
t 0 "&& inside a double-quoted sed script"     'ls | sed "s/a && b/x/"'
t 0 "awk program with no pipe at all"          'awk '"'"'$1 > 0 && $2 < 5 {print}'"'"' data.txt'
# THE TWIN OF THOSE, and the reason the fix is not "blank quoted spans". Here the quote opens AFTER
# the formatter name too, but the operator is outside it — so quoting alone cannot decide.
t 2 "quoted sed script, then a REAL &&"        'terraform apply | sed "s/^/  /" && echo applied'
t 2 "awk IS the formatter, then a REAL &&"     'make build | awk '"'"'{print $1}'"'"' && echo built'
# AND THE OTHER DIRECTION, which blanking WOULD have broken: a nested shell whose whole pipeline and
# operator sit inside one quoted span. Caught before the fix and must stay caught after it. These
# were untested until the fix went in — the behaviour was real but unpinned.
t 2 "sh -c, double-quoted inner pipeline"      'sh -c "make build | tail -3 && echo ok"'
t 2 "sh -c, single-quoted inner pipeline"      'sh -c '"'"'make build | tail -3 && echo ok'"'"''

echo "git commit, then a git push that runs regardless: [gate:commit-then-push-unguarded]"
# The incident: `git commit --only <untracked>; …; git push` — the commit failed and the push
# shipped nineteen earlier, untested commits. Replayed, this pair was 402 of the 427 hits of the
# broader any-mutator-then-mutator rule it replaced, and the rest were mostly false positives
# (`kubectl create ns x 2>/dev/null; kubectl apply`, `git tag -l; git push --tags`).
t 2 "the incident: commit; push"               'git commit -q --only a.py -m x; git push -q origin HEAD:main'
t 2 "newline spelling"                         'git commit -q -F msg.txt
git push -q'
t 2 "a read-only step between does not help"   'git commit -m x; git log -1; git push'
t 2 "&& before the commit does not guard it"   'cd repo && git commit -m x; git push'
t 2 "a push in an if condition after"          'git commit -m x; if git push; then echo ok; fi'
t 2 "git -C on both"                           'git -C repo commit -m x; git -C repo push'
t 2 "git -c and --git-dir options"             'git -c user.name=a commit -m x; git --git-dir=r/.git push'
t 2 "env assignment before git"                'GIT_EDITOR=true git commit -q; git push'
t 2 "nested quotes in an earlier assignment"   $'x="$(echo \'a"b\')"; git commit -m x; git push'
t 2 "a here-string earlier is not a heredoc"   'grep -q foo <<< "hello world"
git commit -m x
git push'
t 2 "case...esac earlier, then commit; push"   'case $x in (a) echo;; esac; git commit -m x; git push'
t 2 "\${x:-\\}} brace in a variable"            'echo ${x:-\}}; git commit -m x; git push'
t 2 "inside a function body"                   'f() { git commit -m x; git push; }; f'
t 2 "inside a subshell"                        '( cd repo; git commit -m x; git push )'
t 2 "inside a nested brace block"              'if true; then { git commit -m x; git push; }; fi'
echo "MUST ALLOW — not commit-then-push, or guarded:"
t 0 "commit && push is the fix"                'git commit -m x && git push'
t 0 "&& then a newline"                        'git commit -m x &&
  git push'
t 0 "line continuation into &&"                'git commit \
  -m x \
  && git push'
t 0 "commit || exit, then push"                'git commit -m x || exit 1; git push'
t 0 "&& chain inside a subshell"               '( cd repo && git commit -m x && git push )'
t 0 "set -e carries into a function body"      'set -e; f() { git commit -m x; git push; }; f'
t 0 "set -e inside the function body"          'f() { set -e; git commit -m x; git push; }; f'
t 0 "commit as an if condition"                'if git commit -m x; then git push; fi'
t 0 "status read between the two"              'git commit -m x; rc=$?; git push'
t 0 "status echoed between the two"            'git commit -m x; echo rc=$?; git push'
t 0 "set -e before commit; push"               'set -e; git commit -m x; git push'
t 0 "set -euo pipefail, newline form"          'set -euo pipefail
git commit -m x
git push'
t 0 "two independent pushes"                   'cd ~/a && git push; cd ~/b && git push'
t 0 "case branches are alternatives"           'case $1 in
  a) git commit -m x ;;
  b) git push ;;
esac'
t 0 "git tag -l, then push --tags"             'git tag -l; git push --tags'
t 0 "commit-tree in a substitution"            't=$(git commit-tree HEAD^{tree} -m x); git push origin $t:refs/heads/y'
t 0 "push named in an unquoted echo"           'echo step 2 git commit then git push next
git status'
t 0 "kubectl create ns idiom"                  'kubectl create ns foo 2>/dev/null; kubectl apply -n foo -f x.yaml'
t 0 "apply then rollout restart (not this rule)" 'kubectl apply -f x.yaml; kubectl rollout restart deploy/app'
t 0 "push in a trailing comment"               'git commit -m x  # then git push later
git log -1'
t 0 "push inside the heredoc body"             $'git commit -F - <<\'EOF\'\nmsg; git push\nEOF\ngit log -1'
t 0 "Claude-style commit message heredoc"      $'git commit -m "$(cat <<\'EOF\'\nfix: don\'t break\n\nCo-Authored-By: x\nEOF\n)" && git push'
t 0 "echo after push (output shows the rejection)" 'git push -q origin HEAD:main
echo "PUSHED"'
t 0 "echo after commit"                        'git commit -q -F msg.txt; echo "committed"'
t 0 "echo after vault write"                   'vault kv put kv/x @f.json
echo "done"'
t 0 "echo after flux reconcile"                'flux reconcile kustomization flux-system
echo "✓ reconciled"'
t 0 "section header after push"                'git push -q origin HEAD:main
echo "=== now the tags ==="'
t 0 "progress label after apply"               'kubectl apply -f x.yaml
echo "waiting for rollout"'
t 0 "commit then log"                          'git commit -m x; git log -1'
t 0 "commit then show --stat"                  'git commit -q --only f -m x; git show --stat HEAD'
t 0 "push then status"                         'cd repo && git push; git status'
t 0 "apply then get"                           'kubectl apply -f x.yaml; kubectl get pods'
t 0 "if-body apply, then echo"                 'if [ -f x.yaml ]; then kubectl apply -f x.yaml; fi; echo next'
t 0 "backgrounded apply, then sleep"           'kubectl apply -f x.yaml & sleep 1'
t 0 "&& is the correct guarded form"           'git push -q origin HEAD:main && echo "PUSHED"'
t 0 "&& into a read-only check"                'kubectl apply -f a.yaml && kubectl get pods'
t 0 "|| failure branch, then more"             'kubectl apply -f a.yaml || echo FAILED; kubectl get pods'
t 0 "set -e makes the echo unreachable"        'set -euo pipefail
git push -q origin HEAD:main
echo "PUSHED"'
t 0 "set -o errexit spelling"                  'set -o errexit; git push -q origin HEAD:main; echo "PUSHED"'
t 0 "mutator is the last statement"            'cd repo; git status; git push'
t 0 "read-only command is out of scope"        'git log --oneline -1
echo "done"'
t 0 "printing what the command returned"       'git push -q origin HEAD:main
echo "push exit: $?"'
t 0 "capturing the status"                     'git push -q origin HEAD:main; rc=$?; echo "rc=$rc"'
t 0 "mutator as an if condition"               'if git push; then echo ok; else echo FAILED; fi'
t 0 "mutator last in a loop body"              'for f in a.yaml b.yaml; do kubectl apply -f "$f"; done'
t 0 "mutator named inside a quoted string"     'echo "next: git push origin main"; ls'
t 0 "2>&1 is a redirect, not a separator"      'git push origin main 2>&1'
t 0 "trailing comment line is not a statement" 'git push origin main
# that is all'
t 0 "heredoc terminator is not a statement"    $'git commit -F - <<EOF\nmsg; echo hi\nEOF'
t 2 "zsh pipestatus is empty in bash"          'make build | tail -5; [ "${pipestatus[1]}" -eq 0 ] && echo ok'
t 0 "the pipe comes AFTER the operator"        'test -f x && cat x | tail -3'
t 0 "formatter with no following operator"     'git push origin main | tail -3'

echo "zsh's pipestatus in a bash shell MUST BLOCK: [gate:zsh-pipestatus-in-bash]"
# The inverse of the retired bash-pipestatus-in-zsh: the Bash tool is bash now, where lowercase
# `pipestatus` is an unset variable and expands to nothing.
t 2 "the habit from the zsh era"               'git push -q origin main 2>&1 | grep -v x; echo "push rc=${pipestatus[1]}"'
t 2 "bare \$pipestatus"                        'make | tail -2; echo $pipestatus'
t 2 "~/.ssh is a path, not ssh"                'ls ~/.ssh; make | tee log; echo rc=${pipestatus[1]}'
echo "MUST ALLOW — the bash form, pipefail, a real zsh context, or merely NAMING it:"
t 0 "bash PIPESTATUS"                          'ruff check . | head -5; echo "rc=${PIPESTATUS[0]}"'
t 0 "pipefail instead"                         'set -o pipefail; ruff check . | head -5; echo "rc=$?"'
t 0 "explicit zsh -c is genuinely zsh"         'zsh -c "ruff check . | head -5; echo \${pipestatus[1]}"'
t 0 "sent to a remote zsh over ssh"            "ssh host 'make | tail -2; echo \${pipestatus[1]}'"
t 0 "grepping FOR the trap is not the trap"    "grep -n 'pipestatus' ~/.claude/hooks/bash-footgun-gate.sh"
t 0 "the expansion as a single-quoted grep pattern" "grep -rn '\${pipestatus[1]}' ~/.claude/skills"
t 0 "the expansion as a single-quoted rg pattern"   "rg -F '\${pipestatus[1]}' ~/.claude"

echo "NEW RULE — cat -A through a line-prefixing sed MUST BLOCK: [gate:cat-a-through-line-prefix]"
t 2 "the exact shape that bit, three times"  "cat -A file.yaml | sed 's/^/  /'"
t 2 "sed -n range piped to cat -A then prefixed" "sed -n '1,5p' f.yaml | cat -A | sed 's/^/  /'"
t 2 "pipe delimiter instead of slash"         "cat -A f | sed 's|^|    |'"
t 2 "cat -An (flag cluster)"                  "cat -An f | sed 's/^/  /'"
echo "MUST ALLOW — cat -A raw, or a prefix with no cat -A:"
t 0 "cat -A on its own (the correct form)"     "cat -A cluster1/app/kustomization.yaml"
t 0 "cat -A piped to a NON-prefixing filter"   "cat -A f | grep -n resources"
t 0 "prefixing sed with no cat -A present"     "sed -n '1,5p' f.yaml | sed 's/^/  /'"
t 0 "cat -A then tail, no prefix"              "cat -A f | tail -5"

echo "sudo-drains-heredoc-stdin MUST BLOCK:"
t 2 "sudo then more lines, quoted bash -s"       $'ssh host \'bash -s\' <<\'EOS\'\nsudo -n id\necho after\nEOS'
t 2 "unquoted bash -s and delimiter"             $'ssh host bash -s <<EOS\nsudo apt update\necho done\nEOS'
t 2 "sh -s rather than bash -s"                  $'ssh host \'sh -s\' <<\'EOS\'\nsudo id\necho after\nEOS'
echo "sudo-drains-heredoc-stdin MUST ALLOW:"
t 0 "sudo given </dev/null"                      $'ssh host \'bash -s\' <<\'EOS\'\nsudo -n id </dev/null\necho after\nEOS'
t 0 "heredoc written to a FILE, not a shell"     $'cat > /tmp/x.sh <<\'EOS\'\nsudo -n id\necho after\nEOS'
t 0 "sudo on the last line drains nothing"       $'ssh host \'bash -s\' <<\'EOS\'\necho first\nsudo -n id\nEOS'
t 0 "heredoc into bash -s with no sudo"          $'ssh host \'bash -s\' <<\'EOS\'\nid\necho after\nEOS'
t 0 "nested in another heredoc (doc authoring)"  $'python3 - <<\'PY\'\nx = \'ssh h \'bash -s\' <<EOS sudo id after EOS\'\nPY'
t 0 "unterminated <<EOS inside a quoted string"  $'printf \'ssh host bash -s <<EOS sudo apt update EOS\' > /tmp/d.txt\necho sudo done'
t 0 "recommended scp-then-run form"              'scp x.sh host:/tmp/ && ssh host "bash /tmp/x.sh"'

echo
echo "pgrep-f-self-match MUST BLOCK:"
t 2 "self-kill at line start in a heredoc body"  $'cat > /tmp/x.sh <<\'SH\'\npkill -f scratchpad/poll.sh\nSH\nbash /tmp/x.sh'
t 2 "bare one-liner"                             'pkill -f poll.sh'
echo "pgrep-f-self-match MUST ALLOW:"
t 0 "the form quoted in backticks (its own docs)" $'cat > doc.md <<\'MD\'\n- `pkill -f monitor.sh` killed it (exit 144).\nMD'
t 0 "mid-sentence prose"                          "echo 'note pkill -f matches the wrapper'"
t 0 "ps|grep instead"                             "ps -eo pid,args | grep -E '[p]oll.sh'"
t 0 "kill by name, no -f"                         'pkill poll.sh'

echo "NEW RULE — stdin-eater-in-read-loop MUST BLOCK:"
t 2 "eater in loop body, heredoc'd script"        $'cat > /tmp/y.sh <<\'SH\'\nwhile IFS= read -r id; do\n  ssh $id uptime\ndone < hosts.txt\nSH'
t 2 "ssh in loop body, one-liner (after \`do\`)"    'while read -r h; do kubectl --context $h get nodes; done < hosts.txt'
echo "MUST ALLOW — redirected, outside the loop, or no eater:"
t 0 "same loop WITH </dev/null"                    'while IFS= read -r id; do ssh $id uptime < /dev/null; done < hosts.txt'
t 0 "eater OUTSIDE the loop"                       'kubectl get nodes -o name > f.txt; while IFS= read -r l; do echo $l; done < f.txt'
t 0 "loop with no eater"                           'while IFS= read -r l; do printf %s $l; done < f.txt'

echo "NEW RULE — vault-secret-to-stdout MUST BLOCK:"
# Both real leaks. The second is the one a subagent ran while its brief told it not to.
t 2 "bare vault token lookup (the parent's)"      'vault token lookup'
t 2 "vault kv get, no -field (the subagent's)"    'vault kv get -mount=kv appsecrets'
t 2 "-format=json does NOT redact the token id"   'vault token lookup -format=json'
t 2 "vault kv get path form"                      'vault kv get kv/proj1'
t 2 "vault read"                                  'vault read kv/data/proj1'
t 2 "vault token create prints the new token"     'vault token create -ttl=1h'
t 2 "vault print token"                           'vault print token'
# A PIPE IS NOT AN ESCAPE. The first version of the rule deferred on any `|` and would have ALLOWED
# the real leak below — every key sat inside the 30-line cut. Regression-locked in both directions.
t 2 "the actual leak: | head -30"                 'vault kv get -mount=kv appsecrets 2>&1 | head -30'
t 2 "| grep <key> still prints the value"         'vault kv get -mount=kv proj1 2>&1 | grep -iE "^field_one"'
t 2 "| tail"                                      'vault kv get kv/proj1 | tail -20'
t 2 "| cat"                                       'vault read kv/data/proj1 | cat'
echo "vault-secret-to-stdout MUST ALLOW — the idioms you should be using:"
t 0 "-field= names the one field"                 'vault token lookup -field=ttl'
t 0 "-field= captured into a var"                 'export DB_USER="$(vault kv get -field=DB_USER apps/demo)"'
t 0 "keys-only listing goes via a file, not a pipe" 'vault kv get -format=json kv/proj1 > /tmp/s.json && python3 -c "import json;print(sorted(json.load(open(\"/tmp/s.json\"))[\"data\"][\"data\"]))"'
t 0 "redirected to a file, not the transcript"    'vault kv get -format=json kv/proj1 > /tmp/s.json'
t 0 "unrelated vault subcommands stay free"       'vault status'
t 0 "listing paths reveals no values"             'vault kv list kv'
t 0 "stat the token file (does not print it)"     'ls -la ~/.vault-token'

echo "NEW RULE — talosctl-dryrun-context-secrets MUST BLOCK:"
# The leak, verbatim in shape: the reflex WARNING filter keeps every context line.
t 2 "the actual leak: | grep -v WARNING"          'talosctl -n 192.0.2.11 patch machineconfig --patch @cp.yaml --mode=no-reboot --dry-run 2>&1 | grep -v "^WARNING" | head -80'
t 2 "bare apply-config --dry-run"                 'talosctl -n 192.0.2.12 apply-config --file controlplane.yaml -p @node1.yaml --dry-run'
t 2 "patch mc short form"                         'talosctl -n 192.0.2.13 patch mc --patch @p.yaml --dry-run'
t 2 "| tail is not a filter"                      'talosctl -n 192.0.2.13 apply-config --file f.yaml --dry-run | tail -40'
echo "talosctl-dryrun-context-secrets MUST ALLOW:"
t 0 "filtered to changed lines"                   "talosctl -n 192.0.2.11 patch machineconfig --patch @cp.yaml --dry-run 2>&1 | grep -E '^[+-][^+-]|reboot'"
t 0 "redirected to a file"                        'talosctl -n 192.0.2.11 apply-config --file f.yaml --dry-run > /tmp/d.txt 2>&1'
t 0 "not a dry run"                               'talosctl -n 192.0.2.11 patch mc --patch @p.yaml --mode=no-reboot'
t 0 "--dry-run=false is a real apply"             'talosctl -n 192.0.2.11 apply-config --file f.yaml --dry-run=false'
t 0 "upgrade-k8s dry run stays ungated"           'talosctl -n 192.0.2.11 upgrade-k8s --to 1.37.1 --dry-run'

echo "NEW RULE — memory-write-via-bash MUST BLOCK:"
# The shape that actually happened, seven times: path and write_text BOTH inside the heredoc, so
# this case also proves the rule reads raw_cmd. Against stripped `cmd` it would allow.
t 2 "python heredoc write_text (the real one)"    $'python3 - <<\'PY\'\nfrom pathlib import Path\nPath("/home/x/.claude/memory/x.md").write_text(s)\nPY'
t 2 "cat > a new memory"                          $'cat > ~/.claude/memory/new-thing.md <<\'MD\'\nbody\nMD'
t 2 "sed -i on a memory"                          "sed -i 's/a/b/' ~/.claude/memory/prefer-subtraction.md"
t 2 "append to a skill"                           'echo "- extra" >> ~/.claude/skills/repo-vet/SKILL.md'
t 2 "tee into a project memory"                   'echo x | tee /home/x/.claude/projects/-home-x-proj/memory/y.md'
t 2 "python open(...,'w') form"                   $'python3 - <<\'PY\'\nopen("/home/x/.claude/skills/repo-vet/SKILL.md", "w").write(s)\nPY'
echo "MUST ALLOW — reads, bulk moves, and the index:"
t 0 "grep a memory"                               "grep -n foo ~/.claude/memory/verify-dont-anchor.md"
t 0 "cat a memory"                                'cat ~/.claude/memory/prefer-subtraction.md'
t 0 "sed -n read of a memory"                     "sed -n '1,20p' ~/.claude/memory/knowledge-routing.md"
t 0 "read a memory, redirect to /tmp"             'grep foo ~/.claude/memory/x.md > /tmp/out.txt'
t 0 "python READ of a memory"                     $'python3 - <<\'PY\'\nprint(open("/home/x/.claude/memory/x.md").read())\nPY'
t 0 "MEMORY.md index append (documented idiom)"   'echo "- [X](x.md) — hook" >> ~/.claude/memory/MEMORY.md'
t 0 "bulk cp OUT to a transfer bundle"            'cp ~/.claude/memory/*.md /tmp/claude-transfer/'
t 0 "bulk cp IN from a bundle"                    'cp /tmp/claude-transfer/x.md ~/.claude/memory/'
t 0 "write somewhere that is not a memory"        'echo hi > /tmp/scratch/notes.md'
# KNOWN OVER-TRIGGER, ASSERTED ON PURPOSE so the verdict is executable and nobody re-derives it.
# A skill path as a `cp` SOURCE plus a Python write to a SCRATCH path blocks, because the Python
# branch fires on the conjunction and cannot prove the two refer to one file. Narrowing it would
# need the path adjacent to the write, and the real shape puts the path in a variable — so the
# narrowing buys a false negative in exactly the case worth catching. Fires; the finding
# text was corrected to stop claiming a target it has not established. Split the command to proceed.
t 2 "cp SOURCE is a skill path + a python write to /tmp (over-trigger, deliberate)" $'cp ~/.claude/skills/shell-footguns/SKILL.md /tmp/x/ && python3 - <<PY\nimport pathlib\npathlib.Path("/tmp/x/out.md").write_text("hi")\nPY'
# The two halves separately must NOT block — that is what makes the case above a CONJUNCTION rule
# rather than either half being enough, and it is the control that would catch an over-broad edit.
t 0 "the cp half alone"                           'cp ~/.claude/skills/shell-footguns/SKILL.md /tmp/x/'
t 0 "the python-write half alone"                 $'python3 - <<PY\nimport pathlib\npathlib.Path("/tmp/x/out.md").write_text("hi")\nPY'

echo "glab-ci-list-b-is-a-date MUST BLOCK:"
# The measured case: `-b` guessed as --branch, silently an unparseable --updated-before.
t 2 "branch name after -b"              'glab ci list -b my-feature'
t 2 "quoted branch name"                'glab ci list -b "my-feature" | head -5'
t 2 "the pipeline alias"                'glab pipeline list -b main'
t 2 "with other flags around it"        'glab ci list --status=failed -b my-feature -p 1'
echo "glab-ci-list-b-is-a-date MUST ALLOW:"
# A REAL --updated-before. Blocking this would make the flag unusable, which is how a gate
# earns a reputation for false positives and gets switched off.
t 0 "an ISO 8601 date, which is valid"  'glab ci list -b 2026-01-01T00:00:00Z'
t 0 "a bare ISO date"                   'glab ci list -b 2026-09-13'
# A variable could hold a perfectly good date; the gate cannot know and must not guess.
t 0 "a variable value"                  'glab ci list -b "$SINCE"'
# The correct form this rule steers toward must never fire.
t 0 "the ref flag, which is the fix"    'glab ci list -r my-feature'
# -b on a DIFFERENT glab subcommand is a real branch flag and none of this applies.
t 0 "-b on another subcommand"          'glab mr list -b my-feature'

echo "NEW RULE — a value piped into ssh bash -s MUST BLOCK: [gate:ssh-bash-s-stdin]"
t 2 "value piped into bash -s with args"      'printf '"'"'%s\n'"'"' "$VAL" | ssh host bash -s -- --dry-run'
t 2 "echo piped into bash -s"                 'echo "$VAL" | ssh -o BatchMode=yes host bash -s'
t 2 "sh -s variant"                           'echo "$VAL" | ssh host sh -s'
t 2 "inside a longer chain"                   'set -e; printf '"'"'%s'"'"' "$VAL" | ssh host bash -s -- a b; echo done'

echo "MUST ALLOW — sending a real script, or letting a stdin consumer read it:"
t 0 "script file on stdin"                    'ssh host bash -s -- a b < /tmp/x/remote.sh'
t 0 "cat of a script file"                    'cat /tmp/x/remote.sh | ssh host bash -s'
t 0 "no stdin plumbing at all"                'ssh host bash -s'
# The sudo-drains-heredoc-stdin cases upstream are all heredocs into `bash -s`. This rule must not
# shadow them in either direction: its heredoc exclusion keeps it off their must-ALLOW cases, and
# their must-BLOCK case must still block for its own reason, not this one.
t 0 "heredoc into bash -s with no sudo"       $'ssh host \'bash -s\' <<\'EOS\'\nid\necho after\nEOS'
t 2 "heredoc WITH sudo still blocks (sudo rule, not this one)" $'ssh host \'bash -s\' <<\'EOS\'\nsudo -n id\necho after\nEOS'

echo "NEW RULE — command -v over ssh MUST BLOCK: [gate:ssh-command-v-path]"
t 2 "the shape that produced a false 'not installed'" 'ssh -o BatchMode=yes host "command -v claude"'
t 2 "which, same trap"                        'ssh host "which glab"'
t 2 "which, single-quoted remote command"     'ssh host '"'"'which vault'"'"''
t 2 "which opening a later statement"         'ssh host uptime; which glab'
t 2 "inside a longer remote script"           'ssh host "cd /tmp && command -v podman && echo ok"'

echo "MUST ALLOW — login shell, explicit path, or no ssh:"
t 0 "login shell DOES source the profile"     'ssh host '"'"'bash -lc "command -v claude"'"'"''
t 0 "explicit path test is the fix"           'ssh host "test -x \$HOME/.local/bin/claude && echo yes"'
t 0 "sourcing a profile first"                'ssh host "source ~/.profile && command -v claude"'
t 0 "command -v locally, no ssh"              'command -v claude'
t 0 "local which, no ssh"                     'which python3'
# MENTION VS USE, fixed on first contact: the rule as imported blocked a command that
# merely DOCUMENTED it — `ssh` inside an echo string, `command -v` inside a grep pattern, no ssh
# invocation anywhere. A real call has `ssh` bare, in command position; a mention has it quoted.
t 0 "grepping the skill for the rule's own subject" 'echo "any claim about command -v / ssh?"; grep -n "command -v\\|which " SKILL.md'
t 0 "ssh named only inside a quoted string"   'echo "use ssh here"; which python3'
# The twin: `command -v` quoted as ssh'"'"'s remote command is the REAL trap and must still block,
# which is why the fix blanks quotes for the ssh test only and not for the probe test.
t 2 "ssh bare, probe quoted as its argument"  'ssh host "command -v claude"'
# MENTION VS USE, SECOND SPELLING, fixed later. `which` is an English relative pronoun, so the
# probe test fired on ordinary prose whenever a real ssh ran in the same string. These are the shapes
# that must stay quiet; the block cases above are what stops the fix becoming a hole.
t 0 "the exact false positive: real ssh + prose 'which' in a grep" 'ssh host '"'"'sha256sum /x'"'"'; grep -c "trap 5, which sometimes wants" SKILL.md'
t 0 "real ssh + prose 'which' in an echo"     'ssh host uptime; echo "a value which changed"'
t 0 "prose 'which' after a comma, ssh earlier in a pipeline" 'ssh host cat /etc/os-release | grep -c "the id, which names the distro"'

echo "NEW RULE — exec fed stdin without -i MUST BLOCK: [gate:exec-stdin-without-i]"
t 2 "kubectl exec heredoc, no -i (a real case)" $'kubectl -n ns exec pod -c postgres -- psql -At <<\'EOF\'\nselect 1;\nEOF'
t 2 "kubectl exec < file"                     'kubectl exec pod -- psql -f - < q.sql'
t 2 "pipe into kubectl exec"                  'cat q.sql | kubectl exec pod -- psql'
t 2 "podman exec heredoc"                     $'podman exec pg psql <<EOF\nselect 1;\nEOF'
echo "MUST ALLOW — stdin attached, or no stdin:"
t 0 "kubectl exec -i heredoc"                 $'kubectl -n ns exec -i pod -- psql <<\'EOF\'\nselect 1;\nEOF'
t 0 "kubectl exec --stdin"                    'cat q.sql | kubectl exec --stdin pod -- psql'
t 0 "podman exec -i"                          'podman exec -i pg psql < q.sql'
t 0 "exec with no stdin, output piped out"    'kubectl exec pod -- psql -c "select 1" 2>&1 | grep x'
t 0 "exec mentioned inside a quoted string"   'echo "kubectl exec pod <<EOF"'

echo "volume-prune-unfiltered MUST BLOCK:"
t 2 "volume prune after rm"              'podman rm -f -v my-pg >/dev/null; podman volume prune -f >/dev/null 2>&1'
t 2 "docker volume prune"                'docker volume prune -f'
t 2 "system prune with volumes"          'podman system prune -a --volumes -f'
echo "volume-prune-unfiltered MUST ALLOW:"
t 0 "prune by label"                     'podman volume prune -f --filter label=agent=a1'
t 0 "one volume by name"                 'podman volume rm my-pg-data'
t 0 "system prune without volumes"       'podman system prune -f'
t 0 "listing volumes"                    'podman volume ls'

echo "preprinted-empty-verdict MUST BLOCK:"
t 2 "(empty above = not implemented)"   'grep -ric fooFeature src; echo "(empty above = not implemented)"'
t 2 "(empty = no X calls)"              'grep -rinE "api.example.com" src; echo "(empty = no API calls)"'
t 2 "(blank above = no wildcard)"       'dig +short nope.example.com; echo "(blank above = no wildcard)"'
t 2 "(no files listed above = clean)"   'grep -rilE someField "$DEST"; echo "(no files listed above = clean)"'
t 2 "means, not ="                      'find . -name x; echo "nothing above means it is unused"'
t 2 "dig probe + verdict"              'dig +short example.test; echo "(none = no records)"'
echo "preprinted-empty-verdict MUST ALLOW:"
t 0 "section header before a probe"     'echo "=== control: term that MUST exist ==="; grep -c foo f'
t 0 "=== nothing to do === header"      'grep -c foo f; echo "=== nothing to do ==="'
t 0 "reports a result, no verdict"      'grep foo f; echo "no matches found"'
t 0 "no emptiness word"                 'grep -c foo f; echo "count above"'
t 0 "verdict echo with no probe"        'echo "(empty = use the default)"'
t 0 "asserted control, not a gloss"     'grep foo f > out; test -s out || echo "PROBE BROKEN"'
t 0 "guarded success echo"              'grep -q foo f && echo "found"'

echo "SYNC — every gate rule is documented and vice versa:"
sync_out=$(python3 - <<'SYNCPY'
import os, re, pathlib
hook = pathlib.Path(os.environ["GATE"]).read_text()
# The catalog lives in references/ beside SKILL.md; a rule documented there is documented.
skill_md = pathlib.Path(os.environ["SKILL_MD"])
skill = "".join(p.read_text() for p in [skill_md, *sorted((skill_md.parent / "references").glob("*.md"))])
in_hook = set(re.findall(r"# RULE-ID: (\S+)", hook))
in_skill = set(re.findall(r"\[gate:([a-z0-9-]+)\]", skill))
bad = False
for r in sorted(in_hook - in_skill):
    print("  FAIL  gated but undocumented in the skill: %s" % r); bad = True
for r in sorted(in_skill - in_hook):
    print("  FAIL  the skill claims [gate:%s] but no such rule in the hook" % r); bad = True
if not bad:
    print("  PASS  %d rules, hook and skill docs agree" % len(in_hook))
raise SystemExit(1 if bad else 0)
SYNCPY
)
sync_rc=$?
echo "$sync_out"
if [ "$sync_rc" -eq 0 ]; then pass=$((pass+1)); else fail=$((fail+1)); fi

echo "SIZE — a command over 128 KiB is still gated:"
# The payload used to reach python through an env var; past MAX_ARG_STRLEN (128 KiB) exec failed with
# E2BIG and the gate exited 0. Built in python, because mkjson's argv has the same limit.
big_rc=$(python3 -c 'import json; print(json.dumps({"tool_name":"Bash","tool_input":{"command":"echo " + "x"*140000 + "\nfor f in $(find /data -name \"*.log\"); do tail -1 \"$f\"; done"}}))' \
  | bash "$GATE" >/dev/null 2>&1; echo $?)
if [ "$big_rc" -eq 2 ]; then echo "  PASS  (rc=2) 140 KB command with a gated pattern"; pass=$((pass+1))
else echo "  FAIL  (rc=$big_rc want=2) 140 KB command with a gated pattern"; fail=$((fail+1)); fi

echo
echo "pass=$pass fail=$fail"
[ "$fail" -eq 0 ]

