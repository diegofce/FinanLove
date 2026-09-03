"""add budgets, saving goals, and notifications

Revision ID: 0005_add_planning_features
Revises: 0004_add_loan_repayments
"""

from collections.abc import Sequence
from typing import cast

import sqlalchemy as sa
from sqlalchemy.schema import SchemaItem

from alembic import op

revision: str = "0005_add_planning_features"
down_revision: str | None = "0004_add_loan_repayments"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table, columns in {
        "budgets": [
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "owner_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("category", sa.String(100), nullable=False),
            sa.Column("period_start", sa.Date(), nullable=False),
            sa.Column("period_end", sa.Date(), nullable=False),
            sa.Column("limit_amount", sa.Numeric(14, 2), nullable=False),
            sa.Column(
                "spent_amount", sa.Numeric(14, 2), nullable=False, server_default="0"
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        ],
        "saving_goals": [
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "owner_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(100), nullable=False),
            sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
            sa.Column(
                "contributed_amount",
                sa.Numeric(14, 2),
                nullable=False,
                server_default="0",
            ),
            sa.Column("deadline", sa.Date(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        ],
        "notifications": [
            sa.Column("id", sa.Uuid(), primary_key=True),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("title", sa.String(150), nullable=False),
            sa.Column("message", sa.String(500), nullable=False),
            sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        ],
    }.items():
        op.create_table(table, *cast(list[SchemaItem], columns))
        index_name = (
            f"ix_{table}_owner_id"
            if table != "notifications"
            else "ix_notifications_user_id"
        )
        index_column = "owner_id" if table != "notifications" else "user_id"
        op.create_index(index_name, table, [index_column])


def downgrade() -> None:
    for table in ("notifications", "saving_goals", "budgets"):
        op.drop_table(table)
