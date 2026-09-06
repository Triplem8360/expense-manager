"""Add authentication tables.

Revision ID: 20260906_02
Revises: 20260906_01
Create Date: 2026-09-06 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260906_02"
down_revision: str | Sequence[str] | None = "20260906_01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create users and refresh-session storage."""
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.true(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "email = lower(email)",
            name=op.f("ck_users_email_lowercase"),
        ),
        sa.CheckConstraint(
            "char_length(btrim(email)) > 3",
            name=op.f("ck_users_email_not_blank"),
        ),
        sa.CheckConstraint(
            "char_length(btrim(password_hash)) > 0",
            name=op.f("ck_users_password_hash_not_blank"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )

    op.create_table(
        "refresh_sessions",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "replaced_by_token_hash",
            sa.String(length=64),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name=op.f("ck_refresh_sessions_expiration_after_creation"),
        ),
        sa.CheckConstraint(
            "replaced_by_token_hash IS NULL "
            "OR char_length(replaced_by_token_hash) = 64",
            name=op.f("ck_refresh_sessions_replacement_hash_length"),
        ),
        sa.CheckConstraint(
            "char_length(token_hash) = 64",
            name=op.f("ck_refresh_sessions_token_hash_length"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_refresh_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_sessions")),
        sa.UniqueConstraint(
            "token_hash",
            name=op.f("uq_refresh_sessions_token_hash"),
        ),
    )
    op.create_index(
        op.f("ix_refresh_sessions_expires_at"),
        "refresh_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_refresh_sessions_user_id"),
        "refresh_sessions",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop authentication tables in dependency order."""
    op.drop_index(
        op.f("ix_refresh_sessions_user_id"),
        table_name="refresh_sessions",
    )
    op.drop_index(
        op.f("ix_refresh_sessions_expires_at"),
        table_name="refresh_sessions",
    )
    op.drop_table("refresh_sessions")
    op.drop_table("users")
