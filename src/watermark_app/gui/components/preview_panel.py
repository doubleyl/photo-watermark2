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
        self.drag_start_offset_x = 0
        self.drag_start_offset_y = 0
        
        # 实时拖动反馈相关变量
        self.drag_preview_item = None  # Canvas上的临时水印预览项
        self.base_image_item = None    # Canvas上的基础图像项
        
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
        
        # 添加鼠标滚轮支持
        self.bind_mousewheel()
    
    def bind_mousewheel(self):
        """绑定鼠标滚轮事件"""
        def _on_mousewheel(event):
            # 检查是否有图片显示且需要滚动
            if self.current_image is not None:
                # 检查事件来源，只在Canvas或合适的区域处理滚轮事件
                widget = event.widget
                widget_class = widget.winfo_class()
                
                # 如果是数值输入控件或其他交互控件，不处理滚轮事件
                if widget_class in ['Spinbox', 'Entry', 'Scale', 'TSpinbox', 'TEntry', 'TScale', 'Combobox', 'TCombobox']:
                    return
                
                # 只在Canvas或面板本身上处理滚轮事件
                if widget == self.canvas or widget == self:
                    # 根据Shift键决定滚动方向
                    if event.state & 0x1:  # Shift键按下，水平滚动
                        self.canvas.xview_scroll(int(-1*(event.delta/120)), "units")
                    else:  # 垂直滚动
                        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # 只绑定到Canvas，避免冲突
        self.canvas.bind("<MouseWheel>", _on_mousewheel)
    
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
                            font_bold=watermark_settings.get('font_bold', False),
                            font_italic=watermark_settings.get('font_italic', False),
                            color=watermark_settings.get('color', '#FFFFFF'),
                            opacity=watermark_settings.get('opacity', 80),
                            position=position,
                            offset=(watermark_settings.get('offset_x', 0), watermark_settings.get('offset_y', 0)),
                            rotation=watermark_settings.get('rotation_angle', 0),
                            shadow_enabled=watermark_settings.get('shadow_enabled', False),
                            shadow_offset=(watermark_settings.get('shadow_offset_x', 2), watermark_settings.get('shadow_offset_y', 2)),
                            shadow_blur=watermark_settings.get('shadow_blur', 4),
                            shadow_color=watermark_settings.get('shadow_color', '#000000'),
                            stroke_enabled=watermark_settings.get('stroke_enabled', False),
                            stroke_width=watermark_settings.get('stroke_width', 2),
                            stroke_color=watermark_settings.get('stroke_color', '#000000')
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
            
            # 在居中位置显示图片，并保存引用
            self.base_image_item = self.canvas.create_image(x, y, anchor=tk.NW, image=self.current_photo)
            
            # 更新滚动区域
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            self.show_error(f"显示图片失败: {e}")
    
    def create_drag_preview(self, x, y):
        """创建拖动时的水印预览"""
        if not hasattr(self.app, 'watermark_panel'):
            return
            
        try:
            watermark_panel = self.app.watermark_panel
            watermark_type = watermark_panel.watermark_type.get()
            
            # 移除之前的预览
            self.remove_drag_preview()
            
            if watermark_type == "text":
                # 文本水印预览
                text = watermark_panel.text_content.get()
                if text.strip():
                    # 获取真实的字体属性
                    font_size = int(watermark_panel.font_size.get() * self.zoom_factor)
                    font_family = watermark_panel.font_family.get()
                    font_bold = watermark_panel.font_bold.get()
                    font_italic = watermark_panel.font_italic.get()
                    
                    # 获取真实的颜色
                    text_color = watermark_panel.text_color.get()
                    
                    # 获取旋转角度
                    rotation_angle = watermark_panel.rotation_angle.get()
                    
                    # 构建字体样式
                    font_style = "normal"
                    font_weight = "bold" if font_bold else "normal"
                    if font_italic:
                        font_style = "italic"
                    
                    # 创建更真实的文本预览
                    self.drag_preview_item = self.canvas.create_text(
                        x, y,
                        text=text,
                        font=(font_family, max(12, font_size), font_weight, font_style),
                        fill=text_color,
                        anchor=tk.CENTER,
                        angle=rotation_angle  # 添加旋转角度
                    )
            else:
                # 图片水印预览
                if hasattr(watermark_panel, 'watermark_image') and watermark_panel.watermark_image:
                    # 计算水印图片的显示尺寸
                    scale = watermark_panel.scale.get() / 100.0
                    img_width = int(watermark_panel.watermark_image.width * scale * self.zoom_factor)
                    img_height = int(watermark_panel.watermark_image.height * scale * self.zoom_factor)
                    
                    # 获取旋转角度
                    rotation_angle = watermark_panel.rotation_angle.get()
                    
                    # 如果有旋转，创建旋转的矩形预览
                    if rotation_angle != 0:
                        # 计算旋转后的四个角点
                        import math
                        rad = math.radians(rotation_angle)
                        cos_a = math.cos(rad)
                        sin_a = math.sin(rad)
                        
                        # 矩形的四个角点（相对于中心）
                        corners = [
                            (-img_width//2, -img_height//2),
                            (img_width//2, -img_height//2),
                            (img_width//2, img_height//2),
                            (-img_width//2, img_height//2)
                        ]
                        
                        # 旋转后的角点
                        rotated_corners = []
                        for cx, cy in corners:
                            rx = cx * cos_a - cy * sin_a + x
                            ry = cx * sin_a + cy * cos_a + y
                            rotated_corners.extend([rx, ry])
                        
                        # 创建旋转的多边形预览
                        self.drag_preview_item = self.canvas.create_polygon(
                            rotated_corners,
                            outline="#FF6B6B",
                            width=2,
                            fill="",
                            dash=(5, 5)
                        )
                    else:
                        # 创建普通矩形框预览
                        self.drag_preview_item = self.canvas.create_rectangle(
                            x - img_width//2, y - img_height//2,
                            x + img_width//2, y + img_height//2,
                            outline="#FF6B6B",
                            width=2,
                            dash=(5, 5),
                            fill=""
                        )
                else:
                    # 如果没有水印图片，显示默认大小的矩形
                    size = int(100 * self.zoom_factor)
                    self.drag_preview_item = self.canvas.create_rectangle(
                        x - size//2, y - size//2,
                        x + size//2, y + size//2,
                        outline="#FF6B6B",
                        width=2,
                        fill="",
                        dash=(5, 5)
                    )
                
        except Exception as e:
            print(f"创建拖动预览失败: {e}")
    
    def update_drag_preview(self, x, y):
        """更新拖动预览的位置"""
        if self.drag_preview_item:
            try:
                watermark_panel = self.app.watermark_panel
                watermark_type = watermark_panel.watermark_type.get()
                
                if watermark_type == "text":
                    # 更新文本位置
                    self.canvas.coords(self.drag_preview_item, x, y)
                else:
                    # 更新图片水印位置
                    if hasattr(watermark_panel, 'watermark_image') and watermark_panel.watermark_image:
                        scale = watermark_panel.scale.get() / 100.0
                        img_width = int(watermark_panel.watermark_image.width * scale * self.zoom_factor)
                        img_height = int(watermark_panel.watermark_image.height * scale * self.zoom_factor)
                        rotation_angle = watermark_panel.rotation_angle.get()
                        
                        if rotation_angle != 0:
                            # 更新旋转多边形的位置
                            import math
                            rad = math.radians(rotation_angle)
                            cos_a = math.cos(rad)
                            sin_a = math.sin(rad)
                            
                            corners = [
                                (-img_width//2, -img_height//2),
                                (img_width//2, -img_height//2),
                                (img_width//2, img_height//2),
                                (-img_width//2, img_height//2)
                            ]
                            
                            rotated_corners = []
                            for cx, cy in corners:
                                rx = cx * cos_a - cy * sin_a + x
                                ry = cx * sin_a + cy * cos_a + y
                                rotated_corners.extend([rx, ry])
                            
                            self.canvas.coords(self.drag_preview_item, *rotated_corners)
                        else:
                            # 更新普通矩形位置
                            self.canvas.coords(
                                self.drag_preview_item,
                                x - img_width//2, y - img_height//2,
                                x + img_width//2, y + img_height//2
                            )
                    else:
                        # 默认大小矩形
                        size = int(100 * self.zoom_factor)
                        self.canvas.coords(
                            self.drag_preview_item,
                            x - size//2, y - size//2,
                            x + size//2, y + size//2
                        )
            except Exception as e:
                print(f"更新拖动预览失败: {e}")
    
    def remove_drag_preview(self):
        """移除拖动预览"""
        if self.drag_preview_item:
            self.canvas.delete(self.drag_preview_item)
            self.drag_preview_item = None
    
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
        
        # 存储缩放因子，用于拖拽计算
        self.zoom_factor = scale
        
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
        
        # 获取当前水印偏移作为拖拽起始点
        if hasattr(self.app, 'watermark_panel'):
            self.drag_start_offset_x = self.app.watermark_panel.offset_x.get()
            self.drag_start_offset_y = self.app.watermark_panel.offset_y.get()
            
            # 设置拖动状态，暂停自动保存
            self.app.watermark_panel.set_dragging_state(True)
            
            # 创建拖动预览
            self.create_drag_preview(event.x, event.y)
    
    def on_canvas_drag(self, event):
        """画布拖拽事件 - 实时更新水印位置"""
        if not self.dragging or self.current_image is None:
            return
            
        # 计算从拖拽开始点到当前位置的总偏移量（考虑缩放因子）
        total_dx = (event.x - self.drag_start_x) / self.zoom_factor
        total_dy = (event.y - self.drag_start_y) / self.zoom_factor
        
        # 基于拖拽起始偏移计算新的绝对位置（移除所有位置限制）
        new_offset_x = self.drag_start_offset_x + total_dx
        new_offset_y = self.drag_start_offset_y + total_dy
        
        # 更新水印面板的偏移值
        if hasattr(self.app, 'watermark_panel'):
            self.app.watermark_panel.offset_x.set(int(new_offset_x))
            self.app.watermark_panel.offset_y.set(int(new_offset_y))
            
        # 更新拖动预览位置，提供实时视觉反馈
        self.update_drag_preview(event.x, event.y)
    
    def on_canvas_release(self, event):
        """画布释放事件 - 结束拖拽"""
        self.dragging = False
        
        # 移除拖动预览
        self.remove_drag_preview()
        
        # 恢复自动保存状态
        if hasattr(self.app, 'watermark_panel'):
            self.app.watermark_panel.set_dragging_state(False)
    
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
        
        # 清理拖动预览
        self.remove_drag_preview()
        self.base_image_item = None
        
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