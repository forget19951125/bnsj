"""
斐波拉契扩展位API
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.fib_service import FibService
from ..services.price_monitor import PriceMonitor
from ..api.admin import get_admin_auth as admin_auth_dep

router = APIRouter(prefix="/api/fib", tags=["斐波拉契"])

# 全局价格监控实例
_price_monitor: Optional[PriceMonitor] = None


def get_price_monitor(db: Session = None) -> PriceMonitor:
    """获取价格监控实例（单例）"""
    global _price_monitor
    if _price_monitor is None:
        _price_monitor = PriceMonitor()
        # 启动监控（内部会创建独立的数据库会话）
        _price_monitor.start_monitoring()
    return _price_monitor


class SyncFibLevelsRequest(BaseModel):
    """同步斐波拉契点位请求"""
    up_data: Optional[dict] = None
    down_data: Optional[dict] = None


class SyncFibLevelsResponse(BaseModel):
    """同步斐波拉契点位响应"""
    code: int = 200
    message: str = "success"


class CurrentFibLevelsResponse(BaseModel):
    """当前斐波拉契点位响应"""
    code: int = 200
    message: str = "success"
    data: dict


@router.post("/sync-levels", response_model=SyncFibLevelsResponse)
def sync_fib_levels(
    request: SyncFibLevelsRequest,
    admin_token: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    同步斐波拉契扩展位到服务器
    当2.py的send_instant_alert触发时调用此接口
    """
    # 验证管理员权限（可选，如果需要的话）
    # admin_auth_dep(admin_token, authorization, db)
    
    fib_service = FibService()
    
    # 缓存点位
    success = fib_service.cache_fib_levels(
        up_data=request.up_data,
        down_data=request.down_data
    )
    
    if success:
        return SyncFibLevelsResponse(message="点位已缓存")
    else:
        raise HTTPException(status_code=500, detail="缓存点位失败")


@router.get("/current-levels", response_model=CurrentFibLevelsResponse)
def get_current_fib_levels(
    admin_auth: str = Depends(admin_auth_dep),
    db: Session = Depends(get_db)
):
    """
    获取当前缓存的斐波拉契扩展位
    包含当前价格和RSI
    """
    fib_service = FibService()
    price_monitor = get_price_monitor(db)
    
    # 获取缓存的点位
    cached_levels = fib_service.get_cached_fib_levels()
    
    # 获取当前价格和RSI
    current_price = price_monitor.get_ethusdt_price()
    current_rsi = price_monitor.calculate_rsi()
    
    # 获取错误信息（如果有）
    error_info = None
    if hasattr(price_monitor, 'last_error') and price_monitor.last_error:
        error_info = price_monitor.last_error
    
    data = {
        'up_data': cached_levels.get('up') if cached_levels else None,
        'down_data': cached_levels.get('down') if cached_levels else None,
        'cached_at': cached_levels.get('cached_at') if cached_levels else None,
        'current_price': current_price,
        'current_rsi': current_rsi,
        'error': error_info  # 添加错误信息
    }
    
    return CurrentFibLevelsResponse(data=data)

