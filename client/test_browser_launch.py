"""
测试Playwright浏览器启动的最小示例
"""
import sys
import os

# 设置控制台编码
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

print("=" * 60)
print("Playwright浏览器启动测试")
print("=" * 60)

try:
    print("\n[1] 导入playwright模块...")
    from playwright.sync_api import sync_playwright
    print("[OK] playwright模块导入成功")
except ImportError as e:
    print(f"[ERROR] playwright模块导入失败: {e}")
    print("请运行: pip install playwright")
    sys.exit(1)

try:
    print("\n[2] 创建Playwright实例...")
    with sync_playwright() as pw:
        print("[OK] Playwright实例创建成功")
        
        print("\n[3] 检查浏览器是否已安装...")
        try:
            browser_path = pw.chromium.executable_path
            print(f"[OK] 浏览器路径: {browser_path}")
            
            # 检查文件是否存在
            if os.path.exists(browser_path):
                print(f"[OK] 浏览器可执行文件存在")
            else:
                print(f"[ERROR] 浏览器可执行文件不存在: {browser_path}")
                print("请运行: python -m playwright install chromium")
                sys.exit(1)
        except Exception as e:
            print(f"[ERROR] 检查浏览器路径失败: {e}")
            print("请运行: python -m playwright install chromium")
            sys.exit(1)
        
        print("\n[4] 启动浏览器（非无头模式）...")
        try:
            # 使用最简单的启动方式
            browser = pw.chromium.launch(headless=False)
            print("[OK] 浏览器启动成功")
            
            print("\n[5] 创建浏览器上下文...")
            context = browser.new_context()
            print("[OK] 浏览器上下文创建成功")
            
            print("\n[6] 创建新页面...")
            page = context.new_page()
            print("[OK] 页面创建成功")
            
            print("\n[7] 导航到测试页面...")
            page.goto("https://www.baidu.com", wait_until="domcontentloaded", timeout=30000)
            print(f"[OK] 页面加载成功，当前URL: {page.url}")
            
            print("\n[8] 等待5秒，请检查浏览器窗口是否打开...")
            import time
            time.sleep(5)
            
            print("\n[9] 关闭浏览器...")
            browser.close()
            print("[OK] 浏览器已关闭")
            
            print("\n" + "=" * 60)
            print("测试完成！如果浏览器窗口没有打开，请检查：")
            print("1. 浏览器是否被最小化或隐藏在后台")
            print("2. 检查任务栏是否有浏览器窗口")
            print("3. 使用Alt+Tab切换窗口查看")
            print("=" * 60)
            
        except Exception as e:
            print(f"[ERROR] 启动浏览器失败: {e}")
            import traceback
            print("\n详细错误信息:")
            traceback.print_exc()
            sys.exit(1)
            
except Exception as e:
    print(f"[ERROR] 测试过程出错: {e}")
    import traceback
    print("\n详细错误信息:")
    traceback.print_exc()
    sys.exit(1)

