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
                
                # 拉取订单
                self._log("正在拉取订单...")
                try:
                    order = self.api_client.pull_order()
                    
                    if order and isinstance(order, dict):
                        order_id = order.get('id', 'N/A')
                        symbol_name = order.get('symbol_name', 'N/A')
                        direction = order.get('direction', 'N/A')
                        self._log(f"收到订单: ID={order_id}, 交易对={symbol_name}, 方向={direction}")
                        # 检查订单有效期
                        if self._is_order_valid(order):
                            self._log("订单在有效期内，开始执行下单...")
                            # 执行下单
                            self._execute_order(order)
                        else:
                            self._log("订单已过期，跳过")
                    else:
                        # 只有在没有订单时才记录，避免日志过多
                        pass  # 不记录"暂无新订单"，减少日志噪音
                except Exception as e:
                    # 这个异常会在外层catch中处理
                    raise
                
                # 等待指定间隔
                time.sleep(settings.order_pull_interval)
                
            except Exception as e:
                error_msg = str(e)
                self._log(f"拉取订单错误: {error_msg}")
                # 检查是否是token失效（单点登录）
                if "Token已失效" in error_msg or "已在其他地方登录" in error_msg or "401" in error_msg:
                    # Token失效，停止循环
                    self.running = False
                    if self.on_order_callback:
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
            self._log(f"准备下单: 金额={self.order_amount}, 交易对={order['symbol_name']}, 方向={order['direction']}")
            
            # TODO: 临时注释掉实际下单，用于测试客户端逻辑
            # # 调用币安下单
            # self._log("正在调用币安API下单...")
            # result = self.binance_service.place_order(
            #     orderAmount=str(int(self.order_amount)),
            #     timeIncrements=order["time_increments"],
            #     symbolName=order["symbol_name"],
            #     payoutRatio="0.80",
            #     direction=order["direction"]
            # )
            # self._log(f"币安API返回: {result}")
            
            # 模拟下单成功（用于测试）
            self._log("正在执行下单（测试模式）...")
            result = {
                "success": True,
                "code": 200,
                "message": "下单成功（测试模式）",
                "data": {
                    "orderId": "test_order_123",
                    "symbol": order["symbol_name"],
                    "direction": order["direction"],
                    "amount": self.order_amount
                }
            }
            self._log(f"下单成功: {result}")
            
            # 记录结果
            self._log("正在记录订单结果到服务器...")
            self.api_client.record_order_result(order["id"], result)
            self._log("订单结果已记录")
            
            # 调用回调
            if self.on_order_callback:
                self.on_order_callback(order, result)
                
        except Exception as e:
            # 记录错误
            error_msg = str(e)
            self._log(f"下单失败: {error_msg}")
            error_result = {"success": False, "error": error_msg}
            try:
                self.api_client.record_order_result(order["id"], error_result)
                self._log("错误结果已记录到服务器")
            except:
                self._log("记录错误结果失败")
            
            if self.on_order_callback:
                self.on_order_callback(order, error_result)

