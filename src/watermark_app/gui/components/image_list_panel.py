#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片列表面板
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import List, Optional
from PIL import Image, ImageTk

from ...utils import show_error, format_file_size


class ImageListPanel(ttk.LabelFrame):
    """图片列表面板类"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="图片列表", padding=10)
        self.app = app
        self.image_files = []
        self.current_selection = None
        self.thumbnails = {}
        
        self.setup_ui()
        self.setup_bindings()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建工具栏
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 导入按钮
        ttk.Button(
            toolbar, 
            text="导入图片", 
            command=self.app.import_images
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar, 
            text="导入文件夹", 
            command=self.app.import_folder
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            toolbar, 
            text="清空", 
            command=self.clear_images
        ).pack(side=tk.RIGHT)
        
        # 创建列表框架
        list_frame = ttk.Frame(self)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建列表框和滚动条
        self.listbox = tk.Listbox(
            list_frame,
            selectmode=tk.SINGLE,
            height=10
        )
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        
        # 布局
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 信息标签
        self.info_label = ttk.Label(self, text="未选择图片")
        self.info_label.pack(fill=tk.X, pady=(10, 0))
    
    def setup_bindings(self):
        """设置事件绑定"""
        self.listbox.bind('<<ListboxSelect>>', self.on_selection_change)
        self.listbox.bind('<Double-Button-1>', self.on_double_click)
    
    def add_images(self, file_paths: List[str]):
        """添加图片文件"""
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        added_count = 0
        
        for file_path in file_paths:
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in supported_formats:
                    if file_path not in self.image_files:
                        self.image_files.append(file_path)
                        filename = os.path.basename(file_path)
                        self.listbox.insert(tk.END, filename)
                        added_count += 1
                        
                        # 生成缩略图
                        self.generate_thumbnail(file_path)
        
        if added_count > 0:
            self.update_info()
            # 选择第一个图片
            if self.listbox.size() == added_count:
                self.listbox.selection_set(0)
                self.on_selection_change(None)
        
        return added_count
    
    def add_folder(self, folder_path: str):
        """添加文件夹中的图片"""
        if not os.path.isdir(folder_path):
            return 0
        
        image_files = []
        supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_formats:
                    image_files.append(os.path.join(root, file))
        
        return self.add_images(image_files)
    
    def generate_thumbnail(self, file_path: str):
        """生成缩略图"""
        try:
            with Image.open(file_path) as img:
                # 创建缩略图
                img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                # 转换为PhotoImage
                photo = ImageTk.PhotoImage(img)
                self.thumbnails[file_path] = photo
        except Exception as e:
            print(f"生成缩略图失败 {file_path}: {e}")
    
    def on_selection_change(self, event):
        """选择变化事件"""
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.current_selection = index
            file_path = self.image_files[index]
            
            # 更新信息显示
            self.update_selection_info(file_path)
            
            # 通知预览面板更新
            if hasattr(self.app, 'preview_panel'):
                self.app.preview_panel.load_image(file_path)
    
    def on_double_click(self, event):
        """双击事件"""
        # 可以在这里添加双击打开图片的功能
        pass
    
    def update_selection_info(self, file_path: str):
        """更新选择的图片信息"""
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                file_size = os.path.getsize(file_path)
                size_mb = file_size / (1024 * 1024)
                
                info = f"尺寸: {width}x{height} | 大小: {size_mb:.2f}MB"
                self.info_label.config(text=info)
        except Exception as e:
            self.info_label.config(text=f"读取信息失败: {e}")
    
    def update_info(self):
        """更新总体信息"""
        count = len(self.image_files)
        if count == 0:
            self.info_label.config(text="未选择图片")
        elif self.current_selection is None:
            self.info_label.config(text=f"共 {count} 张图片")
    
    def clear_images(self):
        """清空图片列表"""
        if self.image_files and messagebox.askyesno("确认", "确定要清空所有图片吗？"):
            self.image_files.clear()
            self.thumbnails.clear()
            self.listbox.delete(0, tk.END)
            self.current_selection = None
            self.update_info()
            
            # 清空预览
            if hasattr(self.app, 'preview_panel'):
                self.app.preview_panel.clear_preview()
    
    def has_images(self) -> bool:
        """检查是否有图片"""
        return len(self.image_files) > 0
    
    def get_current_image(self) -> Optional[str]:
        """获取当前选择的图片路径"""
        if self.current_selection is not None and self.current_selection < len(self.image_files):
            return self.image_files[self.current_selection]
        return None
    
    def get_all_images(self) -> List[str]:
        """获取所有图片路径"""
        return self.image_files.copy()
    
    def remove_current_image(self):
        """移除当前选择的图片"""
        if self.current_selection is not None:
            file_path = self.image_files[self.current_selection]
            self.image_files.pop(self.current_selection)
            self.listbox.delete(self.current_selection)
            
            # 清理缩略图
            if file_path in self.thumbnails:
                del self.thumbnails[file_path]
            
            # 更新选择
            if self.image_files:
                new_index = min(self.current_selection, len(self.image_files) - 1)
                self.listbox.selection_set(new_index)
                self.current_selection = new_index
                self.on_selection_change(None)
            else:
                self.current_selection = None
                self.update_info()
                if hasattr(self.app, 'preview_panel'):
                    self.app.preview_panel.clear_preview()