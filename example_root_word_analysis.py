"""
词根趋势分析使用示例
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(str(Path(__file__).parent / "src"))

from src.demand_mining.root_word_trends_analyzer import RootWordTrendsAnalyzer

def example_single_word_analysis():
    """示例：分析单个词根"""
    print("=== 单个词根分析示例 ===")
    
    analyzer = RootWordTrendsAnalyzer()
    
    # 分析"AI"这个词根
    result = analyzer.analyze_single_root_word("AI", timeframe="12-m")
    
    if result["status"] == "success":
        data = result["data"]
        print(f"词根: {result['root_word']}")
        print(f"平均兴趣度: {data['average_interest']:.1f}")
        print(f"峰值兴趣度: {data['peak_interest']}")
        print(f"趋势方向: {data['trend_direction']}")
        
        print(f"\n前5个趋势点:")
        for point in data['trend_points'][:5]:
            print(f"  {point['date']}: {point['interest']}")
        
        print(f"\n前5个相关查询:")
        for query in data['related_queries'][:5]:
            print(f"  - {query['query']} (值: {query['value']})")
    else:
        print(f"分析失败: {result.get('error', '未知错误')}")

def example_get_related_keywords():
    """示例：获取相关关键词"""
    print("\n=== 获取相关关键词示例 ===")
    
    analyzer = RootWordTrendsAnalyzer()
    
    # 获取"Generator"的相关关键词
    keywords = analyzer.get_trending_keywords_for_root("Generator", limit=10)
    
    print(f"'Generator' 的相关关键词:")
    for i, keyword in enumerate(keywords, 1):
        print(f"{i:2d}. {keyword}")

def example_batch_analysis():
    """示例：批量分析（少量词根）"""
    print("\n=== 批量分析示例 ===")
    
    analyzer = RootWordTrendsAnalyzer()
    
    # 临时修改词根列表为少量测试
    test_words = ["AI", "Generator", "Converter", "Online", "Calculator"]
    analyzer.root_words = test_words
    
    print(f"分析 {len(test_words)} 个测试词根...")
    results = analyzer.analyze_all_root_words(timeframe="3-m", batch_size=2)
    
    print(f"\n分析结果:")
    print(f"成功: {results['summary']['successful_analyses']}")
    print(f"失败: {results['summary']['failed_analyses']}")
    
    if results['summary']['top_trending_words']:
        print(f"\n上升趋势:")
        for word_data in results['summary']['top_trending_words']:
            print(f"  - {word_data['word']}: {word_data['average_interest']:.1f}")

def main():
    """运行所有示例"""
    print("词根趋势分析工具使用示例\n")
    
    try:
        # 示例1：单个词根分析
        example_single_word_analysis()
        
        # 示例2：获取相关关键词
        example_get_related_keywords()
        
        # 示例3：批量分析（测试用）
        example_batch_analysis()
        
        print("\n=== 完整分析命令 ===")
        print("要分析所有51个词根，请运行:")
        print("python root_word_trends_cli.py")
        print("\n其他有用的命令:")
        print("python root_word_trends_cli.py --single-word 'AI'")
        print("python root_word_trends_cli.py --get-keywords 'Generator'")
        print("python root_word_trends_cli.py --timeframe 3-m --batch-size 3")
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已安装所需依赖: pip install pytrends pandas")

if __name__ == "__main__":
    main()