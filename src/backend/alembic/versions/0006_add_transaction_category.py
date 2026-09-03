"""add optional transaction category for budgets

Revision ID: 0006_add_transaction_category
Revises: 0005_add_planning_features
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_add_transaction_category"
down_revision: str | None = "0005_add_planning_features"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("transactions", sa.Column("category", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("transactions", "category")
