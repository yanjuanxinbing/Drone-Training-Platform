"""JWT helpers + password hashing."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .settings import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _pwd_context.verify(plain, hashed)
    except Exception:
        return False


def create_access_token(subject: str, extra: Optional[dict] = None, expires_minutes: Optional[int] = None) -> str:
    exp_minutes = expires_minutes if expires_minutes is not None else settings.jwt_expire_minutes
    payload = {
        "sub": subject,
        "iat": datetime.now(tz=timezone.utc),
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=exp_minutes),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError:
        return None