from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, CheckConstraint, Identity, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_api.db import Base
from expense_api.db.mixins import TimestampMixin

if TYPE_CHECKING:
    from expense_api.db.models.refresh_session import RefreshSessionRecord


class UserRecord(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint(
            "char_length(btrim(email)) > 3",
            name="email_not_blank",
        ),
        CheckConstraint(
            "char_length(btrim(password_hash)) > 0",
            name="password_hash_not_blank",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )

    refresh_sessions: Mapped[list[RefreshSessionRecord]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )
