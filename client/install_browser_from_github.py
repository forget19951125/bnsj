"""
从GitHub或Playwright官方源安装浏览器
参考: https://github.com/microsoft/playwright
"""
import sys
import os
import subprocess
import urllib.request
import json
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

print("=" * 60)
print("Playwright浏览器安装（从GitHub/官方源）")
print("参考: https://github.com/microsoft/playwright")
print("=" * 60)

def get_playwright_version():
    """获取当前安装的Playwright版本"""
    try:
        import playwright
        # Playwright Python包可能没有__version__属性
        # 尝试从playwright模块获取
        try:
            version = playwright.__version__
        except:
            # 尝试从playwright包获取
            import pkg_resources
            version = pkg_resources.get_distribution('playwright').version
        return version
    except:
        # 如果无法获取，使用默认版本
        return "1.57.0"

def get_browser_download_url(version=None):
    """
    获取浏览器下载URL
    Playwright浏览器通常从Azure CDN下载:
    https://playwright.azureedge.net/builds/chromium/{revision}/chromium-{platform}.zip
    """
    if not version:
        version = get_playwright_version()
    
    print(f"\n[信息] Playwright版本: {version}")
    
    # 根据平台确定下载URL
    platform_map = {
        'win32': 'win64',
        'darwin': 'mac',
        'linux': 'linux'
    }
    platform = platform_map.get(sys.platform, 'win64')
    
    # Playwright使用特定的revision，需要从Playwright获取
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            # 尝试获取浏览器信息
            try:
                # 获取chromium的revision
                browser_type = pw.chromium
                # Playwright内部会处理revision
                print("[信息] 使用Playwright内置安装方法（推荐）")
                return None  # 返回None表示使用Playwright内置方法
            except:
                pass
    except:
        pass
    
    return None

def install_via_playwright_official():
    """使用Playwright官方方法安装（推荐）"""
    print("\n[方法] 使用Playwright官方安装方法")
    print("=" * 60)
    
    # 设置环境变量（不使用代理，直接连接）
    env = os.environ.copy()
    
    # 移除代理
    env.pop('HTTP_PROXY', None)
    env.pop('HTTPS_PROXY', None)
    env.pop('http_proxy', None)
    env.pop('https_proxy', None)
    
    # 移除镜像设置，使用官方源
    env.pop('PLAYWRIGHT_DOWNLOAD_HOST', None)
    env.pop('npm_config_registry', None)
    
    env['PYTHONIOENCODING'] = 'utf-8'
    
    print("\n配置:")
    print("  使用Playwright官方下载源")
    print("  不使用代理")
    print("  不使用镜像")
    
    print("\n开始安装...")
    print("[提示] 浏览器文件较大（约200-300MB），下载可能需要几分钟")
    print("[提示] 请耐心等待，下方会显示下载进度...\n")
    sys.stdout.flush()
    
    try:
        # 使用subprocess.Popen实时显示输出
        # 注意：在Windows上，使用errors='replace'来处理编码问题
        process = subprocess.Popen(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
            errors='replace'  # 处理编码错误
        )
        
        print("[开始] 正在启动安装进程...\n")
        sys.stdout.flush()
        
        import time
        start_time = time.time()
        last_output_time = start_time
        
        # 实时读取输出（处理编码问题）
        while True:
            try:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # 尝试解码，如果失败则使用错误处理
                    try:
                        line = output.strip()
                    except UnicodeDecodeError:
                        # 如果解码失败，尝试使用errors='replace'
                        line = output.encode('utf-8', errors='replace').decode('utf-8', errors='replace').strip()
                    
                    if line:
                        print(line)
                        sys.stdout.flush()
                        last_output_time = time.time()
                        
                        # 显示进度提示
                        elapsed = time.time() - start_time
                        if 'downloading' in line.lower() or 'downloaded' in line.lower() or '%' in line or 'mib' in line.lower():
                            print(f"[进度] 已用时: {elapsed:.1f}秒")
                            sys.stdout.flush()
            except UnicodeDecodeError as e:
                # 编码错误时继续，不中断
                print(f"[WARN] 编码错误（可忽略）: {e}")
                sys.stdout.flush()
                last_output_time = time.time()
            except Exception as e:
                # 其他错误也继续
                print(f"[WARN] 读取输出时出错（可忽略）: {e}")
                sys.stdout.flush()
                last_output_time = time.time()
            
            # 如果超过5秒没有输出，显示提示
            if time.time() - last_output_time > 5 and process.poll() is None:
                elapsed = time.time() - start_time
                print(f"[等待] 已等待 {elapsed:.1f}秒，正在下载中...")
                sys.stdout.flush()
                last_output_time = time.time()
        
        # 等待进程完成
        return_code = process.poll()
        elapsed_time = time.time() - start_time
        
        print(f"\n[完成] 安装过程耗时: {elapsed_time:.1f}秒")
        print("=" * 60)
        
        return return_code == 0
        
    except Exception as e:
        print(f"[ERROR] 安装过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_installation():
    """验证安装"""
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
                return True
            else:
                print(f"[ERROR] 浏览器文件不存在: {browser_path}")
                return False
    except Exception as e:
        print(f"[ERROR] 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n根据Playwright GitHub仓库说明:")
    print("Playwright浏览器通过 'playwright install' 命令安装")
    print("浏览器文件从Playwright官方CDN下载")
    print("参考: https://github.com/microsoft/playwright\n")
    
    # 检查是否已安装
    if verify_installation():
        print("\n" + "=" * 60)
        print("✓ 浏览器已安装，无需重新安装")
        print("=" * 60)
        return
    
    # 使用官方方法安装
    if install_via_playwright_official():
        # 验证安装
        if verify_installation():
            print("\n" + "=" * 60)
            print("✓✓✓ 安装完成！浏览器已可以使用。")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("安装可能未完成，请检查错误信息")
            print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("安装失败")
        print("\n建议:")
        print("1. 检查网络连接")
        print("2. 查看Playwright文档: https://playwright.dev/python/docs/installation")
        print("3. 查看GitHub Issues: https://github.com/microsoft/playwright/issues")
        print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[取消] 用户中断安装")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

