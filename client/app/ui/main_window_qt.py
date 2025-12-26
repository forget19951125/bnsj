"""
主窗口 - PyQt5版本
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QCloseEvent
from typing import Callable, Optional
from datetime import datetime, timedelta


class MainWindow(QMainWindow):
    """主窗口类"""
    
    def __init__(
        self,
        username: str,
        on_binance_login: Callable,
        on_set_order_amount: Callable,
        on_start_order: Callable,
        on_stop_order: Callable,
        on_logout: Callable,
        on_close: Callable = None,
        login_time: datetime = None,
        account_expire_at: str = None
    ):
        super().__init__()
        self.username = username
        self.on_binance_login = on_binance_login
        self.on_set_order_amount = on_set_order_amount
        self.on_start_order = on_start_order
        self.on_stop_order = on_stop_order
        self.on_logout = on_logout
        self.on_close = on_close
        
        self.binance_logged_in = False
        self.order_running = False
        
        # 时间信息
        self.login_time = login_time or datetime.now()
        self.account_expire_at_str = account_expire_at
        
        # 定时器用于更新倒计时
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_timers)
        self.timer.start(1000)  # 每秒更新一次
        
        self.init_ui()
    
    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        import sys
        import traceback
        from ..utils.logger import debug, error, get_log_file
        
        debug("MainWindow.closeEvent() - 被调用")
        debug(f"MainWindow.closeEvent() - on_close={self.on_close}")
        debug("MainWindow.closeEvent() - 调用堆栈:")
        try:
            stack = traceback.format_stack()
            for line in stack:
                debug(f"  {line.strip()}")
        except:
            pass
        
        # 只有在用户明确关闭窗口时才调用on_close
        # 这可以防止浏览器关闭等操作意外触发窗口关闭
        if self.on_close:
            # 确认用户是否真的要退出
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                '确认退出',
                '确定要退出程序吗？',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                debug("MainWindow.closeEvent() - 用户确认退出，调用on_close()")
                self.on_close()
            else:
                debug("MainWindow.closeEvent() - 用户取消退出")
                event.ignore()  # 取消关闭
                return
        else:
            # 默认退出程序
            error("MainWindow.closeEvent() - on_close为None，退出QApplication")
            from PyQt5.QtWidgets import QApplication
            QApplication.instance().quit()
        event.accept()
        debug("MainWindow.closeEvent() - 事件已接受")
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"币安事件合约群控交易系统 - {self.username}")
        self.setGeometry(100, 100, 800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部信息栏
        info_layout = QVBoxLayout()
        
        # 第一行：用户和币安状态
        first_row = QHBoxLayout()
        first_row.addWidget(QLabel(f"用户: {self.username}"))
        self.binance_status_label = QLabel("币安: 未登录")
        self.binance_status_label.setStyleSheet("color: red;")
        first_row.addWidget(self.binance_status_label)
        first_row.addStretch()
        info_layout.addLayout(first_row)
        
        # 第二行：倒计时信息
        second_row = QHBoxLayout()
        self.restart_countdown_label = QLabel("程序重启倒计时: --:--:--")
        self.restart_countdown_label.setStyleSheet("color: blue;")
        second_row.addWidget(self.restart_countdown_label)
        
        self.account_expire_label = QLabel("账号到期时间: --")
        self.account_expire_label.setStyleSheet("color: orange;")
        second_row.addWidget(self.account_expire_label)
        second_row.addStretch()
        info_layout.addLayout(second_row)
        
        layout.addLayout(info_layout)
        
        # 初始化倒计时显示
        self._update_timers()
        
        # 控制面板
        control_group = QWidget()
        control_layout = QVBoxLayout()
        
        # 下单金额设置
        amount_layout = QHBoxLayout()
        amount_layout.addWidget(QLabel("下单金额:"))
        self.amount_input = QLineEdit()
        self.amount_input.setText("5")
        self.amount_input.setFixedWidth(100)
        amount_layout.addWidget(self.amount_input)
        
        set_amount_btn = QPushButton("设置金额")
        set_amount_btn.clicked.connect(self._handle_set_amount)
        amount_layout.addWidget(set_amount_btn)
        amount_layout.addStretch()
        control_layout.addLayout(amount_layout)
        
        # 按钮组
        button_layout = QHBoxLayout()
        self.binance_login_btn = QPushButton("登录币安账号")
        self.binance_login_btn.clicked.connect(self.on_binance_login)
        button_layout.addWidget(self.binance_login_btn)
        
        self.start_btn = QPushButton("开始自动下单")
        self.start_btn.clicked.connect(self._handle_start_order)
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("停止自动下单")
        self.stop_btn.clicked.connect(self._handle_stop_order)
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        logout_btn = QPushButton("退出登录")
        logout_btn.clicked.connect(self.on_logout)
        button_layout.addWidget(logout_btn)
        
        control_layout.addLayout(button_layout)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 日志区域
        log_label = QLabel("日志:")
        layout.addWidget(log_label)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setFont(QFont("Courier", 10))
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4;")
        layout.addWidget(self.log_area)
        
        central_widget.setLayout(layout)
    
    def _handle_set_amount(self):
        """处理设置金额"""
        try:
            amount = float(self.amount_input.text())
            if amount < 5 or amount > 200:
                QMessageBox.warning(self, "错误", "下单金额必须在5-200之间")
                return
            self.on_set_order_amount(amount)
            self.log(f"下单金额已设置为: {amount}")
        except ValueError:
            QMessageBox.warning(self, "错误", "请输入有效的数字")
    
    def _handle_start_order(self):
        """处理开始下单"""
        # 检查币安是否已登录
        if not self.binance_logged_in:
            QMessageBox.warning(self, "错误", "请先登录币安账号才能开始自动下单")
            return
        
        self.order_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.on_start_order()
    
    def _handle_stop_order(self):
        """处理停止下单"""
        self.order_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.on_stop_order()
    
    def set_binance_logged_in(self, logged_in: bool):
        """设置币安登录状态"""
        def safe_print(*args, **kwargs):
            """安全地打印文本，处理编码错误"""
            try:
                print(*args, **kwargs)
            except UnicodeEncodeError:
                try:
                    safe_args = []
                    for arg in args:
                        if isinstance(arg, str):
                            safe_args.append(arg.encode('ascii', 'replace').decode('ascii'))
                        else:
                            safe_args.append(arg)
                    print(*safe_args, **kwargs)
                except:
                    pass
            except:
                pass
        
        safe_print(f"set_binance_logged_in被调用: logged_in={logged_in}")
        self.binance_logged_in = logged_in
        if logged_in:
            self.binance_status_label.setText("币安: 已登录")
            self.binance_status_label.setStyleSheet("color: green;")
            self.binance_login_btn.setText("重新登录币安")
            self.log("[OK] 币安登录状态已更新为：已登录")
            safe_print("[OK] GUI状态已更新为：已登录")
        else:
            self.binance_status_label.setText("币安: 未登录")
            self.binance_status_label.setStyleSheet("color: red;")
            self.binance_login_btn.setText("登录币安账号")
            self.log("币安登录状态已更新为：未登录")
            safe_print("GUI状态已更新为：未登录")
    
    def log(self, message: str):
        """添加日志"""
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%H:%M:%S")
            # 安全地处理Unicode字符，避免编码错误
            try:
                log_text = f"[{timestamp}] {message}"
                self.log_area.append(log_text)
            except UnicodeEncodeError:
                # 如果编码失败，尝试替换Unicode字符
                safe_message = message.encode('ascii', 'replace').decode('ascii')
                log_text = f"[{timestamp}] {safe_message}"
                self.log_area.append(log_text)
            except Exception as e:
                # 如果还是失败，使用最基本的ASCII字符
                try:
                    safe_message = str(message).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
                    log_text = f"[{timestamp}] {safe_message}"
                    self.log_area.append(log_text)
                except:
                    self.log_area.append(f"[{timestamp}] [日志编码错误]")
            # 自动滚动到底部
            scrollbar = self.log_area.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            # 如果日志输出完全失败，至少尝试输出到控制台
            try:
                print(f"[日志输出失败] {e}")
            except:
                pass
    
    def _update_timers(self):
        """更新倒计时显示"""
        now = datetime.now()
        
        # 程序重启倒计时（24小时）
        from ..config import settings
        restart_expire_time = self.login_time + timedelta(hours=settings.session_expire_hours)
        restart_remaining = restart_expire_time - now
        
        if restart_remaining.total_seconds() > 0:
            hours = int(restart_remaining.total_seconds() // 3600)
            minutes = int((restart_remaining.total_seconds() % 3600) // 60)
            seconds = int(restart_remaining.total_seconds() % 60)
            self.restart_countdown_label.setText(f"程序重启倒计时: {hours:02d}:{minutes:02d}:{seconds:02d}")
        else:
            self.restart_countdown_label.setText("程序重启倒计时: 已到期")
            self.restart_countdown_label.setStyleSheet("color: red;")
        
        # 账号到期时间
        if self.account_expire_at_str:
            try:
                account_expire_at = datetime.fromisoformat(self.account_expire_at_str.replace('Z', '+00:00'))
                account_remaining = account_expire_at - now
                if account_remaining.total_seconds() > 0:
                    expire_str = account_expire_at.strftime("%Y-%m-%d %H:%M:%S")
                    self.account_expire_label.setText(f"账号到期时间: {expire_str}")
                else:
                    self.account_expire_label.setText("账号到期时间: 已到期")
                    self.account_expire_label.setStyleSheet("color: red;")
            except:
                self.account_expire_label.setText(f"账号到期时间: {self.account_expire_at_str}")
        else:
            self.account_expire_label.setText("账号到期时间: 未设置")
    
    def show(self):
        """显示窗口"""
        super().show()

