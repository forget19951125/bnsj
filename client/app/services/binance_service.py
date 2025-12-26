"""
币安服务
"""
from typing import Optional, Dict, Callable
# 延迟导入binance_client，避免Playwright的macOS版本检查
# from ..binance_client import get_token, place_order_web
from ..utils.token_manager import TokenManager


class BinanceService:
    """币安服务类"""
    
    def __init__(self):
        # Token只保存在内存中，不保存到文件
        self._token: Optional[Dict] = None
        self.on_login_success: Optional[Callable] = None  # 登录成功回调
        self.log_callback: Optional[Callable] = None  # 日志回调函数
    
    def set_login_success_callback(self, callback: Optional[Callable]):
        """设置登录成功回调函数"""
        self.on_login_success = callback
    
    def set_log_callback(self, callback: Optional[Callable]):
        """设置日志回调函数"""
        self.log_callback = callback
    
    def _log(self, message: str):
        """输出日志（优先使用回调，否则使用print）"""
        try:
            if self.log_callback:
                try:
                    self.log_callback(message)
                except Exception as e:
                    # 如果回调失败，也输出到控制台
                    print(f"[日志回调失败] {e}")
                    print(f"[BinanceService] {message}")
            else:
                print(f"[BinanceService] {message}")
        except Exception as e:
            # 即使日志输出失败，也要尝试打印
            try:
                print(f"[BinanceService日志错误] {e}")
                print(f"[BinanceService] {message}")
            except:
                pass
    
    def login(self, reset: bool = True, headless: bool = False, qr_callback: Optional[Callable] = None, user_id: Optional[int] = None) -> Optional[Dict]:
        """币安登录
        
        Args:
            reset: 是否重置浏览器缓存（默认True，每次登录都清理）
            headless: 是否无头模式
            qr_callback: 二维码回调函数
            user_id: 用户ID，用于多账号支持
        """
        # 延迟导入，避免启动时的Playwright检查
        import os
        # 设置环境变量尝试绕过版本检查
        os.environ['_PLAYWRIGHT_SKIP_VALIDATE'] = '1'
        
        # 安全的print函数
        def safe_print(*args, **kwargs):
            try:
                print(*args, **kwargs)
            except UnicodeEncodeError:
                try:
                    safe_args = [str(arg).encode('ascii', 'replace').decode('ascii') if isinstance(arg, str) else arg for arg in args]
                    print(*safe_args, **kwargs)
                except:
                    print("[打印错误]")
        
        # 确保日志回调已设置
        safe_print("[DEBUG] BinanceService.login() - 开始执行")
        self._log("准备调用get_token函数启动浏览器...")
        safe_print("[DEBUG] BinanceService.login() - 已输出第一条日志")
        self._log(f"参数: reset={reset}, headless={headless}, user_id={user_id}")
        self._log(f"日志回调状态: {self.log_callback is not None}")
        safe_print(f"[DEBUG] BinanceService.login() - 日志回调: {self.log_callback is not None}")
        
        safe_print("[DEBUG] BinanceService.login() - 准备导入get_token")
        from ..binance_client import get_token
        safe_print("[DEBUG] BinanceService.login() - get_token导入成功")
        
        # 每次登录都清理缓存，支持多账号
        try:
            self._log("正在调用get_token函数...")
            safe_print("[DEBUG] BinanceService.login() - 准备调用get_token()")
            safe_print(f"[DEBUG] BinanceService.login() - log_callback状态: {self.log_callback is not None}")
            safe_print(f"[DEBUG] BinanceService.login() - 参数: reset={reset}, headless={headless}, user_id={user_id}")
            try:
                token_info = get_token(reset=reset, headless=headless, qr_callback=qr_callback, user_id=user_id, log_callback=self.log_callback)
                safe_print(f"[DEBUG] BinanceService.login() - get_token()返回: {token_info is not None}")
                self._log(f"get_token返回结果: {token_info is not None}")
            except Exception as get_token_error:
                safe_print(f"[DEBUG] BinanceService.login() - get_token()抛出异常: {get_token_error}")
                import traceback
                try:
                    trace_str = traceback.format_exc()
                    safe_print(f"[DEBUG] BinanceService.login() - 异常堆栈:\n{trace_str}")
                except:
                    safe_print("[DEBUG] BinanceService.login() - 无法输出异常堆栈")
                raise
        except KeyboardInterrupt:
            self._log("用户中断登录")
            return None  # 返回None而不是抛出异常
        except SystemExit:
            self._log("系统退出")
            return None  # 返回None而不是抛出异常
        except Exception as e:
            error_msg = f"get_token函数执行失败: {str(e)}"
            try:
                self._log(error_msg)
                import traceback
                try:
                    error_trace = traceback.format_exc()
                    self._log(f"详细错误信息:\n{error_trace}")
                except:
                    self._log("无法输出详细错误信息")
            except:
                safe_print(f"[ERROR] get_token函数执行失败: {e}")
            # 不重新抛出异常，返回None表示失败
            return None
        if token_info:
            self._log("✓ 收到Token信息，保存到内存...")
            # 只保存到内存，不保存到文件
            self._token = {
                "csrftoken": token_info.get("csrftoken", ""),
                "p20t": token_info.get("p20t", ""),
                "expirationTimestamp": token_info.get("expirationTimestamp", -1)
            }
            self._log(f"✓ Token已保存到内存: csrftoken={self._token['csrftoken'][:20]}..., p20t={self._token['p20t'][:20]}...")
            
            # Token保存成功后，立即调用回调函数更新GUI状态
            if self.on_login_success:
                try:
                    self._log("✓ 调用回调函数更新GUI状态...")
                    self.on_login_success()
                    self._log("✓ 回调函数已执行")
                except Exception as e:
                    self._log(f"✗ GUI状态更新失败: {e}")
                    import traceback
                    error_trace = traceback.format_exc()
                    self._log(error_trace)
            else:
                self._log("⚠ 警告: 回调函数未设置，GUI状态不会自动更新")
        else:
            self._log("✗ 未获取到Token信息")
        return token_info
    
    def load_token(self) -> Optional[Dict]:
        """加载币安Token（从内存）"""
        return self._token
    
    def is_logged_in(self) -> bool:
        """检查是否已登录币安"""
        if self._token is None:
            return False
        # 检查token是否过期
        expirationTimestamp = self._token.get("expirationTimestamp", -1)
        if expirationTimestamp > 0:
            from datetime import datetime
            expire_time = datetime.fromtimestamp(expirationTimestamp)
            if datetime.now() > expire_time:
                self._token = None  # 清除过期的token
                return False
        return True
    
    def clear_token(self):
        """清除Token（退出登录时调用）"""
        self._token = None
    
    def place_order(
        self,
        orderAmount: str,
        timeIncrements: str,
        symbolName: str,
        payoutRatio: str,
        direction: str
    ) -> Dict:
        """下单"""
        # 导入实际下单函数
        from ..binance_client import place_order_web
        
        token_info = self.load_token()
        if not token_info:
            raise Exception("币安账号未登录")
        
        self._log(f"正在调用币安API下单: 金额={orderAmount}, 交易对={symbolName}, 方向={direction}, 时间周期={timeIncrements}")
        
        result = place_order_web(
            csrftoken=token_info["csrftoken"],
            p20t=token_info["p20t"],
            orderAmount=orderAmount,
            timeIncrements=timeIncrements,
            symbolName=symbolName,
            payoutRatio=payoutRatio,
            direction=direction
        )
        
        self._log(f"币安API返回结果: {result}")
        return result

