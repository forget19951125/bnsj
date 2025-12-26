"""
下载Playwright浏览器到 ./google_web 目录
"""
import sys
import os
import subprocess
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
print("下载Playwright浏览器到 ./google_web 目录")
print("=" * 60)

def get_browser_download_url():
    """获取浏览器下载URL"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            # 获取浏览器路径，从中提取revision
            try:
                browser_path = pw.chromium.executable_path
                # 从路径中提取revision，例如: .../chromium-1200/...
                import re
                match = re.search(r'chromium-(\d+)', browser_path)
                if match:
                    revision = match.group(1)
                else:
                    revision = '1200'  # 默认revision
            except:
                revision = '1200'
    except:
        revision = '1200'
    
    # 根据平台确定下载URL
    platform_map = {
        'win32': 'win64',
        'darwin': 'mac',
        'linux': 'linux'
    }
    platform = platform_map.get(sys.platform, 'win64')
    
    # Playwright浏览器下载URL
    download_url = f"https://playwright.azureedge.net/builds/chromium/{revision}/chromium-{platform}.zip"
    
    return download_url, revision, platform

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
    except Exception as e:
        print(f"\n[ERROR] 下载失败: {e}")
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
    except Exception as e:
        print(f"[ERROR] 解压失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    # 获取当前脚本所在目录（client目录）
    current_dir = os.path.dirname(os.path.abspath(__file__))
    google_web_dir = os.path.join(current_dir, 'google_web')
    
    print(f"\n目标目录: {google_web_dir}")
    
    # 检查是否已安装
    if sys.platform == 'win32':
        chrome_exe = os.path.join(google_web_dir, 'chrome-win64', 'chrome.exe')
    elif sys.platform == 'darwin':
        chrome_exe = os.path.join(google_web_dir, 'chrome-mac', 'chrome')
    else:
        chrome_exe = os.path.join(google_web_dir, 'chrome-linux', 'chrome')
    
    if os.path.exists(chrome_exe):
        print(f"\n[检查] 浏览器已存在于: {chrome_exe}")
        file_size = os.path.getsize(chrome_exe) / (1024 * 1024)
        print(f"[OK] 文件大小: {file_size:.1f} MB")
        
        # 测试启动
        try:
            print("\n[测试] 测试浏览器启动...")
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, executable_path=chrome_exe)
                browser.close()
            print("[OK] 浏览器启动测试成功！")
            print("\n" + "=" * 60)
            print("✓ 浏览器已安装并可用")
            print("=" * 60)
            return
        except Exception as e:
            print(f"[WARN] 浏览器启动测试失败: {e}")
            print("[INFO] 将重新下载...")
    
    # 获取下载URL
    print("\n[步骤1] 获取浏览器下载信息...")
    download_url, revision, platform = get_browser_download_url()
    print(f"版本: chromium-{revision}")
    print(f"平台: {platform}")
    print(f"下载URL: {download_url}")
    
    # 下载ZIP文件
    zip_file = os.path.join(current_dir, f'chromium-{platform}.zip')
    print("\n[步骤2] 下载浏览器ZIP文件...")
    if not download_file(download_url, zip_file, "浏览器ZIP文件"):
        print("\n[ERROR] 下载失败")
        return
    
    # 解压ZIP文件
    print("\n[步骤3] 解压浏览器文件...")
    temp_extract = os.path.join(current_dir, 'temp_chromium_extract')
    if os.path.exists(temp_extract):
        shutil.rmtree(temp_extract, ignore_errors=True)
    
    if not extract_zip(zip_file, temp_extract):
        print("\n[ERROR] 解压失败")
        return
    
    # 移动文件到google_web目录
    print("\n[步骤4] 移动文件到google_web目录...")
    try:
        # 查找解压后的chromium目录
        extracted_dirs = [d for d in os.listdir(temp_extract) if os.path.isdir(os.path.join(temp_extract, d))]
        chromium_dir = None
        for d in extracted_dirs:
            if 'chromium' in d.lower() or 'chrome' in d.lower():
                chromium_dir = os.path.join(temp_extract, d)
                break
        
        if not chromium_dir:
            chromium_dir = temp_extract
        
        # 创建google_web目录
        if os.path.exists(google_web_dir):
            shutil.rmtree(google_web_dir, ignore_errors=True)
        os.makedirs(google_web_dir, exist_ok=True)
        
        # 移动所有文件
        print(f"[移动] 从 {chromium_dir} 到 {google_web_dir}")
        if os.path.exists(chromium_dir):
            for item in os.listdir(chromium_dir):
                src = os.path.join(chromium_dir, item)
                dst = os.path.join(google_web_dir, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            print("[OK] 文件移动完成")
        else:
            print(f"[WARN] 未找到chromium目录: {chromium_dir}")
            # 直接复制整个目录
            shutil.copytree(temp_extract, google_web_dir)
        
        # 清理临时文件
        print("\n[清理] 删除临时文件...")
        try:
            shutil.rmtree(temp_extract, ignore_errors=True)
            os.remove(zip_file)
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
    if os.path.exists(chrome_exe):
        file_size = os.path.getsize(chrome_exe) / (1024 * 1024)
        print(f"[OK] 浏览器文件存在")
        print(f"[OK] 文件大小: {file_size:.1f} MB")
        
        # 测试启动
        try:
            print("\n[测试] 测试浏览器启动...")
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, executable_path=chrome_exe)
                browser.close()
            print("[OK] 浏览器启动测试成功！")
            print("\n" + "=" * 60)
            print("✓✓✓ 安装完成！浏览器已可以使用。")
            print(f"浏览器路径: {chrome_exe}")
            print("=" * 60)
        except Exception as e:
            print(f"[WARN] 浏览器启动测试失败: {e}")
            print("[INFO] 文件已安装，但启动测试失败")
    else:
        print(f"[ERROR] 浏览器文件不存在: {chrome_exe}")

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

