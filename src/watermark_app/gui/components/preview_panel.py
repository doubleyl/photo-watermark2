#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预览面板
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont
import os
from typing import Optional, Tuple

from ...core import WatermarkManager, WatermarkPosition, WatermarkType
from ...utils import show_error


class PreviewPanel(ttk.LabelFrame):
    """预览面板类"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="预览", padding=10)
        self.app = app
        
        # 图片相关变量
        self.original_image: Optional[Image.Image] = None
        self.current_image: Optional[Image.Image] = None
        self.current_photo: Optional[ImageTk.PhotoImage] = None
        self.zoom_factor = 1.0
        
        # 拖拽相关变量
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.watermark_offset_x = 0
        self.watermark_offset_y = 0
        
        self.setup_ui()
        self.setup_bindings()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建画布框架
        canvas_frame = ttk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建画布和滚动条
        self.canvas = tk.Canvas(
            canvas_frame,
            bg='#2d2d2d',  # 深灰色背景，更容易看到图片边界
            relief=tk.SUNKEN,
            borderwidth=2
        )
        
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set
        )
        
        # 布局
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 控制面板
        control_frame = ttk.Frame(self)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 缩放控制
        ttk.Label(control_frame, text="缩放:").pack(side=tk.LEFT)
        
        self.zoom_var = tk.StringVar(value="适应窗口")
        zoom_combo = ttk.Combobox(
            control_frame,
            textvariable=self.zoom_var,
            values=["25%", "50%", "75%", "100%", "125%", "150%", "200%", "适应窗口"],
            state="readonly",
            width=10
        )
        zoom_combo.pack(side=tk.LEFT, padx=(5, 10))
        zoom_combo.bind('<<ComboboxSelected>>', self.on_zoom_change)
        
        # 刷新按钮
        ttk.Button(
            control_frame,
            text="刷新预览",
            command=self.refresh_preview
        ).pack(side=tk.RIGHT)
        
        # 显示提示信息
        self.show_placeholder()
    
    def setup_bindings(self):
        """设置事件绑定"""
        self.canvas.bind('<Button-1>', self.on_canvas_click)
        self.canvas.bind('<B1-Motion>', self.on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_canvas_release)
        self.canvas.bind('<Configure>', self.on_canvas_configure)
    
    def show_placeholder(self):
        """显示占位符"""
        self.canvas.delete("all")
        self.canvas.create_text(
            200, 150,
            text="请选择图片进行预览",
            font=("Arial", 16),
            fill="gray"
        )
    
    def load_image(self, file_path: str):
        """加载图片"""
        try:
            # 打开原始图片
            self.original_image = Image.open(file_path)
            self.current_image = self.original_image.copy()
            
            # 应用水印
            self.apply_watermark()
            
            # 显示图片
            self.display_image()
            
        except Exception as e:
            self.show_error(f"加载图片失败: {e}")
    
    def apply_watermark(self):
        """应用水印"""
        if self.original_image is None:
            return
        
        # 复制原始图片
        self.current_image = self.original_image.copy()
        
        # 获取水印设置
        if hasattr(self.app, 'watermark_panel'):
            watermark_settings = self.app.watermark_panel.get_settings()
            
            if watermark_settings['enabled']:
                # 使用水印管理器应用水印
                watermark_manager = WatermarkManager()
                try:
                    if watermark_settings['type'] == 'text':
                        # 转换位置字符串为枚举
                        position_str = watermark_settings.get('position', 'bottom_right')
                        position = getattr(WatermarkPosition, position_str.upper(), WatermarkPosition.BOTTOM_RIGHT)
                        
                        self.current_image = watermark_manager.apply_text_watermark(
                            self.current_image,
                            text=watermark_settings.get('text', '水印'),
                            font_size=watermark_settings.get('font_size', 36),
                            font_path=watermark_settings.get('font_path', 'default'),
                            color=watermark_settings.get('color', '#FFFFFF'),
                            opacity=watermark_settings.get('opacity', 80),
                            position=position,
                            offset=(watermark_settings.get('offset_x', 0), watermark_settings.get('offset_y', 0)),
                            rotation=watermark_settings.get('rotation_angle', 0),
                            shadow_enabled=watermark_settings.get('shadow_enabled', False),
                            shadow_offset=(watermark_settings.get('shadow_offset_x', 2), watermark_settings.get('shadow_offset_y', 2)),
                            shadow_blur=watermark_settings.get('shadow_blur', 4),
                            shadow_color=watermark_settings.get('shadow_color', '#000000')
                        )
                    elif watermark_settings['type'] == 'image':
                        # 转换位置字符串为枚举
                        position_str = watermark_settings.get('position', 'bottom_right')
                        position = getattr(WatermarkPosition, position_str.upper(), WatermarkPosition.BOTTOM_RIGHT)
                        
                        self.current_image = watermark_manager.apply_image_watermark(
                            self.current_image,
                            watermark_path=watermark_settings.get('image_path', ''),
                            opacity=watermark_settings.get('opacity', 80),
                            position=position,
                            scale=watermark_settings.get('scale', 0.2),
                            offset=(watermark_settings.get('offset_x', 0), watermark_settings.get('offset_y', 0)),
                            rotation=watermark_settings.get('rotation_angle', 0)
                        )
                except Exception as e:
                    print(f"应用水印失败: {e}")
    
    def apply_image_watermark(self, settings: dict):
        """应用图片水印"""
        try:
            watermark_path = settings.get('image_path')
            if not watermark_path or not os.path.exists(watermark_path):
                return
            
            # 打开水印图片
            watermark = Image.open(watermark_path)
            
            # 调整水印大小
            scale = settings.get('scale', 0.2)
            img_width, img_height = self.current_image.size
            wm_width = int(img_width * scale)
            wm_height = int(watermark.height * wm_width / watermark.width)
            watermark = watermark.resize((wm_width, wm_height), Image.Resampling.LANCZOS)
            
            # 计算位置
            position = settings.get('position', 'bottom_right')
            if position == 'top_left':
                x, y = 20, 20
            elif position == 'top_center':
                x, y = (img_width - wm_width) // 2, 20
            elif position == 'top_right':
                x, y = img_width - wm_width - 20, 20
            elif position == 'center_left':
                x, y = 20, (img_height - wm_height) // 2
            elif position == 'center':
                x, y = (img_width - wm_width) // 2, (img_height - wm_height) // 2
            elif position == 'center_right':
                x, y = img_width - wm_width - 20, (img_height - wm_height) // 2
            elif position == 'bottom_left':
                x, y = 20, img_height - wm_height - 20
            elif position == 'bottom_center':
                x, y = (img_width - wm_width) // 2, img_height - wm_height - 20
            else:  # bottom_right
                x, y = img_width - wm_width - 20, img_height - wm_height - 20
            
            # 应用透明度
            opacity = settings.get('opacity', 80)
            if opacity < 100 and watermark.mode in ('RGBA', 'LA'):
                alpha = watermark.split()[-1]
                alpha = alpha.point(lambda p: int(p * opacity / 100))
                watermark.putalpha(alpha)
            
            # 粘贴水印
            if watermark.mode in ('RGBA', 'LA'):
                self.current_image.paste(watermark, (x, y), watermark)
            else:
                self.current_image.paste(watermark, (x, y))
                
        except Exception as e:
            print(f"应用图片水印失败: {e}")
    
    def display_image(self):
        """显示图片"""
        if self.current_image is None:
            return
        
        try:
            # 计算显示尺寸
            display_image = self.calculate_display_size()
            
            # 转换为PhotoImage
            self.current_photo = ImageTk.PhotoImage(display_image)
            
            # 清空画布并显示图片
            self.canvas.delete("all")
            
            # 获取画布尺寸
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # 如果画布尺寸无效，使用默认值
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 400, 300
            
            # 计算图片在画布中的居中位置
            img_width, img_height = display_image.size
            x = max(0, (canvas_width - img_width) // 2)
            y = max(0, (canvas_height - img_height) // 2)
            
            # 在居中位置显示图片
            self.canvas.create_image(x, y, anchor=tk.NW, image=self.current_photo)
            
            # 更新滚动区域
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            self.show_error(f"显示图片失败: {e}")
    
    def calculate_display_size(self) -> Image.Image:
        """计算显示尺寸"""
        if self.current_image is None:
            return None
        
        zoom = self.zoom_var.get()
        
        if zoom == "适应窗口":
            # 适应画布大小
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                canvas_width, canvas_height = 400, 300
            
            img_width, img_height = self.current_image.size
            
            # 计算缩放比例
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y, 1.0)  # 不放大
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
        else:
            # 按百分比缩放
            scale = float(zoom.rstrip('%')) / 100
            img_width, img_height = self.current_image.size
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
        
        return self.current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def on_zoom_change(self, event):
        """缩放变化事件"""
        self.display_image()
    
    def on_canvas_configure(self, event):
        """画布大小变化事件"""
        if self.zoom_var.get() == "适应窗口":
            self.display_image()
    
    def on_canvas_click(self, event):
        """画布点击事件 - 开始拖拽"""
        if self.current_image is None:
            return
            
        # 记录拖拽开始位置
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # 获取当前水印偏移
        if hasattr(self.app, 'watermark_panel'):
            self.watermark_offset_x = self.app.watermark_panel.offset_x.get()
            self.watermark_offset_y = self.app.watermark_panel.offset_y.get()
    
    def on_canvas_drag(self, event):
        """画布拖拽事件 - 实时更新水印位置"""
        if not self.dragging or self.current_image is None:
            return
            
        # 计算拖拽距离
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        # 更新水印偏移
        new_offset_x = self.watermark_offset_x + dx
        new_offset_y = self.watermark_offset_y + dy
        
        # 限制偏移范围
        new_offset_x = max(-200, min(200, new_offset_x))
        new_offset_y = max(-200, min(200, new_offset_y))
        
        # 更新水印面板的偏移值
        if hasattr(self.app, 'watermark_panel'):
            self.app.watermark_panel.offset_x.set(new_offset_x)
            self.app.watermark_panel.offset_y.set(new_offset_y)
            
            # 实时更新预览
            self.refresh_preview()
    
    def on_canvas_release(self, event):
        """画布释放事件 - 结束拖拽"""
        self.dragging = False
    
    def refresh_preview(self):
        """刷新预览"""
        if self.original_image is not None:
            self.apply_watermark()
            self.display_image()
    
    def clear_preview(self):
        """清空预览"""
        self.current_image = None
        self.current_photo = None
        self.original_image = None
        self.show_placeholder()
    
    def show_error(self, message: str):
        """显示错误信息"""
        self.canvas.delete("all")
        self.canvas.create_text(
            200, 150,
            text=message,
            font=("Arial", 12),
            fill="red",
            width=350
        )
    
    def get_preview_image(self) -> Optional[Image.Image]:
        """获取预览图片（带水印）"""
        return self.current_image