# -*- coding: utf-8 -*-
"""
服务商配置管理器模块

负责存储、管理和检索各个LLM服务商的配置信息。
"""

import os
import json
from typing import Dict, List, Optional, Any, Union
from .utils.helpers import load_from_json, save_to_json


class ProviderConfigManager:
    """
    服务商配置管理器类
    
    负责存储、管理和检索各个LLM服务商的配置信息。
    所有服务商配置将持久化存储在一个主JSON文件中。
    """
    
    # 预设的API类型列表
    SUPPORTED_API_TYPES = [
        "openai",
        "anthropic",
        "google-vertex-ai",
        "azure-openai",
        "groq",
        "deepseek",
        "custom"
    ]
    
    def __init__(self, config_file_path: str = None):
        """
        初始化服务商配置管理器
        
        Args:
            config_file_path (str, optional): 配置文件路径，默认为当前目录下的data/llm_providers_config.json
        """
        if config_file_path is None:
            # 默认配置文件路径
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            self.config_file_path = os.path.join(data_dir, 'llm_providers_config.json')
        else:
            self.config_file_path = config_file_path
        
        # 加载配置文件，如果文件不存在则创建空列表
        self.providers = load_from_json(self.config_file_path, default=[])
    
    def save_config(self) -> bool:
        """
        保存配置到文件
        
        Returns:
            bool: 保存成功返回True，否则返回False
        """
        return save_to_json(self.providers, self.config_file_path)
    
    def get_all_provider_names(self) -> List[str]:
        """
        获取所有服务商名称列表
        
        Returns:
            List[str]: 服务商名称列表
        """
        return [provider['name'] for provider in self.providers]
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定服务商的配置
        
        Args:
            provider_name (str): 服务商名称
            
        Returns:
            Optional[Dict[str, Any]]: 服务商配置字典，如果不存在则返回None
        """
        for provider in self.providers:
            if provider['name'] == provider_name:
                return provider
        return None
    
    def provider_exists(self, provider_name: str) -> bool:
        """
        检查服务商是否存在
        
        Args:
            provider_name (str): 服务商名称
            
        Returns:
            bool: 存在返回True，否则返回False
        """
        return provider_name in self.get_all_provider_names()
    
    def add_provider(self, provider_config: Dict[str, Any]) -> bool:
        """
        添加新的服务商配置
        
        Args:
            provider_config (Dict[str, Any]): 服务商配置字典
            
        Returns:
            bool: 添加成功返回True，否则返回False
        """
        # 检查必要字段
        required_fields = ['name', 'api_type', 'api_keys']
        for field in required_fields:
            if field not in provider_config:
                print(f"错误: 缺少必要字段 '{field}'")
                return False
        
        # 检查名称唯一性
        if self.provider_exists(provider_config['name']):
            print(f"错误: 服务商名称 '{provider_config['name']}' 已存在")
            return False
        
        # 检查API类型是否支持
        if provider_config['api_type'] not in self.SUPPORTED_API_TYPES:
            print(f"警告: API类型 '{provider_config['api_type']}' 不在预设列表中")
        
        # 确保支持的模型列表存在
        if 'supported_models' not in provider_config:
            provider_config['supported_models'] = []
        
        # 添加服务商配置
        self.providers.append(provider_config)
        return self.save_config()
    
    def update_provider(self, provider_name: str, updated_config: Dict[str, Any]) -> bool:
        """
        更新服务商配置
        
        Args:
            provider_name (str): 要更新的服务商名称
            updated_config (Dict[str, Any]): 更新后的配置字典
            
        Returns:
            bool: 更新成功返回True，否则返回False
        """
        # 检查服务商是否存在
        if not self.provider_exists(provider_name):
            print(f"错误: 服务商 '{provider_name}' 不存在")
            return False
        
        # 如果更新了名称，检查新名称是否与其他服务商冲突
        if 'name' in updated_config and updated_config['name'] != provider_name:
            if self.provider_exists(updated_config['name']):
                print(f"错误: 新名称 '{updated_config['name']}' 已被其他服务商使用")
                return False
        
        # 更新配置
        for i, provider in enumerate(self.providers):
            if provider['name'] == provider_name:
                # 保留原始配置中未在更新中指定的字段
                for key, value in updated_config.items():
                    self.providers[i][key] = value
                
                # 如果更新了名称，更新provider_name以便后续操作
                if 'name' in updated_config:
                    provider_name = updated_config['name']
                
                return self.save_config()
        
        return False
    
    def delete_provider(self, provider_name: str) -> bool:
        """
        删除服务商配置
        
        Args:
            provider_name (str): 要删除的服务商名称
            
        Returns:
            bool: 删除成功返回True，否则返回False
        """
        # 检查服务商是否存在
        if not self.provider_exists(provider_name):
            print(f"错误: 服务商 '{provider_name}' 不存在")
            return False
        
        # 删除配置
        self.providers = [p for p in self.providers if p['name'] != provider_name]
        return self.save_config()
    
    def find_model_provider(self, model_name: str) -> List[Dict[str, Any]]:
        """
        根据模型名称查找提供该模型的服务商
        
        搜索所有服务商的原始模型名称和映射名称，返回匹配的服务商及其API详情
        
        Args:
            model_name (str): 模型名称（原始名称或映射名称）
            
        Returns:
            List[Dict[str, Any]]: 匹配的服务商信息列表，每个元素包含：
                - provider_name: 服务商名称
                - base_url: 基础URL
                - api_key: 一个API密钥（通常是第一个）
                - actual_model_name: 实际模型名称（如果是映射名称，则返回映射后的名称）
                - custom_headers: 自定义请求头
        """
        results = []
        
        for provider in self.providers:
            # 检查原始模型名称
            if model_name in provider.get('supported_models', []):
                results.append({
                    'provider_name': provider['name'],
                    'base_url': provider.get('base_url', ''),
                    'api_key': provider['api_keys'][0] if provider['api_keys'] else '',
                    'actual_model_name': model_name,
                    'custom_headers': provider.get('custom_headers', {})
                })
            
            # 检查映射模型名称
            model_mappings = provider.get('model_mappings', {})
            if model_name in model_mappings:
                results.append({
                    'provider_name': provider['name'],
                    'base_url': provider.get('base_url', ''),
                    'api_key': provider['api_keys'][0] if provider['api_keys'] else '',
                    'actual_model_name': model_mappings[model_name],
                    'custom_headers': provider.get('custom_headers', {})
                })
        
        return results
    
    def export_model_mappings(self, provider_name: str) -> Optional[Dict[str, str]]:
        """
        导出指定服务商的模型映射
        
        Args:
            provider_name (str): 服务商名称
            
        Returns:
            Optional[Dict[str, str]]: 模型映射字典，如果服务商不存在则返回None
        """
        provider = self.get_provider_config(provider_name)
        if not provider:
            return None
        
        return provider.get('model_mappings', {})
    
    def export_supported_models(self, provider_name: str, use_mappings: bool = False) -> Optional[List[str]]:
        """
        导出指定服务商的支持模型列表
        
        Args:
            provider_name (str): 服务商名称
            use_mappings (bool): 是否使用映射名称，默认为False（使用原始模型名称）
            
        Returns:
            Optional[List[str]]: 模型名称列表，如果服务商不存在则返回None
        """
        provider = self.get_provider_config(provider_name)
        if not provider:
            return None
        
        if use_mappings:
            return list(provider.get('model_mappings', {}).keys())
        else:
            return provider.get('supported_models', [])
    
    def export_api_keys_and_urls(self) -> List[Dict[str, Union[str, List[str]]]]:
        """
        导出所有服务商的API Key及请求地址
        
        Returns:
            List[Dict[str, Union[str, List[str]]]]: 包含服务商名称、基础URL和API密钥的字典列表
        """
        result = []
        for provider in self.providers:
            result.append({
                'name': provider['name'],
                'base_url': provider.get('base_url', ''),
                'api_keys': provider.get('api_keys', [])
            })
        return result
    
    def export_all_configs(self) -> List[Dict[str, Any]]:
        """
        导出所有服务商的完整配置
        
        Returns:
            List[Dict[str, Any]]: 所有服务商配置的列表
        """
        return self.providers