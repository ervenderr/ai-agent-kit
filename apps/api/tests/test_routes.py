import json

import httpx
import pytest

from app.llm.fake import FakeLLM
from app.main import create_app
from app.routes import runs


@pytest.fixture
async def client(db, settings):
    app = create_app(settings, FakeLLM([{"text": "Hi alice"}]), db)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app), base_url="http://t") as c:
        yield c


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def test_requires_auth(client):
    assert (await client.post("/runs", json={"input": "hi"})).status_code == 401
    assert (await client.post("/runs", json={"input": "hi"}, headers=auth("nope"))).status_code == 401


async def test_stream_then_replay_is_user_scoped(client):
    r = await client.post("/runs", json={"input": "hi"}, headers=auth("tok-alice"))
    events = [json.loads(line[6:]) for line in r.text.splitlines() if line.startswith("data: ")]
    assert [e["type"] for e in events][0] == "run" and events[-1]["type"] == "final"
    run_id = events[0]["run_id"]
    mine = await client.get(f"/runs/{run_id}", headers=auth("tok-alice"))
    assert mine.status_code == 200 and mine.json()["messages"][0]["role"] == "user"
    assert (await client.get(f"/runs/{run_id}", headers=auth("tok-bob"))).status_code == 404


async def test_cancel_unknown_run_is_404(client):
    assert (await client.post("/runs/nope/cancel", headers=auth("tok-alice"))).status_code == 404


async def test_concurrency_limit(client, settings):
    for i in range(settings.max_concurrent_runs):
        runs.ACTIVE[f"x{i}"] = runs.RunState(f"x{i}", 1)
    try:
        r = await client.post("/runs", json={"input": "hi"}, headers=auth("tok-alice"))
        assert r.status_code == 429
    finally:
        runs.ACTIVE.clear()
