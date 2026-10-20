import logging
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent.caps import Caps
from app.agent.loop import Agent, LLMLike
from app.agent.prompts import load_system_prompt
from app.config import Settings, get_settings
from app.db import SessionFactory, make_session_factory
from app.llm.client import LLM
from app.routes import runs
from app.tools.examples import build_registry

logging.basicConfig(level=logging.INFO)


def create_app(
    settings: Settings | None = None,
    llm: LLMLike | None = None,
    db: SessionFactory | None = None,
    extra_tools: list[Any] | None = None,
) -> FastAPI:
    s = settings or get_settings()
    app = FastAPI(title="agent-api")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.state.settings = s
    app.state.db = db or make_session_factory(s)
    app.state.agent = Agent(
        llm=llm or LLM(s),
        registry=build_registry(s, extra_tools),
        caps=Caps.from_settings(s),
        system=load_system_prompt(),
        db=app.state.db,
        price_in=s.price_in_per_mtok,
        price_out=s.price_out_per_mtok,
    )
    app.include_router(runs.router)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
