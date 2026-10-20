from typing import Any

from harness import LIVE_RESULTS

from tests.fixtures import db, settings, users  # noqa: F401


def pytest_terminal_summary(terminalreporter: Any) -> None:
    if LIVE_RESULTS:
        passed = sum(ok for _, ok, _ in LIVE_RESULTS)
        cost = sum(c for *_, c in LIVE_RESULTS)
        terminalreporter.write_line(f"LIVE EVALS pass rate: {passed}/{len(LIVE_RESULTS)}  cost: ${cost:.4f}")
        for case_id, ok, _ in LIVE_RESULTS:
            if not ok:
                terminalreporter.write_line(f"  FAILED: {case_id}")
