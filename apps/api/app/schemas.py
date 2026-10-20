from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RunCreate(BaseModel):
    input: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    idx: int
    role: str
    content: Any


class ToolCallOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    idx: int
    name: str
    args: Any
    result_size: int
    latency_ms: int
    error: str | None


class RunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    status: str
    input: str
    final_output: str | None
    cost: float
    steps: int
    created_at: datetime


class RunDetail(RunOut):
    messages: list[MessageOut]
    tool_calls: list[ToolCallOut]
