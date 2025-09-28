#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跨平台字体管理器
"""

import os
import glob
from typing import Dict, List, Optional, Tuple
from PIL import ImageFont
from .helpers import (
    is_macos, is_windows, is_linux, 
    get_system_font_dirs, get_default_fonts
)


class FontManager:
    """跨平台字体管理器"""
    
    def __init__(self):
        """初始化字体管理器"""
        self._font_cache = {}
        self._available_fonts = None
        self._font_paths = {}
    
    def get_available_fonts(self) -> Dict[str, str]:
        """获取可用字体列表，返回字体名称和路径的字典"""
        if self._available_fonts is None:
            self._scan_system_fonts()
        return self._available_fonts.copy()
    
    def _scan_system_fonts(self):
        """扫描系统字体"""
        self._available_fonts = {}
        self._font_paths = {}
        
        # 获取系统字体目录
        font_dirs = get_system_font_dirs()
        
        # 扫描字体文件
        for font_dir in font_dirs:
            self._scan_font_directory(font_dir)
        
        # 添加预定义的常用字体
        self._add_predefined_fonts()
        
        # 如果没有找到任何字体，添加默认选项
        if not self._available_fonts:
            self._available_fonts["系统默认"] = "default"
    
    def _scan_font_directory(self, font_dir: str):
        """扫描字体目录"""
        if not os.path.exists(font_dir):
            return
        
        # 支持的字体文件扩展名
        font_extensions = ['*.ttf', '*.otf', '*.ttc', '*.woff', '*.woff2']
        
        try:
            for ext in font_extensions:
                pattern = os.path.join(font_dir, '**', ext)
                for font_path in glob.glob(pattern, recursive=True):
                    try:
                        font_name = self._extract_font_name(font_path)
                        if font_name:
                            self._available_fonts[font_name] = font_path
                            self._font_paths[font_name] = font_path
                    except Exception:
                        continue
        except Exception:
            pass
    
    def _extract_font_name(self, font_path: str) -> Optional[str]:
        """从字体文件路径提取字体名称"""
        try:
            # 简单的名称提取：使用文件名（去掉扩展名）
            base_name = os.path.splitext(os.path.basename(font_path))[0]
            
            # 清理名称
            name = base_name.replace('_', ' ').replace('-', ' ')
            
            # 特殊处理一些常见的字体名称
            name_mappings = {
                'PingFang': 'PingFang SC',
                'STHeiti': 'STHeiti',
                'Hiragino Sans GB': 'Hiragino Sans GB',
                'Microsoft YaHei': 'Microsoft YaHei',
                'SimHei': 'SimHei',
                'SimSun': 'SimSun',
                'Noto Sans CJK SC': 'Noto Sans CJK SC',
                'WenQuanYi Micro Hei': 'WenQuanYi Micro Hei'
            }
            
            for key, value in name_mappings.items():
                if key.lower() in name.lower():
                    return value
            
            return name
        except Exception:
            return None
    
    def _add_predefined_fonts(self):
        """添加预定义的常用字体"""
        predefined_fonts = {}
        
        if is_macos():
            predefined_fonts = {
                "苹方 (PingFang SC)": "/System/Library/Fonts/PingFang.ttc",
                "华文黑体 (STHeiti)": "/System/Library/Fonts/STHeiti Light.ttc",
                "冬青黑体 (Hiragino Sans GB)": "/System/Library/Fonts/Hiragino Sans GB.ttc",
                "Arial Unicode MS": "/System/Library/Fonts/Arial Unicode MS.ttf",
                "Helvetica": "/System/Library/Fonts/Helvetica.ttc",
                "Arial": "/System/Library/Fonts/Arial.ttf",
                "Times New Roman": "/System/Library/Fonts/Times New Roman.ttf",
                "Courier New": "/System/Library/Fonts/Courier New.ttf"
            }
        elif is_windows():
            windows_fonts_dir = os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Fonts')
            predefined_fonts = {
                "微软雅黑 (Microsoft YaHei)": os.path.join(windows_fonts_dir, "msyh.ttc"),
                "黑体 (SimHei)": os.path.join(windows_fonts_dir, "simhei.ttf"),
                "宋体 (SimSun)": os.path.join(windows_fonts_dir, "simsun.ttc"),
                "Arial Unicode MS": os.path.join(windows_fonts_dir, "ARIALUNI.TTF"),
                "Arial": os.path.join(windows_fonts_dir, "arial.ttf"),
                "Calibri": os.path.join(windows_fonts_dir, "calibri.ttf"),
                "Times New Roman": os.path.join(windows_fonts_dir, "times.ttf")
            }
        else:  # Linux
            predefined_fonts = {
                "思源黑体 (Noto Sans CJK SC)": "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "文泉驿微米黑 (WenQuanYi Micro Hei)": "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "DejaVu Sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "Liberation Sans": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                "Ubuntu": "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf"
            }
        
        # 检查预定义字体是否存在
        for name, path in predefined_fonts.items():
            if os.path.exists(path) and name not in self._available_fonts:
                self._available_fonts[name] = path
                self._font_paths[name] = path
    
    def get_font(self, font_name: str, size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
        """获取字体对象"""
        cache_key = (font_name, size, bold, italic)
        
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]
        
        font = self._load_font(font_name, size, bold, italic)
        self._font_cache[cache_key] = font
        return font
    
    def _load_font(self, font_name: str, size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
        """加载字体"""
        # 如果指定了具体字体名称，尝试加载
        if font_name and font_name != "系统默认":
            font_path = self._find_font_path(font_name)
            if font_path:
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    pass
        
        # 尝试加载系统默认字体
        default_fonts = get_default_fonts()
        for font_name in default_fonts:
            font_path = self._find_font_path(font_name)
            if font_path:
                try:
                    return ImageFont.truetype(font_path, size)
                except Exception:
                    continue
        
        # 最后的备选方案：PIL默认字体
        try:
            return ImageFont.load_default()
        except Exception:
            # 如果连默认字体都加载失败，创建一个基本字体
            return ImageFont.load_default()
    
    def _find_font_path(self, font_name: str) -> Optional[str]:
        """查找字体路径"""
        if self._available_fonts is None:
            self._scan_system_fonts()
        
        # 精确匹配
        if font_name in self._font_paths:
            return self._font_paths[font_name]
        
        # 模糊匹配
        font_name_lower = font_name.lower()
        for name, path in self._font_paths.items():
            if font_name_lower in name.lower() or name.lower() in font_name_lower:
                return path
        
        return None
    
    def get_font_info(self, font_name: str) -> Optional[Dict]:
        """获取字体信息"""
        font_path = self._find_font_path(font_name)
        if not font_path or not os.path.exists(font_path):
            return None
        
        try:
            stat = os.stat(font_path)
            return {
                'name': font_name,
                'path': font_path,
                'size': stat.st_size,
                'exists': True
            }
        except Exception:
            return None
    
    def clear_cache(self):
        """清空字体缓存"""
        self._font_cache.clear()
    
    def refresh_fonts(self):
        """刷新字体列表"""
        self._available_fonts = None
        self._font_paths.clear()
        self.clear_cache()


# 全局字体管理器实例
_font_manager = None

def get_font_manager() -> FontManager:
    """获取全局字体管理器实例"""
    global _font_manager
    if _font_manager is None:
        _font_manager = FontManager()
    return _font_manager