#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
词根母词管理器
整合网络收集的51个高价值词根与关键词挖掘系统
支持默认配置和手动指定母词
"""

import os
import json
import yaml
from typing import Dict, List, Set, Optional, Any
from datetime import datetime


class RootWordManager:
    """
    词根母词管理器
    管理AI工具相关的核心词根，支持动态配置和手动指定
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化词根管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        
        # 加载51个核心词根（来自网络收集）
        self.core_roots = self._get_core_roots()
        
        # AI工具相关前缀
        self.ai_prefixes = self._get_ai_prefixes()
        
        # 工具类型分类
        self.tool_categories = self._get_tool_categories()
        
        # 用户手动指定的母词
        self.manual_roots = set()
        
        print(f"🎯 词根管理器初始化完成")
        print(f"📊 已加载 {len(self.core_roots)} 个核心词根")
        print(f"🤖 已配置 {len(self.ai_prefixes)} 个AI前缀")
        print(f"🏷️ 已分类 {len(self.tool_categories)} 个工具类型")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            'use_all_roots': True,
            'priority_roots': [],
            'excluded_roots': [],
            'ai_focus': True,
            'include_variations': True,
            'max_combinations': 1000
        }
        
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.endswith('.json'):
                        user_config = json.load(f)
                    else:
                        user_config = yaml.safe_load(f)
                    default_config.update(user_config)
            except Exception as e:
                print(f"⚠️ 配置文件加载失败: {e}")
        
        return default_config
    
    def _get_core_roots(self) -> List[str]:
        """
        获取核心词根
        整合原有词根 + 51词根文件中的高价值词根
        """
        return [
            # 生成类 (Generator)
            'generator', 'maker', 'creator', 'builder', 'producer',
            
            # 转换类 (Converter) 
            'converter', 'transformer', 'translator', 'transcriber',
            
            # 编辑类 (Editor)
            'editor', 'modifier', 'enhancer', 'optimizer', 'improver',
            
            # 分析类 (Analyzer)
            'analyzer', 'detector', 'scanner', 'checker', 'validator',
            'tester', 'inspector', 'examiner', 'evaluator', 'verifier',
            'comparator',
            
            # 处理类 (Processor)
            'processor', 'compressor', 'resizer', 'cropper', 'splitter',
            'merger', 'combiner', 'joiner', 'interpreter',
            
            # 提取类 (Extractor)
            'extractor', 'parser', 'scraper', 'harvester', 'collector',
            'cataloger',
            
            # 管理类 (Manager)
            'manager', 'organizer', 'sorter', 'scheduler', 'planner',
            'tracker', 'monitor', 'dashboard',
            
            # 计算类 (Calculator)
            'calculator', 'counter', 'estimator', 'predictor', 'simulator',
            
            # 搜索类 (Finder)
            'finder', 'searcher', 'explorer', 'browser', 'locator',
            'navigator',
            
            # 传输类 (Transfer)
            'downloader', 'uploader', 'exporter', 'importer', 'syncer',
            
            # 清理类 (Cleaner)
            'cleaner', 'remover', 'eraser', 'deleter', 'purifier',
            
            # 展示类 (Viewer) - 新增类别
            'viewer', 'recorder', 'template', 'sample',
            
            # 交互类 (Interactive) - 新增类别  
            'assistant', 'notifier', 'responder'
        ]
    
    def _get_ai_prefixes(self) -> List[str]:
        """获取AI相关前缀"""
        return [
            'ai', 'artificial intelligence', 'machine learning', 'ml',
            'deep learning', 'neural', 'smart', 'intelligent', 'automated',
            'auto', 'gpt', 'chatgpt', 'openai', 'claude'
        ]
    
    def _get_tool_categories(self) -> Dict[str, List[str]]:
        """
        获取工具类型分类
        按照应用场景和功能分类 (已整合51词根)
        """
        return {
            'content_creation': [
                'generator', 'maker', 'creator', 'builder', 'writer',
                'designer', 'composer', 'producer', 'template', 'sample'
            ],
            'data_processing': [
                'converter', 'transformer', 'processor', 'analyzer',
                'parser', 'extractor', 'compressor', 'interpreter', 'cataloger'
            ],
            'media_editing': [
                'editor', 'enhancer', 'optimizer', 'resizer', 'cropper',
                'filter', 'modifier', 'improver', 'recorder'
            ],
            'quality_assurance': [
                'checker', 'validator', 'tester', 'detector', 'scanner',
                'inspector', 'examiner', 'verifier', 'evaluator', 'comparator'
            ],
            'productivity': [
                'manager', 'organizer', 'scheduler', 'planner', 'tracker',
                'monitor', 'calculator', 'counter', 'dashboard', 'assistant'
            ],
            'search_discovery': [
                'finder', 'searcher', 'explorer', 'browser', 'locator',
                'discoverer', 'hunter', 'navigator'
            ],
            'file_management': [
                'downloader', 'uploader', 'exporter', 'importer', 'syncer',
                'backup', 'archiver', 'migrator', 'viewer'
            ],
            'maintenance': [
                'cleaner', 'remover', 'eraser', 'deleter', 'purifier',
                'optimizer', 'fixer', 'repairer'
            ],
            'communication': [  # 新增类别
                'notifier', 'responder', 'assistant'
            ]
        }
    
    def set_manual_roots(self, roots: List[str]) -> None:
        """
        手动指定母词
        
        Args:
            roots: 手动指定的词根列表
        """
        self.manual_roots = set(roots)
        print(f"✅ 已手动指定 {len(roots)} 个母词: {', '.join(roots[:5])}{'...' if len(roots) > 5 else ''}")
    
    def get_active_roots(self) -> List[str]:
        """
        获取当前激活的词根
        优先使用手动指定的母词，否则使用配置的默认母词
        
        Returns:
            当前激活的词根列表
        """
        # 如果有手动指定的母词，优先使用
        if self.manual_roots:
            return list(self.manual_roots)
        
        # 否则使用配置的默认母词
        active_roots = self.core_roots.copy()
        
        # 应用配置过滤
        if self.config.get('priority_roots'):
            # 如果有优先词根，只使用优先词根
            priority_set = set(self.config['priority_roots'])
            active_roots = [root for root in active_roots if root in priority_set]
        
        if self.config.get('excluded_roots'):
            # 排除指定的词根
            excluded_set = set(self.config['excluded_roots'])
            active_roots = [root for root in active_roots if root not in excluded_set]
        
        return active_roots
    
    def generate_keyword_combinations(self, 
                                    seed_words: List[str], 
                                    include_ai: bool = True,
                                    max_combinations: int = None) -> List[str]:
        """
        生成关键词组合
        
        Args:
            seed_words: 种子词列表
            include_ai: 是否包含AI前缀
            max_combinations: 最大组合数量
            
        Returns:
            生成的关键词组合列表
        """
        if max_combinations is None:
            max_combinations = self.config.get('max_combinations', 1000)
        
        combinations = []
        active_roots = self.get_active_roots()
        
        print(f"🔄 开始生成关键词组合...")
        print(f"📊 种子词: {len(seed_words)} 个")
        print(f"🎯 激活词根: {len(active_roots)} 个")
        
        # 基础组合: seed + root
        for seed in seed_words:
            for root in active_roots:
                combinations.extend([
                    f"{seed} {root}",
                    f"{root} {seed}",
                    f"{seed}-{root}",
                    f"{root}-{seed}"
                ])
        
        # AI前缀组合
        if include_ai and self.config.get('ai_focus', True):
            for seed in seed_words:
                for root in active_roots[:20]:  # 限制词根数量
                    for ai_prefix in self.ai_prefixes[:5]:  # 限制AI前缀数量
                        combinations.extend([
                            f"{ai_prefix} {seed} {root}",
                            f"{ai_prefix} {root} {seed}",
                            f"{ai_prefix}-{seed}-{root}"
                        ])
        
        # 去重并限制数量
        unique_combinations = list(set(combinations))[:max_combinations]
        
        print(f"✅ 生成完成: {len(unique_combinations)} 个独特组合")
        return unique_combinations
    
    def get_category_roots(self, category: str) -> List[str]:
        """
        获取指定类别的词根
        
        Args:
            category: 工具类别名称
            
        Returns:
            该类别的词根列表
        """
        return self.tool_categories.get(category, [])
    
    def analyze_root_coverage(self, keywords: List[str]) -> Dict[str, Any]:
        """
        分析关键词的词根覆盖情况
        
        Args:
            keywords: 关键词列表
            
        Returns:
            词根覆盖分析结果
        """
        active_roots = self.get_active_roots()
        root_usage = {root: 0 for root in active_roots}
        covered_roots = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for root in active_roots:
                if root in keyword_lower:
                    root_usage[root] += 1
                    covered_roots.add(root)
        
        coverage_rate = len(covered_roots) / len(active_roots) if active_roots else 0
        
        return {
            'total_roots': len(active_roots),
            'covered_roots': len(covered_roots),
            'coverage_rate': round(coverage_rate * 100, 1),
            'root_usage': dict(sorted(root_usage.items(), key=lambda x: x[1], reverse=True)),
            'top_used_roots': [root for root, count in sorted(root_usage.items(), key=lambda x: x[1], reverse=True)[:10]],
            'unused_roots': [root for root in active_roots if root not in covered_roots]
        }
    
    def suggest_missing_opportunities(self, current_keywords: List[str]) -> List[str]:
        """
        基于词根覆盖分析，建议缺失的机会关键词
        
        Args:
            current_keywords: 当前关键词列表
            
        Returns:
            建议的新关键词列表
        """
        coverage_analysis = self.analyze_root_coverage(current_keywords)
        unused_roots = coverage_analysis['unused_roots']
        
        # 从当前关键词中提取种子词
        seed_words = self._extract_seed_words(current_keywords)
        
        # 为未使用的词根生成新关键词
        suggestions = []
        for root in unused_roots[:10]:  # 限制数量
            for seed in seed_words[:5]:  # 限制种子词数量
                suggestions.extend([
                    f"{seed} {root}",
                    f"ai {seed} {root}",
                    f"free {seed} {root}",
                    f"online {seed} {root}"
                ])
        
        return list(set(suggestions))[:20]  # 返回前20个建议
    
    def _extract_seed_words(self, keywords: List[str]) -> List[str]:
        """从关键词中提取种子词"""
        seed_words = set()
        active_roots = set(self.get_active_roots())
        ai_prefixes = set(self.ai_prefixes)
        
        for keyword in keywords:
            words = keyword.lower().replace('-', ' ').split()
            for word in words:
                # 排除词根和AI前缀，剩下的作为种子词
                if word not in active_roots and word not in ai_prefixes:
                    if len(word) > 2:  # 过滤太短的词
                        seed_words.add(word)
        
        return list(seed_words)
    
    def export_config(self, output_path: str) -> None:
        """
        导出当前配置
        
        Args:
            output_path: 输出文件路径
        """
        export_data = {
            'config': self.config,
            'core_roots': self.core_roots,
            'ai_prefixes': self.ai_prefixes,
            'tool_categories': self.tool_categories,
            'manual_roots': list(self.manual_roots),
            'export_time': datetime.now().isoformat()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            if output_path.endswith('.json'):
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            else:
                yaml.dump(export_data, f, allow_unicode=True, default_flow_style=False)
        
        print(f"✅ 配置已导出到: {output_path}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        active_roots = self.get_active_roots()
        
        return {
            'total_core_roots': len(self.core_roots),
            'active_roots': len(active_roots),
            'manual_roots': len(self.manual_roots),
            'ai_prefixes': len(self.ai_prefixes),
            'tool_categories': len(self.tool_categories),
            'using_manual_roots': len(self.manual_roots) > 0,
            'config_loaded': self.config_path is not None
        }