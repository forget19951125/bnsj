"""
客户端主程序入口 - 使用PyQt5 GUI
"""
import sys
import threading
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from .services.auth_service import AuthService
# 延迟导入BinanceService，避免Playwright的macOS版本检查
# from .services.binance_service import BinanceService
from .services.order_service import OrderService
from .api_client import APIClient
from .ui.login_window_qt import LoginWindow
from .ui.main_window_qt import MainWindow
from .ui.qr_window_qt import QRWindow
from .config import settings
from .utils.token_manager import TokenManager


class BinanceLoginSignals(QObject):
    """币安登录信号类，用于跨线程通信"""
    login_success = pyqtSignal()  # 登录成功信号


class ClientApp:
    """客户端应用主类"""
    
    def __init__(self):
        self.auth_service = AuthService()
        # 延迟初始化BinanceService
        self.binance_service = None
        self.api_client = APIClient()
        self.order_service: OrderService = None
        # TokenManager只用于用户登录token，币安token保存在内存中
        self.token_manager = TokenManager()
        
        # PyQt5应用实例
        self.qt_app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        self.login_window = None
        self.main_window = None
        self.qr_window = None
        self.session_timer: threading.Timer = None
        
        # 创建信号对象用于跨线程通信
        self.binance_signals = BinanceLoginSignals()
        self.binance_signals.login_success.connect(self._on_binance_login_success)
    
    def _get_binance_service(self):
        """延迟获取BinanceService"""
        if self.binance_service is None:
            from .services.binance_service import BinanceService
            self.binance_service = BinanceService()
        return self.binance_service
        
    def run(self):
        """运行应用"""
        # 尝试加载已保存的会话
        if self.auth_service.load_session():
            user_data = self.auth_service.get_current_user()
            if user_data:
                # 同步token到main的api_client
                if user_data.get("token"):
                    self.api_client.set_token(user_data["token"])
                self._start_main_window(user_data["username"])
                # 运行Qt事件循环
                sys.exit(self.qt_app.exec_())
                return
        
        # 显示登录窗口
        self._show_login_window()
        
        # 运行Qt事件循环
        sys.exit(self.qt_app.exec_())
    
    def _show_login_window(self):
        """显示登录窗口"""
        try:
            self.login_window = LoginWindow(self._handle_login, on_close=self._handle_exit)
            self.login_window.show()
        except Exception as e:
            import traceback
            print(f"显示登录窗口失败: {e}")
            traceback.print_exc()
    
    def _handle_exit(self):
        """处理退出程序"""
        import sys
        # 清理资源
        if self.order_service:
            self.order_service.stop()
        if self.session_timer:
            self.session_timer.cancel()
        # 退出程序
        sys.exit(0)
    
    def _handle_login(self, username: str, password: str):
        """处理登录"""
        try:
            result = self.auth_service.login(username, password)
            
            if result.get("code") == 200:
                # 登录成功，关闭登录窗口，启动主窗口
                if self.login_window:
                    self.login_window.close()
                self._start_main_window(username)
            else:
                # 显示错误
                error_msg = result.get("message", "登录失败")
                # 检查是否是单点登录导致的旧token失效
                if "Token已失效" in error_msg or "已在其他地方登录" in error_msg:
                    error_msg = "账号已在其他地方登录，请重新登录"
                if self.login_window:
                    self.login_window.show_error(error_msg)
        except Exception as e:
            error_msg = str(e)
            if "Token已失效" in error_msg or "已在其他地方登录" in error_msg:
                error_msg = "账号已在其他地方登录，请重新登录"
            if self.login_window:
                self.login_window.show_error(f"登录失败: {error_msg}")
    
    def _start_main_window(self, username: str):
        """启动主窗口"""
        # 获取用户信息
        user_data = self.auth_service.get_current_user()
        login_time = datetime.now()
        account_expire_at = user_data.get("expire_at") if user_data else None
        
        # 创建主窗口
        self.main_window = MainWindow(
            username=username,
            on_binance_login=self._handle_binance_login,
            on_set_order_amount=self._handle_set_order_amount,
            on_start_order=self._handle_start_order,
            on_stop_order=self._handle_stop_order,
            on_logout=self._handle_logout,
            on_close=self._handle_exit,
            login_time=login_time,
            account_expire_at=account_expire_at
        )
        
        # 检查币安登录状态（内存中的token，程序重启后需要重新登录）
        binance_service = self._get_binance_service()
        
        # 设置登录成功回调，在token保存后立即更新GUI状态
        def update_gui_on_login_success():
            """登录成功后的回调函数"""
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(0, lambda: self.main_window.set_binance_logged_in(True) if self.main_window else None)
            QTimer.singleShot(0, lambda: self.main_window.log("✓ 币安登录成功，GUI状态已更新") if self.main_window else None)
        
        binance_service.set_login_success_callback(update_gui_on_login_success)
        
        # Token只保存在内存中，程序重启后需要重新登录
        if binance_service.is_logged_in():
            token = binance_service.load_token()
            self.main_window.set_binance_logged_in(True)
            self.main_window.log("币安账号已登录（内存中）")
            if token and token.get('expirationTimestamp') and token.get('expirationTimestamp') > 0:
                self.main_window.log(f"Token有效期至: {datetime.fromtimestamp(token.get('expirationTimestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            self.main_window.log("请先登录币安账号（Token仅保存在内存中，程序重启后需要重新登录）")
        
        # 创建订单服务
        self.order_service = OrderService(self.api_client, binance_service)
        self.order_service.set_order_callback(self._on_order_callback)
        
        # 设置订单服务的日志回调
        def order_log_callback(msg):
            if self.main_window:
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(0, lambda: self.main_window.log(msg))
        self.order_service.set_log_callback(order_log_callback)
        
        # 设置订单金额
        self.order_service.set_order_amount(settings.default_order_amount)
        self.main_window.amount_input.setText(str(int(settings.default_order_amount)))
        
        # 启动24小时会话定时器和账号到期检查
        self._start_session_timer()
        
        # 显示主窗口
        self.main_window.show()
    
    def _handle_binance_login(self):
        """处理币安登录"""
        def qr_callback(qr_data: str):
            """二维码回调"""
            # 在Qt主线程中显示二维码窗口
            from PyQt5.QtCore import QTimer
            def show_qr():
                if self.qr_window:
                    self.qr_window.close_window()
                self.qr_window = QRWindow(qr_data)
                self.qr_window.show()
            QTimer.singleShot(0, show_qr)
        
        def login_thread():
            """登录线程"""
            try:
                # 在Qt主线程中更新日志
                from PyQt5.QtCore import QTimer
                def log_msg(msg):
                    if self.main_window:
                        self.main_window.log(msg)
                
                QTimer.singleShot(0, lambda: log_msg("正在启动浏览器，请稍候..."))
                QTimer.singleShot(0, lambda: log_msg("正在清理浏览器缓存..."))
                
                # 获取当前用户ID，用于多账号支持
                user_data = self.auth_service.get_current_user()
                user_id = user_data.get("user_id") if user_data else None
                
                binance_service = self._get_binance_service()
                
                # 设置日志回调，将所有输出重定向到GUI
                def log_to_gui(msg):
                    """将日志输出到GUI"""
                    QTimer.singleShot(0, lambda: log_msg(msg))
                
                binance_service.set_log_callback(log_to_gui)
                
                # 设置登录成功回调，使用信号机制确保在主线程中更新GUI
                def update_gui_on_login_success():
                    """登录成功后的回调函数（在token保存到内存后调用，在后台线程中执行）"""
                    log_to_gui("✓ 回调函数被调用（后台线程），发送信号到主线程...")
                    # 使用信号机制，确保在主线程中更新GUI
                    self.binance_signals.login_success.emit()
                    log_to_gui("✓ 信号已发送")
                
                binance_service.set_login_success_callback(update_gui_on_login_success)
                log_to_gui("✓ 回调函数已设置")
                
                # reset=True: 每次登录都清理缓存
                log_to_gui("开始调用binance_service.login()...")
                token_info = binance_service.login(reset=True, headless=False, qr_callback=qr_callback, user_id=user_id)
                log_to_gui(f"login()返回结果: {token_info is not None}")
                
                # 添加调试日志
                QTimer.singleShot(0, lambda: log_msg(f"登录返回结果: {token_info is not None}"))
                if token_info:
                    QTimer.singleShot(0, lambda: log_msg(f"Token信息: csrftoken={token_info.get('csrftoken', '')[:20] if token_info.get('csrftoken') else 'None'}..., p20t={token_info.get('p20t', '')[:20] if token_info.get('p20t') else 'None'}..."))
                    # 再次确认GUI状态（以防回调函数没有执行）
                    QTimer.singleShot(100, lambda: self._check_and_update_binance_status())
                else:
                    QTimer.singleShot(0, lambda: log_msg("币安登录失败: token_info为空"))
            except Exception as e:
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(0, lambda: self.main_window.log(f"币安登录错误: {str(e)}") if self.main_window else None)
                import traceback
                traceback.print_exc()
        
        # 在新线程中执行登录（避免阻塞UI）
        thread = threading.Thread(target=login_thread, daemon=True)
        thread.start()
    
    def _on_binance_login_success(self):
        """币安登录成功后的处理函数（在主线程中执行）"""
        if self.main_window:
            self.main_window.log("✓ 收到登录成功信号，在主线程中更新GUI状态...")
            self.main_window.log("✓ Token已保存到内存，正在更新GUI状态...")
            self.main_window.set_binance_logged_in(True)
            self.main_window.log("✓ 币安登录成功，GUI状态已更新")
            self.main_window.log("⚠ 注意: Token仅保存在内存中，程序关闭后需要重新登录")
        if self.qr_window:
            self.qr_window.close_window()
        if self.main_window:
            self.main_window.log("✓ GUI状态更新完成")
    
    def _check_and_update_binance_status(self):
        """检查并更新币安登录状态"""
        if not self.main_window:
            return
        binance_service = self._get_binance_service()
        if binance_service.is_logged_in():
            if not self.main_window.binance_logged_in:
                self.main_window.set_binance_logged_in(True)
                self.main_window.log("✓ 币安登录状态已确认并更新")
        else:
            if self.main_window.binance_logged_in:
                self.main_window.set_binance_logged_in(False)
                self.main_window.log("币安登录状态已失效")
    
    def _handle_set_order_amount(self, amount: float):
        """设置下单金额"""
        if self.order_service:
            self.order_service.set_order_amount(amount)
            if self.main_window:
                self.main_window.log(f"下单金额已设置为: {amount}")
    
    def _handle_start_order(self):
        """开始自动下单"""
        if self.order_service:
            try:
                self.order_service.start()
            except Exception as e:
                if self.main_window:
                    self.main_window.log(f"启动自动下单失败: {str(e)}")
                    # 更新GUI状态
                    self.main_window.order_running = False
                    self.main_window.start_btn.setEnabled(True)
                    self.main_window.stop_btn.setEnabled(False)
    
    def _handle_stop_order(self):
        """停止自动下单"""
        if self.order_service:
            self.order_service.stop()
            if self.main_window:
                self.main_window.log("自动下单已停止")
    
    def _on_order_callback(self, order, result):
        """订单回调"""
        if not self.main_window:
            return
            
        if order:
            if result.get("success") or result.get("code") == 200:
                amount = self.order_service.order_amount if self.order_service else "N/A"
                self.main_window.log(
                    f"订单执行成功: {order['symbol_name']} {order['direction']} "
                    f"金额={amount}"
                )
            else:
                error_msg = result.get("message") or result.get("error", "未知错误")
                self.main_window.log(
                    f"订单执行失败: {order['symbol_name']} {order['direction']} - {error_msg}"
                )
        else:
            if result.get("error"):
                # 检查是否是token失效
                error_msg = result.get("error", "")
                if "Token已失效" in error_msg or "401" in str(result.get("code", "")):
                    self.main_window.log("登录已失效，请重新登录")
                    self._handle_logout()
                else:
                    self.main_window.log(f"拉取订单错误: {error_msg}")
    
    def _handle_logout(self):
        """处理退出登录"""
        # 停止订单服务
        if self.order_service:
            self.order_service.stop()
        
        # 停止会话定时器
        if self.session_timer:
            self.session_timer.cancel()
            self.session_timer = None
        
        # 清除币安Token（内存中）
        if self.binance_service:
            self.binance_service.clear_token()
        
        # 清除登录信息
        self.auth_service.logout()
        
        # 关闭主窗口和二维码窗口
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        
        if self.qr_window:
            self.qr_window.close_window()
            self.qr_window = None
        
        # 重新显示登录窗口
        self._show_login_window()
    
    def _start_session_timer(self):
        """启动24小时会话定时器"""
        def check_session():
            """检查会话是否过期"""
            if self.token_manager.is_session_expired():
                if self.main_window:
                    self.main_window.log("会话已过期，需要重新登录")
                self._handle_logout()
            else:
                # 继续检查
                self._start_session_timer()
        
        # 每小时检查一次（24小时有效期）
        self.session_timer = threading.Timer(3600.0, check_session)
        self.session_timer.start()


def main():
    """主函数"""
    app = ClientApp()
    app.run()


if __name__ == "__main__":
    main()

