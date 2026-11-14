#!/usr/bin/env python3
"""Show the SHAPE of secret-bearing text (env lines, URLs, configs) without its values.

    python3 -I mask-values.py < file
    some-command | python3 -I mask-values.py

Every run of letters and digits becomes <N> (its length) unless it is all lower-case letters, at
most 8 long, and not pure hex (keeps `https`, `api`, `token`, `host`, `user`; masks `deadbeef`). A
digit anywhere masks the run, so
the short dashed groups of a UUID token (`1a2b-3c4d`) are hidden, which a `{6,}` length filter is not.
"""
import re
import sys

RUN = re.compile(r"[A-Za-z0-9]+")


def mask(m: "re.Match[str]") -> str:
    s = m.group(0)
    if s.isalpha() and s.islower() and len(s) <= 8 and re.search("[g-z]", s):
        return s
    return "<%d>" % len(s)


for line in sys.stdin:
    sys.stdout.write(RUN.sub(mask, line))
