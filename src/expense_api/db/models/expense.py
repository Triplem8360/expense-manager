from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_api.db import Base
from expense_api.db.mixins import TimestampMixin
from expense_api.db.models.category import CategoryRecord
from expense_api.db.models.payment_method import PaymentMethodRecord


class ExpenseRecord(TimestampMixin, Base):
    __tablename__ = "expenses"
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint(
            "currency ~ '^[A-Z]{3}$'",
            name="currency_format",
        ),
        CheckConstraint(
            "char_length(btrim(title)) > 0",
            name="title_not_blank",
        ),
        CheckConstraint(
            "char_length(btrim(description)) > 0",
            name="description_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    category_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    payment_method_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("payment_methods.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    merchant: Mapped[str | None] = mapped_column(String(200), nullable=True)
    spent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    category: Mapped[CategoryRecord] = relationship(
        back_populates="expenses",
        lazy="raise",
    )
    payment_method: Mapped[PaymentMethodRecord] = relationship(
        back_populates="expenses",
        lazy="raise",
    )
