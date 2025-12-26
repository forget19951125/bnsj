"""
修复编码问题的浏览器安装脚本
"""
import sys
import os
import subprocess

# 设置控制台编码为UTF-8
if sys.platform == 'win32':
    import io
    try:
        # 设置标准输出和错误输出为UTF-8
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

PROXY = "http://127.0.0.1:7890"

print("=" * 60)
print("Playwright浏览器安装工具（修复版）")
print("=" * 60)
print(f"\n代理: {PROXY}")
print("\n开始安装...")
print("=" * 60)
sys.stdout.flush()

# 设置环境变量
env = os.environ.copy()
env['HTTP_PROXY'] = PROXY
env['HTTPS_PROXY'] = PROXY
env['http_proxy'] = PROXY
env['https_proxy'] = PROXY

# 设置Python输出编码
env['PYTHONIOENCODING'] = 'utf-8'

print("\n执行命令: python -m playwright install chromium")
print("[提示] 这可能需要几分钟，请耐心等待...")
print("[提示] 如果长时间没有输出，可能是网络问题\n")
sys.stdout.flush()

try:
    # 直接运行，不使用PIPE，避免编码和缓冲问题
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env,
        timeout=600  # 10分钟超时
    )
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("[OK] 安装成功！")
        
        # 验证
        print("\n[验证] 检查浏览器...")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser_path = pw.chromium.executable_path
                if os.path.exists(browser_path):
                    print(f"[OK] 浏览器已安装: {browser_path}")
                else:
                    print(f"[WARN] 路径存在但文件不存在: {browser_path}")
        except Exception as e:
            print(f"[WARN] 验证失败: {e}")
    else:
        print(f"[ERROR] 安装失败，退出码: {result.returncode}")
        print("\n建议:")
        print("1. 检查代理是否正常: curl -x http://127.0.0.1:7890 https://www.google.com")
        print("2. 尝试不使用代理安装")
        print("3. 检查网络连接")
    print("=" * 60)
    
except subprocess.TimeoutExpired:
    print("\n[ERROR] 安装超时（超过10分钟）")
    print("[提示] 可能是网络问题，请检查代理和网络连接")
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

