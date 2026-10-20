import asyncio
import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Protocol

from app.agent.caps import CapExceeded, Caps
from app.agent.state import RunState, finish_run, save_message, save_tool_call
from app.db import SessionFactory
from app.llm.client import LLMResult, ToolCall
from app.tools.base import ToolContext, ToolResult
from app.tools.registry import Registry

log = logging.getLogger("agent")
PREVIEW_CHARS = 500


class LLMLike(Protocol):
    def stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str | LLMResult]: ...


def _error(state: RunState, code: str, message: str) -> dict[str, Any]:
    return {"type": "error", "code": code, "message": message, "steps": state.steps}


class Cancelled(Exception):
    pass


class AgentError(Exception):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


async def _until_cancelled(agen: AsyncIterator[Any], cancel: asyncio.Event) -> AsyncIterator[Any]:
    """Re-yield `agen`, but stop waiting on it the moment `cancel` is set (closing the HTTP stream)."""
    stop = asyncio.ensure_future(cancel.wait())
    nxt: asyncio.Future[Any] | None = None
    try:
        while True:
            nxt = asyncio.ensure_future(anext(agen))
            await asyncio.wait({nxt, stop}, return_when=asyncio.FIRST_COMPLETED)
            if not nxt.done():
                raise Cancelled
            try:
                item = nxt.result()
            except StopAsyncIteration:
                return
            yield item
    finally:
        pending = [t for t in (nxt, stop) if t is not None]
        for t in pending:
            t.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        await agen.aclose()  # type: ignore[attr-defined]


@dataclass
class Agent:
    llm: LLMLike
    registry: Registry
    caps: Caps
    system: str
    db: SessionFactory
    price_in: float
    price_out: float

    async def run(self, text: str, ctx: ToolContext, state: RunState) -> AsyncIterator[dict[str, Any]]:
        """Gather -> act -> verify loop. Yields events; always ends with `final` or `error`."""
        status, final = "failed", None
        try:
            await save_message(self.db, state, "user", text)
            while True:
                self.caps.check(state)
                result = None
                stream = self.llm.stream(state.messages, self.registry.definitions(), self.system)
                async for item in _until_cancelled(stream, state.cancel):
                    if isinstance(item, str):
                        yield {"type": "text_delta", "text": item}
                    else:
                        result = item
                assert result is not None, "LLM stream ended without a final result"
                state.steps += 1
                state.add_usage(result.usage, self.price_in, self.price_out)
                await save_message(self.db, state, "assistant", result.content)
                if result.stop_reason in ("max_tokens", "refusal"):
                    raise AgentError(result.stop_reason, f"Model stopped early ({result.stop_reason}).")
                if not result.tool_calls:
                    final, status = result.text, "completed"
                    yield {
                        "type": "final",
                        "text": final,
                        "steps": state.steps,
                        "cost_usd": round(state.cost, 6),
                    }
                    return
                async for event in self._act(result.tool_calls, ctx, state):
                    yield event
        except CapExceeded as exc:
            yield {
                "type": "error",
                "code": f"cap_exceeded:{exc.kind}",
                "message": f"Run stopped: {exc.kind} cap reached.",
            }
        except AgentError as exc:
            yield _error(state, exc.code, str(exc))
        except Cancelled:
            status = "cancelled"
            yield _error(state, "cancelled", "Run cancelled.")
        except (asyncio.CancelledError, GeneratorExit):  # client disconnected
            status = "cancelled"
            raise
        except Exception:
            log.exception("run_failed run_id=%s", state.run_id)
            yield _error(state, "internal", "The run failed unexpectedly.")
        finally:
            await finish_run(self.db, state, status, final)

    async def _act(self, calls: list[ToolCall], ctx: ToolContext, state: RunState) -> AsyncIterator[dict[str, Any]]:
        self.caps.check(state, pending_tool_calls=len(calls))
        state.tool_calls += len(calls)
        for c in calls:
            yield {"type": "tool_call", "id": c.id, "name": c.name, "args": c.args}
        outcomes = await asyncio.gather(*(self._timed(c, ctx) for c in calls))  # independent calls run in parallel
        blocks, denied = [], None
        for call, (res, ms) in zip(calls, outcomes, strict=True):
            size = len(res.content)
            await save_tool_call(
                self.db,
                state,
                call.name,
                call.args,
                size,
                ms,
                res.content if res.is_error else None,
            )
            blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": call.id,
                    "content": res.content,
                    "is_error": res.is_error,
                }
            )
            state.arg_errors += res.kind == "invalid_args"
            denied = denied or (res if res.final else None)
            yield {
                "type": "tool_result",
                "id": call.id,
                "name": call.name,
                "result_size": size,
                "latency_ms": ms,
                "is_error": res.is_error,
                "preview": res.content[:PREVIEW_CHARS],
            }
        await save_message(self.db, state, "user", blocks)
        if denied:  # a final error ends the run; the model may not retry around it
            code = "tool_denied" if denied.kind == "permission" else "confirmation_required"
            raise AgentError(code, str(denied.content))
        if state.arg_errors > self.caps.max_arg_repairs:
            raise AgentError("invalid_tool_args", "The model kept sending invalid tool arguments.")

    async def _timed(self, call: ToolCall, ctx: ToolContext) -> tuple[ToolResult, int]:
        started = time.monotonic()
        res = await self.registry.execute(call.name, call.args, ctx)
        ms = int((time.monotonic() - started) * 1000)
        log.info(
            "tool_call run_user=%s name=%s kind=%s ms=%d size=%d",
            ctx.user.id,
            call.name,
            res.kind,
            ms,
            len(res.content),
        )
        return res, ms
