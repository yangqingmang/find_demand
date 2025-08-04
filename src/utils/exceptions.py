#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自定义异常模块
定义项目中使用的自定义异常类
"""


class FindDemandError(Exception):
    """项目基础异常类"""
    
    def __init__(self, message: str, error_code: str = None):
        """
        初始化异常
        
        参数:
            message (str): 错误消息
            error_code (str): 错误代码
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
    
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class ConfigError(FindDemandError):
    """配置相关错误"""
    pass


class APIError(FindDemandError):
    """API调用相关错误"""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        """
        初始化API错误
        
        参数:
            message (str): 错误消息
            status_code (int): HTTP状态码
            response_data (dict): 响应数据
        """
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class DataError(FindDemandError):
    """数据处理相关错误"""
    pass


class ValidationError(FindDemandError):
    """数据验证相关错误"""
    pass


class FileOperationError(FindDemandError):
    """文件操作相关错误"""
    pass


class AnalysisError(FindDemandError):
    """分析过程相关错误"""
    pass


# 异常处理装饰器
def handle_exceptions(default_return=None, log_errors=True):
    """
    异常处理装饰器
    
    参数:
        default_return: 异常时的默认返回值
        log_errors (bool): 是否记录错误日志
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FindDemandError as e:
                if log_errors:
                    from .logger import error
                    error(f"业务异常 in {func.__name__}: {e}")
                return default_return
            except Exception as e:
                if log_errors:
                    from .logger import error
                    error(f"未知异常 in {func.__name__}: {e}")
                return default_return
        return wrapper
    return decorator


# 上下文管理器用于异常处理
class ExceptionHandler:
    """异常处理上下文管理器"""
    
    def __init__(self, default_return=None, reraise=False, log_errors=True):
        """
        初始化异常处理器
        
        参数:
            default_return: 异常时的默认返回值
            reraise (bool): 是否重新抛出异常
            log_errors (bool): 是否记录错误日志
        """
        self.default_return = default_return
        self.reraise = reraise
        self.log_errors = log_errors
        self.exception = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.exception = exc_val
            
            if self.log_errors:
                from .logger import error
                error(f"捕获异常: {exc_type.__name__}: {exc_val}")
            
            if self.reraise:
                return False  # 重新抛出异常
            else:
                return True  # 抑制异常
        
        return False
    
    def get_result(self, success_value):
        """
        获取结果值
        
        参数:
            success_value: 成功时的返回值
            
        返回:
            成功值或默认值
        """
        if self.exception is not None:
            return self.default_return
        return success_value