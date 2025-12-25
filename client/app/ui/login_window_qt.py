"""
登录窗口 - PyQt5版本
"""
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, 
    QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtGui import QFont, QCloseEvent
from typing import Callable


class LoginWindow(QWidget):
    """登录窗口类"""
    
    def __init__(self, on_login_success: Callable, on_close: Callable = None):
        super().__init__()
        self.on_login_success = on_login_success
        self.on_close = on_close
        self.login_success = False  # 标记登录是否成功
        self.init_ui()
    
    def closeEvent(self, event: QCloseEvent):
        """窗口关闭事件"""
        # 如果登录成功，关闭登录窗口时不退出程序
        if self.login_success:
            event.accept()
            return
        
        # 如果登录窗口关闭，且没有主窗口，则退出程序
        if self.on_close:
            self.on_close()
        else:
            # 检查是否有其他窗口（主窗口）
            app = QApplication.instance()
            if app:
                # 检查是否有其他窗口（包括隐藏的窗口）
                widgets = app.allWidgets()
                # 查找所有顶级窗口（不包括登录窗口本身）
                top_level_windows = [w for w in widgets if isinstance(w, QWidget) and w.isWindow() and w != self]
                if not top_level_windows:
                    # 没有其他窗口，退出程序
                    app.quit()
        event.accept()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("币安事件合约群控交易系统 - 登录")
        self.setFixedSize(400, 250)
        self._center_window()
        
        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # 标题
        title = QLabel("币安事件合约群控交易系统")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 用户名
        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setFixedWidth(80)
        self.username_entry = QLineEdit()
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_entry)
        layout.addLayout(username_layout)
        
        # 密码
        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFixedWidth(80)
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_entry)
        layout.addLayout(password_layout)
        
        # 登录按钮
        login_button = QPushButton("登录")
        login_button.setFixedHeight(40)
        login_button.clicked.connect(self._handle_login)
        layout.addWidget(login_button)
        
        # 绑定回车键
        self.password_entry.returnPressed.connect(self._handle_login)
        
        self.setLayout(layout)
    
    def _center_window(self):
        """窗口居中"""
        from PyQt5.QtWidgets import QDesktopWidget
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def _handle_login(self):
        """处理登录"""
        username = self.username_entry.text().strip()
        password = self.password_entry.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "错误", "请输入用户名和密码")
            return
        
        # 调用回调函数
        self.on_login_success(username, password)
    
    def show_error(self, message: str):
        """显示错误信息"""
        QMessageBox.critical(self, "登录失败", message)
    
    def show(self):
        """显示窗口"""
        super().show()

