#!/bin/bash
# Linux/Mac shell脚本 - 安装Qt环境

echo "========================================"
echo "Qt环境安装脚本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到Python3，请先安装Python 3.7+"
    exit 1
fi

echo "[1/3] 卸载旧版本的PyQt5..."
python3 -m pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip

echo ""
echo "[2/3] 安装PyQt5..."
python3 -m pip install --upgrade pip
python3 -m pip install PyQt5>=5.15.0

if [ $? -ne 0 ]; then
    echo "[错误] PyQt5安装失败"
    echo "尝试使用国内镜像源..."
    python3 -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt5>=5.15.0
fi

echo ""
echo "[3/3] 验证安装..."
python3 check_qt_env.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[警告] Qt环境检查失败，请查看上面的错误信息"
    echo ""
    echo "可能的解决方案:"
    echo "1. 确保Python版本 >= 3.7"
    echo "2. 尝试手动安装: pip3 install PyQt5 PyQt5-Qt5"
    echo "3. 如果使用虚拟环境，确保已激活虚拟环境"
    echo "4. Linux系统可能需要安装系统Qt库:"
    echo "   Ubuntu/Debian: sudo apt-get install python3-pyqt5"
    echo "   CentOS/RHEL: sudo yum install python3-qt5"
    echo "   macOS: brew install pyqt5"
else
    echo ""
    echo "[成功] Qt环境安装完成！"
fi

