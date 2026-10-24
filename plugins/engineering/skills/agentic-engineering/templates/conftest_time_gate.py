"""Per-test time gate: any test whose call phase uses more than CEILING_S of CPU fails, so a
slow test fails CI the day it appears. It applies to every collected test, present
and future. Merge this into tests/conftest.py.

CPU seconds, not wall seconds. Wall time measures the runner as much as the test: a
slower CPU type or an overloaded shared runner fails fast tests, and a gate that cries
wolf gets switched off. CPU time (this process and its children, via os.times()) moves
far less. It is still not perfectly stable, for two reasons worth knowing before you
trust a red:
  - a lazily built process-level cache charges its whole cost to whichever test fills
    it first, so under xdist a test's seconds depend on the order its worker drew it.
    Build shared data in a fixture (fixture setup is not timed), or charge fills evenly.
  - on a host that is swapping, CPU seconds drift too. Where CI is that host, enforce
    only where TIME_GATE=1 is set and keep timing everywhere.
A test that WAITS (sleep, network, a lock) uses little CPU and passes; that is the
point, and wait-bound slowness belongs to a timeout, not this gate.

Set CEILING_S from a measurement plus headroom, and record that measurement here.
Never raise it to let a test through: speed the test up or split it. The usual
agent-made cause is quadratic re-computation (re-simulating from time zero per sample);
carry state forward instead. HELD lists node ids excused today, may only shrink, and
should start empty in a new repo. A deliberately slow scheduled run sets TEST_CEILING_S
itself."""

import os

import pytest

CEILING_S = float(os.environ.get("TEST_CEILING_S", "2.0"))
HELD: frozenset[str] = frozenset()
CPU_KEY = pytest.StashKey[float]()


def cpu_now() -> float:
    t = os.times()
    return t.user + t.system + t.children_user + t.children_system


def too_slow(nodeid: str, cpu_s: float) -> bool:
    return cpu_s > CEILING_S and nodeid not in HELD


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item: pytest.Item):
    start = cpu_now()
    yield
    item.stash[CPU_KEY] = cpu_now() - start


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    report = outcome.get_result()
    cpu_s = item.stash.get(CPU_KEY, None)
    if (
        report.when == "call"
        and report.passed
        and cpu_s is not None
        and too_slow(item.nodeid, cpu_s)
    ):
        report.outcome = "failed"
        report.longrepr = (
            f"{item.nodeid} used {cpu_s:.2f}s of CPU, "
            f"over the {CEILING_S}s per-test ceiling "
            f"(tests/conftest.py): speed it up or split it"
        )


# Put these in tests/test_time_gate.py so the gate proves it can fail:
#
# from tests import conftest
# def test_over_the_ceiling_is_slow():
#     assert conftest.too_slow("tests/x.py::t", conftest.CEILING_S + 0.01)
# def test_under_the_ceiling_is_fine():
#     assert not conftest.too_slow("tests/x.py::t", conftest.CEILING_S)
# def test_waiting_is_not_cpu():
#     import time
#     start = conftest.cpu_now(); time.sleep(0.3)
#     assert conftest.cpu_now() - start < 0.1
