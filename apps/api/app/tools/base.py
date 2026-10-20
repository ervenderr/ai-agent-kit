from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, ConfigDict

from app.db import SessionFactory
from app.models import User

Kind = Literal["ok", "invalid_args", "unknown_tool", "permission", "confirmation", "error"]


class ToolArgs(BaseModel):
    """Base for tool args. Extra fields are rejected so the model cannot smuggle in e.g. a user_id."""

    model_config = ConfigDict(extra="forbid")


@dataclass
class ToolContext:
    user: User  # set by the server from the auth token, never by the model
    db: SessionFactory
    confirmed: bool = False  # human-in-the-loop hook: set True once a person approved side effects


@dataclass(frozen=True)
class ToolResult:
    content: Any
    is_error: bool = False
    final: bool = False  # the loop must stop; the model may not route around it
    kind: Kind = "ok"

    @classmethod
    def error(cls, message: str, *, final: bool = False, kind: Kind = "error") -> "ToolResult":
        return cls(message, is_error=True, final=final, kind=kind)


class Tool(ABC):
    name: ClassVar[str]
    description: ClassVar[str]
    args_model: ClassVar[type[ToolArgs]]
    scope: ClassVar[str]  # a user needs this in User.scopes
    side_effect: ClassVar[bool] = False

    @abstractmethod
    async def run(self, args: Any, ctx: ToolContext) -> ToolResult: ...

    @classmethod
    def definition(cls) -> dict[str, Any]:
        schema = cls.args_model.model_json_schema()
        schema.pop("title", None)
        return {"name": cls.name, "description": cls.description, "input_schema": schema}


def validation_message(exc: Any) -> str:
    return "; ".join(f"{'.'.join(map(str, e['loc'])) or 'args'}: {e['msg']}" for e in exc.errors(include_url=False))
