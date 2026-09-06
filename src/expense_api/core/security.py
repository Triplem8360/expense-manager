from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from expense_api.core.config import Settings
from expense_api.exceptions import TokenExpiredError, TokenValidationError
from expense_api.models import AuthSessionModel, TokenClaimsModel, TokenType, UserModel

_PASSWORD_HASH = PasswordHash.recommended()
_DUMMY_PASSWORD_HASH = _PASSWORD_HASH.hash("Timing-Protection-Password-123")


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_PASSWORD_HASH.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    return await asyncio.to_thread(_PASSWORD_HASH.verify, password, password_hash)


async def perform_dummy_password_check(password: str) -> None:
    await verify_password(password, _DUMMY_PASSWORD_HASH)


def hash_refresh_token(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


class JWTManager:
    """Issue and validate signed access and refresh JWTs."""

    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key.get_secret_value()
        self._algorithm = settings.jwt_algorithm
        self._issuer = settings.jwt_issuer
        self._audience = settings.jwt_audience
        self._access_ttl = timedelta(minutes=settings.access_token_ttl_minutes)
        self._refresh_ttl = timedelta(days=settings.refresh_token_ttl_days)
        self._clock_skew = timedelta(seconds=settings.jwt_clock_skew_seconds)

    def issue_session(self, user: UserModel) -> AuthSessionModel:
        now = datetime.now(UTC)
        access_expires_at = now + self._access_ttl
        refresh_expires_at = now + self._refresh_ttl
        return AuthSessionModel(
            user=user,
            access_token=self._encode_token(
                user_id=user.id,
                token_type="access",
                issued_at=now,
                expires_at=access_expires_at,
            ),
            refresh_token=self._encode_token(
                user_id=user.id,
                token_type="refresh",
                issued_at=now,
                expires_at=refresh_expires_at,
            ),
            access_token_expires_at=access_expires_at,
            refresh_token_expires_at=refresh_expires_at,
        )

    def decode_access_token(self, token: str) -> TokenClaimsModel:
        return self._decode_token(token, expected_type="access")

    def decode_refresh_token(self, token: str) -> TokenClaimsModel:
        return self._decode_token(token, expected_type="refresh")

    def _encode_token(
        self,
        *,
        user_id: int,
        token_type: TokenType,
        issued_at: datetime,
        expires_at: datetime,
    ) -> str:
        payload: dict[str, object] = {
            "sub": str(user_id),
            "type": token_type,
            "jti": uuid4().hex,
            "iat": issued_at,
            "nbf": issued_at,
            "exp": expires_at,
            "iss": self._issuer,
            "aud": self._audience,
        }
        return jwt.encode(payload, self._secret_key, algorithm=self._algorithm)

    def _decode_token(
        self,
        token: str,
        *,
        expected_type: TokenType,
    ) -> TokenClaimsModel:
        try:
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
                audience=self._audience,
                issuer=self._issuer,
                leeway=self._clock_skew,
                options={
                    "require": [
                        "sub",
                        "type",
                        "jti",
                        "iat",
                        "nbf",
                        "exp",
                        "iss",
                        "aud",
                    ],
                    "strict_aud": True,
                },
            )
        except ExpiredSignatureError as exc:
            raise TokenExpiredError(expected_type) from exc
        except InvalidTokenError as exc:
            raise TokenValidationError(expected_type) from exc

        return self._parse_claims(payload, expected_type=expected_type)

    @staticmethod
    def _parse_claims(
        payload: dict[str, Any],
        *,
        expected_type: TokenType,
    ) -> TokenClaimsModel:
        try:
            token_type = payload["type"]
            if token_type != expected_type:
                raise ValueError("Unexpected token type")

            user_id = int(payload["sub"])
            if user_id <= 0:
                raise ValueError("Invalid token subject")

            token_id = str(UUID(payload["jti"]))
            expires_at = datetime.fromtimestamp(payload["exp"], tz=UTC)
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            raise TokenValidationError(expected_type) from exc

        return TokenClaimsModel(
            user_id=user_id,
            token_type=expected_type,
            token_id=token_id,
            expires_at=expires_at,
        )
