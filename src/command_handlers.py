#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令处理器模块
处理各种命令行参数对应的功能
"""

import os
import sys
import json
from pathlib import Path
import re
import time
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Set

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.cli_parser import print_quiet_summary, get_reports_dir
from src.utils.enhanced_features import (
    monitor_competitors, predict_keyword_trends, generate_seo_audit,
    batch_build_websites
)
from src.demand_mining.tools.multi_platform_keyword_discovery import MultiPlatformKeywordDiscovery
from src.collectors.suggestion_sources import SuggestionCollector
from src.collectors.rss_hotspot_collector import RSSHotspotCollector


def handle_stats_display(manager, args):
    """处理统计信息显示"""
    if args.stats:
        stats = manager.get_manager_stats()
        print("\n📊 管理器统计信息:")
        for manager_name, manager_stats in stats.items():
            if isinstance(manager_stats, dict):
                print(f"\n{manager_name}:")
                for key, value in manager_stats.items():
                    print(f"  {key}: {value}")
            else:
                print(f"{manager_name}: {manager_stats}")
        return True
    return False



STOPWORD_PATTERNS = [
    r'\b(?:news|weather|today|tomorrow|yesterday)\b',
    r'\b(?:login|signup|account|app|download|logo|price|stock|settlement|marketplace)\b',
    r'\b(?:live stream|live score|highlights|match result|match results|score)\b',
    r'\b(?:facebook|instagram|tiktok|youtube|twitter|google|bing|reddit)\b',
]


def _filter_trending_keywords(df):
    """对热门候选词做基础去噪过滤"""
    if df is None or df.empty:
        return df

    if 'query' not in df.columns:
        return df

    filtered = df.copy()
    filtered['query'] = filtered['query'].astype(str)
    filtered['query_lower'] = filtered['query'].str.lower().str.strip()

    initial_count = len(filtered)

    # 过滤过短或非字母数字的词
    filtered = filtered[filtered['query_lower'].str.len() >= 3]
    filtered = filtered[~filtered['query_lower'].str.match(r'^[\d\W_]+$')]

    # 常见品牌/泛词去噪
    for pattern in STOPWORD_PATTERNS:
        filtered = filtered[~filtered['query_lower'].str.contains(pattern, regex=True)]

    # 去重
    filtered = filtered.drop_duplicates(subset=['query_lower']).reset_index(drop=True)
    filtered = filtered.drop(columns=['query_lower'])

    removed = initial_count - len(filtered)
    if removed > 0:
        print(f'[Filter] 已过滤 {removed} 条低质量热门词')

    return filtered


def _print_new_word_summary(summary: Dict[str, Any]) -> None:
    if not summary or not isinstance(summary, dict):
        return

    total = summary.get('total_analyzed')
    detected = summary.get('new_words_detected')
    breakout = summary.get('breakout_keywords')
    rising = summary.get('rising_keywords')
    high_conf = summary.get('high_confidence_new_words')

    print("\n🔎 新词检测摘要:")
    print(f"   • 检测总数: {total}")
    print(f"   • 新词数量: {detected} / 高置信度: {high_conf}")
    if breakout is not None or rising is not None:
        print(f"   • Breakout: {breakout} / Rising: {rising}")
    percentage = summary.get('new_word_percentage')
    if percentage is not None:
        print(f"   • 新词占比: {percentage}%")

    report_files = summary.get('report_files')
    if isinstance(report_files, dict) and report_files:
        print("   • 导出文件:")
        for label, path in report_files.items():
            print(f"     - {label}: {path}")


def _print_top_new_words(result: Dict[str, Any], limit: int = 5) -> None:
    if not result or 'keywords' not in result:
        return

    candidates = []
    for item in result['keywords']:
        nwd = item.get('new_word_detection') if isinstance(item, dict) else None
        if not nwd or not nwd.get('is_new_word'):
            continue
        candidates.append({
            'keyword': item.get('keyword') or item.get('query'),
            'score': nwd.get('new_word_score', 0.0),
            'momentum': nwd.get('trend_momentum'),
            'delta': nwd.get('avg_7d_delta', 0.0),
            'grade': nwd.get('new_word_grade', 'D'),
            'confidence': nwd.get('confidence_level', 'low')
        })

    if not candidates:
        return

    candidates.sort(key=lambda x: (x['momentum'] == 'breakout', x['score']), reverse=True)
    print("\n🔥 Top 新词候选:")
    for idx, item in enumerate(candidates[:limit], 1):
        print(
            f"   {idx}. {item['keyword']} | 分数 {item['score']:.1f} | 动量 {item['momentum']} "
            f"| Δ7D {item['delta']:.1f} | 等级 {item['grade']} | 置信度 {item['confidence']}"
        )


def _extract_records_from_df(df: Optional[pd.DataFrame], source_label: str, seed: str,
                             limit: int, seen_terms: Set[str], text_fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """从DataFrame中提取候选关键词记录"""
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return []

    records: List[Dict[str, Any]] = []
    usable_fields = text_fields or ['query', 'topic_title', 'title']

    for _, row in df.head(max(limit, 0)).iterrows():
        text_value: Optional[str] = None
        for field in usable_fields:
            if field in row and pd.notna(row[field]):
                candidate_text = str(row[field]).strip()
                if candidate_text:
                    text_value = candidate_text
                    break
        if not text_value:
            continue

        normalized = text_value.lower()
        if normalized in seen_terms:
            continue

        record: Dict[str, Any] = {
            'query': text_value,
            'source': source_label,
            'seed': seed
        }

        if 'value' in row and pd.notna(row['value']):
            record['value'] = row['value']
        if 'formattedValue' in row and pd.notna(row['formattedValue']):
            record['growth'] = row['formattedValue']

        records.append(record)
        seen_terms.add(normalized)

    return records


def _collect_trends_related_candidates(trends_collector, seed_keywords: List[str],
                                       geo: str = '', timeframe: str = 'today 12-m',
                                       per_category_limit: int = 5) -> pd.DataFrame:
    """基于种子关键词补集 Google Trends 相关查询/主题建议"""
    if not trends_collector or not seed_keywords:
        return pd.DataFrame(columns=['query', 'source'])

    unique_seeds: List[str] = []
    seen_seed: Set[str] = set()
    for keyword in seed_keywords:
        if not keyword:
            continue
        normalized = str(keyword).strip().lower()
        if not normalized or normalized in seen_seed:
            continue
        unique_seeds.append(str(keyword).strip())
        seen_seed.add(normalized)
        if len(unique_seeds) >= 8:
            break

    if not unique_seeds:
        return pd.DataFrame(columns=['query', 'source'])

    seen_terms: Set[str] = set(seen_seed)
    rows: List[Dict[str, Any]] = []

    for seed in unique_seeds:
        if hasattr(trends_collector, 'is_in_cooldown') and trends_collector.is_in_cooldown():
            print("⚠️ Google Trends 处于冷却期，终止相关查询采集")
            break
        try:
            related_queries = trends_collector.get_related_queries(seed, geo=geo, timeframe=timeframe)
        except Exception as exc:
            print(f"⚠️ 获取 {seed} 相关查询失败: {exc}")
            related_queries = {}

        seed_map = None
        if isinstance(related_queries, dict):
            seed_map = related_queries.get(seed)
            if seed_map is None and len(related_queries) == 1:
                seed_map = next(iter(related_queries.values()))

        if isinstance(seed_map, dict):
            rows.extend(_extract_records_from_df(
                seed_map.get('rising'),
                'Google Trends Related Rising',
                seed,
                per_category_limit,
                seen_terms
            ))
            rows.extend(_extract_records_from_df(
                seed_map.get('top'),
                'Google Trends Related Top',
                seed,
                per_category_limit,
                seen_terms
            ))
        elif isinstance(related_queries, pd.DataFrame):
            rows.extend(_extract_records_from_df(
                related_queries,
                'Google Trends Related Queries',
                seed,
                per_category_limit,
                seen_terms
            ))

        try:
            related_topics = trends_collector.get_related_topics(seed, geo=geo, timeframe=timeframe)
        except Exception as exc:
            print(f"⚠️ 获取 {seed} 相关主题失败: {exc}")
            related_topics = {}

        if hasattr(trends_collector, 'is_in_cooldown') and trends_collector.is_in_cooldown():
            print("⚠️ Google Trends 冷却中，停止继续采集相关主题")
            break

        topic_map = None
        if isinstance(related_topics, dict):
            topic_map = related_topics.get(seed)
            if topic_map is None and len(related_topics) == 1:
                topic_map = next(iter(related_topics.values()))

        if isinstance(topic_map, dict):
            rows.extend(_extract_records_from_df(
                topic_map.get('rising'),
                'Google Trends Related Topics Rising',
                seed,
                per_category_limit,
                seen_terms,
                text_fields=['topic_title', 'title', 'query']
            ))
            rows.extend(_extract_records_from_df(
                topic_map.get('top'),
                'Google Trends Related Topics Top',
                seed,
                per_category_limit,
                seen_terms,
                text_fields=['topic_title', 'title', 'query']
            ))
        elif isinstance(related_topics, pd.DataFrame):
            rows.extend(_extract_records_from_df(
                related_topics,
                'Google Trends Related Topics',
                seed,
                per_category_limit,
                seen_terms,
                text_fields=['topic_title', 'title', 'query']
            ))

        try:
            suggestions = trends_collector.get_suggestions(seed) or []
        except Exception as exc:
            print(f"⚠️ 获取 {seed} Suggestion 失败: {exc}")
            suggestions = []

        for suggestion in suggestions[:max(per_category_limit, 0)]:
            title = suggestion.get('title') if isinstance(suggestion, dict) else None
            if not title:
                continue
            normalized = str(title).strip().lower()
            if not normalized or normalized in seen_terms:
                continue
            rows.append({
                'query': str(title).strip(),
                'source': 'Google Trends Suggestion',
                'seed': seed
            })
            seen_terms.add(normalized)

        time.sleep(0.5)

    if not rows:
        return pd.DataFrame(columns=['query', 'source'])

    return pd.DataFrame(rows)


def _generate_keyword_combinations(seed_keywords: List[str], manager, long_tail_limit: int = 4,
                                   prefix_limit: int = 3, head_limit: int = 3) -> pd.DataFrame:
    """基于种子词生成组合关键词"""
    if not seed_keywords or manager is None:
        return pd.DataFrame(columns=['query', 'source'])

    unique_seeds: List[str] = []
    seen_seed: Set[str] = set()
    for keyword in seed_keywords:
        if not keyword:
            continue
        normalized = str(keyword).strip().lower()
        if not normalized or normalized in seen_seed:
            continue
        unique_seeds.append(str(keyword).strip())
        seen_seed.add(normalized)
        if len(unique_seeds) >= 8:
            break

    if not unique_seeds:
        return pd.DataFrame(columns=['query', 'source'])

    long_tail_terms = sorted(getattr(manager, 'long_tail_modifiers', []), key=lambda x: (len(x), x))[:max(long_tail_limit, 0)]
    question_prefixes = list(getattr(manager, 'question_prefixes', ()))[:max(prefix_limit, 0)]
    generic_heads = sorted(getattr(manager, 'generic_head_terms', []), key=lambda x: (len(x), x))[:max(head_limit, 0)]

    rows: List[Dict[str, Any]] = []
    seen_terms: Set[str] = set(seen_seed)

    def _append_candidate(text: str, source_label: str, seed: str) -> None:
        candidate = text.strip()
        if not candidate:
            return
        normalized = candidate.lower()
        if normalized in seen_terms:
            return
        rows.append({'query': candidate, 'source': source_label, 'seed': seed})
        seen_terms.add(normalized)

    for seed in unique_seeds:
        for modifier in long_tail_terms:
            if modifier:
                _append_candidate(f"{seed} {modifier}".strip(), 'Generated Long Tail', seed)
        for prefix in question_prefixes:
            if prefix:
                _append_candidate(f"{prefix} {seed}".strip(), 'Generated Question Prefix', seed)
        for head in generic_heads:
            if head:
                _append_candidate(f"{seed} {head}".strip(), 'Generated Generic Head', seed)

    if not rows:
        return pd.DataFrame(columns=['query', 'source'])

    return pd.DataFrame(rows)

def handle_input_file_analysis(manager, args):
    """处理关键词文件分析"""
    if not args.input:
        return False
        
    # 分析关键词文件
    if not args.quiet:
        print("🚀 开始分析关键词文件...")
        if args.serp:
            print("🔍 已启用SERP分析功能")
    
    result = manager.analyze_keywords(args.input, args.output, enable_serp=args.serp)
    
    # 显示结果
    if args.quiet:
        print_quiet_summary(result)
    else:
        print(f"\n🎉 分析完成! 共分析 {result['total_keywords']} 个关键词")
        print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
        print(f"📈 平均机会分数: {result['market_insights']['avg_opportunity_score']}")

        # 显示新词检测摘要
        _print_new_word_summary(result.get('new_word_summary'))
        _print_top_new_words(result)

        # 显示SERP分析摘要
        if 'serp_summary' in result and result['serp_summary'].get('serp_analysis_enabled', False):
            serp_summary = result['serp_summary']
            print(f"🔍 SERP分析: 分析了 {serp_summary['total_analyzed']} 个关键词")
            print(f"   高置信度SERP: {serp_summary['high_confidence_serp']} 个")
            print(f"   商业意图关键词: {serp_summary['commercial_intent_keywords']} 个")

        # 显示Top 5关键词
        top_keywords = result['market_insights']['top_opportunities'][:5]
        if top_keywords:
            print("\n🏆 Top 5 机会关键词:")
            for i, kw in enumerate(top_keywords, 1):
                intent_desc = kw['intent']['intent_description']
                score = kw['opportunity_score']
                new_word_info = ""
                if 'new_word_detection' in kw and kw['new_word_detection']['is_new_word']:
                    new_word_grade = kw['new_word_detection']['new_word_grade']
                    new_word_info = f" [新词-{new_word_grade}级]"
                print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc}){new_word_info}")
    
    return True


def handle_keywords_analysis(manager, args):
    """处理单个关键词分析"""
    if not args.keywords:
        return False
        
    # 分析单个关键词
    if not args.quiet:
        print("🚀 开始分析输入的关键词...")
    
    keywords = [kw for kw in args.keywords if kw]
    result = manager.analyze_keywords(keywords, args.output, enable_serp=args.serp)

    # 显示结果
    if args.quiet:
        print_quiet_summary(result)
    else:
        print(f"\n🎉 分析完成! 共分析 {len(args.keywords)} 个关键词")

        # 显示每个关键词的结果
        print("\n📋 关键词分析结果:")
        for kw_result in result['keywords']:
            keyword = kw_result['keyword']
            score = kw_result['opportunity_score']
            intent = kw_result['intent']['intent_description']
            print(f"   • {keyword}: 机会分数 {score}, 意图: {intent}")
    return True


def handle_discover_analysis(manager, args):
    """处理多平台关键词发现"""
    if not args.discover:
        return False
        
    seed_profile = getattr(args, 'seed_profile', None)
    seed_limit = getattr(args, 'seed_limit', None)
    if isinstance(seed_limit, int) and seed_limit <= 0:
        seed_limit = None
    min_seed_terms = getattr(args, 'min_seed_terms', None)
    if isinstance(min_seed_terms, int) and min_seed_terms <= 0:
        min_seed_terms = None

    # 多平台关键词发现
    raw_terms = [] if args.discover == ['default'] else args.discover
    
    try:
        # 创建发现工具
        discoverer = MultiPlatformKeywordDiscovery()

        search_terms = discoverer.prepare_search_terms(
            seeds=raw_terms,
            profile=seed_profile,
            limit=seed_limit,
            min_terms=min_seed_terms
        )

        if not search_terms:
            print("⚠️ 缺少有效的种子关键词，无法执行多平台发现")
            return True

        if not args.quiet:
            print("🔍 开始多平台关键词发现...")
            print(f"📊 搜索词汇: {', '.join(search_terms)}")
        
        # 执行发现
        df = discoverer.discover_all_platforms(search_terms)

        if not df.empty:
            # 分析趋势
            analysis = discoverer.analyze_keyword_trends(df)
            
            # 保存结果
            output_dir = os.path.join(args.output, 'multi_platform_discovery')
            csv_path, json_path = discoverer.save_results(df, analysis, output_dir)
            
            if args.quiet:
                # 静默模式显示
                print(f"\n🎯 多平台关键词发现结果:")
                print(f"   • 发现关键词: {analysis['total_keywords']} 个")
                print(f"   • 平台分布: {analysis['platform_distribution']}")
                
                # 显示Top 3关键词
                top_keywords = analysis['top_keywords_by_score'][:3]
                if top_keywords:
                    print("\n🏆 Top 3 热门关键词:")
                    for i, kw in enumerate(top_keywords, 1):
                        print(f"   {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
            else:
                # 详细模式显示
                print(f"\n🎉 多平台关键词发现完成!")
                print(f"📊 发现 {analysis['total_keywords']} 个关键词")
                print(f"🌐 平台分布: {analysis['platform_distribution']}")
                
                print(f"\n🏆 热门关键词:")
                for i, kw in enumerate(analysis['top_keywords_by_score'][:5], 1):
                    print(f"  {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
            
            print(f"\n📁 结果已保存:")
            print(f"  CSV: {csv_path}")
            print(f"  JSON: {json_path}")
            
            # 询问是否要立即分析发现的关键词
            if not args.quiet:
                user_input = input("\n🤔 是否要立即分析这些关键词的意图和市场机会? (y/n): ")
                if user_input.lower() in ['y', 'yes', '是']:
                    print("🔄 开始分析发现的关键词...")
                    result = manager.analyze_keywords(csv_path, args.output)
                    print(f"✅ 关键词分析完成! 共分析 {result['total_keywords']} 个关键词")
                    print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
        else:
            print("⚠️ 未发现任何关键词，请检查网络连接或调整搜索参数")
            
    except ImportError as e:
        print(f"❌ 导入多平台发现工具失败: {e}")
        print("请确保所有依赖已正确安装")
    except Exception as e:
        print(f"❌ 多平台关键词发现失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    return True


def handle_enhanced_features(manager, args):
    """处理增强功能 (竞品监控、趋势预测、SEO审计、批量建站)"""
    # 竞品监控
    if args.monitor_competitors:
        sites = args.sites or ['canva.com', 'midjourney.com', 'openai.com']
        if not args.quiet:
            print(f"🔍 开始监控 {len(sites)} 个竞品网站...")
        
        try:
            result = monitor_competitors(sites, args.output)
        except Exception as exc:
            print(f"❌ 竞品监控失败: {exc}")
            return True

        print(f"✅ 竞品监控完成: 分析了 {len(result['competitors'])} 个竞品")

        if not args.quiet:
            print("\n📊 监控结果摘要:")
            for comp in result['competitors'][:3]:
                print(f"  • {comp['site']}: {comp['new_keywords_count']} 个新关键词")
        return True
    
    # 趋势预测
    if args.predict_trends:
        if not args.quiet:
            print(f"📈 开始预测未来 {args.timeframe} 的关键词趋势...")
        
        # 获取关键词列表（如果有的话）
        keywords_for_prediction = getattr(args, 'keywords', None)
        
        try:
            result = predict_keyword_trends(
                timeframe=args.timeframe, 
                output_dir=args.output,
                keywords=keywords_for_prediction,
                use_real_data=True
            )
        except Exception as exc:
            print(f"❌ 趋势预测失败: {exc}")
            return True
        
        # 显示结果
        data_source = result.get('data_source', 'unknown')
        if data_source == 'google_trends_real_data':
            print(f"✅ 真实数据趋势预测完成: {len(result['rising_keywords'])} 上升, {len(result['stable_keywords'])} 稳定, {len(result['declining_keywords'])} 下降")
        else:
            print(f"✅ 趋势预测完成: 预测了 {len(result['rising_keywords'])} 个上升关键词 (数据源: {data_source})")
        
        if not args.quiet:
            print("\n📈 趋势预测摘要:")
            
            # 显示上升关键词
            if result['rising_keywords']:
                print("\n🔥 上升趋势关键词:")
                for kw in result['rising_keywords'][:3]:
                    growth = kw.get('predicted_growth', kw.get('growth_rate', 'N/A'))
                    confidence = kw.get('confidence', 0)
                    print(f"  📈 {kw['keyword']}: {growth} (置信度: {confidence:.0%})")
            
            # 显示稳定关键词
            if result['stable_keywords']:
                print("\n📊 稳定趋势关键词:")
                for kw in result['stable_keywords'][:2]:
                    growth = kw.get('predicted_change', kw.get('growth_rate', 'N/A'))
                    confidence = kw.get('confidence', 0)
                    print(f"  📊 {kw['keyword']}: {growth} (置信度: {confidence:.0%})")
            
            # 显示下降关键词
            if result['declining_keywords']:
                print("\n📉 下降趋势关键词:")
                for kw in result['declining_keywords'][:2]:
                    decline = kw.get('predicted_decline', kw.get('growth_rate', 'N/A'))
                    confidence = kw.get('confidence', 0)
                    print(f"  📉 {kw['keyword']}: {decline} (置信度: {confidence:.0%})")
        
        return True
    
    # SEO审计
    if args.seo_audit:
        if not args.domain:
            print("❌ 请指定要审计的域名 (--domain)")
            return True
        
        if not args.quiet:
            print(f"🔍 开始SEO审计: {args.domain}")
        
        try:
            result = generate_seo_audit(args.domain, args.keywords)
        except Exception as exc:
            print(f"❌ SEO审计失败: {exc}")
            return True

        print(f"✅ SEO审计完成: 发现 {len(result['keyword_opportunities'])} 个关键词机会")

        if not args.quiet:
            print("\n🎯 SEO优化建议:")
            for gap in result['content_gaps'][:3]:
                print(f"  • {gap}")
        return True
    
    # 批量建站
    if args.build_websites:
        if not args.quiet:
            print(f"🏗️ 开始批量生成 {args.top_keywords} 个网站...")
        
        try:
            result = batch_build_websites(args.top_keywords, args.output)
        except Exception as exc:
            print(f"❌ 批量建站失败: {exc}")
            return True

        print(f"✅ 批量建站完成: 成功构建 {result['successful_builds']} 个网站")

        if not args.quiet:
            print("\n🌐 构建的网站:")
            for site in result['websites'][:3]:
                print(f"  • {site['keyword']}: {site['domain_suggestion']}")
        return True
    
    return False


def handle_hot_keywords(manager, args):
    """处理热门关键词搜索和需求挖掘"""
    if not args.hotkeywords:
        return False
    
    # 搜索热门关键词：使用 fetch_rising_queries 获取关键词并进行需求挖掘
    if not args.quiet:
        print("🔥 开始搜索热门关键词并进行需求挖掘...")
    
    try:
        # 使用单例获取 TrendsCollector
        from src.collectors.trends_singleton import get_trends_collector
        
        # 获取 TrendsCollector 单例实例
        trends_collector = get_trends_collector()
        
        # 使用 fetch_rising_queries 获取热门关键词
        if not args.quiet:
            print("🔍 正在获取 Rising Queries...")
        
        rising_queries = trends_collector.fetch_rising_queries()
        
        # 将 rising queries 转换为DataFrame格式
        if isinstance(rising_queries, pd.DataFrame):
            # 如果已经是DataFrame，直接使用
            trending_df = rising_queries.head(20)  # 限制前20个
            # 确保有query列
            if 'query' not in trending_df.columns:
                if 'title' in trending_df.columns:
                    trending_df = trending_df.rename(columns={'title': 'query'})
                elif len(trending_df.columns) > 0:
                    trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
        elif rising_queries and len(rising_queries) > 0:
            # 如果返回的是字符串列表
            if isinstance(rising_queries[0], str):
                trending_df = pd.DataFrame([
                    {'query': query}
                    for query in rising_queries[:20]  # 限制前20个
                ])
            # 如果返回的是字典列表
            elif isinstance(rising_queries[0], dict):
                trending_df = pd.DataFrame([
                    {
                        'query': item.get('query', item.get('keyword', str(item))),
                        'value': item.get('value', item.get('interest', 0))
                    }
                    for item in rising_queries[:20]  # 限制前20个
                ])
            else:
                # 其他格式，尝试转换为字符串
                trending_df = pd.DataFrame([
                    {'query': str(query)}
                    for query in rising_queries[:20]
                ])
        else:
            trending_df = pd.DataFrame(columns=['query'])

        if trending_df is not None and not trending_df.empty:
            all_trending_keywords = [trending_df]

            seed_pool = trending_df['query'].dropna().astype(str).tolist()

            # RSS 热点
            try:
                rss_df = RSSHotspotCollector().collect(max_items=20)
                if not rss_df.empty:
                    all_trending_keywords.append(rss_df)
                    if not args.quiet:
                        print(f"✅ RSS 热点: 获取到 {len(rss_df)} 个热点词")
            except Exception as exc:
                if not args.quiet:
                    print(f"⚠️ RSS 热点抓取失败: {exc}")

            # Google Trends 相关词
            try:
                related_df = _collect_trends_related_candidates(trends_collector, seed_pool)
                if not related_df.empty:
                    all_trending_keywords.append(related_df)
                    if not args.quiet:
                        print(f"✅ Google Trends 关联扩展: 新增 {len(related_df)} 个候选关键词")
            except Exception as exc:
                if not args.quiet:
                    print(f"⚠️ Google Trends 关联扩展失败: {exc}")

            # 组合生成
            try:
                combo_df = _generate_keyword_combinations(seed_pool, manager)
                if not combo_df.empty:
                    all_trending_keywords.append(combo_df)
                    if not args.quiet:
                        print(f"✅ 组合生成: 新增 {len(combo_df)} 个候选关键词")
            except Exception as exc:
                if not args.quiet:
                    print(f"⚠️ 组合生成失败: {exc}")

            # Suggestion 来源
            suggestion_records: List = []
            try:
                suggestion_collector = SuggestionCollector()
                suggestion_records = suggestion_collector.collect(seed_pool, per_seed_limit=4)
            except Exception as exc:
                if not args.quiet:
                    print(f"⚠️ Suggestion 收集失败: {exc}")

            if suggestion_records:
                suggestion_df = pd.DataFrame([
                    {
                        'query': item.term,
                        'source': f"Suggestions/{item.source}",
                        'seed': item.seed
                    }
                    for item in suggestion_records if item.term
                ])
                if not suggestion_df.empty:
                    all_trending_keywords.append(suggestion_df)
                    if not args.quiet:
                        print(f"✅ 热门联想: 新增 {len(suggestion_df)} 个候选关键词")
                        stats = suggestion_collector.get_last_stats()
                        print(
                            f"   • 联想摘要: 种子 {stats['seeds_processed']}/{stats['seeds_total']} | 请求 {stats['requests_sent']} | 建议 {stats['suggestions_collected']}"
                        )

            trending_df = pd.concat(all_trending_keywords, ignore_index=True)
            trending_df = trending_df.drop_duplicates(subset=['query'], keep='first')
            trending_df = trending_df.head(50)
            filtered = _filter_trending_keywords(trending_df)
            if not filtered.empty:
                trending_df = filtered
            else:
                print("[Filter] 热门关键词过滤后为空，继续使用未过滤结果")

            # 保存热门关键词到临时文件
            
            # 确保DataFrame有正确的列名
            if 'query' not in trending_df.columns and len(trending_df.columns) > 0:
                # 如果没有query列，使用第一列作为关键词
                trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
            
            # 清洗并直接在内存中触发需求挖掘
            try:
                from src.pipeline.cleaning.cleaner import clean_terms, CleaningConfig
                if 'query' in trending_df.columns:
                    cleaned = clean_terms(
                        trending_df['query'].astype(str).tolist(),
                        CleaningConfig()
                    )
                    trending_df = pd.DataFrame({'query': cleaned})
            except Exception:
                pass

            if not args.quiet:
                print(f"🔍 获取到 {len(trending_df)} 个 Rising Queries，开始需求挖掘分析...")

            # 执行需求挖掘分析，禁用新词检测避免429错误
            original_new_word_flag = getattr(manager, 'new_word_detection_available', True)
            manager.new_word_detection_available = False
            try:
                result = manager.analyze_keywords(trending_df, args.output, enable_serp=False)

                # 显示结果
                if args.quiet:
                    print_quiet_summary(result)
                else:
                    print(f"\n🎉 需求挖掘分析完成! 共分析 {result['total_keywords']} 个 Rising Queries")
                    print(f"📊 高机会关键词: {result['market_insights']['high_opportunity_count']} 个")
                    print(f"📈 平均机会分数: {result['market_insights']['avg_opportunity_score']}")

                    # 显示新词检测摘要
                    _print_new_word_summary(result.get('new_word_summary'))
                    _print_top_new_words(result)

                    # 显示Top 5机会关键词
                    top_keywords = result['market_insights']['top_opportunities'][:5]
                    if top_keywords:
                        print("\n🏆 Top 5 机会关键词:")
                        for i, kw in enumerate(top_keywords, 1):
                            intent_desc = kw['intent']['intent_description']
                            score = kw['opportunity_score']
                            new_word_info = ""
                            if 'new_word_detection' in kw and kw['new_word_detection']['is_new_word']:
                                new_word_grade = kw['new_word_detection']['new_word_grade']
                                new_word_info = f" [新词-{new_word_grade}级]"
                            print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc}){new_word_info}")
                    
                    # 显示原始Rising Queries信息
                    print(f"\n🔥 原始 Rising Queries 数据:")
                    print(f"   • 数据来源: Google Trends Rising Queries")
                    if 'value' in trending_df.columns:
                        print(f"   • 平均热度: {trending_df['value'].mean():.1f}")
                    
                    # 保存原始Rising Queries
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    trending_output_file = os.path.join(args.output, f"rising_queries_raw_{timestamp}.csv")
                    os.makedirs(args.output, exist_ok=True)
                    trending_df.to_csv(trending_output_file, index=False, encoding='utf-8')
                    print(f"📁 原始 Rising Queries 已保存到: {trending_output_file}")
            finally:
                manager.new_word_detection_available = original_new_word_flag

        else:
            # 当无法获取Rising Queries时，直接报告失败
            print("❌ 无法获取 Rising Queries，可能的原因:")
            print("💡 建议:")
            print("   1. 检查网络连接")
            print("   2. 稍后重试")
            print("   3. 或使用 --input 参数指定关键词文件进行分析")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 获取 Rising Queries 或需求挖掘时出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    return True


def handle_all_workflow(manager, args):
    """处理完整的关键词分析工作流程"""
    if not args.all:
        return False
    
    if not args.quiet:
        print("🚀 开始完整的关键词分析工作流程...")
        print("   第一步: 搜索热门关键词 (Google Trends + TrendingKeywords.net)")
        print("   第二步: 基于热门关键词进行多平台发现")
    
    max_seed_keywords = max(1, getattr(args, 'max_seed_keywords', 10))
    max_discovered_keywords = max(10, getattr(args, 'max_discovered_keywords', 150))
    hot_result = None
    trends_collector = None

    try:
        # 第一步：获取热门关键词 - 整合多个数据源
        all_trending_keywords = []
        
        # 1.1 获取 Google Trends Rising Queries
        if not args.quiet:
            print("🔍 正在获取 Google Trends Rising Queries...")
        
        try:
            from src.collectors.trends_singleton import get_trends_collector
            trends_collector = get_trends_collector()
            rising_queries = trends_collector.fetch_rising_queries()
            
            # 处理 Google Trends 数据
            if isinstance(rising_queries, pd.DataFrame):
                trending_df = rising_queries.head(15)  # 减少到15个为TrendingKeywords留空间
                if 'query' not in trending_df.columns:
                    if 'title' in trending_df.columns:
                        trending_df = trending_df.rename(columns={'title': 'query'})
                    elif len(trending_df.columns) > 0:
                        trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
            elif rising_queries and len(rising_queries) > 0:
                if isinstance(rising_queries[0], str):
                    trending_df = pd.DataFrame([
                        {'query': query, 'source': 'Google Trends'}
                        for query in rising_queries[:15]
                    ])
                elif isinstance(rising_queries[0], dict):
                    trending_df = pd.DataFrame([
                        {
                            'query': item.get('query', item.get('keyword', str(item))),
                            'value': item.get('value', item.get('interest', 0)),
                            'source': 'Google Trends'
                        }
                        for item in rising_queries[:15]
                    ])
                else:
                    trending_df = pd.DataFrame([
                        {'query': str(query), 'source': 'Google Trends'}
                        for query in rising_queries[:15]
                    ])
            else:
                trending_df = pd.DataFrame(columns=['query', 'source'])
            
            if not trending_df.empty:
                all_trending_keywords.append(trending_df)
                if not args.quiet:
                    print(f"✅ Google Trends: 获取到 {len(trending_df)} 个关键词")
            
        except Exception as e:
            if not args.quiet:
                print(f"⚠️ Google Trends 获取失败: {e}")
        
        # 1.2 获取 TrendingKeywords.net 数据
        if not args.quiet:
            print("🔍 正在获取 TrendingKeywords.net 数据...")

        try:
            from src.collectors.trending_keywords_collector import TrendingKeywordsCollector
            
            tk_collector = TrendingKeywordsCollector()
            tk_df = tk_collector.get_trending_keywords_for_analysis(max_keywords=15)
            
            if not tk_df.empty:
                # 添加数据源标识
                tk_df['source'] = 'TrendingKeywords.net'
                all_trending_keywords.append(tk_df)
                if not args.quiet:
                    print(f"✅ TrendingKeywords.net: 获取到 {len(tk_df)} 个关键词")
            
        except Exception as e:
            if not args.quiet:
                print(f"⚠️ TrendingKeywords.net 获取失败: {e}")

        # 1.3 获取 RSS 热点数据
        if not args.quiet:
            print("🔍 正在抓取 RSS 热点...")

        try:
            rss_collector = RSSHotspotCollector()
            rss_df = rss_collector.collect(max_items=20)
            if not rss_df.empty:
                all_trending_keywords.append(rss_df)
                if not args.quiet:
                    print(f"✅ RSS 热点: 获取到 {len(rss_df)} 个热点词")
        except Exception as e:
            if not args.quiet:
                print(f"⚠️ RSS 热点抓取失败: {e}")

        # 基于现有数据源扩展相关词与组合词
        seed_pool: List[str] = []
        for df_candidate in all_trending_keywords:
            if isinstance(df_candidate, pd.DataFrame) and 'query' in df_candidate.columns:
                seed_pool.extend(df_candidate['query'].dropna().astype(str).tolist())

        if seed_pool and trends_collector:
            related_candidates = _collect_trends_related_candidates(trends_collector, seed_pool)
            if not related_candidates.empty:
                all_trending_keywords.append(related_candidates)
                if not args.quiet:
                    print(f"✅ Google Trends 关联扩展: 新增 {len(related_candidates)} 个候选关键词")

        suggestion_collector: Optional[SuggestionCollector] = None
        if seed_pool:
            combo_candidates = _generate_keyword_combinations(seed_pool, manager)
            if not combo_candidates.empty:
                all_trending_keywords.append(combo_candidates)
                if not args.quiet:
                    print(f"✅ 组合生成: 新增 {len(combo_candidates)} 个候选关键词")

            try:
                suggestion_collector = SuggestionCollector()
                suggestion_records = suggestion_collector.collect(seed_pool, per_seed_limit=4)
            except Exception as exc:
                if not args.quiet:
                    print(f"⚠️ Suggestion 收集器初始化失败: {exc}")
                suggestion_records = []

            if suggestion_records:
                suggestion_df = pd.DataFrame([
                    {
                        'query': item.term,
                        'source': f"Suggestions/{item.source}",
                        'seed': item.seed
                    }
                    for item in suggestion_records
                    if item.term
                ])
                if not suggestion_df.empty:
                    all_trending_keywords.append(suggestion_df)
                    if not args.quiet:
                        print(f"✅ 热门联想: 新增 {len(suggestion_df)} 个候选关键词")
                        if suggestion_collector is not None:
                            stats = suggestion_collector.get_last_stats()
                            print(
                                f"   • 联想摘要: 种子 {stats['seeds_processed']}/{stats['seeds_total']} | 请求 {stats['requests_sent']} | 建议 {stats['suggestions_collected']}"
                            )

        # 合并所有数据源
        if all_trending_keywords:
            trending_df = pd.concat(all_trending_keywords, ignore_index=True)
            
            # 去重，保留第一个出现的
            trending_df = trending_df.drop_duplicates(subset=['query'], keep='first')
            
            # 限制总数量
            trending_df = trending_df.head(60)
            filtered_trending = _filter_trending_keywords(trending_df)
            if not filtered_trending.empty:
                trending_df = filtered_trending
            else:
                print("[Filter] 热门关键词过滤后为空，继续使用未过滤结果")
            
            if not args.quiet:
                print(f"🎯 合并后总计: {len(trending_df)} 个关键词")
                
                # 显示数据源分布
                if 'source' in trending_df.columns:
                    source_counts = trending_df['source'].value_counts()
                    print("📊 数据源分布:")
                    for source, count in source_counts.items():
                        print(f"   • {source}: {count} 个")
        else:
            trending_df = pd.DataFrame(columns=['query'])
        
        if trending_df is not None and not trending_df.empty:
            # 确保DataFrame有正确的列名
            if 'query' not in trending_df.columns and len(trending_df.columns) > 0:
                trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
            
            # 第一步：对热门关键词进行需求挖掘
            cleaned_terms = None
            try:
                from src.pipeline.cleaning.cleaner import clean_terms, CleaningConfig
                if 'query' in trending_df.columns:
                    cleaned_terms = clean_terms(
                        trending_df['query'].astype(str).tolist(),
                        CleaningConfig()
                    )
            except Exception as exc:
                if not args.quiet:
                    print(f"⚠️ 清洗热门关键词时出现异常: {exc}")
                cleaned_terms = trending_df['query'].dropna().astype(str).tolist() if 'query' in trending_df.columns else []
            if cleaned_terms is not None:
                if not cleaned_terms:
                    if not args.quiet:
                        print("⚠️ 清洗后的热门关键词为空，已终止完整流程。")
                    print("💡 请稍后重试，或使用 --input 指定本地关键词文件。")
                    return True
                trending_df = pd.DataFrame({'query': cleaned_terms})

            if not args.quiet:
                print(f"🔍 第一步: 对 {len(trending_df)} 个热门关键词进行需求挖掘...")

            # 执行需求挖掘分析
            original_new_word_flag = getattr(manager, 'new_word_detection_available', True)
            hot_result = None
            try:
                manager.new_word_detection_available = False
                hot_result = manager.analyze_keywords(trending_df, args.output, enable_serp=False)
            finally:
                manager.new_word_detection_available = original_new_word_flag

            if not hot_result:
                print("⚠️ 热门关键词分析未返回结果，流程终止。")
                return True

            if not args.quiet:
                print(f"✅ 第一步完成! 分析了 {hot_result['total_keywords']} 个热门关键词")
                print(f"📊 发现 {hot_result['market_insights']['high_opportunity_count']} 个高机会关键词")
                _print_new_word_summary(hot_result.get('new_word_summary'))
                _print_top_new_words(hot_result)
                print("\n🌐 第二步: 基于热门关键词进行多平台关键词发现...")
                
                # 选取机会分最高的关键词作为种子
                seed_keywords: List[str] = []
                if isinstance(hot_result, dict) and hot_result.get('keywords'):
                    sorted_keywords = sorted(
                        (kw for kw in hot_result['keywords'] if kw.get('keyword')),
                        key=lambda kw: kw.get('opportunity_score', 0),
                        reverse=True
                    )
                    seed_keywords = [kw['keyword'] for kw in sorted_keywords[:max_seed_keywords]]

                if len(seed_keywords) < max_seed_keywords and 'query' in trending_df.columns:
                    fallback_candidates: List[str] = [
                        kw for kw in trending_df['query'].tolist()
                        if kw and kw not in seed_keywords
                    ]
                    seed_keywords.extend(fallback_candidates[:max_seed_keywords - len(seed_keywords)])

                seed_keywords = [kw for kw in seed_keywords if kw][:max_seed_keywords]
                if not seed_keywords:
                    if not args.quiet:
                        print("⚠️ 未找到有效的种子关键词，跳过多平台关键词发现。")
                        print("💡 建议检查第一步结果，或使用 --input 指定本地关键词文件。")
                    return True

                discovery_tool = MultiPlatformKeywordDiscovery()
                seed_profile = getattr(args, 'seed_profile', None)
                seed_limit_arg = getattr(args, 'seed_limit', None)
                if isinstance(seed_limit_arg, int) and seed_limit_arg <= 0:
                    seed_limit_arg = None
                min_seed_terms = getattr(args, 'min_seed_terms', None)
                if isinstance(min_seed_terms, int) and min_seed_terms <= 0:
                    min_seed_terms = None
                effective_limit = seed_limit_arg or max_seed_keywords
                prepared_seeds = discovery_tool.prepare_search_terms(
                    seeds=seed_keywords,
                    profile=seed_profile,
                    limit=effective_limit,
                    min_terms=min_seed_terms
                )

                if not prepared_seeds:
                    if not args.quiet:
                        print("⚠️ 无有效种子关键词可用于多平台发现，流程终止。")
                    return True

                if not args.quiet:
                    extra_seed_count = len([kw for kw in prepared_seeds if kw not in seed_keywords])
                    if extra_seed_count > 0:
                        print(f"ℹ️ 已追加 {extra_seed_count} 个配置种子关键词以满足发现需求")
                    print(f"🔍 正在发现与 {len(prepared_seeds)} 个关键词相关的关键词...")

                df = discovery_tool.discover_all_platforms(prepared_seeds)
                
                unique_keywords = []
                prioritized_df = None
                if not df.empty and 'keyword' in df.columns:
                    keyword_series = df['keyword'].dropna().astype(str)
                    if 'score' in df.columns:
                        prioritized_df = df[['keyword', 'score']].dropna(subset=['keyword'])
                        prioritized_df = prioritized_df.sort_values('score', ascending=False)
                        prioritized_df = prioritized_df.drop_duplicates(subset=['keyword'], keep='first')
                    else:
                        counts = keyword_series.value_counts().reset_index()
                        counts.columns = ['keyword', 'score']
                        prioritized_df = counts
                    prioritized_df['score'] = prioritized_df['score'].fillna(0)
                    prioritized_df['keyword'] = prioritized_df['keyword'].astype(str)
                    unique_keywords = prioritized_df['keyword'].head(max_discovered_keywords).tolist()

                if unique_keywords:
                    if not args.quiet and prioritized_df is not None and len(prioritized_df) > len(unique_keywords):
                        print(f"⚖️ 已按得分筛选前 {len(unique_keywords)} 个关键词用于最终分析 (上限 {max_discovered_keywords})")
                    # 创建发现关键词的CSV文件
                    discovered_df = pd.DataFrame([
                        {'keyword': kw} for kw in unique_keywords
                    ])
                    
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    discovered_file = os.path.join(args.output, f"discovered_keywords_{timestamp}.csv")
                    os.makedirs(args.output, exist_ok=True)
                    discovered_df.to_csv(discovered_file, index=False, encoding='utf-8')
                    
                    if not args.quiet:
                        print(f"🎯 发现了 {len(unique_keywords)} 个相关关键词")
                        print(f"📁 发现的关键词已保存到: {discovered_file}")
                    
                    # 对发现的关键词进行需求挖掘分析
                    if not args.quiet:
                        print(f"\n🔍 第三步: 对发现的关键词进行需求挖掘分析...")
                    
                    discovery_result = manager.analyze_keywords(discovered_file, args.output, enable_serp=False)
                    
                    # 显示最终结果
                    if args.quiet:
                        print_quiet_summary(discovery_result)
                    else:
                        print(f"\n🎉 完整工作流程完成!")
                        print(f"📊 热门关键词分析: {hot_result['total_keywords']} 个关键词")
                        print(f"🌐 多平台发现: {len(unique_keywords)} 个相关关键词")
                        print(f"🎯 最终分析: {discovery_result['total_keywords']} 个关键词")
                        print(f"🏆 总计高机会关键词: {discovery_result['market_insights']['high_opportunity_count']} 个")
                        print(f"📈 平均机会分数: {discovery_result['market_insights']['avg_opportunity_score']}")
                        
                        # 显示Top 5机会关键词
                        top_keywords = discovery_result['market_insights']['top_opportunities'][:5]
                        if top_keywords:
                            print("\n🏆 Top 5 最终机会关键词:")
                            for i, kw in enumerate(top_keywords, 1):
                                intent_desc = kw['intent']['intent_description']
                                score = kw['opportunity_score']
                                print(f"   {i}. {kw['keyword']} (分数: {score}, 意图: {intent_desc})")
                
                else:
                    if not args.quiet:
                        print("⚠️ 未发现相关关键词，仅显示热门关键词分析结果")
                    
                    if args.quiet:
                        print_quiet_summary(hot_result)
                    else:
                        print(f"\n🎉 热门关键词分析完成! 共分析 {hot_result['total_keywords']} 个关键词")
                        print(f"📊 高机会关键词: {hot_result['market_insights']['high_opportunity_count']} 个")
                        print(f"📈 平均机会分数: {hot_result['market_insights']['avg_opportunity_score']}")
        
        else:
            if not args.quiet:
                print("❌ 无法获取热门关键词，工作流程终止")
                print("💡 建议:")
                print("   1. 检查网络连接")
                print("   2. 稍后重试")
                print("   3. 或使用其他参数进行分析")
            return True
    
    except Exception as e:
        print(f"❌ 完整工作流程执行时出错: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
    
    return True


def handle_demand_validation(manager, args):
    """
    处理需求验证流程
    
    Args:
        manager: IntegratedDemandMiningManager实例
        args: 命令行参数
    """
    print("🔍 开始需求验证流程...")
    print("📋 第一步：获取高机会关键词")
    
    try:
        from src.collectors.trends_singleton import get_trends_collector
        trends_collector = get_trends_collector()
        rising_queries = trends_collector.fetch_rising_queries()
        
        if isinstance(rising_queries, pd.DataFrame):
            trending_df = rising_queries.head(20)
            if 'query' not in trending_df.columns:
                if 'title' in trending_df.columns:
                    trending_df = trending_df.rename(columns={'title': 'query'})
                elif len(trending_df.columns) > 0:
                    trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})
        elif rising_queries and len(rising_queries) > 0:
            if isinstance(rising_queries[0], str):
                trending_df = pd.DataFrame([{'query': query} for query in rising_queries[:20]])
            elif isinstance(rising_queries[0], dict):
                trending_df = pd.DataFrame([{
                    'query': item.get('query', item.get('keyword', str(item))),
                    'value': item.get('value', item.get('interest', 0))
                } for item in rising_queries[:20]])
            else:
                trending_df = pd.DataFrame([{'query': str(query)} for query in rising_queries[:20]])
        else:
            trending_df = pd.DataFrame(columns=['query'])

        if trending_df is not None and not trending_df.empty:
            if 'query' not in trending_df.columns and len(trending_df.columns) > 0:
                trending_df = trending_df.rename(columns={trending_df.columns[0]: 'query'})

            try:
                from src.pipeline.cleaning.cleaner import clean_terms, CleaningConfig
                cleaned = clean_terms(
                    trending_df['query'].astype(str).tolist(),
                    CleaningConfig()
                )
                trending_df = pd.DataFrame({'query': cleaned})
            except Exception:
                trending_df = pd.DataFrame({'query': trending_df['query'].astype(str).tolist()})

            original_new_word_flag = getattr(manager, 'new_word_detection_available', True)
            keywords_result = None
            try:
                print(f"🔍 获取到 {len(trending_df)} 个关键词，开始机会分析...")
                manager.new_word_detection_available = False
                keywords_result = manager.analyze_keywords(trending_df, args.output, enable_serp=False)
            finally:
                manager.new_word_detection_available = original_new_word_flag

            if not keywords_result:
                print("⚠️ 关键词分析未返回结果，终止需求验证流程。")
                return True

            print(f"✅ 第一步完成! 分析了 {keywords_result['total_keywords']} 个关键词")

            # 第二步：多平台需求验证
            print("\n📋 第二步：多平台需求验证")

            try:
                # 确保能够导入模块
                analyzer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src', 'demand_mining', 'analyzers')
                if analyzer_path not in sys.path:
                    sys.path.insert(0, analyzer_path)

                from src.demand_mining.analyzers.multi_platform_demand_analyzer import MultiPlatformDemandAnalyzer

                # 创建多平台分析器
                demand_analyzer = MultiPlatformDemandAnalyzer()

                # 执行多平台需求分析
                import asyncio
                demand_results = asyncio.run(demand_analyzer.analyze_high_opportunity_keywords(
                    keywords_result.get('keywords', []),
                    min_opportunity_score=60.0,  # 降低阈值以获取更多关键词
                    max_keywords=3  # 限制分析数量避免请求过多
                ))

                # 保存需求验证结果
                demand_output_file = demand_analyzer.save_results(demand_results)

                print(f"✅ 第二步完成! 需求验证分析完成")
                print(f"📊 分析了 {demand_results.get('analyzed_keywords', 0)} 个高机会关键词")

                # 显示需求验证摘要
                summary = demand_results.get('summary', {})
                if summary:
                    print(f"\n🎯 需求验证摘要:")
                    print(f"   • 总搜索结果: {summary.get('total_search_results', 0)}")
                    print(f"   • 发现痛点: {summary.get('total_pain_points_found', 0)} 个")
                    print(f"   • 功能需求: {summary.get('total_feature_requests_found', 0)} 个")

                    high_demand = summary.get('high_demand_keywords', [])
                    if high_demand:
                        print(f"   • 高需求关键词: {', '.join(high_demand)}")

                    top_opportunities = summary.get('top_opportunities', [])[:3]
                    if top_opportunities:
                        print(f"\n🏆 Top 3 验证结果:")
                        for i, opp in enumerate(top_opportunities, 1):
                            print(f"   {i}. {opp['keyword']} - {opp['demand_level']} ({opp['pain_points_count']} 个痛点)")

                print(f"\n📁 需求验证结果已保存到: {demand_output_file}")

            except ImportError:
                print("⚠️ 多平台需求分析器未找到，请确保相关模块已安装")
            except Exception as e:
                print(f"❌ 需求验证失败: {e}")
                if args.verbose:
                    import traceback
                    traceback.print_exc()
                
        else:
            print("❌ 无法获取关键词进行需求验证")
            
    except Exception as e:
        print(f"❌ 需求验证流程失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

def refresh_dashboard_data(output_dir: str, history_size: int = 20) -> None:
    """Refresh aggregated dashboard data after primary workflows finish."""
    try:
        from src.utils.dashboard_data_builder import generate_dashboard_payload
        from src.utils.file_utils import ensure_directory_exists

        target_dir = Path(output_dir or get_reports_dir()).resolve()
        ensure_directory_exists(str(target_dir))

        payload = generate_dashboard_payload(target_dir, history_size=history_size)
        dashboard_path = target_dir / "dashboard_data.json"
        with dashboard_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        if payload.get("last_updated"):
            print(f"[Dashboard] 数据已刷新: {dashboard_path}")
        else:
            print("[Dashboard] 仪表盘已更新，但尚未检测到有效的分析结果。")
    except Exception as exc:
        print(f"[Dashboard] 刷新仪表盘数据失败: {exc}")
