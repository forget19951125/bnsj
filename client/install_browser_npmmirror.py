"""
按照npmmirror网站说明安装Playwright浏览器
参考: https://npmmirror.com/package/playwright
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
print("按照npmmirror说明安装Playwright浏览器")
print("参考: https://npmmirror.com/package/playwright")
print("=" * 60)

# 根据npmmirror的使用说明，需要设置registry
env = os.environ.copy()

# 方法1: 设置npm registry为npmmirror（Playwright可能使用npm下载浏览器）
env['npm_config_registry'] = 'https://registry.npmmirror.com'

# 方法2: 设置Playwright下载主机
# npmmirror提供二进制文件镜像在 /mirrors/ 目录下
env['PLAYWRIGHT_DOWNLOAD_HOST'] = 'https://npmmirror.com/mirrors/playwright'

# 方法3: 设置disturl（npm下载二进制文件的URL）
env['npm_config_disturl'] = 'https://npmmirror.com/mirrors/node'

# 不使用代理（直接连接镜像）
env.pop('HTTP_PROXY', None)
env.pop('HTTPS_PROXY', None)
env.pop('http_proxy', None)
env.pop('https_proxy', None)

# Python输出编码
env['PYTHONIOENCODING'] = 'utf-8'

print("\n环境变量配置（按照npmmirror说明）:")
print(f"  npm_config_registry = {env.get('npm_config_registry')}")
print(f"  npm_config_disturl = {env.get('npm_config_disturl')}")
print(f"  PLAYWRIGHT_DOWNLOAD_HOST = {env.get('PLAYWRIGHT_DOWNLOAD_HOST')}")
print(f"  代理 = 未设置（直接连接镜像）")

print("\n开始安装...")
print("=" * 60)
sys.stdout.flush()

try:
    # 测试连接
    print("\n[测试] 测试npmmirror连接...")
    try:
        import urllib.request
        # 测试registry
        registry_url = "https://registry.npmmirror.com/playwright"
        req = urllib.request.Request(registry_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"[OK] npm registry可访问: {registry_url}")
        
        # 测试镜像目录
        mirror_url = "https://npmmirror.com/mirrors/playwright"
        req2 = urllib.request.Request(mirror_url)
        req2.add_header('User-Agent', 'Mozilla/5.0')
        try:
            with urllib.request.urlopen(req2, timeout=10) as response2:
                print(f"[OK] 镜像目录可访问: {mirror_url}")
        except:
            print(f"[INFO] 镜像目录可能需要具体文件路径")
    except Exception as e:
        print(f"[WARN] 连接测试失败: {e}")
        print("[INFO] 继续尝试安装...")
    
    print("\n[执行] python -m playwright install chromium")
    print("[提示] 使用npmmirror镜像源")
    print("[提示] 安装过程可能需要几分钟，请耐心等待...\n")
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
                    print(f"[OK] ✓ 浏览器文件存在！")
                    print(f"[OK] 文件大小: {file_size:.1f} MB")
                    
                    # 测试启动
                    print("\n[测试] 测试浏览器启动...")
                    browser = pw.chromium.launch(headless=True)
                    browser.close()
                    print("[OK] ✓ 浏览器启动测试成功！")
                    print("\n" + "=" * 60)
                    print("✓✓✓ 安装完成！浏览器已可以使用。")
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
        print("\n如果安装失败，可以尝试:")
        print("1. 检查网络连接")
        print("2. 访问 https://npmmirror.com/package/playwright 查看最新说明")
        print("3. 尝试手动下载浏览器文件")
    print("=" * 60)
    
except subprocess.TimeoutExpired:
    print("\n[ERROR] 安装超时（超过10分钟）")
    print("\n建议:")
    print("1. 检查网络连接")
    print("2. 访问 https://npmmirror.com/package/playwright 查看是否有其他安装方法")
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断安装")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 安装过程出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

