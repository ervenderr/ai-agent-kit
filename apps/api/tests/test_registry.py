from typing import Any

import pytest

from app.models import User
from app.tools.base import Tool, ToolArgs, ToolContext, ToolResult
from app.tools.examples import build_registry


class _Boom(Tool):
    name = "boom"
    description = "always fails"
    args_model = ToolArgs
    scope = "calc"

    async def run(self, args: Any, ctx: ToolContext) -> ToolResult:
        raise RuntimeError("secret internal detail")


class _Big(Tool):
    name = "big"
    description = "huge output"
    args_model = ToolArgs
    scope = "calc"

    async def run(self, args: Any, ctx: ToolContext) -> ToolResult:
        return ToolResult("x" * 10_000)


class _Write(Tool):
    name = "write"
    description = "changes data"
    args_model = ToolArgs
    scope = "notes:write"
    side_effect = True

    async def run(self, args: Any, ctx: ToolContext) -> ToolResult:
        return ToolResult("done")


@pytest.fixture
def reg(settings):
    return build_registry(settings, [_Boom(), _Big(), _Write()])


def ctx(db, user: User, confirmed: bool = False) -> ToolContext:
    return ToolContext(user, db, confirmed)


async def test_calculate_ok(reg, db, users):
    r = await reg.execute("calculate", {"expression": "(3+4)*2"}, ctx(db, users["alice"]))
    assert not r.is_error and "14" in r.content


async def test_calculate_rejects_code(reg, db, users):
    r = await reg.execute("calculate", {"expression": "__import__('os').system('id')"}, ctx(db, users["alice"]))
    assert r.is_error and not r.final


async def test_invalid_args_are_actionable(reg, db, users):
    r = await reg.execute("calculate", {"expr": "1+1"}, ctx(db, users["alice"]))
    assert r.kind == "invalid_args" and "expression" in r.content


async def test_extra_args_forbidden(reg, db, users):
    r = await reg.execute("search_notes", {"query": "x", "user_id": 2}, ctx(db, users["alice"]))
    assert r.kind == "invalid_args"


async def test_permission_error_is_final_and_checked_before_args(reg, db, users):
    r = await reg.execute("calculate", {"garbage": 1}, ctx(db, users["carol"]))
    assert r.kind == "permission" and r.final


async def test_side_effect_needs_confirmation(reg, db, users):
    assert (await reg.execute("write", {}, ctx(db, users["alice"]))).kind == "confirmation"
    assert (await reg.execute("write", {}, ctx(db, users["alice"], confirmed=True))).content == "done"


async def test_exceptions_do_not_leak_internals(reg, db, users):
    r = await reg.execute("boom", {}, ctx(db, users["alice"]))
    assert r.is_error and "secret internal detail" not in r.content


async def test_oversized_result_is_truncated(reg, db, users):
    r = await reg.execute("big", {}, ctx(db, users["alice"]))
    assert len(r.content) < 4200 and "truncated" in r.content


async def test_unknown_tool(reg, db, users):
    r = await reg.execute("nope", {}, ctx(db, users["alice"]))
    assert r.kind == "unknown_tool" and "calculate" in r.content


async def test_search_is_scoped_to_user(reg, db, users):
    mine = await reg.execute("search_notes", {"query": "Falcon"}, ctx(db, users["alice"]))
    theirs = await reg.execute("search_notes", {"query": "Falcon"}, ctx(db, users["bob"]))
    assert mine.content == "[]" and "Falcon" in theirs.content
