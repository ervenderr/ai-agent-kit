"""users, notes, runs, messages, tool_calls

Revision ID: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("api_token", sa.String(64), nullable=False, unique=True),
        sa.Column("scopes", sa.JSON, nullable=False),
    )
    op.create_table(
        "notes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("body", sa.Text, nullable=False),
    )
    op.create_table(
        "runs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("input", sa.Text, nullable=False),
        sa.Column("final_output", sa.Text),
        sa.Column("cost", sa.Float, nullable=False),
        sa.Column("steps", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "messages",
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("idx", sa.Integer, primary_key=True),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("content", sa.JSON, nullable=False),
    )
    op.create_table(
        "tool_calls",
        sa.Column("run_id", sa.String(36), sa.ForeignKey("runs.id"), primary_key=True),
        sa.Column("idx", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("args", sa.JSON, nullable=False),
        sa.Column("result_size", sa.Integer, nullable=False),
        sa.Column("latency_ms", sa.Integer, nullable=False),
        sa.Column("error", sa.Text),
    )


def downgrade() -> None:
    for table in ("tool_calls", "messages", "runs", "notes", "users"):
        op.drop_table(table)
