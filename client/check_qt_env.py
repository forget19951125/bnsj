#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt环境检查脚本
用于诊断PyQt5环境是否正确安装
"""
import sys
import platform
import io

# Windows控制台编码修复
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def check_qt_environment():
    """检查Qt环境"""
    print("=" * 60)
    print("Qt环境诊断工具")
    print("=" * 60)
    print(f"Python版本: {sys.version}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print()
    
    # 检查PyQt5是否安装
    print("1. 检查PyQt5安装...")
    try:
        import PyQt5
        from PyQt5 import QtCore
        print(f"   [OK] PyQt5已安装")
        print(f"   版本: {QtCore.PYQT_VERSION_STR}")
        print(f"   Qt版本: {QtCore.QT_VERSION_STR}")
    except ImportError as e:
        print(f"   [ERROR] PyQt5未安装: {e}")
        print("   解决方案: pip install PyQt5")
        return False
    except Exception as e:
        print(f"   [ERROR] PyQt5导入失败: {e}")
        return False
    
    print()
    
    # 检查Qt核心模块
    print("2. 检查Qt核心模块...")
    modules = [
        ('QtWidgets', 'QApplication'),
        ('QtCore', 'QObject'),
        ('QtGui', 'QFont'),
    ]
    
    all_modules_ok = True
    for module_name, class_name in modules:
        try:
            module = __import__(f'PyQt5.{module_name}', fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"   [OK] {module_name}.{class_name} 可用")
        except Exception as e:
            print(f"   [ERROR] {module_name}.{class_name} 不可用: {e}")
            all_modules_ok = False
    
    if not all_modules_ok:
        return False
    
    print()
    
    # 尝试创建QApplication
    print("3. 测试创建QApplication...")
    try:
        from PyQt5.QtWidgets import QApplication
        # 不显示窗口，只测试能否创建
        app = QApplication(sys.argv)
        print("   [OK] QApplication创建成功")
        app.quit()
    except Exception as e:
        print(f"   [ERROR] QApplication创建失败: {e}")
        print("   这通常意味着Qt运行时库缺失或损坏")
        print("   解决方案:")
        print("   1. 重新安装PyQt5: pip uninstall PyQt5 && pip install PyQt5")
        print("   2. 如果问题仍然存在，尝试安装PyQt5-Qt5: pip install PyQt5-Qt5")
        return False
    
    print()
    
    # 检查Qt插件路径
    print("4. 检查Qt插件路径...")
    try:
        from PyQt5.QtCore import QCoreApplication
        plugin_paths = QCoreApplication.libraryPaths()
        if plugin_paths:
            print(f"   [OK] 找到 {len(plugin_paths)} 个插件路径:")
            for path in plugin_paths:
                print(f"      - {path}")
        else:
            print("   [WARN] 未找到插件路径（可能正常）")
    except Exception as e:
        print(f"   ⚠ 无法检查插件路径: {e}")
    
    print()
    
    # 检查Qt库文件
    print("5. 检查Qt库文件...")
    try:
        import os
        from PyQt5 import QtCore
        qt_core_path = QtCore.__file__
        qt_dir = os.path.dirname(qt_core_path)
        print(f"   Qt安装目录: {qt_dir}")
        
        # 检查关键DLL文件（Windows）
        if platform.system() == 'Windows':
            dll_files = [
                'Qt5Core.dll',
                'Qt5Gui.dll',
                'Qt5Widgets.dll',
            ]
            dll_dir = os.path.join(qt_dir, '..', '..', '..', 'PyQt5', 'Qt5', 'bin')
            if os.path.exists(dll_dir):
                print(f"   DLL目录: {dll_dir}")
                for dll in dll_files:
                    dll_path = os.path.join(dll_dir, dll)
                    if os.path.exists(dll_path):
                        print(f"   [OK] {dll} 存在")
                    else:
                        print(f"   [ERROR] {dll} 缺失")
    except Exception as e:
        print(f"   [WARN] 无法检查库文件: {e}")
    
    print()
    print("=" * 60)
    print("诊断完成！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = check_qt_environment()
    sys.exit(0 if success else 1)

