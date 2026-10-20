import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.db import SessionFactory
from app.llm.client import Usage
from app.models import Message, Run, ToolCallRow


@dataclass
class RunState:
    run_id: str
    user_id: int
    messages: list[dict[str, Any]] = field(default_factory=list)
    steps: int = 0
    tool_calls: int = 0
    input_tokens: int = 0
    cost: float = 0.0
    arg_errors: int = 0
    started: float = field(default_factory=time.monotonic)
    cancel: asyncio.Event = field(default_factory=asyncio.Event)
    _tool_idx: int = 0

    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def add_usage(self, usage: Usage, price_in: float, price_out: float) -> None:
        self.input_tokens += usage.total_input
        self.cost += usage.cost_usd(price_in, price_out)

    def next_tool_idx(self) -> int:
        self._tool_idx += 1
        return self._tool_idx - 1


async def create_run(db: SessionFactory, user_id: int, text: str) -> RunState:
    run_id = str(uuid.uuid4())
    async with db() as s:
        s.add(Run(id=run_id, user_id=user_id, status="running", input=text))
        await s.commit()
    return RunState(run_id, user_id)


async def save_message(db: SessionFactory, state: RunState, role: str, content: Any) -> None:
    async with db() as s:
        s.add(Message(run_id=state.run_id, idx=len(state.messages), role=role, content=content))
        await s.commit()
    state.messages.append({"role": role, "content": content})


async def save_tool_call(
    db: SessionFactory,
    state: RunState,
    name: str,
    args: dict[str, Any],
    size: int,
    latency_ms: int,
    error: str | None,
) -> None:
    async with db() as s:
        s.add(
            ToolCallRow(
                run_id=state.run_id,
                idx=state.next_tool_idx(),
                name=name,
                args=args,
                result_size=size,
                latency_ms=latency_ms,
                error=error,
            )
        )
        await s.commit()


async def finish_run(db: SessionFactory, state: RunState, status: str, final: str | None) -> None:
    async with db() as s:
        run = await s.get(Run, state.run_id)
        if run:
            run.status, run.final_output, run.cost, run.steps = (
                status,
                final,
                state.cost,
                state.steps,
            )
            await s.commit()
