"""
安装Playwright浏览器，实时显示下载进度
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

print("=" * 60)
print("Playwright浏览器安装（实时显示进度）")
print("=" * 60)

# 设置环境变量
env = os.environ.copy()

# 使用npmmirror镜像
env['PLAYWRIGHT_DOWNLOAD_HOST'] = 'https://npmmirror.com/mirrors/playwright'
env['npm_config_registry'] = 'https://registry.npmmirror.com'

# 不使用代理
env.pop('HTTP_PROXY', None)
env.pop('HTTPS_PROXY', None)
env.pop('http_proxy', None)
env.pop('https_proxy', None)

env['PYTHONIOENCODING'] = 'utf-8'

print("\n配置:")
print(f"  镜像源: {env.get('PLAYWRIGHT_DOWNLOAD_HOST')}")
print(f"  npm镜像: {env.get('npm_config_registry')}")
print(f"  代理: 不使用")

print("\n开始安装...")
print("=" * 60)
print("\n[提示] 浏览器文件较大（约200-300MB），下载可能需要几分钟")
print("[提示] 请耐心等待，下方会显示下载进度...\n")
sys.stdout.flush()

try:
    # 使用Popen启动进程，实时读取输出
    process = subprocess.Popen(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # 行缓冲
        universal_newlines=True
    )
    
    # 实时读取并输出
    print("[开始] 正在启动安装进程...\n")
    sys.stdout.flush()
    
    output_lines = []
    start_time = time.time()
    
    # 读取输出
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            line = output.strip()
            if line:
                print(line)
                sys.stdout.flush()
                output_lines.append(line)
                
                # 检查是否有进度信息
                if 'downloading' in line.lower() or 'downloaded' in line.lower() or '%' in line or 'mb' in line.lower():
                    elapsed = time.time() - start_time
                    print(f"[进度] 已用时: {elapsed:.1f}秒")
                    sys.stdout.flush()
    
    # 等待进程完成
    return_code = process.poll()
    
    elapsed_time = time.time() - start_time
    print(f"\n[完成] 安装过程耗时: {elapsed_time:.1f}秒")
    print("=" * 60)
    
    if return_code == 0:
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
                    sys.exit(0)
                else:
                    print(f"[ERROR] 浏览器文件不存在: {browser_path}")
                    print("\n可能的原因:")
                    print("1. 下载过程中断")
                    print("2. 文件解压失败")
                    print("3. 权限问题")
                    sys.exit(1)
        except Exception as e:
            print(f"[ERROR] 验证失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    else:
        print(f"[ERROR] 安装失败，退出码: {return_code}")
        print("\n输出内容:")
        for line in output_lines[-20:]:  # 显示最后20行
            print(f"  {line}")
        sys.exit(1)
    
except KeyboardInterrupt:
    print("\n\n[取消] 用户中断安装")
    if 'process' in locals():
        process.terminate()
    sys.exit(1)
except Exception as e:
    print(f"\n[ERROR] 安装过程出错: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

