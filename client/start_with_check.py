#!/usr/bin/env python3
"""
带Qt环境检查的客户端启动脚本
在启动客户端前自动检查Qt环境
"""
import sys
import os
import traceback
import warnings

# 设置环境变量，尝试绕过Playwright的版本检查
os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '1'
os.environ['PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS'] = '1'

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

def check_qt_before_start():
    """启动前检查Qt环境"""
    print("=" * 60)
    print("正在检查Qt环境...")
    print("=" * 60)
    
    # 检查PyQt5是否安装
    try:
        import PyQt5
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QCoreApplication
        
        # 尝试创建QApplication（不显示窗口）
        app = QApplication(sys.argv)
        app.quit()
        
        print("✓ Qt环境检查通过")
        print(f"  PyQt5版本: {PyQt5.QtCore.PYQT_VERSION_STR}")
        print(f"  Qt版本: {PyQt5.QtCore.QT_VERSION_STR}")
        print()
        return True
        
    except ImportError as e:
        print("✗ PyQt5未安装")
        print(f"  错误: {e}")
        print()
        print("解决方案:")
        print("  1. 运行安装脚本: install_qt_env.bat (Windows) 或 install_qt_env.sh (Linux/Mac)")
        print("  2. 或手动安装: pip install PyQt5>=5.15.0")
        print()
        return False
        
    except Exception as e:
        print("✗ Qt环境检查失败")
        print(f"  错误: {e}")
        print()
        print("解决方案:")
        print("  1. 运行诊断脚本: python check_qt_env.py")
        print("  2. 重新安装PyQt5: pip uninstall PyQt5 && pip install PyQt5>=5.15.0")
        print("  3. Windows系统可以尝试: pip install PyQt5-Qt5")
        print()
        return False

def main():
    """主函数"""
    # 先检查Qt环境
    if not check_qt_before_start():
        print("=" * 60)
        print("Qt环境检查失败，无法启动客户端")
        print("请按照上面的提示解决Qt环境问题后重试")
        print("=" * 60)
        input("按回车键退出...")
        sys.exit(1)
    
    # Qt环境正常，启动客户端
    try:
        print("=" * 60)
        print("正在启动客户端...")
        print("=" * 60)
        print()
        
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
        input("\n按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()

