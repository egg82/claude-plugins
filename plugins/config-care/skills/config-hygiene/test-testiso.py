"""Both-directions cases for check_test_isolation's mention-vs-use split.

Must-stay-quiet cases are verbatim lines from suites that are CORRECT; must-flag cases are real
writes under the real $HOME. Run: python3 test-testiso.py
"""
import importlib.util
import pathlib
import re
import sys

spec = importlib.util.spec_from_file_location(
    "hyg", str(pathlib.Path(__file__).resolve().parent / "hygiene.py"))
assert spec and spec.loader
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def flags(line):
    """Replicates the decision in check_test_isolation's loop body."""
    if not h._REAL_HOME.search(line):
        return False
    b = h._blank_quoted(line)
    return bool(h._MUTATES.search(b)
                or (h._REDIR.search(b) and h._redirect_writes_home(line))
                or (re.search(r"\b(cp|mv)\b", line) and h._copy_writes_home(line)))


MEM = "~/.claude/memory"
SKL = "~/.claude/skills"
HMEM = '"$HOME/.claude/memory'
HSKL = '"$HOME/.claude/skills'

CASES = [
    # --- must stay QUIET: real lines from suites that do not touch the real $HOME -------------
    (False, '{ say "x"; route ' + HMEM + '/foo.md"; }                  > "$TD/e.jsonl"',
     "real-home path as an ARGUMENT, redirect goes to a temp dir"),
    (False, 't 2 "cat > a new memory"   ' + repr('cat > ' + MEM + '/new-thing.md <<MD'),
     "fixture STRING handed to a gate, never executed"),
    (False, 't 2 "append to a skill"    ' + repr('echo "- extra" >> ' + SKL + '/repo-vet/SKILL.md'),
     "fixture string, quoted"),
    (False, 't 0 "index append"         ' + repr('echo "- [X](x.md)" >> ' + MEM + '/MEMORY.md'),
     "fixture string, quoted"),
    (False, 'cp "$HOME/.claude/hooks/x.sh" "$T/"',
     "staging a real installed file OUT — a read, not a write"),

    # --- must FLAG: genuine mutations of the real $HOME ---------------------------------------
    (True, 'echo "x" >> ' + MEM + '/foo.md',
     "unquoted redirect straight at the real home"),
    (True, 'cat > ' + HSKL + '/x/SKILL.md" <<EOF',
     "QUOTED target — the case a blanket quote-blank would have silenced"),
    (True, 'rm -f "$HOME/.claude/.detached-checked/$sid"',
     "verb branch: rm"),
    (True, 'mv "$T/x" "$HOME/.claude/y" 2>/dev/null',
     "cp/mv dest — must survive an unrelated 2> on the same line"),
    (True, 'touch ' + SKL + '/../agents/fixture.md',
     "verb branch: touch"),
]

bad = 0
for want, line, why in CASES:
    got = flags(line)
    ok = got == want
    bad += not ok
    print("  %s  %s :: %s" % ("PASS" if ok else "FAIL",
                              "flag " if want else "quiet", why))
    if not ok:
        print("        line: %s" % line[:100])

print("\n%d/%d cases" % (len(CASES) - bad, len(CASES)))
sys.exit(1 if bad else 0)
