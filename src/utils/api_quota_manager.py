#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API配额管理器
管理各种API的月度限制和降级逻辑
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class APIQuota:
    """API配额配置"""
    name: str
    monthly_limit: int
    current_usage: int = 0
    reset_date: str = ""
    enabled: bool = True
    fallback_enabled: bool = True
    
    def __post_init__(self):
        if not self.reset_date:
            # 设置为下个月1号
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            self.reset_date = next_month.replace(day=1).strftime("%Y-%m-%d")

class APIQuotaManager:
    """API配额管理器"""
    
    def __init__(self, quota_file: str = "config/api_quotas.json"):
        self.quota_file = quota_file
        self.quotas: Dict[str, APIQuota] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        
        # 默认API配额配置
        self.default_quotas = {
            "SERPAPI": APIQuota("SERPAPI", 100),  # SERP API 月限制100次
            "GOOGLE_ADS": APIQuota("GOOGLE_ADS", 15000),  # Google Ads API 月限制15000次
            "PRODUCTHUNT": APIQuota("PRODUCTHUNT", 500),  # ProductHunt API 月限制500次
            "GOOGLE_SEARCH": APIQuota("GOOGLE_SEARCH", 100),  # Google Custom Search 月限制100次
            "AHREFS": APIQuota("AHREFS", 1000),  # Ahrefs API 月限制1000次
        }
        
        self.load_quotas()
        self._register_fallback_handlers()
    
    def load_quotas(self):
        """加载配额数据"""
        try:
            if os.path.exists(self.quota_file):
                with open(self.quota_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for api_name, quota_data in data.items():
                    self.quotas[api_name] = APIQuota(**quota_data)
                    
                print(f"✓ 已加载API配额配置: {len(self.quotas)} 个API")
            else:
                # 使用默认配置
                self.quotas = self.default_quotas.copy()
                self.save_quotas()
                print("✓ 已创建默认API配额配置")
                
        except Exception as e:
            print(f"⚠️ 加载API配额配置失败: {e}")
            self.quotas = self.default_quotas.copy()
    
    def save_quotas(self):
        """保存配额数据"""
        try:
            os.makedirs(os.path.dirname(self.quota_file), exist_ok=True)
            
            data = {}
            for api_name, quota in self.quotas.items():
                data[api_name] = asdict(quota)
            
            with open(self.quota_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 保存API配额配置失败: {e}")
    
    def check_quota(self, api_name: str, required_calls: int = 1) -> Dict[str, Any]:
        """
        检查API配额
        
        Args:
            api_name: API名称
            required_calls: 需要的调用次数
            
        Returns:
            dict: 包含可用性和建议的字典
        """
        if api_name not in self.quotas:
            return {
                "available": True,
                "reason": "API未配置配额限制",
                "remaining": float('inf'),
                "use_fallback": False
            }
        
        quota = self.quotas[api_name]
        
        # 检查是否需要重置配额
        self._check_reset_quota(api_name)
        
        # 检查API是否启用
        if not quota.enabled:
            return {
                "available": False,
                "reason": f"{api_name} API已禁用",
                "remaining": 0,
                "use_fallback": quota.fallback_enabled
            }
        
        # 检查配额是否足够
        remaining = quota.monthly_limit - quota.current_usage
        if remaining < required_calls:
            return {
                "available": False,
                "reason": f"{api_name} API月配额不足 (剩余: {remaining}, 需要: {required_calls})",
                "remaining": remaining,
                "use_fallback": quota.fallback_enabled
            }
        
        return {
            "available": True,
            "reason": "配额充足",
            "remaining": remaining,
            "use_fallback": False
        }
    
    def use_quota(self, api_name: str, calls_used: int = 1) -> bool:
        """
        使用API配额
        
        Args:
            api_name: API名称
            calls_used: 使用的调用次数
            
        Returns:
            bool: 是否成功使用配额
        """
        if api_name not in self.quotas:
            return True  # 未配置限制的API直接允许
        
        quota_check = self.check_quota(api_name, calls_used)
        if not quota_check["available"]:
            return False
        
        # 更新使用量
        self.quotas[api_name].current_usage += calls_used
        self.save_quotas()
        
        print(f"📊 {api_name} API使用量: {self.quotas[api_name].current_usage}/{self.quotas[api_name].monthly_limit}")
        
        return True
    
    def _check_reset_quota(self, api_name: str):
        """检查是否需要重置配额"""
        quota = self.quotas[api_name]
        reset_date = datetime.strptime(quota.reset_date, "%Y-%m-%d")
        
        if datetime.now() >= reset_date:
            # 重置配额
            quota.current_usage = 0
            # 设置下个月的重置日期
            next_month = reset_date.replace(day=1) + timedelta(days=32)
            quota.reset_date = next_month.replace(day=1).strftime("%Y-%m-%d")
            
            print(f"🔄 {api_name} API配额已重置")
            self.save_quotas()
    
    def _register_fallback_handlers(self):
        """注册降级处理器"""
        self.fallback_handlers = {
            "SERPAPI": self._serpapi_fallback,
            "GOOGLE_ADS": self._google_ads_fallback,
            "PRODUCTHUNT": self._producthunt_fallback,
            "GOOGLE_SEARCH": self._google_search_fallback,
            "AHREFS": self._ahrefs_fallback,
        }
    
    def get_fallback_data(self, api_name: str, **kwargs) -> Any:
        """获取降级数据"""
        if api_name in self.fallback_handlers:
            print(f"🔄 使用 {api_name} 降级方案")
            return self.fallback_handlers[api_name](**kwargs)
        else:
            print(f"⚠️ {api_name} 没有配置降级方案")
            return None
    
    def _serpapi_fallback(self, **kwargs) -> pd.DataFrame:
        """SERP API降级方案：使用静态SERP特征数据"""
        raise RuntimeError("SERP API 配额耗尽且未配置降级数据源，无法提供静态数据")
    
    def _google_ads_fallback(self, **kwargs) -> pd.DataFrame:
        """Google Ads API降级方案：使用估算数据"""
        raise RuntimeError("Google Ads API 降级数据未配置，无法返回估算搜索量")
    
    def _producthunt_fallback(self, **kwargs) -> pd.DataFrame:
        """ProductHunt API降级方案：使用缓存或静态数据"""
        raise RuntimeError("ProductHunt API 降级数据未配置，无法提供静态产品列表")
    
    def _google_search_fallback(self, **kwargs) -> pd.DataFrame:
        """Google Custom Search API降级方案：使用预定义结果"""
        raise RuntimeError("Google Search API 降级数据未配置，无法提供预定义搜索结果")
    
    def _ahrefs_fallback(self, **kwargs) -> pd.DataFrame:
        """Ahrefs API降级方案：使用估算SEO数据"""
        raise RuntimeError("Ahrefs API 降级数据未配置，无法提供估算指标")
    
    def get_quota_status(self) -> Dict[str, Dict]:
        """获取所有API的配额状态"""
        status = {}
        
        for api_name, quota in self.quotas.items():
            self._check_reset_quota(api_name)
            
            remaining = quota.monthly_limit - quota.current_usage
            usage_percent = (quota.current_usage / quota.monthly_limit) * 100
            
            status[api_name] = {
                "enabled": quota.enabled,
                "monthly_limit": quota.monthly_limit,
                "current_usage": quota.current_usage,
                "remaining": remaining,
                "usage_percent": round(usage_percent, 1),
                "reset_date": quota.reset_date,
                "fallback_enabled": quota.fallback_enabled,
                "status": "🟢 正常" if remaining > quota.monthly_limit * 0.1 
                         else "🟡 即将耗尽" if remaining > 0 
                         else "🔴 已耗尽"
            }
        
        return status
    
    def print_quota_report(self):
        """打印配额报告"""
        print("\n" + "="*60)
        print("📊 API配额使用报告")
        print("="*60)
        
        status = self.get_quota_status()
        
        for api_name, info in status.items():
            print(f"\n🔌 {api_name} API:")
            print(f"   状态: {info['status']}")
            print(f"   使用量: {info['current_usage']}/{info['monthly_limit']} ({info['usage_percent']}%)")
            print(f"   剩余: {info['remaining']} 次")
            print(f"   重置日期: {info['reset_date']}")
            print(f"   降级方案: {'✅ 已启用' if info['fallback_enabled'] else '❌ 未启用'}")
        
        print("\n" + "="*60)

# 全局配额管理器实例
_quota_manager = None

def get_quota_manager() -> APIQuotaManager:
    """获取全局配额管理器实例"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = APIQuotaManager()
    return _quota_manager

def check_api_quota(api_name: str, required_calls: int = 1) -> Dict[str, Any]:
    """快捷方式：检查API配额"""
    return get_quota_manager().check_quota(api_name, required_calls)

def use_api_quota(api_name: str, calls_used: int = 1) -> bool:
    """快捷方式：使用API配额"""
    return get_quota_manager().use_quota(api_name, calls_used)

def get_fallback_data(api_name: str, **kwargs) -> Any:
    """快捷方式：获取降级数据"""
    return get_quota_manager().get_fallback_data(api_name, **kwargs)


if __name__ == "__main__":
    # 测试配额管理器
    manager = APIQuotaManager()
    
    # 打印配额报告
    manager.print_quota_report()
    
    # 测试配额检查
    print("\n🧪 测试API配额检查:")
    
    apis_to_test = ["SERPAPI", "GOOGLE_ADS", "PRODUCTHUNT"]
    
    for api in apis_to_test:
        result = manager.check_quota(api, 5)
        print(f"{api}: {result}")
        
        if result["available"]:
            manager.use_quota(api, 5)
        elif result["use_fallback"]:
            fallback_data = manager.get_fallback_data(api, keywords=["AI tool", "ChatGPT"])
            print(f"  降级数据: {len(fallback_data) if fallback_data is not None else 0} 条记录")
