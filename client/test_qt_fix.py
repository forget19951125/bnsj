#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Qt插件路径修复是否生效
"""
import sys
import os

print("=" * 60)
print("测试Qt插件路径修复")
print("=" * 60)
print()

# 在导入PyQt5之前设置Qt插件路径（Windows平台）
if sys.platform == 'win32':
    try:
        # 尝试找到PyQt5的插件路径
        import site
        
        # 查找site-packages目录
        site_packages = site.getsitepackages()
        if not site_packages:
            # 如果getsitepackages返回空，尝试使用distutils
            try:
                from distutils.sysconfig import get_python_lib
                site_packages = [get_python_lib()]
            except:
                pass
        
        print("查找PyQt5插件路径...")
        # 在所有可能的site-packages目录中查找PyQt5
        plugin_path = None
        for sp in site_packages:
            pyqt5_path = os.path.join(sp, 'PyQt5', 'Qt5', 'plugins')
            if os.path.exists(pyqt5_path):
                plugin_path = pyqt5_path
                print(f"找到插件路径: {plugin_path}")
                os.environ['QT_PLUGIN_PATH'] = plugin_path
                break
        
        if not plugin_path:
            print("警告: 未找到PyQt5插件路径")
    except Exception as e:
        print(f"设置插件路径时出错: {e}")
        import traceback
        traceback.print_exc()

print()
print("尝试导入PyQt5...")
try:
    import PyQt5
    from PyQt5.QtCore import QCoreApplication, PYQT_VERSION_STR, QT_VERSION_STR
    print(f"✓ PyQt5导入成功")
    print(f"  PyQt5版本: {PYQT_VERSION_STR}")
    print(f"  Qt版本: {QT_VERSION_STR}")
except ImportError as e:
    print(f"✗ PyQt5导入失败: {e}")
    print("请先安装PyQt5: pip install PyQt5")
    sys.exit(1)

print()
print("尝试创建QApplication...")
try:
    from PyQt5.QtWidgets import QApplication
    
    # 设置插件路径
    if sys.platform == 'win32' and plugin_path:
        if not QCoreApplication.instance():
            QCoreApplication.setLibraryPaths([plugin_path])
            print(f"✓ 已设置Qt插件路径: {plugin_path}")
    
    # 创建QApplication
    app = QApplication(sys.argv)
    print("✓ QApplication创建成功！")
    print("✓ Qt平台插件初始化成功！")
    
    app.quit()
    print()
    print("=" * 60)
    print("测试通过！Qt环境正常，可以运行客户端了")
    print("=" * 60)
    
except Exception as e:
    print(f"✗ QApplication创建失败: {e}")
    print()
    print("可能的解决方案:")
    print("1. 运行修复脚本: fix_qt_plugin.bat")
    print("2. 安装PyQt5-Qt5: pip install PyQt5-Qt5")
    print("3. 重新安装PyQt5: pip uninstall PyQt5 && pip install PyQt5")
    import traceback
    traceback.print_exc()
    sys.exit(1)

