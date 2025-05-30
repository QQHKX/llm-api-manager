# -*- coding: utf-8 -*-
"""
模型测试系统模块

负责针对从ProviderConfigManager中选择的特定服务商的模型执行并发API测试。
"""

import http.client
import json
import time
import threading
import csv
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse

from .utils.helpers import clear_console, extract_domain, format_timestamp, generate_filename, create_progress_bar
from .utils.error_handbook import parse_error, parse_exception


class ModelTestSystem:
    """
    模型测试系统类
    
    负责针对特定服务商的模型执行并发API测试，使用由ProviderConfigManager提供的配置详情。
    """
    
    # 默认全局测试配置
    DEFAULT_GLOBAL_TEST_CONFIG = {
        'max_workers': 50,              # 最大并发线程数
        'request_timeout': 30,          # 单次API请求超时时间（秒）
        'max_retries': 3,               # 单个模型测试的最大重试次数
        'global_timeout': 300,          # 测试总运行时间上限（秒）
        'status_refresh': 0.2,          # 状态监控界面刷新频率（秒）
        'test_prompt': {                # 标准化的测试负载JSON结构
            'messages': [
                {'role': 'user', 'content': 'Respond with \'OK\''}
            ],
            'model': 'placeholder',      # 将动态填充
            'temperature': 0.1,
            'max_tokens': 5
        }
    }
    
    def __init__(self, provider_config: Dict[str, Any], global_test_config: Optional[Dict[str, Any]] = None):
        """
        初始化模型测试系统
        
        Args:
            provider_config (Dict[str, Any]): 用户从ProviderConfigManager选择的单个服务商的配置字典
            global_test_config (Optional[Dict[str, Any]], optional): 全局测试配置字典
        """
        self.provider_config = provider_config
        self.config = global_test_config or self.DEFAULT_GLOBAL_TEST_CONFIG
        
        # 提取服务商信息
        self.provider_name = provider_config['name']
        self.api_type = provider_config['api_type']
        self.base_url = provider_config.get('base_url', '')
        
        # 选择API密钥（简单实现：使用第一个密钥）
        self.api_key = provider_config['api_keys'][0] if provider_config['api_keys'] else ''
        
        # 自定义请求头
        self.custom_headers = provider_config.get('custom_headers', {})
        
        # 从base_url提取域名
        self.domain = extract_domain(self.base_url)
        
        # 设置HTTP请求头
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        # 添加自定义请求头
        self.headers.update(self.custom_headers)
        
        # 初始化内部状态变量
        self.models_data = []  # 针对当前选定服务商的模型数据
        self.categories = {}   # 如果能从/models端点获取分类信息
        
        # 并发控制变量
        self.status_lock = threading.Lock()
        self.progress_lock = threading.Lock()
        self.active_tasks = {}  # 当前活动任务状态
        self.should_stop = False  # 全局停止标志
        
        # 进度统计
        self.total_tasks = 0
        self.completed_tasks = 0
    
    def load_models_for_provider(self) -> bool:
        """
        加载当前选定服务商的模型列表
        
        尝试从服务商的API端点获取模型列表，如果失败则使用配置中的supported_models
        
        Returns:
            bool: 加载成功返回True，否则返回False
        """
        # 首先检查provider_config中的supported_models
        if 'supported_models' in self.provider_config and self.provider_config['supported_models']:
            self.models_data = [{'id': model_id} for model_id in self.provider_config['supported_models']]
            print(f"已从配置加载 {len(self.models_data)} 个模型")
            return True
        
        # 如果supported_models为空，尝试从API获取
        if not self.base_url:
            print("错误: 未提供base_url，无法从API获取模型列表")
            return False
        
        try:
            # 确定模型列表API端点
            endpoint = '/v1/models'
            if self.api_type == 'azure-openai':
                # Azure OpenAI API可能有不同的端点格式
                endpoint = '/openai/deployments?api-version=2023-05-15'
            
            # 解析URL
            parsed_url = urlparse(self.base_url)
            conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=self.config['request_timeout'])
            
            # 发送请求
            conn.request('GET', endpoint, headers=self.headers)
            response = conn.getresponse()
            response_data = response.read().decode('utf-8')
            
            if response.status == 200:
                data = json.loads(response_data)
                
                # 解析响应数据，格式可能因API类型而异
                if self.api_type == 'azure-openai':
                    # Azure OpenAI API格式
                    self.models_data = data.get('data', [])
                else:
                    # 标准OpenAI API格式
                    self.models_data = data.get('data', [])
                    
                    # 如果API返回信息包含owned_by，可据此进行分类
                    for model in self.models_data:
                        if 'owned_by' in model:
                            category = model['owned_by']
                            if category not in self.categories:
                                self.categories[category] = []
                            self.categories[category].append(model['id'])
                
                # 按名称排序模型
                self.models_data.sort(key=lambda x: x.get('id', ''))
                
                print(f"已从API加载 {len(self.models_data)} 个模型")
                return True
            else:
                error_info = parse_error(response.status, response_data)
                print(f"从API获取模型列表失败: {error_info['error_category']} - {error_info['solution']}")
                return False
        
        except Exception as e:
            error_info = parse_exception(e)
            print(f"从API获取模型列表时发生错误: {error_info['error_category']} - {error_info['solution']}")
            return False
    
    def _select_models_for_testing(self) -> List[str]:
        """
        交互式模型选择菜单
        
        在用户选定一个服务商并加载其模型后呈现，让用户选择要测试的模型
        
        Returns:
            List[str]: 包含待测试的实际模型ID的列表
        """
        try:
            import questionary
            from questionary import Choice
        except ImportError:
            print("错误: 未安装questionary库，无法显示交互式菜单。请使用pip install questionary安装。")
            return []
        
        if not self.models_data:
            print("错误: 未加载任何模型，请先调用load_models_for_provider()方法")
            return []
        
        # 准备模型选择列表
        model_choices = []
        model_mappings = self.provider_config.get('model_mappings', {})
        
        # 添加所有模型选项
        for model_data in self.models_data:
            model_id = model_data.get('id', '')
            if not model_id:
                continue
            
            # 查找友好名称（如果存在映射）
            friendly_name = None
            for map_name, map_id in model_mappings.items():
                if map_id == model_id:
                    friendly_name = map_name
                    break
            
            # 构建显示名称
            display_name = model_id
            if friendly_name:
                display_name = f"{friendly_name} ({model_id})"
            
            model_choices.append(Choice(title=display_name, value=model_id))
        
        # 添加特殊选项
        model_choices.insert(0, Choice(title="测试此服务商的所有已加载模型", value="ALL_MODELS"))
        model_choices.append(Choice(title="返回服务商选择界面", value="BACK"))
        
        # 显示选择菜单
        print(f"\n服务商 '{self.provider_name}' 的可用模型:")
        selection = questionary.select(
            "请选择要测试的模型:",
            choices=model_choices
        ).ask()
        
        if selection == "BACK":
            return []
        elif selection == "ALL_MODELS":
            return [model.get('id') for model in self.models_data if model.get('id')]
        else:
            # 如果用户选择了特定模型，则返回单个模型ID的列表
            return [selection]
    
    def run_tests(self, models_to_test: List[str]) -> None:
        """
        运行模型测试
        
        Args:
            models_to_test (List[str]): 要测试的模型ID列表
        """
        if not models_to_test:
            print("没有选择任何模型进行测试")
            return
        
        # 初始化计数器和状态变量
        self.total_tasks = len(models_to_test)
        self.completed_tasks = 0
        self.active_tasks = {}
        self.should_stop = False
        
        # 创建结果列表
        results = []
        
        # 启动全局超时计时器
        global_timeout_timer = threading.Timer(self.config['global_timeout'], self._handle_global_timeout)
        global_timeout_timer.daemon = True
        global_timeout_timer.start()
        
        # 启动状态监控线程
        monitor_thread = threading.Thread(target=self._status_monitor)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            # 使用ThreadPoolExecutor并发执行测试
            with ThreadPoolExecutor(max_workers=min(self.config['max_workers'], len(models_to_test))) as executor:
                # 提交所有测试任务
                future_to_model = {executor.submit(self._test_model_once, model_id): model_id for model_id in models_to_test}
                
                # 收集结果
                for future in future_to_model:
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        model_id = future_to_model[future]
                        error_info = parse_exception(e)
                        results.append({
                            'model_id': model_id,
                            'provider_name': self.provider_name,
                            'timestamp': format_timestamp(),
                            'status': 'error',
                            'latency': 0,
                            'retries': 0,
                            'error_code': error_info['error_code'],
                            'error_category': error_info['error_category'],
                            'solution': error_info['solution'],
                            'response': str(e)
                        })
        
        finally:
            # 停止全局超时计时器
            global_timeout_timer.cancel()
            
            # 设置停止标志，等待监控线程结束
            self.should_stop = True
            monitor_thread.join(timeout=1.0)
            
            # 清空控制台并显示结果
            clear_console()
            self._show_results(results)
            
            # 生成报告
            report_file = self.generate_report(results)
            if report_file:
                print(f"\n测试报告已保存到: {report_file}")
    
    def _test_model_once(self, model_id: str) -> Dict[str, Any]:
        """
        测试单个模型
        
        Args:
            model_id (str): 当前服务商的实际模型ID
            
        Returns:
            Dict[str, Any]: 包含详细测试结果的字典
        """
        # 初始化结果字典
        result = {
            'model_id': model_id,
            'provider_name': self.provider_name,
            'timestamp': format_timestamp(),
            'status': 'pending',
            'latency': 0,
            'retries': 0,
            'error_code': '',
            'error_category': '',
            'solution': '',
            'response': ''
        }
        
        # 检查全局停止标志
        if self.should_stop:
            result['status'] = 'global_timeout'
            return result
        
        # 构建请求负载
        payload = self.config['test_prompt'].copy()
        payload['model'] = model_id
        
        # 确定API端点
        endpoint = '/v1/chat/completions'
        if self.api_type == 'anthropic':
            endpoint = '/v1/messages'
        elif self.api_type == 'google-vertex-ai':
            # Google Vertex AI可能有不同的端点格式
            endpoint = '/v1/models/{model}:predict'.format(model=model_id)
        
        # 更新活动任务状态
        with self.status_lock:
            self.active_tasks[model_id] = {
                'status': 'starting',
                'start_time': time.time(),
                'retries': 0,
                'latency': 0
            }
        
        # 重试逻辑
        retry_count = 0
        max_retries = self.config['max_retries']
        
        while retry_count <= max_retries:
            # 检查全局停止标志
            if self.should_stop:
                result['status'] = 'global_timeout'
                break
            
            # 更新重试计数
            result['retries'] = retry_count
            
            # 更新活动任务状态
            with self.status_lock:
                self.active_tasks[model_id]['status'] = 'running' if retry_count == 0 else f'retry_{retry_count}'
                self.active_tasks[model_id]['retries'] = retry_count
            
            try:
                # 解析URL
                parsed_url = urlparse(self.base_url)
                conn = http.client.HTTPSConnection(parsed_url.netloc, timeout=self.config['request_timeout'])
                
                # 发送请求
                start_time = time.time()
                conn.request('POST', endpoint, body=json.dumps(payload), headers=self.headers)
                response = conn.getresponse()
                response_data = response.read().decode('utf-8')
                end_time = time.time()
                
                # 计算延迟（毫秒）
                latency = int((end_time - start_time) * 1000)
                result['latency'] = latency
                
                # 更新活动任务状态
                with self.status_lock:
                    self.active_tasks[model_id]['latency'] = latency
                
                # 处理响应
                if response.status == 200:
                    # 成功
                    result['status'] = 'success'
                    result['response'] = response_data
                    break
                else:
                    # HTTP错误
                    error_info = parse_error(response.status, response_data)
                    result['status'] = f"{response.status}/{error_info['error_code']}"
                    result['error_code'] = error_info['error_code']
                    result['error_category'] = error_info['error_category']
                    result['solution'] = error_info['solution']
                    result['response'] = response_data
                    
                    # 某些错误不应重试
                    if response.status in [400, 401, 403, 404]:
                        break
            
            except Exception as e:
                # Python异常
                error_info = parse_exception(e)
                result['status'] = f"exception/{error_info['error_code']}"
                result['error_code'] = error_info['error_code']
                result['error_category'] = error_info['error_category']
                result['solution'] = error_info['solution']
                result['response'] = str(e)
            
            # 增加重试计数
            retry_count += 1
            
            # 如果还有重试次数，等待一段时间后重试（简单的指数退避）
            if retry_count <= max_retries:
                backoff_time = min(2 ** retry_count, 10)  # 最多等待10秒
                time.sleep(backoff_time)
        
        # 测试结束，从活动任务中移除
        with self.status_lock:
            if model_id in self.active_tasks:
                del self.active_tasks[model_id]
        
        # 原子地增加已完成任务计数
        with self.progress_lock:
            self.completed_tasks += 1
        
        return result
    
    def _status_monitor(self) -> None:
        """
        实时状态监控
        
        在独立线程中运行，定期刷新控制台显示当前测试状态
        """
        while not self.should_stop:
            # 清空控制台
            clear_console()
            
            # 获取当前状态的快照
            with self.status_lock:
                active_tasks_snapshot = self.active_tasks.copy()
            
            with self.progress_lock:
                completed = self.completed_tasks
                total = self.total_tasks
            
            # 显示当前并发数和进度
            print(f"服务商: {self.provider_name}")
            print(f"当前并发数: {len(active_tasks_snapshot)}/{self.config['max_workers']}")
            print(create_progress_bar(completed, total))
            
            # 显示当前测试中的模型
            if active_tasks_snapshot:
                print("\n当前测试中的模型:")
                for model_id, task_info in active_tasks_snapshot.items():
                    status_icon = "🔄" if task_info['status'] == 'running' else "⏹️"
                    latency = task_info['latency']
                    retries = task_info['retries']
                    print(f"{status_icon} {model_id} ({self.provider_name}) - {latency}ms - 重试: {retries}")
            
            # 休眠一段时间
            time.sleep(self.config['status_refresh'])
    
    def _handle_global_timeout(self) -> None:
        """
        处理全局超时
        
        由全局超时计时器调用，设置停止标志
        """
        print(f"\n警告: 已达到全局超时限制 ({self.config['global_timeout']}秒)，正在停止测试...")
        self.should_stop = True
    
    def _show_results(self, results: List[Dict[str, Any]]) -> None:
        """
        显示测试结果
        
        Args:
            results (List[Dict[str, Any]]): 测试结果列表
        """
        print("\n测试结果摘要:")
        print("-" * 80)
        
        success_count = 0
        failure_count = 0
        
        for result in results:
            if result['status'] == 'success':
                status_icon = "✅"
                success_count += 1
            else:
                status_icon = "❌"
                failure_count += 1
            
            print(f"{status_icon} {result['provider_name']} - {result['model_id']} - 状态: {result['status']} - 延迟: {result['latency']}ms - 重试: {result['retries']}")
        
        print("-" * 80)
        print(f"总计: {len(results)} 个模型测试完成，成功: {success_count}，失败: {failure_count}")
    
    def generate_report(self, results: List[Dict[str, Any]]) -> str:
        """
        生成测试报告
        
        Args:
            results (List[Dict[str, Any]]): 测试结果列表
            
        Returns:
            str: 报告文件路径
        """
        try:
            # 生成报告文件名
            timestamp = time.time()
            report_filename = generate_filename("model_test_report", "csv", timestamp)
            
            # 确保data目录存在
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            report_path = os.path.join(data_dir, report_filename)
            
            # 定义CSV列
            fieldnames = [
                'timestamp',
                'provider_name',
                'category',
                'model_id',
                'status',
                'error_code',
                'error_category',
                'solution',
                'latency_ms',
                'retries',
                'response_content'
            ]
            
            # 写入CSV文件
            with open(report_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    # 查找模型分类（如果有）
                    category = ''
                    for cat, models in self.categories.items():
                        if result['model_id'] in models:
                            category = cat
                            break
                    
                    # 写入行
                    writer.writerow({
                        'timestamp': result['timestamp'],
                        'provider_name': result['provider_name'],
                        'category': category,
                        'model_id': result['model_id'],
                        'status': result['status'],
                        'error_code': result.get('error_code', ''),
                        'error_category': result.get('error_category', ''),
                        'solution': result.get('solution', ''),
                        'latency_ms': result['latency'],
                        'retries': result['retries'],
                        'response_content': result['response']
                    })
            
            return report_path
        
        except Exception as e:
            print(f"生成报告时发生错误: {e}")
            return ""