# -*- coding: utf-8 -*-
"""
导出功能工具模块

提供各种导出功能，用于操作由ProviderConfigManager管理的数据。
"""

import os
import json
from typing import Dict, List, Any, Optional, Union

from .utils.helpers import save_to_json, generate_filename, copy_to_clipboard


class ExportUtils:
    """
    导出功能工具类
    
    提供各种导出功能，用于操作由ProviderConfigManager管理的数据。
    """
    
    def __init__(self, provider_config_manager):
        """
        初始化导出功能工具类
        
        Args:
            provider_config_manager: ProviderConfigManager实例
        """
        self.manager = provider_config_manager
        
        # 确保导出目录存在
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.export_dir = os.path.join(base_dir, 'exports')
        os.makedirs(self.export_dir, exist_ok=True)
    
    def export_model_mappings(self, provider_name: str, to_clipboard: bool = False) -> Optional[str]:
        """
        导出指定服务商的模型映射
        
        Args:
            provider_name (str): 服务商名称
            to_clipboard (bool, optional): 是否复制到剪贴板，默认为False
            
        Returns:
            Optional[str]: 如果导出到文件，返回文件路径；如果复制到剪贴板，返回None
        """
        # 获取模型映射
        model_mappings = self.manager.export_model_mappings(provider_name)
        if model_mappings is None:
            print(f"错误: 服务商 '{provider_name}' 不存在")
            return None
        
        if not model_mappings:
            print(f"警告: 服务商 '{provider_name}' 没有定义任何模型映射")
            return None
        
        # 转换为JSON字符串
        json_str = json.dumps(model_mappings, ensure_ascii=False, indent=2)
        
        if to_clipboard:
            # 复制到剪贴板
            if copy_to_clipboard(json_str):
                print(f"服务商 '{provider_name}' 的模型映射已复制到剪贴板")
            return None
        else:
            # 导出到文件
            filename = f"{provider_name}_model_mappings.json"
            filepath = os.path.join(self.export_dir, filename)
            
            if save_to_json(model_mappings, filepath):
                print(f"服务商 '{provider_name}' 的模型映射已导出到: {filepath}")
                return filepath
            else:
                return None
    
    def export_supported_models(self, provider_name: str, use_mappings: bool = False, to_clipboard: bool = False) -> Optional[str]:
        """
        导出指定服务商的支持模型列表
        
        Args:
            provider_name (str): 服务商名称
            use_mappings (bool, optional): 是否使用映射名称，默认为False（使用原始模型名称）
            to_clipboard (bool, optional): 是否复制到剪贴板，默认为False
            
        Returns:
            Optional[str]: 如果导出到文件，返回文件路径；如果复制到剪贴板，返回None
        """
        # 获取模型列表
        models = self.manager.export_supported_models(provider_name, use_mappings)
        if models is None:
            print(f"错误: 服务商 '{provider_name}' 不存在")
            return None
        
        if not models:
            print(f"警告: 服务商 '{provider_name}' 没有{'映射' if use_mappings else '支持'}的模型")
            return None
        
        # 转换为逗号分隔的字符串
        models_str = ",".join(models)
        
        if to_clipboard:
            # 复制到剪贴板
            if copy_to_clipboard(models_str):
                print(f"服务商 '{provider_name}' 的{'映射' if use_mappings else '支持'}模型列表已复制到剪贴板")
            return None
        else:
            # 导出到文件
            type_str = "mapped" if use_mappings else "supported"
            filename = f"{provider_name}_{type_str}_models.txt"
            filepath = os.path.join(self.export_dir, filename)
            
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(models_str)
                print(f"服务商 '{provider_name}' 的{'映射' if use_mappings else '支持'}模型列表已导出到: {filepath}")
                return filepath
            except Exception as e:
                print(f"导出模型列表失败: {e}")
                return None
    
    def export_api_keys_and_urls(self, to_clipboard: bool = False) -> Optional[str]:
        """
        导出所有服务商的API Key及请求地址
        
        Args:
            to_clipboard (bool, optional): 是否复制到剪贴板，默认为False
            
        Returns:
            Optional[str]: 如果导出到文件，返回文件路径；如果复制到剪贴板，返回None
        """
        # 获取API Key和URL信息
        api_info = self.manager.export_api_keys_and_urls()
        if not api_info:
            print("警告: 没有配置任何服务商")
            return None
        
        # 转换为JSON字符串
        json_str = json.dumps(api_info, ensure_ascii=False, indent=2)
        
        if to_clipboard:
            # 复制到剪贴板
            if copy_to_clipboard(json_str):
                print("所有服务商的API Key及请求地址已复制到剪贴板")
            return None
        else:
            # 导出到文件
            filename = "api_keys_and_urls.json"
            filepath = os.path.join(self.export_dir, filename)
            
            if save_to_json(api_info, filepath):
                print(f"所有服务商的API Key及请求地址已导出到: {filepath}")
                return filepath
            else:
                return None
    
    def export_all_configs(self, to_clipboard: bool = False) -> Optional[str]:
        """
        导出所有服务商的完整配置
        
        Args:
            to_clipboard (bool, optional): 是否复制到剪贴板，默认为False
            
        Returns:
            Optional[str]: 如果导出到文件，返回文件路径；如果复制到剪贴板，返回None
        """
        # 获取所有配置
        all_configs = self.manager.export_all_configs()
        if not all_configs:
            print("警告: 没有配置任何服务商")
            return None
        
        # 转换为JSON字符串
        json_str = json.dumps(all_configs, ensure_ascii=False, indent=2)
        
        if to_clipboard:
            # 复制到剪贴板
            if copy_to_clipboard(json_str):
                print("所有服务商的完整配置已复制到剪贴板")
            return None
        else:
            # 导出到文件
            filename = generate_filename("all_provider_configs", "json")
            filepath = os.path.join(self.export_dir, filename)
            
            if save_to_json(all_configs, filepath):
                print(f"所有服务商的完整配置已导出到: {filepath}")
                return filepath
            else:
                return None