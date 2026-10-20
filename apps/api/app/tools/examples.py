import ast
import operator
from typing import Any

from pydantic import Field
from sqlalchemy import func, select

from app.config import Settings
from app.models import Note
from app.tools.base import Tool, ToolArgs, ToolContext, ToolResult
from app.tools.registry import Registry


class SearchNotesArgs(ToolArgs):
    query: str = Field(min_length=1, max_length=200, description="Words to look for in note titles and bodies.")
    limit: int = Field(default=5, ge=1, le=10, description="Maximum notes to return.")


class SearchNotes(Tool):
    name = "search_notes"
    description = (
        "Full-text search over the user's own notes. Use it when the answer may be in their saved notes; "
        "do not use it for general knowledge. Returns id, title and a snippet per note."
    )
    args_model = SearchNotesArgs
    scope = "notes:read"

    async def run(self, args: SearchNotesArgs, ctx: ToolContext) -> ToolResult:
        async with ctx.db() as s:
            stmt = select(Note).where(Note.user_id == ctx.user.id)  # tenant scope comes from ctx, not args
            if s.get_bind().dialect.name == "postgresql":
                doc = func.to_tsvector("english", Note.title + " " + Note.body)
                tsq = func.plainto_tsquery("english", args.query)
                stmt = stmt.where(doc.op("@@")(tsq)).order_by(func.ts_rank(doc, tsq).desc())
            else:  # SQLite in tests: no full-text, substring match instead
                stmt = stmt.where(Note.body.ilike(f"%{args.query}%") | Note.title.ilike(f"%{args.query}%"))
            notes = (await s.scalars(stmt.limit(args.limit))).all()
        return ToolResult([{"id": n.id, "title": n.title, "snippet": n.body[:300]} for n in notes])


_BIN = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd | ast.USub):
        v = _eval(node.operand)
        return v if isinstance(node.op, ast.UAdd) else -v
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return _BIN[type(node.op)](left, right)
    raise ValueError("only numbers and + - * / // % ** are allowed")


class CalculateArgs(ToolArgs):
    expression: str = Field(min_length=1, max_length=200, description="Arithmetic such as '(3 + 4) * 2.5'.")


class Calculate(Tool):
    name = "calculate"
    description = "Evaluate an arithmetic expression exactly. Use it for any non-trivial math instead of estimating."
    args_model = CalculateArgs
    scope = "calc"

    async def run(self, args: CalculateArgs, ctx: ToolContext) -> ToolResult:
        try:
            return ToolResult({"result": _eval(ast.parse(args.expression, mode="eval").body)})
        except (ValueError, SyntaxError, ZeroDivisionError, OverflowError) as exc:
            return ToolResult.error(f"Cannot calculate: {exc}. Rewrite the expression and try again.")


def build_registry(settings: Settings, extra: list[Any] | None = None) -> Registry:
    return Registry([SearchNotes(), Calculate(), *(extra or [])], settings.tool_result_max_chars)
