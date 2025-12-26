"""
不使用代理，直接使用npmmirror镜像安装Playwright浏览器
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
print("Playwright浏览器安装（使用npmmirror镜像，不使用代理）")
print("=" * 60)

# 设置环境变量（不使用代理）
env = os.environ.copy()

# 移除代理设置（如果存在）
env.pop('HTTP_PROXY', None)
env.pop('HTTPS_PROXY', None)
env.pop('http_proxy', None)
env.pop('https_proxy', None)

# 设置Playwright下载镜像
env['PLAYWRIGHT_DOWNLOAD_HOST'] = 'https://npmmirror.com/mirrors/playwright'

# 设置npm镜像
env['npm_config_registry'] = 'https://registry.npmmirror.com'

# Python输出编码
env['PYTHONIOENCODING'] = 'utf-8'

print("\n环境变量配置:")
print(f"  PLAYWRIGHT_DOWNLOAD_HOST = {env.get('PLAYWRIGHT_DOWNLOAD_HOST')}")
print(f"  npm_config_registry = {env.get('npm_config_registry')}")
print(f"  HTTP_PROXY = {env.get('HTTP_PROXY', '未设置（不使用代理）')}")
print(f"  HTTPS_PROXY = {env.get('HTTPS_PROXY', '未设置（不使用代理）')}")

print("\n开始安装...")
print("=" * 60)
sys.stdout.flush()

try:
    # 测试镜像源连接
    print("\n[测试] 测试npmmirror镜像源连接...")
    try:
        import urllib.request
        test_url = "https://npmmirror.com/package/playwright"
        req = urllib.request.Request(test_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"[OK] 镜像源可访问: {test_url}")
    except Exception as e:
        print(f"[WARN] 镜像源测试失败: {e}")
        print("[INFO] 继续尝试安装...")
    
    print("\n[执行] python -m playwright install chromium")
    print("[提示] 使用npmmirror镜像，不使用代理")
    print("[提示] 安装过程可能需要几分钟，请耐心等待...")
    print("[提示] 如果看到下载进度，说明正在下载中...\n")
    sys.stdout.flush()
    
    # 直接运行，输出到控制台
    result = subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env,
        timeout=600  # 10分钟超时
    )
    
    print("\n" + "=" * 60)
    if result.returncode == 0:
        print("[OK] 安装命令执行成功！")
        
        # 验证安装
        print("\n[验证] 检查浏览器是否已安装...")
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser_path = pw.chromium.executable_path
                print(f"[INFO] 浏览器路径: {browser_path}")
                
                if os.path.exists(browser_path):
                    file_size = os.path.getsize(browser_path) / (1024 * 1024)
                    print(f"[OK] 浏览器文件存在！")
                    print(f"[OK] 文件大小: {file_size:.1f} MB")
                    
                    # 测试启动
                    print("\n[测试] 测试浏览器启动...")
                    browser = pw.chromium.launch(headless=True)
                    browser.close()
                    print("[OK] 浏览器启动测试成功！")
                    print("\n" + "=" * 60)
                    print("✓ 安装完成！浏览器已可以使用。")
                    print("=" * 60)
                else:
                    print(f"[ERROR] 浏览器文件不存在: {browser_path}")
                    print("\n可能的原因:")
                    print("1. 下载过程中断")
                    print("2. 文件解压失败")
                    print("3. 权限问题")
        except Exception as e:
            print(f"[ERROR] 验证失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"[ERROR] 安装失败，退出码: {result.returncode}")
        print("\n建议:")
        print("1. 检查网络连接")
        print("2. 检查镜像源是否可访问")
        print("3. 查看Playwright文档: https://playwright.dev/python/docs/installation")
    print("=" * 60)
    
except subprocess.TimeoutExpired:
    print("\n[ERROR] 安装超时（超过10分钟）")
    print("\n可能的原因:")
    print("1. 网络连接慢")
    print("2. 镜像源响应慢")
    print("3. 下载被中断")
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断安装")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 安装过程出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

