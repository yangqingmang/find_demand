#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
需求挖掘与关键词分析主程序
整合传统关键词挖掘与出海AI工具需求发现策略
基于路漫漫分享的六大需求挖掘方法进行系统性需求分析
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.demand_mining.analyzers.intent_analyzer_v2 import IntentAnalyzerV2
from src.demand_mining.analyzers.intent_analyzer import IntentAnalyzer
from src.demand_mining.analyzers.market_analyzer import MarketAnalyzer
from src.demand_mining.analyzers.keyword_analyzer import KeywordAnalyzer
from src.demand_mining.core.root_word_manager import RootWordManager

class DemandMiningManager:
    """
    整合需求挖掘管理器
    基于六大需求挖掘方法：
    1. 基于词根关键词拓展
    2. 基于SEO大站流量分析  
    3. 搜索引擎下拉推荐
    4. 循环挖掘法
    5. 付费广告关键词分析
    6. 收入排行榜分析
    """
    
    def __init__(self, config_path: str = None):
        """初始化需求挖掘管理器"""
        self.config = self._load_config(config_path)
        self.output_dir = "src/demand_mining/reports"
        self._ensure_output_dirs()
        
        # 初始化分析器（启用建站建议功能）
        self.intent_analyzer = IntentAnalyzer(
            use_v2=True, 
            enable_website_recommendations=True
        )
        self.market_analyzer = MarketAnalyzer()
        self.keyword_analyzer = KeywordAnalyzer()
        
        # 初始化词根管理器（整合51个网络收集的词根）
        self.root_manager = RootWordManager(config_path)
        
        # 获取当前激活的词根（支持手动指定和默认配置）
        self.core_roots = self.root_manager.get_active_roots()
        self.ai_prefixes = self.root_manager.ai_prefixes
        
        # 高价值竞品网站（用于流量分析）
        self.competitor_sites = [
            'canva.com', 'midjourney.com', 'openai.com', 'jasper.ai',
            'copy.ai', 'writesonic.com', 'rytr.me', 'jarvis.ai'
        ]
        
        print("🚀 整合需求挖掘管理器初始化完成")
        print(f"📊 已加载 {len(self.core_roots)} 个核心词根")
        print(f"🎯 已配置 {len(self.competitor_sites)} 个竞品分析目标")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        default_config = {
            'min_search_volume': 100,
            'max_competition': 0.8,
            'min_confidence': 0.7,
            'output_formats': ['csv', 'json'],
            'data_sources': ['google_trends', 'keyword_planner'],
            'analysis_depth': 'standard'  # basic, standard, deep
        }
        
        if config_path and os.path.exists(config_path):
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _ensure_output_dirs(self):
        """确保输出目录存在"""
        dirs = [
            self.output_dir,
            os.path.join(self.output_dir, 'daily_reports'),
            os.path.join(self.output_dir, 'weekly_reports'),
            os.path.join(self.output_dir, 'monthly_reports'),
            os.path.join(self.output_dir, 'keyword_analysis'),
            os.path.join(self.output_dir, 'intent_analysis'),
            os.path.join(self.output_dir, 'market_analysis')
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def analyze_keywords(self, input_file: str, output_dir: str = None) -> Dict[str, Any]:
        """分析关键词文件"""
        print(f"📊 开始分析关键词文件: {input_file}")
        
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"输入文件不存在: {input_file}")
        
        # 读取数据
        if input_file.endswith('.csv'):
            df = pd.read_csv(input_file)
        elif input_file.endswith('.json'):
            df = pd.read_json(input_file)
        else:
            raise ValueError("不支持的文件格式，请使用CSV或JSON文件")
        
        print(f"✅ 成功读取 {len(df)} 条关键词数据")
        
        # 分析结果
        results = {
            'total_keywords': len(df),
            'analysis_time': datetime.now().isoformat(),
            'keywords': [],
            'intent_summary': {},
            'market_insights': {},
            'recommendations': []
        }
        
        # 关键词逐个分析
        for idx, row in df.iterrows():
            keyword = row.get('query', row.get('keyword', ''))
            if not keyword:
                continue
            
            print(f"🔍 分析关键词 ({idx+1}/{len(df)}): {keyword}")
            
            # 意图分析
            intent_result = self._analyze_keyword_intent(keyword)
            
            # 市场分析
            market_result = self._analyze_keyword_market(keyword)
            
            # 整合结果
            keyword_result = {
                'keyword': keyword,
                'intent': intent_result,
                'market': market_result,
                'opportunity_score': self._calculate_opportunity_score(intent_result, market_result)
            }
            
            results['keywords'].append(keyword_result)
        
        # 生成摘要
        results['intent_summary'] = self._generate_intent_summary(results['keywords'])
        results['market_insights'] = self._generate_market_insights(results['keywords'])
        results['recommendations'] = self._generate_recommendations(results['keywords'])
        
        # 保存结果
        output_path = self._save_analysis_results(results, output_dir)
        
        print(f"✅ 关键词分析完成，结果已保存到: {output_path}")
        return results
    
    def _analyze_keyword_intent(self, keyword: str) -> Dict[str, Any]:
        """分析关键词意图（包含建站建议）"""
        try:
            # 创建包含关键词的DataFrame进行分析
            import pandas as pd
            df = pd.DataFrame({'query': [keyword]})
            
            # 使用意图分析器进行完整分析（包含建站建议）
            result_df = self.intent_analyzer.analyze_keywords(df, keyword_col='query')
            
            if len(result_df) > 0:
                row = result_df.iloc[0]
                return {
                    'primary_intent': row.get('intent', 'Unknown'),
                    'confidence': row.get('intent_confidence', 0.0),
                    'secondary_intent': row.get('secondary_intent'),
                    'intent_description': row.get('intent_description', ''),
                    'website_recommendations': {
                        'website_type': row.get('website_type'),
                        'ai_tool_category': row.get('ai_tool_category'),
                        'domain_suggestions': row.get('domain_suggestions', []),
                        'monetization_strategy': row.get('monetization_strategy', []),
                        'technical_requirements': row.get('technical_requirements', []),
                        'competition_analysis': row.get('competition_analysis', {}),
                        'development_priority': row.get('development_priority', {}),
                        'content_strategy': row.get('content_strategy', [])
                    }
                }
            else:
                raise Exception("分析结果为空")
                
        except Exception as e:
            print(f"⚠️ 意图分析失败 ({keyword}): {e}")
            return {
                'primary_intent': 'Unknown',
                'confidence': 0.0,
                'secondary_intent': None,
                'intent_description': '分析失败',
                'website_recommendations': {}
            }
    
    def _analyze_keyword_market(self, keyword: str) -> Dict[str, Any]:
        """
        分析关键词市场数据
        整合六大挖掘方法的市场验证逻辑
        """
        try:
            # 基础市场数据（模拟，实际可接入真实API）
            base_data = {
                'search_volume': 1000,
                'competition': 0.5,
                'cpc': 2.0,
                'trend': 'stable',
                'seasonality': 'low'
            }
            
            # 新增：AI相关关键词加分
            ai_bonus = self._calculate_ai_bonus(keyword)
            
            # 新增：词根匹配度评分
            root_match_score = self._calculate_root_match_score(keyword)
            
            # 新增：新兴关键词检测
            newness_score = self._detect_keyword_newness(keyword)
            
            # 新增：商业价值评估
            commercial_value = self._assess_commercial_value(keyword)
            
            # 整合评分
            base_data.update({
                'ai_bonus': ai_bonus,
                'root_match_score': root_match_score,
                'newness_score': newness_score,
                'commercial_value': commercial_value,
                'opportunity_indicators': self._get_opportunity_indicators(keyword)
            })
            
            return base_data
            
        except Exception as e:
            print(f"⚠️ 市场分析失败 ({keyword}): {e}")
            return {
                'search_volume': 0,
                'competition': 0.0,
                'cpc': 0.0,
                'trend': 'unknown',
                'seasonality': 'unknown',
                'ai_bonus': 0,
                'root_match_score': 0,
                'newness_score': 0,
                'commercial_value': 0,
                'opportunity_indicators': []
            }
    
    def _calculate_ai_bonus(self, keyword: str) -> float:
        """计算AI相关关键词加分"""
        keyword_lower = keyword.lower()
        ai_score = 0
        
        # AI前缀匹配
        for prefix in self.ai_prefixes:
            if prefix in keyword_lower:
                ai_score += 20
                break
        
        # AI工具类型匹配
        ai_tool_types = ['generator', 'detector', 'writer', 'assistant', 'chatbot']
        for tool_type in ai_tool_types:
            if tool_type in keyword_lower:
                ai_score += 15
                break
        
        # 新兴AI概念
        emerging_concepts = ['gpt', 'llm', 'diffusion', 'transformer', 'neural']
        for concept in emerging_concepts:
            if concept in keyword_lower:
                ai_score += 10
                break
        
        return min(ai_score, 50)  # 最高50分
    
    def _calculate_root_match_score(self, keyword: str) -> float:
        """计算词根匹配度评分"""
        keyword_lower = keyword.lower()
        match_score = 0
        
        for root in self.core_roots:
            if root in keyword_lower:
                match_score += 30
                break
        
        return min(match_score, 30)  # 最高30分
    
    def _detect_keyword_newness(self, keyword: str) -> float:
        """检测关键词新兴程度"""
        # 简化的新兴关键词检测逻辑
        keyword_lower = keyword.lower()
        newness_indicators = [
            'ai', 'gpt', 'chatbot', 'neural', 'machine learning',
            'deep learning', 'transformer', 'diffusion', 'stable diffusion'
        ]
        
        newness_score = 0
        for indicator in newness_indicators:
            if indicator in keyword_lower:
                newness_score += 15
        
        # 检查是否包含年份（如2024, 2025等，表示新兴）
        import re
        if re.search(r'202[4-9]', keyword):
            newness_score += 20
        
        return min(newness_score, 40)  # 最高40分
    
    def _assess_commercial_value(self, keyword: str) -> float:
        """评估商业价值"""
        keyword_lower = keyword.lower()
        commercial_score = 0
        
        # 高价值关键词类型
        high_value_types = [
            'generator', 'converter', 'editor', 'maker', 'creator',
            'optimizer', 'enhancer', 'analyzer', 'detector'
        ]
        
        for value_type in high_value_types:
            if value_type in keyword_lower:
                commercial_score += 25
                break
        
        # 付费意愿强的领域
        high_payment_domains = [
            'business', 'marketing', 'seo', 'content', 'design',
            'video', 'image', 'writing', 'coding', 'academic'
        ]
        
        for domain in high_payment_domains:
            if domain in keyword_lower:
                commercial_score += 20
                break
        
        return min(commercial_score, 50)  # 最高50分
    
    def _get_opportunity_indicators(self, keyword: str) -> List[str]:
        """获取机会指标"""
        indicators = []
        keyword_lower = keyword.lower()
        
        # AI相关
        if any(prefix in keyword_lower for prefix in self.ai_prefixes):
            indicators.append("AI相关需求")
        
        # 工具类
        if any(root in keyword_lower for root in self.core_roots):
            indicators.append("工具类需求")
        
        # 新兴概念
        if any(concept in keyword_lower for concept in ['gpt', 'chatbot', 'neural']):
            indicators.append("新兴技术")
        
        # 出海友好
        if not any(chinese_char in keyword for chinese_char in '中文汉字'):
            indicators.append("出海友好")
        
        return indicators
    
    def _calculate_opportunity_score(self, intent_result: Dict, market_result: Dict) -> float:
        """
        计算综合机会分数
        整合六大挖掘方法的评分逻辑
        """
        try:
            # 基础评分权重
            weights = {
                'intent_confidence': 0.15,      # 意图置信度
                'search_volume': 0.20,          # 搜索量
                'competition': 0.15,            # 竞争度（越低越好）
                'ai_bonus': 0.20,              # AI相关加分
                'commercial_value': 0.15,       # 商业价值
                'newness': 0.10,               # 新兴程度
                'root_match': 0.05             # 词根匹配
            }
            
            # 各项分数计算
            intent_score = intent_result.get('confidence', 0) * 100
            volume_score = min(market_result.get('search_volume', 0) / 1000, 1) * 100
            competition_score = (1 - market_result.get('competition', 1)) * 100
            ai_bonus = market_result.get('ai_bonus', 0)
            commercial_value = market_result.get('commercial_value', 0)
            newness_score = market_result.get('newness_score', 0)
            root_match_score = market_result.get('root_match_score', 0)
            
            # 加权计算总分
            total_score = (
                intent_score * weights['intent_confidence'] +
                volume_score * weights['search_volume'] +
                competition_score * weights['competition'] +
                ai_bonus * weights['ai_bonus'] +
                commercial_value * weights['commercial_value'] +
                newness_score * weights['newness'] +
                root_match_score * weights['root_match']
            )
            
            # 特殊加分项
            bonus_points = 0
            
            # 趋势加分
            if market_result.get('trend') == 'rising':
                bonus_points += 5
            
            # 机会指标加分
            opportunity_indicators = market_result.get('opportunity_indicators', [])
            if len(opportunity_indicators) >= 3:
                bonus_points += 5
            
            final_score = total_score + bonus_points
            return round(min(final_score, 100), 2)
            
        except Exception as e:
            print(f"⚠️ 机会分数计算失败: {e}")
            return 0.0
    
    def _generate_intent_summary(self, keywords: List[Dict]) -> Dict[str, Any]:
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
    
    def _generate_market_insights(self, keywords: List[Dict]) -> Dict[str, Any]:
        """生成市场洞察"""
        high_opportunity = [kw for kw in keywords if kw['opportunity_score'] >= 70]
        medium_opportunity = [kw for kw in keywords if 40 <= kw['opportunity_score'] < 70]
        low_opportunity = [kw for kw in keywords if kw['opportunity_score'] < 40]
        
        return {
            'high_opportunity_count': len(high_opportunity),
            'medium_opportunity_count': len(medium_opportunity),
            'low_opportunity_count': len(low_opportunity),
            'top_opportunities': sorted(keywords, key=lambda x: x['opportunity_score'], reverse=True)[:10],
            'avg_opportunity_score': round(sum(kw['opportunity_score'] for kw in keywords) / len(keywords), 2) if keywords else 0
        }
    
    def _generate_recommendations(self, keywords: List[Dict]) -> List[str]:
        """
        生成基于六大挖掘方法的综合建议
        """
        recommendations = []
        
        # 分析关键词分布
        high_opportunity = [kw for kw in keywords if kw['opportunity_score'] >= 70]
        medium_opportunity = [kw for kw in keywords if 40 <= kw['opportunity_score'] < 70]
        ai_keywords = [kw for kw in keywords if kw['market'].get('ai_bonus', 0) > 0]
        new_keywords = [kw for kw in keywords if kw['market'].get('newness_score', 0) > 20]
        
        # 高机会关键词建议
        if high_opportunity:
            recommendations.append(f"🎯 发现 {len(high_opportunity)} 个高机会关键词，建议立即开发MVP产品抢占先机")
            top_3 = sorted(high_opportunity, key=lambda x: x['opportunity_score'], reverse=True)[:3]
            for i, kw in enumerate(top_3, 1):
                recommendations.append(f"   {i}. {kw['keyword']} (机会分数: {kw['opportunity_score']})")
        
        # AI相关建议
        if ai_keywords:
            recommendations.append(f"🤖 发现 {len(ai_keywords)} 个AI相关关键词，符合出海AI工具方向")
            recommendations.append("   建议重点关注AI Generator、AI Detector、AI Assistant等高价值类型")
        
        # 新兴关键词建议
        if new_keywords:
            recommendations.append(f"🆕 发现 {len(new_keywords)} 个新兴关键词，竞争相对较小")
            recommendations.append("   建议快速验证需求并开发，利用SEO优势抢占排名")
        
        # 基于六大方法的具体建议
        recommendations.extend([
            "📊 方法一建议：基于核心词根继续拓展，重点关注Generator、Converter、Analyzer类关键词",
            "🔍 方法二建议：分析Canva、Midjourney等大站流量，寻找内页排名的机会关键词",
            "💡 方法三建议：利用Google下拉推荐发现长尾关键词，降低竞争难度",
            "🔄 方法四建议：建立循环挖掘机制，从搜索结果→竞品分析→新关键词→再搜索",
            "💰 方法五建议：关注付费广告投放的关键词，这些通常是高ROI的盈利需求",
            "📈 方法六建议：定期查看Toolify.ai和IndieHackers排行榜，跟踪成功产品的关键词策略"
        ])
        
        # 流量获取建议
        recommendations.extend([
            "🚀 流量获取：优先SEO+SEM组合，免费流量+付费流量双管齐下",
            "🌐 导航站：提交到300+个AI导航站，重点关注theresanaiforthat.com和Toolify.ai",
            "📱 社交媒体：利用Reddit、ProductHunt、Hacker News等平台进行软性推广",
            "🤝 联盟营销：建立Affiliate机制，让中小流量渠道帮助推广"
        ])
        
        # 收入验证建议
        if medium_opportunity or high_opportunity:
            recommendations.extend([
                "💵 收入验证：通过Similarweb分析checkout.stripe.com流量，验证需求的真实盈利能力",
                "📊 竞品分析：关注竞品的广告投放情况，持续投放=持续盈利",
                "⚡ 快速行动：发现高价值需求后24-48小时内完成MVP，抢占先发优势"
            ])
        
        # 意图分布建议
        intent_summary = self._generate_intent_summary(keywords)
        dominant_intent = intent_summary['dominant_intent']
        if dominant_intent != 'Unknown':
            recommendations.append(f"🎯 主要意图为 {dominant_intent}，建议针对此意图优化产品功能和页面内容")
        
        return recommendations
    
    def _save_analysis_results(self, results: Dict[str, Any], output_dir: str = None) -> str:
        """保存分析结果"""
        if not output_dir:
            output_dir = os.path.join(self.output_dir, 'keyword_analysis')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存JSON格式
        json_path = os.path.join(output_dir, f'keyword_analysis_{timestamp}.json')
        import json
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存CSV格式（关键词详情）
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
    
    def generate_daily_report(self, date: str = None) -> str:
        """生成日报"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        print(f"📅 生成日报: {date}")
        
        # 这里可以集成实际的日报生成逻辑
        report_content = f"""# 需求挖掘日报 - {date}

## 📊 今日概览
- 分析关键词数量: 待统计
- 发现高价值关键词: 待统计
- 新增意图类别: 待统计

## 🔍 关键发现
- 待补充具体发现

## 📈 趋势分析
- 待补充趋势数据

## 💡 行动建议
- 待补充具体建议

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        report_path = os.path.join(self.output_dir, 'daily_reports', f'daily_report_{date}.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"✅ 日报已生成: {report_path}")
        return report_path
    
    def analyze_root_words(self, output_dir: str = None) -> Dict[str, Any]:
        """
        分析51个词根的趋势数据
        集成词根趋势分析器功能
        """
        print("🌱 开始分析51个词根的Google Trends趋势...")
        
        try:
            # 导入词根趋势分析器
            from src.demand_mining.root_word_trends_analyzer import RootWordTrendsAnalyzer
            
            # 创建分析器
            analyzer = RootWordTrendsAnalyzer(output_dir or os.path.join(self.output_dir, 'root_word_trends'))
            
            # 执行分析
            results = analyzer.analyze_all_root_words(timeframe="12-m", batch_size=5)
            
            # 转换为统一格式，兼容现有的显示逻辑
            unified_result = {
                'analysis_type': 'root_words_trends',
                'analysis_time': results['analysis_date'],
                'total_root_words': results['total_root_words'],
                'successful_analyses': results['summary']['successful_analyses'],
                'failed_analyses': results['summary']['failed_analyses'],
                'top_trending_words': results['summary']['top_trending_words'],
                'declining_words': results['summary']['declining_words'],
                'stable_words': results['summary']['stable_words'],
                'total_keywords': results['total_root_words'],  # 兼容现有显示逻辑
                'market_insights': {
                    'high_opportunity_count': len(results['summary']['top_trending_words']),
                    'avg_opportunity_score': self._calculate_avg_interest(results['summary']['top_trending_words'])
                }
            }
            
            print(f"✅ 词根趋势分析完成!")
            print(f"   成功分析: {unified_result['successful_analyses']} 个词根")
            print(f"   失败分析: {unified_result['failed_analyses']} 个词根")
            print(f"   上升趋势: {len(unified_result['top_trending_words'])} 个词根")
            
            return unified_result
            
        except ImportError as e:
            print(f"❌ 导入词根趋势分析器失败: {e}")
            print("请确保 root_word_trends_analyzer.py 文件存在")
            return self._create_empty_root_result()
        except Exception as e:
            print(f"❌ 词根趋势分析失败: {e}")
            return self._create_empty_root_result()
    
    def _calculate_avg_interest(self, trending_words: List[Dict]) -> float:
        """计算平均兴趣度"""
        if not trending_words:
            return 0.0
        
        total_interest = sum(word.get('average_interest', 0) for word in trending_words)
        return round(total_interest / len(trending_words), 2)
    
    def _create_empty_root_result(self) -> Dict[str, Any]:
        """创建空的词根分析结果"""
        return {
            'analysis_type': 'root_words_trends',
            'analysis_time': datetime.now().isoformat(),
            'total_root_words': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'top_trending_words': [],
            'declining_words': [],
            'stable_words': [],
            'total_keywords': 0,
            'market_insights': {
                'high_opportunity_count': 0,
                'avg_opportunity_score': 0.0
            }
        }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='需求挖掘与关键词分析工具')
    parser.add_argument('--action', choices=['analyze', 'report', 'discover', 'help'], 
                       default='help', help='执行的操作')
    parser.add_argument('--input', help='输入文件路径')
    parser.add_argument('--output', help='输出目录路径')
    parser.add_argument('--config', help='配置文件路径')
    parser.add_argument('--date', help='报告日期 (YYYY-MM-DD)')
    parser.add_argument('--search-terms', nargs='+', help='多平台发现的搜索词汇')
    
    args = parser.parse_args()
    
    if args.action == 'help':
        print("""
🔍 需求挖掘与关键词分析工具

使用方法:
  python demand_mining_main.py --action analyze --input data/keywords.csv
  python demand_mining_main.py --action report --date 2025-08-08
  python demand_mining_main.py --action discover --search-terms "AI tool" "AI generator"
  python demand_mining_main.py --help

操作说明:
  analyze   - 分析关键词文件
  report    - 生成分析报告
  discover  - 多平台关键词发现
  help      - 显示帮助信息

示例:
  # 分析关键词
  python demand_mining_main.py --action analyze --input data/test_intent_keywords.csv
  
  # 生成今日报告
  python demand_mining_main.py --action report
  
  # 多平台关键词发现
  python demand_mining_main.py --action discover --search-terms "AI tool" "AI generator" "chatbot"
  
  # 生成指定日期报告
  python demand_mining_main.py --action report --date 2025-08-08

🌐 多平台关键词发现支持的平台:
  • Reddit (r/artificial, r/MachineLearning, r/ChatGPT 等)
  • Hacker News (技术讨论和Show HN项目)
  • YouTube (搜索建议和热门视频)
  • Google (搜索建议和自动完成)
  • 更多平台持续添加中...

💡 发现高价值关键词的最佳实践:
  1. 使用多个相关搜索词汇
  2. 关注社交媒体讨论热点
  3. 分析技术社区的问题和需求
  4. 跟踪搜索引擎的建议词汇
  5. 结合传统关键词工具验证数据
        """)
        return
    
    try:
        # 初始化管理器
        manager = DemandMiningManager(args.config)
        
        if args.action == 'analyze':
            if not args.input:
                print("❌ 错误: 请指定输入文件 (--input)")
                return
            
            results = manager.analyze_keywords(args.input, args.output)
            print(f"🎉 分析完成! 共分析 {results['total_keywords']} 个关键词")
            
        elif args.action == 'report':
            report_path = manager.generate_daily_report(args.date)
            print(f"📋 报告已生成: {report_path}")
            
        elif args.action == 'discover':
            # 多平台关键词发现
            search_terms = args.search_terms or ['AI tool', 'AI generator', 'AI assistant']
            
            print(f"🔍 开始多平台关键词发现...")
            print(f"📊 搜索词汇: {', '.join(search_terms)}")
            
            try:
                # 导入多平台发现工具
                from src.demand_mining.tools.multi_platform_keyword_discovery import MultiPlatformKeywordDiscovery
                
                # 创建发现工具
                discoverer = MultiPlatformKeywordDiscovery()
                
                # 执行发现
                df = discoverer.discover_all_platforms(search_terms)
                
                if not df.empty:
                    # 分析趋势
                    analysis = discoverer.analyze_keyword_trends(df)
                    
                    # 保存结果
                    output_dir = args.output or 'src/demand_mining/reports/multi_platform_discovery'
                    csv_path, json_path = discoverer.save_results(df, analysis, output_dir)
                    
                    # 显示结果摘要
                    print(f"\n🎉 多平台关键词发现完成!")
                    print(f"📊 发现 {analysis['total_keywords']} 个关键词")
                    print(f"🌐 平台分布: {analysis['platform_distribution']}")
                    
                    print(f"\n🏆 热门关键词:")
                    for i, kw in enumerate(analysis['top_keywords_by_score'][:5], 1):
                        print(f"  {i}. {kw['keyword']} (评分: {kw['score']}, 来源: {kw['platform']})")
                    
                    print(f"\n📁 结果已保存:")
                    print(f"  CSV: {csv_path}")
                    print(f"  JSON: {json_path}")
                    
                    # 可选：直接分析发现的关键词
                    user_input = input("\n🤔 是否要立即分析这些关键词的意图和市场机会? (y/n): ")
                    if user_input.lower() in ['y', 'yes', '是']:
                        print("🔄 开始分析发现的关键词...")
                        results = manager.analyze_keywords(csv_path, args.output)
                        print(f"✅ 关键词分析完成! 共分析 {results['total_keywords']} 个关键词")
                else:
                    print("⚠️ 未发现任何关键词，请检查网络连接或调整搜索参数")
                    
            except ImportError as e:
                print(f"❌ 导入多平台发现工具失败: {e}")
                print("请确保所有依赖已正确安装")
            except Exception as e:
                print(f"❌ 多平台关键词发现失败: {e}")
                import traceback
                traceback.print_exc()
        
        elif args.action == 'report':
            report_path = manager.generate_daily_report(args.date)
            print(f"📋 报告已生成: {report_path}")
            
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()