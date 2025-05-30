#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LLM API管理器主程序入口

提供一个命令行工具，用于管理多个LLM服务商的API配置和测试模型性能。
"""

import sys
import os

# 确保llm_api_manager包可以被导入
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from llm_api_manager.cli import main

if __name__ == "__main__":
    main()