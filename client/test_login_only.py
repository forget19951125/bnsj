#!/usr/bin/env python3
"""
最简单的登录窗口测试 - 不导入任何app模块
"""
# 在导入任何东西之前，先patch platform
import platform
_original_release = platform.release

def patched_release():
    """返回假的macOS版本26.0.0"""
    return '26.0.0'

platform.release = patched_release

import tkinter as tk
from tkinter import messagebox

class SimpleLoginWindow:
    """简单的登录窗口"""
    
    def __init__(self, on_login_success):
        self.on_login_success = on_login_success
        self.window = tk.Tk()
        self.window.title("币安事件合约群控交易系统 - 登录")
        self.window.geometry("400x250")
        self.window.resizable(False, False)
        
        # 居中显示
        self._center_window()
        
        # 创建UI
        self._create_widgets()
    
    def _center_window(self):
        """窗口居中"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_widgets(self):
        """创建UI组件"""
        # 标题
        title_label = tk.Label(
            self.window,
            text="币安事件合约群控交易系统",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=20)
        
        # 用户名
        username_frame = tk.Frame(self.window)
        username_frame.pack(pady=10)
        tk.Label(username_frame, text="用户名:", width=10).pack(side=tk.LEFT)
        self.username_entry = tk.Entry(username_frame, width=20)
        self.username_entry.pack(side=tk.LEFT)
        
        # 密码
        password_frame = tk.Frame(self.window)
        password_frame.pack(pady=10)
        tk.Label(password_frame, text="密码:", width=10).pack(side=tk.LEFT)
        self.password_entry = tk.Entry(password_frame, width=20, show="*")
        self.password_entry.pack(side=tk.LEFT)
        
        # 登录按钮
        login_button = tk.Button(
            self.window,
            text="登录",
            command=self._handle_login,
            width=15,
            height=2
        )
        login_button.pack(pady=20)
        
        # 绑定回车键
        self.window.bind('<Return>', lambda e: self._handle_login())
    
    def _handle_login(self):
        """处理登录"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return
        
        # 调用回调函数
        print(f"登录尝试: 用户名={username}, 密码={'*' * len(password)}")
        print("✓ 登录界面功能正常！")
        self.on_login_success(username, password)
    
    def show(self):
        """显示窗口"""
        self.window.mainloop()
    
    def close(self):
        """关闭窗口"""
        self.window.destroy()


def handle_login(username, password):
    """处理登录的回调函数"""
    print(f"登录成功: {username}")
    print("✓ 登录功能测试完成")


if __name__ == "__main__":
    print("启动最简单的登录窗口测试...")
    print("如果看到登录窗口，说明GUI正常")
    print("")
    
    window = SimpleLoginWindow(handle_login)
    window.show()

