#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工具模块初始化
"""

from .helpers import (
    get_system_info, is_macos, is_windows, is_linux, 
    get_app_data_dir, get_system_font_dirs, open_file_manager,
    get_default_fonts, is_arm_architecture, get_python_architecture,
    ensure_dir_exists, safe_file_name,
    format_file_size, format_duration, clamp, lerp,
    color_to_hex, hex_to_color, rgba_to_hex, hex_to_rgba,
    retry, threaded, ProgressTracker, Timer,
    show_error, show_warning, show_info, ask_yes_no,
    center_window, validate_color, get_resource_path,
    load_icon, create_tooltip, debounce, throttle
)
from .font_manager import FontManager, get_font_manager
from .logger import get_logger, get_error_handler, log_errors, safe_execute, WatermarkLogger, ErrorHandler

__all__ = [
    'get_system_info', 'is_macos', 'is_windows', 'is_linux',
    'get_app_data_dir', 'get_system_font_dirs', 'open_file_manager',
    'get_default_fonts', 'is_arm_architecture', 'get_python_architecture',
    'ensure_dir_exists', 'safe_file_name',
    'format_file_size', 'format_duration', 'clamp', 'lerp',
    'color_to_hex', 'hex_to_color', 'rgba_to_hex', 'hex_to_rgba',
    'retry', 'threaded', 'ProgressTracker', 'Timer',
    'show_error', 'show_warning', 'show_info', 'ask_yes_no',
    'center_window', 'validate_color', 'get_resource_path',
    'load_icon', 'create_tooltip', 'debounce', 'throttle',
    'FontManager', 'get_font_manager',
    'get_logger', 'get_error_handler', 'log_errors', 'safe_execute', 'WatermarkLogger', 'ErrorHandler'
]