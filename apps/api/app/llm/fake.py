"""Scripted stand-in for LLM: every test and CI eval runs on this, no API key needed."""

import asyncio
from collections.abc import AsyncIterator
from typing import Any

from app.llm.client import LLMResult, ToolCall, Usage


class FakeLLM:
    """Each script turn: {"text", "tool_calls": [{"id","name","args"}], "usage", "stop_reason", "delay"}."""

    def __init__(self, script: list[dict[str, Any]]):
        self._turns = iter(script)
        self.requests: list[list[dict[str, Any]]] = []

    def _next(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        self.requests.append(list(messages))
        try:
            return next(self._turns)
        except StopIteration:
            raise AssertionError("FakeLLM script exhausted: the loop made an unscripted call") from None

    @staticmethod
    def _result(turn: dict[str, Any]) -> LLMResult:
        text = turn.get("text", "")
        calls = [ToolCall(c["id"], c["name"], c["args"]) for c in turn.get("tool_calls", [])]
        content: list[dict[str, Any]] = [{"type": "text", "text": text}] if text else []
        content += [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.args} for c in calls]
        usage = Usage(**turn.get("usage", {"input_tokens": 100, "output_tokens": 20}))
        stop = turn.get("stop_reason", "tool_use" if calls else "end_turn")
        return LLMResult(text, calls, usage, stop, content, request_id="fake")

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], system: str, max_tokens: int | None = None
    ) -> LLMResult:
        turn = self._next(messages)
        await asyncio.sleep(turn.get("delay", 0))
        return self._result(turn)

    async def stream(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], system: str, max_tokens: int | None = None
    ) -> AsyncIterator[str | LLMResult]:
        turn = self._next(messages)
        for word in turn.get("text", "").split(" ")[:-1]:
            yield word + " "
        if turn.get("text"):
            yield turn["text"].split(" ")[-1]
        await asyncio.sleep(turn.get("delay", 0))
        yield self._result(turn)
