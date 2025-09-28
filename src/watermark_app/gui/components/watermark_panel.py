#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
水印设置面板
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog
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
        self.font_bold = tk.BooleanVar(value=False)  # 粗体选项
        self.font_italic = tk.BooleanVar(value=False)  # 斜体选项
        self.text_color = tk.StringVar(value="#FFFFFF")
        self.opacity = tk.IntVar(value=80)
        self.position = tk.StringVar(value="bottom_right")
        self.image_path = tk.StringVar()
        self.image_scale = tk.DoubleVar(value=0.2)
        self.offset_x = tk.IntVar(value=0)
        self.offset_y = tk.IntVar(value=0)
        
        # 高级功能变量
        self.rotation_angle = tk.IntVar(value=0)
        self.shadow_enabled = tk.BooleanVar(value=False)
        self.shadow_offset_x = tk.IntVar(value=2)
        self.shadow_offset_y = tk.IntVar(value=2)
        self.shadow_blur = tk.IntVar(value=4)
        self.shadow_color = tk.StringVar(value="#000000")
        
        # 描边效果变量
        self.stroke_enabled = tk.BooleanVar(value=False)
        self.stroke_width = tk.IntVar(value=2)
        self.stroke_color = tk.StringVar(value="#000000")
        
        # 获取可用字体
        from ...core import WatermarkManager
        self.watermark_manager = WatermarkManager()
        self.available_fonts = self.watermark_manager.get_available_fonts()
        
        self.setup_ui()
        self.setup_bindings()
    
    def setup_ui(self):
        """设置用户界面"""
        # 水印类型选择
        type_frame = ttk.Frame(self)
        type_frame.pack(fill=tk.X, pady=(0, 5))
        
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
        
        # 创建笔记本控件
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 设置notebook的最小尺寸，确保文本水印和图片水印时宽度一致
        self.notebook.configure(width=350, height=180)
        
        # 文本设置tab
        self.text_frame = ttk.Frame(self.notebook)
        self.setup_text_settings()
        
        # 图片设置tab
        self.image_frame = ttk.Frame(self.notebook)
        self.setup_image_settings()
        
        # 位置设置tab
        self.position_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.position_frame, text="位置设置")
        self.setup_position_settings()
        
        # 高级设置tab
        self.advanced_frame = ttk.Frame(self.notebook)
        self.setup_advanced_settings()
        
        # 模板操作按钮（直接放在面板底部，减小间距）
        template_frame = ttk.Frame(self)
        template_frame.pack(fill=tk.X, pady=(2, 0))
        
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
        
        # 初始化显示状态
        self.on_type_change()
    
    def setup_text_settings(self):
        """设置文本水印选项"""
        # 配置列权重
        self.text_frame.columnconfigure(1, weight=1)
        
        # 文本内容
        ttk.Label(self.text_frame, text="文本内容:").grid(row=0, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        text_entry = ttk.Entry(self.text_frame, textvariable=self.text_content, width=20)
        text_entry.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        # 字体选择
        ttk.Label(self.text_frame, text="字体:").grid(row=1, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        font_combo = ttk.Combobox(
            self.text_frame,
            textvariable=self.font_family,
            values=list(self.available_fonts.keys()),
            state="readonly",
            width=18
        )
        font_combo.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        font_combo.bind('<<ComboboxSelected>>', self.on_setting_change)
        
        # 字体大小
        ttk.Label(self.text_frame, text="字体大小:").grid(row=2, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        font_scale = ttk.Scale(
            self.text_frame,
            from_=8,
            to=200,
            variable=self.font_size,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        font_scale.grid(row=2, column=1, sticky=tk.EW, pady=1, padx=(5, 0))
        
        font_label = ttk.Label(self.text_frame, text="36")
        font_label.grid(row=2, column=2, pady=1, padx=(5, 0))
        
        # 绑定字体大小显示更新
        def update_font_label(*args):
            font_label.config(text=str(self.font_size.get()))
        self.font_size.trace('w', update_font_label)
        
        # 字体样式
        ttk.Label(self.text_frame, text="字体样式:").grid(row=3, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        style_frame = ttk.Frame(self.text_frame)
        style_frame.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        bold_check = ttk.Checkbutton(
            style_frame,
            text="粗体",
            variable=self.font_bold,
            command=self.on_setting_change
        )
        bold_check.pack(side=tk.LEFT, padx=(0, 10))
        
        italic_check = ttk.Checkbutton(
            style_frame,
            text="斜体",
            variable=self.font_italic,
            command=self.on_setting_change
        )
        italic_check.pack(side=tk.LEFT)
        
        # 文本颜色
        ttk.Label(self.text_frame, text="文本颜色:").grid(row=4, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        color_frame = ttk.Frame(self.text_frame)
        color_frame.grid(row=4, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        self.color_button = tk.Button(
            color_frame,
            text="选择颜色",
            bg=self.text_color.get(),
            command=self.choose_color,
            width=10
        )
        self.color_button.pack(side=tk.LEFT)
        
        ttk.Label(color_frame, textvariable=self.text_color).pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_image_settings(self):
        """设置图片水印选项"""
        # 配置列权重
        self.image_frame.columnconfigure(1, weight=1)
        
        # 图片路径
        ttk.Label(self.image_frame, text="水印图片:").grid(row=0, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        path_frame = ttk.Frame(self.image_frame)
        path_frame.grid(row=0, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        self.path_entry = ttk.Entry(path_frame, textvariable=self.image_path, state="readonly")
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(
            path_frame,
            text="浏览",
            command=self.browse_image,
            width=8
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 图片缩放
        ttk.Label(self.image_frame, text="缩放比例:").grid(row=1, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        scale_scale = ttk.Scale(
            self.image_frame,
            from_=0.1,
            to=1.0,
            variable=self.image_scale,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        scale_scale.grid(row=1, column=1, sticky=tk.EW, pady=1, padx=(5, 0))
        
        scale_label = ttk.Label(self.image_frame, text="20%")
        scale_label.grid(row=1, column=2, pady=1, padx=(5, 0))
        
        # 绑定缩放比例显示更新
        def update_scale_label(*args):
            scale_label.config(text=f"{int(self.image_scale.get() * 100)}%")
        self.image_scale.trace('w', update_scale_label)
    
    def setup_position_settings(self):
        """设置位置选项"""
        # 配置列权重
        self.position_frame.columnconfigure(1, weight=1)
        
        # 预设位置（九宫格）
        ttk.Label(self.position_frame, text="预设位置:").grid(row=0, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        position_frame = ttk.Frame(self.position_frame)
        position_frame.grid(row=0, column=1, columnspan=3, sticky=tk.EW, pady=1, padx=(5, 0))
        
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
            ).grid(row=row, column=col, sticky=tk.W, padx=5, pady=1)
        
        # 透明度
        ttk.Label(self.position_frame, text="透明度:").grid(row=1, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        opacity_scale = ttk.Scale(
            self.position_frame,
            from_=0,
            to=100,
            variable=self.opacity,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        opacity_scale.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        opacity_label = ttk.Label(self.position_frame, text="80%")
        opacity_label.grid(row=1, column=3, pady=1, padx=(5, 0))
        
        # 绑定透明度显示更新
        def update_opacity_label(*args):
            opacity_label.config(text=f"{self.opacity.get()}%")
        self.opacity.trace('w', update_opacity_label)
        
        # 位置微调
        ttk.Label(self.position_frame, text="位置微调:").grid(row=2, column=0, sticky=tk.W, pady=2, padx=(10, 0))
        
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
        
        # 旋转角度
        ttk.Label(self.position_frame, text="旋转角度:").grid(row=3, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        rotation_scale = ttk.Scale(
            self.position_frame,
            from_=-180,
            to=180,
            variable=self.rotation_angle,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        rotation_scale.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        rotation_label = ttk.Label(self.position_frame, text="0°")
        rotation_label.grid(row=3, column=3, pady=1, padx=(5, 0))
        
        # 绑定旋转角度显示更新
        def update_rotation_label(*args):
            rotation_label.config(text=f"{self.rotation_angle.get()}°")
        self.rotation_angle.trace('w', update_rotation_label)
        
        # 配置列权重
        self.position_frame.columnconfigure(1, weight=1)
    
    def setup_advanced_settings(self):
        """设置高级功能选项"""
        # 配置列权重
        self.advanced_frame.columnconfigure(1, weight=1)
        
        # 阴影设置 - 直接放在advanced_frame中
        ttk.Checkbutton(
            self.advanced_frame,
            text="启用阴影",
            variable=self.shadow_enabled,
            command=self.on_shadow_toggle
        ).grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(3, 3), padx=(10, 0))
        
        # 阴影偏移
        ttk.Label(self.advanced_frame, text="阴影偏移:").grid(row=1, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        shadow_offset_frame = ttk.Frame(self.advanced_frame)
        shadow_offset_frame.grid(row=1, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        ttk.Label(shadow_offset_frame, text="X:").pack(side=tk.LEFT)
        ttk.Spinbox(
            shadow_offset_frame,
            from_=-20,
            to=20,
            textvariable=self.shadow_offset_x,
            width=6,
            command=self.on_setting_change
        ).pack(side=tk.LEFT, padx=(2, 10))
        
        ttk.Label(shadow_offset_frame, text="Y:").pack(side=tk.LEFT)
        ttk.Spinbox(
            shadow_offset_frame,
            from_=-20,
            to=20,
            textvariable=self.shadow_offset_y,
            width=6,
            command=self.on_setting_change
        ).pack(side=tk.LEFT, padx=(2, 0))
        
        # 阴影模糊
        ttk.Label(self.advanced_frame, text="模糊半径:").grid(row=2, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        blur_scale = ttk.Scale(
            self.advanced_frame,
            from_=0,
            to=10,
            variable=self.shadow_blur,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        blur_scale.grid(row=2, column=1, sticky=tk.EW, pady=1, padx=(5, 0))
        
        blur_label = ttk.Label(self.advanced_frame, text="4px")
        blur_label.grid(row=2, column=2, pady=1, padx=(5, 0))
        
        # 绑定模糊半径显示更新
        def update_blur_label(*args):
            blur_label.config(text=f"{self.shadow_blur.get()}px")
        self.shadow_blur.trace('w', update_blur_label)
        
        # 阴影颜色
        ttk.Label(self.advanced_frame, text="阴影颜色:").grid(row=3, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        shadow_color_frame = ttk.Frame(self.advanced_frame)
        shadow_color_frame.grid(row=3, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        self.shadow_color_button = tk.Button(
            shadow_color_frame,
            text="选择颜色",
            bg="black",  # 使用系统颜色名称
            fg="white",
            command=self.choose_shadow_color,
            width=10
        )
        self.shadow_color_button.pack(side=tk.LEFT)
        
        ttk.Label(shadow_color_frame, textvariable=self.shadow_color).pack(side=tk.LEFT, padx=(10, 0))
        
        # 描边设置
        ttk.Checkbutton(
            self.advanced_frame,
            text="启用描边",
            variable=self.stroke_enabled,
            command=self.on_stroke_toggle
        ).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(5, 3), padx=(10, 0))
        
        # 描边宽度
        ttk.Label(self.advanced_frame, text="描边宽度:").grid(row=5, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        stroke_width_scale = ttk.Scale(
            self.advanced_frame,
            from_=1,
            to=10,
            variable=self.stroke_width,
            orient=tk.HORIZONTAL,
            command=self.on_setting_change
        )
        stroke_width_scale.grid(row=5, column=1, sticky=tk.EW, pady=1, padx=(5, 0))
        
        stroke_width_label = ttk.Label(self.advanced_frame, text="2px")
        stroke_width_label.grid(row=5, column=2, pady=1, padx=(5, 0))
        
        # 绑定描边宽度显示更新
        def update_stroke_width_label(*args):
            stroke_width_label.config(text=f"{self.stroke_width.get()}px")
        self.stroke_width.trace('w', update_stroke_width_label)
        
        # 描边颜色
        ttk.Label(self.advanced_frame, text="描边颜色:").grid(row=6, column=0, sticky=tk.W, pady=1, padx=(10, 0))
        
        stroke_color_frame = ttk.Frame(self.advanced_frame)
        stroke_color_frame.grid(row=6, column=1, columnspan=2, sticky=tk.EW, pady=1, padx=(5, 0))
        
        self.stroke_color_button = tk.Button(
            stroke_color_frame,
            text="选择颜色",
            bg="black",
            fg="white",
            command=self.choose_stroke_color,
            width=10
        )
        self.stroke_color_button.pack(side=tk.LEFT)
        
        ttk.Label(stroke_color_frame, textvariable=self.stroke_color).pack(side=tk.LEFT, padx=(10, 0))
        
        # 配置列权重
        self.advanced_frame.columnconfigure(1, weight=1)
        
        # 初始化阴影和描边控件状态
        self.on_shadow_toggle()
        self.on_stroke_toggle()
    
    def setup_bindings(self):
        """设置事件绑定"""
        # 绑定变量变化事件
        self.text_content.trace('w', self.on_setting_change)
        self.image_path.trace('w', self.on_setting_change)
        self.offset_x.trace('w', self.on_setting_change)
        self.offset_y.trace('w', self.on_setting_change)
        self.rotation_angle.trace('w', self.on_setting_change)
        self.shadow_offset_x.trace('w', self.on_setting_change)
        self.shadow_offset_y.trace('w', self.on_setting_change)
    
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
        
        # 清空所有tabs
        for tab in self.notebook.tabs():
            self.notebook.forget(tab)
        
        # 根据水印类型添加相应的tabs
        if watermark_type == "text":
            # 文本水印：文本设置、位置设置、高级设置
            self.notebook.add(self.text_frame, text="文本设置")
            self.notebook.add(self.position_frame, text="位置设置")
            self.notebook.add(self.advanced_frame, text="高级设置")
        else:
            # 图片水印：图片设置、位置设置
            self.notebook.add(self.image_frame, text="图片设置")
            self.notebook.add(self.position_frame, text="位置设置")
        
        # 选择第一个tab
        if self.notebook.tabs():
            self.notebook.select(0)
        
        self.on_setting_change()
    
    def on_setting_change(self, *args):
        """设置变化事件"""
        # 通知预览面板更新
        if hasattr(self.app, 'preview_panel'):
            self.app.preview_panel.refresh_preview()
    
    def on_shadow_toggle(self):
        """阴影启用/禁用切换"""
        enabled = self.shadow_enabled.get()
        
        # 启用/禁用阴影相关控件
        state = tk.NORMAL if enabled else tk.DISABLED
        
        # 查找阴影设置框架并设置其子控件状态
        for child in self.advanced_frame.winfo_children():
            if isinstance(child, ttk.LabelFrame) and "阴影效果" in str(child.cget('text')):
                for shadow_child in child.winfo_children():
                    if not isinstance(shadow_child, ttk.Checkbutton):  # 不禁用复选框本身
                        self.set_widget_state(shadow_child, state)
        
        self.on_setting_change()
    
    def on_stroke_toggle(self):
        """描边启用/禁用切换"""
        enabled = self.stroke_enabled.get()
        
        # 启用/禁用描边相关控件
        state = tk.NORMAL if enabled else tk.DISABLED
        
        # 查找描边设置相关控件并设置状态
        for child in self.advanced_frame.winfo_children():
            if isinstance(child, ttk.Label):
                text = child.cget('text')
                if text in ["描边宽度:", "描边颜色:"]:
                    child.configure(state=state)
            elif isinstance(child, ttk.Scale):
                # 检查是否是描边宽度滑块
                if child.cget('from') == 1 and child.cget('to') == 10:
                    child.configure(state=state)
            elif isinstance(child, ttk.Frame):
                # 检查是否是描边颜色框架
                for frame_child in child.winfo_children():
                    if isinstance(frame_child, tk.Button) and frame_child.cget('command') == self.choose_stroke_color:
                        self.set_widget_state(child, state)
                        break
        
        self.on_setting_change()
    
    def choose_color(self):
        """选择颜色"""
        # 获取当前颜色，如果是默认的黑色，使用一个更明显的初始颜色
        current_color = self.text_color.get()
        if current_color == "#000000":
            initial_color = "#333333"  # 使用深灰色作为初始颜色，更容易看到
        else:
            initial_color = current_color
            
        color = colorchooser.askcolor(
            color=initial_color,
            title="选择文本颜色"
        )
        
        if color[1]:  # 用户选择了颜色
            self.text_color.set(color[1])
            # 更新按钮颜色，确保文本颜色与背景形成对比
            bg_color = color[1]
            # 计算亮度来决定文本颜色
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = "white" if brightness < 128 else "black"
            
            self.color_button.config(bg=bg_color, fg=text_color)
            self.on_setting_change()
    
    def choose_shadow_color(self):
        """选择阴影颜色"""
        # 获取当前颜色，如果是默认的黑色，使用一个更明显的初始颜色
        current_color = self.shadow_color.get()
        if current_color == "#000000":
            initial_color = "#333333"  # 使用深灰色作为初始颜色，更容易看到
        else:
            initial_color = current_color
            
        color = colorchooser.askcolor(
            color=initial_color,
            title="选择阴影颜色"
        )
        
        if color[1]:  # 用户选择了颜色
            self.shadow_color.set(color[1])
            # 更新按钮颜色，确保文本颜色与背景形成对比
            bg_color = color[1]
            # 计算亮度来决定文本颜色
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = "white" if brightness < 128 else "black"
            
            self.shadow_color_button.config(bg=bg_color, fg=text_color)
            self.on_setting_change()
    
    def choose_stroke_color(self):
        """选择描边颜色"""
        # 获取当前颜色，如果是默认的黑色，使用一个更明显的初始颜色
        current_color = self.stroke_color.get()
        if current_color == "#000000":
            initial_color = "#333333"  # 使用深灰色作为初始颜色，更容易看到
        else:
            initial_color = current_color
            
        color = colorchooser.askcolor(
            color=initial_color,
            title="选择描边颜色"
        )
        
        if color[1]:  # 用户选择了颜色
            self.stroke_color.set(color[1])
            # 更新按钮颜色，确保文本颜色与背景形成对比
            bg_color = color[1]
            # 计算亮度来决定文本颜色
            r = int(bg_color[1:3], 16)
            g = int(bg_color[3:5], 16)
            b = int(bg_color[5:7], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            text_color = "white" if brightness < 128 else "black"
            
            self.stroke_color_button.config(bg=bg_color, fg=text_color)
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
            'font_bold': self.font_bold.get(),
            'font_italic': self.font_italic.get(),
            'color': self.text_color.get(),
            'opacity': self.opacity.get(),
            'position': self.position.get(),
            'image_path': self.image_path.get(),
            'scale': self.image_scale.get(),
            'offset_x': self.offset_x.get(),
            'offset_y': self.offset_y.get(),
            'rotation_angle': self.rotation_angle.get(),
            'shadow_enabled': self.shadow_enabled.get(),
            'shadow_offset_x': self.shadow_offset_x.get(),
            'shadow_offset_y': self.shadow_offset_y.get(),
            'shadow_blur': self.shadow_blur.get(),
            'shadow_color': self.shadow_color.get(),
            'stroke_enabled': self.stroke_enabled.get(),
            'stroke_width': self.stroke_width.get(),
            'stroke_color': self.stroke_color.get()
        }
    
    def set_settings(self, settings: Dict[str, Any]):
        """设置水印参数"""
        self.watermark_enabled.set(settings.get('enabled', True))
        self.watermark_type.set(settings.get('type', 'text'))
        self.text_content.set(settings.get('text', '水印'))
        self.font_size.set(settings.get('font_size', 36))
        self.font_family.set(settings.get('font_family', '苹方 (PingFang SC)'))
        self.font_bold.set(settings.get('font_bold', False))
        self.font_italic.set(settings.get('font_italic', False))
        self.text_color.set(settings.get('color', '#FFFFFF'))
        self.opacity.set(settings.get('opacity', 80))
        self.position.set(settings.get('position', 'bottom_right'))
        self.image_path.set(settings.get('image_path', ''))
        self.image_scale.set(settings.get('scale', 0.2))
        self.offset_x.set(settings.get('offset_x', 0))
        self.offset_y.set(settings.get('offset_y', 0))
        self.rotation_angle.set(settings.get('rotation_angle', 0))
        self.shadow_enabled.set(settings.get('shadow_enabled', False))
        self.shadow_offset_x.set(settings.get('shadow_offset_x', 2))
        self.shadow_offset_y.set(settings.get('shadow_offset_y', 2))
        self.shadow_blur.set(settings.get('shadow_blur', 4))
        self.shadow_color.set(settings.get('shadow_color', '#000000'))
        self.stroke_enabled.set(settings.get('stroke_enabled', False))
        self.stroke_width.set(settings.get('stroke_width', 2))
        self.stroke_color.set(settings.get('stroke_color', '#000000'))
        
        # 更新颜色按钮
        self.color_button.config(bg=self.text_color.get())
        if hasattr(self, 'shadow_color_button'):
            self.shadow_color_button.config(bg=self.shadow_color.get())
        if hasattr(self, 'stroke_color_button'):
            self.stroke_color_button.config(bg=self.stroke_color.get())
        
        # 更新界面状态
        self.on_watermark_toggle()
        self.on_type_change()
        if hasattr(self, 'shadow_enabled'):
            self.on_shadow_toggle()
    
    def reset_settings(self):
        """重置设置"""
        if messagebox.askyesno("确认", "确定要重置所有水印设置吗？"):
            default_settings = {
                'enabled': True,
                'type': 'text',
                'text': '水印',
                'font_size': 36,
                'font_bold': False,
                'font_italic': False,
                'color': '#FFFFFF',
                'opacity': 80,
                'position': 'bottom_right',
                'image_path': '',
                'scale': 0.2,
                'offset_x': 0,
                'offset_y': 0,
                'rotation_angle': 0,
                'shadow_enabled': False,
                'shadow_offset_x': 2,
                'shadow_offset_y': 2,
                'shadow_blur': 4,
                'shadow_color': '#000000',
                'stroke_enabled': False,
                'stroke_width': 2,
                'stroke_color': '#000000'
            }
            self.set_settings(default_settings)
    
    def save_template(self):
        """保存模板"""
        try:
            # 弹出对话框让用户输入模板名称
            template_name = tk.simpledialog.askstring(
                "保存模板",
                "请输入模板名称:",
                parent=self
            )
            
            if not template_name:
                return
                
            # 获取当前设置
            settings = self.get_settings()
            
            # 保存模板
            from ...config import Settings
            config = Settings()
            
            if config.save_template(template_name, settings):
                messagebox.showinfo("成功", f"模板 '{template_name}' 保存成功！")
            else:
                messagebox.showerror("错误", "模板保存失败！")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存模板时发生错误: {e}")
    
    def load_template(self):
        """加载模板"""
        try:
            from ...config import Settings
            config = Settings()
            
            # 获取可用模板列表
            templates = config.list_templates()
            
            if not templates:
                messagebox.showinfo("提示", "没有可用的模板")
                return
            
            # 创建模板选择对话框
            dialog = TemplateSelectDialog(self, templates, config)
            template_data = dialog.show()
            
            if template_data:
                # 加载模板设置
                self.set_settings(template_data)
                messagebox.showinfo("成功", "模板加载成功！")
                
        except Exception as e:
            messagebox.showerror("错误", f"加载模板时发生错误: {e}")
    
class TemplateSelectDialog:
    """模板选择对话框"""
    
    def __init__(self, parent, templates, config):
        self.parent = parent
        self.templates = templates
        self.config = config
        self.result = None
        
    def show(self):
        """显示对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("选择模板")
        self.dialog.geometry("400x300")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 模板列表
        frame = ttk.Frame(self.dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="选择要加载的模板:").pack(anchor=tk.W, pady=(0, 5))
        
        # 创建列表框
        listbox_frame = ttk.Frame(frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.listbox = tk.Listbox(listbox_frame)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 添加模板到列表
        for template in self.templates:
            self.listbox.insert(tk.END, template)
        
        # 按钮
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="删除", command=self.delete_selected).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="加载", command=self.load_selected).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT)
        
        # 等待对话框关闭
        self.dialog.wait_window()
        return self.result
    
    def load_selected(self):
        """加载选中的模板"""
        selection = self.listbox.curselection()
        if selection:
            template_name = self.templates[selection[0]]
            self.result = self.config.load_template(template_name)
        self.dialog.destroy()
    
    def delete_selected(self):
        """删除选中的模板"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的模板")
            return
        
        template_name = self.templates[selection[0]]
        
        if messagebox.askyesno("确认删除", f"确定要删除模板 '{template_name}' 吗？"):
            if self.config.delete_template(template_name):
                messagebox.showinfo("成功", "模板删除成功！")
                # 从列表中移除
                self.listbox.delete(selection[0])
                self.templates.remove(template_name)
            else:
                messagebox.showerror("错误", "模板删除失败！")