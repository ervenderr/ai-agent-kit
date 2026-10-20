import asyncio

from sqlalchemy import select

from app.agent.state import create_run
from app.llm.fake import FakeLLM
from app.models import Run
from app.tools.base import ToolContext
from tests.fixtures import make_agent, run_to_end


async def test_final_answer_persists_run(db, settings, users):
    agent = make_agent(db, FakeLLM([{"text": "Hello there"}]), settings)
    res = await run_to_end(agent, db, users["alice"], "hi")
    assert res.last["type"] == "final"
    async with db() as s:
        run = await s.scalar(select(Run).where(Run.id == res.run_id))
    assert run and run.status == "completed" and run.final_output == "Hello there"


async def test_cancel_stops_inflight_llm_call(db, settings, users):
    llm = FakeLLM([{"text": "slow", "delay": 30}])
    agent = make_agent(db, llm, settings)
    state = await create_run(db, 1, "hi")
    events = []

    async def consume():
        async for e in agent.run("hi", ToolContext(users["alice"], db), state):
            events.append(e)

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.2)
    state.cancel.set()
    await asyncio.wait_for(task, timeout=2)  # would take 30s if the call were not interrupted
    assert events[-1]["code"] == "cancelled"
    async with db() as s:
        run = await s.get(Run, state.run_id)
    assert run and run.status == "cancelled"


async def test_client_disconnect_cancels_run(db, settings, users):
    agent = make_agent(db, FakeLLM([{"text": "slow", "delay": 30}]), settings)
    state = await create_run(db, 1, "hi")

    async def consume():
        async for _ in agent.run("hi", ToolContext(users["alice"], db), state):
            pass

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.2)
    task.cancel()  # what the server does when the SSE client goes away
    await asyncio.gather(task, return_exceptions=True)
    async with db() as s:
        run = await s.get(Run, state.run_id)
    assert run and run.status == "cancelled"


async def test_truncated_model_output_fails_loudly(db, settings, users):
    agent = make_agent(db, FakeLLM([{"text": "partial", "stop_reason": "max_tokens"}]), settings)
    res = await run_to_end(agent, db, users["alice"], "hi")
    assert res.last["code"] == "max_tokens"
