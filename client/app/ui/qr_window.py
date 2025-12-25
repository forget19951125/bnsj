"""
二维码窗口
"""
import tkinter as tk
from PIL import Image, ImageTk
import qrcode
from io import BytesIO


class QRWindow:
    """二维码窗口类"""
    
    def __init__(self, qr_data: str):
        self.window = tk.Toplevel()
        self.window.title("币安登录二维码")
        self.window.geometry("400x450")
        self.window.resizable(False, False)
        
        # 居中显示
        self._center_window()
        
        # 创建二维码
        self._create_qr(qr_data)
    
    def _center_window(self):
        """窗口居中"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_qr(self, data: str):
        """创建二维码"""
        # 提示文字
        label = tk.Label(
            self.window,
            text="请使用币安App扫描二维码登录",
            font=("Arial", 12)
        )
        label.pack(pady=10)
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为PhotoImage
        photo = ImageTk.PhotoImage(img)
        
        # 显示二维码
        qr_label = tk.Label(self.window, image=photo)
        qr_label.image = photo  # 保持引用
        qr_label.pack(pady=10)
    
    def close(self):
        """关闭窗口"""
        self.window.destroy()

