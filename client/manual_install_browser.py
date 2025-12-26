"""
手动下载并安装Playwright浏览器
"""
import sys
import os
import json
import subprocess
import urllib.request
import urllib.error
import zipfile
import shutil
from pathlib import Path

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

def setup_proxy():
    """设置代理"""
    proxy_handler = urllib.request.ProxyHandler({
        'http': PROXY,
        'https': PROXY
    })
    opener = urllib.request.build_opener(proxy_handler)
    urllib.request.install_opener(opener)
    print(f"[OK] 已设置代理: {PROXY}")

def get_playwright_browser_path():
    """获取Playwright浏览器安装路径"""
    if sys.platform == 'win32':
        local_appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        return os.path.join(local_appdata, 'ms-playwright')
    else:
        return os.path.expanduser('~/.cache/ms-playwright')

def get_chromium_download_url():
    """获取Chromium下载URL"""
    try:
        # 获取Playwright版本
        import playwright
        playwright_version = playwright.__version__
        print(f"[INFO] Playwright版本: {playwright_version}")
        
        # 尝试从Playwright获取浏览器版本信息
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                # 尝试获取浏览器信息
                try:
                    browser_path = pw.chromium.executable_path
                    print(f"[INFO] 浏览器路径: {browser_path}")
                    return None  # 如果路径存在，不需要下载
                except:
                    pass
        except:
            pass
        
        # 根据Playwright版本，Chromium版本通常是固定的
        # Playwright 1.40+ 使用 Chromium 1200
        # 我们可以尝试从Playwright的服务器下载
        # 但更简单的方法是使用playwright的安装脚本
        
        print("[INFO] 尝试使用Playwright内置安装方法...")
        return None
        
    except Exception as e:
        print(f"[ERROR] 获取下载URL失败: {e}")
        return None

def download_file(url, dest_path, description="文件"):
    """下载文件"""
    print(f"\n[下载] 开始下载 {description}...")
    print(f"URL: {url}")
    print(f"保存到: {dest_path}")
    
    try:
        # 创建目录
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # 下载文件
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(downloaded * 100 / total_size, 100) if total_size > 0 else 0
            print(f"\r[进度] {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        urllib.request.urlretrieve(url, dest_path, show_progress)
        print(f"\n[OK] {description}下载完成")
        return True
    except urllib.error.URLError as e:
        print(f"\n[ERROR] 下载失败: {e}")
        if "proxy" in str(e).lower() or "connection" in str(e).lower():
            print("[提示] 可能是代理设置问题，请检查代理是否正常工作")
        return False
    except Exception as e:
        print(f"\n[ERROR] 下载过程出错: {e}")
        return False

def install_via_playwright_cli():
    """通过Playwright CLI安装"""
    print("\n" + "=" * 60)
    print("方法1: 使用Playwright CLI安装（推荐）")
    print("=" * 60)
    
    # 设置代理环境变量
    env = os.environ.copy()
    env['HTTP_PROXY'] = PROXY
    env['HTTPS_PROXY'] = PROXY
    
    print(f"\n[安装] 使用代理 {PROXY} 安装Chromium...")
    print("[提示] 这可能需要几分钟，请耐心等待...")
    
    try:
        # 使用subprocess运行安装命令
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            env=env,
            capture_output=False,  # 显示实时输出
            text=True,
            timeout=600  # 10分钟超时
        )
        
        if result.returncode == 0:
            print("\n[OK] Chromium安装成功！")
            return True
        else:
            print(f"\n[ERROR] 安装失败，退出码: {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        print("\n[ERROR] 安装超时（超过10分钟）")
        print("[提示] 可能是网络问题，请检查代理设置或网络连接")
        return False
    except Exception as e:
        print(f"\n[ERROR] 安装过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_installation():
    """验证安装"""
    print("\n" + "=" * 60)
    print("验证安装...")
    print("=" * 60)
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser_path = pw.chromium.executable_path
            print(f"\n[检查] 浏览器路径: {browser_path}")
            
            if os.path.exists(browser_path):
                print(f"[OK] 浏览器可执行文件存在")
                file_size = os.path.getsize(browser_path) / (1024 * 1024)  # MB
                print(f"[OK] 文件大小: {file_size:.1f} MB")
                return True
            else:
                print(f"[ERROR] 浏览器可执行文件不存在")
                return False
    except Exception as e:
        print(f"[ERROR] 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("Playwright浏览器手动安装工具")
    print("=" * 60)
    
    # 设置代理
    setup_proxy()
    
    # 检查是否已安装
    print("\n[检查] 检查是否已安装...")
    if verify_installation():
        print("\n[OK] 浏览器已安装，无需重新安装")
        return
    
    # 尝试安装
    print("\n[安装] 开始安装...")
    if install_via_playwright_cli():
        # 验证安装
        if verify_installation():
            print("\n" + "=" * 60)
            print("安装成功！")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("安装可能未完成，请手动验证")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("安装失败")
        print("\n建议:")
        print("1. 检查代理设置是否正确（当前: " + PROXY + "）")
        print("2. 检查网络连接")
        print("3. 尝试手动运行: python -m playwright install chromium")
        print("4. 查看Playwright文档: https://playwright.dev/python/docs/installation")
        print("=" * 60)

if __name__ == "__main__":
    main()

