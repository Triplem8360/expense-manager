from __future__ import annotations

from datetime import datetime
from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from expense_api.db.models import RefreshSessionRecord, UserRecord
from expense_api.models import UserCredentialsModel, UserModel

type RefreshRotationStatus = Literal[
    "rotated",
    "not_found",
    "reused",
    "expired",
    "invalid_user",
]


class AuthRepository:
    """Persist users and revocable refresh-token sessions."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_user(self, *, email: str, password_hash: str) -> UserModel:
        user = UserRecord(email=email, password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)

        result = self._to_user_model(user)
        await self._session.commit()
        return result

    async def email_exists(self, email: str) -> bool:
        statement = select(UserRecord.id).where(UserRecord.email == email)
        return await self._session.scalar(statement) is not None

    async def get_user_by_id(self, user_id: int) -> UserModel | None:
        user = await self._session.get(UserRecord, user_id)
        return self._to_user_model(user) if user is not None else None

    async def get_credentials_by_email(
        self,
        email: str,
    ) -> UserCredentialsModel | None:
        statement = select(UserRecord).where(UserRecord.email == email)
        user = await self._session.scalar(statement)
        if user is None:
            return None
        return UserCredentialsModel(
            user=self._to_user_model(user),
            password_hash=user.password_hash,
        )

    async def create_refresh_session(
        self,
        *,
        token_hash: str,
        user_id: int,
        expires_at: datetime,
    ) -> None:
        self._session.add(
            RefreshSessionRecord(
                token_hash=token_hash,
                user_id=user_id,
                expires_at=expires_at,
            )
        )
        await self._session.commit()

    async def rotate_refresh_session(
        self,
        *,
        current_token_hash: str,
        user_id: int,
        replacement_token_hash: str,
        replacement_expires_at: datetime,
        now: datetime,
    ) -> RefreshRotationStatus:
        statement = (
            select(RefreshSessionRecord)
            .where(RefreshSessionRecord.token_hash == current_token_hash)
            .with_for_update()
        )
        current_session = await self._session.scalar(statement)
        if current_session is None:
            return "not_found"
        if current_session.user_id != user_id:
            return "invalid_user"

        if current_session.revoked_at is not None:
            await self._revoke_active_sessions(user_id=user_id, revoked_at=now)
            await self._session.commit()
            return "reused"

        if current_session.expires_at <= now:
            current_session.revoked_at = now
            await self._session.commit()
            return "expired"

        current_session.revoked_at = now
        current_session.replaced_by_token_hash = replacement_token_hash
        self._session.add(
            RefreshSessionRecord(
                token_hash=replacement_token_hash,
                user_id=user_id,
                expires_at=replacement_expires_at,
            )
        )
        await self._session.commit()
        return "rotated"

    async def revoke_refresh_session(
        self,
        *,
        token_hash: str,
        user_id: int,
        revoked_at: datetime,
    ) -> None:
        statement = (
            select(RefreshSessionRecord)
            .where(RefreshSessionRecord.token_hash == token_hash)
            .with_for_update()
        )
        refresh_session = await self._session.scalar(statement)
        if (
            refresh_session is not None
            and refresh_session.user_id == user_id
            and refresh_session.revoked_at is None
        ):
            refresh_session.revoked_at = revoked_at
            await self._session.commit()

    async def _revoke_active_sessions(
        self,
        *,
        user_id: int,
        revoked_at: datetime,
    ) -> None:
        statement = (
            update(RefreshSessionRecord)
            .where(
                RefreshSessionRecord.user_id == user_id,
                RefreshSessionRecord.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await self._session.execute(statement)

    @staticmethod
    def _to_user_model(user: UserRecord) -> UserModel:
        return UserModel(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
