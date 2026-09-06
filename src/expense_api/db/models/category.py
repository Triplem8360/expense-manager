from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, CheckConstraint, Identity, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_api.db import Base
from expense_api.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from expense_api.db.models.expense import ExpenseRecord


class CategoryRecord(TimestampMixin, Base):
    __tablename__ = "categories"
    __table_args__ = (
        CheckConstraint(
            "char_length(btrim(name)) > 0",
            name="name_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    expenses: Mapped[list[ExpenseRecord]] = relationship(
        back_populates="category",
        passive_deletes=True,
        lazy="raise",
    )
