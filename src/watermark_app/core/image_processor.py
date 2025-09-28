#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片处理核心模块
"""

import os
from typing import List, Tuple, Optional, Union
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import numpy as np
from ..utils.logger import get_logger, get_error_handler, log_errors


class ImageProcessor:
    """图片处理器类"""
    
    # 支持的图片格式
    SUPPORTED_FORMATS = {
        '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'
    }
    
    def __init__(self):
        """初始化图片处理器"""
        self.current_image = None
        self.original_image = None
        self.logger = get_logger("image_processor")
        self.error_handler = get_error_handler()
    
    def is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_FORMATS
    
    @log_errors
    def load_image(self, file_path: str) -> bool:
        """加载图片文件"""
        try:
            self.logger.info(f"开始加载图片: {file_path}")
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            if not self.is_supported_format(file_path):
                raise ValueError(f"不支持的文件格式: {file_path}")
            
            # 打开图片
            self.original_image = Image.open(file_path)
            self.current_image = self.original_image.copy()
            
            self.logger.info(f"成功加载图片: {file_path}, 尺寸: {self.original_image.size}")
            return True
            
        except Exception as e:
            self.error_handler.handle_image_error(file_path, "加载", e)
            return False
    
    def get_image_info(self, file_path: str) -> Optional[dict]:
        """获取图片信息"""
        try:
            with Image.open(file_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'mode': img.mode,
                    'format': img.format,
                    'size_bytes': os.path.getsize(file_path),
                    'has_transparency': img.mode in ('RGBA', 'LA') or 'transparency' in img.info
                }
        except Exception as e:
            print(f"获取图片信息失败 {file_path}: {e}")
            return None
    
    def create_thumbnail(self, file_path: str, size: Tuple[int, int] = (100, 100)) -> Optional[Image.Image]:
        """创建缩略图"""
        try:
            with Image.open(file_path) as img:
                # 创建缩略图
                img.thumbnail(size, Image.Resampling.LANCZOS)
                return img.copy()
        except Exception as e:
            print(f"创建缩略图失败 {file_path}: {e}")
            return None
    
    def resize_image(self, img: Image.Image, target_size: Tuple[int, int], 
                    keep_aspect: bool = True) -> Image.Image:
        """调整图片尺寸"""
        if not keep_aspect:
            return img.resize(target_size, Image.Resampling.LANCZOS)
        
        # 保持宽高比
        original_width, original_height = img.size
        target_width, target_height = target_size
        
        # 计算缩放比例
        ratio_w = target_width / original_width
        ratio_h = target_height / original_height
        ratio = min(ratio_w, ratio_h)
        
        # 计算新尺寸
        new_width = int(original_width * ratio)
        new_height = int(original_height * ratio)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def convert_format(self, img: Image.Image, target_format: str) -> Image.Image:
        """转换图片格式"""
        if target_format.upper() == 'JPEG':
            # JPEG不支持透明度，需要转换为RGB
            if img.mode in ('RGBA', 'LA'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])
                else:
                    background.paste(img, mask=img.split()[-1])
                return background
            elif img.mode != 'RGB':
                return img.convert('RGB')
        elif target_format.upper() == 'PNG':
            # PNG支持透明度
            if img.mode not in ('RGBA', 'RGB'):
                return img.convert('RGBA')
        
        return img
    
    def adjust_quality(self, img: Image.Image, quality: int) -> Image.Image:
        """调整图片质量（主要用于JPEG）"""
        if quality < 0 or quality > 100:
            raise ValueError("质量值必须在0-100之间")
        
        # 通过调整图片的锐度和对比度来模拟质量调整
        if quality < 50:
            # 低质量：降低锐度
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(0.5)
        elif quality > 90:
            # 高质量：增强锐度
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.2)
        
        return img
    
    def validate_image_file(self, file_path: str) -> Tuple[bool, str]:
        """验证图片文件"""
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                return False, "文件不存在"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return False, "文件为空"
            
            # 检查文件格式
            if not self.is_supported_format(file_path):
                return False, "不支持的文件格式"
            
            # 尝试打开图片
            with Image.open(file_path) as img:
                # 检查图片尺寸
                if img.width == 0 or img.height == 0:
                    return False, "图片尺寸无效"
                
                # 检查图片是否过大
                if img.width > 10000 or img.height > 10000:
                    return False, "图片尺寸过大"
                
                # 验证图片数据
                img.verify()
            
            return True, "验证通过"
            
        except Exception as e:
            return False, f"验证失败: {e}"
    
    def batch_validate_images(self, file_paths: List[str]) -> List[Tuple[str, bool, str]]:
        """批量验证图片文件"""
        results = []
        for file_path in file_paths:
            is_valid, message = self.validate_image_file(file_path)
            results.append((file_path, is_valid, message))
        return results
    
    def get_supported_formats_filter(self) -> List[Tuple[str, str]]:
        """获取文件对话框的格式过滤器"""
        return [
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("PNG文件", "*.png"),
            ("BMP文件", "*.bmp"),
            ("TIFF文件", "*.tiff *.tif"),
            ("所有文件", "*.*")
        ]
    
    def scan_folder_for_images(self, folder_path: str, recursive: bool = True) -> List[str]:
        """扫描文件夹中的图片文件"""
        image_files = []
        
        try:
            if recursive:
                # 递归扫描
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.is_supported_format(file_path):
                            image_files.append(file_path)
            else:
                # 只扫描当前文件夹
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file)
                    if os.path.isfile(file_path) and self.is_supported_format(file_path):
                        image_files.append(file_path)
        
        except Exception as e:
            print(f"扫描文件夹失败 {folder_path}: {e}")
        
        return sorted(image_files)
    
    def calculate_optimal_size(self, original_size: Tuple[int, int], 
                             max_size: Tuple[int, int]) -> Tuple[int, int]:
        """计算最优显示尺寸"""
        orig_width, orig_height = original_size
        max_width, max_height = max_size
        
        # 计算缩放比例
        ratio_w = max_width / orig_width
        ratio_h = max_height / orig_height
        ratio = min(ratio_w, ratio_h, 1.0)  # 不放大
        
        # 计算新尺寸
        new_width = int(orig_width * ratio)
        new_height = int(orig_height * ratio)
        
        return new_width, new_height
    
    def create_preview_image(self, img: Image.Image, max_size: Tuple[int, int] = (800, 600)) -> Image.Image:
        """创建预览图片"""
        # 计算预览尺寸
        preview_size = self.calculate_optimal_size(img.size, max_size)
        
        # 调整尺寸
        preview_img = img.resize(preview_size, Image.Resampling.LANCZOS)
        
        return preview_img
    
    @log_errors
    def save_image(self, img: Image.Image, output_path: str, 
                  format_type: str = None, quality: int = 95, **kwargs) -> bool:
        """保存图片"""
        try:
            self.logger.info(f"开始保存图片: {output_path}")
            
            # 确定输出格式
            if format_type is None:
                ext = os.path.splitext(output_path)[1].lower()
                if ext in ['.jpg', '.jpeg']:
                    format_type = 'JPEG'
                elif ext == '.png':
                    format_type = 'PNG'
                elif ext == '.bmp':
                    format_type = 'BMP'
                elif ext in ['.tiff', '.tif']:
                    format_type = 'TIFF'
                else:
                    format_type = 'PNG'  # 默认格式
            
            self.logger.debug(f"使用格式: {format_type}, 质量: {quality}")
            
            # 转换图片格式
            save_img = self.convert_format(img, format_type)
            
            # 准备保存参数
            save_kwargs = kwargs.copy()
            
            if format_type == 'JPEG':
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif format_type == 'PNG':
                save_kwargs['optimize'] = True
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self.logger.debug(f"创建输出目录: {output_dir}")
            
            # 保存图片
            save_img.save(output_path, format=format_type, **save_kwargs)
            
            self.logger.info(f"成功保存图片: {output_path}")
            return True
            
        except Exception as e:
            self.error_handler.handle_file_error(output_path, "保存图片", e)
            return False