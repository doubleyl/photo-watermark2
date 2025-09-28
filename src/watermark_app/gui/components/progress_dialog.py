#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进度弹窗组件
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class ProgressDialog:
    """进度弹窗类"""
    
    def __init__(self, parent: tk.Tk, title: str = "处理进度", 
                 width: int = 400, height: int = 150):
        self.parent = parent
        self.dialog = None
        self.progress_var = None
        self.status_label = None
        self.cancel_callback: Optional[Callable] = None
        self.is_cancelled = False
        
        self.title = title
        self.width = width
        self.height = height
        
    def show(self, cancel_callback: Optional[Callable] = None):
        """显示进度弹窗"""
        if self.dialog is not None:
            return
            
        self.cancel_callback = cancel_callback
        self.is_cancelled = False
        
        # 创建弹窗
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(self.title)
        self.dialog.geometry(f"{self.width}x{self.height}")
        self.dialog.resizable(False, False)
        
        # 设置为模态窗口
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # 居中显示
        self._center_dialog()
        
        # 设置关闭事件
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 创建界面
        self._setup_ui()
        
    def _center_dialog(self):
        """将弹窗居中显示"""
        self.dialog.update_idletasks()
        
        # 获取父窗口位置和大小
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # 计算居中位置
        x = parent_x + (parent_width - self.width) // 2
        y = parent_y + (parent_height - self.height) // 2
        
        self.dialog.geometry(f"{self.width}x{self.height}+{x}+{y}")
        
    def _setup_ui(self):
        """设置界面"""
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态标签
        self.status_label = ttk.Label(
            main_frame, 
            text="准备开始...",
            font=("", 10)
        )
        self.status_label.pack(pady=(0, 15))
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        progress_bar.pack(pady=(0, 15))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack()
        
        # 取消按钮（如果提供了取消回调）
        if self.cancel_callback:
            cancel_button = ttk.Button(
                button_frame,
                text="取消",
                command=self._on_cancel
            )
            cancel_button.pack()
            
    def update_progress(self, value: float, status: str = ""):
        """更新进度"""
        if self.dialog is None:
            return
            
        try:
            self.progress_var.set(value)
            if status and self.status_label:
                self.status_label.config(text=status)
            self.dialog.update_idletasks()
        except tk.TclError:
            # 窗口已关闭
            pass
            
    def _on_cancel(self):
        """取消按钮点击事件"""
        self.is_cancelled = True
        if self.cancel_callback:
            self.cancel_callback()
        self.close()
        
    def _on_close(self):
        """窗口关闭事件"""
        if self.cancel_callback:
            self._on_cancel()
        else:
            self.close()
            
    def close(self):
        """关闭弹窗"""
        if self.dialog:
            try:
                self.dialog.grab_release()
                self.dialog.destroy()
            except tk.TclError:
                pass
            finally:
                self.dialog = None
                self.progress_var = None
                self.status_label = None
                
    def is_open(self) -> bool:
        """检查弹窗是否打开"""
        return self.dialog is not None and self.dialog.winfo_exists()