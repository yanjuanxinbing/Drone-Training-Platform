"""/api/auth — login / register."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..core.security import create_access_token, hash_password, verify_password
from ..core.settings import settings
from ..domain.user_manager import user_manager
from ..schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _public(phone: str) -> UserPublic:
    u = user_manager.get(phone)
    if not u:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "用户不存在")
    return UserPublic(
        phone=phone,
        nick_name=u["nick_name"],
        gender=u.get("gender", "保密"),
        birthday=u.get("birthday", ""),
        addresses=u.get("addresses", []),
        is_real_name_verified=u.get("is_real_name_verified", False),
        is_pilot_verified=u.get("is_pilot_verified", False),
    )


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    if not user_manager.verify_login(req.phone, req.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "手机号或密码错误")
    user = user_manager.get(req.phone)
    # Auto-upgrade legacy SHA-256 hashes to bcrypt on successful login.
    if isinstance(user["password"], str) and len(user["password"]) == 64 and not user["password"].startswith("$2"):
        user["password"] = hash_password(req.password)
        user_manager.save()
    token = create_access_token(req.phone)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        user=_public(req.phone),
    )


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(req: RegisterRequest):
    if user_manager.contains(req.phone):
        raise HTTPException(status.HTTP_409_CONFLICT, "手机号已注册")
    if not req.agree:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "请先同意协议")
    user_manager.add(req.phone, f"用户{req.phone}", req.password)
    token = create_access_token(req.phone)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        user=_public(req.phone),
    )