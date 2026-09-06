from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from expense_api.db import Base
from expense_api.db.mixins import TimestampMixin
from expense_api.db.models.user import UserRecord


class RefreshSessionRecord(TimestampMixin, Base):
    __tablename__ = "refresh_sessions"
    __table_args__ = (
        CheckConstraint(
            "char_length(token_hash) = 64",
            name="token_hash_length",
        ),
        CheckConstraint(
            "replaced_by_token_hash IS NULL "
            "OR char_length(replaced_by_token_hash) = 64",
            name="replacement_hash_length",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="expiration_after_creation",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    replaced_by_token_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    user: Mapped[UserRecord] = relationship(
        back_populates="refresh_sessions",
        lazy="raise",
    )
