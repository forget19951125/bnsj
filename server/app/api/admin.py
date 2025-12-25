"""
管理员API - 订单列表等
"""
from fastapi import APIRouter, Depends, Query, Header, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.order_service import OrderService
from ..utils.decorators import verify_admin_token, verify_web3_admin

router = APIRouter(prefix="/api/admin", tags=["管理员"])


def get_admin_auth(
    admin_token: Optional[str] = Header(None, alias="admin-token"),
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
    page_size: int = Query(100, ge=1, le=100),  # 默认100条，最多100条
    admin_auth: str = Depends(get_admin_auth),
    db: Session = Depends(get_db)
):
    """订单列表（管理员）"""
    # 限制最多返回100条
    limit = min(page_size, 100)
    skip = (page - 1) * limit
    orders = OrderService.list_orders(db, skip=skip, limit=limit)
    total = OrderService.count_orders(db)
    
    # 为每个订单添加是否有效的判断
    from datetime import datetime
    order_list = []
    for order in orders:
        order_dict = order.to_dict()
        # 判断订单是否过期（基于创建时间和有效时间）
        created_at = order.created_at
        if created_at:
            elapsed = (datetime.now() - created_at).total_seconds()
            order_dict["is_valid"] = elapsed < order.valid_duration
        else:
            order_dict["is_valid"] = False
        order_list.append(order_dict)
    
    return OrderListResponse(
        data={
            "total": total,
            "list": order_list
        }
    )

