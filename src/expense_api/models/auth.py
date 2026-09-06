from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

type TokenType = Literal["access", "refresh"]


@dataclass(frozen=True, slots=True, kw_only=True)
class UserModel:
    id: int
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class UserCredentialsModel:
    user: UserModel
    password_hash: str


@dataclass(frozen=True, slots=True, kw_only=True)
class TokenClaimsModel:
    user_id: int
    token_type: TokenType
    token_id: str
    expires_at: datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthSessionModel:
    user: UserModel
    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
