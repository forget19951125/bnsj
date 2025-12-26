"""
使用代理安装Playwright浏览器（显示详细日志）
"""
import sys
import os
import subprocess

# 设置控制台编码
if sys.platform == 'win32':
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 代理设置
PROXY = "http://127.0.0.1:7890"

print("=" * 60)
print("Playwright浏览器安装工具（使用代理）")
print("=" * 60)
print(f"\n代理设置: {PROXY}")
print("\n[提示] 如果安装失败，请检查：")
print("1. 代理是否正常运行（127.0.0.1:7890）")
print("2. 网络连接是否正常")
print("3. 防火墙是否阻止了连接")
print("\n开始安装...")
print("=" * 60)

# 设置代理环境变量
env = os.environ.copy()
env['HTTP_PROXY'] = PROXY
env['HTTPS_PROXY'] = PROXY
env['http_proxy'] = PROXY  # 小写版本
env['https_proxy'] = PROXY  # 小写版本

# 设置超时时间（10分钟）
env['PLAYWRIGHT_DOWNLOAD_CONNECTION_TIMEOUT'] = '600000'

try:
    print("\n[执行] python -m playwright install chromium")
    print("[提示] 安装过程可能需要几分钟，请耐心等待...")
    print("[提示] 如果看到下载进度，说明正在下载中...\n")
    sys.stdout.flush()  # 确保输出立即显示
    
    # 直接运行命令，输出到控制台（不使用PIPE，避免缓冲问题）
    return_code = subprocess.call(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env
    )
    
    print("\n" + "=" * 60)
    if return_code == 0:
        print("[OK] 安装成功！")
        
        # 验证安装
        print("\n[验证] 检查浏览器是否已安装...")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser_path = pw.chromium.executable_path
                if os.path.exists(browser_path):
                    print(f"[OK] 浏览器路径: {browser_path}")
                    print(f"[OK] 文件存在，安装验证成功！")
                else:
                    print(f"[WARN] 浏览器路径存在但文件不存在: {browser_path}")
        except Exception as e:
            print(f"[WARN] 验证时出错: {e}")
    else:
        print(f"[ERROR] 安装失败，退出码: {return_code}")
        print("\n建议:")
        print("1. 检查代理设置是否正确")
        print("2. 尝试关闭代理后重新安装")
        print("3. 检查网络连接")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断安装")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 安装过程出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

