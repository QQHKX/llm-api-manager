# -*- coding: utf-8 -*-
"""
错误处理与诊断模块

定义了LLM API测试过程中可能遇到的各种错误类型、分类和解决方案。
"""

# 错误手册：映射HTTP状态码/API特定错误码到错误分类和解决方案
ERROR_HANDBOOK = {
    # HTTP状态码错误
    "400": {
        "category": "请求错误",
        "solution": "检查请求参数是否正确，特别是模型名称、温度值等是否在有效范围内。"
    },
    "401": {
        "category": "认证失败",
        "solution": "API密钥无效或已过期，请更新API密钥。"
    },
    "403": {
        "category": "权限不足",
        "solution": "当前API密钥没有访问此模型的权限，请联系服务提供商升级权限。"
    },
    "404": {
        "category": "资源不存在",
        "solution": "请求的模型不存在或端点URL错误，请检查模型ID和API端点。"
    },
    "429": {
        "category": "请求过多",
        "solution": "已超出API速率限制，请减少请求频率或联系服务提供商提高限额。"
    },
    "500": {
        "category": "服务器错误",
        "solution": "服务提供商内部错误，请稍后重试或联系服务提供商支持。"
    },
    "502": {
        "category": "网关错误",
        "solution": "服务提供商网关错误，请稍后重试。"
    },
    "503": {
        "category": "服务不可用",
        "solution": "服务提供商暂时不可用，可能正在维护，请稍后重试。"
    },
    "504": {
        "category": "网关超时",
        "solution": "服务提供商响应超时，请检查网络连接或稍后重试。"
    },
    
    # API特定错误
    "model_not_found": {
        "category": "模型不存在",
        "solution": "指定的模型ID不存在，请检查模型名称是否正确。"
    },
    "context_length_exceeded": {
        "category": "上下文长度超限",
        "solution": "请求的提示内容超出模型最大上下文长度，请减少输入内容或使用支持更长上下文的模型。"
    },
    "content_filter": {
        "category": "内容过滤",
        "solution": "请求内容被服务提供商的内容过滤系统拦截，请修改请求内容。"
    },
    "quota_exceeded": {
        "category": "配额超限",
        "solution": "已超出账户配额限制，请充值或联系服务提供商提高配额。"
    },
    
    # 网络和连接错误
    "connection_error": {
        "category": "连接错误",
        "solution": "无法连接到服务提供商API，请检查网络连接和防火墙设置。"
    },
    "timeout": {
        "category": "请求超时",
        "solution": "请求超时，可能是网络延迟或服务提供商响应慢，请稍后重试或增加超时设置。"
    },
    "ssl_error": {
        "category": "SSL错误",
        "solution": "SSL证书验证失败，请检查系统证书配置或尝试禁用SSL验证（不推荐用于生产环境）。"
    },
    
    # 默认错误
    "unknown": {
        "category": "未知错误",
        "solution": "发生未知错误，请检查日志获取详细信息并联系服务提供商支持。"
    }
}


def parse_error(status_code, response_body):
    """
    解析HTTP错误响应
    
    Args:
        status_code (int): HTTP状态码
        response_body (str): 响应体内容
        
    Returns:
        dict: 包含错误分类和解决方案的字典
    """
    status_str = str(status_code)
    error_info = ERROR_HANDBOOK.get(status_str, ERROR_HANDBOOK["unknown"])
    
    # 尝试从响应体中提取更详细的错误信息
    error_code = "unknown"
    try:
        import json
        response_json = json.loads(response_body)
        if "error" in response_json:
            error_data = response_json["error"]
            if "type" in error_data:
                error_code = error_data["type"]
            elif "code" in error_data:
                error_code = error_data["code"]
            
            # 如果在ERROR_HANDBOOK中找到特定的API错误码，使用它的分类和解决方案
            if error_code in ERROR_HANDBOOK:
                error_info = ERROR_HANDBOOK[error_code]
    except (json.JSONDecodeError, KeyError, TypeError):
        pass
    
    return {
        "error_code": error_code,
        "error_category": error_info["category"],
        "solution": error_info["solution"]
    }


def parse_exception(exception_obj):
    """
    解析Python异常
    
    Args:
        exception_obj (Exception): 异常对象
        
    Returns:
        dict: 包含错误分类和解决方案的字典
    """
    import socket
    import ssl
    from http.client import HTTPException
    
    error_code = type(exception_obj).__name__
    
    # 根据异常类型确定错误分类
    if isinstance(exception_obj, socket.timeout) or "timeout" in str(exception_obj).lower():
        error_info = ERROR_HANDBOOK["timeout"]
    elif isinstance(exception_obj, (ConnectionError, socket.error)):
        error_info = ERROR_HANDBOOK["connection_error"]
    elif isinstance(exception_obj, ssl.SSLError):
        error_info = ERROR_HANDBOOK["ssl_error"]
    elif isinstance(exception_obj, HTTPException):
        error_info = ERROR_HANDBOOK["unknown"]
        error_info["solution"] = f"HTTP客户端错误: {str(exception_obj)}. 请检查请求格式和网络连接。"
    else:
        error_info = ERROR_HANDBOOK["unknown"]
    
    return {
        "error_code": error_code,
        "error_category": error_info["category"],
        "solution": error_info["solution"]
    }