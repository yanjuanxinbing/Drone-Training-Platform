"""/api/users — profile only.

Address management was removed when the rental surface was deprecated.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.deps import get_current_user
from ..core.security import verify_password
from ..domain.user_manager import user_manager
from ..schemas.auth import PasswordChange, UserPublic, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


def _public(user: dict) -> UserPublic:
    return UserPublic(
        phone=user["phone"],
        nick_name=user["nick_name"],
        gender=user.get("gender", "保密"),
        birthday=user.get("birthday", ""),
        addresses=[],  # legacy field — preserved for backwards compatibility
        is_real_name_verified=user.get("is_real_name_verified", False),
        is_pilot_verified=user.get("is_pilot_verified", False),
    )


@router.get("/me", response_model=UserPublic)
def me(user=Depends(get_current_user)):
    return _public(user)


@router.patch("/me", response_model=UserPublic)
def update_me(req: UserUpdate, user=Depends(get_current_user)):
    from ..domain.user_manager import user_manager as um
    um.update_value(user["phone"], req.nick_name, req.gender, req.birthday)
    updated = um.get(user["phone"])
    return _public({"phone": user["phone"], **updated})


@router.post("/me/password")
def change_password(req: PasswordChange, user=Depends(get_current_user)):
    if not verify_password(req.old_password, user["password"]):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "原密码错误")
    from ..core.security import hash_password
    user_manager.update_password(user["phone"], hash_password(req.new_password))
    return {"ok": True}