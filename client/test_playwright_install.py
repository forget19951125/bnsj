"""
测试Playwright安装命令，带超时和详细日志
"""
import sys
import os
import subprocess
import threading
import time

# 设置控制台编码
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

PROXY = "http://127.0.0.1:7890"

print("=" * 60)
print("测试Playwright安装命令")
print("=" * 60)

# 设置环境变量
env = os.environ.copy()
env['HTTP_PROXY'] = PROXY
env['HTTPS_PROXY'] = PROXY
env['http_proxy'] = PROXY
env['https_proxy'] = PROXY

# 先测试 --dry-run（不会真正下载）
print("\n[测试1] 运行 --dry-run（不会真正下载）...")
print("命令: python -m playwright install chromium --dry-run\n")
sys.stdout.flush()

try:
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium", "--dry-run"],
        env=env,
        timeout=30,  # 30秒超时
        capture_output=True,
        text=True
    )
    
    print(f"退出码: {result.returncode}")
    print(f"\n标准输出:\n{result.stdout}")
    if result.stderr:
        print(f"\n标准错误:\n{result.stderr}")
        
except subprocess.TimeoutExpired:
    print("[ERROR] 命令超时（30秒）")
    print("[提示] playwright install 命令可能在等待网络连接")
except Exception as e:
    print(f"[ERROR] 执行出错: {e}")

print("\n" + "=" * 60)

# 如果 --dry-run 成功，再尝试真实安装
print("\n[测试2] 检查浏览器是否已安装...")
try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        try:
            browser_path = pw.chromium.executable_path
            print(f"浏览器路径: {browser_path}")
            if os.path.exists(browser_path):
                print("[OK] 浏览器已安装！")
            else:
                print("[WARN] 浏览器路径存在但文件不存在")
                print("\n[建议] 尝试手动安装:")
                print(f"  1. 打开新的命令行窗口")
                print(f"  2. 设置代理: set HTTP_PROXY={PROXY}")
                print(f"  3. 运行: python -m playwright install chromium")
        except Exception as e:
            print(f"[ERROR] 检查浏览器失败: {e}")
            print("\n[建议] 需要安装浏览器")
except Exception as e:
    print(f"[ERROR] 导入playwright失败: {e}")

print("\n" + "=" * 60)

