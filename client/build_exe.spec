# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller配置文件 - 用于打包客户端为exe
"""
import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# 获取项目根目录
block_cipher = None

# 收集所有需要的模块
hiddenimports = [
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'playwright',
    'playwright._impl',
    'playwright.sync_api',
    'qrcode',
    'PIL',
    'PIL._tkinter_finder',
    'requests',
    'pydantic',
    'pydantic_core',
    'pydantic_settings',
    'app',
    'app.main',
    'app.binance_client',
    'app.api_client',
    'app.config',
    'app.services',
    'app.services.auth_service',
    'app.services.binance_service',
    'app.services.order_service',
    'app.ui',
    'app.ui.login_window_qt',
    'app.ui.main_window_qt',
    'app.ui.qr_window_qt',
    'app.utils',
    'app.utils.logger',
    'app.utils.token_manager',
]

# 收集PyQt5的数据文件
datas = []

# 收集pydantic_core的整个目录（包括所有文件）
try:
    import pydantic_core
    import os
    pydantic_core_path = os.path.dirname(pydantic_core.__file__)
    # 将整个pydantic_core目录添加到datas，确保所有文件（包括.pyd）都被包含
    datas.append((pydantic_core_path, 'pydantic_core'))
    print(f"[打包] [OK] 添加pydantic_core整个目录到datas: {pydantic_core_path}")
except Exception as e:
    print(f"[打包] [警告] 无法添加pydantic_core目录: {e}")

# 注意：PyQt5插件由PyInstaller的hook自动处理，不需要手动添加
# 手动添加可能导致路径编码问题（特别是包含中文的路径）

# 添加google_web浏览器目录（如果存在）
# 获取spec文件所在目录（client目录）
# 在PyInstaller中，SPECPATH变量指向spec文件路径
try:
    # PyInstaller会自动设置SPECPATH变量
    if 'SPECPATH' in globals():
        spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
    else:
        # 如果SPECPATH不存在，使用当前工作目录
        spec_dir = os.getcwd()
except:
    spec_dir = os.getcwd()

# 确保spec_dir是client目录（包含run_client.py和google_web）
# 如果当前目录不对，尝试查找client目录
if not os.path.exists(os.path.join(spec_dir, 'run_client.py')):
    # 尝试从当前工作目录查找
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, 'run_client.py')):
        spec_dir = cwd
    else:
        # 尝试查找父目录下的client目录
        parent_dir = os.path.dirname(spec_dir)
        if os.path.exists(os.path.join(parent_dir, 'client', 'run_client.py')):
            spec_dir = os.path.join(parent_dir, 'client')
        elif os.path.exists(os.path.join(cwd, 'client', 'run_client.py')):
            spec_dir = os.path.join(cwd, 'client')

print(f"[打包] 工作目录: {spec_dir}")

# 查找google_web目录
google_web_path = os.path.join(spec_dir, 'google_web')
google_web_path = os.path.abspath(google_web_path)  # 使用绝对路径

if os.path.exists(google_web_path):
    # 直接添加整个目录，PyInstaller会自动递归包含所有文件和子目录
    # 格式: (源路径, 目标路径) - 目标路径是打包后在exe中的相对路径
    datas.append((google_web_path, 'google_web'))
    print(f"[打包] [OK] 已添加浏览器目录: {google_web_path}")
    
    # 检查chrome.exe是否存在
    chrome_exe = os.path.join(google_web_path, 'chrome.exe')
    if os.path.exists(chrome_exe):
        chrome_size = os.path.getsize(chrome_exe) / (1024 * 1024)  # MB
        print(f"[打包] [OK] 找到chrome.exe，大小: {chrome_size:.2f} MB")
        
        # 统计目录中的文件数量（用于验证）
        file_count = sum([len(files) for r, d, files in os.walk(google_web_path)])
        print(f"[打包] [OK] google_web目录包含约 {file_count} 个文件")
    else:
        print(f"[警告] chrome.exe不存在于: {chrome_exe}")
else:
    print(f"[错误] google_web目录不存在: {google_web_path}")
    print(f"[错误] 请确保google_web目录位于: {spec_dir}")
    print(f"[错误] 打包后的exe可能无法找到浏览器")

# 手动添加PyQt5插件文件到打包中
# 这是必需的，因为自定义hook在失败时跳过了插件收集
try:
    import PyQt5
    from PyQt5 import QtCore
    qt_dir = os.path.dirname(QtCore.__file__)
    
    # 尝试查找插件目录
    plugin_path = None
    possible_plugin_paths = [
        os.path.join(qt_dir, 'Qt5', 'plugins'),
        os.path.join(qt_dir, 'plugins'),
    ]
    
    for path in possible_plugin_paths:
        if os.path.exists(path):
            platforms_path = os.path.join(path, 'platforms')
            if sys.platform == 'win32':
                qwindows_dll = os.path.join(platforms_path, 'qwindows.dll')
                if os.path.exists(qwindows_dll):
                    plugin_path = path
                    # 添加整个plugins目录到datas
                    # 格式: (源路径, 目标路径)
                    datas.append((path, 'PyQt5/Qt5/plugins'))
                    print(f"[打包] [OK] 已添加Qt插件目录: {path}")
                    # 设置环境变量
                    os.environ['QT_PLUGIN_PATH'] = path
                    break
            elif sys.platform == 'darwin':
                qcocoa_dylib = os.path.join(platforms_path, 'qcocoa.dylib')
                if os.path.exists(qcocoa_dylib):
                    plugin_path = path
                    datas.append((path, 'PyQt5/Qt5/plugins'))
                    print(f"[打包] [OK] 已添加Qt插件目录: {path}")
                    os.environ['QT_PLUGIN_PATH'] = path
                    break
    
    if not plugin_path:
        print(f"[打包] [警告] 未找到Qt插件目录，可能影响运行")
except Exception as e:
    print(f"[打包] [警告] 无法添加Qt插件: {e}")
    print(f"[打包] 将继续打包，但可能无法正常运行")

# 收集pydantic_core的二进制文件
binaries = []
try:
    import pydantic_core
    import glob
    pydantic_core_path = os.path.dirname(pydantic_core.__file__)
    pyd_files = glob.glob(os.path.join(pydantic_core_path, '*.pyd'))
    for pyd_file in pyd_files:
        # 添加到binaries，目标路径设为pydantic_core（确保.pyd文件在pydantic_core目录下）
        bin_tuple = (pyd_file, 'pydantic_core')
        binaries.append(bin_tuple)
        print(f"[打包] [OK] 添加pydantic_core二进制文件到binaries: {os.path.basename(pyd_file)}")
    
    # 也添加.dll文件（如果有）
    dll_files = glob.glob(os.path.join(pydantic_core_path, '*.dll'))
    for dll_file in dll_files:
        bin_tuple = (dll_file, 'pydantic_core')
        binaries.append(bin_tuple)
        print(f"[打包] [OK] 添加pydantic_core DLL文件到binaries: {os.path.basename(dll_file)}")
except Exception as e:
    print(f"[打包] [警告] 收集pydantic_core二进制文件失败: {e}")
    import traceback
    traceback.print_exc()

a = Analysis(
    ['run_client.py'],
    pathex=[spec_dir],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[spec_dir],  # 使用自定义hook目录
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],  # 添加运行时hook
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BNSJ客户端',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
)

