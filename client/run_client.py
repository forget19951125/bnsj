#!/usr/bin/env python3
"""
客户端启动脚本
"""
import sys
import os
import traceback
import warnings

# 设置环境变量，尝试绕过Playwright的版本检查
os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'

# 在导入PyQt5之前设置Qt插件路径（Windows平台）
# runtime_hook.py 应该已经设置了，但这里作为备用
if sys.platform == 'win32' and not os.environ.get('QT_PLUGIN_PATH'):
    try:
        # 方法0: 如果是打包后的环境，优先检查 _MEIPASS 目录
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            meipass_plugin_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt5', 'plugins')
            if os.path.exists(meipass_plugin_path):
                platforms_path = os.path.join(meipass_plugin_path, 'platforms')
                qwindows_dll = os.path.join(platforms_path, 'qwindows.dll')
                if os.path.exists(qwindows_dll):
                    os.environ['QT_PLUGIN_PATH'] = meipass_plugin_path
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = meipass_plugin_path
                    print(f"已设置Qt插件路径（打包环境）: {meipass_plugin_path}")
        
        # 方法1: 优先通过导入PyQt5来查找（最可靠的方法）
        if not os.environ.get('QT_PLUGIN_PATH'):
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
                    print(f"已设置Qt插件路径: {plugin_path}")
            except ImportError:
                # PyQt5未安装，使用备用方法
                pass
            except Exception as e:
                print(f"通过PyQt5查找路径失败: {e}")
        
        # 方法2: 如果方法1失败，尝试查找site-packages目录（备用方法）
        if not os.environ.get('QT_PLUGIN_PATH'):
            try:
                import site
                import sysconfig
                
                # 收集所有可能的site-packages路径
                site_packages = []
                site_packages.extend(site.getsitepackages())
                try:
                    site_packages.append(site.getusersitepackages())
                except:
                    pass
                try:
                    site_packages.append(sysconfig.get_path('purelib'))
                except:
                    pass
                try:
                    from distutils.sysconfig import get_python_lib
                    site_packages.append(get_python_lib())
                except:
                    pass
                
                # 去重并检查每个路径
                plugin_path = None
                for sp in set(site_packages):
                    if not sp:
                        continue
                    pyqt5_path = os.path.join(sp, 'PyQt5', 'Qt5', 'plugins')
                    if os.path.exists(pyqt5_path):
                        platforms_path = os.path.join(pyqt5_path, 'platforms')
                        qwindows_dll = os.path.join(platforms_path, 'qwindows.dll')
                        if os.path.exists(qwindows_dll):
                            plugin_path = pyqt5_path
                            break
                
                if plugin_path:
                    os.environ['QT_PLUGIN_PATH'] = plugin_path
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                    print(f"已设置Qt插件路径（备用方法）: {plugin_path}")
                else:
                    print("警告: 未找到Qt插件路径，将尝试自动查找")
            except Exception as e:
                print(f"设置Qt插件路径时出错: {e}")
    except Exception as e:
        print(f"设置Qt插件路径时出错: {e}")

# 忽略警告
warnings.filterwarnings('ignore')

def main():
    try:
        print("正在启动客户端...")
        from app.main import ClientApp
        
        app = ClientApp()
        print("客户端已初始化，显示登录窗口...")
        app.run()
    except KeyboardInterrupt:
        print("\n用户中断，退出程序")
        sys.exit(0)
    except Exception as e:
        print(f"\n启动失败: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

