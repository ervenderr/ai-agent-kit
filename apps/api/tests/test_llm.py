"""LLM wrapper against a mocked HTTP transport: checks the request shape and response parsing."""

import json

import anthropic
import httpx2

from app.config import Settings
from app.llm.client import LLM, LLMResult

MESSAGE = {
    "id": "msg_1",
    "type": "message",
    "role": "assistant",
    "model": "claude-sonnet-5-5",
    "content": [
        {"type": "text", "text": "hi"},
        {"type": "tool_use", "id": "tu_1", "name": "calculate", "input": {"expression": "1+1"}},
    ],
    "stop_reason": "tool_use",
    "stop_sequence": None,
    "usage": {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 0},
}


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def stream_body() -> str:
    start = {**MESSAGE, "content": [], "stop_reason": None}
    return "".join(
        [
            sse("message_start", {"type": "message_start", "message": start}),
            sse(
                "content_block_start",
                {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}},
            ),
            sse(
                "content_block_delta",
                {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "hi"}},
            ),
            sse("content_block_stop", {"type": "content_block_stop", "index": 0}),
            sse(
                "message_delta",
                {
                    "type": "message_delta",
                    "delta": {"stop_reason": "end_turn", "stop_sequence": None},
                    "usage": {"output_tokens": 5},
                },
            ),
            sse("message_stop", {"type": "message_stop"}),
        ]
    )


def make_llm(seen: list[dict]) -> LLM:
    def handler(req: httpx2.Request) -> httpx2.Response:
        body = json.loads(req.content)
        seen.append(body)
        if body.get("stream"):
            return httpx2.Response(200, headers={"content-type": "text/event-stream"}, text=stream_body())
        return httpx2.Response(200, json=MESSAGE)

    client = anthropic.AsyncAnthropic(
        api_key="test", http_client=httpx2.AsyncClient(transport=httpx2.MockTransport(handler)), max_retries=0
    )
    return LLM(Settings(), client)


async def test_complete_sets_cache_breakpoints_and_parses():
    seen: list[dict] = []
    res = await make_llm(seen).complete([{"role": "user", "content": "x"}], [], "SYSTEM")
    assert seen[0]["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert seen[0]["cache_control"] == {"type": "ephemeral"} and seen[0]["max_tokens"] == 4096
    assert res.tool_calls[0].args == {"expression": "1+1"} and res.usage.cache_read_tokens == 100
    assert res.stop_reason == "tool_use"


async def test_stream_yields_deltas_then_result():
    items = [i async for i in make_llm([]).stream([{"role": "user", "content": "x"}], [], "SYSTEM")]
    assert items[0] == "hi" and isinstance(items[-1], LLMResult) and items[-1].stop_reason == "end_turn"
