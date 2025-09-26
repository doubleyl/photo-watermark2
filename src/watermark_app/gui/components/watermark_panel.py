#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印设置面板
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
import os
from typing import Dict, Any, Optional, Callable

from ...core import WatermarkPosition, WatermarkType
from ...utils import show_error, color_to_hex, hex_to_color


class WatermarkPanel(ttk.LabelFrame):
    """水印设置面板类"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="水印设置", padding=10)
        self.app = app
        
        # 水印设置变量
        self.watermark_enabled = tk.BooleanVar(value=True)
        self.watermark_type = tk.StringVar(value="text")
        self.text_content = tk.StringVar(value="水印")
        self.font_size = tk.IntVar(value=36)
        self.font_family = tk.StringVar(value="苹方 (PingFang SC)")  # 默认中文字体
        self.text_color = tk.StringVar(value="#FFFFFF")
        self.opacity = tk.IntVar(value=80)
        self.position = tk.StringVar(value="bottom_right")
        self.image_path = tk.StringVar()
        self.image_scale = tk.DoubleVar(value=0.2)
        self.offset_x = tk.IntVar(value=0)
        self.offset_y = tk.IntVar(value=0)
        
        # 获取可用字体
        from ...core import WatermarkManager
        self.watermark_manager = WatermarkManager()
        self.available_fonts = self.watermark_manager.get_available_fonts()
        
        self.setup_ui()
        self.setup_bindings()
    
    def setup_ui(self):
        """设置用户界面"""
        # 启用水印复选框
        enable_frame = ttk.Frame(self)
        enable_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Checkbutton(
            enable_frame,
            text="启用水印",
            variable=self.watermark_enabled,
            command=self.on_watermark_toggle
        ).pack(side=tk.LEFT)
        
        # 水印类型选择
        type_frame = ttk.LabelFrame(self, text="水印类型", padding=5)
        type_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(
            type_frame,
            text="文本水印",
            variable=self.watermark_type,
            value="text",
            command=self.on_type_change
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Radiobutton(
            type_frame,
            text="图片水印",
            variable=self.watermark_type,
            value="image",
            command=self.on_type_change
        ).pack(side=tk.LEFT)
        
        # 创建笔记本控件用于切换设置
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 文本水印设置
        self.text_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.text_frame, text="文本设置")
        self.setup_text_settings()
        
        # 图片水印设置
        self.image_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.image_frame, text="图片设置")
        self.setup_image_settings()
        
        # 位置和样式设置
        self.position_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.position_frame, text="位置设置")
        self.setup_position_settings()
        
        # 模板管理
        template_frame = ttk.LabelFrame(self, text="模板管理", padding=5)
        template_frame.pack(fill=tk.X)
        
        ttk.Button(
            template_frame,
            text="保存模板",
            command=self.save_template
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            template_frame,
            text="加载模板",
            command=self.load_template
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            template_frame,
            text="重置",
            command=self.reset_settings
        ).pack(side=tk.RIGHT)
    
    def setup_text_settings(self):
        """设置文本水印选项"""
        # 文本内容
        ttk.Label(self.text_frame, text="文本内容:").grid(row=0, column=0, sticky=tk.W, pady=2)
        text_entry = ttk.Entry(self.text_frame, textvariable=self.text_content, width=20)
        text_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=2, padx=(5, 0))
        
        # 字体选择
        ttk.Label(self.text_frame, text="字体:").grid(row=1, column=0, sticky=tk.W, pady=2)
        font_combo = ttk.Combobox(
            self.text_frame,
            textvariable=self.font_family,
            values=list(self.available_fonts.keys()),
            state="readonly",
            width=18
        )
        font_combo.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=2, padx=(5, 0))
        font_combo.bind('<<ComboboxSelected>>', self.on_setting_change)
        
        # 字体大小
        ttk.Label(self.text_frame, text="字体大小:").grid(row=2, column=0, sticky=tk.W, pady=2)
        font_scale = ttk.Scale(
            self.text_frame,
            from_=12,
            to=100,
            variable=self.font_size,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        font_scale.grid(row=2, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        font_label = ttk.Label(self.text_frame, text="36")
        font_label.grid(row=2, column=2, pady=2, padx=(5, 0))
        
        # 绑定字体大小显示更新
        def update_font_label(*args):
            font_label.config(text=str(self.font_size.get()))
        self.font_size.trace('w', update_font_label)
        
        # 文本颜色
        ttk.Label(self.text_frame, text="文本颜色:").grid(row=3, column=0, sticky=tk.W, pady=2)
        
        color_frame = ttk.Frame(self.text_frame)
        color_frame.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=2, padx=(5, 0))
        
        self.color_button = tk.Button(
            color_frame,
            text="选择颜色",
            bg=self.text_color.get(),
            command=self.choose_color,
            width=10
        )
        self.color_button.pack(side=tk.LEFT)
        
        ttk.Label(color_frame, textvariable=self.text_color).pack(side=tk.LEFT, padx=(10, 0))
        
        # 配置列权重
        self.text_frame.columnconfigure(1, weight=1)
    
    def setup_image_settings(self):
        """设置图片水印选项"""
        # 图片路径
        ttk.Label(self.image_frame, text="水印图片:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        path_frame = ttk.Frame(self.image_frame)
        path_frame.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=2, padx=(5, 0))
        
        self.path_entry = ttk.Entry(path_frame, textvariable=self.image_path, state="readonly")
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            path_frame,
            text="浏览",
            command=self.browse_image,
            width=8
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 图片缩放
        ttk.Label(self.image_frame, text="缩放比例:").grid(row=1, column=0, sticky=tk.W, pady=2)
        
        scale_scale = ttk.Scale(
            self.image_frame,
            from_=0.1,
            to=1.0,
            variable=self.image_scale,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        scale_scale.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        
        scale_label = ttk.Label(self.image_frame, text="20%")
        scale_label.grid(row=1, column=2, pady=2, padx=(5, 0))
        
        # 绑定缩放比例显示更新
        def update_scale_label(*args):
            scale_label.config(text=f"{int(self.image_scale.get() * 100)}%")
        self.image_scale.trace('w', update_scale_label)
        
        # 配置列权重
        self.image_frame.columnconfigure(1, weight=1)
    
    def setup_position_settings(self):
        """设置位置选项"""
        # 预设位置（九宫格）
        ttk.Label(self.position_frame, text="预设位置:").grid(row=0, column=0, sticky=tk.W, pady=2)
        
        position_frame = ttk.Frame(self.position_frame)
        position_frame.grid(row=0, column=1, columnspan=3, sticky=tk.EW, pady=2, padx=(5, 0))
        
        positions = [
            ("左上", "top_left"), ("上中", "top_center"), ("右上", "top_right"),
            ("左中", "center_left"), ("正中", "center"), ("右中", "center_right"),
            ("左下", "bottom_left"), ("下中", "bottom_center"), ("右下", "bottom_right")
        ]
        
        for i, (text, value) in enumerate(positions):
            row = i // 3
            col = i % 3
            ttk.Radiobutton(
                position_frame,
                text=text,
                variable=self.position,
                value=value,
                command=self.on_setting_change
            ).grid(row=row, column=col, sticky=tk.W, padx=5, pady=2)
        
        # 透明度
        ttk.Label(self.position_frame, text="透明度:").grid(row=1, column=0, sticky=tk.W, pady=2)
        
        opacity_scale = ttk.Scale(
            self.position_frame,
            from_=0,
            to=100,
            variable=self.opacity,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        opacity_scale.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=2, padx=(5, 0))
        
        opacity_label = ttk.Label(self.position_frame, text="80%")
        opacity_label.grid(row=1, column=3, pady=2, padx=(5, 0))
        
        # 绑定透明度显示更新
        def update_opacity_label(*args):
            opacity_label.config(text=f"{self.opacity.get()}%")
        self.opacity.trace('w', update_opacity_label)
        
        # 位置微调
        ttk.Label(self.position_frame, text="位置微调:").grid(row=2, column=0, sticky=tk.W, pady=2)
        
        offset_frame = ttk.Frame(self.position_frame)
        offset_frame.grid(row=2, column=1, columnspan=3, sticky=tk.EW, pady=2, padx=(5, 0))
        
        ttk.Label(offset_frame, text="X:").pack(side=tk.LEFT)
        ttk.Spinbox(
            offset_frame,
            from_=-200,
            to=200,
            textvariable=self.offset_x,
            width=8,
            command=self.on_setting_change
        ).pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(offset_frame, text="Y:").pack(side=tk.LEFT)
        ttk.Spinbox(
            offset_frame,
            from_=-200,
            to=200,
            textvariable=self.offset_y,
            width=8,
            command=self.on_setting_change
        ).pack(side=tk.LEFT, padx=(2, 0))
        
        # 配置列权重
        self.position_frame.columnconfigure(1, weight=1)
    
    def setup_bindings(self):
        """设置事件绑定"""
        # 绑定变量变化事件
        self.text_content.trace('w', self.on_setting_change)
        self.image_path.trace('w', self.on_setting_change)
        self.offset_x.trace('w', self.on_setting_change)
        self.offset_y.trace('w', self.on_setting_change)
    
    def on_watermark_toggle(self):
        """水印启用/禁用切换"""
        enabled = self.watermark_enabled.get()
        
        # 启用/禁用所有子控件
        state = tk.NORMAL if enabled else tk.DISABLED
        for child in self.notebook.winfo_children():
            self.set_widget_state(child, state)
        
        self.on_setting_change()
    
    def set_widget_state(self, widget, state):
        """递归设置控件状态"""
        try:
            widget.configure(state=state)
        except:
            pass
        
        for child in widget.winfo_children():
            self.set_widget_state(child, state)
    
    def on_type_change(self):
        """水印类型变化"""
        watermark_type = self.watermark_type.get()
        
        # 切换到对应的标签页
        if watermark_type == "text":
            self.notebook.select(0)
        else:
            self.notebook.select(1)
        
        self.on_setting_change()
    
    def on_setting_change(self, *args):
        """设置变化事件"""
        # 通知预览面板更新
        if hasattr(self.app, 'preview_panel'):
            self.app.preview_panel.refresh_preview()
    
    def choose_color(self):
        """选择颜色"""
        color = colorchooser.askcolor(
            color=self.text_color.get(),
            title="选择文本颜色"
        )
        
        if color[1]:  # 用户选择了颜色
            self.text_color.set(color[1])
            self.color_button.config(bg=color[1])
            self.on_setting_change()
    
    def browse_image(self):
        """浏览图片文件"""
        filetypes = [
            ("图片文件", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("PNG文件", "*.png"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("所有文件", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="选择水印图片",
            filetypes=filetypes
        )
        
        if file_path:
            self.image_path.set(file_path)
    
    def get_settings(self) -> Dict[str, Any]:
        """获取当前水印设置"""
        # 获取选中字体的路径
        font_name = self.font_family.get()
        font_path = self.available_fonts.get(font_name, "default")
        
        return {
            'enabled': self.watermark_enabled.get(),
            'type': self.watermark_type.get(),
            'text': self.text_content.get(),
            'font_size': self.font_size.get(),
            'font_family': font_name,
            'font_path': font_path,
            'color': self.text_color.get(),
            'opacity': self.opacity.get(),
            'position': self.position.get(),
            'image_path': self.image_path.get(),
            'scale': self.image_scale.get(),
            'offset_x': self.offset_x.get(),
            'offset_y': self.offset_y.get()
        }
    
    def set_settings(self, settings: Dict[str, Any]):
        """设置水印参数"""
        self.watermark_enabled.set(settings.get('enabled', True))
        self.watermark_type.set(settings.get('type', 'text'))
        self.text_content.set(settings.get('text', '水印'))
        self.font_size.set(settings.get('font_size', 36))
        self.font_family.set(settings.get('font_family', '苹方 (PingFang SC)'))
        self.text_color.set(settings.get('color', '#FFFFFF'))
        self.opacity.set(settings.get('opacity', 80))
        self.position.set(settings.get('position', 'bottom_right'))
        self.image_path.set(settings.get('image_path', ''))
        self.image_scale.set(settings.get('scale', 0.2))
        self.offset_x.set(settings.get('offset_x', 0))
        self.offset_y.set(settings.get('offset_y', 0))
        
        # 更新颜色按钮
        self.color_button.config(bg=self.text_color.get())
        
        # 更新界面状态
        self.on_watermark_toggle()
        self.on_type_change()
    
    def reset_settings(self):
        """重置设置"""
        if messagebox.askyesno("确认", "确定要重置所有水印设置吗？"):
            default_settings = {
                'enabled': True,
                'type': 'text',
                'text': '水印',
                'font_size': 36,
                'color': '#FFFFFF',
                'opacity': 80,
                'position': 'bottom_right',
                'image_path': '',
                'scale': 0.2,
                'offset_x': 0,
                'offset_y': 0
            }
            self.set_settings(default_settings)
    
    def save_template(self):
        """保存模板"""
        # 这里可以实现模板保存功能
        messagebox.showinfo("提示", "模板保存功能将在后续版本中实现")
    
    def load_template(self):
        """加载模板"""
        # 这里可以实现模板加载功能
        messagebox.showinfo("提示", "模板加载功能将在后续版本中实现")
    
    def manage_templates(self):
        """管理模板"""
        # 这里可以实现模板管理功能
        messagebox.showinfo("提示", "模板管理功能将在后续版本中实现")