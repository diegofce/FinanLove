"""add reusable categories and recurring transaction templates

Revision ID: 0007_categories_recurring
Revises: 0006_add_transaction_category
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0007_categories_recurring"
down_revision: str | None = "0006_add_transaction_category"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_categories_owner_id", "categories", ["owner_id"])
    op.create_table(
        "recurring_transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("frequency", sa.String(length=20), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_recurring_transactions_owner_id",
        "recurring_transactions",
        ["owner_id"],
    )
    op.create_index(
        "ix_recurring_transactions_account_id",
        "recurring_transactions",
        ["account_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recurring_transactions_account_id", table_name="recurring_transactions"
    )
    op.drop_index(
        "ix_recurring_transactions_owner_id", table_name="recurring_transactions"
    )
    op.drop_table("recurring_transactions")
    op.drop_index("ix_categories_owner_id", table_name="categories")
    op.drop_table("categories")
