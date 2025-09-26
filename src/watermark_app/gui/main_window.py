#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口GUI界面
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from typing import List, Optional

# 导入核心模块
from ..core import ImageProcessor, WatermarkManager, FileManager
from ..config import Settings
from ..utils import show_error, show_info, center_window
from .components import ImageListPanel, PreviewPanel, WatermarkPanel, ExportPanel


class WatermarkApp:
    """主应用程序类"""
    
    def __init__(self, root: tk.Tk):
        """初始化应用程序"""
        self.root = root
        self.setup_window()
        self.setup_components()
        self.setup_layout()
        self.setup_menu()
        self.setup_bindings()
        
        # 初始化核心组件
        self.image_processor = ImageProcessor()
        self.watermark_manager = WatermarkManager()
        self.file_manager = FileManager()
        self.settings = Settings()
        
        # 加载默认设置
        self.load_default_settings()
    
    def setup_window(self):
        """设置主窗口"""
        self.root.title("图片水印工具 v1.0")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # 设置窗口图标（如果有的话）
        try:
            # 这里可以设置应用程序图标
            pass
        except:
            pass
        
        # 设置窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_components(self):
        """设置GUI组件"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root)
        
        # 创建左侧面板（图片列表和水印设置）
        self.left_panel = ttk.Frame(self.main_frame)
        
        # 创建右侧面板（预览和导出）
        self.right_panel = ttk.Frame(self.main_frame)
        
        # 创建各个功能面板
        self.image_list_panel = ImageListPanel(self.left_panel, self)
        self.watermark_panel = WatermarkPanel(self.left_panel, self)
        self.preview_panel = PreviewPanel(self.right_panel, self)
        self.export_panel = ExportPanel(self.right_panel, self)
        
        # 创建状态栏
        self.status_bar = ttk.Label(
            self.root, 
            text="就绪", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
    
    def setup_layout(self):
        """设置布局"""
        # 主框架布局
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 左右面板布局
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5))
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 左侧面板内容布局
        self.image_list_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.watermark_panel.pack(fill=tk.X, pady=(0, 5))
        
        # 右侧面板内容布局 - 增加预览区域高度，压缩导出区域
        self.preview_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        self.export_panel.pack(fill=tk.X, pady=(0, 0))
        
        # 状态栏布局
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_menu(self):
        """设置菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="导入图片...", command=self.import_images, accelerator="Cmd+O")
        file_menu.add_command(label="导入文件夹...", command=self.import_folder, accelerator="Cmd+Shift+O")
        file_menu.add_separator()
        file_menu.add_command(label="导出图片...", command=self.export_images, accelerator="Cmd+E")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.on_closing, accelerator="Cmd+Q")
        
        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        edit_menu.add_command(label="清空图片列表", command=self.clear_images)
        edit_menu.add_separator()
        edit_menu.add_command(label="重置水印设置", command=self.reset_watermark)
        
        # 水印菜单
        watermark_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="水印", menu=watermark_menu)
        watermark_menu.add_command(label="保存模板...", command=self.save_template)
        watermark_menu.add_command(label="加载模板...", command=self.load_template)
        watermark_menu.add_command(label="管理模板...", command=self.manage_templates)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_help)
        help_menu.add_command(label="关于", command=self.show_about)
    
    def setup_bindings(self):
        """设置键盘快捷键"""
        self.root.bind('<Command-o>', lambda e: self.import_images())
        self.root.bind('<Command-Shift-O>', lambda e: self.import_folder())
        self.root.bind('<Command-e>', lambda e: self.export_images())
        self.root.bind('<Command-q>', lambda e: self.on_closing())
    
    def load_default_settings(self):
        """加载默认设置"""
        try:
            self.settings.load_default()
            self.update_status("已加载默认设置")
        except Exception as e:
            self.update_status(f"加载设置失败: {e}")
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def import_images(self):
        """导入图片文件"""
        filetypes = [
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("PNG文件", "*.png"),
            ("BMP文件", "*.bmp"),
            ("TIFF文件", "*.tiff"),
            ("所有文件", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=filetypes
        )
        
        if files:
            self.image_list_panel.add_images(files)
            self.update_status(f"已导入 {len(files)} 个文件")
    
    def import_folder(self):
        """导入文件夹"""
        folder = filedialog.askdirectory(title="选择图片文件夹")
        if folder:
            self.image_list_panel.add_folder(folder)
            self.update_status(f"已导入文件夹: {folder}")
    
    def export_images(self):
        """导出图片"""
        if not self.image_list_panel.has_images():
            messagebox.showwarning("警告", "请先导入图片文件")
            return
        
        self.export_panel.start_export()
    
    def clear_images(self):
        """清空图片列表"""
        if messagebox.askyesno("确认", "确定要清空所有图片吗？"):
            self.image_list_panel.clear_images()
            self.preview_panel.clear_preview()
            self.update_status("已清空图片列表")
    
    def reset_watermark(self):
        """重置水印设置"""
        if messagebox.askyesno("确认", "确定要重置水印设置吗？"):
            self.watermark_panel.reset_settings()
            self.update_status("已重置水印设置")
    
    def save_template(self):
        """保存水印模板"""
        self.watermark_panel.save_template()
    
    def load_template(self):
        """加载水印模板"""
        self.watermark_panel.load_template()
    
    def manage_templates(self):
        """管理水印模板"""
        self.watermark_panel.manage_templates()
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
图片水印工具使用说明：

1. 导入图片：
   - 点击"导入图片"按钮或使用 Cmd+O 快捷键
   - 支持 JPEG、PNG、BMP、TIFF 格式
   - 可批量导入或导入整个文件夹

2. 设置水印：
   - 选择文本水印或图片水印
   - 调整位置、大小、透明度等参数
   - 实时预览效果

3. 导出图片：
   - 选择输出格式和质量
   - 设置文件命名规则
   - 指定输出文件夹

4. 模板管理：
   - 保存常用的水印设置为模板
   - 快速加载已保存的模板
        """
        messagebox.showinfo("使用说明", help_text)
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
图片水印工具 v1.0

一个简单易用的图片水印处理工具
适用于 macOS 系统

开发团队：Photo Watermark Team
        """
        messagebox.showinfo("关于", about_text)
    
    def on_closing(self):
        """窗口关闭事件"""
        try:
            # 保存当前设置
            self.settings.save_current()
        except:
            pass
        
        self.root.quit()
        self.root.destroy()