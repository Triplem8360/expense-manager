from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, Identity, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_api.db import Base
from expense_api.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from expense_api.db.models.expense import ExpenseRecord


class PaymentMethodRecord(TimestampMixin, Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        CheckConstraint(
            "code ~ '^[a-z][a-z0-9_]*$'",
            name="code_format",
        ),
        CheckConstraint(
            "char_length(btrim(display_name)) > 0",
            name="display_name_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)

    expenses: Mapped[list[ExpenseRecord]] = relationship(
        back_populates="payment_method",
        passive_deletes=True,
        lazy="raise",
    )
