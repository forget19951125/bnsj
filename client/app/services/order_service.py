"""
订单服务
"""
import time
import threading
from typing import Optional, Dict, Callable, TYPE_CHECKING
from datetime import datetime
from ..api_client import APIClient
# 延迟导入BinanceService，避免Playwright的macOS版本检查
# from ..services.binance_service import BinanceService
from ..config import settings

if TYPE_CHECKING:
    from ..services.binance_service import BinanceService


class OrderService:
    """订单服务类"""
    
    def __init__(self, api_client: APIClient, binance_service):
        self.api_client = api_client
        self.binance_service = binance_service
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.order_amount = settings.default_order_amount
        self.on_order_callback: Optional[Callable] = None
        self.log_callback: Optional[Callable] = None  # 日志回调函数
    
    def set_order_amount(self, amount: float):
        """设置下单金额"""
        if amount < settings.min_order_amount:
            amount = settings.min_order_amount
        if amount > settings.max_order_amount:
            amount = settings.max_order_amount
        self.order_amount = amount
    
    def set_order_callback(self, callback: Callable):
        """设置订单回调函数"""
        self.on_order_callback = callback
    
    def set_log_callback(self, callback: Callable):
        """设置日志回调函数"""
        self.log_callback = callback
    
    def _log(self, message: str):
        """输出日志"""
        if self.log_callback:
            try:
                self.log_callback(message)
            except:
                print(message)
        else:
            print(message)
    
    def start(self):
        """启动订单拉取循环"""
        if self.running:
            return
        
        # 检查币安是否已登录
        if not self.binance_service.is_logged_in():
            raise Exception("币安账号未登录，无法开始自动下单")
        
        self.running = True
        self._log("✓ 自动下单已启动")
        self.thread = threading.Thread(target=self._order_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止订单拉取循环"""
        if not self.running:
            return
        self.running = False
        self._log("自动下单已停止")
        if self.thread:
            self.thread.join(timeout=5)
    
    def _order_loop(self):
        """订单拉取循环"""
        while self.running:
            try:
                # 检查币安登录状态
                if not self.binance_service.is_logged_in():
                    self._log("币安账号未登录，停止自动下单")
                    self.running = False
                    break
                
                # 拉取订单（不打印日志，避免日志过多）
                try:
                    order = self.api_client.pull_order()
                    
                    if order and isinstance(order, dict):
                        order_id = order.get('id', 'N/A')
                        symbol_name = order.get('symbol_name', 'N/A')
                        direction = order.get('direction', 'N/A')
                        self._log(f"✓ 收到订单: ID={order_id}, 交易对={symbol_name}, 方向={direction}")
                        # 检查订单有效期
                        if self._is_order_valid(order):
                            self._log("✓ 订单在有效期内，开始执行下单...")
                            # 执行下单
                            self._execute_order(order)
                        else:
                            self._log("✗ 订单已过期，跳过")
                    # 没有订单时不打印日志，减少日志噪音
                except Exception as e:
                    # 这个异常会在外层catch中处理
                    raise
                
                # 等待指定间隔（0.1秒）
                time.sleep(settings.order_pull_interval)
                
            except Exception as e:
                error_msg = str(e)
                self._log(f"✗ 拉取订单错误: {error_msg}")
                # 检查是否是token失效或账号过期
                if "Token已失效" in error_msg or "已在其他地方登录" in error_msg or "账号已过期" in error_msg or "已禁用" in error_msg or "401" in error_msg:
                    # Token失效或账号过期，停止循环
                    self.running = False
                    if self.on_order_callback:
                        if "账号已过期" in error_msg or "已禁用" in error_msg:
                            self.on_order_callback(None, {"error": "账号已过期或已禁用，请重新登录", "expired": True})
                        else:
                            self.on_order_callback(None, {"error": "登录已失效，请重新登录"})
                    break
                
                if self.on_order_callback:
                    self.on_order_callback(None, {"error": error_msg})
                time.sleep(settings.order_pull_interval)
    
    def _is_order_valid(self, order: Dict) -> bool:
        """检查订单是否在有效期内"""
        if not order or not isinstance(order, dict):
            return False
        
        created_at_str = order.get("created_at")
        if not created_at_str:
            return False
        
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            current_time = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now()
            elapsed = (current_time - created_at).total_seconds()
            valid_duration = order.get("valid_duration", 0)
            
            return elapsed < valid_duration
        except:
            return False
    
    def _execute_order(self, order: Dict):
        """执行下单"""
        try:
            # 根据订单时间周期设置不同的payoutRatio
            time_increments = order.get("time_increments", "TEN_MINUTE")
            if time_increments == "THIRTY_MINUTE":
                payout_ratio = "0.85"  # 30分钟使用0.85
            else:
                payout_ratio = "0.80"  # 10分钟使用0.80（默认）
            
            # 调用币安下单
            result = self.binance_service.place_order(
                orderAmount=str(int(self.order_amount)),
                timeIncrements=time_increments,
                symbolName=order["symbol_name"],
                payoutRatio=payout_ratio,
                direction=order["direction"]
            )
            
            # 记录结果
            self.api_client.record_order_result(order["id"], result)
            
            # 下单成功时打印日志（包含时间周期）
            time_increments = order.get('time_increments', 'N/A')
            if result.get("success") or result.get("code") == 200:
                self._log(f"✓ 下单成功: 订单ID={order['id']}, 交易对={order['symbol_name']}, 方向={order['direction']}, 时间周期={time_increments}, 金额={self.order_amount}")
            else:
                error_msg = result.get("message") or result.get("error", "未知错误")
                self._log(f"✗ 下单失败: 订单ID={order['id']}, 错误={error_msg}")
            
            # 调用回调
            if self.on_order_callback:
                self.on_order_callback(order, result)
                
        except Exception as e:
            # 记录错误
            error_msg = str(e)
            error_result = {"success": False, "error": error_msg}
            try:
                self.api_client.record_order_result(order["id"], error_result)
            except:
                pass
            
            # 下单失败时打印日志
            self._log(f"✗ 下单失败: 订单ID={order.get('id', 'N/A')}, 错误={error_msg}")
            
            if self.on_order_callback:
                self.on_order_callback(order, error_result)

