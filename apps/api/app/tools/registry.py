import json
import logging
from collections.abc import Iterable
from typing import Any

from pydantic import ValidationError

from app.tools.base import Tool, ToolContext, ToolResult, validation_message

log = logging.getLogger("tools")


class Registry:
    def __init__(self, tools: Iterable[Tool], max_result_chars: int = 4000):
        self._tools = {t.name: t for t in tools}
        self._max = max_result_chars

    def definitions(self) -> list[dict[str, Any]]:
        return [t.definition() for t in self._tools.values()]

    async def execute(self, name: str, raw_args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Authorize, then validate, then run. Never raises; every failure becomes a ToolResult."""
        tool = self._tools.get(name)
        if tool is None:
            known = ", ".join(self._tools)
            return ToolResult.error(f"Unknown tool '{name}'. Available: {known}.", kind="unknown_tool")
        # Authz is checked before args are parsed so a denied call reveals nothing about the schema.
        if tool.scope not in ctx.user.scopes:
            return ToolResult.error(f"You are not permitted to use {name}.", final=True, kind="permission")
        if tool.side_effect and not ctx.confirmed:
            msg = f"{name} changes data and needs human confirmation. It was not run."
            return ToolResult.error(msg, final=True, kind="confirmation")
        try:
            args = tool.args_model.model_validate(raw_args)
        except ValidationError as exc:
            msg = f"Invalid arguments for {name}: {validation_message(exc)}. Fix them and call again."
            return ToolResult.error(msg, kind="invalid_args")
        try:
            result = await tool.run(args, ctx)
        except Exception:
            log.exception("tool_failed name=%s user=%s", name, ctx.user.id)
            return ToolResult.error(f"{name} failed unexpectedly. Try different input or answer without it.")
        return self._truncate(result)

    def _truncate(self, result: ToolResult) -> ToolResult:
        text = result.content if isinstance(result.content, str) else json.dumps(result.content)
        if len(text) > self._max:
            text = f"{text[: self._max]}...[truncated {len(text) - self._max} chars]"
        return ToolResult(text, result.is_error, result.final, result.kind)
