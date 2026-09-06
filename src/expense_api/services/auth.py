from __future__ import annotations

from datetime import UTC, datetime

from expense_api.core.config import Settings
from expense_api.core.security import (
    JWTManager,
    hash_password,
    hash_refresh_token,
    perform_dummy_password_check,
    verify_password,
)
from expense_api.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    RefreshTokenReuseError,
    TokenExpiredError,
    TokenValidationError,
    UserAlreadyExistsError,
)
from expense_api.models import AuthSessionModel, UserModel
from expense_api.repositories import AuthRepository, RefreshRotationStatus
from expense_api.schemas import LoginSchema, UserRegisterSchema


class AuthService:
    """Coordinate registration, login, token rotation, and logout."""

    def __init__(self, repository: AuthRepository, settings: Settings) -> None:
        self._repository = repository
        self._tokens = JWTManager(settings)

    async def register_user(self, data: UserRegisterSchema) -> UserModel:
        email = str(data.email)
        if await self._repository.email_exists(email):
            raise UserAlreadyExistsError(email)

        password_hash = await hash_password(data.password)
        return await self._repository.create_user(
            email=email,
            password_hash=password_hash,
        )

    async def login(self, data: LoginSchema) -> AuthSessionModel:
        credentials = await self._repository.get_credentials_by_email(str(data.email))
        if credentials is None:
            await perform_dummy_password_check(data.password)
            raise InvalidCredentialsError

        if not await verify_password(data.password, credentials.password_hash):
            raise InvalidCredentialsError
        if not credentials.user.is_active:
            raise InactiveUserError

        return await self._start_session(credentials.user)

    async def authenticate_access_token(self, token: str) -> UserModel:
        claims = self._tokens.decode_access_token(token)
        user = await self._repository.get_user_by_id(claims.user_id)
        if user is None:
            raise TokenValidationError("access")
        if not user.is_active:
            raise InactiveUserError
        return user

    async def refresh_session(self, refresh_token: str) -> AuthSessionModel:
        claims = self._tokens.decode_refresh_token(refresh_token)
        user = await self._repository.get_user_by_id(claims.user_id)
        if user is None:
            raise TokenValidationError("refresh")
        if not user.is_active:
            raise InactiveUserError

        replacement = self._tokens.issue_session(user)
        rotation_status = await self._repository.rotate_refresh_session(
            current_token_hash=hash_refresh_token(refresh_token),
            user_id=user.id,
            replacement_token_hash=hash_refresh_token(replacement.refresh_token),
            replacement_expires_at=replacement.refresh_token_expires_at,
            now=datetime.now(UTC),
        )
        self._raise_for_rotation_failure(rotation_status)
        return replacement

    async def logout(self, refresh_token: str | None) -> None:
        if refresh_token is None:
            return
        try:
            claims = self._tokens.decode_refresh_token(refresh_token)
        except TokenValidationError:
            return

        await self._repository.revoke_refresh_session(
            token_hash=hash_refresh_token(refresh_token),
            user_id=claims.user_id,
            revoked_at=datetime.now(UTC),
        )

    async def _start_session(self, user: UserModel) -> AuthSessionModel:
        session = self._tokens.issue_session(user)
        await self._repository.create_refresh_session(
            token_hash=hash_refresh_token(session.refresh_token),
            user_id=user.id,
            expires_at=session.refresh_token_expires_at,
        )
        return session

    @staticmethod
    def _raise_for_rotation_failure(status: RefreshRotationStatus) -> None:
        if status == "rotated":
            return
        if status == "reused":
            raise RefreshTokenReuseError
        if status == "expired":
            raise TokenExpiredError("refresh")
        raise TokenValidationError("refresh")
