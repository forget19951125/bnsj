"""
Web3认证API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.admin_service import AdminService
from ..utils.web3_auth import verify_auth_message, generate_auth_message
from ..utils.jwt import create_token
from ..redis_client import get_redis
from ..config import settings
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/web3", tags=["Web3认证"])


class Web3LoginRequest(BaseModel):
    address: str
    message: str
    signature: str
    timestamp: int


class Web3LoginResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


class GetAuthMessageRequest(BaseModel):
    address: str


class GetAuthMessageResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


@router.post("/get-auth-message", response_model=GetAuthMessageResponse)
def get_auth_message(request: GetAuthMessageRequest):
    """获取认证消息"""
    import time
    timestamp = int(time.time())
    message = generate_auth_message(request.address, timestamp)
    
    return GetAuthMessageResponse(
        data={
            "message": message,
            "timestamp": timestamp
        }
    )


@router.post("/login", response_model=Web3LoginResponse)
def web3_login(request: Web3LoginRequest, db: Session = Depends(get_db)):
    """Web3签名登录"""
    # 验证是否为管理员
    if not AdminService.is_admin(db, request.address):
        raise HTTPException(status_code=403, detail="该地址不是管理员")
    
    # 验证签名
    if not verify_auth_message(
        request.address,
        request.message,
        request.signature,
        request.timestamp,
        expire_seconds=300  # 5分钟过期
    ):
        raise HTTPException(status_code=401, detail="签名验证失败")
    
    # 创建Token
    token = create_token(0, request.address)  # user_id设为0表示管理员
    
    # 保存Token到Redis（单点登录：使旧token失效）
    redis_client = get_redis()
    
    # 查找并删除该地址的旧token
    old_token_key = f"admin:token:{request.address.lower()}"
    old_token = redis_client.get(old_token_key)
    if old_token:
        # 删除旧的session
        redis_client.delete(f"admin:session:{request.address.lower()}")
    
    # 保存新的token
    session_key = f"admin:session:{request.address.lower()}"
    redis_client.setex(
        session_key,
        settings.jwt_expire_hours * 3600,
        token
    )
    # 保存地址到token的映射（用于单点登录）
    redis_client.setex(
        old_token_key,
        settings.jwt_expire_hours * 3600,
        token
    )
    
    # 计算过期时间
    expire_at = datetime.now() + timedelta(hours=settings.jwt_expire_hours)
    
    return Web3LoginResponse(
        data={
            "token": token,
            "address": request.address,
            "expire_at": expire_at.isoformat()
        }
    )


@router.get("/verify")
def verify_admin_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """验证管理员Token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未授权")
    
    token = authorization.split(" ")[1]
    
    # 从JWT中获取地址
    from ..utils.jwt import verify_token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效或已过期")
    
    address = payload.get("username").lower()  # 在JWT中，address存储在username字段
    
    # 检查Token是否仍然有效（单点登录检查）
    redis_client = get_redis()
    session_key = f"admin:session:{address}"
    if not redis_client.exists(session_key):
        raise HTTPException(status_code=401, detail="Token已失效（已在其他地方登录）")
    
    # 验证是否为管理员
    if not AdminService.is_admin(db, address):
        raise HTTPException(status_code=403, detail="该地址不是管理员")
    
    return {
        "code": 200,
        "message": "success",
        "data": {
            "address": address
        }
    }

