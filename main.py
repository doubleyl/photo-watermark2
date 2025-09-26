#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片水印应用程序主入口
适用于macOS的GUI应用程序
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from watermark_app.gui.main_window import WatermarkApp
except ImportError as e:
    messagebox.showerror("导入错误", f"无法导入应用程序模块: {e}")
    sys.exit(1)


def main():
    """主函数"""
    try:
        # 创建主窗口
        root = tk.Tk()
        app = WatermarkApp(root)
        
        # 启动应用程序
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("应用程序错误", f"应用程序启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()