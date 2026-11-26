"""Per-test time gate: any test whose setup + call + teardown takes more than CEILING_S of
wall clock fails, so a slow test fails CI the day it appears. It applies to every
collected test, present and future. Save it as tests/time_gate.py, a module of its own, and
register it from tests/conftest.py; never merge it into conftest, where a hook conftest already
defines (pytest_runtest_setup, pytest_configure) is silently replaced by the second definition:

    from tests import time_gate
    def pytest_configure(config: pytest.Config) -> None:
        config.pluginmanager.register(time_gate, "time_gate")

Registered this way its hooks are global, so they also see a session fixture's setup, which
runs through hooks that see only rootdir conftests and plugins.

Wall clock over all three phases, because setup, teardown and waits are what a person
waits on; a CPU-only body gate let agents move cost into fixtures unseen.

A shared fixture (class, module, package or session scope) is timed on its own against
FIXTURE_CEILING_S, keyed by name, and taken out of the test's charge: under xdist the
first test to use it differs from run to run, so charging that test is random. Its
teardown still lands on the last user; keep shared teardowns cheap. The CI job's timeout
bounds the total.

Set the ceilings from a measurement plus generous headroom: unit tests take milliseconds,
so a second or two catches every real wait without crying wolf on a slow runner. Adopting it
into an existing suite, add a non-failing readout of every test over half the ceiling, as the
gate charges it (pytest's --durations include shared-fixture setup the gate subtracts), seed HELD
from that readout over several CI runs, and watch main's next few runs before calling it done:
one run under-holds, and a ceiling flaking on main skips the release. Never raise one to let
a test through; speed it up or split it. HELD and HELD_FIXTURES start
empty and may only shrink: each entry carries its own measured ceiling (worst seen run plus
headroom), so a held test can't quietly get slower, and an entry leaves when it's fixed. A
deliberately slow scheduled run sets TEST_CEILING_S and
FIXTURE_CEILING_S itself."""

import importlib
import os
import time

import pytest
from _pytest.runner import runtestprotocol

CEILING_S = float(os.environ.get("TEST_CEILING_S", "2.0"))
FIXTURE_CEILING_S = float(os.environ.get("FIXTURE_CEILING_S", "10.0"))
HELD: dict[str, float] = {}  # node id -> its own ceiling in seconds
HELD_FIXTURES: dict[str, float] = {}  # fixture name -> its own ceiling in seconds
SPENT_KEY = pytest.StashKey[float]()
SHARED_KEY = pytest.StashKey[float]()
OVER_KEY = pytest.StashKey[float]()  # the first timing, when it was over the ceiling
SLOW_ONCE = "time_gate_slow_once"


class Shared:
    """Seconds spent setting up shared fixtures, outermost only, so a shared fixture that
    requests another is not subtracted twice. Only `request.getfixturevalue` inside a shared
    fixture's body nests: pytest sets up DECLARED arguments before calling this hook, so a
    control built from declared arguments never reaches the depth guard."""

    depth = 0
    total = 0.0


def too_slow(nodeid: str, wall_s: float) -> bool:
    return wall_s > HELD.get(nodeid, CEILING_S)


def fixture_too_slow(name: str, wall_s: float) -> bool:
    return wall_s > HELD_FIXTURES.get(name, FIXTURE_CEILING_S)


def charge(item: pytest.Item, seconds: float) -> float:
    total = item.stash.get(SPENT_KEY, 0.0) + seconds
    item.stash[SPENT_KEY] = total
    return total


@pytest.hookimpl(wrapper=True)
def pytest_fixture_setup(fixturedef: pytest.FixtureDef[object]):
    if fixturedef.scope == "function":
        return (yield)
    Shared.depth += 1
    start = time.perf_counter()
    try:
        result = yield
    finally:
        spent = time.perf_counter() - start
        Shared.depth -= 1
        if Shared.depth == 0:
            Shared.total += spent
    if fixture_too_slow(fixturedef.argname, spent):
        pytest.fail(
            f"fixture {fixturedef.argname} ({fixturedef.scope} scope) took {spent:.2f}s to "
            f"set up, over the {FIXTURE_CEILING_S}s shared-fixture ceiling "
            f"(tests/time_gate.py): make it cheaper",
            pytrace=False,
        )
    return result


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item: pytest.Item):
    before = Shared.total
    yield
    item.stash[SHARED_KEY] = Shared.total - before


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    report = outcome.get_result()
    own = call.stop - call.start
    if call.when == "setup":
        own -= item.stash.get(SHARED_KEY, 0.0)
    spent = charge(item, own)
    if report.when == "teardown" and report.passed and too_slow(item.nodeid, spent):
        item.stash[OVER_KEY] = spent
        report.outcome = "failed"
        report.longrepr = (
            f"{item.nodeid} took {spent:.2f}s wall clock including setup and teardown "
            f"(shared fixtures excluded), over the {CEILING_S}s per-test ceiling "
            f"(tests/time_gate.py): speed it up or split it"
        )


def rearm_hang_guard(item: pytest.Item) -> None:
    """pytest-timeout's timer covers the whole protocol, so a second timing gets the full guard of its own."""
    hook = item.config.pluginmanager.hook
    if item.config.pluginmanager.has_plugin("timeout"):
        settings = importlib.import_module("pytest_timeout")._get_item_settings(item)
        if settings.timeout and not settings.func_only:
            hook.pytest_timeout_cancel_timer(item=item)
            hook.pytest_timeout_set_timer(item=item, settings=settings)


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: pytest.Item | None):
    """One noisy sample does not fail a test: a test that passes but for the ceiling is timed
    once more, in the same worker straight after (its fixtures set up again, shared ones kept).
    It fails only if the second timing is over too. Real failures and fixture ceilings are never
    retimed. Under xdist each worker retimes its own test, so the second timing is alone only
    within its process."""
    hook = item.ihook
    hook.pytest_runtest_logstart(nodeid=item.nodeid, location=item.location)
    reports = runtestprotocol(item, nextitem=nextitem, log=False)
    first = item.stash.get(OVER_KEY, None)
    if first is not None:
        del item.stash[OVER_KEY]
        if SPENT_KEY in item.stash:
            del item.stash[SPENT_KEY]
        rearm_hang_guard(item)
        reports = runtestprotocol(item, nextitem=nextitem, log=False)
        if OVER_KEY not in item.stash:
            call = next((r for r in reports if r.when == "call"), reports[-1])
            call.user_properties.append((SLOW_ONCE, f"{first:.2f}"))
    for report in reports:
        hook.pytest_runtest_logreport(report=report)
    hook.pytest_runtest_logfinish(nodeid=item.nodeid, location=item.location)
    return True


def pytest_terminal_summary(terminalreporter: pytest.TerminalReporter) -> None:
    """Tests over the ceiling on their first timing and under on the second: slow, not failed.
    Read this section over several runs; a test that keeps appearing is a test to speed up."""
    slow = [(r.nodeid, v) for r in terminalreporter.stats.get("passed", []) for k, v in r.user_properties
            if k == SLOW_ONCE]
    if slow:
        terminalreporter.section("time gate: slow once, passed on a second timing")
        for nodeid, first in slow:
            terminalreporter.write_line(f"{nodeid}: {first}s the first time, under {CEILING_S}s the second")


# Put these in tests/test_time_gate.py so the gate proves it can fail. Add two retime controls:
# one slow only on its first run passes and appears in the summary; one slow every run fails. A control that runs
# pytest in a subprocess takes seconds and trips the gate itself: run the subprocess once in
# a module-scoped fixture (timed as a shared fixture) and assert on its result per test.
#
# from tests import time_gate
# def test_over_the_ceiling_is_slow():
#     assert time_gate.too_slow("tests/x.py::t", time_gate.CEILING_S + 0.01)
# def test_under_the_ceiling_is_fine():
#     assert not time_gate.too_slow("tests/x.py::t", time_gate.CEILING_S)
# def test_a_slow_shared_fixture_is_slow():
#     assert time_gate.fixture_too_slow("tree", time_gate.FIXTURE_CEILING_S + 0.01)
# def test_a_held_test_is_bounded_by_its_own_ceiling(monkeypatch):
#     monkeypatch.setitem(time_gate.HELD, "tests/x.py::t", 5.0)
#     assert not time_gate.too_slow("tests/x.py::t", 4.9)
#     assert time_gate.too_slow("tests/x.py::t", 5.01)
#
# And one end-to-end control, run once by hand. Serially it must report 3 errors (the
# third is the last case below):
# test_slow_setup at teardown (a slow function fixture is the test's own cost) and the
# first test using `tree` at setup (a slow shared fixture, named), while
# test_uses_tree_again passes (the shared cost was not charged to it). Under `-n 2` the
# `tree` error appears once per worker that builds it. Needs pytest 8+ (wrapper=True).
#     TEST_CEILING_S=0.1 FIXTURE_CEILING_S=0.2 pytest tests/time_gate_control.py
# where tests/time_gate_control.py (not collected by default: no test_ prefix) holds:
#     import time, pytest
#     @pytest.fixture
#     def slow():
#         time.sleep(0.3)
#         yield
#     @pytest.fixture(scope="session")
#     def tree():
#         time.sleep(0.3)
#         return 1
#     def test_slow_setup(slow):
#         pass
#     def test_uses_tree(tree):
#         pass
#     def test_uses_tree_again(tree):
#         pass
#     def test_slow_after_the_shared_fixture(tree):   # must ALSO error at teardown
#         time.sleep(0.3)
# The last case catches bookkeeping bugs in the subtraction, which first-item controls miss.
# None of these reaches the nesting guard in `Shared`; a second run does. Add to the file a
# session fixture `inner` (sleep 0.15), a session fixture `outer(request)` that calls
# `request.getfixturevalue("inner")` then sleeps 0.15, a function fixture `fair` (sleep 0.2) and
# `def test_after_nested_shared(outer, fair): pass`; deselect it above (`-k "not nested"`) and
# require it to error under TEST_CEILING_S=0.1 FIXTURE_CEILING_S=10. Counted twice, its own
# 0.2 s vanishes under the ceiling. Prove the controls can fail: seed faults into the gate (drop
# the depth guard, subtract twice) and watch each one turn a control red.
