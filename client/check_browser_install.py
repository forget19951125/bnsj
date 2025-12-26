"""
检查Playwright浏览器安装状态
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
print("Playwright浏览器安装状态检查")
print("=" * 60)

# 检查1: Playwright模块
print("\n[检查1] Playwright模块...")
try:
    import playwright
    print(f"[OK] Playwright已安装")
except ImportError:
    print("[ERROR] Playwright未安装")
    print("请运行: pip install playwright")
    sys.exit(1)

# 检查2: 浏览器路径
print("\n[检查2] 浏览器路径...")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser_path = pw.chromium.executable_path
        print(f"[INFO] 浏览器路径: {browser_path}")
        
        # 检查文件是否存在
        if os.path.exists(browser_path):
            file_size = os.path.getsize(browser_path) / (1024 * 1024)
            print(f"[OK] 浏览器文件存在")
            print(f"[OK] 文件大小: {file_size:.1f} MB")
        else:
            print(f"[ERROR] 浏览器文件不存在")
            print(f"[INFO] 需要安装浏览器")
            
            # 检查目录是否存在
            browser_dir = os.path.dirname(browser_path)
            if os.path.exists(browser_dir):
                print(f"[INFO] 浏览器目录存在: {browser_dir}")
                # 列出目录内容
                try:
                    files = os.listdir(browser_dir)
                    print(f"[INFO] 目录中的文件数: {len(files)}")
                    if files:
                        print("[INFO] 目录内容:")
                        for f in files[:10]:  # 只显示前10个
                            print(f"  - {f}")
                except:
                    pass
            else:
                print(f"[INFO] 浏览器目录不存在: {browser_dir}")
except Exception as e:
    print(f"[ERROR] 检查失败: {e}")
    import traceback
    traceback.print_exc()

# 检查3: 安装目录
print("\n[检查3] Playwright安装目录...")
if sys.platform == 'win32':
    local_appdata = os.environ.get('LOCALAPPDATA', '')
    playwright_dir = os.path.join(local_appdata, 'ms-playwright')
else:
    playwright_dir = os.path.expanduser('~/.cache/ms-playwright')

print(f"[INFO] Playwright目录: {playwright_dir}")
if os.path.exists(playwright_dir):
    print("[OK] Playwright目录存在")
    try:
        subdirs = [d for d in os.listdir(playwright_dir) if os.path.isdir(os.path.join(playwright_dir, d))]
        print(f"[INFO] 子目录数: {len(subdirs)}")
        if subdirs:
            print("[INFO] 子目录:")
            for d in subdirs:
                print(f"  - {d}")
    except:
        pass
else:
    print("[INFO] Playwright目录不存在（首次安装）")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)

print("\n如果浏览器未安装，请尝试:")
print("1. 运行: python install_browser_china_mirror.py")
print("2. 或手动运行: python -m playwright install chromium")
print("3. 如果网络问题，可以尝试:")
print("   - 设置代理")
print("   - 使用VPN")
print("   - 手动下载浏览器文件")

