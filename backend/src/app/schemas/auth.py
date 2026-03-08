from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SignUpRequest(BaseModel):
    email: EmailStr
    password: SecretStr = Field(min_length=8)


class SignInRequest(BaseModel):
    email: EmailStr
    password: SecretStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: SecretStr = Field(min_length=8)


class AuthenticatedUserResponse(BaseModel):
    user: UserResponse


class MessageResponse(BaseModel):
    message: str


class PasswordResetRequestResponse(BaseModel):
    message: str
    reset_token: str | None = None
