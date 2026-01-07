#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包脚本 - 将客户端打包为exe文件
"""
import os
import sys
import subprocess
import shutil

def safe_print(*args, **kwargs):
    """安全的打印函数，处理编码问题"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # 如果编码失败，尝试使用ASCII
        try:
            encoded_args = [str(arg).encode('ascii', 'replace').decode('ascii') for arg in args]
            print(*encoded_args, **kwargs)
        except:
            print("[打印错误: 无法编码内容]")

def check_dependencies():
    """检查必要的依赖"""
    safe_print("检查依赖...")
    try:
        import PyInstaller
        safe_print(f"[OK] PyInstaller已安装: {PyInstaller.__version__}")
    except ImportError:
        safe_print("[INFO] PyInstaller未安装，正在安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        safe_print("[OK] PyInstaller安装完成")
    
    try:
        import PyQt5
        safe_print("[OK] PyQt5已安装")
    except ImportError:
        safe_print("[ERROR] PyQt5未安装，请先安装: pip install PyQt5")
        return False
    
    try:
        import playwright
        safe_print("[OK] Playwright已安装")
    except ImportError:
        safe_print("[ERROR] Playwright未安装，请先安装: pip install playwright")
        return False
    
    return True

def clean_build():
    """清理之前的构建文件"""
    safe_print("\n清理之前的构建文件...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            safe_print(f"[OK] 已删除: {dir_name}")
    
    # 清理spec文件生成的临时文件
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            shutil.rmtree(os.path.join(root, '__pycache__'))
    
    safe_print("[OK] 清理完成")

def build_exe():
    """执行打包"""
    safe_print("\n开始打包...")
    spec_file = 'build_exe.spec'
    
    if not os.path.exists(spec_file):
        safe_print(f"[ERROR] 找不到spec文件: {spec_file}")
        return False
    
    try:
        # 运行PyInstaller
        cmd = [sys.executable, "-m", "PyInstaller", spec_file, "--clean", "--noconfirm"]
        safe_print(f"执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, cwd=os.path.dirname(os.path.abspath(__file__)))
        
        safe_print("\n[OK] 打包完成！")
        safe_print("\n输出文件位置:")
        exe_path = os.path.join('dist', 'BNSJ客户端.exe')
        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
            safe_print(f"  {exe_path} ({size:.2f} MB)")
        else:
            safe_print(f"  {exe_path} (未找到)")
        
        return True
    except subprocess.CalledProcessError as e:
        safe_print(f"\n[ERROR] 打包失败: {e}")
        return False
    except Exception as e:
        safe_print(f"\n[ERROR] 打包出错: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("BNSJ客户端打包工具")
    print("=" * 60)
    
    # 切换到脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"\n工作目录: {os.getcwd()}")
    
    # 检查依赖
    if not check_dependencies():
        safe_print("\n[ERROR] 依赖检查失败，请先安装必要的依赖")
        sys.exit(1)
    
    # 清理
    clean_build()
    
    # 打包
    if build_exe():
        safe_print("\n" + "=" * 60)
        safe_print("打包成功！")
        safe_print("=" * 60)
        safe_print("\n提示:")
        safe_print("1. exe文件位于 dist/BNSJ客户端.exe")
        safe_print("2. 首次运行可能需要一些时间解压文件")
        safe_print("3. google_web目录已打包进exe，会自动解压到exe同级目录")
        safe_print("4. 如果遇到问题，可以修改build_exe.spec中的console=True查看错误信息")
    else:
        safe_print("\n" + "=" * 60)
        safe_print("打包失败！")
        safe_print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()

