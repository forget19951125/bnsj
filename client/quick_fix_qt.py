#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt插件问题快速修复脚本
用于诊断和修复Qt平台插件初始化失败的问题
"""
import sys
import os
import subprocess

# Windows控制台编码修复
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def find_qt_plugins():
    """查找Qt插件路径"""
    print("=" * 60)
    print("查找Qt插件路径...")
    print("=" * 60)
    
    import site
    plugin_paths = []
    
    # 查找site-packages目录
    try:
        site_packages = site.getsitepackages()
        if not site_packages:
            try:
                from distutils.sysconfig import get_python_lib
                site_packages = [get_python_lib()]
            except:
                try:
                    import sysconfig
                    site_packages = [sysconfig.get_path('purelib')]
                except:
                    pass
        
        for sp in site_packages:
            pyqt5_path = os.path.join(sp, 'PyQt5', 'Qt5', 'plugins')
            if os.path.exists(pyqt5_path):
                platforms_path = os.path.join(pyqt5_path, 'platforms')
                if os.path.exists(platforms_path):
                    qwindows_dll = os.path.join(platforms_path, 'qwindows.dll')
                    if os.path.exists(qwindows_dll):
                        plugin_paths.append(pyqt5_path)
                        print(f"✓ 找到插件路径: {pyqt5_path}")
                        print(f"  qwindows.dll存在: {os.path.exists(qwindows_dll)}")
    except Exception as e:
        print(f"查找插件路径时出错: {e}")
    
    return plugin_paths

def test_qt_application():
    """测试Qt应用程序能否正常创建"""
    print("\n" + "=" * 60)
    print("测试Qt应用程序...")
    print("=" * 60)
    
    # 先设置插件路径
    plugin_paths = find_qt_plugins()
    if plugin_paths:
        plugin_path = plugin_paths[0]
        os.environ['QT_PLUGIN_PATH'] = plugin_path
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
        print(f"\n已设置环境变量 QT_PLUGIN_PATH={plugin_path}")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QCoreApplication
        
        # 设置插件路径
        if plugin_paths and not QCoreApplication.instance():
            QCoreApplication.setLibraryPaths(plugin_paths)
        
        # 创建QApplication
        app = QApplication(sys.argv)
        print("✓ QApplication创建成功！")
        print("✓ Qt平台插件初始化成功！")
        app.quit()
        return True
    except Exception as e:
        print(f"✗ QApplication创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def install_pyqt5_qt5():
    """安装PyQt5-Qt5"""
    print("\n" + "=" * 60)
    print("安装PyQt5-Qt5...")
    print("=" * 60)
    
    try:
        print("正在安装PyQt5-Qt5...")
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'PyQt5-Qt5'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ PyQt5-Qt5安装成功")
            return True
        else:
            print("✗ PyQt5-Qt5安装失败，尝试使用国内镜像源...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-i', 
                 'https://pypi.tuna.tsinghua.edu.cn/simple', 'PyQt5-Qt5'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                print("✓ PyQt5-Qt5安装成功（使用镜像源）")
                return True
            else:
                print(f"✗ 安装失败: {result.stderr}")
                return False
    except Exception as e:
        print(f"✗ 安装过程出错: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("Qt插件问题快速修复工具")
    print("=" * 60)
    print()
    
    # 检查PyQt5是否安装
    try:
        import PyQt5
        from PyQt5 import QtCore
        print(f"✓ PyQt5已安装 (版本: {QtCore.PYQT_VERSION_STR})")
    except ImportError:
        print("✗ PyQt5未安装")
        print("\n请先安装PyQt5:")
        print("  pip install PyQt5>=5.15.0")
        return
    
    # 查找插件路径
    plugin_paths = find_qt_plugins()
    
    if not plugin_paths:
        print("\n未找到Qt插件路径，可能需要安装PyQt5-Qt5")
        response = input("\n是否安装PyQt5-Qt5? (y/n): ")
        if response.lower() == 'y':
            if install_pyqt5_qt5():
                plugin_paths = find_qt_plugins()
    
    # 测试Qt应用程序
    if test_qt_application():
        print("\n" + "=" * 60)
        print("✓ 修复成功！Qt环境正常，可以运行客户端了")
        print("=" * 60)
        print("\n运行客户端:")
        print("  python run_client.py")
        print("  或")
        print("  python start_with_check.py")
    else:
        print("\n" + "=" * 60)
        print("✗ 修复失败")
        print("=" * 60)
        print("\n请尝试以下解决方案:")
        print("1. 运行修复脚本: fix_qt_plugin.bat")
        print("2. 手动安装: pip install PyQt5-Qt5")
        print("3. 重新安装PyQt5: pip uninstall PyQt5 PyQt5-Qt5 && pip install PyQt5 PyQt5-Qt5")
        print("4. Windows系统可能需要安装Visual C++ Redistributable")
        print("   下载地址: https://aka.ms/vs/17/release/vc_redist.x64.exe")
        print("5. 运行诊断脚本: python check_qt_env.py")

if __name__ == "__main__":
    main()

