#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出面板
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from typing import Dict, Any, Optional, List, Callable
from PIL import Image

from ...core import ImageProcessor, WatermarkManager, FileManager
from ...utils import show_error, show_info, ProgressTracker


class ExportPanel(ttk.LabelFrame):
    """导出面板类"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="导出设置", padding=10)
        self.app = app
        
        # 导出设置变量
        self.output_format = tk.StringVar(value="PNG")
        self.output_folder = tk.StringVar()
        self.naming_rule = tk.StringVar(value="original")
        self.custom_prefix = tk.StringVar(value="wm_")
        self.custom_suffix = tk.StringVar(value="_watermarked")
        self.jpeg_quality = tk.IntVar(value=95)
        self.resize_enabled = tk.BooleanVar(value=False)
        self.resize_width = tk.IntVar(value=1920)
        self.resize_height = tk.IntVar(value=1080)
        self.resize_mode = tk.StringVar(value="width")
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 输出格式
        format_frame = ttk.Frame(self)
        format_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(format_frame, text="输出格式:").pack(side=tk.LEFT)
        
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.output_format,
            values=["PNG", "JPEG"],
            state="readonly",
            width=10
        )
        format_combo.pack(side=tk.LEFT, padx=(5, 0))
        format_combo.bind('<<ComboboxSelected>>', self.on_format_change)
        
        # 输出文件夹
        folder_frame = ttk.Frame(self)
        folder_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(folder_frame, text="输出文件夹:").pack(side=tk.LEFT)
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.output_folder, state="readonly")
        folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        
        ttk.Button(
            folder_frame,
            text="浏览",
            command=self.browse_output_folder,
            width=8
        ).pack(side=tk.RIGHT)
        
        # 创建并排的框架用于文件命名和尺寸调整
        settings_row_frame = ttk.Frame(self)
        settings_row_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 文件命名规则 - 左侧
        naming_frame = ttk.LabelFrame(settings_row_frame, text="文件命名", padding=5)
        naming_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Radiobutton(
            naming_frame,
            text="保留原文件名",
            variable=self.naming_rule,
            value="original"
        ).grid(row=0, column=0, sticky=tk.W, pady=1)
        
        ttk.Radiobutton(
            naming_frame,
            text="添加前缀:",
            variable=self.naming_rule,
            value="prefix"
        ).grid(row=1, column=0, sticky=tk.W, pady=1)
        
        ttk.Entry(
            naming_frame,
            textvariable=self.custom_prefix,
            width=12
        ).grid(row=1, column=1, sticky=tk.W, padx=(5, 0), pady=1)
        
        ttk.Radiobutton(
            naming_frame,
            text="添加后缀:",
            variable=self.naming_rule,
            value="suffix"
        ).grid(row=2, column=0, sticky=tk.W, pady=1)
        
        ttk.Entry(
            naming_frame,
            textvariable=self.custom_suffix,
            width=12
        ).grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=1)
        
        # 尺寸调整设置 - 右侧
        resize_frame = ttk.LabelFrame(settings_row_frame, text="尺寸调整", padding=5)
        resize_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # JPEG质量设置 - 单独一行，更紧凑
        self.quality_frame = ttk.LabelFrame(self, text="JPEG质量", padding=3)
        self.quality_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Label(self.quality_frame, text="压缩质量:").grid(row=0, column=0, sticky=tk.W, pady=1)
        
        quality_scale = ttk.Scale(
            self.quality_frame,
            from_=10,
            to=100,
            variable=self.jpeg_quality,
            orient=tk.HORIZONTAL
        )
        quality_scale.grid(row=0, column=1, sticky=tk.EW, pady=1, padx=(5, 0))
        
        self.quality_label = ttk.Label(self.quality_frame, text="95%")
        self.quality_label.grid(row=0, column=2, pady=1, padx=(5, 0))
        
        # 绑定质量显示更新
        def update_quality_label(*args):
            self.quality_label.config(text=f"{self.jpeg_quality.get()}%")
        self.jpeg_quality.trace('w', update_quality_label)
        
        self.quality_frame.columnconfigure(1, weight=1)
        
        ttk.Checkbutton(
            resize_frame,
            text="启用尺寸调整",
            variable=self.resize_enabled,
            command=self.on_resize_toggle
        ).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=1)
        
        ttk.Label(resize_frame, text="模式:").grid(row=1, column=0, sticky=tk.W, pady=1)
        
        mode_combo = ttk.Combobox(
            resize_frame,
            textvariable=self.resize_mode,
            values=["width", "height", "both"],
            state="readonly",
            width=8
        )
        mode_combo.grid(row=1, column=1, sticky=tk.W, pady=1, padx=(5, 0))
        
        ttk.Label(resize_frame, text="宽度:").grid(row=2, column=0, sticky=tk.W, pady=1)
        self.width_spinbox = ttk.Spinbox(
            resize_frame,
            from_=100,
            to=10000,
            textvariable=self.resize_width,
            width=8
        )
        self.width_spinbox.grid(row=2, column=1, sticky=tk.W, pady=1, padx=(5, 0))
        
        ttk.Label(resize_frame, text="高度:").grid(row=3, column=0, sticky=tk.W, pady=1)
        self.height_spinbox = ttk.Spinbox(
            resize_frame,
            from_=100,
            to=10000,
            textvariable=self.resize_height,
            width=8
        )
        self.height_spinbox.grid(row=3, column=1, sticky=tk.W, pady=1, padx=(5, 0))
        
        # 导出按钮和进度条 - 更紧凑的布局
        export_frame = ttk.Frame(self)
        export_frame.pack(fill=tk.X, pady=(8, 0))
        
        self.export_button = ttk.Button(
            export_frame,
            text="开始导出",
            command=self.start_export,
            style="Accent.TButton"
        )
        self.export_button.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            export_frame,
            variable=self.progress_var,
            maximum=100
        )
        
        # 状态标签
        self.status_label = ttk.Label(self, text="")
        
        # 初始化界面状态
        self.on_format_change()
        self.on_resize_toggle()
    
    def on_format_change(self, event=None):
        """输出格式变化事件"""
        format_type = self.output_format.get()
        
        if format_type == "JPEG":
            self.quality_frame.pack(fill=tk.X, pady=(0, 10), before=self.winfo_children()[-3])
        else:
            self.quality_frame.pack_forget()
    
    def on_resize_toggle(self):
        """尺寸调整切换事件"""
        enabled = self.resize_enabled.get()
        state = tk.NORMAL if enabled else tk.DISABLED
        
        try:
            self.width_spinbox.configure(state=state)
            self.height_spinbox.configure(state=state)
        except:
            pass
    
    def browse_output_folder(self):
        """浏览输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)
    
    def generate_output_filename(self, original_path: str) -> str:
        """生成输出文件名"""
        base_name = os.path.splitext(os.path.basename(original_path))[0]
        extension = f".{self.output_format.get().lower()}"
        
        if extension == ".jpeg":
            extension = ".jpg"
        
        naming_rule = self.naming_rule.get()
        
        if naming_rule == "prefix":
            new_name = f"{self.custom_prefix.get()}{base_name}{extension}"
        elif naming_rule == "suffix":
            new_name = f"{base_name}{self.custom_suffix.get()}{extension}"
        else:  # original
            new_name = f"{base_name}{extension}"
        
        return new_name
    
    def validate_settings(self) -> bool:
        """验证导出设置"""
        if not self.output_folder.get():
            messagebox.showerror("错误", "请选择输出文件夹")
            return False
        
        if not os.path.exists(self.output_folder.get()):
            messagebox.showerror("错误", "输出文件夹不存在")
            return False
        
        # 检查是否有图片
        if not self.app.image_list_panel.has_images():
            messagebox.showerror("错误", "请先导入图片文件")
            return False
        
        # 检查输出文件夹是否与原文件夹相同
        image_files = self.app.image_list_panel.get_all_images()
        output_folder = os.path.abspath(self.output_folder.get())
        
        for image_file in image_files:
            image_folder = os.path.abspath(os.path.dirname(image_file))
            if image_folder == output_folder:
                if not messagebox.askyesno(
                    "警告", 
                    "输出文件夹与原文件夹相同，可能会覆盖原文件。是否继续？"
                ):
                    return False
                break
        
        return True
    
    def start_export(self):
        """开始导出"""
        if not self.validate_settings():
            return
        
        # 禁用导出按钮
        self.export_button.configure(state=tk.DISABLED, text="导出中...")
        
        # 显示进度条
        self.progress_bar.pack(fill=tk.X, pady=(5, 0))
        self.status_label.pack(fill=tk.X, pady=(5, 0))
        
        # 在后台线程中执行导出
        export_thread = threading.Thread(target=self.export_images)
        export_thread.daemon = True
        export_thread.start()
    
    def export_images(self):
        """导出图片（后台线程）"""
        try:
            image_files = self.app.image_list_panel.get_all_images()
            total_files = len(image_files)
            success_count = 0
            
            for i, image_file in enumerate(image_files):
                try:
                    # 更新状态
                    self.update_progress(
                        (i / total_files) * 100,
                        f"正在处理: {os.path.basename(image_file)}"
                    )
                    
                    # 处理图片
                    self.process_single_image(image_file)
                    success_count += 1
                    
                except Exception as e:
                    print(f"处理图片失败 {image_file}: {e}")
                    continue
            
            # 完成
            self.update_progress(100, f"导出完成: {success_count}/{total_files} 张图片")
            
            # 显示完成消息
            self.app.root.after(
                0,
                lambda: messagebox.showinfo(
                    "导出完成",
                    f"成功导出 {success_count}/{total_files} 张图片到:\n{self.output_folder.get()}"
                )
            )
            
        except Exception as e:
            self.app.root.after(
                0,
                lambda: messagebox.showerror("导出失败", f"导出过程中发生错误: {e}")
            )
        
        finally:
            # 恢复界面
            self.app.root.after(0, self.reset_export_ui)
    
    def process_single_image(self, image_file: str):
        """处理单张图片"""
        # 打开原始图片
        with Image.open(image_file) as img:
            # 应用水印
            processed_img = self.apply_watermark_to_image(img)
            
            # 调整尺寸
            if self.resize_enabled.get():
                processed_img = self.resize_image(processed_img)
            
            # 生成输出文件名
            output_filename = self.generate_output_filename(image_file)
            output_path = os.path.join(self.output_folder.get(), output_filename)
            
            # 保存图片
            save_kwargs = {}
            if self.output_format.get() == "JPEG":
                # 转换为RGB模式（JPEG不支持透明度）
                if processed_img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', processed_img.size, (255, 255, 255))
                    background.paste(processed_img, mask=processed_img.split()[-1] if processed_img.mode == 'RGBA' else None)
                    processed_img = background
                
                save_kwargs['quality'] = self.jpeg_quality.get()
                save_kwargs['optimize'] = True
            
            processed_img.save(output_path, **save_kwargs)
    
    def apply_watermark_to_image(self, img: Image.Image) -> Image.Image:
        """为图片应用水印"""
        # 复制图片
        result_img = img.copy()
        
        # 获取水印设置
        if hasattr(self.app, 'watermark_panel'):
            watermark_settings = self.app.watermark_panel.get_settings()
            
            if watermark_settings['enabled']:
                # 这里重用预览面板的水印应用逻辑
                # 临时设置原始图片
                original_image = self.app.preview_panel.original_image
                self.app.preview_panel.original_image = result_img
                
                # 应用水印
                self.app.preview_panel.apply_watermark()
                result_img = self.app.preview_panel.current_image.copy()
                
                # 恢复原始图片
                self.app.preview_panel.original_image = original_image
        
        return result_img
    
    def resize_image(self, img: Image.Image) -> Image.Image:
        """调整图片尺寸"""
        mode = self.resize_mode.get()
        target_width = self.resize_width.get()
        target_height = self.resize_height.get()
        
        original_width, original_height = img.size
        
        if mode == "width":
            # 按宽度调整，保持比例
            ratio = target_width / original_width
            new_height = int(original_height * ratio)
            new_size = (target_width, new_height)
        elif mode == "height":
            # 按高度调整，保持比例
            ratio = target_height / original_height
            new_width = int(original_width * ratio)
            new_size = (new_width, target_height)
        else:  # both
            # 强制调整到指定尺寸
            new_size = (target_width, target_height)
        
        return img.resize(new_size, Image.Resampling.LANCZOS)
    
    def update_progress(self, value: float, status: str):
        """更新进度（线程安全）"""
        self.app.root.after(0, lambda: self._update_progress_ui(value, status))
    
    def _update_progress_ui(self, value: float, status: str):
        """更新进度界面"""
        self.progress_var.set(value)
        self.status_label.config(text=status)
        self.app.root.update_idletasks()
    
    def reset_export_ui(self):
        """重置导出界面"""
        self.export_button.configure(state=tk.NORMAL, text="开始导出")
        self.progress_bar.pack_forget()
        self.status_label.pack_forget()
        self.progress_var.set(0)