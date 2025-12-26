#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试Qt启动是否正常
"""
import sys
import os
import io

# Windows控制台编码修复
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

print("=" * 60)
print("测试Qt启动")
print("=" * 60)

# 检查环境变量
print("\n1. 检查环境变量:")
qt_plugin_path = os.environ.get('QT_PLUGIN_PATH')
if qt_plugin_path:
    print(f"   [OK] QT_PLUGIN_PATH = {qt_plugin_path}")
else:
    print("   [WARN] QT_PLUGIN_PATH 未设置")

# 尝试导入并创建QApplication
print("\n2. 尝试导入PyQt5...")
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication
    print("   [OK] PyQt5导入成功")
except Exception as e:
    print(f"   [ERROR] PyQt5导入失败: {e}")
    sys.exit(1)

print("\n3. 尝试创建QApplication...")
try:
    # 检查是否已有实例
    if QApplication.instance():
        print("   [WARN] QApplication实例已存在")
        app = QApplication.instance()
    else:
        app = QApplication(sys.argv)
        print("   [OK] QApplication创建成功")
    
    print("   [OK] Qt平台插件初始化成功！")
    app.quit()
    print("\n" + "=" * 60)
    print("[SUCCESS] 测试通过！Qt环境正常")
    print("=" * 60)
except Exception as e:
    print(f"   [ERROR] QApplication创建失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 60)
    print("[FAILED] 测试失败！Qt环境有问题")
    print("=" * 60)
    sys.exit(1)

