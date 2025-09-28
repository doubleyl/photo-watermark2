#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理模块
提供统一的日志记录和错误处理功能
"""

import os
import sys
import logging
import traceback
from datetime import datetime
from typing import Optional, Any, Callable
from functools import wraps
from .helpers import get_app_data_dir, ensure_dir_exists


class WatermarkLogger:
    """水印应用日志管理器"""
    
    def __init__(self, name: str = "watermark_app"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置日志记录器"""
        if self.logger.handlers:
            return  # 避免重复设置
        
        self.logger.setLevel(logging.DEBUG)
        
        # 创建日志目录
        log_dir = os.path.join(get_app_data_dir(), "logs")
        ensure_dir_exists(log_dir)
        
        # 日志文件路径
        log_file = os.path.join(log_dir, f"{self.name}.log")
        
        # 文件处理器 - 记录所有级别的日志
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # 控制台处理器 - 只记录INFO及以上级别
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # 日志格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, *args, **kwargs):
        """记录调试信息"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """记录一般信息"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录警告信息"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录错误信息"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录严重错误信息"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """记录异常信息（包含堆栈跟踪）"""
        self.logger.exception(message, *args, **kwargs)
    
    def log_function_call(self, func_name: str, args: tuple = (), kwargs: dict = None):
        """记录函数调用"""
        kwargs = kwargs or {}
        self.debug(f"调用函数: {func_name}, 参数: args={args}, kwargs={kwargs}")
    
    def log_performance(self, operation: str, duration: float):
        """记录性能信息"""
        self.info(f"性能统计: {operation} 耗时 {duration:.3f} 秒")
    
    def log_system_info(self):
        """记录系统信息"""
        from .helpers import get_system_info, get_python_architecture
        
        system_info = get_system_info()
        python_arch = get_python_architecture()
        
        self.info(f"系统信息: {system_info}")
        self.info(f"Python架构: {python_arch}")
        self.info(f"Python版本: {sys.version}")


# 全局日志实例
_logger_instance: Optional[WatermarkLogger] = None


def get_logger(name: str = "watermark_app") -> WatermarkLogger:
    """获取日志记录器实例"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = WatermarkLogger(name)
    return _logger_instance


def log_errors(func: Callable) -> Callable:
    """装饰器：自动记录函数执行中的错误"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            logger.log_function_call(func.__name__, args, kwargs)
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.exception(f"函数 {func.__name__} 执行出错: {str(e)}")
            raise
    return wrapper


def safe_execute(func: Callable, *args, default_return=None, log_errors: bool = True, **kwargs) -> Any:
    """安全执行函数，捕获并记录异常"""
    logger = get_logger()
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            logger.exception(f"安全执行函数 {func.__name__ if hasattr(func, '__name__') else str(func)} 时出错: {str(e)}")
        return default_return


class ErrorHandler:
    """错误处理器"""
    
    def __init__(self, logger: Optional[WatermarkLogger] = None):
        self.logger = logger or get_logger()
    
    def handle_file_error(self, file_path: str, operation: str, error: Exception) -> bool:
        """处理文件操作错误"""
        error_msg = f"文件操作失败 - 操作: {operation}, 文件: {file_path}, 错误: {str(error)}"
        self.logger.error(error_msg)
        
        # 根据错误类型提供具体的处理建议
        if isinstance(error, FileNotFoundError):
            self.logger.warning(f"文件不存在: {file_path}")
            return False
        elif isinstance(error, PermissionError):
            self.logger.warning(f"文件权限不足: {file_path}")
            return False
        elif isinstance(error, OSError):
            self.logger.warning(f"系统错误: {str(error)}")
            return False
        
        return False
    
    def handle_image_error(self, image_path: str, operation: str, error: Exception) -> bool:
        """处理图像处理错误"""
        error_msg = f"图像处理失败 - 操作: {operation}, 图像: {image_path}, 错误: {str(error)}"
        self.logger.error(error_msg)
        
        # 检查是否是支持的图像格式
        if "cannot identify image file" in str(error).lower():
            self.logger.warning(f"不支持的图像格式: {image_path}")
        elif "truncated" in str(error).lower():
            self.logger.warning(f"图像文件损坏或不完整: {image_path}")
        
        return False
    
    def handle_font_error(self, font_path: str, error: Exception) -> bool:
        """处理字体加载错误"""
        error_msg = f"字体加载失败 - 字体: {font_path}, 错误: {str(error)}"
        self.logger.error(error_msg)
        
        if isinstance(error, OSError):
            self.logger.warning(f"字体文件不存在或损坏: {font_path}")
        
        return False
    
    def handle_config_error(self, config_file: str, error: Exception) -> bool:
        """处理配置文件错误"""
        error_msg = f"配置文件处理失败 - 文件: {config_file}, 错误: {str(error)}"
        self.logger.error(error_msg)
        return False


# 全局错误处理器实例
_error_handler_instance: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取错误处理器实例"""
    global _error_handler_instance
    if _error_handler_instance is None:
        _error_handler_instance = ErrorHandler()
    return _error_handler_instance


def setup_exception_handler():
    """设置全局异常处理器"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger = get_logger()
        logger.critical(
            "未捕获的异常",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception


# 初始化时设置异常处理器
setup_exception_handler()