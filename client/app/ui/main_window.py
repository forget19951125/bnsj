"""
主窗口
"""
import tkinter as tk
from tkinter import messagebox, scrolledtext
from typing import Callable, Optional
from datetime import datetime
from ..config import settings


class MainWindow:
    """主窗口类"""
    
    def __init__(
        self,
        username: str,
        on_binance_login: Callable,
        on_set_order_amount: Callable,
        on_start_order: Callable,
        on_stop_order: Callable,
        on_logout: Callable
    ):
        self.username = username
        self.on_binance_login = on_binance_login
        self.on_set_order_amount = on_set_order_amount
        self.on_start_order = on_start_order
        self.on_stop_order = on_stop_order
        self.on_logout = on_logout
        
        self.window = tk.Tk()
        self.window.title(f"币安事件合约群控交易系统 - {username}")
        self.window.geometry("800x600")
        
        # 创建UI
        self._create_widgets()
        
        # 状态
        self.binance_logged_in = False
        self.order_running = False
    
    def _create_widgets(self):
        """创建UI组件"""
        # 顶部信息栏
        info_frame = tk.Frame(self.window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(info_frame, text=f"用户: {self.username}", font=("Arial", 10)).pack(side=tk.LEFT)
        self.binance_status_label = tk.Label(
            info_frame,
            text="币安: 未登录",
            font=("Arial", 10),
            fg="red"
        )
        self.binance_status_label.pack(side=tk.LEFT, padx=20)
        
        tk.Button(info_frame, text="退出登录", command=self._handle_logout).pack(side=tk.RIGHT)
        
        # 币安登录区域
        binance_frame = tk.LabelFrame(self.window, text="币安账号绑定", padx=10, pady=10)
        binance_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.binance_login_button = tk.Button(
            binance_frame,
            text="扫码登录币安",
            command=self._handle_binance_login,
            width=20
        )
        self.binance_login_button.pack()
        
        # 交易设置区域
        settings_frame = tk.LabelFrame(self.window, text="交易设置", padx=10, pady=10)
        settings_frame.pack(fill=tk.X, padx=10, pady=5)
        
        amount_frame = tk.Frame(settings_frame)
        amount_frame.pack()
        tk.Label(amount_frame, text="下单金额 (USDT):").pack(side=tk.LEFT, padx=5)
        self.amount_entry = tk.Entry(amount_frame, width=10)
        self.amount_entry.insert(0, str(settings.default_order_amount))
        self.amount_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(amount_frame, text=f"(范围: {settings.min_order_amount}-{settings.max_order_amount})").pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            settings_frame,
            text="保存设置",
            command=self._handle_save_amount
        ).pack(pady=5)
        
        # 订单控制区域
        control_frame = tk.LabelFrame(self.window, text="订单控制", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        button_frame = tk.Frame(control_frame)
        button_frame.pack()
        
        self.start_button = tk.Button(
            button_frame,
            text="开始自动下单",
            command=self._handle_start_order,
            width=15,
            height=2,
            state=tk.DISABLED
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(
            button_frame,
            text="停止自动下单",
            command=self._handle_stop_order,
            width=15,
            height=2,
            state=tk.DISABLED
        )
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 日志区域
        log_frame = tk.LabelFrame(self.window, text="运行日志", padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _handle_binance_login(self):
        """处理币安登录"""
        self.on_binance_login()
    
    def _handle_save_amount(self):
        """保存下单金额"""
        try:
            amount = float(self.amount_entry.get())
            if amount < settings.min_order_amount or amount > settings.max_order_amount:
                messagebox.showerror(
                    "错误",
                    f"金额必须在 {settings.min_order_amount}-{settings.max_order_amount} 之间"
                )
                return
            
            self.on_set_order_amount(amount)
            self.log(f"下单金额已设置为: {amount} USDT")
            messagebox.showinfo("成功", "设置已保存")
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def _handle_start_order(self):
        """开始自动下单"""
        if not self.binance_logged_in:
            messagebox.showerror("错误", "请先登录币安账号")
            return
        
        self.on_start_order()
        self.order_running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.log("开始自动下单...")
    
    def _handle_stop_order(self):
        """停止自动下单"""
        self.on_stop_order()
        self.order_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log("已停止自动下单")
    
    def _handle_logout(self):
        """退出登录"""
        if self.order_running:
            if not messagebox.askyesno("确认", "正在运行自动下单，确定要退出吗？"):
                return
            self._handle_stop_order()
        
        self.on_logout()
        self.window.destroy()
    
    def set_binance_logged_in(self, logged_in: bool):
        """设置币安登录状态"""
        self.binance_logged_in = logged_in
        if logged_in:
            self.binance_status_label.config(text="币安: 已登录", fg="green")
            self.start_button.config(state=tk.NORMAL)
        else:
            self.binance_status_label.config(text="币安: 未登录", fg="red")
            self.start_button.config(state=tk.DISABLED)
    
    def log(self, message: str):
        """添加日志"""
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def show(self):
        """显示窗口"""
        self.window.mainloop()
    
    def close(self):
        """关闭窗口"""
        self.window.destroy()

