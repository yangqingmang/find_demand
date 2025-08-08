#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
关键词评分模块 - Keyword Scorer
基于多维度指标对关键词进行综合评分
"""

import pandas as pd
import numpy as np
import os
import argparse
import re

from .base_analyzer import BaseAnalyzer
try:
    from src.utils import (
        FileUtils, Logger, ExceptionHandler, DataError,
        DEFAULT_CONFIG, SCORE_GRADES
    )
except ImportError:
    # 如果无法导入utils，使用简化版本
    class Logger:
        def info(self, msg): print(f"INFO: {msg}")
        def warning(self, msg): print(f"WARNING: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
    
    class FileUtils:
        @staticmethod
        def generate_filename(prefix, extension='csv'):
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            return f"{prefix}_{timestamp}.{extension}"
        
        @staticmethod
        def save_dataframe(df, output_dir, filename):
            import os
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, filename)
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            return file_path
    
    DEFAULT_CONFIG = {'high_score_threshold': 70}
    SCORE_GRADES = ['D', 'C', 'B', 'A']

class KeywordScorer(BaseAnalyzer):
    """关键词评分类，用于对关键词进行综合评分"""
    
    def __init__(self, volume_weight=0.4, growth_weight=0.4, kd_weight=0.2):
        """
        初始化关键词评分器
        
        参数:
            volume_weight (float): 搜索量权重
            growth_weight (float): 增长率权重
            kd_weight (float): 关键词难度权重
        """
        super().__init__()
        self.volume_weight = volume_weight
        self.growth_weight = growth_weight
        self.kd_weight = kd_weight
        
        # 验证权重总和为1
        from src.utils import validate_weights
        if not validate_weights(volume_weight, growth_weight, kd_weight):
            total_weight = volume_weight + growth_weight + kd_weight
            self.logger.warning(f"权重总和 ({total_weight}) 不等于1，已自动归一化")
            self.volume_weight /= total_weight
            self.growth_weight /= total_weight
            self.kd_weight /= total_weight
    
    def analyze(self, data, volume_col='value', growth_col='growth', kd_col=None, **kwargs):
        """
        实现基础分析器的抽象方法
        
        参数:
            data: 关键词数据DataFrame
            volume_col: 搜索量列名
            growth_col: 增长率列名
            kd_col: 关键词难度列名
            **kwargs: 其他参数
            
        返回:
            评分后的DataFrame
        """
        return self.score_keywords(data, volume_col, growth_col, kd_col)
    
    def normalize(self, series, min_val=None, max_val=None):
        """
        将数据系列归一化到0-100范围
        
        参数:
            series: 要归一化的pandas Series
            min_val: 最小值，如果为None则使用series的最小值
            max_val: 最大值，如果为None则使用series的最大值
            
        返回:
            归一化后的pandas Series
        """
        if series.empty:
            return series
            
        if min_val is None:
            min_val = series.min()
        if max_val is None:
            max_val = series.max()
            
        # 如果最大值等于最小值，返回50分
        if max_val == min_val:
            return pd.Series([50] * len(series))
            
        # 归一化到0-100
        normalized = 100 * (series - min_val) / (max_val - min_val)
        return normalized
    
    def score_keywords(self, df, volume_col='value', growth_col='growth', kd_col=None):
        """
        对关键词进行评分
        
        参数:
            df (DataFrame): 包含关键词数据的DataFrame
            volume_col (str): 搜索量列名
            growth_col (str): 增长率列名
            kd_col (str): 关键词难度列名，如果为None则不考虑KD
            
        返回:
            添加了评分列的DataFrame
        """
        if not self.validate_input(df):
            return df
        
        self.log_analysis_start("关键词评分", f"，共 {len(df)} 个关键词")
            
        # 创建副本避免修改原始数据
        result_df = df.copy()
        
        # 归一化搜索量
        if volume_col in result_df.columns:
            result_df['volume_score'] = self.normalize(result_df[volume_col])
        else:
            self.logger.warning(f"未找到搜索量列 '{volume_col}'")
            result_df['volume_score'] = 0
            
        # 归一化增长率
        if growth_col in result_df.columns:
            # 确保增长率为数值型
            if result_df[growth_col].dtype == 'object':
                # 尝试从字符串中提取数字，如 "1,500%" -> 1500
                result_df[growth_col] = result_df[growth_col].apply(
                    lambda x: float(re.sub(r'[^0-9.]', '', str(x))) if pd.notnull(x) else 0
                )
            result_df['growth_score'] = self.normalize(result_df[growth_col])
        else:
            self.logger.warning(f"未找到增长率列 '{growth_col}'")
            result_df['growth_score'] = 0
            
        # 归一化关键词难度（KD越低越好，所以用100减去归一化值）
        if kd_col and kd_col in result_df.columns:
            result_df['kd_score'] = 100 - self.normalize(result_df[kd_col])
        else:
            self.logger.warning(f"未找到关键词难度列 '{kd_col}'，使用默认值")
            result_df['kd_score'] = 50  # 默认中等难度
            
        # 计算综合评分
        result_df['score'] = (
            self.volume_weight * result_df['volume_score'] +
            self.growth_weight * result_df['growth_score'] +
            self.kd_weight * result_df['kd_score']
        )
        
        # 四舍五入到整数
        result_df['score'] = result_df['score'].round().astype(int)
        
        # 添加评分等级
        result_df['grade'] = pd.cut(
            result_df['score'],
            bins=[0, 30, 50, 70, 100],
            labels=['D', 'C', 'B', 'A']
        )
        
        return result_df
    
    def filter_keywords(self, df, min_score=None, min_volume=None, min_growth=None, max_kd=None):
        """
        根据条件过滤关键词
        
        参数:
            df (DataFrame): 关键词数据
            min_score (int): 最低评分
            min_volume (int): 最低搜索量
            min_growth (float): 最低增长率
            max_kd (int): 最高关键词难度
            
        返回:
            过滤后的DataFrame
        """
        filtered_df = df.copy()
        
        if min_score is not None:
            filtered_df = filtered_df[filtered_df['score'] >= min_score]
            
        if min_volume is not None and 'value' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['value'] >= min_volume]
            
        if min_growth is not None and 'growth' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['growth'] >= min_growth]
            
        if max_kd is not None and 'kd' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['kd'] <= max_kd]
            
        return filtered_df
    
    def enrich_with_ads_data(self, df, keyword_col='query', api_key=None):
        """
        使用Google Ads API丰富关键词数据（模拟实现）
        
        参数:
            df (DataFrame): 关键词数据
            keyword_col (str): 关键词列名
            api_key (str): Google Ads API密钥
            
        返回:
            丰富后的DataFrame
        """
        # 注意：这是一个模拟实现，实际使用需要替换为真实的API调用
        from src.utils.mock_data_generator import generate_mock_ads_data
        
        self.logger.info("使用模拟数据丰富关键词信息...")
        return generate_mock_ads_data(df, keyword_col)
    
    def save_results(self, df, output_dir='data', prefix='scored'):
        """
        保存评分结果
        
        参数:
            df (DataFrame): 评分后的DataFrame
            output_dir (str): 输出目录
            prefix (str): 文件名前缀
        """
        # 保存主要结果
        filename = FileUtils.generate_filename(prefix, extension='csv')
        file_path = FileUtils.save_dataframe(df, output_dir, filename)
        self.logger.info(f"已保存评分结果到: {file_path}")
        
        # 保存高分关键词
        high_score_threshold = DEFAULT_CONFIG['high_score_threshold']
        high_score_df = df[df['score'] >= high_score_threshold].sort_values('score', ascending=False)
        if not high_score_df.empty:
            high_score_filename = FileUtils.generate_filename(f'{prefix}_high_score', extension='csv')
            high_score_path = FileUtils.save_dataframe(high_score_df, output_dir, high_score_filename)
            self.logger.info(f"已保存高分关键词 ({len(high_score_df)}个) 到: {high_score_path}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='关键词评分工具')
    parser.add_argument('--input', required=True, help='输入CSV文件路径')
    parser.add_argument('--output', default='data', help='输出目录，默认为data')
    parser.add_argument('--volume-weight', type=float, default=0.4, help='搜索量权重，默认0.4')
    parser.add_argument('--growth-weight', type=float, default=0.4, help='增长率权重，默认0.4')
    parser.add_argument('--kd-weight', type=float, default=0.2, help='关键词难度权重，默认0.2')
    parser.add_argument('--min-score', type=int, help='最低评分过滤')
    parser.add_argument('--enrich', action='store_true', help='使用模拟的Ads数据丰富关键词')
    
    args = parser.parse_args()
    
    # 创建日志记录器
    logger = Logger()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input):
        logger.error(f"输入文件 '{args.input}' 不存在")
        return
    
    # 读取输入文件
    try:
        df = pd.read_csv(args.input)
        logger.info(f"已读取 {len(df)} 条关键词数据")
    except Exception as e:
        logger.error(f"读取文件时出错: {e}")
        return
    
    # 创建评分器
    scorer = KeywordScorer(
        volume_weight=args.volume_weight,
        growth_weight=args.growth_weight,
        kd_weight=args.kd_weight
    )
    
    # 丰富数据（可选）
    if args.enrich:
        df = scorer.enrich_with_ads_data(df)
    
    # 评分
    scored_df = scorer.score_keywords(df)
    
    # 过滤（可选）
    if args.min_score:
        scored_df = scorer.filter_keywords(scored_df, min_score=args.min_score)
        logger.info(f"过滤后剩余 {len(scored_df)} 条关键词")
    
    # 保存结果
    scorer.save_results(scored_df, args.output)


if __name__ == "__main__":
    main()