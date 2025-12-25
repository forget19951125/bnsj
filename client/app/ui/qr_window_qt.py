"""
二维码窗口 - PyQt5版本
"""
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
import qrcode
from io import BytesIO


class QRWindow(QWidget):
    """二维码窗口类"""
    
    def __init__(self, qr_data: str):
        super().__init__()
        self.qr_data = qr_data
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("币安登录二维码")
        self.setFixedSize(400, 450)
        self._center_window()
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 提示文字
        label = QLabel("请使用币安App扫描二维码登录")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(self.qr_data)
        qr.make(fit=True)
        
        # 创建二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为QPixmap
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qimage = QImage()
        qimage.loadFromData(buffer.getvalue())
        pixmap = QPixmap.fromImage(qimage)
        
        # 显示二维码
        qr_label = QLabel()
        qr_label.setPixmap(pixmap)
        qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qr_label)
        
        self.setLayout(layout)
    
    def _center_window(self):
        """窗口居中"""
        from PyQt5.QtWidgets import QDesktopWidget
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def close_window(self):
        """关闭窗口"""
        self.close()
    
    def closeEvent(self, event):
        """处理关闭事件"""
        self.close()
        event.accept()

