"""
JWT工具函数
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional
from ..config import settings


def create_token(user_id: int, username: str) -> str:
    """创建JWT Token"""
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expire
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token


def verify_token(token: str) -> Optional[dict]:
    """验证JWT Token"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

