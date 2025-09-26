#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印管理核心模块
"""

import os
import math
from typing import Tuple, Optional, Union, Dict, Any, List
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from enum import Enum


class WatermarkPosition(Enum):
    """水印位置枚举"""
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"
    CUSTOM = "custom"


class WatermarkType(Enum):
    """水印类型枚举"""
    TEXT = "text"
    IMAGE = "image"


class WatermarkManager:
    """水印管理器类"""
    
    def __init__(self):
        """初始化水印管理器"""
        self.default_font_size = 24
        self.default_color = (255, 255, 255, 128)  # 白色半透明
        self.default_position = WatermarkPosition.BOTTOM_RIGHT
        self.margin = 20  # 边距
    
    def apply_text_watermark(self, img: Image.Image, text: str, 
                           font_size: int = None, color: Tuple[int, int, int, int] = None,
                           position: WatermarkPosition = None, 
                           offset: Tuple[int, int] = (0, 0),
                           rotation: float = 0, font_path: str = None) -> Image.Image:
        """应用文本水印"""
        if not text.strip():
            return img.copy()
        
        # 使用默认值
        font_size = font_size or self.default_font_size
        color = color or self.default_color
        position = position or self.default_position
        
        # 创建副本
        watermarked_img = img.copy()
        
        # 确保图片有透明度通道
        if watermarked_img.mode != 'RGBA':
            watermarked_img = watermarked_img.convert('RGBA')
        
        # 创建透明图层用于绘制水印
        overlay = Image.new('RGBA', watermarked_img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        
        try:
            # 加载字体
            if font_path and os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
            else:
                # 尝试使用系统默认字体
                try:
                    # macOS 系统字体
                    font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                    except:
                        # 使用PIL默认字体
                        font = ImageFont.load_default()
        except Exception as e:
            print(f"加载字体失败: {e}")
            font = ImageFont.load_default()
        
        # 获取文本尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # 计算水印位置
        x, y = self._calculate_position(
            watermarked_img.size, (text_width, text_height), position, offset
        )
        
        # 如果有旋转，创建旋转的文本图像
        if rotation != 0:
            # 创建文本图像
            text_img = Image.new('RGBA', (text_width + 20, text_height + 20), (255, 255, 255, 0))
            text_draw = ImageDraw.Draw(text_img)
            text_draw.text((10, 10), text, font=font, fill=color)
            
            # 旋转文本图像
            rotated_text = text_img.rotate(rotation, expand=True)
            
            # 调整位置以适应旋转后的尺寸
            rot_width, rot_height = rotated_text.size
            x = max(0, min(x - (rot_width - text_width) // 2, watermarked_img.width - rot_width))
            y = max(0, min(y - (rot_height - text_height) // 2, watermarked_img.height - rot_height))
            
            # 粘贴旋转的文本
            overlay.paste(rotated_text, (x, y), rotated_text)
        else:
            # 直接绘制文本
            draw.text((x, y), text, font=font, fill=color)
        
        # 合并图层
        watermarked_img = Image.alpha_composite(watermarked_img, overlay)
        
        return watermarked_img
    
    def apply_image_watermark(self, img: Image.Image, watermark_path: str,
                            scale: float = 1.0, opacity: float = 1.0,
                            position: WatermarkPosition = None,
                            offset: Tuple[int, int] = (0, 0),
                            rotation: float = 0) -> Image.Image:
        """应用图片水印"""
        if not os.path.exists(watermark_path):
            print(f"水印图片不存在: {watermark_path}")
            return img.copy()
        
        position = position or self.default_position
        
        try:
            # 加载水印图片
            watermark = Image.open(watermark_path)
            
            # 确保水印有透明度通道
            if watermark.mode != 'RGBA':
                watermark = watermark.convert('RGBA')
            
            # 调整水印尺寸
            if scale != 1.0:
                new_width = int(watermark.width * scale)
                new_height = int(watermark.height * scale)
                watermark = watermark.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 调整透明度
            if opacity != 1.0:
                # 创建透明度蒙版
                alpha = watermark.split()[-1]
                alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
                watermark.putalpha(alpha)
            
            # 旋转水印
            if rotation != 0:
                watermark = watermark.rotate(rotation, expand=True)
            
            # 创建副本
            watermarked_img = img.copy()
            if watermarked_img.mode != 'RGBA':
                watermarked_img = watermarked_img.convert('RGBA')
            
            # 计算水印位置
            x, y = self._calculate_position(
                watermarked_img.size, watermark.size, position, offset
            )
            
            # 确保水印在图片范围内
            x = max(0, min(x, watermarked_img.width - watermark.width))
            y = max(0, min(y, watermarked_img.height - watermark.height))
            
            # 粘贴水印
            watermarked_img.paste(watermark, (x, y), watermark)
            
            return watermarked_img
            
        except Exception as e:
            print(f"应用图片水印失败: {e}")
            return img.copy()
    
    def _calculate_position(self, img_size: Tuple[int, int], 
                          watermark_size: Tuple[int, int],
                          position: WatermarkPosition,
                          offset: Tuple[int, int] = (0, 0)) -> Tuple[int, int]:
        """计算水印位置"""
        img_width, img_height = img_size
        wm_width, wm_height = watermark_size
        offset_x, offset_y = offset
        
        # 基础位置计算
        if position == WatermarkPosition.TOP_LEFT:
            x, y = self.margin, self.margin
        elif position == WatermarkPosition.TOP_CENTER:
            x, y = (img_width - wm_width) // 2, self.margin
        elif position == WatermarkPosition.TOP_RIGHT:
            x, y = img_width - wm_width - self.margin, self.margin
        elif position == WatermarkPosition.CENTER_LEFT:
            x, y = self.margin, (img_height - wm_height) // 2
        elif position == WatermarkPosition.CENTER:
            x, y = (img_width - wm_width) // 2, (img_height - wm_height) // 2
        elif position == WatermarkPosition.CENTER_RIGHT:
            x, y = img_width - wm_width - self.margin, (img_height - wm_height) // 2
        elif position == WatermarkPosition.BOTTOM_LEFT:
            x, y = self.margin, img_height - wm_height - self.margin
        elif position == WatermarkPosition.BOTTOM_CENTER:
            x, y = (img_width - wm_width) // 2, img_height - wm_height - self.margin
        elif position == WatermarkPosition.BOTTOM_RIGHT:
            x, y = img_width - wm_width - self.margin, img_height - wm_height - self.margin
        else:  # CUSTOM
            x, y = offset_x, offset_y
            return x, y
        
        # 应用偏移
        x += offset_x
        y += offset_y
        
        return x, y
    
    def get_position_name(self, position: WatermarkPosition) -> str:
        """获取位置名称"""
        position_names = {
            WatermarkPosition.TOP_LEFT: "左上角",
            WatermarkPosition.TOP_CENTER: "上方居中",
            WatermarkPosition.TOP_RIGHT: "右上角",
            WatermarkPosition.CENTER_LEFT: "左侧居中",
            WatermarkPosition.CENTER: "正中央",
            WatermarkPosition.CENTER_RIGHT: "右侧居中",
            WatermarkPosition.BOTTOM_LEFT: "左下角",
            WatermarkPosition.BOTTOM_CENTER: "下方居中",
            WatermarkPosition.BOTTOM_RIGHT: "右下角",
            WatermarkPosition.CUSTOM: "自定义位置"
        }
        return position_names.get(position, "未知位置")
    
    def get_all_positions(self) -> Dict[str, WatermarkPosition]:
        """获取所有位置选项"""
        return {
            "左上角": WatermarkPosition.TOP_LEFT,
            "上方居中": WatermarkPosition.TOP_CENTER,
            "右上角": WatermarkPosition.TOP_RIGHT,
            "左侧居中": WatermarkPosition.CENTER_LEFT,
            "正中央": WatermarkPosition.CENTER,
            "右侧居中": WatermarkPosition.CENTER_RIGHT,
            "左下角": WatermarkPosition.BOTTOM_LEFT,
            "下方居中": WatermarkPosition.BOTTOM_CENTER,
            "右下角": WatermarkPosition.BOTTOM_RIGHT,
            "自定义位置": WatermarkPosition.CUSTOM
        }
    
    def create_watermark_config(self, watermark_type: WatermarkType, **kwargs) -> Dict[str, Any]:
        """创建水印配置"""
        config = {
            'type': watermark_type.value,
            'enabled': kwargs.get('enabled', True),
            'position': kwargs.get('position', self.default_position).value,
            'offset_x': kwargs.get('offset_x', 0),
            'offset_y': kwargs.get('offset_y', 0),
            'rotation': kwargs.get('rotation', 0)
        }
        
        if watermark_type == WatermarkType.TEXT:
            config.update({
                'text': kwargs.get('text', ''),
                'font_size': kwargs.get('font_size', self.default_font_size),
                'font_path': kwargs.get('font_path', ''),
                'color': kwargs.get('color', self.default_color),
                'opacity': kwargs.get('opacity', 0.5)
            })
        elif watermark_type == WatermarkType.IMAGE:
            config.update({
                'image_path': kwargs.get('image_path', ''),
                'scale': kwargs.get('scale', 1.0),
                'opacity': kwargs.get('opacity', 1.0)
            })
        
        return config
    
    def apply_watermark_from_config(self, img: Image.Image, config: Dict[str, Any]) -> Image.Image:
        """根据配置应用水印"""
        if not config.get('enabled', True):
            return img.copy()
        
        watermark_type = WatermarkType(config['type'])
        position = WatermarkPosition(config['position'])
        offset = (config.get('offset_x', 0), config.get('offset_y', 0))
        rotation = config.get('rotation', 0)
        
        if watermark_type == WatermarkType.TEXT:
            return self.apply_text_watermark(
                img=img,
                text=config.get('text', ''),
                font_size=config.get('font_size', self.default_font_size),
                color=config.get('color', self.default_color),
                position=position,
                offset=offset,
                rotation=rotation,
                font_path=config.get('font_path', '')
            )
        elif watermark_type == WatermarkType.IMAGE:
            return self.apply_image_watermark(
                img=img,
                watermark_path=config.get('image_path', ''),
                scale=config.get('scale', 1.0),
                opacity=config.get('opacity', 1.0),
                position=position,
                offset=offset,
                rotation=rotation
            )
        
        return img.copy()
    
    def validate_watermark_config(self, config: Dict[str, Any]) -> Tuple[bool, str]:
        """验证水印配置"""
        try:
            # 检查基本字段
            if 'type' not in config:
                return False, "缺少水印类型"
            
            watermark_type = WatermarkType(config['type'])
            
            # 检查位置
            if 'position' in config:
                WatermarkPosition(config['position'])
            
            # 检查数值范围
            if 'rotation' in config:
                rotation = config['rotation']
                if not isinstance(rotation, (int, float)) or rotation < -360 or rotation > 360:
                    return False, "旋转角度必须在-360到360之间"
            
            if watermark_type == WatermarkType.TEXT:
                # 验证文本水印
                if not config.get('text', '').strip():
                    return False, "文本水印内容不能为空"
                
                font_size = config.get('font_size', self.default_font_size)
                if not isinstance(font_size, int) or font_size < 1 or font_size > 500:
                    return False, "字体大小必须在1-500之间"
                
                opacity = config.get('opacity', 0.5)
                if not isinstance(opacity, (int, float)) or opacity < 0 or opacity > 1:
                    return False, "透明度必须在0-1之间"
                
            elif watermark_type == WatermarkType.IMAGE:
                # 验证图片水印
                image_path = config.get('image_path', '')
                if not image_path:
                    return False, "图片水印路径不能为空"
                
                if not os.path.exists(image_path):
                    return False, f"水印图片不存在: {image_path}"
                
                scale = config.get('scale', 1.0)
                if not isinstance(scale, (int, float)) or scale <= 0 or scale > 10:
                    return False, "缩放比例必须在0-10之间"
                
                opacity = config.get('opacity', 1.0)
                if not isinstance(opacity, (int, float)) or opacity < 0 or opacity > 1:
                    return False, "透明度必须在0-1之间"
            
            return True, "配置验证通过"
            
        except ValueError as e:
            return False, f"配置值错误: {e}"
        except Exception as e:
            return False, f"配置验证失败: {e}"
    
    def get_available_fonts(self) -> List[str]:
        """获取可用字体列表"""
        fonts = []
        
        # macOS 系统字体路径
        font_paths = [
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            "~/Library/Fonts/"
        ]
        
        for font_path in font_paths:
            expanded_path = os.path.expanduser(font_path)
            if os.path.exists(expanded_path):
                try:
                    for file in os.listdir(expanded_path):
                        if file.lower().endswith(('.ttf', '.ttc', '.otf')):
                            fonts.append(os.path.join(expanded_path, file))
                except PermissionError:
                    continue
        
        return sorted(fonts)
    
    def preview_watermark(self, img: Image.Image, config: Dict[str, Any], 
                         preview_size: Tuple[int, int] = (400, 300)) -> Image.Image:
        """生成水印预览"""
        # 创建预览尺寸的图片
        preview_img = img.copy()
        
        # 调整预览尺寸
        if preview_img.size != preview_size:
            preview_img.thumbnail(preview_size, Image.Resampling.LANCZOS)
        
        # 应用水印
        watermarked_preview = self.apply_watermark_from_config(preview_img, config)
        
        return watermarked_preview