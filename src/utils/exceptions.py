#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常处理模块
定义项目中使用的自定义异常类
"""

class APIError(Exception):
    """API调用错误"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code

class ConfigError(Exception):
    """配置错误"""
    pass

class ValidationError(Exception):
    """验证错误"""
    pass

class ExceptionHandler:
    """异常处理器类，兼容现有代码"""
    
    @staticmethod
    def handle_api_error(error: Exception) -> str:
        """处理API错误"""
        if isinstance(error, APIError):
            return f"API错误: {str(error)}"
        return f"未知错误: {str(error)}"