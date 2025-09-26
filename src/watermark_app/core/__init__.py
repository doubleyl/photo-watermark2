#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心模块初始化
"""

from .image_processor import ImageProcessor
from .watermark_manager import WatermarkManager, WatermarkPosition, WatermarkType
from .file_manager import FileManager

__all__ = [
    'ImageProcessor',
    'WatermarkManager', 
    'WatermarkPosition',
    'WatermarkType',
    'FileManager'
]