#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API装饰器
自动处理API配额限制和降级逻辑
"""

from functools import wraps
from typing import Callable, Any, Dict
import pandas as pd
from .api_quota_manager import get_quota_manager

def with_quota_management(api_name: str, calls_per_request: int = 1, enable_fallback: bool = True):
    """
    API配额管理装饰器
    
    Args:
        api_name: API名称
        calls_per_request: 每次请求消耗的调用次数
        enable_fallback: 是否启用降级方案
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            quota_manager = get_quota_manager()
            
            # 检查配额
            quota_check = quota_manager.check_quota(api_name, calls_per_request)
            
            if quota_check["available"]:
                try:
                    # 执行原始函数
                    result = func(*args, **kwargs)
                    
                    # 成功后扣除配额
                    quota_manager.use_quota(api_name, calls_per_request)
                    
                    return result
                    
                except Exception as e:
                    print(f"⚠️ {api_name} API调用失败: {e}")
                    
                    # API调用失败，尝试降级方案
                    if enable_fallback and quota_check.get("use_fallback", True):
                        return quota_manager.get_fallback_data(api_name, **kwargs)
                    else:
                        raise e
            else:
                print(f"🚫 {quota_check['reason']}")
                
                # 配额不足，使用降级方案
                if enable_fallback and quota_check["use_fallback"]:
                    return quota_manager.get_fallback_data(api_name, **kwargs)
                else:
                    raise Exception(f"{api_name} API配额不足且未启用降级方案")
        
        return wrapper
    return decorator

def batch_quota_management(api_name: str, batch_size: int = 10):
    """
    批量API配额管理装饰器
    自动将大批量请求分割成小批次
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            quota_manager = get_quota_manager()
            
            # 获取需要处理的数据
            data_key = kwargs.get('data_key', 'keywords')  # 默认处理keywords参数
            data = kwargs.get(data_key, [])
            
            if not isinstance(data, list) or len(data) <= batch_size:
                # 数据量小，直接处理
                return func(*args, **kwargs)
            
            # 分批处理
            results = []
            total_batches = (len(data) + batch_size - 1) // batch_size
            
            print(f"📦 {api_name} 批量处理: {len(data)} 项数据，分为 {total_batches} 批")
            
            for i in range(0, len(data), batch_size):
                batch_data = data[i:i + batch_size]
                batch_kwargs = kwargs.copy()
                batch_kwargs[data_key] = batch_data
                
                print(f"  处理批次 {i//batch_size + 1}/{total_batches} ({len(batch_data)} 项)")
                
                # 检查配额
                quota_check = quota_manager.check_quota(api_name, len(batch_data))
                
                if quota_check["available"]:
                    try:
                        batch_result = func(*args, **batch_kwargs)
                        quota_manager.use_quota(api_name, len(batch_data))
                        
                        if isinstance(batch_result, pd.DataFrame):
                            results.append(batch_result)
                        elif isinstance(batch_result, list):
                            results.extend(batch_result)
                        
                    except Exception as e:
                        print(f"⚠️ 批次 {i//batch_size + 1} 处理失败: {e}")
                        
                        # 使用降级方案
                        fallback_result = quota_manager.get_fallback_data(api_name, **batch_kwargs)
                        if fallback_result is not None:
                            if isinstance(fallback_result, pd.DataFrame):
                                results.append(fallback_result)
                            elif isinstance(fallback_result, list):
                                results.extend(fallback_result)
                else:
                    print(f"🚫 批次 {i//batch_size + 1} 配额不足: {quota_check['reason']}")
                    
                    # 使用降级方案
                    if quota_check["use_fallback"]:
                        fallback_result = quota_manager.get_fallback_data(api_name, **batch_kwargs)
                        if fallback_result is not None:
                            if isinstance(fallback_result, pd.DataFrame):
                                results.append(fallback_result)
                            elif isinstance(fallback_result, list):
                                results.extend(fallback_result)
            
            # 合并结果
            if results:
                if isinstance(results[0], pd.DataFrame):
                    return pd.concat(results, ignore_index=True)
                else:
                    return results
            else:
                return pd.DataFrame() if 'DataFrame' in str(type(func(*args, **kwargs))) else []
        
        return wrapper
    return decorator

# 预定义的API装饰器
serpapi_quota = lambda func: with_quota_management("SERPAPI", 1, True)(func)
google_ads_quota = lambda func: with_quota_management("GOOGLE_ADS", 1, True)(func)
producthunt_quota = lambda func: with_quota_management("PRODUCTHUNT", 1, True)(func)
google_search_quota = lambda func: with_quota_management("GOOGLE_SEARCH", 1, True)(func)
ahrefs_quota = lambda func: with_quota_management("AHREFS", 1, True)(func)

# 批量处理装饰器
serpapi_batch = lambda func: batch_quota_management("SERPAPI", 10)(func)
google_ads_batch = lambda func: batch_quota_management("GOOGLE_ADS", 50)(func)
producthunt_batch = lambda func: batch_quota_management("PRODUCTHUNT", 20)(func)