"""
测试Playwright持久化上下文启动的最小示例
"""
import sys
import os
import tempfile
import shutil

# 设置控制台编码
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

print("=" * 60)
print("Playwright持久化上下文启动测试")
print("=" * 60)

try:
    print("\n[1] 导入playwright模块...")
    from playwright.sync_api import sync_playwright
    print("[OK] playwright模块导入成功")
except ImportError as e:
    print(f"[ERROR] playwright模块导入失败: {e}")
    print("请运行: pip install playwright")
    sys.exit(1)

# 创建临时用户数据目录
user_data_dir = os.path.join(tempfile.gettempdir(), "test_playwright_browser")
if os.path.exists(user_data_dir):
    print(f"\n[清理] 删除旧的用户数据目录: {user_data_dir}")
    shutil.rmtree(user_data_dir, ignore_errors=True)

try:
    print("\n[2] 创建Playwright实例...")
    with sync_playwright() as pw:
        print("[OK] Playwright实例创建成功")
        
        print("\n[3] 检查浏览器是否已安装...")
        try:
            browser_path = pw.chromium.executable_path
            print(f"[OK] 浏览器路径: {browser_path}")
            
            if os.path.exists(browser_path):
                print(f"[OK] 浏览器可执行文件存在")
            else:
                print(f"[ERROR] 浏览器可执行文件不存在: {browser_path}")
                print("请运行: python -m playwright install chromium")
                sys.exit(1)
        except Exception as e:
            print(f"[ERROR] 检查浏览器路径失败: {e}")
            sys.exit(1)
        
        print("\n[4] 启动持久化上下文（非无头模式）...")
        print(f"用户数据目录: {user_data_dir}")
        try:
            context = pw.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            print("[OK] 持久化上下文创建成功")
            
            print("\n[5] 获取或创建页面...")
            if context.pages:
                page = context.pages[0]
                print(f"[OK] 使用现有页面，当前URL: {page.url}")
            else:
                page = context.new_page()
                print("[OK] 创建新页面")
            
            print("\n[6] 导航到测试页面...")
            page.goto("https://www.baidu.com", wait_until="domcontentloaded", timeout=30000)
            print(f"[OK] 页面加载成功，当前URL: {page.url}")
            
            print("\n[7] 尝试将浏览器窗口置于最前...")
            try:
                page.bring_to_front()
                print("[OK] 已尝试将浏览器窗口置于最前")
            except Exception as e:
                print(f"[WARN] 无法将浏览器窗口置于最前: {e}")
            
            print("\n[8] 等待10秒，请检查浏览器窗口是否打开...")
            print("   提示: 如果看不到浏览器窗口，请检查任务栏或使用Alt+Tab切换")
            import time
            time.sleep(10)
            
            print("\n[9] 关闭浏览器上下文...")
            context.close()
            print("[OK] 浏览器上下文已关闭")
            
            print("\n" + "=" * 60)
            print("测试完成！")
            print("=" * 60)
            
        except Exception as e:
            print(f"[ERROR] 启动持久化上下文失败: {e}")
            import traceback
            print("\n详细错误信息:")
            traceback.print_exc()
            
            # 检查是否是浏览器可执行文件不存在
            error_str = str(e)
            if "Executable doesn't exist" in error_str or "playwright install" in error_str.lower():
                print("\n" + "=" * 60)
                print("浏览器可执行文件不存在，正在尝试安装...")
                print("=" * 60)
                try:
                    import subprocess
                    print("正在运行: python -m playwright install chromium")
                    result = subprocess.run(
                        [sys.executable, "-m", "playwright", "install", "chromium"],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode == 0:
                        print("[OK] 浏览器安装成功，请重新运行测试")
                    else:
                        print(f"[ERROR] 浏览器安装失败: {result.stderr}")
                        print("请手动运行: python -m playwright install chromium")
                except Exception as install_error:
                    print(f"[ERROR] 安装浏览器时出错: {install_error}")
            
            sys.exit(1)
            
except Exception as e:
    print(f"[ERROR] 测试过程出错: {e}")
    import traceback
    print("\n详细错误信息:")
    traceback.print_exc()
    sys.exit(1)

