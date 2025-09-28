#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用设置管理模块
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime


class Settings:
    """应用设置管理器"""
    
    def __init__(self, config_dir: str = None):
        """初始化设置管理器"""
        if config_dir is None:
            # 使用用户主目录下的配置文件夹
            self.config_dir = os.path.join(os.path.expanduser("~"), ".watermark_app")
        else:
            self.config_dir = config_dir
        
        # 确保配置目录存在
        os.makedirs(self.config_dir, exist_ok=True)
        
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.templates_dir = os.path.join(self.config_dir, "templates")
        
        # 确保模板目录存在
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # 默认设置
        self.default_settings = {
            # 窗口设置
            'window': {
                'width': 1200,
                'height': 800,
                'x': 100,
                'y': 100,
                'maximized': False
            },
            
            # 文件设置
            'file': {
                'last_import_dir': os.path.expanduser("~/Pictures"),
                'last_export_dir': os.path.expanduser("~/Desktop"),
                'auto_save_settings': True,
                'remember_last_files': True,
                'max_recent_files': 10
            },
            
            # 预览设置
            'preview': {
                'auto_refresh': True,
                'preview_quality': 'medium',  # low, medium, high
                'zoom_step': 0.1,
                'max_zoom': 5.0,
                'min_zoom': 0.1
            },
            
            # 导出设置
            'export': {
                'default_format': 'PNG',
                'default_quality': 95,
                'default_naming': 'suffix',
                'default_suffix': '_watermarked',
                'default_prefix': '',
                'resize_enabled': False,
                'resize_width': 1920,
                'resize_height': 1080,
                'resize_keep_aspect': True
            },
            
            # 水印设置
            'watermark': {
                'default_type': 'text',
                'default_position': 'bottom_right',
                'default_opacity': 0.7,
                'default_margin': 20,
                
                # 文本水印默认设置
                'text': {
                    'content': 'Watermark',
                    'font_size': 24,
                    'color': [255, 255, 255, 180],  # RGBA
                    'font_path': '',
                    'rotation': 0
                },
                
                # 图片水印默认设置
                'image': {
                    'path': '',
                    'scale': 1.0,
                    'rotation': 0
                }
            },
            
            # 界面设置
            'ui': {
                'theme': 'default',
                'language': 'zh_CN',
                'show_tooltips': True,
                'show_status_bar': True,
                'panel_layout': 'horizontal'  # horizontal, vertical
            },
            
            # 性能设置
            'performance': {
                'max_threads': 4,
                'cache_thumbnails': True,
                'thumbnail_size': 150,
                'preview_size': 800
            }
        }
        
        # 当前设置
        self.settings = self.default_settings.copy()
        
        # 加载设置
        self.load_settings()
    
    def get(self, key_path: str, default=None) -> Any:
        """获取设置值"""
        keys = key_path.split('.')
        value = self.settings
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """设置值"""
        keys = key_path.split('.')
        settings = self.settings
        
        # 导航到最后一级
        for key in keys[:-1]:
            if key not in settings:
                settings[key] = {}
            settings = settings[key]
        
        # 设置值
        settings[keys[-1]] = value
    
    def load_settings(self) -> bool:
        """加载设置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                
                # 合并设置（保留默认值）
                self._merge_settings(self.settings, loaded_settings)
                
                return True
        except Exception as e:
            print(f"加载设置失败: {e}")
        
        return False
    
    def save_settings(self) -> bool:
        """保存设置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"保存设置失败: {e}")
            return False
    
    def _merge_settings(self, default: Dict, loaded: Dict):
        """合并设置"""
        for key, value in loaded.items():
            if key in default:
                if isinstance(default[key], dict) and isinstance(value, dict):
                    self._merge_settings(default[key], value)
                else:
                    default[key] = value
    
    def reset_settings(self):
        """重置为默认设置"""
        self.settings = self.default_settings.copy()
    
    def reset_section(self, section: str):
        """重置指定部分的设置"""
        if section in self.default_settings:
            self.settings[section] = self.default_settings[section].copy()
    
    def export_settings(self, file_path: str, format_type: str = 'json') -> bool:
        """导出设置"""
        try:
            if format_type.lower() == 'json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.settings, f, indent=2, ensure_ascii=False)
            elif format_type.lower() == 'yaml':
                with open(file_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.settings, f, default_flow_style=False, allow_unicode=True)
            else:
                return False
            
            return True
        except Exception as e:
            print(f"导出设置失败: {e}")
            return False
    
    def import_settings(self, file_path: str) -> bool:
        """导入设置"""
        try:
            if not os.path.exists(file_path):
                return False
            
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_settings = json.load(f)
            elif ext in ['.yaml', '.yml']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported_settings = yaml.safe_load(f)
            else:
                return False
            
            # 合并导入的设置
            self._merge_settings(self.settings, imported_settings)
            
            return True
        except Exception as e:
            print(f"导入设置失败: {e}")
            return False
    
    def get_templates_dir(self) -> str:
        """获取模板目录"""
        return self.templates_dir
    
    def save_template(self, name: str, template_data: Dict[str, Any]) -> bool:
        """保存水印模板"""
        try:
            template_file = os.path.join(self.templates_dir, f"{name}.json")
            
            # 添加元数据
            template_with_meta = {
                'name': name,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'version': '1.0',
                'data': template_data
            }
            
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(template_with_meta, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"保存模板失败: {e}")
            return False
    
    def load_template(self, name: str) -> Optional[Dict[str, Any]]:
        """加载水印模板"""
        try:
            template_file = os.path.join(self.templates_dir, f"{name}.json")
            
            if not os.path.exists(template_file):
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            return template.get('data', template)  # 兼容旧格式
        except Exception as e:
            print(f"加载模板失败: {e}")
            return None
    
    def delete_template(self, name: str) -> bool:
        """删除水印模板"""
        try:
            template_file = os.path.join(self.templates_dir, f"{name}.json")
            
            if os.path.exists(template_file):
                os.remove(template_file)
                return True
            
            return False
        except Exception as e:
            print(f"删除模板失败: {e}")
            return False
    
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        templates = []
        
        try:
            for file in os.listdir(self.templates_dir):
                if file.endswith('.json'):
                    template_name = os.path.splitext(file)[0]
                    templates.append(template_name)
        except Exception as e:
            print(f"列出模板失败: {e}")
        
        return sorted(templates)
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息"""
        try:
            template_file = os.path.join(self.templates_dir, f"{name}.json")
            
            if not os.path.exists(template_file):
                return None
            
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
            
            # 获取文件信息
            stat = os.stat(template_file)
            
            return {
                'name': template.get('name', name),
                'created_at': template.get('created_at', ''),
                'version': template.get('version', '1.0'),
                'file_size': stat.st_size,
                'modified_at': stat.st_mtime,
                'has_data': 'data' in template
            }
        except Exception as e:
            print(f"获取模板信息失败: {e}")
            return None
    
    def validate_template(self, template_data: Dict[str, Any]) -> Tuple[bool, str]:
        """验证模板数据"""
        try:
            # 检查必需字段
            required_fields = ['type', 'enabled']
            for field in required_fields:
                if field not in template_data:
                    return False, f"缺少必需字段: {field}"
            
            # 检查水印类型
            watermark_type = template_data.get('type')
            if watermark_type not in ['text', 'image']:
                return False, f"无效的水印类型: {watermark_type}"
            
            # 根据类型验证特定字段
            if watermark_type == 'text':
                if not template_data.get('text', '').strip():
                    return False, "文本水印内容不能为空"
            elif watermark_type == 'image':
                image_path = template_data.get('image_path', '')
                if not image_path:
                    return False, "图片水印路径不能为空"
            
            return True, "模板验证通过"
        except Exception as e:
            return False, f"模板验证失败: {e}"
    
    def backup_settings(self, backup_dir: str = None) -> bool:
        """备份设置"""
        try:
            if backup_dir is None:
                backup_dir = os.path.join(self.config_dir, "backups")
            
            os.makedirs(backup_dir, exist_ok=True)
            
            # 生成备份文件名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"settings_backup_{timestamp}.json")
            
            # 复制设置文件
            import shutil
            shutil.copy2(self.config_file, backup_file)
            
            return True
        except Exception as e:
            print(f"备份设置失败: {e}")
            return False
    
    def restore_settings(self, backup_file: str) -> bool:
        """恢复设置"""
        try:
            if not os.path.exists(backup_file):
                return False
            
            # 备份当前设置
            self.backup_settings()
            
            # 恢复设置
            import shutil
            shutil.copy2(backup_file, self.config_file)
            
            # 重新加载设置
            self.load_settings()
            
            return True
        except Exception as e:
            print(f"恢复设置失败: {e}")
            return False
    
    def get_config_dir(self) -> str:
        """获取配置目录"""
        return self.config_dir
    
    def cleanup_old_backups(self, keep_count: int = 10):
        """清理旧备份"""
        try:
            backup_dir = os.path.join(self.config_dir, "backups")
            if not os.path.exists(backup_dir):
                return
            
            # 获取所有备份文件
            backup_files = []
            for file in os.listdir(backup_dir):
                if file.startswith("settings_backup_") and file.endswith(".json"):
                    file_path = os.path.join(backup_dir, file)
                    backup_files.append((file_path, os.path.getmtime(file_path)))
            
            # 按修改时间排序
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # 删除多余的备份
            for file_path, _ in backup_files[keep_count:]:
                os.remove(file_path)
        
        except Exception as e:
            print(f"清理备份失败: {e}")