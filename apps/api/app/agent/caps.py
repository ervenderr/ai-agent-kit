from dataclasses import dataclass
from typing import TYPE_CHECKING

from app.config import Settings

if TYPE_CHECKING:
    from app.agent.state import RunState


class CapExceeded(Exception):
    def __init__(self, kind: str):
        super().__init__(kind)
        self.kind = kind


@dataclass(frozen=True)
class Caps:
    """Hard limits enforced in code on every iteration. Nothing in a prompt can change them."""

    max_steps: int = 8
    max_tool_calls: int = 10
    max_seconds: float = 60.0
    max_input_tokens: int = 200_000
    max_cost_usd: float = 0.50
    max_arg_repairs: int = 1

    @classmethod
    def from_settings(cls, s: Settings) -> "Caps":
        return cls(
            s.cap_max_steps,
            s.cap_max_tool_calls,
            s.cap_max_seconds,
            s.cap_max_input_tokens,
            s.cap_max_cost_usd,
            s.cap_max_arg_repairs,
        )

    def check(self, state: "RunState", pending_tool_calls: int = 0) -> None:
        if state.steps >= self.max_steps:
            raise CapExceeded("steps")
        if state.tool_calls + pending_tool_calls > self.max_tool_calls:
            raise CapExceeded("tool_calls")
        if state.elapsed() > self.max_seconds:
            raise CapExceeded("seconds")
        if state.input_tokens > self.max_input_tokens:
            raise CapExceeded("input_tokens")
        if state.cost > self.max_cost_usd:
            raise CapExceeded("cost")
