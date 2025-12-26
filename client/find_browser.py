"""查找Playwright浏览器位置"""
import os
import glob

def find_browser():
    """查找浏览器可执行文件"""
    paths = []
    
    # 检查常见的Playwright安装位置
    local_appdata = os.environ.get('LOCALAPPDATA', '')
    user_home = os.path.expanduser('~')
    
    search_dirs = []
    if local_appdata:
        search_dirs.append(os.path.join(local_appdata, 'ms-playwright'))
    if user_home:
        search_dirs.append(os.path.join(user_home, 'AppData', 'Local', 'ms-playwright'))
        search_dirs.append(os.path.join(user_home, '.cache', 'ms-playwright'))
    
    # 递归搜索chrome.exe
    for search_dir in search_dirs:
        if os.path.exists(search_dir):
            pattern = os.path.join(search_dir, '**', 'chrome.exe')
            found = glob.glob(pattern, recursive=True)
            paths.extend(found)
    
    # 也检查项目目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_patterns = [
        os.path.join(current_dir, '**', 'chrome.exe'),
        os.path.join(current_dir, '**', 'chromium', '**', 'chrome.exe'),
    ]
    for pattern in project_patterns:
        found = glob.glob(pattern, recursive=True)
        paths.extend(found)
    
    return paths

if __name__ == '__main__':
    print("正在查找Playwright浏览器...")
    paths = find_browser()
    if paths:
        print(f"\n找到 {len(paths)} 个浏览器文件:")
        for path in paths:
            print(f"  {path}")
            if os.path.exists(path):
                size = os.path.getsize(path) / (1024 * 1024)
                print(f"    大小: {size:.1f} MB")
    else:
        print("\n未找到浏览器文件")
        print("\n请检查以下位置:")
        local_appdata = os.environ.get('LOCALAPPDATA', '')
        user_home = os.path.expanduser('~')
        print(f"  {os.path.join(local_appdata, 'ms-playwright')}")
        print(f"  {os.path.join(user_home, 'AppData', 'Local', 'ms-playwright')}")
        print(f"  {os.path.join(user_home, '.cache', 'ms-playwright')}")

