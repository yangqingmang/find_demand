#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量关键词分析工具
用于分析AI工具相关的多个种子关键词
"""

import sys
import os
import json
from datetime import datetime

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.market_analyzer import MarketAnalyzer
from src.utils import Logger, safe_print

def load_seed_keywords(file_path):
    """从文件加载种子关键词"""
    keywords = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过空行和注释行
                if line and not line.startswith('#'):
                    keywords.append(line)
        
        safe_print(f"已加载 {len(keywords)} 个种子关键词")
        return keywords
        
    except Exception as e:
        safe_print(f"加载关键词文件失败: {e}")
        return []

def analyze_ai_tools_keywords():
    """分析AI工具相关关键词"""
    
    # 创建日志记录器
    logger = Logger()
    logger.setup_console_encoding()
    
    safe_print("AI工具关键词批量分析")
    safe_print("=" * 50)
    
    # 加载种子关键词
    seed_file = 'data/ai_tools_seed_keywords.txt'
    keywords = load_seed_keywords(seed_file)
    
    if not keywords:
        safe_print("没有找到有效的种子关键词")
        return
    
    # 创建分析器
    analyzer = MarketAnalyzer('data/ai_tools_analysis')
    
    # 分析参数
    analysis_params = {
        'geo': 'US',  # 主要针对美国市场
        'timeframe': 'today 3-m',
        'volume_weight': 0.4,
        'growth_weight': 0.4,
        'kd_weight': 0.2,
        'min_score': 20,  # 降低最低分数以获取更多关键词
        'enrich': True
    }
    
    safe_print(f"分析参数: {analysis_params}")
    safe_print("")
    
    # 存储所有结果
    all_results = []
    successful_analyses = 0
    failed_analyses = 0
    
    # 分批处理关键词（每批3-5个）
    batch_size = 3
    total_batches = (len(keywords) + batch_size - 1) // batch_size
    
    for batch_idx in range(0, len(keywords), batch_size):
        batch_keywords = keywords[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        
        safe_print(f"正在分析第 {batch_num}/{total_batches} 批关键词: {batch_keywords}")
        
        try:
            # 运行分析
            result = analyzer.run_analysis(
                keywords=batch_keywords,
                **analysis_params
            )
            
            if 'error' in result:
                safe_print(f"  ❌ 批次 {batch_num} 分析失败: {result['error']}")
                failed_analyses += 1
            else:
                safe_print(f"  ✅ 批次 {batch_num} 分析成功: {result['关键词总数']} 个关键词")
                
                # 添加批次信息
                result['批次'] = batch_num
                result['种子关键词'] = batch_keywords
                all_results.append(result)
                successful_analyses += 1
                
        except Exception as e:
            safe_print(f"  ❌ 批次 {batch_num} 分析出错: {e}")
            failed_analyses += 1
        
        safe_print("")
    
    # 生成综合报告
    if all_results:
        generate_comprehensive_report(all_results, analysis_params)
    
    # 显示总结
    safe_print("批量分析完成!")
    safe_print(f"成功分析: {successful_analyses} 批")
    safe_print(f"失败分析: {failed_analyses} 批")
    safe_print(f"总关键词数: {sum(r['关键词总数'] for r in all_results)}")
    safe_print(f"高分关键词: {sum(r['高分关键词数'] for r in all_results)}")

def generate_comprehensive_report(results, params):
    """生成综合分析报告"""
    
    safe_print("正在生成综合分析报告...")
    
    # 汇总统计
    total_keywords = sum(r['关键词总数'] for r in results)
    total_high_score = sum(r['高分关键词数'] for r in results)
    avg_score = sum(r['平均指标']['平均评分'] for r in results) / len(results)
    avg_volume = sum(r['平均指标']['平均搜索量'] for r in results) / len(results)
    
    # 收集所有Top关键词
    all_top_keywords = []
    for result in results:
        for kw in result['Top5关键词']:
            kw['批次'] = result['批次']
            kw['种子关键词'] = ', '.join(result['种子关键词'])
            all_top_keywords.append(kw)
    
    # 按分数排序，取Top 20
    top_keywords = sorted(all_top_keywords, key=lambda x: x['score'], reverse=True)[:20]
    
    # 汇总意图分布
    intent_summary = {}
    for result in results:
        for intent, count in result['意图分布'].items():
            intent_summary[intent] = intent_summary.get(intent, 0) + count
    
    # 创建综合报告
    comprehensive_report = {
        '分析概览': {
            '分析时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '分析批次数': len(results),
            '总种子关键词数': sum(len(r['种子关键词']) for r in results),
            '分析参数': params
        },
        '关键指标': {
            '总关键词数': total_keywords,
            '高分关键词数': total_high_score,
            '高分关键词比例': f"{total_high_score/total_keywords*100:.1f}%" if total_keywords > 0 else "0%",
            '平均评分': round(avg_score, 2),
            '平均搜索量': round(avg_volume, 0)
        },
        'Top20高价值关键词': top_keywords,
        '整体意图分布': intent_summary,
        '各批次详情': [
            {
                '批次': r['批次'],
                '种子关键词': r['种子关键词'],
                '关键词总数': r['关键词总数'],
                '高分关键词数': r['高分关键词数'],
                '平均评分': r['平均指标']['平均评分']
            }
            for r in results
        ]
    }
    
    # 保存综合报告
    import json
    report_file = f"data/ai_tools_analysis/comprehensive_report_{datetime.now().strftime('%Y-%m-%d')}.json"
    os.makedirs(os.path.dirname(report_file), exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(comprehensive_report, f, ensure_ascii=False, indent=2)
    
    safe_print(f"综合报告已保存到: {report_file}")
    
    # 显示关键发现
    safe_print("\n🎯 关键发现:")
    safe_print(f"   • 总共发现 {total_keywords} 个相关关键词")
    safe_print(f"   • 其中 {total_high_score} 个为高价值关键词")
    safe_print(f"   • 平均评分: {avg_score:.1f}")
    safe_print(f"   • 平均搜索量: {avg_volume:.0f}")
    
    safe_print("\n🏆 Top 5 高价值关键词:")
    for i, kw in enumerate(top_keywords[:5]):
        safe_print(f"   {i+1}. {kw['query']} (分数: {kw['score']}, {kw['intent']}, 搜索量: {kw['volume']})")
    
    safe_print("\n📊 意图分布:")
    for intent, count in sorted(intent_summary.items(), key=lambda x: x[1], reverse=True):
        percentage = count / total_keywords * 100
        safe_print(f"   • {intent}: {count} 个关键词 ({percentage:.1f}%)")

if __name__ == "__main__":
    analyze_ai_tools_keywords()