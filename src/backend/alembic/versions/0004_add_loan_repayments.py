"""add loan repayment requests

Revision ID: 0004_add_loan_repayments
Revises: 0003_transactions_loans
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_add_loan_repayments"
down_revision: str | None = "0003_transactions_loans"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "loan_repayments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("loan_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
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
        sa.ForeignKeyConstraint(["loan_id"], ["loans.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_loan_repayments_loan_id", "loan_repayments", ["loan_id"])


def downgrade() -> None:
    op.drop_index("ix_loan_repayments_loan_id", table_name="loan_repayments")
    op.drop_table("loan_repayments")
