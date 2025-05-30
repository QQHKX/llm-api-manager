# -*- coding: utf-8 -*-
"""
辅助函数模块

包含项目中使用的各种辅助函数。
"""

import json
import os
import sys
import time
from datetime import datetime
from urllib.parse import urlparse


def clear_console():
    """
    清空控制台屏幕
    
    根据操作系统类型使用不同的命令清空控制台
    """
    if sys.platform.startswith('win'):
        os.system('cls')
    else:
        os.system('clear')


def extract_domain(url):
    """
    从URL中提取域名
    
    Args:
        url (str): 完整的URL
        
    Returns:
        str: 提取的域名
    """
    if not url:
        return ""
    
    # 确保URL有协议前缀
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed_url = urlparse(url)
    return parsed_url.netloc


def format_timestamp(timestamp=None):
    """
    格式化时间戳为ISO格式字符串
    
    Args:
        timestamp (float, optional): 时间戳，默认为当前时间
        
    Returns:
        str: ISO格式的时间字符串
    """
    if timestamp is None:
        timestamp = time.time()
    return datetime.fromtimestamp(timestamp).isoformat()


def generate_filename(prefix, extension, timestamp=None):
    """
    生成带有时间戳的文件名
    
    Args:
        prefix (str): 文件名前缀
        extension (str): 文件扩展名（不包含点）
        timestamp (float, optional): 时间戳，默认为当前时间
        
    Returns:
        str: 生成的文件名
    """
    if timestamp is None:
        timestamp = time.time()
    
    dt = datetime.fromtimestamp(timestamp)
    formatted_time = dt.strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{formatted_time}.{extension}"


def save_to_json(data, filepath):
    """
    将数据保存为JSON文件
    
    Args:
        data: 要保存的数据（字典或列表）
        filepath (str): 文件保存路径
        
    Returns:
        bool: 保存成功返回True，否则返回False
    """
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存JSON文件失败: {e}")
        return False


def load_from_json(filepath, default=None):
    """
    从JSON文件加载数据
    
    Args:
        filepath (str): 文件路径
        default: 文件不存在或加载失败时返回的默认值
        
    Returns:
        加载的数据或默认值
    """
    if not os.path.exists(filepath):
        return default
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载JSON文件失败: {e}")
        return default


def copy_to_clipboard(text):
    """
    将文本复制到剪贴板
    
    Args:
        text (str): 要复制的文本
        
    Returns:
        bool: 复制成功返回True，否则返回False
    """
    try:
        import pyperclip
        pyperclip.copy(text)
        return True
    except ImportError:
        print("未安装pyperclip库，无法复制到剪贴板。请使用pip install pyperclip安装。")
        return False
    except Exception as e:
        print(f"复制到剪贴板失败: {e}")
        return False


def create_progress_bar(current, total, width=50):
    """
    创建ASCII进度条
    
    Args:
        current (int): 当前进度
        total (int): 总进度
        width (int): 进度条宽度
        
    Returns:
        str: 格式化的进度条字符串
    """
    progress = min(1.0, current / total if total > 0 else 1.0)
    filled_width = int(width * progress)
    bar = '█' * filled_width + '░' * (width - filled_width)
    percentage = progress * 100
    return f"[{bar}] {percentage:.1f}% ({current}/{total})"