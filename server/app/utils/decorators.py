"""
装饰器工具
"""
from functools import wraps
from fastapi import HTTPException, Header, Depends
from typing import Optional
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..services.user_service import UserService
from ..services.admin_service import AdminService
from ..utils.jwt import verify_token


def verify_admin_token(admin_token: Optional[str] = Header(None, alias="admin-token")):
    """验证管理员Token（兼容旧方式）"""
    if not admin_token or admin_token != settings.admin_token:
        raise HTTPException(status_code=403, detail="管理员权限不足")
    return admin_token


def verify_web3_admin(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """验证Web3管理员Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    token = authorization.split(" ")[1]
    
    # 验证Token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    address = payload.get("username", "").lower()  # 在JWT中，address存储在username字段
    
    # 验证是否为管理员
    if not AdminService.is_admin(db, address):
        raise HTTPException(status_code=403, detail="该地址不是管理员")
    
    return address


def get_current_user_id(authorization: Optional[str] = Header(None)):
    """从JWT Token中获取当前用户ID（单点登录检查）"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    token = authorization.split(" ")[1]
    
    # 验证JWT Token
    from ..utils.jwt import verify_token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    user_id = payload.get("user_id")
    
    # 检查Token是否仍然有效（单点登录检查）
    from ..redis_client import get_redis
    redis_client = get_redis()
    session_key = f"session:token:{token}"
    if not redis_client.exists(session_key):
        raise HTTPException(status_code=401, detail="Token已失效（已在其他地方登录）")
    
    return int(user_id)

