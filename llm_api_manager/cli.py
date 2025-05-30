# -*- coding: utf-8 -*-
"""
命令行界面应用程序模块

提供一个全面的命令行界面（CLI），简化开发者在多模型环境下的工作流程。
"""

import os
import sys
from typing import Dict, List, Any, Optional, Union, Tuple

from .provider_config_manager import ProviderConfigManager
from .model_test_system import ModelTestSystem
from .export_utils import ExportUtils


class CLI:
    """
    命令行界面应用程序类
    
    协调用户交互，允许用户在管理配置和启动模型测试之间切换。
    """
    
    def __init__(self):
        """
        初始化CLI应用程序
        """
        # 初始化ProviderConfigManager
        self.config_manager = ProviderConfigManager()
        
        # 初始化ExportUtils
        self.export_utils = ExportUtils(self.config_manager)
        
        # 导入questionary库
        try:
            import questionary
            from questionary import Choice
            self.questionary = questionary
            self.Choice = Choice
        except ImportError:
            print("错误: 未安装questionary库，无法显示交互式菜单。请使用pip install questionary安装。")
            sys.exit(1)
    
    def run(self) -> None:
        """
        运行CLI应用程序
        """
        while True:
            # 显示主菜单
            choice = self.questionary.select(
                "LLM API 管理器 - 主菜单:",
                choices=[
                    self.Choice("1. 管理LLM服务商配置", "manage_providers"),
                    self.Choice("2. 测试LLM模型", "test_models"),
                    self.Choice("3. 导出配置数据", "export_data"),
                    self.Choice("4. 查询模型信息", "query_model"),
                    self.Choice("5. 退出", "exit")
                ]
            ).ask()
            
            if choice == "manage_providers":
                self._manage_providers_menu()
            elif choice == "test_models":
                self._test_models_menu()
            elif choice == "export_data":
                self._export_data_menu()
            elif choice == "query_model":
                self._query_model()
            elif choice == "exit":
                print("感谢使用LLM API管理器，再见！")
                break
    
    def _manage_providers_menu(self) -> None:
        """
        服务商配置管理子菜单
        """
        while True:
            choice = self.questionary.select(
                "管理LLM服务商配置:",
                choices=[
                    self.Choice("1. 添加服务商", "add"),
                    self.Choice("2. 编辑服务商", "edit"),
                    self.Choice("3. 删除服务商", "delete"),
                    self.Choice("4. 查看所有服务商", "list"),
                    self.Choice("5. 查看服务商详情", "view"),
                    self.Choice("6. 返回主菜单", "back")
                ]
            ).ask()
            
            if choice == "add":
                self._add_provider()
            elif choice == "edit":
                self._edit_provider()
            elif choice == "delete":
                self._delete_provider()
            elif choice == "list":
                self._list_providers()
            elif choice == "view":
                self._view_provider()
            elif choice == "back":
                break
    
    def _add_provider(self) -> None:
        """
        添加新的服务商配置
        """
        print("\n添加新的服务商配置")
        
        # 输入服务商名称
        name = self.questionary.text(
            "服务商名称 (必填):",
            validate=lambda text: len(text) > 0 or "名称不能为空"
        ).ask()
        
        if not name:
            return
        
        # 检查名称唯一性
        if self.config_manager.provider_exists(name):
            print(f"错误: 服务商名称 '{name}' 已存在")
            return
        
        # 选择API类型
        api_type = self.questionary.select(
            "API类型 (必填):",
            choices=[
                self.Choice(api_type, api_type) 
                for api_type in self.config_manager.SUPPORTED_API_TYPES
            ]
        ).ask()
        
        # 输入基础URL
        base_url = self.questionary.text(
            "基础URL (可选，对于非OpenAI标准格式或自定义接入点时必填):"
        ).ask()
        
        # 输入API密钥
        api_keys = []
        while True:
            api_key = self.questionary.text(
                "API密钥 (必填，输入空字符串结束添加):",
                validate=lambda text: True  # 允许空字符串用于结束添加
            ).ask()
            
            if not api_key:
                if not api_keys:  # 确保至少有一个API密钥
                    print("错误: 至少需要一个API密钥")
                    continue
                break
            
            api_keys.append(api_key)
        
        # 输入支持的模型列表
        supported_models = []
        print("\n输入支持的模型列表 (可选):")
        print("提示: 您可以稍后通过编辑功能添加或修改模型列表")
        print("提示: 如果API类型支持，系统将尝试自动获取模型列表")
        
        while True:
            model = self.questionary.text(
                "模型名称 (输入空字符串结束添加):"
            ).ask()
            
            if not model:
                break
            
            supported_models.append(model)
        
        # 输入模型映射
        model_mappings = {}
        print("\n输入模型名称映射 (可选):")
        print("提示: 模型映射用于将用户友好的名称映射到服务商特定的实际模型ID")
        print("例如: {\"Doubao-pro-32k\": \"ep-xxx\"}")
        
        while True:
            friendly_name = self.questionary.text(
                "友好名称 (输入空字符串结束添加):"
            ).ask()
            
            if not friendly_name:
                break
            
            actual_model_id = self.questionary.text(
                f"实际模型ID (对应 {friendly_name}):",
                validate=lambda text: len(text) > 0 or "实际模型ID不能为空"
            ).ask()
            
            if not actual_model_id:
                continue
            
            model_mappings[friendly_name] = actual_model_id
        
        # 输入自定义请求头
        custom_headers = {}
        print("\n输入自定义请求头 (可选):")
        print("提示: 自定义请求头用于添加特定的HTTP头部到API请求中")
        print("例如: {\"X-Custom-Feature\": \"enabled\"}")
        
        while True:
            header_name = self.questionary.text(
                "请求头名称 (输入空字符串结束添加):"
            ).ask()
            
            if not header_name:
                break
            
            header_value = self.questionary.text(
                f"请求头值 (对应 {header_name}):",
                validate=lambda text: len(text) > 0 or "请求头值不能为空"
            ).ask()
            
            if not header_value:
                continue
            
            custom_headers[header_name] = header_value
        
        # 构建服务商配置
        provider_config = {
            'name': name,
            'api_type': api_type,
            'api_keys': api_keys,
            'supported_models': supported_models
        }
        
        # 添加可选字段
        if base_url:
            provider_config['base_url'] = base_url
        
        if model_mappings:
            provider_config['model_mappings'] = model_mappings
        
        if custom_headers:
            provider_config['custom_headers'] = custom_headers
        
        # 添加服务商配置
        if self.config_manager.add_provider(provider_config):
            print(f"成功添加服务商: {name}")
            
            # 如果用户未输入模型列表，尝试自动获取
            if not supported_models and base_url:
                print("\n检测到未输入模型列表，正在尝试自动获取...")
                # 创建临时ModelTestSystem实例来获取模型列表
                test_system = ModelTestSystem(provider_config)
                if test_system.load_models_for_provider():
                    # 获取模型ID列表
                    fetched_models = [model.get('id') for model in test_system.models_data if model.get('id')]
                    
                    if fetched_models:
                        # 更新服务商配置中的模型列表
                        provider_config['supported_models'] = fetched_models
                        if self.config_manager.update_provider(name, provider_config):
                            print(f"成功自动获取并更新了 {len(fetched_models)} 个模型")
                        else:
                            print("自动更新模型列表失败")
                    else:
                        print("未从API获取到任何模型")
                else:
                    print("自动获取模型列表失败，您可以稍后通过编辑功能手动添加")
        else:
            print(f"添加服务商失败: {name}")
    
    def _edit_provider(self) -> None:
        """
        编辑服务商配置
        """
        # 获取所有服务商名称
        provider_names = self.config_manager.get_all_provider_names()
        if not provider_names:
            print("没有配置任何服务商")
            return
        
        # 选择要编辑的服务商
        provider_name = self.questionary.select(
            "选择要编辑的服务商:",
            choices=provider_names + ["返回"]
        ).ask()
        
        if provider_name == "返回":
            return
        
        # 获取当前配置
        current_config = self.config_manager.get_provider_config(provider_name)
        if not current_config:
            print(f"错误: 无法获取服务商 '{provider_name}' 的配置")
            return
        
        # 选择要编辑的字段
        while True:
            field = self.questionary.select(
                f"编辑服务商 '{provider_name}' - 选择要编辑的字段:",
                choices=[
                    self.Choice("名称", "name"),
                    self.Choice("API类型", "api_type"),
                    self.Choice("基础URL", "base_url"),
                    self.Choice("API密钥", "api_keys"),
                    self.Choice("支持的模型列表", "supported_models"),
                    self.Choice("模型映射", "model_mappings"),
                    self.Choice("自定义请求头", "custom_headers"),
                    self.Choice("保存并返回", "save")
                ]
            ).ask()
            
            if field == "save":
                break
            
            # 编辑选定的字段
            if field == "name":
                new_name = self.questionary.text(
                    "新的服务商名称:",
                    default=current_config['name'],
                    validate=lambda text: len(text) > 0 or "名称不能为空"
                ).ask()
                
                if new_name and new_name != current_config['name']:
                    # 检查名称唯一性
                    if self.config_manager.provider_exists(new_name):
                        print(f"错误: 服务商名称 '{new_name}' 已存在")
                    else:
                        current_config['name'] = new_name
            
            elif field == "api_type":
                new_api_type = self.questionary.select(
                    "新的API类型:",
                    choices=[
                        self.Choice(api_type, api_type) 
                        for api_type in self.config_manager.SUPPORTED_API_TYPES
                    ],
                    default=current_config['api_type']
                ).ask()
                
                if new_api_type and new_api_type != current_config['api_type']:
                    confirm = self.questionary.confirm(
                        f"警告: 更改API类型可能会影响现有配置。确定要将API类型从 '{current_config['api_type']}' 更改为 '{new_api_type}' 吗?"
                    ).ask()
                    
                    if confirm:
                        current_config['api_type'] = new_api_type
            
            elif field == "base_url":
                new_base_url = self.questionary.text(
                    "新的基础URL:",
                    default=current_config.get('base_url', '')
                ).ask()
                
                if new_base_url != current_config.get('base_url', ''):
                    if new_base_url:
                        current_config['base_url'] = new_base_url
                    elif 'base_url' in current_config:
                        del current_config['base_url']
            
            elif field == "api_keys":
                self._edit_api_keys(current_config)
            
            elif field == "supported_models":
                self._edit_supported_models(current_config)
            
            elif field == "model_mappings":
                self._edit_model_mappings(current_config)
            
            elif field == "custom_headers":
                self._edit_custom_headers(current_config)
        
        # 更新服务商配置
        original_name = provider_name
        if self.config_manager.update_provider(original_name, current_config):
            print(f"成功更新服务商: {current_config['name']}")
        else:
            print(f"更新服务商失败: {original_name}")
    
    def _edit_api_keys(self, config: Dict[str, Any]) -> None:
        """
        编辑API密钥列表
        
        Args:
            config (Dict[str, Any]): 服务商配置字典
        """
        api_keys = config.get('api_keys', [])
        
        while True:
            # 显示当前API密钥列表
            print("\n当前API密钥列表:")
            for i, key in enumerate(api_keys):
                # 显示部分密钥，保护敏感信息
                masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "*" * len(key)
                print(f"{i+1}. {masked_key}")
            
            action = self.questionary.select(
                "选择操作:",
                choices=[
                    self.Choice("添加新密钥", "add"),
                    self.Choice("编辑现有密钥", "edit"),
                    self.Choice("删除密钥", "delete"),
                    self.Choice("完成编辑", "done")
                ]
            ).ask()
            
            if action == "add":
                new_key = self.questionary.text(
                    "输入新的API密钥:",
                    validate=lambda text: len(text) > 0 or "API密钥不能为空"
                ).ask()
                
                if new_key:
                    api_keys.append(new_key)
            
            elif action == "edit" and api_keys:
                index = self.questionary.select(
                    "选择要编辑的密钥:",
                    choices=[f"{i+1}. {key[:4]}...{key[-4:]}" for i, key in enumerate(api_keys)] + ["取消"]
                ).ask()
                
                if index != "取消":
                    i = int(index.split(".")[0]) - 1
                    new_key = self.questionary.text(
                        "输入新的API密钥:",
                        default=api_keys[i],
                        validate=lambda text: len(text) > 0 or "API密钥不能为空"
                    ).ask()
                    
                    if new_key:
                        api_keys[i] = new_key
            
            elif action == "delete" and api_keys:
                if len(api_keys) <= 1:
                    print("错误: 至少需要保留一个API密钥")
                    continue
                
                index = self.questionary.select(
                    "选择要删除的密钥:",
                    choices=[f"{i+1}. {key[:4]}...{key[-4:]}" for i, key in enumerate(api_keys)] + ["取消"]
                ).ask()
                
                if index != "取消":
                    i = int(index.split(".")[0]) - 1
                    confirm = self.questionary.confirm(f"确定要删除密钥 {i+1} 吗?").ask()
                    
                    if confirm:
                        del api_keys[i]
            
            elif action == "done":
                break
        
        # 更新配置
        config['api_keys'] = api_keys
    
    def _edit_supported_models(self, config: Dict[str, Any]) -> None:
        """
        编辑支持的模型列表
        
        Args:
            config (Dict[str, Any]): 服务商配置字典
        """
        supported_models = config.get('supported_models', [])
        
        while True:
            # 显示当前支持的模型列表
            print("\n当前支持的模型列表:")
            for i, model in enumerate(supported_models):
                print(f"{i+1}. {model}")
            
            action = self.questionary.select(
                "选择操作:",
                choices=[
                    self.Choice("添加新模型", "add"),
                    self.Choice("编辑现有模型", "edit"),
                    self.Choice("删除模型", "delete"),
                    self.Choice("尝试从API自动获取", "fetch"),
                    self.Choice("完成编辑", "done")
                ]
            ).ask()
            
            if action == "add":
                new_model = self.questionary.text(
                    "输入新的模型名称:",
                    validate=lambda text: len(text) > 0 or "模型名称不能为空"
                ).ask()
                
                if new_model and new_model not in supported_models:
                    supported_models.append(new_model)
                elif new_model in supported_models:
                    print(f"模型 '{new_model}' 已存在")
            
            elif action == "edit" and supported_models:
                index = self.questionary.select(
                    "选择要编辑的模型:",
                    choices=[f"{i+1}. {model}" for i, model in enumerate(supported_models)] + ["取消"]
                ).ask()
                
                if index != "取消":
                    i = int(index.split(".")[0]) - 1
                    new_model = self.questionary.text(
                        "输入新的模型名称:",
                        default=supported_models[i],
                        validate=lambda text: len(text) > 0 or "模型名称不能为空"
                    ).ask()
                    
                    if new_model:
                        supported_models[i] = new_model
            
            elif action == "delete" and supported_models:
                index = self.questionary.select(
                    "选择要删除的模型:",
                    choices=[f"{i+1}. {model}" for i, model in enumerate(supported_models)] + ["取消"]
                ).ask()
                
                if index != "取消":
                    i = int(index.split(".")[0]) - 1
                    confirm = self.questionary.confirm(f"确定要删除模型 '{supported_models[i]}' 吗?").ask()
                    
                    if confirm:
                        del supported_models[i]
            
            elif action == "fetch":
                print("尝试从API自动获取模型列表...")
                
                # 创建临时ModelTestSystem实例来获取模型列表
                test_system = ModelTestSystem(config)
                if test_system.load_models_for_provider():
                    # 获取模型ID列表
                    fetched_models = [model.get('id') for model in test_system.models_data if model.get('id')]
                    
                    if fetched_models:
                        # 询问是否替换或合并
                        if supported_models:
                            merge_action = self.questionary.select(
                                "已从API获取模型列表，请选择操作:",
                                choices=[
                                    self.Choice("替换现有列表", "replace"),
                                    self.Choice("合并到现有列表", "merge"),
                                    self.Choice("取消", "cancel")
                                ]
                            ).ask()
                            
                            if merge_action == "replace":
                                supported_models = fetched_models
                            elif merge_action == "merge":
                                # 合并列表，去除重复项
                                for model in fetched_models:
                                    if model not in supported_models:
                                        supported_models.append(model)
                        else:
                            supported_models = fetched_models
                        
                        print(f"成功获取 {len(fetched_models)} 个模型")
                    else:
                        print("未从API获取到任何模型")
            
            elif action == "done":
                break
        
        # 更新配置
        config['supported_models'] = supported_models
    
    def _edit_model_mappings(self, config: Dict[str, Any]) -> None:
        """
        编辑模型映射
        
        Args:
            config (Dict[str, Any]): 服务商配置字典
        """
        model_mappings = config.get('model_mappings', {})
        
        while True:
            # 显示当前模型映射
            print("\n当前模型映射:")
            for i, (friendly_name, actual_id) in enumerate(model_mappings.items()):
                print(f"{i+1}. {friendly_name} -> {actual_id}")
            
            action = self.questionary.select(
                "选择操作:",
                choices=[
                    self.Choice("添加新映射", "add"),
                    self.Choice("编辑现有映射", "edit"),
                    self.Choice("删除映射", "delete"),
                    self.Choice("完成编辑", "done")
                ]
            ).ask()
            
            if action == "add":
                friendly_name = self.questionary.text(
                    "输入友好名称:",
                    validate=lambda text: len(text) > 0 or "友好名称不能为空"
                ).ask()
                
                if not friendly_name:
                    continue
                
                if friendly_name in model_mappings:
                    print(f"友好名称 '{friendly_name}' 已存在")
                    continue
                
                actual_id = self.questionary.text(
                    f"输入实际模型ID (对应 {friendly_name}):",
                    validate=lambda text: len(text) > 0 or "实际模型ID不能为空"
                ).ask()
                
                if actual_id:
                    model_mappings[friendly_name] = actual_id
            
            elif action == "edit" and model_mappings:
                # 准备选项列表
                mapping_list = list(model_mappings.items())
                index = self.questionary.select(
                    "选择要编辑的映射:",
                    choices=[f"{i+1}. {name} -> {id}" for i, (name, id) in enumerate(mapping_list)] + ["取消"]
                ).ask()
                
                if index != "取消":
                    i = int(index.split(".")[0]) - 1
                    friendly_name, actual_id = mapping_list[i]
                    
                    edit_field = self.questionary.select(
                        "编辑哪个字段:",
                        choices=[
                            self.Choice("友好名称", "friendly_name"),
                            self.Choice("实际模型ID", "actual_id"),
                            self.Choice("取消", "cancel")
                        ]
                    ).ask()
                    
                    if edit_field == "friendly_name":
                        new_name = self.questionary.text(
                            "输入新的友好名称:",
                            default=friendly_name,
                            validate=lambda text: len(text) > 0 or "友好名称不能为空"
                        ).ask()
                        
                        if new_name and new_name != friendly_name:
                            if new_name in model_mappings:
                                print(f"友好名称 '{new_name}' 已存在")
                            else:
                                # 删除旧映射并添加新映射
                                del model_mappings[friendly_name]
                                model_mappings[new_name] = actual_id
                    
                    elif edit_field == "actual_id":
                        new_id = self.questionary.text(
                            "输入新的实际模型ID:",
                            default=actual_id,
                            validate=lambda text: len(text) > 0 or "实际模型ID不能为空"
                        ).ask()
                        
                        if new_id:
                            model_mappings[friendly_name] = new_id
            
            elif action == "delete" and model_mappings:
                # 准备选项列表
                mapping_list = list(model_mappings.items())
                index = self.questionary.select(
                    "选择要删除的映射:",
                    choices=[f"{i+1}. {name} -> {id}" for i, (name, id) in enumerate(mapping_list)] + ["取消"]
                ).ask()
                
                if index != "取消":
                    i = int(index.split(".")[0]) - 1
                    friendly_name = mapping_list[i][0]
                    
                    confirm = self.questionary.confirm(f"确定要删除映射 '{friendly_name}' 吗?").ask()
                    
                    if confirm:
                        del model_mappings[friendly_name]
            
            elif action == "done":
                break
        
        # 更新配置
        if model_mappings:
            config['model_mappings'] = model_mappings
        elif 'model_mappings' in config:
            del config['model_mappings']
    
    def _edit_custom_headers(self, config: Dict[str, Any]) -> None:
        """
        编辑自定义请求头
        
        Args:
            config (Dict[str, Any]): 服务商配置字典
        """
        custom_headers = config.get('custom_headers', {})
        
        while True:
            # 显示当前自定义请求头
            print("\n当前自定义请求头:")
            for i, (name, value) in enumerate(custom_headers.items()):
                print(f"{i+1}. {name}: {value}")
            
            action = self.questionary.select(
                "选择操作:",
                choices=[
                    self.Choice("添加新请求头", "add"),
                    self.Choice("编辑现有请求头", "edit"),
                    self.Choice("删除请求头", "delete"),
                    self.Choice("完成编辑", "done")
                ]
            ).ask()
            
            if action == "add":
                header_name = self.questionary.text(
                    "输入请求头名称:",
                    validate=lambda text: len(text) > 0 or "请求头名称不能为空"
                ).ask()
                
                if not header_name:
                    continue
                
                if header_name in custom_headers:
                    print(f"请求头 '{header_name}' 已存在")
                    continue
                
                header_value = self.questionary.text(
                    f"输入请求头值 (对应 {header_name}):",
                    validate=lambda text: len(text) > 0 or "请求头值不能为空"
                ).ask()
                
                if header_value:
                    custom_headers[header_name] = header_value
            
            elif action == "edit" and custom_headers:
                # 准备选项列表
                header_list = list(custom_headers.items())
                index = self.questionary.select(
                    "选择要编辑的请求头:",
                    choices=[f"{i+1}. {name}: {value}" for i, (name, value) in enumerate(header_list)] + ["取消"]
                ).ask()
                
                if index != "取消":
                    i = int(index.split(".")[0]) - 1
                    header_name, header_value = header_list[i]
                    
                    edit_field = self.questionary.select(
                        "编辑哪个字段:",
                        choices=[
                            self.Choice("请求头名称", "header_name"),
                            self.Choice("请求头值", "header_value"),
                            self.Choice("取消", "cancel")
                        ]
                    ).ask()
                    
                    if edit_field == "header_name":
                        new_name = self.questionary.text(
                            "输入新的请求头名称:",
                            default=header_name,
                            validate=lambda text: len(text) > 0 or "请求头名称不能为空"
                        ).ask()
                        
                        if new_name and new_name != header_name:
                            if new_name in custom_headers:
                                print(f"请求头 '{new_name}' 已存在")
                            else:
                                # 删除旧请求头并添加新请求头
                                del custom_headers[header_name]
                                custom_headers[new_name] = header_value
                    
                    elif edit_field == "header_value":
                        new_value = self.questionary.text(
                            "输入新的请求头值:",
                            default=header_value,
                            validate=lambda text: len(text) > 0 or "请求头值不能为空"
                        ).ask()
                        
                        if new_value:
                            custom_headers[header_name] = new_value
            
            elif action == "delete" and custom_headers:
                # 准备选项列表
                header_list = list(custom_headers.items())
                index = self.questionary.select(
                    "选择要删除的请求头:",
                    choices=[f"{i+1}. {name}: {value}" for i, (name, value) in enumerate(header_list)] + ["取消"]
                ).ask()
                
                if index != "取消":
                    i = int(index.split(".")[0]) - 1
                    header_name = header_list[i][0]
                    
                    confirm = self.questionary.confirm(f"确定要删除请求头 '{header_name}' 吗?").ask()
                    
                    if confirm:
                        del custom_headers[header_name]
            
            elif action == "done":
                break
        
        # 更新配置
        if custom_headers:
            config['custom_headers'] = custom_headers
        elif 'custom_headers' in config:
            del config['custom_headers']
    
    def _delete_provider(self) -> None:
        """
        删除服务商配置
        """
        # 获取所有服务商名称
        provider_names = self.config_manager.get_all_provider_names()
        if not provider_names:
            print("没有配置任何服务商")
            return
        
        # 选择要删除的服务商
        provider_name = self.questionary.select(
            "选择要删除的服务商:",
            choices=provider_names + ["返回"]
        ).ask()
        
        if provider_name == "返回":
            return
        
        # 确认删除
        confirm = self.questionary.confirm(f"确定要删除服务商 '{provider_name}' 吗? 此操作不可撤销!").ask()
        
        if confirm:
            if self.config_manager.delete_provider(provider_name):
                print(f"成功删除服务商: {provider_name}")
            else:
                print(f"删除服务商失败: {provider_name}")
    
    def _list_providers(self) -> None:
        """
        列出所有服务商
        """
        provider_names = self.config_manager.get_all_provider_names()
        if not provider_names:
            print("没有配置任何服务商")
            return
        
        print("\n所有服务商:")
        for i, name in enumerate(provider_names):
            print(f"{i+1}. {name}")
    
    def _view_provider(self) -> None:
        """
        查看服务商详情
        """
        # 获取所有服务商名称
        provider_names = self.config_manager.get_all_provider_names()
        if not provider_names:
            print("没有配置任何服务商")
            return
        
        # 选择要查看的服务商
        provider_name = self.questionary.select(
            "选择要查看的服务商:",
            choices=provider_names + ["返回"]
        ).ask()
        
        if provider_name == "返回":
            return
        
        # 获取服务商配置
        config = self.config_manager.get_provider_config(provider_name)
        if not config:
            print(f"错误: 无法获取服务商 '{provider_name}' 的配置")
            return
        
        # 显示服务商详情
        print(f"\n服务商 '{provider_name}' 详情:")
        print(f"API类型: {config['api_type']}")
        
        if 'base_url' in config:
            print(f"基础URL: {config['base_url']}")
        
        # 显示API密钥（部分隐藏）
        print("API密钥:")
        for i, key in enumerate(config.get('api_keys', [])):
            masked_key = key[:4] + "*" * (len(key) - 8) + key[-4:] if len(key) > 8 else "*" * len(key)
            print(f"  {i+1}. {masked_key}")
        
        # 显示支持的模型
        supported_models = config.get('supported_models', [])
        if supported_models:
            print(f"支持的模型 ({len(supported_models)}):")
            for i, model in enumerate(supported_models[:10]):  # 只显示前10个
                print(f"  {i+1}. {model}")
            if len(supported_models) > 10:
                print(f"  ... 还有 {len(supported_models) - 10} 个模型")
        else:
            print("支持的模型: 无")
        
        # 显示模型映射
        model_mappings = config.get('model_mappings', {})
        if model_mappings:
            print(f"模型映射 ({len(model_mappings)}):")
            for i, (name, id) in enumerate(list(model_mappings.items())[:10]):  # 只显示前10个
                print(f"  {i+1}. {name} -> {id}")
            if len(model_mappings) > 10:
                print(f"  ... 还有 {len(model_mappings) - 10} 个映射")
        else:
            print("模型映射: 无")
        
        # 显示自定义请求头
        custom_headers = config.get('custom_headers', {})
        if custom_headers:
            print(f"自定义请求头 ({len(custom_headers)}):")
            for name, value in custom_headers.items():
                print(f"  {name}: {value}")
        else:
            print("自定义请求头: 无")
    
    def _test_models_menu(self) -> None:
        """
        模型测试子菜单
        """
        # 获取所有服务商名称
        provider_names = self.config_manager.get_all_provider_names()
        if not provider_names:
            print("没有配置任何服务商，请先添加服务商配置")
            return
        
        # 选择服务商
        provider_name = self.questionary.select(
            "选择要测试的服务商:",
            choices=provider_names + ["返回主菜单"]
        ).ask()
        
        if provider_name == "返回主菜单":
            return
        
        # 获取服务商配置
        provider_config = self.config_manager.get_provider_config(provider_name)
        if not provider_config:
            print(f"错误: 无法获取服务商 '{provider_name}' 的配置")
            return
        
        # 实例化ModelTestSystem
        test_system = ModelTestSystem(provider_config)
        
        # 加载模型
        print(f"正在加载服务商 '{provider_name}' 的模型...")
        if not test_system.load_models_for_provider():
            print("加载模型失败，请检查服务商配置或网络连接")
            return
        
        # 选择模型进行测试
        models_to_test = test_system._select_models_for_testing()
        if not models_to_test:
            print("未选择任何模型进行测试")
            return
        
        # 执行测试
        print(f"开始测试 {len(models_to_test)} 个模型...")
        test_system.run_tests(models_to_test)
    
    def _export_data_menu(self) -> None:
        """
        导出配置数据子菜单
        """
        while True:
            choice = self.questionary.select(
                "导出配置数据:",
                choices=[
                    self.Choice("1. 导出指定服务商的模型映射", "export_mappings"),
                    self.Choice("2. 导出指定服务商的支持模型列表", "export_models"),
                    self.Choice("3. 导出所有服务商的API Key及请求地址", "export_api_keys"),
                    self.Choice("4. 导出所有服务商的完整配置", "export_all"),
                    self.Choice("5. 返回主菜单", "back")
                ]
            ).ask()
            
            if choice == "export_mappings":
                self._export_model_mappings()
            elif choice == "export_models":
                self._export_supported_models()
            elif choice == "export_api_keys":
                self._export_api_keys()
            elif choice == "export_all":
                self._export_all_configs()
            elif choice == "back":
                break
    
    def _export_model_mappings(self) -> None:
        """
        导出指定服务商的模型映射
        """
        # 获取所有服务商名称
        provider_names = self.config_manager.get_all_provider_names()
        if not provider_names:
            print("没有配置任何服务商")
            return
        
        # 选择服务商
        provider_name = self.questionary.select(
            "选择要导出模型映射的服务商:",
            choices=provider_names + ["返回"]
        ).ask()
        
        if provider_name == "返回":
            return
        
        # 选择导出方式
        export_method = self.questionary.select(
            "选择导出方式:",
            choices=[
                self.Choice("导出到文件", "file"),
                self.Choice("复制到剪贴板", "clipboard"),
                self.Choice("取消", "cancel")
            ]
        ).ask()
        
        if export_method == "cancel":
            return
        
        # 执行导出
        to_clipboard = (export_method == "clipboard")
        self.export_utils.export_model_mappings(provider_name, to_clipboard)
    
    def _export_supported_models(self) -> None:
        """
        导出指定服务商的支持模型列表
        """
        # 获取所有服务商名称
        provider_names = self.config_manager.get_all_provider_names()
        if not provider_names:
            print("没有配置任何服务商")
            return
        
        # 选择服务商
        provider_name = self.questionary.select(
            "选择要导出模型列表的服务商:",
            choices=provider_names + ["返回"]
        ).ask()
        
        if provider_name == "返回":
            return
        
        # 选择模型类型
        model_type = self.questionary.select(
            "选择要导出的模型类型:",
            choices=[
                self.Choice("原始模型列表", "original"),
                self.Choice("映射模型名称列表", "mapped"),
                self.Choice("取消", "cancel")
            ]
        ).ask()
        
        if model_type == "cancel":
            return
        
        # 选择导出方式
        export_method = self.questionary.select(
            "选择导出方式:",
            choices=[
                self.Choice("导出到文件", "file"),
                self.Choice("复制到剪贴板", "clipboard"),
                self.Choice("取消", "cancel")
            ]
        ).ask()
        
        if export_method == "cancel":
            return
        
        # 执行导出
        use_mappings = (model_type == "mapped")
        to_clipboard = (export_method == "clipboard")
        self.export_utils.export_supported_models(provider_name, use_mappings, to_clipboard)
    
    def _export_api_keys(self) -> None:
        """
        导出所有服务商的API Key及请求地址
        """
        # 选择导出方式
        export_method = self.questionary.select(
            "选择导出方式:",
            choices=[
                self.Choice("导出到文件", "file"),
                self.Choice("复制到剪贴板", "clipboard"),
                self.Choice("取消", "cancel")
            ]
        ).ask()
        
        if export_method == "cancel":
            return
        
        # 执行导出
        to_clipboard = (export_method == "clipboard")
        self.export_utils.export_api_keys_and_urls(to_clipboard)
    
    def _export_all_configs(self) -> None:
        """
        导出所有服务商的完整配置
        """
        # 选择导出方式
        export_method = self.questionary.select(
            "选择导出方式:",
            choices=[
                self.Choice("导出到文件", "file"),
                self.Choice("复制到剪贴板", "clipboard"),
                self.Choice("取消", "cancel")
            ]
        ).ask()
        
        if export_method == "cancel":
            return
        
        # 执行导出
        to_clipboard = (export_method == "clipboard")
        self.export_utils.export_all_configs(to_clipboard)
    
    def _query_model(self) -> None:
        """
        查询模型信息
        """
        # 输入模型名称
        model_name = self.questionary.text(
            "输入要查询的模型名称 (原始名称或映射名称):",
            validate=lambda text: len(text) > 0 or "模型名称不能为空"
        ).ask()
        
        if not model_name:
            return
        
        # 查找模型
        providers = self.config_manager.find_model_provider(model_name)
        
        if not providers:
            print(f"未找到提供模型 '{model_name}' 的服务商")
            return
        
        # 显示结果
        print(f"\n找到 {len(providers)} 个提供模型 '{model_name}' 的服务商:")
        for i, provider in enumerate(providers):
            print(f"\n{i+1}. 服务商: {provider['provider_name']}")
            print(f"   实际模型名称: {provider['actual_model_name']}")
            print(f"   基础URL: {provider['base_url'] or '默认'}")
            
            # 显示API密钥（部分隐藏）
            api_key = provider['api_key']
            if api_key:
                masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "*" * len(api_key)
                print(f"   API密钥: {masked_key}")
            
            # 显示自定义请求头
            custom_headers = provider.get('custom_headers', {})
            if custom_headers:
                print("   自定义请求头:")
                for name, value in custom_headers.items():
                    print(f"     {name}: {value}")


def main():
    """
    主函数
    """
    cli = CLI()
    cli.run()


if __name__ == "__main__":
    main()