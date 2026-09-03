"""create transactions and loans tables

Revision ID: 0003_transactions_loans
Revises: 0002_create_accounts
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_transactions_loans"
down_revision: str | None = "0002_create_accounts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "transactions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("account_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("destination_account_id", sa.Uuid(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["account_id"], ["accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["destination_account_id"], ["accounts.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_owner_id", "transactions", ["owner_id"])
    op.create_index("ix_transactions_account_id", "transactions", ["account_id"])
    op.create_table(
        "loans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("borrower_id", sa.Uuid(), nullable=False),
        sa.Column("lender_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["borrower_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lender_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_loans_borrower_id", "loans", ["borrower_id"])
    op.create_index("ix_loans_lender_id", "loans", ["lender_id"])


def downgrade() -> None:
    op.drop_index("ix_loans_lender_id", table_name="loans")
    op.drop_index("ix_loans_borrower_id", table_name="loans")
    op.drop_table("loans")
    op.drop_index("ix_transactions_account_id", table_name="transactions")
    op.drop_index("ix_transactions_owner_id", table_name="transactions")
    op.drop_table("transactions")
