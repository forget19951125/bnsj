"""
客户端主程序入口 - 使用PyQt5 GUI
"""
import sys
import os

# 在导入PyQt5之前设置Qt插件路径（Windows和macOS平台）
# 这必须在导入PyQt5之前执行，否则可能导致插件初始化失败
if sys.platform in ('win32', 'darwin') and not os.environ.get('QT_PLUGIN_PATH'):
    try:
        # 方法1: 尝试通过导入PyQt5来获取实际路径（虽然会导入，但不会创建QApplication）
        # 这是最可靠的方法，因为PyQt5知道自己的安装位置
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
            
            # 根据平台检查不同的插件文件
            if sys.platform == 'win32':
                plugin_file = 'qwindows.dll'
            elif sys.platform == 'darwin':
                plugin_file = 'qcocoa.dylib'
            else:
                plugin_file = None
            
            plugin_path = None
            if plugin_file:
                for path in possible_plugin_paths:
                    abs_path = os.path.abspath(path)
                    platforms_path = os.path.join(abs_path, 'platforms')
                    platform_plugin = os.path.join(platforms_path, plugin_file)
                    if os.path.exists(platform_plugin):
                        plugin_path = abs_path
                        break
            
            if plugin_path:
                os.environ['QT_PLUGIN_PATH'] = plugin_path
                os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                print(f"[早期设置] Qt插件路径: {plugin_path}")
        except ImportError:
            # PyQt5未安装，使用备用方法
            pass
        except Exception as e:
            print(f"[早期设置] 通过PyQt5查找路径失败: {e}")
        
        # 方法2: 如果方法1失败，尝试查找site-packages目录（备用方法）
        if not os.environ.get('QT_PLUGIN_PATH'):
            try:
                import site
                import sysconfig
                
                # 收集所有可能的site-packages路径
                site_packages = []
                
                # 标准site-packages
                site_packages.extend(site.getsitepackages())
                
                # 用户site-packages
                try:
                    site_packages.append(site.getusersitepackages())
                except:
                    pass
                
                # sysconfig路径
                try:
                    site_packages.append(sysconfig.get_path('purelib'))
                except:
                    pass
                
                # 尝试distutils（Python < 3.12）
                try:
                    from distutils.sysconfig import get_python_lib
                    site_packages.append(get_python_lib())
                except:
                    pass
                
                # 去重并检查每个路径
                for sp in set(site_packages):
                    if not sp:
                        continue
                    pyqt5_path = os.path.join(sp, 'PyQt5', 'Qt5', 'plugins')
                    if os.path.exists(pyqt5_path):
                        platforms_path = os.path.join(pyqt5_path, 'platforms')
                        # 根据平台检查不同的插件文件
                        if sys.platform == 'win32':
                            platform_plugin = os.path.join(platforms_path, 'qwindows.dll')
                        elif sys.platform == 'darwin':
                            platform_plugin = os.path.join(platforms_path, 'qcocoa.dylib')
                        else:
                            platform_plugin = None
                        
                        if platform_plugin and os.path.exists(platform_plugin):
                            plugin_path = pyqt5_path
                            os.environ['QT_PLUGIN_PATH'] = plugin_path
                            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                            print(f"[早期设置-备用] Qt插件路径: {plugin_path}")
                            break
            except Exception as e:
                print(f"[早期设置] 备用方法失败: {e}")
    except Exception as e:
        # 如果早期设置失败，会在ClientApp.__init__中再次尝试
        print(f"[早期设置] 设置Qt插件路径时出错: {e}")
        import traceback
        traceback.print_exc()

import threading
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QCoreApplication
from .services.auth_service import AuthService
# 延迟导入BinanceService，避免Playwright的macOS版本检查
# from .services.binance_service import BinanceService
from .services.order_service import OrderService
from .api_client import APIClient
from .ui.login_window_qt import LoginWindow
from .ui.main_window_qt import MainWindow
from .ui.qr_window_qt import QRWindow
from .config import settings
from .utils.token_manager import TokenManager


class BinanceLoginSignals(QObject):
    """币安登录信号类，用于跨线程通信"""
    login_success = pyqtSignal()  # 登录成功信号


class ClientApp:
    """客户端应用主类"""
    
    def __init__(self):
        # 在创建QApplication之前设置Qt插件路径（Windows和macOS平台）
        self._setup_qt_plugin_paths()
        
        self.auth_service = AuthService()
        # 延迟初始化BinanceService
        self.binance_service = None
        self.api_client = APIClient()
        self.order_service: OrderService = None
        # TokenManager只用于用户登录token，币安token保存在内存中
        self.token_manager = TokenManager()
        
        # PyQt5应用实例
        self.qt_app = QApplication(sys.argv) if not QApplication.instance() else QApplication.instance()
        self.login_window = None
        self.main_window = None
        self.qr_window = None
        self.session_timer: threading.Timer = None
        self.heartbeat_timer: threading.Timer = None
        
        # 创建信号对象用于跨线程通信
        self.binance_signals = BinanceLoginSignals()
        self.binance_signals.login_success.connect(self._on_binance_login_success)
    
    def _setup_qt_plugin_paths(self):
        """设置Qt插件路径，解决Windows和macOS平台插件初始化失败问题"""
        if sys.platform in ('win32', 'darwin'):
            try:
                # 如果环境变量已设置，直接使用
                plugin_path = os.environ.get('QT_PLUGIN_PATH') or os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH')
                if plugin_path and os.path.exists(plugin_path):
                    platforms_path = os.path.join(plugin_path, 'platforms')
                    # 根据平台检查不同的插件文件
                    if sys.platform == 'win32':
                        platform_plugin = os.path.join(platforms_path, 'qwindows.dll')
                    elif sys.platform == 'darwin':
                        platform_plugin = os.path.join(platforms_path, 'qcocoa.dylib')
                    else:
                        platform_plugin = None
                    
                    if platform_plugin and os.path.exists(platform_plugin):
                        print(f"[_setup_qt_plugin_paths] 使用环境变量中的插件路径: {plugin_path}")
                        return
                
                # 方法1: 优先通过导入PyQt5来查找（最可靠的方法）
                plugin_path = None
                try:
                    import PyQt5
                    from PyQt5 import QtCore
                    
                    # 获取PyQt5安装路径
                    qt_core_path = QtCore.__file__
                    qt_dir = os.path.dirname(qt_core_path)
                    
                    # 查找platforms插件目录（尝试多个可能的路径）
                    paths_to_check = [
                        os.path.join(qt_dir, 'Qt5', 'plugins'),
                        os.path.join(qt_dir, 'plugins'),
                        os.path.join(qt_dir, '..', 'Qt5', 'plugins'),
                        os.path.join(qt_dir, '..', '..', 'PyQt5', 'Qt5', 'plugins'),
                        os.path.join(qt_dir, '..', '..', 'Qt5', 'plugins'),
                    ]
                    # 根据平台检查不同的插件文件
                    if sys.platform == 'win32':
                        plugin_file = 'qwindows.dll'
                    elif sys.platform == 'darwin':
                        plugin_file = 'qcocoa.dylib'
                    else:
                        plugin_file = None
                    
                    if plugin_file:
                        for path in paths_to_check:
                            abs_path = os.path.abspath(path)
                            platforms_path = os.path.join(abs_path, 'platforms')
                            platform_plugin = os.path.join(platforms_path, plugin_file)
                            if os.path.exists(platform_plugin):
                                plugin_path = abs_path
                                break
                except Exception as e:
                    print(f"通过PyQt5查找插件路径时出错: {e}")
                
                # 方法2: 如果方法1失败，尝试从site-packages查找
                if not plugin_path:
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
                        for sp in set(site_packages):
                            if not sp:
                                continue
                            # 尝试多个可能的路径结构
                            paths_to_check = [
                                os.path.join(sp, 'PyQt5', 'Qt5', 'plugins'),
                                os.path.join(sp, 'PyQt5', 'plugins'),
                                os.path.join(sp, 'Qt5', 'plugins'),
                            ]
                            for pyqt5_path in paths_to_check:
                                if os.path.exists(pyqt5_path):
                                    platforms_path = os.path.join(pyqt5_path, 'platforms')
                                    # 根据平台检查不同的插件文件
                                    if sys.platform == 'win32':
                                        platform_plugin = os.path.join(platforms_path, 'qwindows.dll')
                                    elif sys.platform == 'darwin':
                                        platform_plugin = os.path.join(platforms_path, 'qcocoa.dylib')
                                    else:
                                        platform_plugin = None
                                    
                                    if platform_plugin and os.path.exists(platform_plugin):
                                        plugin_path = pyqt5_path
                                        break
                            if plugin_path:
                                break
                    except Exception as e:
                        print(f"查找site-packages时出错: {e}")
                
                if plugin_path:
                    # 设置环境变量（必须在创建QApplication之前）
                    os.environ['QT_PLUGIN_PATH'] = plugin_path
                    # 也设置QT_QPA_PLATFORM_PLUGIN_PATH（某些版本需要）
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path
                    try:
                        print(f"[OK] 已设置Qt插件路径: {plugin_path}")
                    except UnicodeEncodeError:
                        print(f"[OK] 已设置Qt插件路径: {plugin_path.encode('ascii', 'replace').decode('ascii')}")
                    
                    # 尝试使用QCoreApplication.setLibraryPaths()设置插件路径
                    # 这需要在创建QApplication之前调用
                    try:
                        from PyQt5.QtCore import QCoreApplication
                        if not QCoreApplication.instance():
                            QCoreApplication.setLibraryPaths([plugin_path])
                            try:
                                print(f"[OK] 已通过QCoreApplication设置插件路径")
                            except UnicodeEncodeError:
                                print("[OK] 已通过QCoreApplication设置插件路径")
                    except Exception as e:
                        # 如果QCoreApplication不可用，仅使用环境变量也可以
                        print(f"通过QCoreApplication设置插件路径失败（可忽略）: {e}")
                else:
                    print("[WARN] 警告: 未找到Qt插件路径")
                    print("\n解决方案:")
                    print("  1. 确保已安装PyQt5和PyQt5-Qt5:")
                    print("     pip install PyQt5 PyQt5-Qt5")
                    print("  2. 运行诊断脚本:")
                    print("     python check_qt_env.py")
                    print("  3. 运行修复脚本:")
                    print("     fix_qt_plugin.bat")
                    print("\n尝试继续运行，Qt可能会自动找到插件路径...")
                    
            except Exception as e:
                print(f"[ERROR] 设置Qt插件路径时出错: {e}")
                import traceback
                traceback.print_exc()
                print("\n尝试继续运行，Qt可能会自动找到插件路径...")
    
    def _get_binance_service(self):
        """延迟获取BinanceService"""
        if self.binance_service is None:
            from .services.binance_service import BinanceService
            self.binance_service = BinanceService()
        return self.binance_service
        
    def run(self):
        """运行应用"""
        try:
            # 每次启动都清除之前的会话，强制用户重新登录
            self.auth_service.logout()
            
            # 显示登录窗口（强制登录）
            self._show_login_window()
            
            print("[DEBUG] 准备启动Qt事件循环...")
            # 运行Qt事件循环
            exit_code = self.qt_app.exec_()
            print(f"[DEBUG] Qt事件循环退出，退出码: {exit_code}")
            sys.exit(exit_code)
        except Exception as e:
            import traceback
            error_msg = f"运行应用时出错: {str(e)}"
            print(f"[严重错误] {error_msg}")
            traceback.print_exc()
            # 尝试显示错误对话框
            try:
                from PyQt5.QtWidgets import QMessageBox
                if QApplication.instance():
                    QMessageBox.critical(None, "严重错误", f"{error_msg}\n\n详细错误信息请查看控制台输出")
            except:
                pass
            sys.exit(1)
    
    def _show_login_window(self):
        """显示登录窗口"""
        try:
            # 不传递on_close回调，避免关闭登录窗口时退出程序
            self.login_window = LoginWindow(self._handle_login, on_close=None)
            self.login_window.show()
        except Exception as e:
            import traceback
            print(f"显示登录窗口失败: {e}")
            traceback.print_exc()
    
    def _handle_exit(self):
        """处理退出程序"""
        import sys
        # 清理资源
        if self.order_service:
            self.order_service.stop()
        if self.session_timer:
            self.session_timer.cancel()
            self.session_timer = None
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
            self.heartbeat_timer = None
        # 退出程序
        sys.exit(0)
    
    def _handle_login(self, username: str, password: str):
        """处理登录"""
        try:
            result = self.auth_service.login(username, password)
            
            if result.get("code") == 200:
                # 登录成功，同步token到api_client
                if result.get("data", {}).get("token"):
                    self.api_client.set_token(result["data"]["token"])
                
                # 标记登录成功，避免关闭登录窗口时退出程序
                if self.login_window:
                    self.login_window.login_success = True
                
                # 先创建并显示主窗口（确保主窗口存在）
                self._start_main_window(username)
                
                # 主窗口创建后再关闭登录窗口（此时主窗口已存在，且已标记登录成功，不会触发退出）
                if self.login_window:
                    self.login_window.close()
                    self.login_window = None
            else:
                # 显示错误
                error_msg = result.get("message", "登录失败")
                # 检查是否是单点登录导致的旧token失效
                if "Token已失效" in error_msg or "已在其他地方登录" in error_msg:
                    error_msg = "账号已在其他地方登录，请重新登录"
                if self.login_window:
                    self.login_window.show_error(error_msg)
        except Exception as e:
            import traceback
            error_msg = str(e)
            print(f"登录异常: {error_msg}")
            traceback.print_exc()
            
            # 提取更详细的错误信息
            if "401" in error_msg or "Unauthorized" in error_msg:
                if "用户名或密码错误" in error_msg or "账号已过期" in error_msg:
                    # 保持原有错误信息
                    pass
                else:
                    error_msg = "用户名或密码错误，或账号已过期"
            elif "Connection" in error_msg or "timeout" in error_msg or "网络" in error_msg or "无法连接" in error_msg:
                error_msg = f"无法连接到服务器 {settings.server_url}，请检查网络连接"
            elif "404" in error_msg:
                error_msg = f"服务器地址错误: {settings.server_url}"
            elif "Token已失效" in error_msg or "已在其他地方登录" in error_msg:
                error_msg = "账号已在其他地方登录，请重新登录"
            
            if self.login_window:
                self.login_window.show_error(f"登录失败: {error_msg}")
    
    def _start_main_window(self, username: str):
        """启动主窗口"""
        try:
            # 获取用户信息
            user_data = self.auth_service.get_current_user()
            login_time = datetime.now()
            account_expire_at = user_data.get("expire_at") if user_data else None
            
            # 创建主窗口
            try:
                self.main_window = MainWindow(
                    username=username,
                    on_binance_login=self._handle_binance_login,
                    on_set_order_amount=self._handle_set_order_amount,
                    on_start_order=self._handle_start_order,
                    on_stop_order=self._handle_stop_order,
                    on_logout=self._handle_logout,
                    on_close=self._handle_exit,
                    login_time=login_time,
                    account_expire_at=account_expire_at
                )
            except Exception as e:
                import traceback
                error_msg = f"创建主窗口失败: {str(e)}"
                print(f"[错误] {error_msg}")
                traceback.print_exc()
                # 显示错误对话框
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(None, "错误", f"{error_msg}\n\n详细错误信息请查看控制台输出")
                # 如果登录窗口还存在，显示错误
                if self.login_window:
                    self.login_window.show_error(f"启动主窗口失败: {str(e)}")
                return
            
            # 检查币安登录状态（内存中的token，程序重启后需要重新登录）
            try:
                binance_service = self._get_binance_service()
                
                # 设置登录成功回调，在token保存后立即更新GUI状态
                def update_gui_on_login_success():
                    """登录成功后的回调函数"""
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self.main_window.set_binance_logged_in(True) if self.main_window else None)
                    QTimer.singleShot(0, lambda: self.main_window.log("✓ 币安登录成功，GUI状态已更新") if self.main_window else None)
                
                binance_service.set_login_success_callback(update_gui_on_login_success)
                
                # Token只保存在内存中，程序重启后需要重新登录
                if binance_service.is_logged_in():
                    token = binance_service.load_token()
                    self.main_window.set_binance_logged_in(True)
                    self.main_window.log("币安账号已登录（内存中）")
                    if token and token.get('expirationTimestamp') and token.get('expirationTimestamp') > 0:
                        self.main_window.log(f"Token有效期至: {datetime.fromtimestamp(token.get('expirationTimestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    self.main_window.log("请先登录币安账号（Token仅保存在内存中，程序重启后需要重新登录）")
                
                # 创建订单服务
                self.order_service = OrderService(self.api_client, binance_service)
                self.order_service.set_order_callback(self._on_order_callback)
                
                # 设置订单服务的日志回调
                def order_log_callback(msg):
                    if self.main_window:
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(0, lambda: self.main_window.log(msg))
                self.order_service.set_log_callback(order_log_callback)
                
                # 设置订单金额
                try:
                    self.order_service.set_order_amount(settings.default_order_amount)
                    if hasattr(self.main_window, 'amount_input'):
                        self.main_window.amount_input.setText(str(int(settings.default_order_amount)))
                except Exception as e:
                    print(f"[警告] 设置订单金额失败: {e}")
                    if self.main_window:
                        self.main_window.log(f"警告: 设置订单金额失败: {e}")
                
                # 启动心跳定时器（每10秒发送一次心跳）
                self._start_heartbeat()
                
                # 启动24小时会话定时器和账号到期检查
                self._start_session_timer()
                
                # 显示主窗口（确保窗口显示）
                self.main_window.show()
                self.main_window.raise_()  # 将窗口置于最前
                self.main_window.activateWindow()  # 激活窗口
                
                # 如果币安未登录，自动弹出币安登录窗口
                if not binance_service.is_logged_in():
                    # 延迟一下，确保主窗口已经显示
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(500, self._handle_binance_login)
            except Exception as e:
                import traceback
                error_msg = f"初始化主窗口功能失败: {str(e)}"
                print(f"[错误] {error_msg}")
                traceback.print_exc()
                if self.main_window:
                    self.main_window.log(f"错误: {error_msg}")
                    # 显示错误对话框
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.warning(self.main_window, "警告", f"{error_msg}\n\n程序可能无法正常工作，请查看日志了解详情")
        except Exception as e:
            import traceback
            error_msg = f"启动主窗口时发生未预期的错误: {str(e)}"
            print(f"[严重错误] {error_msg}")
            traceback.print_exc()
            # 显示错误对话框
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(None, "严重错误", f"{error_msg}\n\n详细错误信息请查看控制台输出")
            # 如果登录窗口还存在，显示错误
            if self.login_window:
                self.login_window.show_error(f"启动主窗口失败: {str(e)}")
    
    def _handle_binance_login(self):
        """处理币安登录"""
        def qr_callback(qr_data: str):
            """二维码回调"""
            # 在Qt主线程中显示二维码窗口
            from PyQt5.QtCore import QTimer
            def show_qr():
                if self.qr_window:
                    self.qr_window.close_window()
                self.qr_window = QRWindow(qr_data)
                self.qr_window.show()
            QTimer.singleShot(0, show_qr)
        
        def login_thread():
            """登录线程"""
            try:
                # 在Qt主线程中更新日志
                from PyQt5.QtCore import QTimer
                def safe_print(*args, **kwargs):
                    """安全地打印文本，处理编码错误"""
                    try:
                        print(*args, **kwargs)
                    except UnicodeEncodeError:
                        # 如果编码失败，尝试替换Unicode字符
                        try:
                            safe_args = []
                            for arg in args:
                                if isinstance(arg, str):
                                    safe_args.append(arg.encode('ascii', 'replace').decode('ascii'))
                                else:
                                    safe_args.append(arg)
                            print(*safe_args, **kwargs)
                        except:
                            # 如果还是失败，只打印ASCII部分
                            try:
                                safe_args = []
                                for arg in args:
                                    if isinstance(arg, str):
                                        safe_args.append(arg.encode('utf-8', errors='replace').decode('utf-8', errors='replace'))
                                    else:
                                        safe_args.append(arg)
                                print(*safe_args, **kwargs)
                            except:
                                print("[打印错误: 无法编码内容]")
                    except Exception as e:
                        # 其他打印错误也捕获
                        try:
                            print(f"[打印错误] {e}")
                        except:
                            print("[打印错误]")
                
                def log_msg(msg):
                    try:
                        if self.main_window:
                            self.main_window.log(msg)
                        safe_print(f"[币安登录] {msg}")  # 同时输出到控制台
                    except Exception as e:
                        # 即使日志输出失败，也要继续
                        print(f"[日志输出失败] {e}")
                        print(f"[币安登录] {msg}")
                
                log_msg("正在启动浏览器，请稍候...")
                
                # 检查Playwright浏览器是否已安装（快速检查）
                try:
                    from playwright.sync_api import sync_playwright
                    with sync_playwright() as pw:
                        # 尝试获取chromium浏览器路径，检查是否已安装
                        try:
                            browser_path = pw.chromium.executable_path
                            log_msg(f"✓ Playwright浏览器已安装: {browser_path}")
                        except Exception as e:
                            log_msg(f"✗ Playwright浏览器未安装或路径错误: {e}")
                            log_msg("正在安装Playwright浏览器...")
                            import subprocess
                            import sys
                            result = subprocess.run(
                                [sys.executable, "-m", "playwright", "install", "chromium"],
                                capture_output=True,
                                text=True,
                                timeout=300
                            )
                            if result.returncode == 0:
                                log_msg("✓ Playwright浏览器安装成功")
                            else:
                                log_msg(f"✗ Playwright浏览器安装失败: {result.stderr}")
                                QTimer.singleShot(0, lambda: self.main_window.log("请手动运行: python -m playwright install chromium") if self.main_window else None)
                                return
                except ImportError:
                    log_msg("✗ Playwright未安装，请运行: pip install playwright")
                    QTimer.singleShot(0, lambda: self.main_window.log("请先安装Playwright: pip install playwright") if self.main_window else None)
                    return
                except Exception as e:
                    log_msg(f"✗ 检查Playwright时出错: {e}")
                    import traceback
                    log_msg(traceback.format_exc())
                    return
                
                log_msg("正在清理浏览器缓存...")
                
                # 获取当前用户ID，用于多账号支持
                user_data = self.auth_service.get_current_user()
                user_id = user_data.get("user_id") if user_data else None
                
                binance_service = self._get_binance_service()
                
                # 设置日志回调，将所有输出重定向到GUI
                def log_to_gui(msg):
                    """将日志输出到GUI"""
                    QTimer.singleShot(0, lambda: log_msg(msg))
                
                binance_service.set_log_callback(log_to_gui)
                
                # 设置登录成功回调，使用信号机制确保在主线程中更新GUI
                def update_gui_on_login_success():
                    """登录成功后的回调函数（在token保存到内存后调用，在后台线程中执行）"""
                    log_to_gui("✓ 回调函数被调用（后台线程），发送信号到主线程...")
                    # 使用信号机制，确保在主线程中更新GUI
                    self.binance_signals.login_success.emit()
                    log_to_gui("✓ 信号已发送")
                
                binance_service.set_login_success_callback(update_gui_on_login_success)
                log_to_gui("✓ 回调函数已设置")
                
                # reset=True: 每次登录都清理缓存
                log_to_gui("开始调用binance_service.login()...")
                log_to_gui("注意: 浏览器窗口应该会弹出，如果没有弹出，请查看错误日志")
                
                # 调用登录函数（这会启动浏览器）
                try:
                    log_msg("准备调用binance_service.login()...")
                    log_msg(f"参数: reset=True, headless=False, user_id={user_id}")
                    log_msg(f"日志回调已设置: {binance_service.log_callback is not None}")
                    
                    # 确保日志回调正确传递
                    if not binance_service.log_callback:
                        log_msg("警告: 日志回调未设置，重新设置...")
                        binance_service.set_log_callback(log_to_gui)
                    
                    # 测试日志回调是否工作
                    log_msg("测试日志回调...")
                    try:
                        binance_service._log("测试日志回调是否正常工作")
                    except Exception as test_e:
                        log_msg(f"日志回调测试失败: {test_e}")
                    
                    log_msg("开始调用binance_service.login()...")
                    safe_print("[DEBUG] 准备调用binance_service.login()")
                    safe_print(f"[DEBUG] binance_service对象: {binance_service}")
                    safe_print(f"[DEBUG] log_callback: {binance_service.log_callback}")
                    
                    # 直接调用并捕获所有异常
                    try:
                        safe_print("[DEBUG] 开始执行binance_service.login()...")
                        token_info = binance_service.login(reset=True, headless=False, qr_callback=qr_callback, user_id=user_id)
                        safe_print(f"[DEBUG] binance_service.login()返回: {token_info is not None}")
                        if token_info is None:
                            log_msg("登录失败: binance_service.login()返回None")
                            log_to_gui("登录失败，请查看错误日志")
                            return
                        log_msg(f"login()执行完成，返回结果: {token_info is not None}")
                        log_to_gui(f"login()返回结果: {token_info is not None}")
                    except Exception as login_error:
                        safe_print(f"[DEBUG] binance_service.login()抛出异常: {login_error}")
                        import traceback
                        try:
                            trace_str = traceback.format_exc()
                            safe_print(f"[DEBUG] 异常堆栈:\n{trace_str}")
                            log_msg(f"登录过程出错: {login_error}")
                            log_msg("详细错误信息请查看控制台输出")
                        except Exception as trace_error:
                            safe_print(f"[DEBUG] 无法输出异常堆栈: {trace_error}")
                            log_msg(f"登录过程出错: {login_error}")
                        # 不重新抛出异常，避免程序崩溃
                        return
                except KeyboardInterrupt:
                    log_msg("用户中断登录")
                    return
                except SystemExit:
                    log_msg("系统退出，停止登录")
                    return
                except Exception as e:
                    error_msg = f"币安登录过程出错: {str(e)}"
                    log_msg(error_msg)
                    import traceback
                    error_trace = traceback.format_exc()
                    log_msg(f"详细错误信息:\n{error_trace}")
                    # 确保错误信息显示在GUI中
                    try:
                        if self.main_window:
                            QTimer.singleShot(0, lambda: self.main_window.log(error_msg) if self.main_window else None)
                            QTimer.singleShot(0, lambda: self.main_window.log("详细错误信息请查看控制台输出") if self.main_window else None)
                    except:
                        pass
                    # 不要退出程序，只是返回
                    return
                
                # 添加调试日志
                # 注意：token_info 可能已经在回调函数中处理了，这里只是确认状态
                try:
                    if 'token_info' in locals() and token_info:
                        QTimer.singleShot(0, lambda: log_msg(f"登录返回结果: token_info不为空"))
                        QTimer.singleShot(0, lambda: log_msg(f"Token信息: csrftoken={token_info.get('csrftoken', '')[:20] if token_info.get('csrftoken') else 'None'}..., p20t={token_info.get('p20t', '')[:20] if token_info.get('p20t') else 'None'}..."))
                        # 再次确认GUI状态（以防回调函数没有执行）
                        QTimer.singleShot(100, lambda: self._check_and_update_binance_status())
                    else:
                        QTimer.singleShot(0, lambda: log_msg("币安登录失败: token_info为空"))
                except Exception as e:
                    log_msg(f"处理登录结果时出错: {e}")
                    # 即使出错也不退出程序，只是记录错误
            except KeyboardInterrupt:
                safe_print("[币安登录] 用户中断")
                return
            except SystemExit:
                safe_print("[币安登录] 系统退出")
                return
            except Exception as e:
                from PyQt5.QtCore import QTimer
                error_msg = f"币安登录线程错误: {str(e)}"
                safe_print(f"[币安登录错误] {error_msg}")
                import traceback
                try:
                    error_trace = traceback.format_exc()
                    safe_print(f"[币安登录错误详情]\n{error_trace}")
                except:
                    safe_print("[币安登录错误详情] 无法输出错误详情")
                # 确保错误信息显示在GUI中，但不退出程序
                try:
                    if self.main_window:
                        QTimer.singleShot(0, lambda: self.main_window.log(error_msg) if self.main_window else None)
                        QTimer.singleShot(0, lambda: self.main_window.log("详细错误信息请查看控制台输出") if self.main_window else None)
                except:
                    pass
                # 不要退出程序，只是记录错误
        
        # 在新线程中执行登录（避免阻塞UI）
        # 注意：daemon=True意味着主程序退出时线程会被强制终止
        # 但我们需要确保线程中的异常不会导致程序退出
        thread = threading.Thread(target=login_thread, daemon=True, name="BinanceLoginThread")
        thread.start()
        try:
            print(f"[DEBUG] 币安登录线程已启动: {thread.name}, daemon={thread.daemon}")
        except UnicodeEncodeError:
            print(f"[DEBUG] 币安登录线程已启动")
    
    def _on_binance_login_success(self):
        """币安登录成功后的处理函数（在主线程中执行）"""
        from .utils.logger import debug, error, exception, get_log_file
        
        try:
            debug("_on_binance_login_success() - 开始执行")
            if self.main_window:
                debug("_on_binance_login_success() - main_window存在")
                try:
                    self.main_window.log("[OK] 收到登录成功信号，在主线程中更新GUI状态...")
                    self.main_window.log("[OK] Token已保存到内存，正在更新GUI状态...")
                    self.main_window.set_binance_logged_in(True)
                    self.main_window.log("[OK] 币安登录成功，GUI状态已更新")
                    self.main_window.log("[WARN] 注意: Token仅保存在内存中，程序关闭后需要重新登录")
                    self.main_window.log(f"[INFO] 详细日志已保存到: {get_log_file()}")
                except Exception as log_error:
                    error(f"输出日志到GUI时出错: {log_error}")
                    # 即使日志输出失败，也要继续执行
                    try:
                        self.main_window.set_binance_logged_in(True)
                    except:
                        pass
            else:
                error("_on_binance_login_success() - main_window不存在！")
            
            if self.qr_window:
                debug("_on_binance_login_success() - 关闭qr_window")
                try:
                    self.qr_window.close_window()
                    self.qr_window = None
                    debug("_on_binance_login_success() - qr_window已关闭")
                except Exception as qr_error:
                    error(f"_on_binance_login_success() - 关闭qr_window时出错: {qr_error}")
            else:
                debug("_on_binance_login_success() - qr_window不存在")
            
            if self.main_window:
                self.main_window.log("✓ GUI状态更新完成")
                debug("_on_binance_login_success() - 完成")
            else:
                error("_on_binance_login_success() - main_window在关闭qr_window后不存在了！")
        except Exception as e:
            exception(f"_on_binance_login_success() - 出错")
            # 确保错误不会导致程序退出
            if self.main_window:
                try:
                    self.main_window.log(f"登录成功处理出错: {e}")
                    self.main_window.log(f"详细错误请查看日志文件: {get_log_file()}")
                except:
                    pass
    
    def _check_and_update_binance_status(self):
        """检查并更新币安登录状态"""
        if not self.main_window:
            return
        binance_service = self._get_binance_service()
        if binance_service.is_logged_in():
            if not self.main_window.binance_logged_in:
                self.main_window.set_binance_logged_in(True)
                self.main_window.log("✓ 币安登录状态已确认并更新")
        else:
            if self.main_window.binance_logged_in:
                self.main_window.set_binance_logged_in(False)
                self.main_window.log("币安登录状态已失效")
    
    def _handle_set_order_amount(self, amount: float):
        """设置下单金额"""
        if self.order_service:
            self.order_service.set_order_amount(amount)
            if self.main_window:
                self.main_window.log(f"下单金额已设置为: {amount}")
    
    def _handle_start_order(self):
        """开始自动下单"""
        if self.order_service:
            try:
                self.order_service.start()
            except Exception as e:
                if self.main_window:
                    self.main_window.log(f"启动自动下单失败: {str(e)}")
                    # 更新GUI状态
                    self.main_window.order_running = False
                    self.main_window.start_btn.setEnabled(True)
                    self.main_window.stop_btn.setEnabled(False)
    
    def _handle_stop_order(self):
        """停止自动下单"""
        if self.order_service:
            self.order_service.stop()
            if self.main_window:
                self.main_window.log("自动下单已停止")
    
    def _on_order_callback(self, order, result):
        """订单回调"""
        if not self.main_window:
            return
            
        if order:
            if result.get("success") or result.get("code") == 200:
                amount = self.order_service.order_amount if self.order_service else "N/A"
                time_increments = order.get('time_increments', 'N/A')
                self.main_window.log(
                    f"订单执行成功: {order['symbol_name']} {order['direction']} "
                    f"时间周期={time_increments} 金额={amount}"
                )
            else:
                error_msg = result.get("message") or result.get("error", "未知错误")
                self.main_window.log(
                    f"订单执行失败: {order['symbol_name']} {order['direction']} - {error_msg}"
                )
        else:
            if result.get("error"):
                # 检查是否是token失效或账号过期
                error_msg = result.get("error", "")
                if "Token已失效" in error_msg or "账号已过期" in error_msg or "已禁用" in error_msg or "401" in str(result.get("code", "")):
                    if "账号已过期" in error_msg or "已禁用" in error_msg:
                        self.main_window.log("账号已过期或已禁用，正在退出登录...")
                    else:
                        self.main_window.log("登录已失效，请重新登录")
                    self._handle_logout()
                else:
                    self.main_window.log(f"拉取订单错误: {error_msg}")
    
    def _start_heartbeat(self):
        """启动心跳定时器"""
        def send_heartbeat():
            """发送心跳"""
            try:
                self.api_client.send_heartbeat()
            except Exception as e:
                error_msg = str(e)
                if "Token已失效" in error_msg or "已在其他地方登录" in error_msg:
                    if self.main_window:
                        from PyQt5.QtCore import QTimer
                        QTimer.singleShot(0, lambda: self.main_window.log("心跳失败: Token已失效，正在退出...") if self.main_window else None)
                    self._handle_logout()
                    return
                # 其他错误不处理，继续发送心跳
            
            # 10秒后再次发送心跳
            self.heartbeat_timer = threading.Timer(10.0, send_heartbeat)
            self.heartbeat_timer.daemon = True
            self.heartbeat_timer.start()
        
        # 立即发送第一次心跳
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
        self.heartbeat_timer = threading.Timer(10.0, send_heartbeat)
        self.heartbeat_timer.daemon = True
        self.heartbeat_timer.start()
    
    def _handle_logout(self):
        """处理退出登录"""
        # 停止订单服务
        if self.order_service:
            self.order_service.stop()
        
        # 停止心跳定时器
        if self.heartbeat_timer:
            self.heartbeat_timer.cancel()
            self.heartbeat_timer = None
        
        # 停止会话定时器
        if self.session_timer:
            self.session_timer.cancel()
            self.session_timer = None
        
        # 清除币安Token（内存中）
        if self.binance_service:
            self.binance_service.clear_token()
        
        # 清除登录信息
        self.auth_service.logout()
        
        # 关闭主窗口和二维码窗口
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        
        if self.qr_window:
            self.qr_window.close_window()
            self.qr_window = None
        
        # 重新显示登录窗口
        self._show_login_window()
    
    def _start_session_timer(self):
        """启动24小时会话定时器"""
        def check_session():
            """检查会话是否过期"""
            if self.token_manager.is_session_expired():
                if self.main_window:
                    self.main_window.log("会话已过期，需要重新登录")
                self._handle_logout()
            else:
                # 继续检查
                self._start_session_timer()
        
        # 每小时检查一次（24小时有效期）
        self.session_timer = threading.Timer(3600.0, check_session)
        self.session_timer.start()


def main():
    """主函数"""
    from .utils.logger import debug, error, exception, get_log_file
    
    try:
        debug("程序开始启动...")
        print(f"[INFO] 日志文件: {get_log_file()}")
        app = ClientApp()
        debug("ClientApp创建成功，开始运行...")
        app.run()
        debug("app.run()返回，程序正常退出")
    except KeyboardInterrupt:
        debug("用户中断，退出程序")
        print("\n用户中断，退出程序")
        sys.exit(0)
    except SystemExit:
        debug("系统退出")
        print("\n系统退出")
        raise  # 重新抛出SystemExit
    except Exception as e:
        exception("程序启动失败")
        error_msg = f"程序启动失败: {str(e)}"
        print(f"[严重错误] {error_msg}")
        print(f"[INFO] 详细日志请查看: {get_log_file()}")
        # 尝试显示错误对话框
        try:
            from PyQt5.QtWidgets import QApplication, QMessageBox
            if QApplication.instance():
                QMessageBox.critical(None, "严重错误", f"{error_msg}\n\n详细错误信息请查看日志文件:\n{get_log_file()}")
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()

