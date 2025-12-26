@echo off
REM Windows批处理脚本 - 安装Qt环境
echo ========================================
echo Qt环境安装脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [1/3] 卸载旧版本的PyQt5...
python -m pip uninstall -y PyQt5 PyQt5-Qt5 PyQt5-sip

echo.
echo [2/3] 安装PyQt5...
python -m pip install --upgrade pip
python -m pip install PyQt5>=5.15.0

if errorlevel 1 (
    echo [错误] PyQt5安装失败
    echo 尝试使用国内镜像源...
    python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt5>=5.15.0
)

echo.
echo [3/3] 验证安装...
python check_qt_env.py

if errorlevel 1 (
    echo.
    echo [警告] Qt环境检查失败，请查看上面的错误信息
    echo.
    echo 可能的解决方案:
    echo 1. 确保Python版本 >= 3.7
    echo 2. 尝试手动安装: pip install PyQt5 PyQt5-Qt5
    echo 3. 如果使用虚拟环境，确保已激活虚拟环境
    echo 4. 检查是否有权限问题
) else (
    echo.
    echo [成功] Qt环境安装完成！
)

echo.
pause

