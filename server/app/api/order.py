"""
订单相关API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.order_service import OrderService
from ..services.user_service import UserService
from ..utils.decorators import get_current_user_id, verify_admin_token

router = APIRouter(prefix="/api/orders", tags=["订单"])


class CreateOrderRequest(BaseModel):
    time_increments: str
    symbol_name: str
    direction: str
    valid_duration: int


class CreateOrderResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: dict


class PullOrderResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class MarkAssignedRequest(BaseModel):
    order_id: int


class MarkAssignedResponse(BaseModel):
    code: int = 200
    message: str = "success"


class RecordResultRequest(BaseModel):
    order_id: int
    result: dict


class RecordResultResponse(BaseModel):
    code: int = 200
    message: str = "success"


@router.post("/create", response_model=CreateOrderResponse)
def create_order(
    request: CreateOrderRequest,
    admin_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """创建订单（管理员）"""
    # 验证管理员权限
    from ..api.admin import get_admin_auth
    get_admin_auth(admin_token, authorization, db)
    
    order = OrderService.create_order(
        db=db,
        time_increments=request.time_increments,
        symbol_name=request.symbol_name,
        direction=request.direction,
        valid_duration=request.valid_duration
    )
    
    return CreateOrderResponse(
        data={
            "order_id": order.id
        }
    )
    """创建订单（管理员）"""
    order = OrderService.create_order(
        db=db,
        time_increments=request.time_increments,
        symbol_name=request.symbol_name,
        direction=request.direction,
        valid_duration=request.valid_duration
    )
    
    return CreateOrderResponse(
        data={
            "order_id": order.id
        }
    )


@router.get("/pull", response_model=PullOrderResponse)
def pull_order(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """拉取订单（客户端）"""
    # 获取用户ID
    user_id = get_current_user_id(authorization)
    
    # 检查用户是否有效
    if not UserService.check_user_valid(db, user_id):
        raise HTTPException(status_code=401, detail="账号已过期或已禁用")
    
    # 拉取订单
    order = OrderService.pull_order(db, user_id)
    
    if order:
        return PullOrderResponse(
            data=order.to_dict()
        )
    else:
        return PullOrderResponse(
            data=None
        )


@router.post("/mark-assigned", response_model=MarkAssignedResponse)
def mark_assigned(
    request: MarkAssignedRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """标记订单已拉取"""
    user_id = get_current_user_id(authorization)
    
    # 检查用户是否有效
    if not UserService.check_user_valid(db, user_id):
        raise HTTPException(status_code=401, detail="账号已过期或已禁用")
    
    OrderService.mark_order_assigned(db, request.order_id, user_id)
    
    return MarkAssignedResponse()


@router.post("/record-result", response_model=RecordResultResponse)
def record_result(
    request: RecordResultRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """记录订单执行结果"""
    user_id = get_current_user_id(authorization)
    
    # 检查用户是否有效
    if not UserService.check_user_valid(db, user_id):
        raise HTTPException(status_code=401, detail="账号已过期或已禁用")
    
    OrderService.record_order_result(
        db,
        request.order_id,
        user_id,
        request.result
    )
    
    return RecordResultResponse()

