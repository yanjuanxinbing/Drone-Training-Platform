"""Pydantic schemas — auth & users."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

PHONE_PATTERN = r"^1[3-9]\d{9}$"


class LoginRequest(BaseModel):
    phone: str
    password: str


class RegisterRequest(BaseModel):
    phone: str
    password: str = Field(min_length=6)
    confirm_password: str
    agree: bool = True

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        import re
        if not re.match(PHONE_PATTERN, v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if info.data.get("password") and v != info.data["password"]:
            raise ValueError("两次密码不一致")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserPublic"


class UserPublic(BaseModel):
    phone: str
    nick_name: str
    gender: str = "保密"
    birthday: str = ""
    addresses: list = []  # legacy field, retained for forward-compat
    is_real_name_verified: bool = False
    is_pilot_verified: bool = False


class UserUpdate(BaseModel):
    nick_name: str
    gender: str = "保密"
    birthday: str = ""


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)


TokenResponse.model_rebuild()