"""add persistent idempotency keys

Revision ID: 0008_add_idempotency_keys
Revises: 0007_categories_recurring
"""

import sqlalchemy as sa

from alembic import op

revision = "0008_add_idempotency_keys"
down_revision = "0007_categories_recurring"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_keys",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column("operation", sa.String(length=100), nullable=False),
        sa.Column("response_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "key", "operation"),
    )
    op.create_index("ix_idempotency_keys_owner_id",
                    "idempotency_keys", ["owner_id"])
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=20),
                  nullable=False, server_default="USER"),
    )
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "is_revoked", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.add_column("loans", sa.Column(
        "lender_account_id", sa.Uuid(), nullable=True))
    op.add_column("loans", sa.Column(
        "borrower_account_id", sa.Uuid(), nullable=True))


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_column("users", "role")
    op.drop_column("loans", "borrower_account_id")
    op.drop_column("loans", "lender_account_id")
    op.drop_index("ix_idempotency_keys_owner_id",
                  table_name="idempotency_keys")
    op.drop_table("idempotency_keys")
