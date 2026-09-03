"""add idempotency payload fingerprint

Revision ID: 0010_add_idempotency_fingerprint
Revises: 0009_add_debts_installments
"""

import sqlalchemy as sa

from alembic import op

revision = "0010_add_idempotency_fingerprint"
down_revision = "0009_add_debts_installments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "idempotency_keys",
        sa.Column("fingerprint", sa.String(length=64), nullable=True),
    )
    op.execute("UPDATE idempotency_keys SET fingerprint = repeat('0', 64)")
    op.alter_column("idempotency_keys", "fingerprint", nullable=False)


def downgrade() -> None:
    op.drop_column("idempotency_keys", "fingerprint")
