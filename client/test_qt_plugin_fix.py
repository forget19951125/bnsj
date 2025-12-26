#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Qt插件路径修复是否有效
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

# 在导入PyQt5之前设置Qt插件路径（Windows平台）
if sys.platform == 'win32' and not os.environ.get('QT_PLUGIN_PATH'):
    try:
        # 方法1: 优先通过导入PyQt5来查找（最可靠的方法）
        try:
            import PyQt5
            from PyQt5 import QtCore
            qt_core_path = QtCore.__file__
            qt_dir = os.path.dirname(qt_core_path)
            
            # 检查多个可能的插件路径
            possible_plugin_paths = [
                os.path.join(qt_dir, 'Qt5', 'plugins'),
                os.path.join(qt_dir, 'plugins'),
                os.path.join(qt_dir, '..', 'Qt5', 'plugins'),
            ]
            
            plugin_path = None
            for path in possible_plugin_paths:
                abs_path = os.path.abspath(path)
                platforms_path = os.path.join(abs_path, 'platforms')
                qwindows_dll = os.path.join(platforms_path, 'qwindows.dll')
                if os.path.exists(qwindows_dll):
                    plugin_path = abs_path
                    break
            
            if plugin_path:
                os.environ['QT_PLUGIN_PATH'] = plugin_path
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                print(f"✓ 已设置Qt插件路径: {plugin_path}")
            else:
                print("✗ 未找到Qt插件路径")
        except ImportError:
            print("✗ PyQt5未安装")
            sys.exit(1)
        except Exception as e:
            print(f"✗ 通过PyQt5查找路径失败: {e}")
            sys.exit(1)
    except Exception as e:
        print(f"✗ 设置Qt插件路径时出错: {e}")
        sys.exit(1)

# 测试创建QApplication
print("\n测试创建QApplication...")
try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication
    
    # 设置插件路径（如果还没设置）
    if sys.platform == 'win32':
        plugin_path = os.environ.get('QT_PLUGIN_PATH')
        if plugin_path and not QCoreApplication.instance():
            QCoreApplication.setLibraryPaths([plugin_path])
            print(f"✓ 已通过QCoreApplication设置插件路径")
    
    # 创建QApplication
    app = QApplication(sys.argv)
    print("✓ QApplication创建成功！")
    print("✓ Qt平台插件初始化成功！")
    app.quit()
    print("\n✓ 测试通过！Qt环境正常，可以运行客户端了")
except Exception as e:
    print(f"\n✗ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

