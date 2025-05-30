# LLM API 管理器

一个用于管理和测试多个大型语言模型(LLM)服务商API的命令行工具。

## 项目概述

LLM API管理器是一个全面的工具，旨在简化开发者在多模型环境下的工作流程。它提供了以下核心功能：

- **服务商配置管理**：集中管理多个LLM服务商的API密钥、URL和模型映射
- **模型测试系统**：对选定的模型执行并发API测试，评估性能和稳定性
- **导出功能**：将配置数据导出为多种格式，便于集成到其他系统
- **交互式CLI界面**：提供友好的命令行界面，简化操作流程

## 功能特点

### 服务商配置管理

- 支持多种API类型（OpenAI、Azure OpenAI等）
- 集中管理API密钥和基础URL
- 维护模型映射，将友好名称映射到实际模型ID
- 存储支持的模型列表
- 管理自定义请求头

### 模型测试系统

- 交互式选择要测试的模型
- 并发执行API测试
- 实时状态监控
- 错误处理与诊断
- 生成测试报告

### 导出功能

- 导出模型映射
- 导出支持的模型列表
- 导出API密钥和URL
- 导出完整配置
- 支持导出到文件或剪贴板

## 安装

### 前提条件

- Python 3.8+

### 安装步骤

1. 克隆仓库：

```bash
git clone <repository-url>
cd llm-api-manager
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 启动程序

```bash
python main.py
```

### 主菜单选项

1. **管理LLM服务商配置**
   - 添加服务商
   - 编辑服务商
   - 删除服务商
   - 查看所有服务商
   - 查看服务商详情

2. **测试LLM模型**
   - 选择服务商
   - 选择模型
   - 执行测试
   - 查看测试结果

3. **导出配置数据**
   - 导出模型映射
   - 导出支持模型列表
   - 导出API Key及请求地址
   - 导出所有服务商的完整配置

4. **查询模型信息**
   - 通过模型名称查找服务商

## 配置示例

### 添加OpenAI服务商

```
服务商名称: OpenAI
API类型: openai
基础URL: (留空使用默认)
API密钥: sk-xxxxxxxxxxxxxxxxxxxx
支持的模型列表: gpt-3.5-turbo, gpt-4, gpt-4-turbo
```

### 添加Azure OpenAI服务商

```
服务商名称: AzureOpenAI
API类型: azure_openai
基础URL: https://your-resource-name.openai.azure.com
API密钥: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
支持的模型列表: gpt-35-turbo, gpt-4
模型映射: {"gpt-35-turbo": "deployment-name-1", "gpt-4": "deployment-name-2"}
```

## 开发

### 项目结构

```
llm-api-manager/
├── llm_api_manager/
│   ├── __init__.py
│   ├── cli.py                    # 命令行界面
│   ├── provider_config_manager.py # 服务商配置管理
│   ├── model_test_system.py      # 模型测试系统
│   ├── export_utils.py           # 导出功能
│   └── utils/
│       ├── __init__.py
│       ├── error_handbook.py     # 错误处理
│       └── helpers.py            # 辅助函数
├── main.py                       # 程序入口
├── requirements.txt              # 依赖项
└── README.md                     # 项目说明
```

### 运行测试

```bash
python -m pytest
```

## 许可证

[MIT](LICENSE)