"""
使用国内镜像安装Playwright浏览器（尝试多种方法）
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

print("=" * 60)
print("Playwright浏览器安装（国内镜像加速）")
print("=" * 60)

# 方法1: 使用npm镜像（如果Playwright使用npm下载）
# 设置npm使用淘宝镜像
env = os.environ.copy()

# 设置npm镜像
env['npm_config_registry'] = 'https://registry.npmmirror.com'

# 方法2: 尝试设置Playwright下载主机
# Playwright可能使用以下环境变量：
# - PLAYWRIGHT_DOWNLOAD_HOST
# - PLAYWRIGHT_BROWSERS_PATH
# 但具体格式需要查看Playwright源码

# 方法3: 使用代理 + 可能的镜像配置
PROXY = "http://127.0.0.1:7890"
env['HTTP_PROXY'] = PROXY
env['HTTPS_PROXY'] = PROXY
env['http_proxy'] = PROXY
env['https_proxy'] = PROXY

# 方法4: 尝试设置Playwright的下载基础URL
# 根据Playwright的下载机制，浏览器文件通常从以下URL下载：
# https://playwright.azureedge.net/builds/chromium/{revision}/chromium-{platform}.zip
# 我们可以尝试设置代理或使用CDN加速

print("\n配置:")
print(f"- npm镜像: {env.get('npm_config_registry', 'Not set')}")
print(f"- 代理: {PROXY}")
print("\n注意: Playwright Python版本可能不支持直接设置镜像源")
print("将尝试使用代理加速下载\n")

print("=" * 60)
print("开始安装...")
print("=" * 60)
sys.stdout.flush()

try:
    print("\n执行: python -m playwright install chromium")
    print("[提示] 安装可能需要几分钟，请耐心等待...\n")
    sys.stdout.flush()
    
    # 使用subprocess.call直接输出到控制台
    result = subprocess.call(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env
    )
    
    print("\n" + "=" * 60)
    if result == 0:
        print("[OK] 安装成功！")
        
        # 验证
        print("\n[验证] 检查浏览器...")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser_path = pw.chromium.executable_path
                if os.path.exists(browser_path):
                    file_size = os.path.getsize(browser_path) / (1024 * 1024)
                    print(f"[OK] 浏览器已安装: {browser_path}")
                    print(f"[OK] 文件大小: {file_size:.1f} MB")
                else:
                    print(f"[WARN] 路径存在但文件不存在: {browser_path}")
        except Exception as e:
            print(f"[WARN] 验证失败: {e}")
    else:
        print(f"[ERROR] 安装失败，退出码: {result}")
        print("\n如果安装失败，可以尝试:")
        print("1. 手动下载浏览器文件")
        print("2. 使用VPN或其他网络工具")
        print("3. 检查代理设置")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

