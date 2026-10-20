"""Shared fixtures for tests/ and evals/ (both conftests re-export these)."""

import json
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.agent.caps import Caps
from app.agent.loop import Agent, LLMLike
from app.agent.prompts import load_system_prompt
from app.agent.state import create_run
from app.config import Settings
from app.db import SessionFactory
from app.models import Base, Note, User
from app.tools.base import ToolContext
from app.tools.examples import build_registry

CANARY = "CANARY-9d41"
SCOPES = ["notes:read", "calc", "notes:write"]


@pytest.fixture
def settings() -> Settings:
    return Settings(anthropic_api_key="", database_url="sqlite+aiosqlite://")


@pytest.fixture
async def db(tmp_path: Path) -> AsyncIterator[SessionFactory]:
    # CI sets TEST_DATABASE_URL to Postgres so the full-text path runs; locally it falls back to SQLite.
    engine = create_async_engine(os.getenv("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{tmp_path}/test.db")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        s.add_all(
            [
                User(id=1, email="alice@example.com", api_token="tok-alice", scopes=SCOPES),
                User(id=2, email="bob@example.com", api_token="tok-bob", scopes=SCOPES),
                User(id=3, email="carol@example.com", api_token="tok-carol", scopes=[]),
            ]
        )
        await s.flush()  # users first: Postgres enforces the notes -> users foreign key
        s.add_all(
            [
                Note(user_id=1, title="Groceries", body="Milk, eggs, bread. Budget 12 dollars."),
                Note(user_id=1, title="Reading", body="Finish the book on distributed systems."),
                Note(user_id=2, title="Launch", body=f"{CANARY} Project Falcon launch plan."),
            ]
        )
        await s.commit()
    yield factory
    await engine.dispose()


@pytest.fixture
async def users(db: SessionFactory) -> dict[str, User]:
    async with db() as s:
        return {u.email.split("@")[0]: u for u in [await s.get(User, i) for i in (1, 2, 3)] if u}


@dataclass
class RunResult:
    events: list[dict[str, Any]] = field(default_factory=list)
    run_id: str = ""

    @property
    def last(self) -> dict[str, Any]:
        return self.events[-1]

    @property
    def tools(self) -> list[str]:
        return [e["name"] for e in self.events if e["type"] == "tool_call"]

    @property
    def status(self) -> str:
        return "completed" if self.last["type"] == "final" else "failed"

    @property
    def text(self) -> str:
        return json.dumps(self.events)


def make_agent(db: SessionFactory, llm: LLMLike, settings: Settings, caps: Caps | None = None,
               extra_tools: list[Any] | None = None) -> Agent:  # fmt: skip
    return Agent(llm, build_registry(settings, extra_tools), caps or Caps.from_settings(settings),
                 load_system_prompt(), db, settings.price_in_per_mtok, settings.price_out_per_mtok)  # fmt: skip


async def run_to_end(agent: Agent, db: SessionFactory, user: User, text: str, confirmed: bool = False) -> RunResult:
    state = await create_run(db, user.id, text)
    result = RunResult(run_id=state.run_id)
    async for event in agent.run(text, ToolContext(user, db, confirmed), state):
        result.events.append(event)
    return result
