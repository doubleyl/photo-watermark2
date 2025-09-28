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

try:
    from tkinterdnd2 import TkinterDnD
except ImportError:
    TkinterDnD = None

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
        
        # 左侧面板内容布局 - 限制图片列表高度，确保设置面板可见
        self.image_list_panel.pack(fill=tk.BOTH, expand=False, pady=(0, 5))
        self.watermark_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
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
        """加载默认设置或上次保存的设置"""
        try:
            # 尝试加载上次的设置
            last_settings = self.settings.load_default()
            
            if last_settings:
                # 如果有上次的设置，应用到界面
                if 'settings' in last_settings:
                    # 这是完整的会话数据
                    watermark_settings = last_settings['settings']
                    self.settings.apply_watermark_settings(self, watermark_settings)
                    self.update_status("已加载上次会话设置")
                else:
                    # 这是模板数据
                    self.settings.apply_watermark_settings(self, last_settings)
                    self.update_status("已加载默认模板设置")
            else:
                # 没有保存的设置，使用程序默认值
                self.update_status("使用程序默认设置")
                
        except Exception as e:
            self.update_status(f"加载设置失败: {e}")
            print(f"加载设置详细错误: {e}")
    
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def import_images(self):
        """导入图片文件"""
        filetypes = [
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif *.webp *.gif *.ico"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("PNG文件", "*.png"),
            ("BMP文件", "*.bmp"),
            ("TIFF文件", "*.tiff *.tif"),
            ("WebP文件", "*.webp"),
            ("GIF文件", "*.gif"),
            ("所有文件", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="选择图片文件（支持多选）",
            filetypes=filetypes,
            initialdir=os.path.expanduser("~/Pictures")  # 默认打开图片文件夹
        )
        
        if files:
            # 过滤有效的图片文件
            valid_files = self.filter_valid_images(files)
            if valid_files:
                added_count = self.image_list_panel.add_images(valid_files)
                if added_count > 0:
                    self.update_status(f"成功导入 {added_count} 个图片文件")
                    if len(valid_files) != len(files):
                        invalid_count = len(files) - len(valid_files)
                        messagebox.showwarning("警告", f"已导入 {added_count} 个有效图片文件，跳过了 {invalid_count} 个无效文件")
                else:
                    self.update_status("所选文件已在列表中")
            else:
                messagebox.showwarning("警告", "所选文件中没有有效的图片文件")
    
    def import_folder(self):
        """导入文件夹"""
        folder = filedialog.askdirectory(
            title="选择图片文件夹",
            initialdir=os.path.expanduser("~/Pictures")
        )
        if folder:
            # 询问是否包含子文件夹
            include_subfolders = messagebox.askyesno(
                "搜索选项", 
                "是否包含子文件夹中的图片？\n\n是：搜索所有子文件夹\n否：仅搜索当前文件夹",
                default='yes'
            )
            
            added_count = self.image_list_panel.add_folder(folder, include_subfolders)
            if added_count > 0:
                self.update_status(f"从文件夹导入了 {added_count} 个图片文件")
            else:
                self.update_status("文件夹中没有找到新的图片文件")
    
    def filter_valid_images(self, files):
        """过滤有效的图片文件"""
        from PIL import Image
        
        valid_files = []
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif', '.ico'}
        
        for file_path in files:
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in supported_formats:
                    # 尝试用PIL打开文件验证是否为有效图片
                    try:
                        with Image.open(file_path) as img:
                            img.verify()  # 验证图片完整性
                        valid_files.append(file_path)
                    except Exception:
                        # 如果无法打开或验证失败，跳过该文件
                        continue
        
        return valid_files
    
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
            # 获取并保存当前水印设置
            current_watermark_settings = self.settings.get_current_watermark_settings(self)
            if current_watermark_settings:
                self.settings.save_current(current_watermark_settings)
        except Exception as e:
            print(f"保存设置失败: {e}")
        
        self.root.quit()
        self.root.destroy()