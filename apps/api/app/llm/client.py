"""The only module that imports the provider SDK."""

import logging
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

import anthropic

from app.config import Settings

log = logging.getLogger("llm")


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    def __add__(self, o: "Usage") -> "Usage":
        return Usage(
            self.input_tokens + o.input_tokens,
            self.output_tokens + o.output_tokens,
            self.cache_read_tokens + o.cache_read_tokens,
            self.cache_write_tokens + o.cache_write_tokens,
        )

    @property
    def total_input(self) -> int:
        return self.input_tokens + self.cache_read_tokens + self.cache_write_tokens

    def cost_usd(self, price_in: float, price_out: float) -> float:
        # cache reads bill at ~0.1x and cache writes at ~1.25x of the input price
        weighted_in = self.input_tokens + 0.1 * self.cache_read_tokens + 1.25 * self.cache_write_tokens
        return (weighted_in * price_in + self.output_tokens * price_out) / 1_000_000


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    args: dict[str, Any]


@dataclass
class LLMResult:
    text: str
    tool_calls: list[ToolCall]
    usage: Usage
    stop_reason: str
    # Assistant content blocks exactly as the API returned them (thinking blocks must be replayed).
    content: list[dict[str, Any]] = field(default_factory=list)
    request_id: str | None = None


class LLM:
    def __init__(self, settings: Settings, client: anthropic.AsyncAnthropic | None = None):
        self._s = settings
        # The SDK retries connection errors, 408/409/429 and 5xx with exponential backoff.
        self._client = client or anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key or None,
            timeout=settings.llm_timeout_s,
            max_retries=settings.llm_max_retries,
        )

    def _params(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
        max_tokens: int | None,
    ) -> dict[str, Any]:
        return {
            "model": self._s.llm_model,
            "max_tokens": max_tokens or self._s.llm_max_tokens,
            "messages": messages,
            "tools": tools,
            # Tools render before system, so one breakpoint on system caches both.
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            # Auto-caches the growing conversation prefix between loop iterations.
            "cache_control": {"type": "ephemeral"},
        }

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
        max_tokens: int | None = None,
    ) -> LLMResult:
        started = time.monotonic()
        msg = await self._client.messages.create(**self._params(messages, tools, system, max_tokens))
        return self._finish(msg, started)

    async def stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        system: str,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str | LLMResult]:
        """Yields text deltas, then one final LLMResult carrying the tool calls."""
        started = time.monotonic()
        async with self._client.messages.stream(**self._params(messages, tools, system, max_tokens)) as s:
            async for delta in s.text_stream:
                yield delta
            msg = await s.get_final_message()
        yield self._finish(msg, started)

    def _finish(self, msg: anthropic.types.Message, started: float) -> LLMResult:
        u = msg.usage
        usage = Usage(
            u.input_tokens,
            u.output_tokens,
            u.cache_read_input_tokens or 0,
            u.cache_creation_input_tokens or 0,
        )
        result = LLMResult(
            text="".join(b.text for b in msg.content if b.type == "text"),
            tool_calls=[ToolCall(b.id, b.name, dict(b.input)) for b in msg.content if b.type == "tool_use"],
            usage=usage,
            stop_reason=msg.stop_reason or "end_turn",
            content=[b.model_dump(exclude_none=True) for b in msg.content],
            request_id=getattr(msg, "_request_id", None),
        )
        log.info(
            "llm_call request_id=%s model=%s in=%d out=%d cache_read=%d cache_write=%d latency_ms=%d tool_calls=%d",
            result.request_id,
            self._s.llm_model,
            usage.input_tokens,
            usage.output_tokens,
            usage.cache_read_tokens,
            usage.cache_write_tokens,
            int((time.monotonic() - started) * 1000),
            len(result.tool_calls),
        )
        return result
