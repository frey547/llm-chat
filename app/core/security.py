from datetime import datetime, timedelta, timezone
from typing import Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

# bcrypt 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(password: str) -> str:
    """明文密码 → bcrypt 哈希"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码是否匹配哈希"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:
    """
    生成 JWT access token。
    subject 通常是 user_id，存入 JWT 的 sub 字段。
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(subject: Any) -> str:
    """生成 JWT refresh token，有效期更长"""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    """
    解码并验证 JWT token。
    失败时抛出 JWTError，由调用方处理。
    """
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
