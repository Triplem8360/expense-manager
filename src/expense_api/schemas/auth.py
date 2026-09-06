from __future__ import annotations

from typing import Annotated, ClassVar, Self

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    PositiveInt,
    StringConstraints,
    field_validator,
    model_validator,
)

EmailAddress = Annotated[
    EmailStr,
    Field(max_length=320, description="Normalized user email address"),
]
LoginPassword = Annotated[
    str,
    StringConstraints(min_length=1, max_length=128),
    Field(description="User password"),
]
NewPassword = Annotated[
    str,
    StringConstraints(min_length=12, max_length=128),
    Field(description="Password with upper, lower, and numeric characters"),
]


class _EmailInputSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailAddress

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class UserRegisterSchema(_EmailInputSchema):
    password: NewPassword

    @field_validator("password", mode="after")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("Password cannot contain null characters")
        if not any(character.islower() for character in value):
            raise ValueError("Password must include a lowercase character")
        if not any(character.isupper() for character in value):
            raise ValueError("Password must include an uppercase character")
        if not any(character.isdigit() for character in value):
            raise ValueError("Password must include a numeric character")
        return value


class LoginSchema(_EmailInputSchema):
    password: LoginPassword


class UserReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: PositiveInt
    email: EmailStr
    is_active: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime


class AuthSessionReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    _TOKEN_DELIVERY: ClassVar[str] = "secure_cookie"

    user: UserReadSchema
    access_token_expires_at: AwareDatetime
    refresh_token_expires_at: AwareDatetime
    token_delivery: str = Field(
        default=_TOKEN_DELIVERY,
        description="Authentication tokens are returned only as secure cookies",
    )

    @model_validator(mode="after")
    def validate_expiration_order(self) -> Self:
        if self.refresh_token_expires_at <= self.access_token_expires_at:
            raise ValueError("Refresh token must outlive the access token")
        return self
