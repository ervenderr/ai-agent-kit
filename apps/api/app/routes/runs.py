import json
from collections.abc import AsyncIterator
from contextlib import aclosing
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.agent.state import RunState, create_run
from app.auth import current_user
from app.models import Message, Run, ToolCallRow, User
from app.schemas import MessageOut, RunCreate, RunDetail, RunOut, ToolCallOut
from app.tools.base import ToolContext

router = APIRouter(prefix="/runs", tags=["runs"])
ACTIVE: dict[str, RunState] = {}  # in-process; use a shared store if you run more than one worker

CurrentUser = Annotated[User, Depends(current_user)]


def _sse(event: dict[str, Any]) -> str:
    return f"data: {json.dumps(event)}\n\n"


@router.post("")
async def start_run(body: RunCreate, user: CurrentUser, request: Request) -> StreamingResponse:
    app = request.app
    if sum(s.user_id == user.id for s in ACTIVE.values()) >= app.state.settings.max_concurrent_runs:
        raise HTTPException(429, "Too many runs in progress")
    state = await create_run(app.state.db, user.id, body.input)
    ACTIVE[state.run_id] = state
    ctx = ToolContext(user=user, db=app.state.db)

    async def events() -> AsyncIterator[str]:
        try:
            yield _sse({"type": "run", "run_id": state.run_id})
            # aclosing makes a client disconnect close the loop (and its upstream LLM stream) right away
            async with aclosing(app.state.agent.run(body.input, ctx, state)) as run:
                async for event in run:
                    yield _sse(event)
        finally:
            ACTIVE.pop(state.run_id, None)

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@router.get("/{run_id}", response_model=RunDetail)
async def get_run(run_id: str, user: CurrentUser, request: Request) -> RunDetail:
    async with request.app.state.db() as s:
        run = await s.scalar(select(Run).where(Run.id == run_id, Run.user_id == user.id))
        if run is None:
            raise HTTPException(404, "Run not found")
        msgs = (await s.scalars(select(Message).where(Message.run_id == run_id).order_by(Message.idx))).all()
        calls = (
            await s.scalars(select(ToolCallRow).where(ToolCallRow.run_id == run_id).order_by(ToolCallRow.idx))
        ).all()
    return RunDetail(
        **RunOut.model_validate(run).model_dump(),
        messages=[MessageOut.model_validate(m) for m in msgs],
        tool_calls=[ToolCallOut.model_validate(c) for c in calls],
    )


@router.post("/{run_id}/cancel")
async def cancel_run(run_id: str, user: CurrentUser) -> dict[str, str]:
    state = ACTIVE.get(run_id)
    if state is None or state.user_id != user.id:
        raise HTTPException(404, "No active run with that id")
    state.cancel.set()
    return {"status": "cancelling"}
