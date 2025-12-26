"""
使用国内镜像源安装Playwright浏览器
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
print("Playwright浏览器安装工具（使用国内镜像）")
print("=" * 60)

# 国内镜像源配置
MIRRORS = {
    'tsinghua': 'https://mirrors.tuna.tsinghua.edu.cn/playwright/',
    'aliyun': 'https://mirrors.aliyun.com/playwright/',
    'tencent': 'https://mirrors.cloud.tencent.com/playwright/',
}

# 设置环境变量使用国内镜像
# Playwright使用PLAYWRIGHT_DOWNLOAD_HOST环境变量来指定下载服务器
env = os.environ.copy()

# 方法1: 使用Playwright的镜像环境变量（如果支持）
# 注意：Playwright可能不支持直接设置镜像URL，但我们可以尝试设置下载主机

# 方法2: 使用代理指向国内镜像（如果镜像支持）
PROXY = "http://127.0.0.1:7890"
env['HTTP_PROXY'] = PROXY
env['HTTPS_PROXY'] = PROXY
env['http_proxy'] = PROXY
env['https_proxy'] = PROXY

# 方法3: 尝试设置npm镜像（Playwright可能使用npm来下载）
# 但这可能不适用于Python版本

print("\n尝试的镜像源:")
print("1. 清华大学镜像")
print("2. 阿里云镜像")
print("3. 腾讯云镜像")
print("\n注意: Playwright Python版本可能不支持直接设置镜像源")
print("将尝试使用代理 + 可能的镜像配置\n")

# 尝试设置Playwright下载主机（如果支持）
# 根据Playwright文档，可能需要设置PLAYWRIGHT_DOWNLOAD_HOST
# 但具体格式可能因版本而异

print("=" * 60)
print("开始安装...")
print("=" * 60)
sys.stdout.flush()

try:
    print("\n执行命令: python -m playwright install chromium")
    print("[提示] 如果卡住，可能是网络问题")
    print("[提示] 可以尝试:")
    print("  1. 检查代理是否正常工作")
    print("  2. 尝试不使用代理")
    print("  3. 使用VPN或其他网络工具\n")
    sys.stdout.flush()
    
    # 直接运行，输出到控制台
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
                    file_size = os.path.getsize(browser_path) / (1024 * 1024)
                    print(f"[OK] 浏览器已安装")
                    print(f"[OK] 路径: {browser_path}")
                    print(f"[OK] 大小: {file_size:.1f} MB")
                else:
                    print(f"[WARN] 路径存在但文件不存在: {browser_path}")
        except Exception as e:
            print(f"[WARN] 验证失败: {e}")
    else:
        print(f"[ERROR] 安装失败，退出码: {result.returncode}")
    print("=" * 60)
    
except subprocess.TimeoutExpired:
    print("\n[ERROR] 安装超时（超过10分钟）")
    print("\n建议:")
    print("1. 检查网络连接")
    print("2. 尝试手动下载浏览器文件")
    print("3. 查看Playwright文档: https://playwright.dev/python/docs/installation")
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断")
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

