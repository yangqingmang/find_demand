#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
意图配置管理器 - 使建站脚本适应意图分析规则变化
"""

from typing import Dict, List, Any, Optional
import json
import os

class IntentConfigManager:
    """意图配置管理器"""
    
    def __init__(self, config_path: str = None):
        """
        初始化意图配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载意图配置"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载意图配置失败: {e}")
        
        # 返回默认配置
        return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认意图配置"""
        return {
            "intent_types": {
                "I": {
                    "name": "信息获取",
                    "description": "用户寻求信息和知识",
                    "page_template": "article_i",
                    "content_sections": [
                        {"name": "介绍", "type": "introduction", "word_count": 300},
                        {"name": "详细信息", "type": "detailed_info", "word_count": 1000},
                        {"name": "常见问题", "type": "faq", "word_count": 500},
                        {"name": "总结", "type": "summary", "word_count": 200}
                    ],
                    "seo_priority": "medium",
                    "word_count": 2000
                },
                "C": {
                    "name": "商业评估",
                    "description": "用户进行商业决策评估",
                    "page_template": "article_c",
                    "content_sections": [
                        {"name": "产品介绍", "type": "introduction", "word_count": 300},
                        {"name": "比较分析", "type": "comparison", "word_count": 800},
                        {"name": "优缺点", "type": "pros_cons", "word_count": 600},
                        {"name": "推荐建议", "type": "recommendations", "word_count": 300}
                    ],
                    "seo_priority": "high",
                    "word_count": 2000
                },
                "E": {
                    "name": "交易购买",
                    "description": "用户准备进行交易购买",
                    "page_template": "article_e",
                    "content_sections": [
                        {"name": "产品介绍", "type": "introduction", "word_count": 300},
                        {"name": "产品特点", "type": "features", "word_count": 600},
                        {"name": "价格信息", "type": "pricing", "word_count": 400},
                        {"name": "购买指南", "type": "buying_guide", "word_count": 700}
                    ],
                    "seo_priority": "very_high",
                    "word_count": 2000
                }
            },
            "default_intent": {
                "name": "通用内容",
                "description": "通用内容类型",
                "page_template": "article_default",
                "content_sections": [
                    {"name": "介绍", "type": "introduction", "word_count": 300},
                    {"name": "主要内容", "type": "main_content", "word_count": 1200},
                    {"name": "总结", "type": "summary", "word_count": 500}
                ],
                "seo_priority": "medium",
                "word_count": 2000
            },
            "homepage_sections": [
                {"type": "hero", "title": "英雄区"},
                {"type": "intent_nav", "title": "意图导航"},
                {"type": "intent_sections", "title": "意图专区"}
            ]
        }
    
    def get_intent_config(self, intent: str) -> Dict[str, Any]:
        """
        获取指定意图的配置
        
        Args:
            intent: 意图代码
            
        Returns:
            意图配置字典
        """
        intent_types = self.config.get("intent_types", {})
        return intent_types.get(intent, self.config.get("default_intent", {}))
    
    def get_all_intent_types(self) -> List[str]:
        """获取所有支持的意图类型"""
        return list(self.config.get("intent_types", {}).keys())
    
    def get_intent_name(self, intent: str) -> str:
        """获取意图名称"""
        config = self.get_intent_config(intent)
        return config.get("name", intent)
    
    def get_intent_description(self, intent: str) -> str:
        """获取意图描述"""
        config = self.get_intent_config(intent)
        return config.get("description", "")
    
    def get_page_template(self, intent: str) -> str:
        """获取页面模板类型"""
        config = self.get_intent_config(intent)
        return config.get("page_template", "article_default")
    
    def get_content_sections(self, intent: str) -> List[Dict[str, Any]]:
        """获取内容区块配置"""
        config = self.get_intent_config(intent)
        return config.get("content_sections", [])
    
    def get_seo_priority(self, intent: str) -> str:
        """获取SEO优先级"""
        config = self.get_intent_config(intent)
        return config.get("seo_priority", "medium")
    
    def get_word_count(self, intent: str) -> int:
        """获取建议字数"""
        config = self.get_intent_config(intent)
        return config.get("word_count", 1500)
    
    def add_intent_type(self, intent: str, config: Dict[str, Any]) -> None:
        """
        添加新的意图类型配置
        
        Args:
            intent: 意图代码
            config: 意图配置
        """
        if "intent_types" not in self.config:
            self.config["intent_types"] = {}
        
        self.config["intent_types"][intent] = config
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        if not self.config_path:
            return False
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存意图配置失败: {e}")
            return False