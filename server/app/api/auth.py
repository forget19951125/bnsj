"""
认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.user_service import UserService
from ..utils.jwt import create_token, verify_token
from ..redis_client import get_redis
from ..config import settings
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


class VerifyResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    # 验证用户
    user = UserService.verify_user(db, request.username, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误，或账号已过期")
    
    # 创建Token
    token = create_token(user.id, user.username)
    
    # 保存Token到Redis（单点登录：使旧token失效）
    redis_client = get_redis()
    
    # 查找并删除该用户的旧token
    old_token_key = f"user:token:{user.id}"
    old_token = redis_client.get(old_token_key)
    if old_token:
        # 删除旧的session
        redis_client.delete(f"session:token:{old_token}")
    
    # 保存新的token
    session_key = f"session:token:{token}"
    redis_client.setex(
        session_key,
        settings.jwt_expire_hours * 3600,
        str(user.id)
    )
    # 保存用户ID到token的映射（用于单点登录）
    redis_client.setex(
        old_token_key,
        settings.jwt_expire_hours * 3600,
        token
    )
    
    # 计算过期时间
    expire_at = datetime.now() + timedelta(hours=settings.jwt_expire_hours)
    
    return LoginResponse(
        data={
            "token": token,
            "user_id": user.id,
            "username": user.username,
            "expire_at": expire_at.isoformat()
        }
    )


@router.get("/verify", response_model=VerifyResponse)
def verify(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """验证Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    token = authorization.split(" ")[1]
    
    # 验证Token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    user_id = payload.get("user_id")
    
    # 检查Token是否仍然有效（单点登录检查）
    redis_client = get_redis()
    session_key = f"session:token:{token}"
    if not redis_client.exists(session_key):
        raise HTTPException(status_code=401, detail="Token已失效（已在其他地方登录）")
    
    # 检查用户是否有效
    if not UserService.check_user_valid(db, user_id):
        raise HTTPException(status_code=401, detail="账号已过期或已禁用")
    
    user = UserService.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    
    return VerifyResponse(
        data={
            "user_id": user.id,
            "username": user.username
        }
    )

