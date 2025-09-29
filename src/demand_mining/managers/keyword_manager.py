#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词管理器 - 负责关键词分析功能
"""

import os
import sys
import json
import re
import copy
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from src.demand_mining.analyzers.intent_analyzer_v2 import IntentAnalyzerV2 as IntentAnalyzer
from src.demand_mining.analyzers.market_analyzer import MarketAnalyzer
from src.demand_mining.analyzers.keyword_analyzer import KeywordAnalyzer
from src.demand_mining.analyzers.comprehensive_analyzer import ComprehensiveAnalyzer
from src.demand_mining.analyzers.serp_analyzer import SerpAnalyzer

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from .base_manager import BaseManager


class KeywordManager(BaseManager):
    """关键词分析管理器"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        
        # 延迟导入分析器，避免循环导入
        self._intent_analyzer = None
        self._market_analyzer = None
        self._keyword_analyzer = None
        self._comprehensive_analyzer = None
        self._serp_analyzer = None
        
        print("🔍 关键词管理器初始化完成")
        default_weights = {
            'intent_confidence': 0.17,
            'search_volume': 0.18,
            'competition': 0.14,
            'ai_bonus': 0.07,
            'commercial_value': 0.16,
            'serp_purchase_intent': 0.05,
            'serp_ads_presence': 0.05,
            'long_tail': 0.1,
            'brand_penalty': 0.08
        }

        keyword_scoring_cfg = {}
        if hasattr(self, 'config') and self.config:
            attr = getattr(self.config, 'keyword_scoring', None)
            if isinstance(attr, dict):
                keyword_scoring_cfg = attr

        combined = default_weights.copy()
        weights_cfg = keyword_scoring_cfg.get('weights', {}) if isinstance(keyword_scoring_cfg, dict) else {}
        if isinstance(weights_cfg, dict):
            combined.update({k: float(v) for k, v in weights_cfg.items() if isinstance(v, (int, float))})

        env_weights = os.getenv('KEYWORD_SCORING_WEIGHTS')
        if env_weights:
            try:
                env_data = json.loads(env_weights)
                combined.update({k: float(v) for k, v in env_data.items()})
            except Exception:
                pass

        self.scoring_weights = combined
        self._normalize_scoring_weights()

        default_cost_penalty = 0.15
        if isinstance(keyword_scoring_cfg, dict):
            try:
                default_cost_penalty = float(keyword_scoring_cfg.get('cost_penalty', default_cost_penalty))
            except Exception:
                pass
        env_cost_penalty = os.getenv('KEYWORD_SCORING_COST_PENALTY')
        if env_cost_penalty:
            try:
                default_cost_penalty = float(env_cost_penalty)
            except Exception:
                pass
        self.cost_penalty = max(0.0, min(default_cost_penalty, 1.0))

        filters_cfg = self.config.get('keyword_filters', {}) if isinstance(self.config, dict) else {}

        def _extract_values(raw_value):
            if raw_value is None:
                return []
            if isinstance(raw_value, dict):
                for key in ('values', 'items', 'terms'):
                    if key in raw_value and isinstance(raw_value[key], (list, tuple, set)):
                        return [str(v).strip() for v in raw_value[key] if isinstance(v, str) and v.strip()]
                if 'value' in raw_value and isinstance(raw_value['value'], str):
                    return [raw_value['value'].strip()]
                return []
            if isinstance(raw_value, (list, tuple, set)):
                return [str(v).strip() for v in raw_value if isinstance(v, str) and v.strip()]
            if isinstance(raw_value, str) and raw_value.strip():
                return [raw_value.strip()]
            return []

        def _resolve_terms(default_values, list_key, mode_key, default_mode='extend'):
            base_list = [str(v).strip().lower() for v in default_values if isinstance(v, str) and v.strip()]
            raw_entries = filters_cfg.get(list_key)
            mode_candidate = filters_cfg.get(mode_key, default_mode)
            if isinstance(raw_entries, dict) and 'mode' in raw_entries:
                mode_candidate = raw_entries['mode']
            mode = str(mode_candidate).lower() if isinstance(mode_candidate, str) else default_mode
            if mode not in ('extend', 'replace', 'disable'):
                mode = default_mode
            if mode == 'replace':
                base_list = []
            elif mode == 'disable':
                return []

            for value in _extract_values(raw_entries):
                lowered = value.lower()
                if lowered not in base_list:
                    base_list.append(lowered)
            return base_list

        default_brand_phrases = [
            'chatgpt', 'openai', 'gpt', 'gpt-4', 'gpt4', 'gpt5', 'claude',
            'midjourney', 'deepseek', 'hix bypass', 'undetectable ai', 'turnitin',
            'copilot'
        ]
        default_brand_modifiers = [
            'login', 'logins', 'signup', 'sign', 'account', 'app', 'apps', 'download',
            'downloads', 'premium', 'price', 'prices', 'pricing', 'cost', 'costs',
            'free', 'trial', 'promo', 'discount', 'code', 'codes', 'coupon', 'review',
            'reviews', 'vs', 'versus', 'alternative', 'alternatives', 'compare',
            'comparison', 'checker', 'detector', 'essay', 'humanizer', 'turnitin',
            'unlimited', 'pro', 'plus', 'plan', 'plans', 'tier', 'tiers', 'lifetime',
            'prompt', 'prompts'
        ]
        default_long_tail_modifiers = [
            'workflow', 'strategy', 'ideas', 'guide', 'guides', 'step', 'steps',
            'framework', 'frameworks', 'template', 'templates', 'checklist',
            'automation', 'process', 'plan', 'plans', 'blueprint', 'examples',
            'case', 'cases', 'study', 'studies', 'tutorial', 'tutorials', 'use',
            'uses', 'stack', 'stacks', 'integration', 'integrations', 'workflows',
            'niche', 'niches', 'system', 'systems'
        ]
        default_generic_heads = [
            'service', 'services', 'software', 'platform', 'platforms', 'solution',
            'solutions', 'application', 'applications', 'tool', 'tools',
            'machine learning', 'artificial intelligence', 'automation', 'ai',
            'technology', 'technologies', 'gpt'
        ]
        default_question_prefixes = [
            'how to', 'how do', 'how can', 'what is', 'what are', 'why', 'should i',
            'can i', 'is there', 'best way', 'ways to'
        ]

        brand_phrases_list = _resolve_terms(default_brand_phrases, 'brand_phrases', 'brand_phrases_mode')
        brand_modifier_list = _resolve_terms(default_brand_modifiers, 'brand_modifiers', 'brand_modifier_mode')
        long_tail_list = _resolve_terms(default_long_tail_modifiers, 'long_tail_tokens', 'long_tail_mode')
        generic_head_list = _resolve_terms(default_generic_heads, 'generic_head_terms', 'generic_head_mode')
        question_prefix_list = _resolve_terms(default_question_prefixes, 'question_prefixes', 'question_prefix_mode')

        self.brand_phrases = set(brand_phrases_list)
        self.brand_token_set = {token for phrase in self.brand_phrases for token in phrase.split()}
        self.brand_token_set.update({'chatgpt', 'openai', 'gpt', 'claude', 'midjourney', 'deepseek', 'hix', 'bypass', 'turnitin', 'copilot'})
        self.brand_modifier_tokens = set(brand_modifier_list)
        self.long_tail_modifiers = set(long_tail_list)
        self.generic_head_terms = set(generic_head_list)
        self.question_prefixes = tuple(question_prefix_list)

        keyword_analysis_cfg = self.config.get('keyword_analysis', {})
        if not isinstance(keyword_analysis_cfg, dict):
            keyword_analysis_cfg = {}
        self.keyword_analysis_config = keyword_analysis_cfg

        def _resolve_positive_int(value, fallback):
            try:
                candidate = int(value)
            except (TypeError, ValueError):
                return fallback
            return candidate if candidate > 0 else fallback

        base_batch = _resolve_positive_int(keyword_analysis_cfg.get('batch_size', 25), 25)
        self.intent_batch_size = _resolve_positive_int(keyword_analysis_cfg.get('intent_batch_size', base_batch), base_batch)
        self.market_batch_size = _resolve_positive_int(keyword_analysis_cfg.get('market_batch_size', base_batch), base_batch)

        self._cache_enabled = bool(keyword_analysis_cfg.get('enable_cache', True))
        ttl_hours = keyword_analysis_cfg.get('cache_ttl_hours', 12)
        try:
            ttl_hours_value = float(ttl_hours)
        except (TypeError, ValueError):
            ttl_hours_value = 12.0

        if ttl_hours_value <= 0:
            self.cache_ttl = None
            self._cache_enabled = False
        else:
            self.cache_ttl = timedelta(hours=ttl_hours_value)

        cache_dir_cfg = keyword_analysis_cfg.get('cache_dir') or os.path.join(self.output_dir, 'keyword_cache')
        self.cache_dir = Path(cache_dir_cfg)
        self.intent_cache_path = self.cache_dir / 'intent_cache.json'
        self.market_cache_path = self.cache_dir / 'market_cache.json'
        self.intent_cache: Dict[str, Dict[str, Any]] = {}
        self.market_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_dirty: Dict[str, bool] = {'intent': False, 'market': False}

        if self._cache_enabled:
            self._load_caches()

    
    @property
    def intent_analyzer(self):
        """延迟加载意图分析器"""
        if self._intent_analyzer is None:
            self._intent_analyzer = IntentAnalyzer()
        return self._intent_analyzer
    
    @property
    def market_analyzer(self):
        """延迟加载市场分析器"""
        if self._market_analyzer is None:
            self._market_analyzer = MarketAnalyzer()
        return self._market_analyzer
    
    @property
    def keyword_analyzer(self):
        """延迟加载关键词分析器"""
        if self._keyword_analyzer is None:
            self._keyword_analyzer = KeywordAnalyzer()
        return self._keyword_analyzer
    
    @property
    def comprehensive_analyzer(self):
        """延迟加载综合分析器"""
        if self._comprehensive_analyzer is None:
            self._comprehensive_analyzer = ComprehensiveAnalyzer()
        return self._comprehensive_analyzer

    @property
    def serp_analyzer(self):
        """延迟加载SERP分析器"""
        if getattr(self, '_serp_analyzer', None) is False:
            return None

        if self._serp_analyzer is None:
            demand_cfg = self.config.get('demand_mining', {})
            use_serp = demand_cfg.get('use_serp_signals', self.config.get('intent_analysis', {}).get('enable_serp_analysis', False))
            if not use_serp:
                self._serp_analyzer = False
                return None
            try:
                analyzer = SerpAnalyzer(use_proxy=self.config.get('serp', {}).get('use_proxy', True))
                if not getattr(analyzer, 'credentials_available', True):
                    warning = getattr(analyzer, 'credential_warning', None) or '未检测到SERP相关API凭证，跳过SERP信号提取'
                    print(f"⚠️ {warning}")
                    self._serp_analyzer = False
                    return None
                self._serp_analyzer = analyzer
            except Exception as exc:
                print(f"⚠️ SERP分析器初始化失败: {exc}")
                self._serp_analyzer = False
        return self._serp_analyzer or None

    
    def analyze(self, input_source, analysis_type: str = 'file', 
                output_dir: str = None, use_comprehensive: bool = False) -> Dict[str, Any]:
        """
        分析关键词
        
        Args:
            input_source: 输入源（文件路径或关键词列表）
            analysis_type: 分析类型 ('file' 或 'keywords')
            output_dir: 输出目录
            use_comprehensive: 是否使用综合分析器
            
        Returns:
            分析结果
        """
        print(f"🚀 开始关键词分析 - 类型: {analysis_type}, 综合分析: {use_comprehensive}")
        
        if use_comprehensive:
            return self._comprehensive_analyze(input_source, analysis_type, output_dir)
        
        if analysis_type == 'file':
            return self._analyze_from_file(input_source, output_dir)
        elif analysis_type == 'keywords':
            if isinstance(input_source, (list, tuple, set)):
                keywords = [str(kw) for kw in input_source if kw]
            elif hasattr(input_source, 'tolist'):
                keywords = [str(kw) for kw in input_source.tolist() if kw]
            else:
                keywords = [str(input_source)] if input_source else []
            return self._analyze_from_keywords(keywords, output_dir)
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")
    
    def _analyze_from_file(self, file_path: str, output_dir: str = None) -> Dict[str, Any]:
        """从文件分析关键词"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"输入文件不存在: {file_path}")
        
        # 读取数据
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
        else:
            raise ValueError("不支持的文件格式，请使用CSV或JSON文件")
        
        print(f"✅ 成功读取 {len(df)} 条关键词数据")
        
        # 提取关键词列表
        keywords = []
        for col in ['query', 'keyword', 'term']:
            if col in df.columns:
                keywords = df[col].dropna().tolist()
                break
        
        if not keywords:
            raise ValueError("未找到有效的关键词列")
        
        return self._perform_analysis(keywords, output_dir)
    
    def _analyze_from_keywords(self, keywords: List[str], output_dir: str = None) -> Dict[str, Any]:
        """从关键词列表分析"""
        if not keywords:
            raise ValueError("关键词列表不能为空")
        
        print(f"✅ 接收到 {len(keywords)} 个关键词")
        return self._perform_analysis(keywords, output_dir)
    
    def _perform_analysis(self, keywords: List[str], output_dir: str = None) -> Dict[str, Any]:
        """执行关键词分析"""
        normalized_keywords = self._prepare_keywords(keywords)
        results = {
            'total_keywords': len(normalized_keywords),
            'analysis_time': datetime.now().isoformat(),
            'keywords': [],
            'intent_summary': {},
            'market_insights': {},
            'recommendations': [],
            'processing_summary': {}
        }

        if not normalized_keywords:
            results['intent_summary'] = self._generate_intent_summary([])
            results['market_insights'] = self._generate_market_insights([])
            results['recommendations'] = []
            results['processing_summary'] = {
                'total_keywords': 0,
                'unique_keywords': 0,
                'intent_cache_hits': 0,
                'intent_batches': 0,
                'intent_computed': 0,
                'market_cache_hits': 0,
                'market_batches': 0,
                'market_computed': 0
            }
            if output_dir:
                output_path = self._save_analysis_results(results, output_dir)
                results['output_path'] = output_path
            return results

        unique_keywords = list(dict.fromkeys(normalized_keywords))
        intent_map, intent_stats = self._collect_intent_results(unique_keywords)
        market_map, market_stats = self._collect_market_results(unique_keywords)

        print(f"🧮 关键词批处理: 总计 {len(normalized_keywords)} 个，唯一 {len(unique_keywords)} 个")
        print(
            f"🧠 意图分析 → 缓存命中 {intent_stats['cache_hits']}，新计算 {intent_stats['computed']}，批次数 {intent_stats['batches']}"
        )
        print(
            f"📊 市场分析 → 缓存命中 {market_stats['cache_hits']}，新计算 {market_stats['computed']}，批次数 {market_stats['batches']}"
        )

        for keyword in normalized_keywords:
            intent_result = copy.deepcopy(intent_map.get(keyword, self._get_default_intent_result()))
            market_result = copy.deepcopy(market_map.get(keyword, self._get_default_market_result(keyword)))
            serp_signals = market_result.get('serp_signals')

            keyword_result = {
                'keyword': keyword,
                'intent': intent_result,
                'market': market_result,
                'opportunity_score': self._calculate_opportunity_score(
                    intent_result, market_result, serp_signals, keyword
                ),
                'execution_cost': market_result.get('execution_cost', 0.0)
            }

            if serp_signals:
                keyword_result['serp_signals'] = serp_signals

            results['keywords'].append(keyword_result)

        results['intent_summary'] = self._generate_intent_summary(results['keywords'])
        results['market_insights'] = self._generate_market_insights(results['keywords'])
        results['recommendations'] = self._generate_recommendations(results['keywords'])
        results['processing_summary'] = {
            'total_keywords': len(normalized_keywords),
            'unique_keywords': len(unique_keywords),
            'intent_cache_hits': intent_stats['cache_hits'],
            'intent_batches': intent_stats['batches'],
            'intent_computed': intent_stats['computed'],
            'market_cache_hits': market_stats['cache_hits'],
            'market_batches': market_stats['batches'],
            'market_computed': market_stats['computed']
        }

        if output_dir:
            output_path = self._save_analysis_results(results, output_dir)
            results['output_path'] = output_path

        if self._cache_enabled:
            self._flush_caches()

        return results

    @staticmethod
    def _prepare_keywords(keywords: List[str]) -> List[str]:
        """清理输入关键词列表"""
        prepared: List[str] = []
        if not keywords:
            return prepared

        for keyword in keywords:
            if keyword is None:
                continue
            text = str(keyword).strip()
            if text:
                prepared.append(text)
        return prepared

    def _collect_intent_results(self, keywords: List[str]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int]]:
        """批量收集意图分析结果，带缓存"""
        results: Dict[str, Dict[str, Any]] = {}
        stats = {'cache_hits': 0, 'computed': 0, 'batches': 0}

        if not keywords:
            return results, stats

        pending: List[str] = []
        for keyword in keywords:
            cached = self._get_cached_intent_result(keyword)
            if cached is not None:
                results[keyword] = cached
                stats['cache_hits'] += 1
            else:
                pending.append(keyword)

        if not pending:
            return results, stats

        analyzer = self.intent_analyzer
        if analyzer is None:
            for keyword in pending:
                results[keyword] = self._get_default_intent_result()
            return results, stats

        for batch in self._chunked(pending, self.intent_batch_size):
            if not batch:
                continue
            stats['batches'] += 1
            try:
                df = pd.DataFrame({'query': batch})
                payload = analyzer.analyze_keywords(df)
            except Exception as exc:
                print(f"⚠️ 意图分析批处理失败: {exc}")
                payload = {}

            batch_results = self._extract_intent_results(batch, payload)
            stats['computed'] += len(batch)
            for keyword, intent_result in batch_results.items():
                results[keyword] = intent_result
                self._set_cached_intent_result(keyword, intent_result)

        return results, stats

    def _extract_intent_results(self, batch: List[str], analyzer_payload: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """从意图分析器返回值中提取结构化结果"""
        normalized: Dict[str, Dict[str, Any]] = {}
        payload = analyzer_payload or {}
        raw_results = payload.get('results') if isinstance(payload, dict) else None
        raw_results = raw_results or []

        indexed: Dict[str, Dict[str, Any]] = {}
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            query = item.get('query')
            if not query:
                continue
            formatted = self._format_intent_result(item)
            indexed[str(query)] = formatted

        for keyword in batch:
            normalized[keyword] = copy.deepcopy(indexed.get(keyword, self._get_default_intent_result()))

        return normalized

    def _format_intent_result(self, intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化单个意图分析结果"""
        if not isinstance(intent_data, dict):
            return self._get_default_intent_result()

        website_recs = intent_data.get('website_recommendations')
        if not isinstance(website_recs, dict):
            website_recs = {}

        return {
            'primary_intent': intent_data.get('intent_primary', 'Unknown') or 'Unknown',
            'confidence': intent_data.get('probability', 0.0) or 0.0,
            'secondary_intent': intent_data.get('intent_secondary') or None,
            'intent_description': intent_data.get('intent_primary', 'Unknown') or 'Unknown',
            'website_recommendations': {
                'website_type': website_recs.get('website_type', intent_data.get('website_type', 'Unknown')),
                'ai_tool_category': website_recs.get('ai_tool_category', intent_data.get('ai_tool_category', 'General')),
                'domain_suggestions': website_recs.get('domain_suggestions', intent_data.get('domain_suggestions', [])),
                'monetization_strategy': website_recs.get('monetization_strategy', intent_data.get('monetization_strategy', [])),
                'technical_requirements': website_recs.get('technical_requirements', intent_data.get('technical_requirements', [])),
                'competition_analysis': website_recs.get('competition_analysis', intent_data.get('competition_analysis', {})),
                'development_priority': website_recs.get('development_priority', intent_data.get('development_priority', {})),
                'content_strategy': website_recs.get('content_strategy', intent_data.get('content_strategy', []))
            }
        }

    def _collect_market_results(self, keywords: List[str]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, int]]:
        """批量收集市场分析结果，带缓存"""
        results: Dict[str, Dict[str, Any]] = {}
        stats = {'cache_hits': 0, 'computed': 0, 'batches': 0}

        if not keywords:
            return results, stats

        pending: List[str] = []
        for keyword in keywords:
            cached = self._get_cached_market_result(keyword)
            if cached is not None:
                results[keyword] = cached
                stats['cache_hits'] += 1
            else:
                pending.append(keyword)

        if not pending:
            return results, stats

        analyzer = self.market_analyzer
        if analyzer is None:
            for keyword in pending:
                results[keyword] = self._get_default_market_result(keyword)
            return results, stats

        for batch in self._chunked(pending, self.market_batch_size):
            if not batch:
                continue
            stats['batches'] += 1
            try:
                base_payload = analyzer.analyze_market_data(batch)
            except Exception as exc:
                print(f"⚠️ 市场分析批处理失败: {exc}")
                base_payload = {}

            stats['computed'] += len(batch)
            for keyword in batch:
                raw_market = base_payload.get(keyword, {}) if isinstance(base_payload, dict) else {}
                try:
                    enriched = self._enrich_market_result(keyword, raw_market)
                except Exception as exc:
                    print(f"⚠️ 市场分析处理失败 ({keyword}): {exc}")
                    enriched = self._get_default_market_result(keyword)
                results[keyword] = enriched
                self._set_cached_market_result(keyword, enriched)

        return results, stats

    def _enrich_market_result(self, keyword: str, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """补全市场分析信息（含 SERP 信号）"""
        if not isinstance(market_data, dict):
            market_data = {}

        base_data = {
            'search_volume': market_data.get('search_volume', 1000),
            'competition': market_data.get('competition', 0.5),
            'cpc': market_data.get('cpc', 2.0),
            'trend': market_data.get('trend', 'stable'),
            'seasonality': market_data.get('seasonality', 'low'),
            'execution_cost': market_data.get('execution_cost', 0.3)
        }

        base_data.update({
            'ai_bonus': self._calculate_ai_bonus(keyword),
            'commercial_value': self._assess_commercial_value(keyword),
            'opportunity_indicators': self._get_opportunity_indicators(keyword),
            'keyword': keyword
        })

        serp_signals = market_data.get('serp_signals')
        if not serp_signals:
            serp_signals = self._gather_serp_signals(keyword)

        if serp_signals:
            base_data['serp_signals'] = serp_signals

        return base_data

    def _get_cached_intent_result(self, keyword: str) -> Optional[Dict[str, Any]]:
        """读取意图缓存"""
        if not self._cache_enabled:
            return None

        entry = self.intent_cache.get(keyword)
        if entry is None or not self._is_cache_entry_valid(entry):
            if entry is not None:
                self.intent_cache.pop(keyword, None)
                self._cache_dirty['intent'] = True
            return None

        return copy.deepcopy(entry.get('value'))

    def _set_cached_intent_result(self, keyword: str, value: Dict[str, Any]) -> None:
        """写入意图缓存"""
        if not self._cache_enabled:
            return

        self.intent_cache[keyword] = {
            'value': copy.deepcopy(value),
            'timestamp': datetime.now().isoformat()
        }
        self._cache_dirty['intent'] = True

    def _get_cached_market_result(self, keyword: str) -> Optional[Dict[str, Any]]:
        """读取市场缓存"""
        if not self._cache_enabled:
            return None

        entry = self.market_cache.get(keyword)
        if entry is None or not self._is_cache_entry_valid(entry):
            if entry is not None:
                self.market_cache.pop(keyword, None)
                self._cache_dirty['market'] = True
            return None

        return copy.deepcopy(entry.get('value'))

    def _set_cached_market_result(self, keyword: str, value: Dict[str, Any]) -> None:
        """写入市场缓存"""
        if not self._cache_enabled:
            return

        self.market_cache[keyword] = {
            'value': copy.deepcopy(value),
            'timestamp': datetime.now().isoformat()
        }
        self._cache_dirty['market'] = True

    def _is_cache_entry_valid(self, entry: Dict[str, Any]) -> bool:
        """检查缓存条目是否在有效期内"""
        if not isinstance(entry, dict) or 'value' not in entry:
            return False

        if not self.cache_ttl:
            return True

        timestamp = entry.get('timestamp')
        if not timestamp:
            return False

        try:
            cached_at = datetime.fromisoformat(timestamp)
        except Exception:
            return False

        return datetime.now() - cached_at <= self.cache_ttl

    def _load_caches(self) -> None:
        """加载缓存文件"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            print(f"⚠️ 无法创建缓存目录 {self.cache_dir}: {exc}")
            self._cache_enabled = False
            return

        self.intent_cache = self._read_cache_file(self.intent_cache_path, 'intent')
        self.market_cache = self._read_cache_file(self.market_cache_path, 'market')

    def _read_cache_file(self, path: Path, cache_type: str) -> Dict[str, Any]:
        """读取单个缓存文件"""
        if not path.exists():
            return {}

        try:
            with path.open('r', encoding='utf-8') as fh:
                raw_data = json.load(fh)
        except Exception as exc:
            print(f"⚠️ 无法加载缓存 {path}: {exc}")
            return {}

        if not isinstance(raw_data, dict):
            return {}

        cleaned: Dict[str, Any] = {}
        removed = False
        for keyword, entry in raw_data.items():
            if not isinstance(keyword, str) or not isinstance(entry, dict):
                removed = True
                continue
            if not self._is_cache_entry_valid(entry):
                removed = True
                continue
            cleaned[keyword] = entry

        if removed:
            self._cache_dirty[cache_type] = True

        return cleaned

    def _write_cache_file(self, path: Path, payload: Dict[str, Any]) -> None:
        """写入缓存文件"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with path.open('w', encoding='utf-8') as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"⚠️ 缓存写入失败 ({path}): {exc}")

    def _flush_caches(self) -> None:
        """将内存缓存写回磁盘"""
        if not self._cache_enabled:
            return

        if self._cache_dirty.get('intent'):
            self._write_cache_file(self.intent_cache_path, self.intent_cache)
            self._cache_dirty['intent'] = False

        if self._cache_dirty.get('market'):
            self._write_cache_file(self.market_cache_path, self.market_cache)
            self._cache_dirty['market'] = False

    @staticmethod
    def _chunked(items: List[str], chunk_size: int):
        """按批次拆分列表"""
        if not items:
            return

        try:
            chunk_size = int(chunk_size)
        except (TypeError, ValueError):
            chunk_size = len(items)

        if chunk_size <= 0:
            chunk_size = len(items)

        for idx in range(0, len(items), chunk_size):
            yield items[idx: idx + chunk_size]

    @staticmethod
    def _get_default_market_result(keyword: str = '') -> Dict[str, Any]:
        """获取默认市场分析结果"""
        return {
            'search_volume': 0,
            'competition': 0.0,
            'cpc': 0.0,
            'trend': 'unknown',
            'seasonality': 'unknown',
            'execution_cost': 0.5,
            'ai_bonus': 0,
            'commercial_value': 0,
            'opportunity_indicators': [],
            'keyword': keyword
        }

    def _analyze_keyword_intent(self, keyword: str) -> Dict[str, Any]:
        """分析关键词意图"""
        try:
            intent_map, _ = self._collect_intent_results([keyword])
            return intent_map.get(keyword, self._get_default_intent_result())
        except Exception as exc:
            print(f"⚠️ 意图分析失败 ({keyword}): {exc}")
            return self._get_default_intent_result()


    def _gather_serp_signals(self, keyword: str) -> Dict[str, Any]:
        """提取SERP信号"""
        serp_analyzer = self.serp_analyzer
        if not serp_analyzer:
            return {}
        try:
            serp_result = serp_analyzer.analyze_keyword_serp(keyword)
        except Exception as exc:
            print(f"⚠️ SERP信号提取失败 ({keyword}): {exc}")
            return {}

        features = serp_result.get('serp_features', {}) or {}
        if not features:
            return {}

        ads_reference = features.get('ads_reference_window', features.get('analyzed_results', 4))
        ads_reference = max(ads_reference or 0, 1)

        return {
            'ads_count': features.get('ads_count', 0),
            'analyzed_results': features.get('analyzed_results', 0),
            'purchase_intent_hits': features.get('purchase_intent_hits', 0),
            'purchase_intent_ratio': features.get('purchase_intent_ratio', 0.0),
            'ads_reference_window': ads_reference,
            'purchase_terms': features.get('purchase_intent_terms', []),
        }
    def _analyze_keyword_market(self, keyword: str) -> Dict[str, Any]:
        """Analyze keyword market data"""
        try:
            market_map, _ = self._collect_market_results([keyword])
            return market_map.get(keyword, self._get_default_market_result(keyword))
        except Exception as exc:
            print(f"⚠️ 市场分析失败 ({keyword}): {exc}")
            return self._get_default_market_result(keyword)

    def _normalize_scoring_weights(self):
        """Ensure opportunity scoring weights are normalized"""
        total = sum(self.scoring_weights.values()) if getattr(self, 'scoring_weights', None) else 0
        if not total:
            self.scoring_weights = {
                'intent_confidence': 0.2,
                'search_volume': 0.22,
                'competition': 0.15,
                'ai_bonus': 0.1,
                'commercial_value': 0.18,
                'serp_purchase_intent': 0.05,
                'serp_ads_presence': 0.05
            }
            total = 1.0
        if total <= 0:
            total = 1.0
        self.scoring_weights = {k: (v / total) for k, v in self.scoring_weights.items()}

    def _calculate_opportunity_score(self, intent_result: Dict, market_result: Dict, serp_signals: Optional[Dict] = None, keyword: Optional[str] = None) -> float:
        """Calculate overall opportunity score"""
        try:
            serp_signals = serp_signals or market_result.get('serp_signals') or {}
            weights = getattr(self, 'scoring_weights', None) or {
                'intent_confidence': 0.17,
                'search_volume': 0.18,
                'competition': 0.14,
                'ai_bonus': 0.07,
                'commercial_value': 0.16,
                'serp_purchase_intent': 0.05,
                'serp_ads_presence': 0.05,
                'long_tail': 0.1,
                'brand_penalty': 0.08
            }

            def _weight(key: str, default: float = 0.0) -> float:
                try:
                    return float(weights.get(key, default))
                except Exception:
                    return default

            intent_score = intent_result.get('confidence', 0) * 100
            volume_score = min(market_result.get('search_volume', 0) / 800, 1) * 100
            competition_raw = market_result.get('competition', 1)
            competition_score = max(0.0, min(1 - competition_raw, 1)) * 100

            ai_bonus_raw = market_result.get('ai_bonus', 0)
            commercial_value_raw = market_result.get('commercial_value', 0)
            ai_bonus_score = min(ai_bonus_raw * 2.5, 100)
            commercial_value_score = min(commercial_value_raw * 2.0, 100)

            purchase_ratio = serp_signals.get('purchase_intent_ratio')
            if purchase_ratio is None:
                purchase_hits = serp_signals.get('purchase_intent_hits', 0)
                analyzed_results = serp_signals.get('analyzed_results', 0)
                purchase_ratio = (purchase_hits / analyzed_results) if analyzed_results else 0.0
            serp_purchase_score = min(purchase_ratio * 100, 100)

            ads_count = serp_signals.get('ads_count', 0)
            ads_reference = max(serp_signals.get('ads_reference_window', 4), 1)
            serp_ads_score = min((ads_count / ads_reference) * 100, 100) if ads_reference else 0.0

            total_score = (
                intent_score * _weight('intent_confidence') +
                volume_score * _weight('search_volume') +
                competition_score * _weight('competition') +
                ai_bonus_score * _weight('ai_bonus') +
                commercial_value_score * _weight('commercial_value') +
                serp_purchase_score * _weight('serp_purchase_intent') +
                serp_ads_score * _weight('serp_ads_presence')
            )

            keyword_text = (keyword or market_result.get('keyword') or '').lower()
            if keyword_text:
                long_tail_signal = self._calculate_long_tail_signal(keyword_text)
                if long_tail_signal > 0:
                    total_score += long_tail_signal * _weight('long_tail', 0.1)

                brand_penalty = self._calculate_brand_penalty(keyword_text)
                if brand_penalty > 0:
                    penalty_weight = _weight('brand_penalty', 0.08)
                    total_score -= brand_penalty * penalty_weight

            execution_cost = market_result.get('execution_cost')
            if execution_cost is None:
                execution_cost = serp_signals.get('execution_cost')
            cost_penalty_weight = getattr(self, 'cost_penalty', 0.15)
            if execution_cost is not None and cost_penalty_weight:
                try:
                    normalized_cost = min(max(float(execution_cost), 0.0), 1.0)
                except Exception:
                    normalized_cost = 0.0
                total_score -= normalized_cost * cost_penalty_weight * 100

            return round(max(0.0, min(total_score, 100.0)), 2)

        except Exception as e:
            print(f"⚠️ 机会分数计算失败: {e}")
            return 0.0

    @staticmethod
    def _get_default_intent_result() -> Dict[str, Any]:
        """Return a default intent analysis result"""
        return {
            'primary_intent': 'Unknown',
            'confidence': 0.0,
            'secondary_intent': None,
            'intent_description': '分析失败',
            'website_recommendations': {}
        }

    @staticmethod
    def _calculate_ai_bonus(keyword: str) -> float:
        """Calculate extra score for AI-related keywords"""
        keyword_lower = keyword.lower()
        ai_score = 0

        ai_prefixes = ['ai', 'artificial intelligence', 'machine learning', 'deep learning']
        if any(prefix in keyword_lower for prefix in ai_prefixes):
            ai_score += 20

        ai_tool_types = ['generator', 'detector', 'writer', 'assistant', 'chatbot', 'humanizer']
        if any(tool_type in keyword_lower for tool_type in ai_tool_types):
            ai_score += 15

        brand_tokens = ['bypass', 'undetectable', 'deepseek', 'chatgpt', 'gpt', 'llm']
        if any(token in keyword_lower for token in brand_tokens):
            ai_score += 10

        return min(ai_score, 60)

    def _calculate_long_tail_signal(self, keyword: str) -> float:
        """Estimate long-tail strength to reward descriptive queries"""
        if not keyword:
            return 0.0

        tokens = [t for t in re.split(r"[^a-z0-9]+", keyword) if t]
        if not tokens:
            return 0.0

        score = 0.0

        if len(tokens) >= 4:
            score += 55
        elif len(tokens) == 3:
            score += 35
        elif len(tokens) == 2:
            score += 15

        unique_tokens = len(set(tokens))
        if unique_tokens >= 3:
            score += 10

        if any(mod in tokens for mod in self.long_tail_modifiers):
            score += 20

        if any(keyword.startswith(prefix) for prefix in self.question_prefixes):
            score += 20

        if 'for' in tokens and tokens.index('for') < len(tokens) - 1:
            score += 15

        if self._is_generic_head_term(keyword):
            score -= 40

        return max(0.0, min(score, 100.0))

    def _calculate_brand_penalty(self, keyword: str) -> float:
        """Apply penalty for branded or vendor-owned terms without unique angle"""
        if not keyword:
            return 0.0

        keyword_lower = keyword.lower()
        raw_tokens = [t for t in re.split(r"[^a-z0-9]+", keyword_lower) if t]
        if not raw_tokens:
            return 0.0

        brand_present = any(phrase in keyword_lower for phrase in self.brand_phrases)
        if not brand_present:
            brand_present = any(token in self.brand_token_set for token in raw_tokens)
        if not brand_present:
            return 0.0

        non_brand_tokens = [t for t in raw_tokens if t not in self.brand_token_set]
        if not non_brand_tokens:
            return 80.0

        if all(token in self.brand_modifier_tokens for token in non_brand_tokens):
            return 65.0

        if len(non_brand_tokens) == 1 and non_brand_tokens[0] in self.brand_modifier_tokens:
            return 55.0

        if self._is_generic_head_term(keyword_lower):
            return 45.0

        return 25.0

    def _is_generic_head_term(self, keyword: str) -> bool:
        """Detect overly generic head terms that lack modifiers"""
        if not keyword:
            return False

        keyword_lower = keyword.lower()
        if keyword_lower in self.generic_head_terms:
            return True

        tokens = [t for t in re.split(r"[^a-z0-9]+", keyword_lower) if t]
        if not tokens:
            return True

        if len(tokens) == 1:
            token = tokens[0]
            return token in self.generic_head_terms or len(token) <= 3

        if len(tokens) == 2:
            joined = " ".join(tokens)
            generic_pairs = {'ai', 'machine', 'software', 'platform', 'service', 'tool'}
            if joined in self.generic_head_terms:
                return True
            if tokens[0] in self.generic_head_terms and tokens[1] in self.generic_head_terms:
                return True
            if tokens[0] in generic_pairs and tokens[1] in self.generic_head_terms:
                return True
            if tokens[1] in generic_pairs and tokens[0] in self.generic_head_terms:
                return True

        return False

    @staticmethod
    def _assess_commercial_value(keyword: str) -> float:
        """Estimate commercial value of a keyword"""
        keyword_lower = keyword.lower()
        commercial_score = 0

        high_value_types = [
            'generator', 'converter', 'editor', 'maker', 'creator',
            'optimizer', 'enhancer', 'analyzer', 'detector'
        ]
        if any(value_type in keyword_lower for value_type in high_value_types):
            commercial_score += 25

        high_payment_domains = [
            'business', 'marketing', 'seo', 'content', 'design',
            'video', 'image', 'writing', 'coding', 'academic'
        ]
        if any(domain in keyword_lower for domain in high_payment_domains):
            commercial_score += 20

        monetization_terms = [
            'pricing', 'price', 'plan', 'plans', 'premium', 'pro', 'subscription',
            'license', 'licence', 'login', 'account', 'service', 'software',
            'discount', 'promo', 'alternative'
        ]
        if any(term in keyword_lower for term in monetization_terms):
            commercial_score += 20

        return min(commercial_score, 60)

    @staticmethod
    def _get_opportunity_indicators(keyword: str) -> List[str]:
        """获取机会指标"""
        indicators = []
        keyword_lower = keyword.lower()
        
        # AI相关
        if any(prefix in keyword_lower for prefix in ['ai', 'artificial intelligence']):
            indicators.append("AI相关需求")
        
        # 工具类
        if any(tool in keyword_lower for tool in ['generator', 'converter', 'editor']):
            indicators.append("工具类需求")
        
        # 新兴概念
        if any(concept in keyword_lower for concept in ['gpt', 'chatbot', 'neural']):
            indicators.append("新兴技术")
        
        # 出海友好
        if not any(ord(char) > 127 for char in keyword):
            indicators.append("出海友好")
        
        return indicators
    
    @staticmethod
    def _generate_intent_summary(keywords: List[Dict]) -> Dict[str, Any]:
        """生成意图摘要"""
        intent_counts = {}
        total_keywords = len(keywords)
        
        for kw in keywords:
            intent = kw['intent']['primary_intent']
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        intent_percentages = {
            intent: round(count / total_keywords * 100, 1)
            for intent, count in intent_counts.items()
        }
        
        return {
            'total_keywords': total_keywords,
            'intent_distribution': intent_counts,
            'intent_percentages': intent_percentages,
            'dominant_intent': max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else 'Unknown'
        }

    @staticmethod
    def _generate_market_insights(keywords: List[Dict]) -> Dict[str, Any]:
        """Generate market insight summary"""
        high_opportunity = [kw for kw in keywords if kw['opportunity_score'] >= 70]
        medium_opportunity = [kw for kw in keywords if 40 <= kw['opportunity_score'] < 70]
        low_opportunity = [kw for kw in keywords if kw['opportunity_score'] < 40]

        avg_cost = 0.0
        if keywords:
            total_cost = sum((kw.get('execution_cost') or kw.get('market', {}).get('execution_cost', 0.0)) for kw in keywords)
            avg_cost = round(total_cost / len(keywords), 2)

        low_cost_keywords = [
            kw for kw in keywords
            if (kw.get('execution_cost') or kw.get('market', {}).get('execution_cost', 1.0)) <= 0.35
        ]

        return {
            'high_opportunity_count': len(high_opportunity),
            'medium_opportunity_count': len(medium_opportunity),
            'low_opportunity_count': len(low_opportunity),
            'top_opportunities': sorted(keywords, key=lambda x: x['opportunity_score'], reverse=True)[:10],
            'avg_opportunity_score': round(sum(kw['opportunity_score'] for kw in keywords) / len(keywords), 2) if keywords else 0,
            'avg_execution_cost': avg_cost,
            'low_cost_candidates': low_cost_keywords[:5]
        }

    @staticmethod
    def _generate_recommendations(keywords: List[Dict]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        # 分析关键词分布
        high_opportunity = [kw for kw in keywords if kw['opportunity_score'] >= 70]
        ai_keywords = [kw for kw in keywords if kw['market'].get('ai_bonus', 0) > 0]
        
        # 高机会关键词建议
        if high_opportunity:
            recommendations.append(f"🎯 发现 {len(high_opportunity)} 个高机会关键词，建议立即开发MVP产品")
            top_3 = sorted(high_opportunity, key=lambda x: x['opportunity_score'], reverse=True)[:3]
            for i, kw in enumerate(top_3, 1):
                recommendations.append(f"   {i}. {kw['keyword']} (机会分数: {kw['opportunity_score']})")
        
        # AI相关建议
        if ai_keywords:
            recommendations.append(f"🤖 发现 {len(ai_keywords)} 个AI相关关键词，符合出海AI工具方向")
        
        return recommendations
    
    @staticmethod
    def _save_analysis_results(results: Dict[str, Any], output_dir: str) -> str:
        """保存分析结果"""
        from src.utils.file_utils import save_results_with_timestamp
        
        # 保存JSON格式
        json_path = save_results_with_timestamp(results, output_dir, 'keyword_analysis')
        
        # 保存CSV格式（关键词详情）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = os.path.join(output_dir, f'keywords_detail_{timestamp}.csv')
        keywords_df = pd.DataFrame([
            {
                'keyword': kw['keyword'],
                'primary_intent': kw['intent']['primary_intent'],
                'confidence': kw['intent']['confidence'],
                'search_volume': kw['market']['search_volume'],
                'competition': kw['market']['competition'],
                'opportunity_score': kw['opportunity_score']
            }
            for kw in results['keywords']
        ])
        keywords_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        return json_path
    
    def _comprehensive_analyze(self, input_source: str, analysis_type: str, output_dir: str = None) -> Dict[str, Any]:
        """使用综合分析器进行全面分析"""
        print("🔧 启动综合分析模式...")
        
        # 准备数据
        if analysis_type == 'file':
            if not os.path.exists(input_source):
                raise FileNotFoundError(f"输入文件不存在: {input_source}")
            
            # 读取数据
            if input_source.endswith('.csv'):
                df = pd.read_csv(input_source)
            elif input_source.endswith('.json'):
                df = pd.read_json(input_source)
            else:
                raise ValueError("不支持的文件格式，请使用CSV或JSON文件")
            
            print(f"✅ 成功读取 {len(df)} 条关键词数据")
            
        elif analysis_type == 'keywords':
            keywords = [input_source] if isinstance(input_source, str) else input_source
            df = pd.DataFrame({'query': keywords})
            print(f"✅ 接收到 {len(keywords)} 个关键词")
        else:
            raise ValueError(f"不支持的分析类型: {analysis_type}")
        
        # 执行综合分析
        try:
            analysis_result = self.comprehensive_analyzer.analyze(df)
            
            # 保存结果
            if output_dir:
                output_path = self.comprehensive_analyzer.export_comprehensive_report(
                    analysis_result, output_dir
                )
                analysis_result['output_path'] = output_path
                print(f"📊 综合分析报告已保存到: {output_dir}")
            
            # 生成简化的返回结果（兼容原有接口）
            simplified_result = self._convert_to_legacy_format(analysis_result)
            
            return simplified_result
            
        except Exception as e:
            print(f"❌ 综合分析失败: {e}")
            # 降级到原有分析方法
            print("🔄 降级到基础分析模式...")
            if analysis_type == 'file':
                return self._analyze_from_file(input_source, output_dir)
            else:
                return self._analyze_from_keywords([input_source], output_dir)
    
    def _convert_to_legacy_format(self, comprehensive_result: Dict[str, Any]) -> Dict[str, Any]:
        """将综合分析结果转换为兼容原有接口的格式"""
        df = comprehensive_result['results']
        summary = comprehensive_result['summary']
        
        # 转换为原有格式
        legacy_result = {
            'total_keywords': summary['total_keywords'],
            'analysis_time': comprehensive_result['analysis_time'],
            'keywords': [],
            'intent_summary': {},
            'market_insights': {},
            'recommendations': [],
            'comprehensive_summary': summary  # 新增综合摘要
        }
        
        # 转换关键词详情
        for _, row in df.iterrows():
            keyword_result = {
                'keyword': row['query'],
                'comprehensive_score': row.get('comprehensive_score', 0),
                'comprehensive_grade': row.get('comprehensive_grade', 'C'),
                'intent': {
                    'primary_intent': row.get('intent_intent', 'Unknown'),
                    'confidence': row.get('intent_confidence', 0.0),
                    'intent_description': row.get('intent_intent_description', '')
                },
                'market': {
                    'search_volume': row.get('market_search_volume', 0),
                    'competition': row.get('market_competition', 0.5),
                    'cpc': row.get('market_cpc', 0.0)
                },
                'timeliness': {
                    'score': row.get('timeliness_score', 50.0),
                    'grade': row.get('timeliness_grade', 'C'),
                    'trend_direction': row.get('timeliness_trend_direction', 'stable')
                },
                'scorer': {
                    'total_score': row.get('scorer_total_score', 50.0),
                    'pray_score': row.get('scorer_pray_score', 50.0),
                    'commercial_score': row.get('scorer_commercial_score', 30.0)
                },
                'opportunity_score': row.get('comprehensive_score', 50.0)  # 使用综合评分作为机会分数
            }
            legacy_result['keywords'].append(keyword_result)
        
        # 生成意图摘要
        if 'intent_intent' in df.columns:
            intent_counts = df['intent_intent'].value_counts().to_dict()
            total = len(df)
            legacy_result['intent_summary'] = {
                'total_keywords': total,
                'intent_distribution': intent_counts,
                'intent_percentages': {k: round(v/total*100, 1) for k, v in intent_counts.items()},
                'dominant_intent': max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else 'Unknown'
            }
        
        # 生成市场洞察
        high_opportunity = df[df['comprehensive_score'] >= 80] if 'comprehensive_score' in df.columns else pd.DataFrame()
        medium_opportunity = df[(df['comprehensive_score'] >= 60) & (df['comprehensive_score'] < 80)] if 'comprehensive_score' in df.columns else pd.DataFrame()
        low_opportunity = df[df['comprehensive_score'] < 60] if 'comprehensive_score' in df.columns else pd.DataFrame()
        
        legacy_result['market_insights'] = {
            'high_opportunity_count': len(high_opportunity),
            'medium_opportunity_count': len(medium_opportunity),
            'low_opportunity_count': len(low_opportunity),
            'top_opportunities': df.nlargest(10, 'comprehensive_score')[['query', 'comprehensive_score']].to_dict('records') if 'comprehensive_score' in df.columns else [],
            'avg_opportunity_score': round(df['comprehensive_score'].mean(), 2) if 'comprehensive_score' in df.columns else 50.0
        }
        
        # 生成建议
        recommendations = []
        if len(high_opportunity) > 0:
            recommendations.append(f"🎯 发现 {len(high_opportunity)} 个高价值关键词 (综合评分≥80)，建议优先开发")
            top_3 = high_opportunity.nlargest(3, 'comprehensive_score')
            for i, (_, row) in enumerate(top_3.iterrows(), 1):
                recommendations.append(f"   {i}. {row['query']} (综合评分: {row['comprehensive_score']})")
        
        if 'timeliness_grade' in df.columns:
            high_timeliness = df[df['timeliness_grade'].isin(['A', 'B'])]
            if len(high_timeliness) > 0:
                recommendations.append(f"⏰ 发现 {len(high_timeliness)} 个高时效性关键词，建议快速行动")
        
        if 'scorer_commercial_score' in df.columns:
            high_commercial = df[df['scorer_commercial_score'] >= 70]
            if len(high_commercial) > 0:
                recommendations.append(f"💰 发现 {len(high_commercial)} 个高商业价值关键词，变现潜力大")
        
        legacy_result['recommendations'] = recommendations
        
        return legacy_result
