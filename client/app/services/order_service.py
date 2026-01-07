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
            self._log("[WARN] 自动下单已在运行中")
            return
        
        # 检查币安是否已登录
        if not self.binance_service.is_logged_in():
            error_msg = "币安账号未登录，无法开始自动下单"
            self._log(f"[ERROR] {error_msg}")
            raise Exception(error_msg)
        
        self.running = True
        self._log("✓ 自动下单已启动")
        self._log("[DEBUG] 准备启动订单拉取线程...")
        try:
            # 使用print直接输出，确保能看到
            print("[DEBUG] 准备创建线程对象...")
            # 使用包装函数，确保异常能被捕获
            self.thread = threading.Thread(target=self._order_loop_wrapper, daemon=True, name="OrderLoopThread")
            print(f"[DEBUG] 线程对象已创建: {self.thread}")
            print(f"[DEBUG] 线程名称: {self.thread.name}")
            print("[DEBUG] 准备启动线程...")
            self.thread.start()
            print("[DEBUG] thread.start()已调用")
            self._log("[DEBUG] 订单拉取线程已启动")
            # 等待一小段时间，检查线程是否真的启动了
            import time
            time.sleep(0.1)
            if self.thread.is_alive():
                self._log("[DEBUG] 线程状态: 正在运行")
                print("[DEBUG] 线程状态: 正在运行")
            else:
                self._log("[DEBUG] 线程状态: 已停止（可能立即出错了）")
                print("[DEBUG] 线程状态: 已停止（可能立即出错了）")
        except Exception as e:
            self.running = False
            error_msg = f"启动订单拉取线程失败: {e}"
            print(f"[ERROR] {error_msg}")
            import traceback
            error_detail = traceback.format_exc()
            print(f"[ERROR] 异常详情: {error_detail}")
            self._log(f"[ERROR] {error_msg}")
            self._log(f"[ERROR] 异常详情: {error_detail}")
            raise
    
    def stop(self):
        """停止订单拉取循环"""
        if not self.running:
            return
        self.running = False
        self._log("自动下单已停止")
        if self.thread:
            self.thread.join(timeout=5)
    
    def _order_loop_wrapper(self):
        """订单拉取循环的包装函数，用于捕获所有异常"""
        # 同时使用print、_log和文件日志，确保能看到
        print("[DEBUG] _order_loop_wrapper开始执行")
        self._log("[DEBUG] _order_loop_wrapper开始执行")
        self._write_file_log("[DEBUG] _order_loop_wrapper开始执行")
        try:
            print("[DEBUG] 准备调用_order_loop...")
            self._log("[DEBUG] 准备调用_order_loop...")
            self._write_file_log("[DEBUG] 准备调用_order_loop...")
            self._order_loop()
        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[ERROR] _order_loop_wrapper捕获到异常: {e}")
            print(f"[ERROR] 异常详情: {error_detail}")
            self._write_file_log(f"[ERROR] _order_loop_wrapper捕获到异常: {e}")
            self._write_file_log(f"[ERROR] 异常详情: {error_detail}")
            try:
                self._log(f"[ERROR] 订单拉取循环发生严重错误: {e}")
                self._log(f"[ERROR] 异常详情: {error_detail}")
            except Exception as log_error:
                print(f"[ERROR] 日志输出失败: {log_error}")
                self._write_file_log(f"[ERROR] 日志输出失败: {log_error}")
            self.running = False
    
    def _write_file_log(self, message: str):
        """写入文件日志"""
        try:
            from ..utils.path_helper import get_logs_dir
            import os
            logs_dir = get_logs_dir()
            os.makedirs(logs_dir, exist_ok=True)
            log_file = os.path.join(logs_dir, 'order_service.log')
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except:
            pass
    
    def _order_loop(self):
        """订单拉取循环"""
        # 同时使用print、_log和文件日志，确保能看到
        print("[DEBUG] _order_loop函数开始执行")
        self._log("[DEBUG] _order_loop函数开始执行")
        self._write_file_log("[DEBUG] _order_loop函数开始执行")
        try:
            loop_count = 0
            print("[DEBUG] 准备记录日志...")
            self._log("[DEBUG] 订单拉取循环已启动")
            self._write_file_log("[DEBUG] 订单拉取循环已启动")
            print("[DEBUG] 第一条日志已记录")
            
            binance_status = self.binance_service.is_logged_in()
            api_status = self.api_client is not None
            print(f"[DEBUG] 币安登录状态: {binance_status}")
            print(f"[DEBUG] API客户端状态: {api_status}")
            self._log(f"[DEBUG] 币安登录状态: {binance_status}")
            self._log(f"[DEBUG] API客户端状态: {api_status}")
            self._write_file_log(f"[DEBUG] 币安登录状态: {binance_status}")
            self._write_file_log(f"[DEBUG] API客户端状态: {api_status}")
            print("[DEBUG] 初始日志已记录，进入循环...")
            
            while self.running:
                try:
                    loop_count += 1
                    # 前10次每次都记录，之后每10次记录一次
                    if loop_count <= 10 or loop_count % 10 == 0:
                        self._log(f"[DEBUG] 循环迭代开始 (第{loop_count}次), running={self.running}")
                        self._write_file_log(f"[DEBUG] 循环迭代开始 (第{loop_count}次), running={self.running}")
                    
                    # 每100次循环记录一次，避免日志过多
                    if loop_count % 100 == 0:
                        self._log(f"[DEBUG] 订单拉取循环运行中，已执行 {loop_count} 次")
                        self._write_file_log(f"[DEBUG] 订单拉取循环运行中，已执行 {loop_count} 次")
                
                    # 检查币安登录状态
                    if not self.binance_service.is_logged_in():
                        self._log("币安账号未登录，停止自动下单")
                        self._write_file_log("币安账号未登录，停止自动下单")
                        self.running = False
                        break
                    
                    # 拉取订单
                    try:
                        # 记录每次拉取订单的调用（前10次每次都记录，之后每10次记录一次）
                        if loop_count <= 10 or loop_count % 10 == 0:
                            self._log(f"[DEBUG] 开始拉取订单... (第{loop_count}次)")
                            self._write_file_log(f"[DEBUG] 开始拉取订单... (第{loop_count}次)")
                        
                        order = self.api_client.pull_order()
                        
                        # 记录返回结果（如果有数据或前10次）
                        if order is not None or loop_count <= 10:
                            self._log(f"[DEBUG] pull_order返回: type={type(order)}, is_dict={isinstance(order, dict)}, value={order}")
                            self._write_file_log(f"[DEBUG] pull_order返回: type={type(order)}, is_dict={isinstance(order, dict)}, value={order}")
                        
                        if order is not None:
                            self._write_file_log(f"[DEBUG] 订单不为None，开始处理订单")
                            if isinstance(order, dict):
                                self._write_file_log(f"[DEBUG] 订单是字典类型，长度={len(order)}")
                                # 检查是否是空字典
                                if len(order) == 0:
                                    self._log("[DEBUG] 收到空字典，跳过")
                                    self._write_file_log("[DEBUG] 收到空字典，跳过")
                                else:
                                    # 检查必要的字段
                                    order_id = order.get('id')
                                    symbol_name = order.get('symbol_name')
                                    direction = order.get('direction')
                                    
                                    self._write_file_log(f"[DEBUG] 订单字段检查: id={order_id}, symbol_name={symbol_name}, direction={direction}")
                                    self._write_file_log(f"[DEBUG] 字段有效性: id={bool(order_id)}, symbol_name={bool(symbol_name)}, direction={bool(direction)}")
                                    
                                    if order_id and symbol_name and direction:
                                        self._log(f"✓ 收到订单: ID={order_id}, 交易对={symbol_name}, 方向={direction}")
                                        self._write_file_log(f"[INFO] 收到订单: ID={order_id}, 交易对={symbol_name}, 方向={direction}")
                                        
                                        # 检查订单有效期
                                        is_valid = self._is_order_valid(order)
                                        self._write_file_log(f"[DEBUG] 订单有效期检查结果: {is_valid}")
                                        
                                        if is_valid:
                                            self._log("✓ 订单在有效期内，开始执行下单...")
                                            self._write_file_log("[INFO] 订单在有效期内，开始执行下单...")
                                            # 执行下单
                                            self._execute_order(order)
                                        else:
                                            self._log("✗ 订单已过期，跳过")
                                            self._write_file_log("[WARN] 订单已过期，跳过")
                                    else:
                                        self._log(f"[WARN] 订单数据不完整: id={order_id}, symbol_name={symbol_name}, direction={direction}")
                                        self._log(f"[WARN] 完整订单数据: {order}")
                                        self._write_file_log(f"[WARN] 订单数据不完整: id={order_id}, symbol_name={symbol_name}, direction={direction}")
                                        self._write_file_log(f"[WARN] 完整订单数据: {order}")
                            else:
                                # order不是dict，记录警告
                                self._log(f"[WARN] pull_order返回了非字典类型: type={type(order)}, value={order}")
                                self._write_file_log(f"[WARN] pull_order返回了非字典类型: type={type(order)}, value={order}")
                        else:
                            # 只在有订单时才记录，避免日志过多
                            if loop_count <= 10:
                                self._write_file_log(f"[DEBUG] 订单为None，跳过处理 (第{loop_count}次)")
                        # 没有订单时不打印日志（前10次除外），减少日志噪音
                    except Exception as e:
                        # 记录异常详情
                        import traceback
                        error_detail = traceback.format_exc()
                        self._log(f"[ERROR] 拉取订单时发生异常: {e}")
                        self._log(f"[ERROR] 异常详情: {error_detail}")
                        # 这个异常会在外层catch中处理
                        raise
                    
                    # 等待指定间隔（0.1秒）
                    if loop_count <= 10:
                        self._write_file_log(f"[DEBUG] 准备sleep {settings.order_pull_interval}秒 (第{loop_count}次)")
                    time.sleep(settings.order_pull_interval)
                    if loop_count <= 10:
                        self._write_file_log(f"[DEBUG] sleep完成，继续循环 (第{loop_count}次)")
                except Exception as e:
                    error_msg = str(e)
                    self._log(f"✗ 拉取订单错误: {error_msg}")
                    self._write_file_log(f"[ERROR] 拉取订单错误: {error_msg}")
                    import traceback
                    self._write_file_log(f"[ERROR] 异常详情: {traceback.format_exc()}")
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
        except Exception as e:
            # 捕获整个循环的异常
            import traceback
            error_detail = traceback.format_exc()
            print(f"[ERROR] _order_loop发生异常: {e}")
            print(f"[ERROR] 异常详情: {error_detail}")
            try:
                self._log(f"[ERROR] 订单拉取循环发生严重错误: {e}")
                self._log(f"[ERROR] 异常详情: {error_detail}")
            except:
                pass
            self.running = False
        finally:
            print("[DEBUG] _order_loop函数结束")
    
    def _is_order_valid(self, order: Dict) -> bool:
        """检查订单是否在有效期内"""
        if not order or not isinstance(order, dict):
            self._write_file_log("[DEBUG] _is_order_valid: 订单为空或不是字典")
            return False
        
        created_at_str = order.get("created_at")
        if not created_at_str:
            self._write_file_log("[DEBUG] _is_order_valid: 订单缺少created_at字段")
            return False
        
        try:
            # 处理时区问题：如果字符串没有时区信息，假设是UTC时间
            if 'Z' in created_at_str or '+' in created_at_str or created_at_str.count('-') > 2:
                created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            else:
                # 没有时区信息，假设是UTC时间
                from datetime import timezone
                created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)
            
            current_time = datetime.now(created_at.tzinfo) if created_at.tzinfo else datetime.now(timezone.utc)
            elapsed = (current_time - created_at).total_seconds()
            valid_duration = order.get("valid_duration", 0)
            
            self._write_file_log(f"[DEBUG] _is_order_valid: created_at={created_at}, current_time={current_time}, elapsed={elapsed:.2f}秒, valid_duration={valid_duration}秒")
            
            is_valid = elapsed < valid_duration
            self._write_file_log(f"[DEBUG] _is_order_valid: 结果={is_valid}")
            
            return is_valid
        except Exception as e:
            import traceback
            self._write_file_log(f"[ERROR] _is_order_valid异常: {e}")
            self._write_file_log(f"[ERROR] 异常详情: {traceback.format_exc()}")
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

