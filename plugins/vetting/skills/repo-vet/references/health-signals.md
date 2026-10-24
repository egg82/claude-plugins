# Measuring maintenance health — how the headline numbers mislead

Open this when writing the health read (check 2).

**Measure health, don't eyeball it.** The headline numbers mislead in specific, checkable ways:
*contributor count* hides commit distribution (15 contributors is often 1 author plus 14 typo
fixes -- get per-person commit counts); *stars* measure how well a launch post did, not whether
anyone still runs it (in community threads, count people describing actual operation separately
from "looks cool, saved for later" -- they differ by an order of magnitude and only the first
predicts anything); *`pushed_at`* can be newer than the default branch's last real commit, so
side-branch or dependabot churn makes a stale project look alive -- compare them; *"0 open
issues"* can mean an auto-close bot, so read who closed them and how fast; and **who files the
issues** tells you whether external users exist at all -- but read it carefully, a tracker full of
maintainer-authored planning tickets can still have a healthy minority of real external reporters,
so count distinct outside humans and the response times rather than the ratio alone.
