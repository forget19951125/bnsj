"""
使用国内镜像源安装Playwright浏览器
支持的环境变量: PLAYWRIGHT_DOWNLOAD_HOST
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
print("Playwright浏览器安装（使用国内镜像源）")
print("=" * 60)

# 国内镜像源配置
# 根据搜索结果，可以使用 npmmirror.com 的 Playwright 镜像
MIRROR_HOST = "https://npmmirror.com/mirrors/playwright"

# 设置环境变量
env = os.environ.copy()

# 方法1: 设置Playwright下载主机（推荐）
env['PLAYWRIGHT_DOWNLOAD_HOST'] = MIRROR_HOST

# 方法2: 同时设置代理（如果需要）
PROXY = "http://127.0.0.1:7890"
env['HTTP_PROXY'] = PROXY
env['HTTPS_PROXY'] = PROXY
env['http_proxy'] = PROXY
env['https_proxy'] = PROXY

# 方法3: 设置npm镜像（Playwright可能使用npm）
env['npm_config_registry'] = 'https://registry.npmmirror.com'

print("\n配置:")
print(f"- Playwright镜像: {MIRROR_HOST}")
print(f"- npm镜像: {env.get('npm_config_registry', 'Not set')}")
print(f"- 代理: {PROXY}")
print("\n开始安装...")
print("=" * 60)
sys.stdout.flush()

try:
    print("\n执行: python -m playwright install chromium")
    print("[提示] 使用国内镜像，应该会更快...")
    print("[提示] 如果仍然很慢，可能是镜像源问题\n")
    sys.stdout.flush()
    
    # 直接运行，输出到控制台
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
                    print(f"[OK] 浏览器已安装")
                    print(f"[OK] 路径: {browser_path}")
                    print(f"[OK] 大小: {file_size:.1f} MB")
                    
                    # 测试启动
                    print("\n[测试] 测试浏览器启动...")
                    browser = pw.chromium.launch(headless=True)
                    browser.close()
                    print("[OK] 浏览器启动测试成功！")
                else:
                    print(f"[WARN] 路径存在但文件不存在: {browser_path}")
        except Exception as e:
            print(f"[WARN] 验证失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"[ERROR] 安装失败，退出码: {result}")
        print("\n如果安装失败，可以尝试:")
        print("1. 检查镜像源是否可用")
        print("2. 尝试不使用镜像，直接下载")
        print("3. 手动下载浏览器文件")
    print("=" * 60)
    
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

