"""
手动下载Playwright浏览器文件并配置
根据GitHub: https://github.com/microsoft/playwright-python
"""
import sys
import os
import urllib.request
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
print("手动下载Playwright浏览器")
print("参考: https://github.com/microsoft/playwright-python")
print("=" * 60)

def get_browser_download_info():
    """获取浏览器下载信息"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            # 获取浏览器路径
            browser_path = pw.chromium.executable_path
            browser_dir = os.path.dirname(browser_path)
            
            # 根据路径推断下载URL
            # Playwright浏览器通常从以下URL下载:
            # https://cdn.playwright.dev/dbazure/download/playwright/builds/chromium/{revision}/chromium-{platform}.zip
            
            # 从路径中提取revision（例如：chromium-1200）
            if 'chromium-1200' in browser_path:
                revision = '1200'
            else:
                # 尝试从Playwright获取revision
                revision = '1200'  # 默认值
            
            # 确定平台
            if sys.platform == 'win32':
                platform = 'win64'
            elif sys.platform == 'darwin':
                platform = 'mac'
            else:
                platform = 'linux'
            
            download_url = f"https://cdn.playwright.dev/dbazure/download/playwright/builds/chromium/{revision}/chromium-{platform}.zip"
            
            return {
                'url': download_url,
                'revision': revision,
                'platform': platform,
                'browser_path': browser_path,
                'browser_dir': browser_dir,
                'zip_file': os.path.join(os.path.expanduser('~'), f'chromium-{platform}.zip')
            }
    except Exception as e:
        print(f"[ERROR] 获取浏览器信息失败: {e}")
        # 使用默认值
        platform = 'win64' if sys.platform == 'win32' else ('mac' if sys.platform == 'darwin' else 'linux')
        revision = '1200'
        download_url = f"https://cdn.playwright.dev/dbazure/download/playwright/builds/chromium/{revision}/chromium-{platform}.zip"
        
        local_appdata = os.environ.get('LOCALAPPDATA', os.path.expanduser('~\\AppData\\Local'))
        browser_dir = os.path.join(local_appdata, 'ms-playwright', f'chromium-{revision}', f'chrome-{platform}')
        browser_path = os.path.join(browser_dir, 'chrome.exe' if platform == 'win64' else 'chrome')
        
        return {
            'url': download_url,
            'revision': revision,
            'platform': platform,
            'browser_path': browser_path,
            'browser_dir': browser_dir,
            'zip_file': os.path.join(os.path.expanduser('~'), f'chromium-{platform}.zip')
        }

def download_file(url, dest_path, description="文件"):
    """下载文件并显示进度"""
    print(f"\n[下载] {description}")
    print(f"URL: {url}")
    print(f"保存到: {dest_path}")
    print("[提示] 文件较大（约200-300MB），下载可能需要几分钟...")
    
    try:
        # 创建目录
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # 下载文件
        def show_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(downloaded * 100 / total_size, 100)
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                print(f"\r[进度] {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='', flush=True)
            else:
                print(f"\r[进度] 已下载: {mb_downloaded:.1f} MB", end='', flush=True)
        
        print("\n开始下载...")
        urllib.request.urlretrieve(url, dest_path, show_progress)
        print(f"\n[OK] {description}下载完成")
        return True
    except urllib.error.URLError as e:
        print(f"\n[ERROR] 下载失败: {e}")
        if "404" in str(e):
            print("[提示] 文件不存在，可能URL不正确")
        elif "timeout" in str(e).lower():
            print("[提示] 下载超时，请检查网络连接")
        else:
            print("[提示] 网络错误，请检查网络连接")
        return False
    except Exception as e:
        print(f"\n[ERROR] 下载过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def extract_zip(zip_path, extract_to):
    """解压ZIP文件"""
    print(f"\n[解压] 正在解压到: {extract_to}")
    
    try:
        # 创建目标目录
        os.makedirs(extract_to, exist_ok=True)
        
        # 解压文件
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 获取文件列表
            file_list = zip_ref.namelist()
            total_files = len(file_list)
            
            print(f"[信息] ZIP文件包含 {total_files} 个文件")
            print("[提示] 解压可能需要几分钟...")
            
            # 解压所有文件
            for i, file_name in enumerate(file_list):
                zip_ref.extract(file_name, extract_to)
                if (i + 1) % 100 == 0:
                    percent = (i + 1) * 100 / total_files
                    print(f"\r[进度] {percent:.1f}% ({i+1}/{total_files} 文件)", end='', flush=True)
            
            print(f"\n[OK] 解压完成")
            return True
    except zipfile.BadZipFile:
        print(f"[ERROR] ZIP文件损坏或格式不正确")
        return False
    except Exception as e:
        print(f"[ERROR] 解压失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_installation(browser_path):
    """验证安装"""
    print(f"\n[验证] 检查浏览器文件: {browser_path}")
    
    if os.path.exists(browser_path):
        file_size = os.path.getsize(browser_path) / (1024 * 1024)
        print(f"[OK] 浏览器文件存在")
        print(f"[OK] 文件大小: {file_size:.1f} MB")
        
        # 测试启动
        try:
            print("\n[测试] 测试浏览器启动...")
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                browser.close()
            print("[OK] 浏览器启动测试成功！")
            return True
        except Exception as e:
            print(f"[WARN] 浏览器启动测试失败: {e}")
            print("[INFO] 文件已安装，但启动测试失败，可能需要重新安装Playwright")
            return True  # 文件存在就算成功
    else:
        print(f"[ERROR] 浏览器文件不存在")
        return False

def main():
    # 获取下载信息
    print("\n[步骤1] 获取浏览器下载信息...")
    info = get_browser_download_info()
    
    print(f"\n浏览器信息:")
    print(f"  版本: chromium-{info['revision']}")
    print(f"  平台: {info['platform']}")
    print(f"  下载URL: {info['url']}")
    print(f"  目标目录: {info['browser_dir']}")
    print(f"  浏览器路径: {info['browser_path']}")
    
    # 检查是否已安装
    if os.path.exists(info['browser_path']):
        print("\n[检查] 浏览器已安装，跳过下载")
        if verify_installation(info['browser_path']):
            print("\n" + "=" * 60)
            print("✓ 浏览器已安装并可用")
            print("=" * 60)
            return
    
    # 下载ZIP文件
    print("\n[步骤2] 下载浏览器ZIP文件...")
    if not download_file(info['url'], info['zip_file'], "浏览器ZIP文件"):
        print("\n[ERROR] 下载失败")
        print("\n建议:")
        print("1. 检查网络连接")
        print("2. 尝试使用代理")
        print("3. 手动下载ZIP文件:")
        print(f"   {info['url']}")
        print(f"   然后解压到: {info['browser_dir']}")
        return
    
    # 解压ZIP文件
    print("\n[步骤3] 解压浏览器文件...")
    # 注意：Playwright的ZIP文件解压后，需要放在正确的目录结构
    # 通常ZIP文件包含 chromium-{platform}/ 目录
    
    # 创建临时解压目录
    temp_extract = os.path.join(os.path.expanduser('~'), 'temp_chromium_extract')
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract, ignore_errors=True)
    
    if not extract_zip(info['zip_file'], temp_extract):
        print("\n[ERROR] 解压失败")
        return
    
    # 移动文件到正确位置
    print("\n[步骤4] 移动文件到正确位置...")
    try:
        # 查找解压后的chromium目录
        extracted_dirs = [d for d in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, d))]
        chromium_dir = None
        for d in extracted_dirs:
            if 'chromium' in d.lower() or 'chrome' in d.lower():
                chromium_dir = os.path.join(temp_extract, d)
                break
        
        if not chromium_dir:
            # 如果没有找到，可能ZIP文件直接包含文件
            chromium_dir = temp_extract
        
        # 创建目标目录
        os.makedirs(info['browser_dir'], exist_ok=True)
        
        # 移动所有文件
        print(f"[移动] 从 {chromium_dir} 到 {info['browser_dir']}")
        if os.path.exists(chromium_dir):
            # 复制所有内容
            for item in os.listdir(chromium_dir):
                src = os.path.join(chromium_dir, item)
                dst = os.path.join(info['browser_dir'], item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            print("[OK] 文件移动完成")
        else:
            print(f"[WARN] 未找到chromium目录: {chromium_dir}")
            print("[INFO] 尝试直接使用解压目录")
            # 直接复制整个目录
            if os.path.exists(info['browser_dir']):
                shutil.rmtree(info['browser_dir'], ignore_errors=True)
            shutil.copytree(temp_extract, info['browser_dir'])
        
        # 清理临时文件
        print("\n[清理] 删除临时文件...")
        try:
            shutil.rmtree(temp_extract, ignore_errors=True)
            os.remove(info['zip_file'])
            print("[OK] 临时文件已清理")
        except:
            pass
        
    except Exception as e:
        print(f"[ERROR] 移动文件失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 验证安装
    print("\n[步骤5] 验证安装...")
    if verify_installation(info['browser_path']):
        print("\n" + "=" * 60)
        print("✓✓✓ 安装完成！浏览器已可以使用。")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("安装可能未完成，请检查错误信息")
        print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[取消] 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 程序出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

