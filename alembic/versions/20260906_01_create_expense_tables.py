"""Create expense management tables.

Revision ID: 20260906_01
Revises:
Create Date: 2026-09-06 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260906_01"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create categories, payment methods, and expenses."""
    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column("description", sa.Text(), nullable=True),
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
            "char_length(btrim(name)) > 0",
            name=op.f("ck_categories_name_not_blank"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint("name", name=op.f("uq_categories_name")),
    )

    op.create_table(
        "payment_methods",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
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
            "code ~ '^[a-z][a-z0-9_]*$'",
            name=op.f("ck_payment_methods_code_format"),
        ),
        sa.CheckConstraint(
            "char_length(btrim(display_name)) > 0",
            name=op.f("ck_payment_methods_display_name_not_blank"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_payment_methods")),
        sa.UniqueConstraint(
            "code",
            name=op.f("uq_payment_methods_code"),
        ),
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.Column("payment_method_id", sa.BigInteger(), nullable=False),
        sa.Column("merchant", sa.String(length=200), nullable=True),
        sa.Column("spent_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
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
            "amount > 0",
            name=op.f("ck_expenses_amount_positive"),
        ),
        sa.CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name=op.f("ck_expenses_currency_format"),
        ),
        sa.CheckConstraint(
            "char_length(btrim(description)) > 0",
            name=op.f("ck_expenses_description_not_blank"),
        ),
        sa.CheckConstraint(
            "char_length(btrim(title)) > 0",
            name=op.f("ck_expenses_title_not_blank"),
        ),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["categories.id"],
            name=op.f("fk_expenses_category_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["payment_method_id"],
            ["payment_methods.id"],
            name=op.f("fk_expenses_payment_method_id_payment_methods"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_expenses")),
    )
    op.create_index(
        op.f("ix_expenses_category_id"),
        "expenses",
        ["category_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_expenses_payment_method_id"),
        "expenses",
        ["payment_method_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_expenses_spent_at"),
        "expenses",
        ["spent_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop expense management tables in dependency order."""
    op.drop_index(op.f("ix_expenses_spent_at"), table_name="expenses")
    op.drop_index(
        op.f("ix_expenses_payment_method_id"),
        table_name="expenses",
    )
    op.drop_index(op.f("ix_expenses_category_id"), table_name="expenses")
    op.drop_table("expenses")
    op.drop_table("payment_methods")
    op.drop_table("categories")
