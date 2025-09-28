#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辅助工具函数
"""

import os
import sys
import platform
import threading
import time
from typing import Tuple, List, Optional, Callable, Any
from functools import wraps
import tkinter as tk
from tkinter import messagebox


def get_system_info() -> dict:
    """获取系统信息"""
    return {
        'platform': platform.platform(),
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
        'python_implementation': platform.python_implementation()
    }


def is_macos() -> bool:
    """检查是否为macOS系统"""
    return platform.system() == 'Darwin'


def is_windows() -> bool:
    """检查是否为Windows系统"""
    return platform.system() == 'Windows'


def is_linux() -> bool:
    """检查是否为Linux系统"""
    return platform.system() == 'Linux'


def get_app_data_dir() -> str:
    """获取应用数据目录"""
    if is_macos():
        return os.path.expanduser("~/Library/Application Support/WatermarkApp")
    elif is_windows():
        return os.path.join(os.environ.get('APPDATA', ''), 'WatermarkApp')
    else:  # Linux
        return os.path.expanduser("~/.watermark_app")


def get_system_font_dirs() -> List[str]:
    """获取系统字体目录列表"""
    font_dirs = []
    
    if is_macos():
        font_dirs.extend([
            "/System/Library/Fonts",
            "/Library/Fonts",
            os.path.expanduser("~/Library/Fonts")
        ])
    elif is_windows():
        font_dirs.extend([
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Microsoft', 'Windows', 'Fonts')
        ])
    else:  # Linux
        font_dirs.extend([
            "/usr/share/fonts",
            "/usr/local/share/fonts",
            os.path.expanduser("~/.fonts"),
            os.path.expanduser("~/.local/share/fonts")
        ])
    
    # 过滤存在的目录
    return [d for d in font_dirs if os.path.exists(d)]


def open_file_manager(path: str) -> bool:
    """跨平台打开文件管理器"""
    try:
        if not os.path.exists(path):
            return False
            
        if is_macos():
            os.system(f"open '{path}'")
        elif is_windows():
            os.startfile(path)
        else:  # Linux
            # 尝试多种Linux文件管理器
            for cmd in ['xdg-open', 'nautilus', 'dolphin', 'thunar', 'pcmanfm']:
                try:
                    os.system(f"{cmd} '{path}' 2>/dev/null &")
                    break
                except:
                    continue
        return True
    except Exception as e:
        print(f"打开文件管理器失败: {e}")
        return False


def get_default_fonts() -> List[str]:
    """获取系统默认字体列表"""
    fonts = []
    
    if is_macos():
        fonts.extend([
            "PingFang SC",  # 苹方
            "Hiragino Sans GB",  # 冬青黑体
            "STHeiti",  # 华文黑体
            "Arial Unicode MS",
            "Helvetica",
            "Arial"
        ])
    elif is_windows():
        fonts.extend([
            "Microsoft YaHei",  # 微软雅黑
            "SimHei",  # 黑体
            "SimSun",  # 宋体
            "Arial Unicode MS",
            "Arial",
            "Calibri"
        ])
    else:  # Linux
        fonts.extend([
            "Noto Sans CJK SC",  # 思源黑体
            "WenQuanYi Micro Hei",  # 文泉驿微米黑
            "DejaVu Sans",
            "Liberation Sans",
            "Arial",
            "Helvetica"
        ])
    
    return fonts


def is_arm_architecture() -> bool:
    """检查是否为ARM架构（如Apple M1/M2）"""
    machine = platform.machine().lower()
    return machine in ['arm64', 'aarch64', 'armv7l', 'armv8']


def get_python_architecture() -> str:
    """获取Python架构信息"""
    import struct
    return f"{platform.machine()}-{struct.calcsize('P') * 8}bit"


def ensure_dir_exists(dir_path: str) -> bool:
    """确保目录存在"""
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"创建目录失败 {dir_path}: {e}")
        return False


def safe_file_name(filename: str) -> str:
    """生成安全的文件名"""
    # 移除或替换不安全的字符
    unsafe_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    
    # 移除前后空格和点
    safe_name = safe_name.strip(' .')
    
    # 确保不为空
    if not safe_name:
        safe_name = 'untitled'
    
    return safe_name


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"


def format_duration(seconds: float) -> str:
    """格式化时间长度"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def clamp(value: float, min_val: float, max_val: float) -> float:
    """限制数值在指定范围内"""
    return max(min_val, min(value, max_val))


def lerp(start: float, end: float, t: float) -> float:
    """线性插值"""
    return start + (end - start) * clamp(t, 0.0, 1.0)


def color_to_hex(color: Tuple[int, int, int]) -> str:
    """将RGB颜色转换为十六进制字符串"""
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"


def hex_to_color(hex_color: str) -> Tuple[int, int, int]:
    """将十六进制颜色字符串转换为RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgba_to_hex(color: Tuple[int, int, int, int]) -> str:
    """将RGBA颜色转换为十六进制字符串"""
    return f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}{color[3]:02x}"


def hex_to_rgba(hex_color: str) -> Tuple[int, int, int, int]:
    """将十六进制颜色字符串转换为RGBA"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 6:
        # RGB格式，添加完全不透明的alpha
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    elif len(hex_color) == 8:
        # RGBA格式
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
    else:
        raise ValueError(f"无效的十六进制颜色格式: {hex_color}")


def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: Tuple = (Exception,)):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    else:
                        raise last_exception
            
            return None
        return wrapper
    return decorator


def threaded(func):
    """线程装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()
        return thread
    return wrapper


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total: int, callback: Callable[[float, int, int], None] = None):
        self.total = total
        self.current = 0
        self.callback = callback
        self.start_time = time.time()
    
    def update(self, increment: int = 1):
        """更新进度"""
        self.current += increment
        if self.callback:
            progress = (self.current / self.total) * 100 if self.total > 0 else 0
            self.callback(progress, self.current, self.total)
    
    def set_progress(self, current: int):
        """设置当前进度"""
        self.current = current
        if self.callback:
            progress = (self.current / self.total) * 100 if self.total > 0 else 0
            self.callback(progress, self.current, self.total)
    
    def get_progress(self) -> float:
        """获取进度百分比"""
        return (self.current / self.total) * 100 if self.total > 0 else 0
    
    def get_elapsed_time(self) -> float:
        """获取已用时间"""
        return time.time() - self.start_time
    
    def get_estimated_time(self) -> float:
        """获取预估总时间"""
        elapsed = self.get_elapsed_time()
        if self.current > 0:
            return elapsed * self.total / self.current
        return 0
    
    def get_remaining_time(self) -> float:
        """获取剩余时间"""
        return max(0, self.get_estimated_time() - self.get_elapsed_time())


class Timer:
    """计时器"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """开始计时"""
        self.start_time = time.time()
        self.end_time = None
    
    def stop(self):
        """停止计时"""
        self.end_time = time.time()
    
    def elapsed(self) -> float:
        """获取已用时间"""
        if self.start_time is None:
            return 0
        
        end_time = self.end_time or time.time()
        return end_time - self.start_time
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def show_error(title: str, message: str, parent=None):
    """显示错误对话框"""
    try:
        messagebox.showerror(title, message, parent=parent)
    except Exception as e:
        print(f"显示错误对话框失败: {e}")
        print(f"错误: {title} - {message}")


def show_warning(title: str, message: str, parent=None):
    """显示警告对话框"""
    try:
        messagebox.showwarning(title, message, parent=parent)
    except Exception as e:
        print(f"显示警告对话框失败: {e}")
        print(f"警告: {title} - {message}")


def show_info(title: str, message: str, parent=None):
    """显示信息对话框"""
    try:
        messagebox.showinfo(title, message, parent=parent)
    except Exception as e:
        print(f"显示信息对话框失败: {e}")
        print(f"信息: {title} - {message}")


def ask_yes_no(title: str, message: str, parent=None) -> bool:
    """显示是否确认对话框"""
    try:
        return messagebox.askyesno(title, message, parent=parent)
    except Exception as e:
        print(f"显示确认对话框失败: {e}")
        return False


def center_window(window: tk.Tk, width: int = None, height: int = None):
    """居中显示窗口"""
    try:
        # 更新窗口以获取实际尺寸
        window.update_idletasks()
        
        # 获取窗口尺寸
        if width is None:
            width = window.winfo_width()
        if height is None:
            height = window.winfo_height()
        
        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # 计算居中位置
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        # 设置窗口位置
        window.geometry(f"{width}x{height}+{x}+{y}")
    
    except Exception as e:
        print(f"居中窗口失败: {e}")


def validate_color(color) -> bool:
    """验证颜色值"""
    try:
        if isinstance(color, str):
            # 十六进制颜色
            if color.startswith('#'):
                hex_color = color[1:]
                if len(hex_color) in [3, 6, 8]:
                    int(hex_color, 16)
                    return True
        elif isinstance(color, (tuple, list)):
            # RGB或RGBA颜色
            if len(color) in [3, 4]:
                return all(isinstance(c, int) and 0 <= c <= 255 for c in color)
        
        return False
    except (ValueError, TypeError):
        return False


def get_resource_path(relative_path: str) -> str:
    """获取资源文件路径（支持打包后的应用）"""
    try:
        # PyInstaller创建的临时文件夹
        base_path = sys._MEIPASS
    except AttributeError:
        # 开发环境
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def load_icon(icon_name: str, size: Tuple[int, int] = None) -> Optional[tk.PhotoImage]:
    """加载图标"""
    try:
        icon_path = get_resource_path(f"assets/icons/{icon_name}")
        
        if os.path.exists(icon_path):
            if size:
                # 如果需要调整大小，这里可以使用PIL
                from PIL import Image, ImageTk
                img = Image.open(icon_path)
                img = img.resize(size, Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            else:
                return tk.PhotoImage(file=icon_path)
    except Exception as e:
        print(f"加载图标失败 {icon_name}: {e}")
    
    return None


def create_tooltip(widget: tk.Widget, text: str):
    """创建工具提示"""
    try:
        from tkinter import Toplevel, Label
        
        def show_tooltip(event):
            tooltip = Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = Label(tooltip, text=text, background="lightyellow", 
                         relief="solid", borderwidth=1, font=("Arial", 9))
            label.pack()
            
            def hide_tooltip():
                tooltip.destroy()
            
            tooltip.after(3000, hide_tooltip)  # 3秒后自动隐藏
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                delattr(widget, 'tooltip')
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    except Exception as e:
        print(f"创建工具提示失败: {e}")


def debounce(wait_time: float):
    """防抖装饰器"""
    def decorator(func):
        timer = None
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal timer
            
            def call_func():
                func(*args, **kwargs)
            
            if timer:
                timer.cancel()
            
            timer = threading.Timer(wait_time, call_func)
            timer.start()
        
        return wrapper
    return decorator


def throttle(wait_time: float):
    """节流装饰器"""
    def decorator(func):
        last_called = [0]
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            if now - last_called[0] >= wait_time:
                last_called[0] = now
                return func(*args, **kwargs)
        
        return wrapper
    return decorator