#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理核心模块
"""

import os
import shutil
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


class FileManager:
    """文件管理器类"""
    
    def __init__(self):
        """初始化文件管理器"""
        self.image_files = []
        self.current_index = -1
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif'}
    
    def add_image_file(self, file_path: str) -> bool:
        """添加单个图片文件"""
        if not os.path.exists(file_path):
            return False
        
        if not self.is_supported_format(file_path):
            return False
        
        if file_path not in self.image_files:
            self.image_files.append(file_path)
            return True
        
        return False
    
    def add_image_files(self, file_paths: List[str]) -> Tuple[int, List[str]]:
        """批量添加图片文件"""
        added_count = 0
        failed_files = []
        
        for file_path in file_paths:
            if self.add_image_file(file_path):
                added_count += 1
            else:
                failed_files.append(file_path)
        
        return added_count, failed_files
    
    def add_folder(self, folder_path: str, recursive: bool = True) -> Tuple[int, List[str]]:
        """添加文件夹中的图片"""
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            return 0, [folder_path]
        
        image_files = self.scan_folder_for_images(folder_path, recursive)
        return self.add_image_files(image_files)
    
    def remove_image_file(self, file_path: str) -> bool:
        """移除图片文件"""
        if file_path in self.image_files:
            index = self.image_files.index(file_path)
            self.image_files.remove(file_path)
            
            # 调整当前索引
            if self.current_index >= index:
                self.current_index -= 1
            
            if self.current_index < 0 and self.image_files:
                self.current_index = 0
            elif not self.image_files:
                self.current_index = -1
            
            return True
        
        return False
    
    def clear_image_files(self):
        """清空图片文件列表"""
        self.image_files.clear()
        self.current_index = -1
    
    def get_image_files(self) -> List[str]:
        """获取图片文件列表"""
        return self.image_files.copy()
    
    def get_current_file(self) -> Optional[str]:
        """获取当前选中的文件"""
        if 0 <= self.current_index < len(self.image_files):
            return self.image_files[self.current_index]
        return None
    
    def set_current_file(self, file_path: str) -> bool:
        """设置当前选中的文件"""
        if file_path in self.image_files:
            self.current_index = self.image_files.index(file_path)
            return True
        return False
    
    def set_current_index(self, index: int) -> bool:
        """设置当前索引"""
        if 0 <= index < len(self.image_files):
            self.current_index = index
            return True
        return False
    
    def get_current_index(self) -> int:
        """获取当前索引"""
        return self.current_index
    
    def get_file_count(self) -> int:
        """获取文件数量"""
        return len(self.image_files)
    
    def is_supported_format(self, file_path: str) -> bool:
        """检查文件格式是否支持"""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.supported_formats
    
    def scan_folder_for_images(self, folder_path: str, recursive: bool = True) -> List[str]:
        """扫描文件夹中的图片文件"""
        image_files = []
        
        try:
            if recursive:
                # 递归扫描
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        if self.is_supported_format(file_path):
                            image_files.append(file_path)
            else:
                # 只扫描当前文件夹
                for file in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file)
                    if os.path.isfile(file_path) and self.is_supported_format(file_path):
                        image_files.append(file_path)
        
        except Exception as e:
            print(f"扫描文件夹失败 {folder_path}: {e}")
        
        return sorted(image_files)
    
    def get_file_info(self, file_path: str) -> Optional[Dict]:
        """获取文件信息"""
        try:
            if not os.path.exists(file_path):
                return None
            
            stat = os.stat(file_path)
            
            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'size_str': self.format_file_size(stat.st_size),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'extension': os.path.splitext(file_path)[1].lower()
            }
        
        except Exception as e:
            print(f"获取文件信息失败 {file_path}: {e}")
            return None
    
    def format_file_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.1f} {size_names[i]}"
    
    def generate_output_filename(self, input_path: str, output_dir: str, 
                                naming_rule: str, prefix: str = "", suffix: str = "",
                                output_format: str = None) -> str:
        """生成输出文件名"""
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        
        # 确定输出格式
        if output_format:
            ext = f".{output_format.lower()}"
        else:
            ext = os.path.splitext(input_path)[1]
        
        # 根据命名规则生成文件名
        if naming_rule == "original":
            output_name = f"{base_name}{ext}"
        elif naming_rule == "prefix":
            output_name = f"{prefix}{base_name}{ext}"
        elif naming_rule == "suffix":
            output_name = f"{base_name}{suffix}{ext}"
        elif naming_rule == "timestamp":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_name = f"{base_name}_{timestamp}{ext}"
        else:
            output_name = f"{base_name}_watermarked{ext}"
        
        return os.path.join(output_dir, output_name)
    
    def ensure_unique_filename(self, file_path: str) -> str:
        """确保文件名唯一"""
        if not os.path.exists(file_path):
            return file_path
        
        base_dir = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        ext = os.path.splitext(file_path)[1]
        
        counter = 1
        while True:
            new_name = f"{base_name}_{counter}{ext}"
            new_path = os.path.join(base_dir, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1
    
    def validate_output_settings(self, output_dir: str, naming_rule: str, 
                                prefix: str = "", suffix: str = "") -> Tuple[bool, str]:
        """验证输出设置"""
        # 检查输出目录
        if not output_dir:
            return False, "输出目录不能为空"
        
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                return False, f"无法创建输出目录: {e}"
        
        if not os.path.isdir(output_dir):
            return False, "输出路径不是有效目录"
        
        if not os.access(output_dir, os.W_OK):
            return False, "输出目录没有写入权限"
        
        # 检查命名规则
        valid_rules = ["original", "prefix", "suffix", "timestamp"]
        if naming_rule not in valid_rules:
            return False, f"无效的命名规则: {naming_rule}"
        
        # 检查前缀和后缀
        if naming_rule == "prefix" and not prefix.strip():
            return False, "使用前缀命名时，前缀不能为空"
        
        if naming_rule == "suffix" and not suffix.strip():
            return False, "使用后缀命名时，后缀不能为空"
        
        # 检查文件名字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            if char in prefix or char in suffix:
                return False, f"前缀或后缀包含无效字符: {char}"
        
        return True, "验证通过"
    
    def batch_process_files(self, process_func: Callable, 
                          progress_callback: Callable = None,
                          max_workers: int = 4) -> Tuple[int, int, List[str]]:
        """批量处理文件"""
        if not self.image_files:
            return 0, 0, []
        
        success_count = 0
        failed_count = 0
        failed_files = []
        total_files = len(self.image_files)
        
        # 使用线程池处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(process_func, file_path): file_path 
                for file_path in self.image_files
            }
            
            # 处理完成的任务
            for i, future in enumerate(as_completed(future_to_file)):
                file_path = future_to_file[future]
                
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_files.append(file_path)
                except Exception as e:
                    failed_count += 1
                    failed_files.append(file_path)
                    print(f"处理文件失败 {file_path}: {e}")
                
                # 更新进度
                if progress_callback:
                    progress = (i + 1) / total_files * 100
                    progress_callback(progress, i + 1, total_files)
        
        return success_count, failed_count, failed_files
    
    def copy_file(self, src_path: str, dst_path: str) -> bool:
        """复制文件"""
        try:
            # 确保目标目录存在
            dst_dir = os.path.dirname(dst_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            
            shutil.copy2(src_path, dst_path)
            return True
        
        except Exception as e:
            print(f"复制文件失败 {src_path} -> {dst_path}: {e}")
            return False
    
    def move_file(self, src_path: str, dst_path: str) -> bool:
        """移动文件"""
        try:
            # 确保目标目录存在
            dst_dir = os.path.dirname(dst_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            
            shutil.move(src_path, dst_path)
            
            # 更新文件列表中的路径
            if src_path in self.image_files:
                index = self.image_files.index(src_path)
                self.image_files[index] = dst_path
            
            return True
        
        except Exception as e:
            print(f"移动文件失败 {src_path} -> {dst_path}: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # 从文件列表中移除
            self.remove_image_file(file_path)
            
            return True
        
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")
            return False
    
    def get_supported_formats_filter(self) -> List[Tuple[str, str]]:
        """获取文件对话框的格式过滤器"""
        return [
            ("图片文件", "*.jpg *.jpeg *.png *.bmp *.tiff *.tif"),
            ("JPEG文件", "*.jpg *.jpeg"),
            ("PNG文件", "*.png"),
            ("BMP文件", "*.bmp"),
            ("TIFF文件", "*.tiff *.tif"),
            ("所有文件", "*.*")
        ]
    
    def sort_files(self, sort_by: str = "name", reverse: bool = False):
        """排序文件列表"""
        if not self.image_files:
            return
        
        current_file = self.get_current_file()
        
        if sort_by == "name":
            self.image_files.sort(key=lambda x: os.path.basename(x).lower(), reverse=reverse)
        elif sort_by == "path":
            self.image_files.sort(key=lambda x: x.lower(), reverse=reverse)
        elif sort_by == "size":
            self.image_files.sort(key=lambda x: os.path.getsize(x) if os.path.exists(x) else 0, reverse=reverse)
        elif sort_by == "modified":
            self.image_files.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=reverse)
        
        # 恢复当前选中的文件
        if current_file:
            self.set_current_file(current_file)
    
    def filter_files(self, filter_text: str) -> List[str]:
        """过滤文件列表"""
        if not filter_text:
            return self.image_files.copy()
        
        filter_text = filter_text.lower()
        filtered_files = []
        
        for file_path in self.image_files:
            file_name = os.path.basename(file_path).lower()
            if filter_text in file_name:
                filtered_files.append(file_path)
        
        return filtered_files
    
    def get_statistics(self) -> Dict:
        """获取文件统计信息"""
        if not self.image_files:
            return {
                'total_files': 0,
                'total_size': 0,
                'total_size_str': '0 B',
                'formats': {}
            }
        
        total_size = 0
        formats = {}
        
        for file_path in self.image_files:
            if os.path.exists(file_path):
                # 计算大小
                file_size = os.path.getsize(file_path)
                total_size += file_size
                
                # 统计格式
                ext = os.path.splitext(file_path)[1].lower()
                formats[ext] = formats.get(ext, 0) + 1
        
        return {
            'total_files': len(self.image_files),
            'total_size': total_size,
            'total_size_str': self.format_file_size(total_size),
            'formats': formats
        }