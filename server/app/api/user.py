"""
用户管理API（管理员）
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from ..database import get_db
from ..services.user_service import UserService
from ..utils.decorators import verify_admin_token
from ..api.admin import get_admin_auth

router = APIRouter(prefix="/api/admin/users", tags=["用户管理"])


class CreateUserRequest(BaseModel):
    username: str
    password: str
    expire_at: Optional[str] = None


class CreateUserResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


class UpdateExpireRequest(BaseModel):
    expire_at: Optional[str] = None


class UpdateExpireResponse(BaseModel):
    code: int = 200
    message: str = "success"


class UserListResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


@router.post("/create", response_model=CreateUserResponse)
def create_user(
    request: CreateUserRequest,
    admin_auth: str = Depends(get_admin_auth),
    db: Session = Depends(get_db)
):
    """创建用户"""
    expire_at = None
    if request.expire_at:
        try:
            expire_at = datetime.fromisoformat(request.expire_at.replace('Z', '+00:00'))
        except:
            raise HTTPException(status_code=400, detail="日期格式错误")
    
    try:
        user = UserService.create_user(
            db=db,
            username=request.username,
            password=request.password,
            expire_at=expire_at
        )
        return CreateUserResponse(
            data={
                "user_id": user.id
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{user_id}/expire", response_model=UpdateExpireResponse)
def update_user_expire(
    user_id: int,
    request: UpdateExpireRequest,
    admin_auth: str = Depends(get_admin_auth),
    db: Session = Depends(get_db)
):
    """更新用户有效期"""
    expire_at = None
    if request.expire_at:
        try:
            expire_at = datetime.fromisoformat(request.expire_at.replace('Z', '+00:00'))
        except:
            raise HTTPException(status_code=400, detail="日期格式错误")
    
    user = UserService.update_user_expire(db, user_id, expire_at)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    return UpdateExpireResponse()


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_auth: str = Depends(get_admin_auth),
    db: Session = Depends(get_db)
):
    """用户列表"""
    skip = (page - 1) * page_size
    users = UserService.list_users(db, skip=skip, limit=page_size)
    total = UserService.count_users(db)
    
    return UserListResponse(
        data={
            "total": total,
            "list": [user.to_dict() for user in users]
        }
    )


class UserStatusResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


@router.get("/status", response_model=UserStatusResponse)
def get_user_status(
    admin_auth: str = Depends(get_admin_auth),
    db: Session = Depends(get_db)
):
    """获取用户状态列表（在线/离线、接单/未接单）"""
    status_data = UserService.get_user_status_list(db)
    
    return UserStatusResponse(
        data=status_data
    )

