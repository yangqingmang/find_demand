#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
综合分析器
整合多种分析方法的综合分析器
"""

import pandas as pd
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from .base_analyzer import BaseAnalyzer

class ComprehensiveAnalyzer(BaseAnalyzer):
    """综合分析器，整合多种分析方法"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # 初始化新词检测器 - 使用单例模式
        try:
            from .new_word_detector_singleton import get_new_word_detector
            self.new_word_detector = get_new_word_detector()
        except Exception as e:
            self.new_word_detector = None
            self.logger.warning(f"新词检测器单例初始化失败: {e}")
        else:
            if self.new_word_detector:
                self.logger.info("新词检测器单例初始化成功")
    
    def analyze(self, keywords: List[str], **kwargs) -> Dict[str, Any]:
        """
        综合分析关键词
        
        Args:
            keywords: 关键词列表
            **kwargs: 其他参数
            
        Returns:
            综合分析结果
        """
        try:
            results = {
                'timestamp': datetime.now().isoformat(),
                'keywords_count': len(keywords),
                'analysis_results': {}
            }
            
            # 新词检测
            if self.new_word_detector and keywords:
                try:
                    # 将关键词转换为DataFrame格式
                    df = pd.DataFrame({'keyword': keywords})
                    new_word_results = self.new_word_detector.detect_new_words(df)
                    results['analysis_results']['new_word_detection'] = new_word_results
                except Exception as e:
                    self.logger.error(f"新词检测失败: {e}")
                    results['analysis_results']['new_word_detection'] = {'error': str(e)}
            
            return results
            
        except Exception as e:
            self.logger.error(f"综合分析失败: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'keywords_count': len(keywords) if keywords else 0
            }
    
    def get_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取分析结果摘要
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            分析摘要
        """
        try:
            summary = {
                'total_keywords': analysis_results.get('keywords_count', 0),
                'analysis_timestamp': analysis_results.get('timestamp'),
                'completed_analyses': []
            }
            
            # 统计完成的分析
            if 'analysis_results' in analysis_results:
                for analysis_type, result in analysis_results['analysis_results'].items():
                    if result and not result.get('error'):
                        summary['completed_analyses'].append(analysis_type)
            
            summary['total_analyses'] = len(summary['completed_analyses'])
            
            return summary
            
        except Exception as e:
            self.logger.error(f"生成摘要失败: {e}")
            return {'error': str(e)}