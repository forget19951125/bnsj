"""
管理员API - 订单列表等
"""
from fastapi import APIRouter, Depends, Query, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.order_service import OrderService
from ..utils.decorators import verify_admin_token, verify_web3_admin

router = APIRouter(prefix="/api/admin", tags=["管理员"])


def get_admin_auth(
    admin_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """获取管理员认证（支持两种方式：admin_token或Web3签名）"""
    # 优先使用Web3签名
    if authorization and authorization.startswith("Bearer "):
        try:
            return verify_web3_admin(authorization, db)
        except:
            pass
    
    # 回退到admin_token
    if admin_token:
        verify_admin_token(admin_token)
        return "admin_token"
    
    raise HTTPException(status_code=403, detail="管理员权限不足")


class OrderListResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


@router.get("/orders", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_auth: str = Depends(get_admin_auth),
    db: Session = Depends(get_db)
):
    """订单列表（管理员）"""
    skip = (page - 1) * page_size
    orders = OrderService.list_orders(db, skip=skip, limit=page_size)
    total = OrderService.count_orders(db)
    
    return OrderListResponse(
        data={
            "total": total,
            "list": [order.to_dict() for order in orders]
        }
    )

