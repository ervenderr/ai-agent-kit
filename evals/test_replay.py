"""Every golden case through the real loop with a scripted FakeLLM: deterministic, free, runs in CI."""

import pytest
from harness import LIVE, LIVE_RESULTS, check, load_cases

from app.agent.caps import Caps
from app.llm.client import LLM
from app.llm.fake import FakeLLM
from tests.fixtures import make_agent, run_to_end

CASES = load_cases()


def _caps(settings, case):
    return Caps(**{**Caps.from_settings(settings).__dict__, **case.get("caps", {})})


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["id"])
async def test_replay(case, db, settings, users):
    agent = make_agent(db, FakeLLM(case["script"]), settings, _caps(settings, case))
    res = await run_to_end(agent, db, users[case["user"]], case["input"])
    assert check(case["expect"], res) == []


@pytest.mark.live
@pytest.mark.skipif(not LIVE, reason="set LIVE_EVALS=1 to call the real model (costs money)")
@pytest.mark.parametrize("case", [c for c in CASES if c.get("live", True)], ids=lambda c: c["id"])
async def test_live(case, db, settings, users):
    settings = type(settings)()  # real env: ANTHROPIC_API_KEY, model, price
    agent = make_agent(db, LLM(settings), settings, _caps(settings, case))
    res = await run_to_end(agent, db, users[case["user"]], case["input"])
    problems = check(case["expect"], res, live=True)
    LIVE_RESULTS.append((case["id"], not problems, res.last.get("cost_usd", 0.0)))
    assert problems == []
