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
from .progress_dialog import ProgressDialog


class ExportPanel(ttk.LabelFrame):
    """导出面板类"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="导出设置", padding=10)
        self.app = app
        
        # 导出设置变量
        self.output_format = tk.StringVar(value="PNG")
        self.output_folder = tk.StringVar()
        self.naming_rule = tk.StringVar(value="suffix")  # 默认使用后缀，更安全
        self.custom_prefix = tk.StringVar(value="wm_")
        self.custom_suffix = tk.StringVar(value="_watermarked")
        self.jpeg_quality = tk.IntVar(value=95)
        self.resize_enabled = tk.BooleanVar(value=False)
        self.resize_width = tk.IntVar(value=1920)
        self.resize_height = tk.IntVar(value=1080)
        self.resize_mode = tk.StringVar(value="width")
        self.allow_overwrite = tk.BooleanVar(value=False)  # 新增：是否允许覆盖原文件
        
        # 进度弹窗
        self.progress_dialog = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 输出格式
        self.format_frame = ttk.Frame(self)
        self.format_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(self.format_frame, text="输出格式:").pack(side=tk.LEFT)
        
        format_combo = ttk.Combobox(
            self.format_frame,
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
        
        # 安全设置
        safety_frame = ttk.LabelFrame(self, text="安全设置", padding=3)
        safety_frame.pack(fill=tk.X, pady=(0, 8))
        
        ttk.Checkbutton(
            safety_frame,
            text="允许覆盖原文件（不推荐）",
            variable=self.allow_overwrite
        ).pack(anchor=tk.W)
        
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
        
        # 导出按钮容器
        button_frame = ttk.Frame(export_frame)
        button_frame.pack(fill=tk.X)
        
        self.export_button = ttk.Button(
            button_frame,
            text="开始导出",
            command=self.start_export,
            style="Accent.TButton"
        )
        self.export_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        # 批量导出按钮
        self.batch_export_button = ttk.Button(
            button_frame,
            text="批量导出",
            command=self.start_batch_export
        )
        self.batch_export_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 初始化界面状态
        self.on_format_change()
        self.on_resize_toggle()
    
    def on_format_change(self, event=None):
        """输出格式变化事件"""
        format_type = self.output_format.get()
        
        if format_type == "JPEG":
            # 先取消pack，然后重新pack到正确位置
            self.quality_frame.pack_forget()
            self.quality_frame.pack(fill=tk.X, pady=(0, 10), after=self.format_frame)
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
        
        # 检查覆盖风险
        image_files = self.app.image_list_panel.get_all_images()
        output_folder = os.path.abspath(self.output_folder.get())
        
        # 检查是否可能覆盖原文件
        potential_overwrites = []
        for image_file in image_files:
            image_folder = os.path.abspath(os.path.dirname(image_file))
            output_filename = self.generate_output_filename(image_file)
            output_path = os.path.join(output_folder, output_filename)
            
            # 检查是否会覆盖原文件
            if os.path.abspath(image_file) == os.path.abspath(output_path):
                potential_overwrites.append(os.path.basename(image_file))
            # 检查是否会覆盖其他已存在的文件
            elif os.path.exists(output_path):
                potential_overwrites.append(output_filename)
        
        if potential_overwrites:
            if not self.allow_overwrite.get():
                messagebox.showerror(
                    "安全警告", 
                    f"检测到以下文件可能被覆盖：\n\n" + 
                    "\n".join(potential_overwrites[:5]) + 
                    ("\n..." if len(potential_overwrites) > 5 else "") +
                    f"\n\n请更改输出文件夹或文件命名规则，\n或在安全设置中允许覆盖文件。"
                )
                return False
            else:
                if not messagebox.askyesno(
                    "覆盖确认", 
                    f"将覆盖 {len(potential_overwrites)} 个文件。\n确定要继续吗？"
                ):
                    return False
        
        return True
    
    def start_export(self):
        """开始导出当前选中的图片"""
        # 检查是否有选中的图片
        current_image = self.app.image_list_panel.get_current_image()
        if not current_image:
            messagebox.showwarning("警告", "请先选择要导出的图片")
            return
            
        if not self.validate_settings():
            return
        
        # 禁用导出按钮
        self.export_button.configure(state=tk.DISABLED, text="导出中...")
        self.batch_export_button.configure(state=tk.DISABLED)
        
        # 显示进度弹窗
        self.progress_dialog = ProgressDialog(
            self.app.root, 
            title="导出进度",
            width=400,
            height=150
        )
        self.progress_dialog.show()
        
        # 在后台线程中执行导出
        export_thread = threading.Thread(target=self.export_single_image, args=(current_image,))
        export_thread.daemon = True
        export_thread.start()
    
    def start_batch_export(self):
        """开始批量导出所有图片"""
        # 检查是否有图片
        image_files = self.app.image_list_panel.get_all_images()
        if not image_files:
            messagebox.showwarning("警告", "请先导入要导出的图片")
            return
            
        if not self.validate_settings():
            return
        
        # 禁用导出按钮
        self.export_button.configure(state=tk.DISABLED)
        self.batch_export_button.configure(state=tk.DISABLED, text="批量导出中...")
        
        # 显示进度弹窗
        self.progress_dialog = ProgressDialog(
            self.app.root, 
            title="批量导出进度",
            width=400,
            height=150
        )
        self.progress_dialog.show()
        
        # 在后台线程中执行导出
        export_thread = threading.Thread(target=self.export_images)
        export_thread.daemon = True
        export_thread.start()
    
    def export_single_image(self, image_file):
        """导出单张图片（后台线程）"""
        try:
            # 更新状态
            self.update_progress(0, f"正在处理: {os.path.basename(image_file)}")
            
            # 处理图片
            self.process_single_image(image_file)
            
            # 完成
            self.update_progress(100, "导出完成")
            
            # 显示完成消息
            self.app.root.after(
                0,
                lambda: messagebox.showinfo(
                    "导出完成",
                    f"成功导出图片到:\n{self.output_folder.get()}"
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
        if self.progress_dialog:
            self.progress_dialog.update_progress(value, status)
    
    def reset_export_ui(self):
        """重置导出界面"""
        self.export_button.configure(state=tk.NORMAL, text="开始导出")
        self.batch_export_button.configure(state=tk.NORMAL, text="批量导出")
        
        # 关闭进度弹窗
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None