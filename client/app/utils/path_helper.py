"""
路径辅助工具 - 处理打包后的路径问题
"""
import os
import sys

def get_client_dir():
    """
    获取client目录路径
    在打包后的exe中，返回exe文件所在目录
    在开发环境中，返回client目录
    """
    if getattr(sys, 'frozen', False):
        # 打包后的exe环境
        # sys.executable是exe文件的路径
        return os.path.dirname(sys.executable)
    else:
        # 开发环境
        # 获取client目录
        # 这个文件在 app/utils/path_helper.py
        # 所以需要向上两级到client目录
        current_file = os.path.abspath(__file__)
        utils_dir = os.path.dirname(current_file)
        app_dir = os.path.dirname(utils_dir)
        client_dir = os.path.dirname(app_dir)
        return client_dir

def get_google_web_dir():
    """获取google_web目录路径"""
    return os.path.join(get_client_dir(), 'google_web')

def get_logs_dir():
    """获取logs目录路径"""
    return os.path.join(get_client_dir(), 'logs')

