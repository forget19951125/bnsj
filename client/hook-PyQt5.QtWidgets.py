# -*- coding: utf-8 -*-
"""
自定义PyQt5.QtWidgets hook - 修复插件路径问题
"""
import os
import sys

# 尝试设置Qt插件路径，避免PyInstaller查找失败
try:
    import PyQt5
    from PyQt5 import QtCore
    qt_dir = os.path.dirname(QtCore.__file__)
    # 尝试查找插件目录
    possible_plugin_paths = [
        os.path.join(qt_dir, 'Qt5', 'plugins'),
        os.path.join(qt_dir, 'plugins'),
    ]
    for plugin_path in possible_plugin_paths:
        if os.path.exists(plugin_path):
            os.environ['QT_PLUGIN_PATH'] = plugin_path
            break
except:
    pass

# 使用PyInstaller的标准hook
try:
    from PyInstaller.utils.hooks.qt import add_qt5_dependencies
    hiddenimports, binaries, datas = add_qt5_dependencies(__file__)
except Exception as e:
    # 如果插件检查失败，只返回基本的导入
    print(f"[Hook] PyQt5插件检查失败，跳过插件收集: {e}")
    hiddenimports = ['PyQt5.QtWidgets', 'PyQt5.QtCore', 'PyQt5.QtGui']
    binaries = []
    datas = []

