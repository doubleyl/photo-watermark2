"""
批量处理面板
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from PIL import Image

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:
    DND_FILES = None
    TkinterDnD = None

from ...core.watermark_manager import WatermarkManager


class BatchPanel(ttk.LabelFrame):
    """批量处理面板 - 可折叠的紧凑面板"""
    
    def __init__(self, parent, app):
        super().__init__(parent, text="批量处理", padding=5)
        self.parent = parent
        self.app = app
        self.watermark_manager = WatermarkManager()
        
        # 批量处理设置
        self.input_files = []
        self.output_folder = tk.StringVar(value=os.path.expanduser("~/Desktop"))
        self.processing = False
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="就绪")
        
        # 折叠状态
        self.is_expanded = tk.BooleanVar(value=False)
        self.content_frame = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建顶部控制区域（始终显示）
        self.setup_header_controls()
        
        # 创建可折叠的内容区域
        self.content_frame = ttk.Frame(self)
        
        # 设置内容区域（默认隐藏）
        self.setup_content_area()
        
        # 初始状态为折叠
        self.toggle_content()
        
        # 初始化按钮状态
        self.update_file_count()
        
        # 设置拖拽支持
        self.setup_drag_drop()
    
    def setup_header_controls(self):
        """设置头部控制区域"""
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 文件选择按钮
        ttk.Button(header_frame, text="选择图片", 
                  command=self.select_files, width=10).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="选择文件夹", 
                  command=self.select_folder, width=10).pack(side=tk.LEFT, padx=(5, 0))
        
        # 文件数量显示
        self.file_count_label = ttk.Label(header_frame, text="0个文件")
        self.file_count_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 展开/折叠按钮
        self.toggle_button = ttk.Button(header_frame, text="▼ 展开", 
                                       command=self.toggle_content, width=8)
        self.toggle_button.pack(side=tk.RIGHT)
        
        # 批量处理按钮
        self.batch_process_button = ttk.Button(header_frame, text="批量处理", 
                                              command=self.start_batch_processing, width=10)
        self.batch_process_button.pack(side=tk.RIGHT, padx=(0, 5))
    
    def setup_content_area(self):
        """设置可折叠的内容区域"""
        # 简化的文件列表
        self.setup_compact_file_list(self.content_frame)
        
        # 简化的输出设置
        self.setup_compact_output_settings(self.content_frame)
        
        # 进度显示
        self.setup_progress_display(self.content_frame)
    
    def setup_compact_file_list(self, parent):
        """设置紧凑的文件列表"""
        list_frame = ttk.LabelFrame(parent, text="选中的文件", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # 简化的文件列表（只显示文件名）
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(list_container, height=6)
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.file_listbox.yview)
        self.file_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 清空按钮
        ttk.Button(list_frame, text="清空列表", 
                  command=self.clear_files).pack(pady=(5, 0))
    
    def setup_compact_output_settings(self, parent):
        """设置紧凑的输出设置"""
        output_frame = ttk.LabelFrame(parent, text="输出设置", padding=5)
        output_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 输出文件夹选择
        folder_frame = ttk.Frame(output_frame)
        folder_frame.pack(fill=tk.X)
        
        ttk.Label(folder_frame, text="输出到:").pack(side=tk.LEFT)
        output_entry = ttk.Entry(folder_frame, textvariable=self.output_folder, 
                                state="readonly", width=30)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        ttk.Button(folder_frame, text="浏览", 
                  command=self.select_output_folder, width=6).pack(side=tk.RIGHT)
    
    def toggle_content(self):
        """切换内容区域的显示/隐藏"""
        if self.is_expanded.get():
            # 折叠
            self.content_frame.pack_forget()
            self.toggle_button.config(text="▼ 展开")
            self.is_expanded.set(False)
        else:
            # 展开
            self.content_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
            self.toggle_button.config(text="▲ 折叠")
            self.is_expanded.set(True)
    
    def update_file_count(self):
        """更新文件数量显示"""
        count = len(self.input_files)
        self.file_count_label.config(text=f"{count}个文件")
        
        # 更新批量处理按钮状态
        if count > 0:
            self.batch_process_button.config(state="normal")
        else:
            self.batch_process_button.config(state="disabled")
        

        
    def setup_progress_display(self, parent):
        """设置进度显示区域"""
        progress_frame = ttk.LabelFrame(parent, text="处理进度", padding=5)
        progress_frame.pack(fill=tk.X, pady=(0, 5))
        
        # 进度条
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=(0, 3))
        
        # 状态标签
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.pack(anchor=tk.W)
        
        # 控制按钮
        button_frame = ttk.Frame(progress_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))
        
        ttk.Button(button_frame, text="停止", 
                  command=self.stop_processing, width=8).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="打开输出文件夹", 
                  command=self.open_output_folder, width=12).pack(side=tk.RIGHT)
        

    def select_files(self):
        """选择图片文件"""
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
                self.add_files(valid_files)
                if len(valid_files) != len(files):
                    invalid_count = len(files) - len(valid_files)
                    messagebox.showwarning("警告", f"已添加 {len(valid_files)} 个有效图片文件，跳过了 {invalid_count} 个无效文件")
                else:
                    self.app.update_status(f"成功添加 {len(valid_files)} 个图片文件")
            else:
                messagebox.showwarning("警告", "所选文件中没有有效的图片文件")
            
    def select_folder(self):
        """选择文件夹"""
        folder = filedialog.askdirectory(
            title="选择包含图片的文件夹",
            initialdir=os.path.expanduser("~/Pictures")
        )
        if folder:
            # 询问是否包含子文件夹
            include_subfolders = messagebox.askyesno(
                "搜索选项", 
                "是否包含子文件夹中的图片？\n\n是：搜索所有子文件夹\n否：仅搜索当前文件夹",
                default='yes'
            )
            
            # 查找文件夹中的图片文件
            files = self.scan_folder_for_images(folder, include_subfolders)
            
            if files:
                # 过滤有效的图片文件
                valid_files = self.filter_valid_images(files)
                if valid_files:
                    added_count = self.add_files(valid_files)
                    if added_count > 0:
                        self.app.update_status(f"从文件夹添加了 {added_count} 个图片文件")
                        messagebox.showinfo("成功", f"找到并添加了 {added_count} 个有效图片文件")
                    else:
                        messagebox.showinfo("提示", "所选文件已在列表中")
                    
                    if len(valid_files) != len(files):
                        invalid_count = len(files) - len(valid_files)
                        messagebox.showwarning("注意", f"跳过了 {invalid_count} 个无效或损坏的图片文件")
                else:
                    messagebox.showwarning("警告", "文件夹中没有找到有效的图片文件")
            else:
                messagebox.showwarning("警告", "在选择的文件夹中没有找到图片文件")
                
    def scan_folder_for_images(self, folder_path, include_subfolders=True):
        """扫描文件夹中的图片文件"""
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif', '.webp', '.gif', '.ico'}
        files = []
        
        try:
            if include_subfolders:
                # 递归搜索所有子文件夹
                for root, dirs, filenames in os.walk(folder_path):
                    for filename in filenames:
                        if os.path.splitext(filename.lower())[1] in image_extensions:
                            files.append(os.path.join(root, filename))
            else:
                # 仅搜索当前文件夹
                for filename in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, filename)
                    if os.path.isfile(file_path):
                        if os.path.splitext(filename.lower())[1] in image_extensions:
                            files.append(file_path)
        except Exception as e:
            messagebox.showerror("错误", f"扫描文件夹时发生错误: {e}")
            
        return files
    
    def filter_valid_images(self, files):
        """过滤有效的图片文件"""
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
    
    def add_files(self, files):
        """添加文件到列表"""
        added_count = 0
        for file_path in files:
            if file_path not in self.input_files:
                self.input_files.append(file_path)
                
                # 添加到简化的列表框
                filename = os.path.basename(file_path)
                self.file_listbox.insert(tk.END, filename)
                added_count += 1
        
        # 更新文件数量显示
        self.update_file_count()
        
        return added_count
                
    def clear_files(self):
        """清空文件列表"""
        self.input_files.clear()
        self.file_listbox.delete(0, tk.END)
        self.update_file_count()
            
    def select_output_folder(self):
        """选择输出文件夹"""
        folder = filedialog.askdirectory(title="选择输出文件夹")
        if folder:
            self.output_folder.set(folder)
            
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
            
    def start_batch_processing(self):
        """开始批量处理"""
        if not self.input_files:
            messagebox.showwarning("警告", "请先选择要处理的图片文件")
            return
            
        if self.processing:
            messagebox.showwarning("警告", "批量处理正在进行中")
            return
            
        # 检查输出文件夹
        output_dir = self.output_folder.get()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出文件夹: {e}")
                return
                
        # 开始处理
        self.processing = True
        self.progress_var.set(0)
        self.status_var.set("开始批量处理...")
        
        # 在新线程中处理
        thread = threading.Thread(target=self.process_files)
        thread.daemon = True
        thread.start()
        
    def process_files(self):
        """处理文件（在后台线程中运行）"""
        total_files = len(self.input_files)
        processed_count = 0
        
        try:
            for i, file_path in enumerate(self.input_files):
                if not self.processing:  # 检查是否被停止
                    break
                    
                # 更新状态
                filename = os.path.basename(file_path)
                self.status_var.set(f"正在处理: {filename}")
                
                # 更新树形视图中的状态
                items = self.file_tree.get_children()
                if i < len(items):
                    self.file_tree.set(items[i], "状态", "处理中")
                
                try:
                    # 处理单个文件
                    self.process_single_file(file_path)
                    
                    # 更新状态为完成
                    if i < len(items):
                        self.file_tree.set(items[i], "状态", "已完成")
                    
                    processed_count += 1
                    
                except Exception as e:
                    # 更新状态为错误
                    if i < len(items):
                        self.file_tree.set(items[i], "状态", f"错误: {str(e)}")
                
                # 更新进度
                progress = (i + 1) / total_files * 100
                self.progress_var.set(progress)
                
        except Exception as e:
            messagebox.showerror("错误", f"批量处理过程中发生错误: {e}")
        
        finally:
            self.processing = False
            if processed_count == total_files:
                self.status_var.set(f"批量处理完成！成功处理 {processed_count} 个文件")
            else:
                self.status_var.set(f"批量处理结束。成功处理 {processed_count}/{total_files} 个文件")
                
    def process_single_file(self, file_path):
        """处理单个文件"""
        # 打开图片
        image = Image.open(file_path)
        
        # 获取当前水印设置
        watermark_settings = self.app.watermark_panel.get_settings()
        
        # 应用水印
        watermarked_image = self.watermark_manager.apply_watermark(image, watermark_settings)
        
        # 生成输出文件名
        output_path = self.generate_output_path(file_path)
        
        # 检查文件是否存在
        if os.path.exists(output_path) and not self.overwrite_var.get():
            # 生成新的文件名
            base, ext = os.path.splitext(output_path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            output_path = f"{base}_{counter}{ext}"
        
        # 保存图片
        watermarked_image.save(output_path, quality=95)
        
    def generate_output_path(self, input_path):
        """生成输出文件路径"""
        output_dir = self.output_folder.get()
        filename = os.path.basename(input_path)
        
        if self.keep_names_var.get():
            # 保持原始文件名
            return os.path.join(output_dir, filename)
        else:
            # 添加水印后缀
            name, ext = os.path.splitext(filename)
            return os.path.join(output_dir, f"{name}_watermarked{ext}")
            
    def stop_processing(self):
        """停止处理"""
        if self.processing:
            self.processing = False
            self.status_var.set("处理已停止")
            
    def open_output_folder(self):
        """打开输出文件夹"""
        output_dir = self.output_folder.get()
        if os.path.exists(output_dir):
            os.system(f"open '{output_dir}'")  # macOS
        else:
            messagebox.showwarning("警告", "输出文件夹不存在")
    
    def setup_drag_drop(self):
        """设置拖拽支持"""
        if DND_FILES is not None:
            # 为整个面板添加拖拽支持
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self.on_drop)
            
            # 为文件列表框也添加拖拽支持
            if hasattr(self, 'file_listbox'):
                self.file_listbox.drop_target_register(DND_FILES)
                self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)
    
    def on_drop(self, event):
        """拖拽文件处理"""
        if not event.data:
            return
            
        # 解析拖拽的文件路径
        files = self.parse_drop_data(event.data)
        
        # 分离文件和文件夹
        image_files = []
        folders = []
        
        for path in files:
            if os.path.isfile(path):
                image_files.append(path)
            elif os.path.isdir(path):
                folders.append(path)
        
        # 收集所有文件
        all_files = image_files.copy()
        
        # 添加文件夹中的图片（包含子文件夹）
        for folder in folders:
            folder_files = self.scan_folder_for_images(folder, include_subfolders=True)
            all_files.extend(folder_files)
        
        if all_files:
            # 过滤有效的图片文件
            valid_files = self.filter_valid_images(all_files)
            if valid_files:
                added_count = self.add_files(valid_files)
                if added_count > 0:
                    self.app.update_status(f"通过拖拽添加了 {added_count} 个文件到批量处理列表")
                    
                    # 显示详细信息
                    if len(folders) > 0:
                        messagebox.showinfo("拖拽成功", 
                                          f"成功添加 {added_count} 个图片文件\n"
                                          f"（包含 {len(folders)} 个文件夹中的图片）")
                else:
                    self.app.update_status("拖拽的文件已在列表中")
                    
                if len(valid_files) != len(all_files):
                    invalid_count = len(all_files) - len(valid_files)
                    messagebox.showwarning("注意", f"跳过了 {invalid_count} 个无效或重复的文件")
            else:
                messagebox.showwarning("警告", "拖拽的文件中没有有效的图片文件")
        else:
            messagebox.showwarning("警告", "没有找到可处理的图片文件")
    
    def parse_drop_data(self, data):
        """解析拖拽数据"""
        # 处理不同平台的文件路径格式
        files = []
        
        # 移除大括号并按空格分割
        data = data.strip('{}')
        
        # 处理包含空格的路径（用大括号包围）
        import re
        # 匹配被大括号包围的路径或不包含空格的路径
        paths = re.findall(r'\{([^}]+)\}|(\S+)', data)
        
        for path_tuple in paths:
            # path_tuple是一个元组，取非空的部分
            path = path_tuple[0] if path_tuple[0] else path_tuple[1]
            if path and os.path.exists(path):
                files.append(path)
        
        # 如果正则表达式解析失败，尝试简单的空格分割
        if not files:
            for path in data.split():
                path = path.strip('{}')
                if os.path.exists(path):
                    files.append(path)
        
        return files