"""
PyInstaller运行时Hook - 处理打包后的路径问题
"""
import os
import sys

def get_base_path():
    """
    获取应用程序基础路径
    在打包后的exe中，sys.executable指向exe文件路径
    在开发环境中，返回client目录
    """
    if getattr(sys, 'frozen', False):
        # 打包后的exe环境
        # sys.executable是exe文件的路径
        # PyInstaller会将数据文件解压到临时目录，我们需要找到exe所在目录
        if hasattr(sys, '_MEIPASS'):
            # PyInstaller创建的临时目录（用于解压数据文件）
            # 但google_web会被解压到exe同级目录
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(sys.executable)
    else:
        # 开发环境
        # 获取client目录
        current_file = os.path.abspath(__file__)
        base_path = os.path.dirname(current_file)
    
    return base_path

# 设置环境变量，让应用程序知道基础路径
os.environ['APP_BASE_PATH'] = get_base_path()

# 在打包后的环境中，将google_web从临时目录解压到exe同级目录
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    import shutil
    
    # exe所在目录
    exe_dir = os.path.dirname(sys.executable)
    target_google_web = os.path.join(exe_dir, 'google_web')
    
    # 临时目录中的google_web
    source_google_web = os.path.join(sys._MEIPASS, 'google_web')
    
    # 如果临时目录中有google_web，但exe同级目录没有，则复制过去
    if os.path.exists(source_google_web) and not os.path.exists(target_google_web):
        try:
            # 复制整个目录
            shutil.copytree(source_google_web, target_google_web)
            # 设置环境变量
            os.environ['GOOGLE_WEB_PATH'] = target_google_web
        except Exception as e:
            # 如果复制失败，记录错误但不中断程序
            try:
                import traceback
                traceback.print_exc()
            except:
                pass
    elif os.path.exists(target_google_web):
        # 如果exe同级目录已经有google_web，直接使用
        os.environ['GOOGLE_WEB_PATH'] = target_google_web

# 设置Qt插件路径（如果PyQt5已导入）
# 必须在导入PyQt5之前设置，否则QApplication无法初始化
try:
    if getattr(sys, 'frozen', False):
        # 打包后的环境
        # PyInstaller会将数据文件解压到临时目录 _MEIPASS
        if hasattr(sys, '_MEIPASS'):
            # 插件被解压到 _MEIPASS/PyQt5/Qt5/plugins
            meipass_plugin_path = os.path.join(sys._MEIPASS, 'PyQt5', 'Qt5', 'plugins')
            if os.path.exists(meipass_plugin_path):
                platforms_path = os.path.join(meipass_plugin_path, 'platforms')
                if sys.platform == 'win32':
                    plugin_file = os.path.join(platforms_path, 'qwindows.dll')
                elif sys.platform == 'darwin':
                    plugin_file = os.path.join(platforms_path, 'qcocoa.dylib')
                else:
                    plugin_file = None
                
                if plugin_file and os.path.exists(plugin_file):
                    os.environ['QT_PLUGIN_PATH'] = meipass_plugin_path
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = meipass_plugin_path
                    # 使用QtCore.QCoreApplication.setLibraryPaths设置插件路径
                    # 但需要在导入QtCore之后设置
    else:
        # 开发环境
        import PyQt5
        from PyQt5 import QtCore
        
        qt_dir = os.path.dirname(QtCore.__file__)
        
        # 查找插件目录
        plugins_dir = None
        possible_plugin_paths = [
            os.path.join(qt_dir, 'Qt5', 'plugins'),
            os.path.join(qt_dir, 'plugins'),
        ]
        
        for path in possible_plugin_paths:
            if os.path.exists(path):
                platforms_path = os.path.join(path, 'platforms')
                if sys.platform == 'win32':
                    plugin_file = os.path.join(platforms_path, 'qwindows.dll')
                elif sys.platform == 'darwin':
                    plugin_file = os.path.join(platforms_path, 'qcocoa.dylib')
                else:
                    plugin_file = None
                
                if plugin_file and os.path.exists(plugin_file):
                    plugins_dir = path
                    break
        
        if plugins_dir:
            os.environ['QT_PLUGIN_PATH'] = plugins_dir
            os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_dir
except Exception as e:
    # 如果设置失败，记录错误但不中断程序
    try:
        import traceback
        traceback.print_exc()
    except:
        pass

