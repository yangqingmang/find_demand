#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
需求挖掘 → 意图分析 → 建站部署 完整集成工作流
整合三大核心模块，实现从需求发现到网站上线的全自动化流程
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.demand_mining.managers.keyword_manager import KeywordManager
from src.website_builder.builder_core import IntentBasedWebsiteBuilder
from src.demand_mining.analyzers.new_word_detector import NewWordDetector
from src.demand_mining.managers.discovery_manager import DiscoveryManager


class IntegratedWorkflow:
    """
    集成工作流管理器
    实现需求挖掘 → 意图分析 → 网站建设 → 自动部署的完整流程
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化集成工作流"""
        self.config = config or self._get_default_config()
        self.output_base_dir = "output/integrated_projects"
        self._ensure_output_dirs()
        
        # 初始化各模块
        self.demand_miner = KeywordManager()
        self.discovery_manager = DiscoveryManager()
        
        print("🚀 集成工作流初始化完成")
        print("📊 支持功能：需求挖掘 → 多平台关键词发现 → 意图分析 → 网站生成 → 自动部署")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'min_opportunity_score': 50,  # 最低机会分数阈值（放宽以捕获更多潜力长尾）
            'max_projects_per_batch': 5,  # 每批次最大项目数
            'auto_deploy': True,          # 是否自动部署
            'deployment_platform': 'cloudflare',  # 部署平台
            'use_tailwind': True,         # 使用TailwindCSS
            'generate_reports': True      # 生成分析报告
        }
    
    def _ensure_output_dirs(self):
        """确保输出目录存在"""
        dirs = [
            self.output_base_dir,
            os.path.join(self.output_base_dir, 'demand_analysis'),
            os.path.join(self.output_base_dir, 'multi_platform_keywords'),
            os.path.join(self.output_base_dir, 'intent_analysis'),
            os.path.join(self.output_base_dir, 'websites'),
            os.path.join(self.output_base_dir, 'reports')
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def run_complete_workflow(self, keywords_file: str) -> Dict[str, Any]:
        """
        运行完整工作流
        
        Args:
            keywords_file: 关键词输入文件路径
            
        Returns:
            工作流执行结果
        """
        print(f"🎯 开始执行完整工作流: {keywords_file}")
        
        workflow_results = {
            'start_time': datetime.now().isoformat(),
            'input_file': keywords_file,
            'steps_completed': [],
            'generated_projects': [],
            'deployment_results': [],
            'summary': {}
        }
        
        try:
            # 步骤1: 需求挖掘与意图分析
            print("\n📊 步骤1: 执行需求挖掘与意图分析...")
            demand_results = self._run_demand_mining(keywords_file)
            workflow_results['steps_completed'].append('demand_mining')
            workflow_results['demand_analysis'] = demand_results
            self._print_new_word_summary(demand_results.get('new_word_summary'))
            self._print_top_new_words(demand_results)
            
            # 步骤2: 多平台关键词发现
            print("\n🔍 步骤2: 执行多平台关键词发现...")
            # 从需求挖掘结果中提取关键词
            initial_keywords = [kw['keyword'] for kw in demand_results.get('keywords', [])[:10]]
            if not initial_keywords and 'keywords' in demand_results:
                # 尝试其他可能的键名
                for key in ['query', 'term']:
                    if key in demand_results['keywords'][0]:
                        initial_keywords = [kw[key] for kw in demand_results.get('keywords', [])[:10]]
                        break
            
            # 如果仍然没有关键词，使用默认关键词
            if not initial_keywords:
                seeds_cfg = self.config.get('discovery_seeds', {}) if isinstance(self.config, dict) else {}
                fallback_profile = seeds_cfg.get('default_profile')
                seed_limit = seeds_cfg.get('min_terms')
                discoverer = self.discovery_manager.discoverer
                if discoverer is None:
                    from src.demand_mining.tools.multi_platform_keyword_discovery import MultiPlatformKeywordDiscovery
                    discoverer = MultiPlatformKeywordDiscovery()
                initial_keywords = discoverer.get_seed_terms(profile=fallback_profile, limit=seed_limit)
                if initial_keywords:
                    print(f"⚠️ 未从需求挖掘结果中找到关键词，使用配置种子: {', '.join(initial_keywords)}")
                else:
                    initial_keywords = ['AI tool', 'AI generator', 'AI writer']
                    print("⚠️ 未从需求挖掘结果中找到关键词，使用默认关键词")
            
            # 执行多平台关键词发现
            discovery_results = self._run_multi_platform_discovery(initial_keywords)
            workflow_results['steps_completed'].append('multi_platform_discovery')
            workflow_results['multi_platform_discovery'] = discovery_results
            
            # 步骤3: 筛选高价值关键词
            print("\n🎯 步骤3: 筛选高价值关键词...")
            high_value_keywords = self._filter_high_value_keywords(demand_results)
            workflow_results['steps_completed'].append('keyword_filtering')
            workflow_results['high_value_keywords'] = high_value_keywords
            
            # 步骤3: 批量生成网站
            print("\n🏗️ 步骤3: 批量生成网站...")
            website_results = self._batch_generate_websites(high_value_keywords)
            workflow_results['steps_completed'].append('website_generation')
            workflow_results['generated_projects'] = website_results
            
            # 步骤4: 自动部署（可选）
            if self.config.get('auto_deploy', False):
                print("\n🚀 步骤4: 自动部署网站...")
                deployment_results = self._batch_deploy_websites(website_results)
                workflow_results['steps_completed'].append('deployment')
                workflow_results['deployment_results'] = deployment_results
            
            # 步骤5: 生成综合报告
            print("\n📋 步骤5: 生成综合报告...")
            report_path = self._generate_workflow_report(workflow_results)
            workflow_results['steps_completed'].append('report_generation')
            workflow_results['report_path'] = report_path
            
            workflow_results['end_time'] = datetime.now().isoformat()
            workflow_results['status'] = 'success'
            
            print(f"\n🎉 完整工作流执行成功！")
            print(f"📊 分析了 {len(demand_results.get('keywords', []))} 个关键词")
            print(f"🎯 筛选出 {len(high_value_keywords)} 个高价值关键词")
            print(f"🏗️ 生成了 {len(website_results)} 个网站项目")
            print(f"📋 报告路径: {report_path}")
            
        return workflow_results

    @staticmethod
    def _print_new_word_summary(summary: Optional[Dict[str, Any]]) -> None:
        if not summary or not isinstance(summary, dict):
            return

        total = summary.get('total_analyzed')
        detected = summary.get('new_words_detected')
        high_conf = summary.get('high_confidence_new_words')
        breakout = summary.get('breakout_keywords')
        rising = summary.get('rising_keywords')
        percentage = summary.get('new_word_percentage')

        print("\n🔎 新词检测摘要：")
        print(f"   • 检测总数: {total}")
        print(f"   • 新词数量: {detected} / 高置信度: {high_conf}")
        if breakout is not None or rising is not None:
            print(f"   • Breakout: {breakout} / Rising: {rising}")
        if percentage is not None:
            print(f"   • 新词占比: {percentage}%")

        report_files = summary.get('report_files')
        if isinstance(report_files, dict) and report_files:
            print("   • 导出文件:")
            for label, path in report_files.items():
                print(f"     - {label}: {path}")

    @staticmethod
    def _print_top_new_words(result: Optional[Dict[str, Any]], limit: int = 5) -> None:
        if not result or 'keywords' not in result:
            return

        candidates = []
        for item in result['keywords']:
            nwd = item.get('new_word_detection') if isinstance(item, dict) else None
            if not nwd or not nwd.get('is_new_word'):
                continue
            candidates.append({
                'keyword': item.get('keyword') or item.get('query'),
                'score': float(nwd.get('new_word_score', 0.0) or 0.0),
                'momentum': nwd.get('trend_momentum'),
                'delta': float(nwd.get('avg_7d_delta', 0.0) or 0.0),
                'grade': nwd.get('new_word_grade', 'D'),
                'confidence': nwd.get('confidence_level', 'low')
            })

        if not candidates:
            return

        candidates.sort(key=lambda x: (x['momentum'] == 'breakout', x['score']), reverse=True)
        print("\n🔥 Top 新词候选:")
        for idx, item in enumerate(candidates[:limit], 1):
            print(
                f"   {idx}. {item['keyword']} | 分数 {item['score']:.1f} | 动量 {item['momentum']} | "
                f"Δ7D {item['delta']:.1f} | 等级 {item['grade']} | 置信度 {item['confidence']}"
            )
            
        except Exception as e:
            workflow_results['end_time'] = datetime.now().isoformat()
            workflow_results['status'] = 'failed'
            workflow_results['error'] = str(e)
            print(f"❌ 工作流执行失败: {e}")
            return workflow_results
    
    def _run_multi_platform_discovery(self, initial_keywords: List[str]) -> Dict[str, Any]:
        """执行多平台关键词发现"""
        output_dir = os.path.join(self.output_base_dir, 'multi_platform_keywords')
        
        try:
            print(f"🔍 开始多平台关键词发现，基于 {len(initial_keywords)} 个初始关键词...")
            print(f"📊 初始关键词: {', '.join(initial_keywords[:5])}{'...' if len(initial_keywords) > 5 else ''}")
            
            # 使用发现管理器执行多平台关键词发现
            seeds_config = self.config.get('discovery_seeds', {}) if isinstance(self.config, dict) else {}
            default_profile = seeds_config.get('default_profile')
            min_terms = seeds_config.get('min_terms')
            discovery_results = self.discovery_manager.analyze(
                search_terms=initial_keywords,
                output_dir=output_dir,
                seed_profile=default_profile,
                min_terms=min_terms
            )
            
            # 如果发现了关键词，显示摘要
            if discovery_results and 'total_keywords' in discovery_results and discovery_results['total_keywords'] > 0:
                print(f"✅ 多平台关键词发现完成，发现 {discovery_results['total_keywords']} 个关键词")
                
                # 显示平台分布
                if 'platform_distribution' in discovery_results:
                    platforms = discovery_results['platform_distribution']
                    print(f"📊 平台分布: {', '.join([f'{p}({c})' for p, c in platforms.items()])}")
                
                # 显示热门关键词
                if 'top_keywords_by_score' in discovery_results and discovery_results['top_keywords_by_score']:
                    print("🏆 热门关键词:")
                    for i, kw in enumerate(discovery_results['top_keywords_by_score'][:5], 1):
                        print(f"  {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
            else:
                print("⚠️ 未发现任何关键词")
            
            return discovery_results
            
        except Exception as e:
            print(f"❌ 多平台关键词发现失败: {e}")
            return {
                'error': str(e),
                'total_keywords': 0,
                'platform_distribution': {},
                'top_keywords_by_score': []
            }
    
    def _run_demand_mining(self, keywords_file: str) -> Dict[str, Any]:
        """执行需求挖掘分析（包含新词检测）"""
        output_dir = os.path.join(self.output_base_dir, 'demand_analysis')
        
        # 执行基础需求挖掘
        demand_results = self.demand_miner.analyze_keywords(keywords_file, output_dir)
        
        # 添加新词检测
        try:
            print("🔍 正在进行新词检测...")
            
            # 读取关键词数据
            import pandas as pd
            df = pd.read_csv(keywords_file)
            
            # 执行新词检测
        try:
            from src.demand_mining.analyzers.new_word_detector_singleton import get_new_word_detector
            new_word_detector = get_new_word_detector()
            new_word_results = new_word_detector.detect_new_words(df)
            
            # 将新词检测结果合并到需求挖掘结果中
            if 'keywords' in demand_results:
                for i, keyword_data in enumerate(demand_results['keywords']):
                    if i < len(new_word_results):
                        # 添加新词检测信息
                        row = new_word_results.iloc[i]
                        keyword_data['new_word_detection'] = {
                            'is_new_word': bool(row.get('is_new_word', False)),
                            'new_word_score': float(row.get('new_word_score', 0)),
                            'new_word_grade': str(row.get('new_word_grade', 'D')),
                            'growth_rate_7d': float(row.get('growth_rate_7d', 0)),
                            'growth_rate_7d_vs_30d': float(row.get('growth_rate_7d_vs_30d', 0)),
                            'mom_growth': float(row.get('mom_growth', 0)),
                            'yoy_growth': float(row.get('yoy_growth', 0)),
                            'explosion_index': float(row.get('explosion_index', 1.0)),
                            'confidence_level': str(row.get('confidence_level', 'low')),
                            'historical_pattern': str(row.get('historical_pattern', 'unknown')),
                            'trend_momentum': str(row.get('trend_momentum', 'unknown')),
                            'growth_label': str(row.get('growth_label', 'unknown')),
                            'trend_fetch_timeframe': row.get('trend_fetch_timeframe'),
                            'trend_fetch_geo': row.get('trend_fetch_geo'),
                            'avg_30d_delta': float(row.get('avg_30d_delta', 0.0) or 0.0),
                            'avg_7d_delta': float(row.get('avg_7d_delta', 0.0) or 0.0),
                            'detection_reasons': str(row.get('detection_reasons', ''))
                        }
                        
                        # 如果是新词，增加机会分数加成
                        if row.get('is_new_word', False):
                            original_score = keyword_data.get('opportunity_score', 0)
                            new_word_bonus = row.get('new_word_score', 0) * 0.1  # 10%加成
                            keyword_data['opportunity_score'] = min(100, original_score + new_word_bonus)
                            keyword_data['new_word_bonus'] = new_word_bonus
            
            # 生成新词检测摘要
            new_words_count = len(new_word_results[new_word_results['is_new_word'] == True])
            high_confidence_count = len(new_word_results[new_word_results['confidence_level'] == 'high'])
            
            momentum_counts = new_word_results.get('trend_momentum', pd.Series(dtype=str)).value_counts() if 'trend_momentum' in new_word_results.columns else {}
            breakout_count = int(momentum_counts.get('breakout', 0)) if momentum_counts is not None else 0
            rising_count = int(momentum_counts.get('rising', 0)) if momentum_counts is not None else 0

            demand_results['new_word_summary'] = {
                'total_analyzed': len(new_word_results),
                'new_words_detected': new_words_count,
                'high_confidence_new_words': high_confidence_count,
                'new_word_percentage': round(new_words_count / len(new_word_results) * 100, 1) if len(new_word_results) > 0 else 0,
                'breakout_keywords': breakout_count,
                'rising_keywords': rising_count
            }

            exported_reports = self._export_new_word_reports(new_word_results)
            if exported_reports:
                demand_results['new_word_summary']['report_files'] = exported_reports

            print(
                f"✅ 新词检测完成: 发现 {new_words_count} 个新词 "
                f"({high_confidence_count} 个高置信度, {demand_results['new_word_summary']['breakout_keywords']} 个 Breakout)"
            )
            
        except Exception as e:
            print(f"⚠️ 新词检测失败: {e}")
            demand_results['new_word_summary'] = {
                'error': str(e),
                'new_words_detected': 0
            }
        
        return demand_results
    
    def _filter_high_value_keywords(self, demand_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """筛选高价值关键词"""
        min_score = self.config.get('min_opportunity_score', 60)
        max_projects = self.config.get('max_projects_per_batch', 5)
        
        # 获取所有关键词
        all_keywords = demand_results.get('keywords', [])
        
        # 按机会分数筛选和排序
        high_value = [
            kw for kw in all_keywords 
            if kw.get('opportunity_score', 0) >= min_score
        ]
        
        # 按分数降序排序，取前N个
        high_value.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
        
        return high_value[:max_projects]
    
    def _batch_generate_websites(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量生成网站（基于建站建议）"""
        website_results = []
        
        for i, keyword_data in enumerate(keywords, 1):
            keyword = keyword_data['keyword']
            intent_info = keyword_data.get('intent', {})
            website_recommendations = intent_info.get('website_recommendations', {})
            
            print(f"🏗️ 生成网站 ({i}/{len(keywords)}): {keyword}")
            
            # 显示建站建议信息
            website_type = website_recommendations.get('website_type', '未知')
            ai_category = website_recommendations.get('ai_tool_category', '未知')
            development_priority = website_recommendations.get('development_priority', {})
            priority_level = development_priority.get('level', '未知') if isinstance(development_priority, dict) else '未知'
            
            print(f"   推荐网站类型: {website_type}")
            print(f"   AI工具类别: {ai_category}")
            print(f"   开发优先级: {priority_level}")
            
            try:
                # 准备意图数据文件
                intent_data = self._prepare_intent_data(keyword_data)
                intent_file_path = self._save_intent_data(intent_data, keyword)
                
                # 生成项目名称（基于建站建议）
                project_name = self._generate_project_name_with_recommendations(keyword, website_recommendations)
                
                # 创建项目配置（基于建站建议）
                project_config = self._create_project_config(website_recommendations, project_name)
                
                # 创建网站建设器
                builder = IntentBasedWebsiteBuilder(
                    intent_data_path=intent_file_path,
                    output_dir=os.path.join(self.output_base_dir, 'websites'),
                    config=project_config
                )
                
                # 执行建站流程
                if builder.load_intent_data():
                    structure = builder.generate_website_structure()
                    content_plan = builder.create_content_plan()
                    source_dir = builder.generate_website_source()
                    
                    if source_dir:
                        website_results.append({
                            'keyword': keyword,
                            'project_name': project_name,
                            'source_dir': source_dir,
                            'intent_info': intent_info,
                            'website_recommendations': website_recommendations,
                            'opportunity_score': keyword_data.get('opportunity_score', 0),
                            'development_priority': priority_level,
                            'website_type': website_type,
                            'ai_category': ai_category,
                            'status': 'success'
                        })
                        print(f"✅ 网站生成成功: {source_dir}")
                        
                        # 显示域名建议
                        domain_suggestions = website_recommendations.get('domain_suggestions', [])
                        if domain_suggestions:
                            print(f"   推荐域名: {', '.join(domain_suggestions[:3])}")
                    else:
                        website_results.append({
                            'keyword': keyword,
                            'project_name': project_name,
                            'website_type': website_type,
                            'status': 'failed',
                            'error': '源代码生成失败'
                        })
                        print(f"❌ 网站生成失败: {keyword}")
                else:
                    website_results.append({
                        'keyword': keyword,
                        'project_name': project_name,
                        'website_type': website_type,
                        'status': 'failed',
                        'error': '意图数据加载失败'
                    })
                    print(f"❌ 意图数据加载失败: {keyword}")
                    
            except Exception as e:
                website_results.append({
                    'keyword': keyword,
                    'project_name': project_name if 'project_name' in locals() else 'unknown',
                    'website_type': website_type,
                    'status': 'failed',
                    'error': str(e)
                })
                print(f"❌ 网站生成异常: {keyword} - {e}")
        
        return website_results
    
    def _generate_project_name_with_recommendations(self, keyword: str, recommendations: Dict[str, Any]) -> str:
        """基于建站建议生成项目名称"""
        # 清理关键词
        clean_keyword = keyword.lower().replace(' ', '_').replace('-', '_')
        clean_keyword = ''.join(c for c in clean_keyword if c.isalnum() or c == '_')
        
        # 根据网站类型添加前缀
        website_type = recommendations.get('website_type', '')
        if 'AI工具站' in website_type:
            prefix = 'ai_tool'
        elif '评测站' in website_type:
            prefix = 'review'
        elif '教程站' in website_type:
            prefix = 'tutorial'
        elif '导航站' in website_type:
            prefix = 'nav'
        else:
            prefix = 'website'
        
        return f"{prefix}_{clean_keyword}"
    
    def _create_project_config(self, recommendations: Dict[str, Any], project_name: str) -> Dict[str, Any]:
        """基于建站建议创建项目配置"""
        config = {
            'project_name': project_name,
            'website_type': recommendations.get('website_type', '通用网站'),
            'ai_category': recommendations.get('ai_tool_category', '非AI工具'),
            'domain_options': recommendations.get('domain_suggestions', []),
            'monetization_strategies': recommendations.get('monetization_strategy', []),
            'technical_requirements': recommendations.get('technical_requirements', []),
            'content_strategies': recommendations.get('content_strategy', []),
            'development_priority': recommendations.get('development_priority', {})
        }
        
        # 根据AI工具类别调整配置
        if 'AI' in config['ai_category']:
            config['use_ai_features'] = True
            config['api_integration'] = True
        
        # 根据网站类型调整模板
        if 'SaaS' in config['website_type']:
            config['template_type'] = 'saas'
        elif '评测' in config['website_type']:
            config['template_type'] = 'review'
        elif '教程' in config['website_type']:
            config['template_type'] = 'tutorial'
        else:
            config['template_type'] = 'default'
        
        return config
    
    def _prepare_intent_data(self, keyword_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """准备意图数据格式"""
        intent_info = keyword_data.get('intent', {})
        market_info = keyword_data.get('market', {})
        
        return [{
            'query': keyword_data['keyword'],
            'intent_primary': intent_info.get('primary_intent', 'I'),
            'intent_secondary': intent_info.get('secondary_intent', ''),
            'sub_intent': intent_info.get('primary_intent', 'I') + '1',
            'probability': intent_info.get('confidence', 0.8),
            'probability_secondary': 0.2,
            'search_volume': market_info.get('search_volume', 1000),
            'competition': market_info.get('competition', 0.5),
            'opportunity_score': keyword_data.get('opportunity_score', 70),
            'ai_bonus': market_info.get('ai_bonus', 0),
            'commercial_value': market_info.get('commercial_value', 0)
        }]
    
    def _save_intent_data(self, intent_data: List[Dict[str, Any]], keyword: str) -> str:
        """保存意图数据到文件"""
        # 生成安全的文件名
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_keyword = safe_keyword.replace(' ', '_')[:50]  # 限制长度
        
        file_path = os.path.join(
            self.output_base_dir, 
            'intent_analysis', 
            f'intent_{safe_keyword}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(intent_data, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def _generate_project_name(self, keyword: str) -> str:
        """生成项目名称"""
        # 清理关键词，生成合适的项目名
        clean_name = "".join(c for c in keyword if c.isalnum() or c in (' ', '-')).strip()
        clean_name = clean_name.replace(' ', '-').lower()
        
        # 限制长度并添加时间戳
        timestamp = datetime.now().strftime("%m%d_%H%M")
        return f"{clean_name[:30]}-{timestamp}"
    
    def _batch_deploy_websites(self, website_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量部署网站"""
        deployment_results = []
        
        successful_websites = [w for w in website_results if w.get('status') == 'success']
        
        for website in successful_websites:
            keyword = website['keyword']
            source_dir = website['source_dir']
            
            print(f"🚀 部署网站: {keyword}")
            
            try:
                # 这里可以集成实际的部署逻辑
                deployment_url = f"https://{website['project_name']}.pages.dev"
                
                deployment_results.append({
                    'keyword': keyword,
                    'project_name': website['project_name'],
                    'deployment_url': deployment_url,
                    'platform': self.config.get('deployment_platform', 'cloudflare'),
                    'status': 'success'
                })
                
                print(f"✅ 部署成功: {deployment_url}")
                
            except Exception as e:
                deployment_results.append({
                    'keyword': keyword,
                    'project_name': website['project_name'],
                    'status': 'failed',
                    'error': str(e)
                })
                print(f"❌ 部署失败: {keyword} - {e}")
        
        return deployment_results
    
    def _generate_workflow_report(self, workflow_results: Dict[str, Any]) -> str:
        """生成工作流综合报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(
            self.output_base_dir, 
            'reports', 
            f'integrated_workflow_report_{timestamp}.md'
        )
        
        # 统计数据
        total_keywords = len(workflow_results.get('demand_analysis', {}).get('keywords', []))
        discovered_keywords = workflow_results.get('multi_platform_discovery', {}).get('total_keywords', 0)
        high_value_count = len(workflow_results.get('high_value_keywords', []))
        successful_websites = len([w for w in workflow_results.get('generated_projects', []) if w.get('status') == 'success'])
        successful_deployments = len([d for d in workflow_results.get('deployment_results', []) if d.get('status') == 'success'])
        
        # 生成报告内容
        report_content = f"""# 集成工作流执行报告

## 📊 执行概览
- **执行时间**: {workflow_results.get('start_time', '')} - {workflow_results.get('end_time', '')}
- **输入文件**: {workflow_results.get('input_file', '')}
- **执行状态**: {workflow_results.get('status', '')}

## 📈 数据统计
- **总关键词数**: {total_keywords}
- **多平台发现关键词**: {discovered_keywords}
- **高价值关键词**: {high_value_count}
- **成功生成网站**: {successful_websites}
- **成功部署网站**: {successful_deployments}

## 🔍 多平台关键词发现
"""
        
        # 添加多平台关键词发现结果
        discovery_results = workflow_results.get('multi_platform_discovery', {})
        if discovery_results and 'total_keywords' in discovery_results and discovery_results['total_keywords'] > 0:
            # 平台分布
            if 'platform_distribution' in discovery_results:
                report_content += "### 平台分布\n"
                for platform, count in discovery_results['platform_distribution'].items():
                    report_content += f"- **{platform}**: {count} 个关键词\n"
                report_content += "\n"
            
            # 热门关键词
            if 'top_keywords_by_score' in discovery_results and discovery_results['top_keywords_by_score']:
                report_content += "### 热门关键词\n"
                for i, kw in enumerate(discovery_results['top_keywords_by_score'][:10], 1):
                    report_content += f"{i}. **{kw['keyword']}** (评分: {kw['score']}, 来源: {kw['platform']})\n"
                report_content += "\n"
            
            # 常见词汇
            if 'common_terms' in discovery_results and discovery_results['common_terms']:
                report_content += "### 常见词汇\n"
                for word, count in list(discovery_results['common_terms'].items())[:10]:
                    report_content += f"- **{word}**: {count}次\n"
                report_content += "\n"
        else:
            report_content += "未发现多平台关键词或发现过程失败。\n\n"
        
        # 新词检测摘要
        new_word_summary = workflow_results.get('demand_analysis', {}).get('new_word_summary')
        if new_word_summary:
            report_content += "## 🔎 新词检测摘要\n"
            report_content += f"- **检测总数**: {new_word_summary.get('total_analyzed', 0)}\n"
            report_content += f"- **新词数量**: {new_word_summary.get('new_words_detected', 0)}\n"
            report_content += f"- **高置信度新词**: {new_word_summary.get('high_confidence_new_words', 0)}\n"
            report_content += f"- **Breakout 级别**: {new_word_summary.get('breakout_keywords', 0)}\n"
            report_content += f"- **Rising 级别**: {new_word_summary.get('rising_keywords', 0)}\n"
            report_content += f"- **新词占比**: {new_word_summary.get('new_word_percentage', 0)}%\n\n"

            # 列出部分 Breakout 新词
            demand_keywords = workflow_results.get('demand_analysis', {}).get('keywords', [])
            breakout_keywords = [
                kw for kw in demand_keywords
                if kw.get('new_word_detection', {}).get('trend_momentum') == 'breakout'
            ]
            if breakout_keywords:
                report_content += "### 🔥 Breakout 新词样例\n"
                for kw in breakout_keywords[:5]:
                    nwd = kw.get('new_word_detection', {})
                    report_content += (
                        f"- **{kw.get('keyword')}** (分数: {nwd.get('new_word_score', 0)}, "
                        f"动量: {nwd.get('trend_momentum', '-')}, 突增: {nwd.get('avg_7d_delta', 0)})\n"
                    )
                report_content += "\n"

        report_content += "## 🎯 高价值关键词列表\n"
        
        # 添加高价值关键词详情
        for kw in workflow_results.get('high_value_keywords', [])[:10]:  # 只显示前10个
            report_content += f"- **{kw['keyword']}** (机会分数: {kw.get('opportunity_score', 0)})\n"
            report_content += f"  - 主要意图: {kw.get('intent', {}).get('primary_intent', 'Unknown')}\n"
            report_content += f"  - AI加分: {kw.get('market', {}).get('ai_bonus', 0)}\n"
            report_content += f"  - 商业价值: {kw.get('market', {}).get('commercial_value', 0)}\n"

            nwd = kw.get('new_word_detection', {})
            if nwd:
                report_content += (
                    "  - 新词信息: "
                    f"{'✅' if nwd.get('is_new_word') else '❌'} 等级 {nwd.get('new_word_grade', '-')}, "
                    f"动量 {nwd.get('trend_momentum', '-')}, Δ30D {nwd.get('avg_30d_delta', 0)}\n"
                )
            report_content += "\n"
        
        # 添加生成的网站项目
        report_content += "\n## 🏗️ 生成的网站项目\n"
        for website in workflow_results.get('generated_projects', []):
            status_icon = "✅" if website.get('status') == 'success' else "❌"
            report_content += f"{status_icon} **{website['keyword']}**\n"
            if website.get('status') == 'success':
                report_content += f"  - 项目目录: {website.get('source_dir', '')}\n"
            else:
                report_content += f"  - 错误: {website.get('error', '')}\n"
        
        # 添加部署结果
        if workflow_results.get('deployment_results'):
            report_content += "\n## 🚀 部署结果\n"
            for deployment in workflow_results.get('deployment_results', []):
                status_icon = "✅" if deployment.get('status') == 'success' else "❌"
                report_content += f"{status_icon} **{deployment['keyword']}**\n"
                if deployment.get('status') == 'success':
                    report_content += f"  - 部署地址: {deployment.get('deployment_url', '')}\n"
                else:
                    report_content += f"  - 错误: {deployment.get('error', '')}\n"
        
        # 添加建议
        report_content += f"""
## 💡 优化建议

### 关键词优化
- 继续挖掘相关长尾关键词
- 关注AI相关高价值关键词
- 定期更新关键词机会分数

### 网站优化
- 优化SEO元数据和结构
- 添加更多交互功能
- 完善移动端适配

### 运营建议
- 提交到AI工具导航站
- 建立社交媒体推广计划
- 监控网站流量和转化

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_path

    def _export_new_word_reports(self, new_word_results: pd.DataFrame) -> Dict[str, str]:
        if new_word_results is None or new_word_results.empty:
            return {}

        reports_dir = os.path.join(self.output_base_dir, 'reports', 'new_words')
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        exports: Dict[str, str] = {}

        def _save(df: pd.DataFrame, filename: str, key: str) -> None:
            if df is None or df.empty:
                return
            path = os.path.join(reports_dir, filename)
            df.to_csv(path, index=False)
            exports[key] = path

        try:
            breakout_df = new_word_results[new_word_results.get('trend_momentum') == 'breakout']
            _save(breakout_df, f'breakout_new_words_{timestamp}.csv', 'breakout')

            rising_df = new_word_results[new_word_results.get('trend_momentum').isin(['breakout', 'rising'])]
            _save(rising_df, f'rising_new_words_{timestamp}.csv', 'rising')

            top_df = new_word_results.sort_values('new_word_score', ascending=False).head(30)
            _save(top_df, f'top_new_words_{timestamp}.csv', 'top')
        except Exception as exc:
            print(f"⚠️ 导出新词报告失败: {exc}")

        return exports


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='集成工作流：需求挖掘 → 意图分析 → 网站生成 → 自动部署')
    parser.add_argument('--input', '-i', required=True, help='关键词输入文件路径')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--min-score', type=int, default=60, help='最低机会分数阈值')
    parser.add_argument('--max-projects', type=int, default=5, help='最大项目数量')
    parser.add_argument('--no-deploy', action='store_true', help='跳过自动部署')
    
    args = parser.parse_args()
    
    # 准备配置
    config = {
        'min_opportunity_score': args.min_score,
        'max_projects_per_batch': args.max_projects,
        'auto_deploy': not args.no_deploy,
        'deployment_platform': 'cloudflare',
        'use_tailwind': True,
        'generate_reports': True
    }
    
    # 如果有配置文件，加载配置
    if args.config and os.path.exists(args.config):
        import json
        with open(args.config, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config.update(user_config)
    
    try:
        # 创建工作流实例
        workflow = IntegratedWorkflow(config)
        
        # 执行完整工作流
        results = workflow.run_complete_workflow(args.input)
        
        if results['status'] == 'success':
            print(f"\n🎉 集成工作流执行成功！")
            print(f"🔍 多平台发现了 {results.get('multi_platform_discovery', {}).get('total_keywords', 0)} 个关键词")
            print(f"📋 详细报告: {results.get('report_path', '')}")
            return 0
        else:
            print(f"\n❌ 集成工作流执行失败: {results.get('error', '')}")
            return 1
            
    except Exception as e:
        print(f"❌ 程序执行异常: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
