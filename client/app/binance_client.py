"""
币安客户端（复用原项目代码）
"""
import os
import re
import json
import sys
import qrcode
import shutil
from http.cookies import SimpleCookie
from email.utils import parsedate_to_datetime
# 延迟导入playwright，只在get_token函数中导入
# from playwright.sync_api import sync_playwright

# 安全的print函数，避免Unicode编码错误
def safe_print(*args, **kwargs):
    """安全地打印，避免Unicode编码错误"""
    try:
        # 尝试直接打印
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 如果失败，尝试替换Unicode字符
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

# 根据平台设置User-Agent
if sys.platform == 'darwin':  # macOS
    DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    DEFAULT_PLATFORM = "MacIntel"
    DEFAULT_SEC_CH_UA_PLATFORM = '"macOS"'
else:  # Windows和其他平台
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
    DEFAULT_PLATFORM = "Win32"
    DEFAULT_SEC_CH_UA_PLATFORM = '"Windows"'


def find_browser_executable():
    """查找浏览器可执行文件"""
    import os
    possible_paths = []
    
    # 0. 优先检查 google_web 目录（用户指定的目录）
    current_file = os.path.abspath(__file__)
    app_dir = os.path.dirname(current_file)
    client_dir = os.path.dirname(app_dir)
    google_web_paths = []
    if sys.platform == 'win32':
        # chrome.exe 直接在 google_web 目录下
        google_web_paths = [
            os.path.join(client_dir, 'google_web', 'chrome.exe'),
            os.path.join(client_dir, 'google_web', 'chrome-win64', 'chrome.exe'),
            os.path.join(client_dir, 'google_web', 'chrome-win32', 'chrome.exe'),
        ]
    elif sys.platform == 'darwin':
        google_web_paths = [
            os.path.join(client_dir, 'google_web', 'chrome'),
            os.path.join(client_dir, 'google_web', 'chrome-mac', 'chrome'),
        ]
    else:
        google_web_paths = [
            os.path.join(client_dir, 'google_web', 'chrome'),
            os.path.join(client_dir, 'google_web', 'chrome-linux', 'chrome'),
        ]
    for path in google_web_paths:
        if os.path.exists(path):
            possible_paths.append(path)
    
    # 1. 检查常见的Playwright安装位置
    local_appdata = os.environ.get('LOCALAPPDATA', '')
    if local_appdata:
        # 尝试不同的revision版本
        for revision in ['1200', '1199', '1201', '1198', '1202']:
            for platform_suffix in ['chrome-win64', 'chrome-win32', 'chrome-win']:
                possible_path = os.path.join(local_appdata, 'ms-playwright', f'chromium-{revision}', platform_suffix, 'chrome.exe')
                if os.path.exists(possible_path):
                    possible_paths.append(possible_path)
    
    # 2. 检查用户目录下的Playwright目录
    user_home = os.path.expanduser('~')
    if user_home:
        for revision in ['1200', '1199', '1201', '1198', '1202']:
            for platform_suffix in ['chrome-win64', 'chrome-win32', 'chrome-win']:
                possible_path = os.path.join(user_home, 'AppData', 'Local', 'ms-playwright', f'chromium-{revision}', platform_suffix, 'chrome.exe')
                if os.path.exists(possible_path):
                    possible_paths.append(possible_path)
    
    # 3. 检查项目目录下是否有浏览器
    project_browser_paths = [
        os.path.join(client_dir, 'chromium', 'chrome.exe'),
        os.path.join(client_dir, 'browser', 'chrome.exe'),
        os.path.join(client_dir, 'playwright-browser', 'chrome.exe'),
    ]
    for path in project_browser_paths:
        if os.path.exists(path):
            possible_paths.append(path)
    
    return possible_paths[0] if possible_paths else None


def launch_persistent_ctx(pw, reset=False, headless=True, user_id=None, log_callback=None):
    """启动持久化浏览器上下文
    
    Args:
        pw: Playwright实例
        reset: 是否重置浏览器缓存（每次登录都清理）
        headless: 是否无头模式
        user_id: 用户ID，用于多账号支持（不同账号使用不同目录）
    """
    # 获取程序运行目录（client目录）
    current_file = os.path.abspath(__file__)
    # app/binance_client.py -> app -> client
    app_dir = os.path.dirname(current_file)
    client_dir = os.path.dirname(app_dir)
    
    # 根据user_id创建不同的目录，支持多开
    if user_id:
        user_data_dir = os.path.join(client_dir, f"playwright-binance-{user_id}")
    else:
        user_data_dir = os.path.join(client_dir, "playwright-binance")
    
    # 每次登录都清理缓存（reset=True）
    if reset:
        if os.path.exists(user_data_dir):
            shutil.rmtree(user_data_dir)
            log_msg = log_callback if log_callback else print
            log_msg(f"已清理浏览器缓存: {user_data_dir}")

    args = [
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1280,960",
    ]

    if headless:
        args += ["--headless=new", "--disable-gpu"]

    # 优先查找 google_web 目录中的浏览器（用户指定的目录）
    browser_executable = None
    found_path = find_browser_executable()
    if found_path and os.path.exists(found_path):
        browser_executable = found_path
        if log_callback:
            log_callback(f"[DEBUG] 优先使用google_web目录中的浏览器: {browser_executable}")
        safe_print(f"[DEBUG] 优先使用google_web目录中的浏览器: {browser_executable}")
    else:
        # 如果google_web目录中没有浏览器，尝试使用Playwright报告的路径
        try:
            browser_executable = pw.chromium.executable_path
            if os.path.exists(browser_executable):
                if log_callback:
                    log_callback(f"[DEBUG] 使用Playwright报告的浏览器路径: {browser_executable}")
                safe_print(f"[DEBUG] 使用Playwright报告的浏览器路径: {browser_executable}")
            else:
                # Playwright报告的路径不存在，尝试查找其他位置
                found_path = find_browser_executable()
                if found_path and os.path.exists(found_path):
                    browser_executable = found_path
                    if log_callback:
                        log_callback(f"[DEBUG] 使用找到的浏览器路径: {browser_executable}")
                    safe_print(f"[DEBUG] 使用找到的浏览器路径: {browser_executable}")
        except:
            # 如果获取executable_path失败，尝试查找
            found_path = find_browser_executable()
            if found_path and os.path.exists(found_path):
                browser_executable = found_path
                if log_callback:
                    log_callback(f"[DEBUG] 使用找到的浏览器路径: {browser_executable}")
                safe_print(f"[DEBUG] 使用找到的浏览器路径: {browser_executable}")

    common_kwargs = dict(
        user_data_dir=user_data_dir,
        headless=headless,
        args=args,
        viewport={"width": 1280, "height": 960},
        locale="zh-CN",
        user_agent=DEFAULT_UA,
        extra_http_headers={
            "sec-ch-ua-platform": DEFAULT_SEC_CH_UA_PLATFORM,
            "sec-ch-ua-mobile": "?0",
            "accept-language": "zh-CN,zh;q=0.9"
        },
    )
    
    # 如果找到了浏览器可执行文件，则使用executable_path参数
    if browser_executable and os.path.exists(browser_executable):
        try:
            pw_executable = pw.chromium.executable_path
            # 如果找到的路径与Playwright报告的路径不同，或者Playwright报告的路径不存在，使用找到的路径
            if browser_executable != pw_executable or not os.path.exists(pw_executable):
                common_kwargs['executable_path'] = browser_executable
                if log_callback:
                    log_callback(f"[DEBUG] 使用自定义浏览器路径: {browser_executable}")
                safe_print(f"[DEBUG] 使用自定义浏览器路径: {browser_executable}")
        except:
            # 如果无法获取Playwright的executable_path，直接使用找到的路径
            common_kwargs['executable_path'] = browser_executable
            if log_callback:
                log_callback(f"[DEBUG] 使用自定义浏览器路径: {browser_executable}")
            safe_print(f"[DEBUG] 使用自定义浏览器路径: {browser_executable}")
    elif browser_executable:
        # 如果浏览器路径存在但文件不存在，记录警告
        if log_callback:
            log_callback(f"[WARN] 浏览器路径不存在: {browser_executable}")
        safe_print(f"[WARN] 浏览器路径不存在: {browser_executable}")

    if log_callback:
        log_callback(f"[DEBUG] launch_persistent_ctx - 准备启动浏览器, user_data_dir={user_data_dir}, headless={headless}")
    safe_print(f"[DEBUG] launch_persistent_ctx - 准备调用pw.chromium.launch_persistent_context()")
    try:
        ctx = pw.chromium.launch_persistent_context(**common_kwargs)
        safe_print(f"[DEBUG] launch_persistent_ctx - 浏览器启动成功")
        if log_callback:
            log_callback(f"[DEBUG] launch_persistent_ctx - 浏览器启动成功")
        return ctx
    except Exception as e:
        safe_print(f"[DEBUG] launch_persistent_ctx - 浏览器启动失败: {e}")
        import traceback
        try:
            trace_str = traceback.format_exc()
            safe_print(f"[DEBUG] launch_persistent_ctx - 异常堆栈:\n{trace_str}")
        except:
            safe_print("[DEBUG] launch_persistent_ctx - 无法输出异常堆栈")
        if log_callback:
            log_callback(f"[DEBUG] launch_persistent_ctx - 浏览器启动失败: {e}")
        raise


def apply_platform_ua(ctx, page):
    """应用平台特定的User-Agent（Windows或macOS）"""
    # 转义User-Agent字符串中的单引号，避免JavaScript语法错误
    escaped_ua = DEFAULT_UA.replace("'", "\\'")
    escaped_platform = DEFAULT_PLATFORM.replace("'", "\\'")
    page.add_init_script(f"""
        Object.defineProperty(navigator, 'userAgent', {{get: () => '{escaped_ua}' }});
        Object.defineProperty(navigator, 'platform', {{get: () => '{escaped_platform}' }});
        Object.defineProperty(navigator, 'vendor', {{get: () => 'Google Inc.' }});
        Object.defineProperty(navigator, 'maxTouchPoints', {{get: () => 0 }});
    """)

    try:
        s = ctx.new_cdp_session(page)
        platform_name = "macOS" if sys.platform == 'darwin' else "Windows"
        s.send("Emulation.setUserAgentOverride", {
            "userAgent": DEFAULT_UA,
            "platform": platform_name,
            "acceptLanguage": "zh-CN,zh;q=0.9"
        })
    except:
        pass

    ctx.set_extra_http_headers({
        "sec-ch-ua-platform": DEFAULT_SEC_CH_UA_PLATFORM,
        "sec-ch-ua-mobile": "?0",
        "accept-language": "zh-CN,zh;q=0.9"
    })


def print_qr(data, log_callback=None):
    """打印二维码到终端"""
    qr = qrcode.QRCode(border=0)
    qr.add_data(data)
    qr.make(fit=True)
    m = qr.get_matrix()

    black = "  "
    white = "██"
    scale = 1
    margin = 1
    w = len(m[0])
    
    log_msg = log_callback if log_callback else print

    for _ in range(margin * scale):
        log_msg(white * (w + margin * 2))

    for row in m:
        line = white * margin
        for v in row:
            line += (black if v else white) * scale
        line += white * margin
        for _ in range(scale):
            log_msg(line)

    for _ in range(margin * scale):
        log_msg(white * (w + margin * 2))


def get_token(reset=False, headless=True, qr_callback=None, user_id=None, log_callback=None):
    """
    获取币安Token
    
    Args:
        reset: 是否重置浏览器缓存（每次登录都清理，默认True）
        headless: 是否无头模式
        qr_callback: 二维码回调函数，接收二维码数据作为参数
        user_id: 用户ID，用于多账号支持（不同账号使用不同目录）
    
    Returns:
        dict: 包含csrftoken, p20t, expirationTimestamp的字典
    """
    # 每次登录都清理缓存
    if reset is None:
        reset = True
    
    # 确保日志回调可用
    def safe_log(msg):
        """安全地输出日志"""
        try:
            if log_callback:
                log_callback(msg)
        except Exception as e:
            # 日志回调失败，尝试安全打印
            try:
                safe_msg = msg.encode('ascii', 'replace').decode('ascii')
                print(f"[LOG ERROR] {safe_msg}")
                print(f"[LOG ERROR] 日志回调失败: {e}")
            except:
                print("[LOG ERROR] 日志输出失败")
        
        # 安全地输出到控制台（避免Unicode编码错误）
        safe_print(f"[LOG] {msg}")
    
    log_msg = safe_log
    safe_print(f"[DEBUG] get_token() - 开始执行, log_callback={log_callback is not None}")
    safe_print(f"[DEBUG] get_token() - 参数: reset={reset}, headless={headless}, user_id={user_id}")
    try:
        log_msg(f"准备启动浏览器: headless={headless}, reset={reset}, user_id={user_id}")
        safe_print(f"[DEBUG] get_token() - 已输出第一条日志")
    except Exception as e:
        safe_print(f"[DEBUG] get_token() - 输出日志失败: {e}")
        import traceback
        try:
            trace_str = traceback.format_exc()
            safe_print(f"[DEBUG] get_token() - 异常堆栈:\n{trace_str}")
        except:
            safe_print("[DEBUG] get_token() - 无法输出异常堆栈")
    
    # 只在需要时才导入playwright
    try:
        safe_print("[DEBUG] get_token() - 准备导入playwright")
        from playwright.sync_api import sync_playwright
        safe_print("[DEBUG] get_token() - playwright导入成功")
        log_msg("✓ Playwright模块导入成功")
    except ImportError as e:
        error_msg = f"✗ Playwright模块导入失败: {e}"
        log_msg(error_msg)
        log_msg("请运行: pip install playwright")
        log_msg("然后运行: python -m playwright install chromium")
        # 不抛出异常，返回None表示失败
        return None
    
    csrftoken = ""
    p20t = ""
    expirationTimestamp = -1
    
    try:
        safe_print("[DEBUG] get_token() - 准备创建Playwright实例")
        log_msg("正在创建Playwright实例...")
        safe_print("[DEBUG] get_token() - 调用sync_playwright()")
        with sync_playwright() as pw:
            safe_print("[DEBUG] get_token() - Playwright实例创建成功")
            log_msg("✓ Playwright实例创建成功")
            
            # 验证浏览器文件是否存在，如果不存在则尝试查找其他位置
            try:
                browser_path = pw.chromium.executable_path
                safe_print(f"[DEBUG] get_token() - Playwright报告的浏览器路径: {browser_path}")
                import os
                
                # 检查浏览器文件是否存在
                if not os.path.exists(browser_path):
                    log_msg(f"✗ 浏览器文件不存在于: {browser_path}")
                    
                    # 尝试查找其他可能的浏览器位置
                    possible_paths = []
                    
                    # 1. 检查常见的Playwright安装位置
                    local_appdata = os.environ.get('LOCALAPPDATA', '')
                    if local_appdata:
                        # 尝试不同的revision版本
                        for revision in ['1200', '1199', '1201', '1198']:
                            for platform_suffix in ['chrome-win64', 'chrome-win32', 'chrome-win']:
                                possible_path = os.path.join(local_appdata, 'ms-playwright', f'chromium-{revision}', platform_suffix, 'chrome.exe')
                                if os.path.exists(possible_path):
                                    possible_paths.append(possible_path)
                    
                    # 2. 检查用户目录下的Playwright目录
                    user_home = os.path.expanduser('~')
                    if user_home:
                        for revision in ['1200', '1199', '1201', '1198']:
                            for platform_suffix in ['chrome-win64', 'chrome-win32', 'chrome-win']:
                                possible_path = os.path.join(user_home, 'AppData', 'Local', 'ms-playwright', f'chromium-{revision}', platform_suffix, 'chrome.exe')
                                if os.path.exists(possible_path):
                                    possible_paths.append(possible_path)
                    
                    # 3. 检查项目目录下是否有浏览器（优先检查google_web目录）
                    current_file = os.path.abspath(__file__)
                    app_dir = os.path.dirname(current_file)
                    client_dir = os.path.dirname(app_dir)
                    project_browser_paths = [
                        os.path.join(client_dir, 'google_web', 'chrome.exe'),  # 优先检查google_web目录
                        os.path.join(client_dir, 'chromium', 'chrome.exe'),
                        os.path.join(client_dir, 'browser', 'chrome.exe'),
                        os.path.join(client_dir, 'playwright-browser', 'chrome.exe'),
                    ]
                    for path in project_browser_paths:
                        if os.path.exists(path):
                            possible_paths.append(path)
                    
                    if possible_paths:
                        # 找到其他位置的浏览器，尝试设置环境变量
                        found_path = possible_paths[0]
                        log_msg(f"✓ 找到浏览器文件: {found_path}")
                        # 注意：Playwright可能不支持直接设置executable_path，但我们可以尝试通过环境变量
                        # 或者直接使用launch_persistent_context的executable_path参数
                        safe_print(f"[DEBUG] 找到的浏览器路径: {found_path}")
                        # 由于Playwright的executable_path是只读的，我们需要在launch_persistent_ctx中处理
                    else:
                        log_msg("✗ 未找到浏览器文件，正在自动安装Playwright浏览器...")
                        log_msg("提示: 安装可能需要几分钟，请耐心等待...")
                        import subprocess
                        import sys
                        safe_print("[DEBUG] get_token() - 开始安装浏览器")
                        
                        # 设置环境变量以使用国内镜像
                        env = os.environ.copy()
                        env['PLAYWRIGHT_DOWNLOAD_HOST'] = 'https://npmmirror.com/mirrors/playwright'
                        env['npm_config_registry'] = 'https://registry.npmmirror.com'
                        env['PYTHONIOENCODING'] = 'utf-8'
                        
                        result = subprocess.run(
                            [sys.executable, "-m", "playwright", "install", "chromium"],
                            capture_output=True,
                            text=True,
                            timeout=600,  # 增加超时时间到10分钟
                            env=env
                        )
                        if result.returncode == 0:
                            log_msg("✓ Playwright浏览器安装成功")
                            safe_print("[DEBUG] get_token() - 浏览器安装成功")
                            # 重新获取路径
                            browser_path = pw.chromium.executable_path
                            if not os.path.exists(browser_path):
                                log_msg(f"✗ 浏览器安装后文件仍不存在: {browser_path}")
                                log_msg("请检查浏览器安装日志或手动安装")
                                return None
                        else:
                            error_msg = f"✗ Playwright浏览器安装失败"
                            log_msg(error_msg)
                            if result.stderr:
                                safe_print(f"[DEBUG] 安装错误: {result.stderr}")
                            if result.stdout:
                                safe_print(f"[DEBUG] 安装输出: {result.stdout}")
                            log_msg("请手动运行: python -m playwright install chromium")
                            return None
                else:
                    safe_print(f"[DEBUG] get_token() - 浏览器文件存在: {browser_path}")
            except Exception as check_error:
                log_msg(f"✗ 检查浏览器时出错: {check_error}")
                import traceback
                try:
                    log_msg(traceback.format_exc())
                except:
                    log_msg("无法输出详细错误信息")
                return None
            
            safe_print(f"[DEBUG] get_token() - 准备启动浏览器, headless={headless}")
            log_msg(f"正在启动浏览器（headless={headless}）...")
            ctx = None
            try:
                safe_print("[DEBUG] get_token() - 调用launch_persistent_ctx()")
                ctx = launch_persistent_ctx(pw, reset=reset, headless=headless, user_id=user_id, log_callback=log_callback)
                safe_print("[DEBUG] get_token() - launch_persistent_ctx()返回成功")
                log_msg("✓ 浏览器上下文创建成功")
                if not headless:
                    log_msg("✓ 浏览器窗口应该已打开")
                    # 尝试激活浏览器窗口
                    try:
                        # 获取第一个页面并尝试聚焦
                        if ctx.pages:
                            first_page = ctx.pages[0]
                            first_page.bring_to_front()
                            log_msg("✓ 已尝试将浏览器窗口置于最前")
                        # 等待一下让窗口有时间显示
                        import time
                        time.sleep(0.5)
                        log_msg("  提示: 如果看不到浏览器窗口，请检查任务栏或使用Alt+Tab切换")
                    except Exception as e:
                        log_msg(f"  警告: 无法激活浏览器窗口: {e}")
            except Exception as e:
                error_str = str(e)
                # 检查是否是浏览器可执行文件不存在
                if "Executable doesn't exist" in error_str or "playwright install" in error_str.lower():
                    log_msg("✗ Playwright浏览器可执行文件不存在")
                    log_msg("正在自动安装Playwright浏览器...")
                    try:
                        import subprocess
                        import sys
                        log_msg("正在运行: python -m playwright install chromium")
                        result = subprocess.run(
                            [sys.executable, "-m", "playwright", "install", "chromium"],
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if result.returncode == 0:
                            log_msg("✓ Playwright浏览器安装成功，正在重试启动...")
                            # 重试启动浏览器
                            try:
                                ctx = launch_persistent_ctx(pw, reset=reset, headless=headless, user_id=user_id, log_callback=log_callback)
                                log_msg("✓ 浏览器上下文创建成功（重试后）")
                                if not headless:
                                    log_msg("✓ 浏览器窗口应该已打开")
                            except Exception as retry_error:
                                error_msg = f"✗ 重试启动浏览器失败: {retry_error}"
                                log_msg(error_msg)
                                import traceback
                                try:
                                    log_msg(traceback.format_exc())
                                except:
                                    log_msg("无法输出详细错误信息")
                                return None
                        else:
                            error_msg = f"✗ Playwright浏览器安装失败: {result.stderr}"
                            log_msg(error_msg)
                            log_msg("请手动运行: python -m playwright install chromium")
                            return None
                    except subprocess.TimeoutExpired:
                        log_msg("✗ 浏览器安装超时")
                        log_msg("请手动运行: python -m playwright install chromium")
                        return None
                    except Exception as install_error:
                        if "浏览器安装失败" not in str(install_error):
                            log_msg(f"✗ 安装浏览器时出错: {install_error}")
                        return None
                else:
                    error_msg = f"✗ 浏览器启动失败: {e}"
                    log_msg(error_msg)
                    import traceback
                    try:
                        log_msg(traceback.format_exc())
                    except:
                        log_msg("无法输出详细错误信息")
                    return None
            
            # 确保ctx已成功创建
            if ctx is None:
                log_msg("✗ 浏览器上下文创建失败")
                return None
            
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            log_msg(f"✓ 页面创建成功，当前URL: {page.url}")
            apply_platform_ua(ctx, page)
            log_msg("✓ User-Agent设置完成")

            qr_results = []

            def update_p20t_from_context():
                try:
                    cookies = ctx.cookies("https://www.binance.com")
                    c = next((c for c in cookies if c.get("name") == "p20t"), None)
                    token = c.get("value", "")
                    if not token:
                        return
                    nonlocal p20t
                    p20t = token
                except:
                    pass

            def on_request(req):
                try:
                    url = req.url
                    if "https://www.binance.com/fapi/v1/ticker/24hr" in url:
                        token = req.headers.get("csrftoken", "")
                        if not token:
                            return
                        nonlocal csrftoken
                        csrftoken = token
                except:
                    pass

            def on_request_finished(req):
                try:
                    url = req.url
                    if "https://accounts.binance.com/bapi/accounts/v2/public/qrcode/login/get" in url:
                        resp = req.response()
                        if not resp:
                            return
                        data = resp.json()
                        if not data.get("success"):
                            return
                        code = data["data"]["qrCode"]
                        if code not in qr_results:
                            qr_results.append(code)
                            log_msg = log_callback if log_callback else print
                            log_msg("请使用 Binance App 扫描以下二维码登录")
                            print_qr(code, log_callback=log_callback)
                            img = qrcode.make(code).convert("RGB")
                            img.save("qrcode.jpg", format="JPEG", quality=100)
                            # 调用回调函数
                            if qr_callback:
                                qr_callback(code)
                    elif "https://accounts.binance.com/bapi/accounts/v2/private/authcenter/setTrustDevice" in url:
                        resp = req.response()
                        if not resp:
                            return
                        hdrs_arr = resp.headers_array()
                        date_hdr = resp.headers.get("date") or resp.header_value("date")
                        if not hdrs_arr or not date_hdr:
                            return
                        sc_values = [h.get("value", "") for h in hdrs_arr if h.get("name", "").lower() == "set-cookie"]
                        m = next((m for sc in sc_values for m in SimpleCookie(sc).values() if m.key == "p20t"), None)
                        if not m:
                            return
                        nonlocal p20t, expirationTimestamp
                        p20t = m.value
                        expirationTimestamp = int(m["max-age"]) + int(parsedate_to_datetime(date_hdr).timestamp())
                except:
                    pass

            page.on("request", on_request)
            page.on("requestfinished", on_request_finished)
            ctx.on("request", on_request)
            ctx.on("requestfinished", on_request_finished)

            log_msg("正在导航到币安登录页面...")
            try:
                page.goto("https://accounts.binance.com/zh-CN/login?loginChannel=&return_to=", wait_until="domcontentloaded", timeout=30000)
                log_msg(f"✓ 页面加载完成，当前URL: {page.url}")
                if not headless:
                    log_msg("✓ 浏览器窗口应该已显示，请查看是否弹出")
                    log_msg("  如果看不到窗口，请检查任务栏或Alt+Tab切换窗口")
                    # 尝试将浏览器窗口置于最前
                    try:
                        # 获取浏览器进程并尝试激活窗口
                        import time
                        time.sleep(1)  # 等待窗口完全加载
                        log_msg("  提示: 如果浏览器窗口没有自动显示，请手动切换到浏览器窗口")
                    except:
                        pass
            except Exception as e:
                error_msg = f"✗ 页面导航失败: {e}"
                log_msg(error_msg)
                import traceback
                try:
                    log_msg(traceback.format_exc())
                except:
                    log_msg("无法输出详细错误信息")
                return None

            try:
                while True:
                    try:
                        page.wait_for_timeout(1500)
                    except Exception as e:
                        # 如果页面已经关闭，退出循环
                        if "Target closed" in str(e) or "Target page, context or browser has been closed" in str(e):
                            log_msg("浏览器已关闭，退出登录循环")
                            break
                        # 其他错误继续
                        safe_print(f"[DEBUG] wait_for_timeout错误（可忽略）: {e}")

                    if csrftoken and p20t:
                        token_dict = {"csrftoken": csrftoken, "p20t": p20t, "expirationTimestamp": expirationTimestamp}
                        log_msg = log_callback if log_callback else print
                        log_msg("✓ 币安登录成功，获取到Token:")
                        log_msg(f"  csrftoken: {csrftoken[:20]}...")
                        log_msg(f"  p20t: {p20t[:20]}...")
                        log_msg(f"  expirationTimestamp: {expirationTimestamp}")
                        
                        # 安全地关闭浏览器上下文
                        try:
                            # 先移除事件监听器，避免关闭时触发事件处理
                            try:
                                page.remove_listener("request", on_request)
                                page.remove_listener("requestfinished", on_request_finished)
                            except:
                                pass
                            try:
                                ctx.remove_listener("request", on_request)
                                ctx.remove_listener("requestfinished", on_request_finished)
                            except:
                                pass
                            
                            # 关闭浏览器上下文
                            ctx.close()
                            log_msg("✓ 浏览器已关闭")
                        except Exception as close_error:
                            safe_print(f"[DEBUG] 关闭浏览器时出错（可忽略）: {close_error}")
                            log_msg("✓ 浏览器关闭完成")
                        
                        return token_dict

                    try:
                        # 检查页面是否仍然有效
                        try:
                            current_url = page.url
                        except Exception as url_error:
                            if "Target closed" in str(url_error) or "Target page, context or browser has been closed" in str(url_error):
                                log_msg("浏览器已关闭，退出登录循环")
                                break
                            raise
                        
                        if "accounts.binance.com" in current_url:
                            try:
                                if page.get_by_text(re.compile("Understand")).count() > 0:
                                    page.get_by_role("button", name=re.compile("Understand")).first.click(timeout=1200, force=True)
                            except:
                                pass

                            try:
                                if page.get_by_text(re.compile("知道了")).count() > 0:
                                    page.get_by_role("button", name=re.compile("知道了")).first.click(timeout=1200, force=True)
                            except:
                                pass

                            try:
                                if page.get_by_text(re.compile("好的")).count() > 0:
                                    page.get_by_role("button", name=re.compile("好的")).first.click(timeout=1200, force=True)
                            except:
                                pass

                            try:
                                if page.get_by_text(re.compile("登录")).count() > 0 and page.get_by_text(re.compile("邮箱/手机号码")).count() > 0 and page.get_by_text(re.compile("用手机相机扫描")).count() == 0:
                                    page.get_by_role("button", name=re.compile("登录")).first.click(timeout=1200, force=True)
                            except:
                                pass

                            try:
                                if page.get_by_text(re.compile("刷新二维码")).count() > 0:
                                    page.get_by_role("button", name=re.compile("刷新二维码")).first.click(timeout=1200, force=True)
                            except:
                                pass

                            try:
                                if page.get_by_text(re.compile("保持登录状态")).count() > 0:
                                    page.get_by_role("button", name=re.compile("是")).first.click(timeout=1200, force=True)
                            except:
                                pass
                        else:
                            try:
                                update_p20t_from_context()
                            except:
                                pass
                    except Exception as loop_error:
                        # 如果页面已关闭，退出循环
                        if "Target closed" in str(loop_error) or "Target page, context or browser has been closed" in str(loop_error):
                            log_msg("浏览器已关闭，退出登录循环")
                            break
                        # 其他错误继续循环
                        safe_print(f"[DEBUG] 登录循环错误（可忽略）: {loop_error}")
            finally:
                # 确保浏览器上下文被关闭
                try:
                    if ctx and not ctx._connection._closed:
                        try:
                            # 移除事件监听器
                            try:
                                page.remove_listener("request", on_request)
                                page.remove_listener("requestfinished", on_request_finished)
                            except:
                                pass
                            try:
                                ctx.remove_listener("request", on_request)
                                ctx.remove_listener("requestfinished", on_request_finished)
                            except:
                                pass
                        except:
                            pass
                        ctx.close()
                except Exception as final_close_error:
                    safe_print(f"[DEBUG] 最终关闭浏览器时出错（可忽略）: {final_close_error}")
    except KeyboardInterrupt:
        log_msg("用户中断登录")
        return None
    except SystemExit:
        log_msg("系统退出，停止登录")
        return None
    except Exception as e:
        error_msg = f"浏览器启动或登录过程出错: {e}"
        try:
            log_msg(error_msg)
            import traceback
            try:
                error_trace = traceback.format_exc()
                log_msg(error_trace)
            except:
                log_msg("无法输出详细错误信息")
        except:
            safe_print(f"[ERROR] 浏览器启动或登录过程出错: {e}")
        # 不重新抛出异常，返回None表示失败
        return None


def place_order_web(csrftoken, p20t, orderAmount, timeIncrements, symbolName, payoutRatio, direction):
    """
    下单函数（复用原项目代码）
    """
    import requests
    url = "https://www.binance.com/bapi/futures/v1/private/future/event-contract/place-order"
    headers = {
        "content-type": "application/json",
        "clienttype": "web",
        "csrftoken": csrftoken,
        "cookie": f"p20t={p20t}"
    }
    data = {
        "orderAmount": orderAmount,
        "timeIncrements": timeIncrements,
        "symbolName": symbolName,
        "payoutRatio": payoutRatio,
        "direction": direction
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

