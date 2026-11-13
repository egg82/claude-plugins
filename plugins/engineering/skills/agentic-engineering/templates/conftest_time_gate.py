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

import os
import time

import pytest

CEILING_S = float(os.environ.get("TEST_CEILING_S", "2.0"))
FIXTURE_CEILING_S = float(os.environ.get("FIXTURE_CEILING_S", "10.0"))
HELD: dict[str, float] = {}  # node id -> its own ceiling in seconds
HELD_FIXTURES: dict[str, float] = {}  # fixture name -> its own ceiling in seconds
SPENT_KEY = pytest.StashKey[float]()
SHARED_KEY = pytest.StashKey[float]()


class Shared:
    """Seconds spent setting up shared fixtures, outermost only, so a shared fixture that
    requests another is not subtracted twice."""

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
        report.outcome = "failed"
        report.longrepr = (
            f"{item.nodeid} took {spent:.2f}s wall clock including setup and teardown "
            f"(shared fixtures excluded), over the {CEILING_S}s per-test ceiling "
            f"(tests/time_gate.py): speed it up or split it"
        )


# Put these in tests/test_time_gate.py so the gate proves it can fail. A control that runs
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
