"""add debts and installments

Revision ID: 0009_add_debts_installments
Revises: 0008_add_idempotency_keys
"""

import sqlalchemy as sa

from alembic import op

revision = "0009_add_debts_installments"
down_revision = "0008_add_idempotency_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "debts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("creditor", sa.String(150), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("description", sa.String(255), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(20),
                  nullable=False, server_default="OPEN"),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_debts_owner_id", "debts", ["owner_id"])
    op.create_table(
        "installments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("debt_id", sa.Uuid(), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(20),
                  nullable=False, server_default="OPEN"),
        sa.ForeignKeyConstraint(["debt_id"], ["debts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_installments_debt_id", "installments", ["debt_id"])


def downgrade() -> None:
    op.drop_index("ix_installments_debt_id", table_name="installments")
    op.drop_table("installments")
    op.drop_index("ix_debts_owner_id", table_name="debts")
    op.drop_table("debts")
