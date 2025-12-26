@echo off
REM Windows批处理脚本 - 修复Qt平台插件问题
echo ========================================
echo Qt平台插件修复脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [1/3] 检查PyQt5安装...
python -c "import PyQt5; print('PyQt5已安装')" 2>nul
if errorlevel 1 (
    echo [错误] PyQt5未安装，正在安装...
    python -m pip install PyQt5>=5.15.0
    if errorlevel 1 (
        echo [错误] PyQt5安装失败
        pause
        exit /b 1
    )
)

echo.
echo [2/3] 安装PyQt5-Qt5（包含Qt运行时库和平台插件）...
python -m pip install PyQt5-Qt5
if errorlevel 1 (
    echo [警告] PyQt5-Qt5安装失败，尝试使用国内镜像源...
    python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt5-Qt5
)

echo.
echo [3/3] 验证Qt环境...
python check_qt_env.py

if errorlevel 1 (
    echo.
    echo [警告] Qt环境检查失败
    echo.
    echo 可能的解决方案:
    echo 1. 确保已安装Visual C++ Redistributable
    echo    下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe
    echo 2. 重新安装PyQt5: pip uninstall PyQt5 PyQt5-Qt5 ^&^& pip install PyQt5 PyQt5-Qt5
    echo 3. 如果使用虚拟环境，确保已激活虚拟环境
) else (
    echo.
    echo [成功] Qt环境修复完成！
    echo 现在可以运行客户端了: python run_client.py
)

echo.
pause

