#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SEO工具集成采集器
支持 Semrush、Ahrefs、Similarweb 等主流SEO工具的API集成
"""

import pandas as pd
import requests
import time
import json
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod

from src.utils import Logger, FileUtils
try:
    from config.config_manager import get_config
    config = get_config()
except ImportError:
    from src.utils.simple_config import get_config
    config = get_config()
from src.utils.mock_data_generator import MockDataGenerator


class BaseSEOToolCollector(ABC):
    """SEO工具采集器基类"""
    
    def __init__(self, api_key: str, tool_name: str):
        self.api_key = api_key
        self.tool_name = tool_name
        self.logger = Logger()
        self.session = requests.Session()
        self.rate_limit_delay = 1.0  # 基础延迟1秒
        self.last_request_time = 0
    
    def _wait_for_rate_limit(self):
        """等待速率限制"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            wait_time = self.rate_limit_delay - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    @abstractmethod
    def get_keyword_data(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """获取关键词数据"""
        pass
    
    @abstractmethod
    def get_competitor_keywords(self, domain: str, **kwargs) -> pd.DataFrame:
        """获取竞争对手关键词"""
        pass


class SemrushCollector(BaseSEOToolCollector):
    """Semrush API 采集器"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "Semrush")
        self.base_url = "https://api.semrush.com/"
        self.rate_limit_delay = 0.1  # Semrush允许每秒10个请求
    
    def get_keyword_data(self, keyword: str, database: str = "us", **kwargs) -> Dict[str, Any]:
        """
        获取关键词数据
        
        参数:
            keyword (str): 关键词
            database (str): 数据库代码，如'us', 'uk', 'de'等
        """
        try:
            self.logger.info(f"🔍 Semrush: 获取关键词 '{keyword}' 数据...")
            
            # 如果启用模拟模式
            if config.MOCK_MODE:
                return self._generate_mock_keyword_data(keyword)
            
            self._wait_for_rate_limit()
            
            # Semrush Keyword Overview API
            params = {
                'type': 'phrase_this',
                'key': self.api_key,
                'phrase': keyword,
                'database': database,
                'export_columns': 'Ph,Nq,Cp,Co,Nr,Td'
            }
            
            response = self.session.get(f"{self.base_url}reports/v1/projects/", params=params)
            
            if response.status_code == 200:
                data = self._parse_semrush_response(response.text)
                self.logger.info(f"✓ Semrush: 成功获取 '{keyword}' 数据")
                return {
                    'keyword': keyword,
                    'source': 'semrush',
                    'data': data,
                    'status': 'success'
                }
            else:
                self.logger.error(f"❌ Semrush API错误: {response.status_code}")
                return self._generate_mock_keyword_data(keyword)
                
        except Exception as e:
            self.logger.error(f"❌ Semrush采集错误: {e}")
            return self._generate_mock_keyword_data(keyword)
    
    def get_competitor_keywords(self, domain: str, database: str = "us", limit: int = 100) -> pd.DataFrame:
        """获取竞争对手关键词"""
        try:
            self.logger.info(f"🔍 Semrush: 获取域名 '{domain}' 的关键词...")
            
            if config.MOCK_MODE:
                return self._generate_mock_competitor_data(domain, limit)
            
            self._wait_for_rate_limit()
            
            params = {
                'type': 'domain_organic',
                'key': self.api_key,
                'domain': domain,
                'database': database,
                'limit': limit,
                'export_columns': 'Ph,Po,Pp,Pd,Nq,Cp,Ur,Tr,Tc,Co,Nr,Td'
            }
            
            response = self.session.get(f"{self.base_url}reports/v1/projects/", params=params)
            
            if response.status_code == 200:
                df = self._parse_semrush_organic_response(response.text)
                self.logger.info(f"✓ Semrush: 成功获取 {len(df)} 个关键词")
                return df
            else:
                self.logger.error(f"❌ Semrush API错误: {response.status_code}")
                return self._generate_mock_competitor_data(domain, limit)
                
        except Exception as e:
            self.logger.error(f"❌ Semrush采集错误: {e}")
            return self._generate_mock_competitor_data(domain, limit)
    
    def _parse_semrush_response(self, response_text: str) -> Dict:
        """解析Semrush响应"""
        lines = response_text.strip().split('\n')
        if len(lines) < 2:
            return {}
        
        headers = lines[0].split(';')
        data = lines[1].split(';') if len(lines) > 1 else []
        
        result = {}
        for i, header in enumerate(headers):
            if i < len(data):
                result[header] = data[i]
        
        return result
    
    def _parse_semrush_organic_response(self, response_text: str) -> pd.DataFrame:
        """解析Semrush有机关键词响应"""
        lines = response_text.strip().split('\n')
        if len(lines) < 2:
            return pd.DataFrame()
        
        headers = lines[0].split(';')
        data_rows = []
        
        for line in lines[1:]:
            if line.strip():
                data_rows.append(line.split(';'))
        
        return pd.DataFrame(data_rows, columns=headers)
    
    def _generate_mock_keyword_data(self, keyword: str) -> Dict:
        """生成模拟关键词数据"""
        mock_generator = MockDataGenerator()
        mock_df = mock_generator.generate_trends_data([keyword])
        
        return {
            'keyword': keyword,
            'source': 'semrush_mock',
            'data': {
                'Ph': keyword,
                'Nq': '12100',  # 搜索量
                'Cp': '2.45',   # CPC
                'Co': '0.67',   # 竞争度
                'Nr': '1250000', # 搜索结果数
                'Td': '45'      # 趋势
            },
            'status': 'mock'
        }
    
    def _generate_mock_competitor_data(self, domain: str, limit: int) -> pd.DataFrame:
        """生成模拟竞争对手数据"""
        mock_generator = MockDataGenerator()
        keywords = [f"{domain} keyword {i}" for i in range(1, min(limit + 1, 51))]
        mock_results = mock_generator.generate_trends_data(keywords)
        
        all_data = []
        for keyword, df in mock_results.items():
            if not df.empty:
                for _, row in df.iterrows():
                    all_data.append({
                        'Ph': row['query'],
                        'Po': f"{len(all_data) + 1}",  # 排名
                        'Nq': str(row['value'] * 100),  # 搜索量
                        'Cp': f"{2.0 + (len(all_data) * 0.1):.2f}",  # CPC
                        'Ur': f"https://{domain}/page{len(all_data) + 1}",
                        'domain': domain
                    })
        
        return pd.DataFrame(all_data[:limit])


class AhrefsCollector(BaseSEOToolCollector):
    """Ahrefs API 采集器"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "Ahrefs")
        self.base_url = "https://apiv2.ahrefs.com/"
        self.rate_limit_delay = 2.0  # Ahrefs限制较严格
    
    def get_keyword_data(self, keyword: str, country: str = "us", **kwargs) -> Dict[str, Any]:
        """获取关键词数据"""
        try:
            self.logger.info(f"🔍 Ahrefs: 获取关键词 '{keyword}' 数据...")
            
            if config.MOCK_MODE:
                return self._generate_mock_keyword_data(keyword)
            
            self._wait_for_rate_limit()
            
            params = {
                'token': self.api_key,
                'from': 'keywords_explorer',
                'target': keyword,
                'country': country,
                'mode': 'exact'
            }
            
            response = self.session.get(f"{self.base_url}keywords-explorer", params=params)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✓ Ahrefs: 成功获取 '{keyword}' 数据")
                return {
                    'keyword': keyword,
                    'source': 'ahrefs',
                    'data': data,
                    'status': 'success'
                }
            else:
                self.logger.error(f"❌ Ahrefs API错误: {response.status_code}")
                return self._generate_mock_keyword_data(keyword)
                
        except Exception as e:
            self.logger.error(f"❌ Ahrefs采集错误: {e}")
            return self._generate_mock_keyword_data(keyword)
    
    def get_competitor_keywords(self, domain: str, country: str = "us", limit: int = 100) -> pd.DataFrame:
        """获取竞争对手关键词"""
        try:
            self.logger.info(f"🔍 Ahrefs: 获取域名 '{domain}' 的关键词...")
            
            if config.MOCK_MODE:
                return self._generate_mock_competitor_data(domain, limit)
            
            self._wait_for_rate_limit()
            
            params = {
                'token': self.api_key,
                'from': 'ahrefs_rank',
                'target': domain,
                'country': country,
                'limit': limit
            }
            
            response = self.session.get(f"{self.base_url}site-explorer", params=params)
            
            if response.status_code == 200:
                data = response.json()
                df = self._parse_ahrefs_response(data)
                self.logger.info(f"✓ Ahrefs: 成功获取 {len(df)} 个关键词")
                return df
            else:
                self.logger.error(f"❌ Ahrefs API错误: {response.status_code}")
                return self._generate_mock_competitor_data(domain, limit)
                
        except Exception as e:
            self.logger.error(f"❌ Ahrefs采集错误: {e}")
            return self._generate_mock_competitor_data(domain, limit)
    
    def _parse_ahrefs_response(self, data: Dict) -> pd.DataFrame:
        """解析Ahrefs响应"""
        if 'keywords' in data:
            return pd.DataFrame(data['keywords'])
        return pd.DataFrame()
    
    def _generate_mock_keyword_data(self, keyword: str) -> Dict:
        """生成模拟关键词数据"""
        return {
            'keyword': keyword,
            'source': 'ahrefs_mock',
            'data': {
                'keyword': keyword,
                'volume': 8900,
                'difficulty': 45,
                'cpc': 3.20,
                'clicks': 5600,
                'return_rate': 0.23
            },
            'status': 'mock'
        }
    
    def _generate_mock_competitor_data(self, domain: str, limit: int) -> pd.DataFrame:
        """生成模拟竞争对手数据"""
        mock_generator = MockDataGenerator()
        keywords = [f"{domain} ahrefs keyword {i}" for i in range(1, min(limit + 1, 51))]
        mock_results = mock_generator.generate_trends_data(keywords)
        
        all_data = []
        for keyword, df in mock_results.items():
            if not df.empty:
                for _, row in df.iterrows():
                    all_data.append({
                        'keyword': row['query'],
                        'position': len(all_data) + 1,
                        'volume': row['value'] * 150,
                        'difficulty': min(100, 20 + (len(all_data) * 2)),
                        'url': f"https://{domain}/page{len(all_data) + 1}",
                        'domain': domain
                    })
        
        return pd.DataFrame(all_data[:limit])


class SimilarwebCollector(BaseSEOToolCollector):
    """Similarweb API 采集器"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "Similarweb")
        self.base_url = "https://api.similarweb.com/v1/"
        self.rate_limit_delay = 1.5
    
    def get_keyword_data(self, keyword: str, country: str = "us", **kwargs) -> Dict[str, Any]:
        """获取关键词数据"""
        try:
            self.logger.info(f"🔍 Similarweb: 获取关键词 '{keyword}' 数据...")
            
            if config.MOCK_MODE:
                return self._generate_mock_keyword_data(keyword)
            
            self._wait_for_rate_limit()
            
            headers = {'api-key': self.api_key}
            params = {
                'keyword': keyword,
                'country': country,
                'start_date': '2024-01',
                'end_date': '2024-12'
            }
            
            response = self.session.get(
                f"{self.base_url}keywords/{keyword}/analysis",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"✓ Similarweb: 成功获取 '{keyword}' 数据")
                return {
                    'keyword': keyword,
                    'source': 'similarweb',
                    'data': data,
                    'status': 'success'
                }
            else:
                self.logger.error(f"❌ Similarweb API错误: {response.status_code}")
                return self._generate_mock_keyword_data(keyword)
                
        except Exception as e:
            self.logger.error(f"❌ Similarweb采集错误: {e}")
            return self._generate_mock_keyword_data(keyword)
    
    def get_competitor_keywords(self, domain: str, country: str = "us", limit: int = 100) -> pd.DataFrame:
        """获取竞争对手关键词"""
        try:
            self.logger.info(f"🔍 Similarweb: 获取域名 '{domain}' 的关键词...")
            
            if config.MOCK_MODE:
                return self._generate_mock_competitor_data(domain, limit)
            
            self._wait_for_rate_limit()
            
            headers = {'api-key': self.api_key}
            params = {
                'domain': domain,
                'country': country,
                'limit': limit
            }
            
            response = self.session.get(
                f"{self.base_url}website/{domain}/search-keywords",
                headers=headers,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                df = self._parse_similarweb_response(data)
                self.logger.info(f"✓ Similarweb: 成功获取 {len(df)} 个关键词")
                return df
            else:
                self.logger.error(f"❌ Similarweb API错误: {response.status_code}")
                return self._generate_mock_competitor_data(domain, limit)
                
        except Exception as e:
            self.logger.error(f"❌ Similarweb采集错误: {e}")
            return self._generate_mock_competitor_data(domain, limit)
    
    def _parse_similarweb_response(self, data: Dict) -> pd.DataFrame:
        """解析Similarweb响应"""
        if 'data' in data:
            return pd.DataFrame(data['data'])
        return pd.DataFrame()
    
    def _generate_mock_keyword_data(self, keyword: str) -> Dict:
        """生成模拟关键词数据"""
        return {
            'keyword': keyword,
            'source': 'similarweb_mock',
            'data': {
                'keyword': keyword,
                'volume': 15600,
                'trend': 'rising',
                'competition': 'medium',
                'traffic_share': 0.15
            },
            'status': 'mock'
        }
    
    def _generate_mock_competitor_data(self, domain: str, limit: int) -> pd.DataFrame:
        """生成模拟竞争对手数据"""
        mock_generator = MockDataGenerator()
        keywords = [f"{domain} similarweb keyword {i}" for i in range(1, min(limit + 1, 51))]
        mock_results = mock_generator.generate_trends_data(keywords)
        
        all_data = []
        for keyword, df in mock_results.items():
            if not df.empty:
                for _, row in df.iterrows():
                    all_data.append({
                        'keyword': row['query'],
                        'volume': row['value'] * 200,
                        'traffic_share': round(0.01 + (len(all_data) * 0.005), 3),
                        'trend': 'stable' if len(all_data) % 3 == 0 else 'rising',
                        'domain': domain
                    })
        
        return pd.DataFrame(all_data[:limit])


class IntegratedSEOCollector:
    """集成SEO工具采集器"""
    
    def __init__(self):
        self.logger = Logger()
        self.collectors = {}
        self._initialize_collectors()
    
    def _initialize_collectors(self):
        """初始化各个采集器"""
        try:
            # 从配置中获取API密钥
            semrush_key = getattr(config, 'SEMRUSH_API_KEY', None)
            ahrefs_key = getattr(config, 'AHREFS_API_KEY', None)
            similarweb_key = getattr(config, 'SIMILARWEB_API_KEY', None)
            
            if semrush_key:
                self.collectors['semrush'] = SemrushCollector(semrush_key)
                self.logger.info("✓ Semrush采集器已初始化")
            
            if ahrefs_key:
                self.collectors['ahrefs'] = AhrefsCollector(ahrefs_key)
                self.logger.info("✓ Ahrefs采集器已初始化")
            
            if similarweb_key:
                self.collectors['similarweb'] = SimilarwebCollector(similarweb_key)
                self.logger.info("✓ Similarweb采集器已初始化")
            
            if not self.collectors:
                self.logger.warning("⚠️ 未配置任何SEO工具API密钥，将使用模拟数据")
                
        except Exception as e:
            self.logger.error(f"❌ 初始化SEO采集器失败: {e}")
    
    def get_comprehensive_keyword_data(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """获取综合关键词数据"""
        results = {
            'keyword': keyword,
            'sources': {},
            'summary': {},
            'timestamp': time.time()
        }
        
        # 从所有可用的采集器获取数据
        for tool_name, collector in self.collectors.items():
            try:
                data = collector.get_keyword_data(keyword, **kwargs)
                results['sources'][tool_name] = data
                self.logger.info(f"✓ {tool_name}: 已获取 '{keyword}' 数据")
            except Exception as e:
                self.logger.error(f"❌ {tool_name}: 获取 '{keyword}' 数据失败: {e}")
        
        # 生成综合摘要
        results['summary'] = self._generate_summary(results['sources'])
        
        return results
    
    def get_competitor_analysis(self, domain: str, **kwargs) -> Dict[str, pd.DataFrame]:
        """获取竞争对手分析"""
        results = {}
        
        for tool_name, collector in self.collectors.items():
            try:
                df = collector.get_competitor_keywords(domain, **kwargs)
                results[tool_name] = df
                self.logger.info(f"✓ {tool_name}: 已获取 '{domain}' 竞争对手数据")
            except Exception as e:
                self.logger.error(f"❌ {tool_name}: 获取 '{domain}' 竞争对手数据失败: {e}")
        
        return results
    
    def _generate_summary(self, sources: Dict) -> Dict:
        """生成数据摘要"""
        summary = {
            'available_sources': list(sources.keys()),
            'data_quality': 'high' if len(sources) >= 2 else 'medium',
            'recommendations': []
        }
        
        # 添加基于数据源的建议
        if 'semrush' in sources:
            summary['recommendations'].append('使用Semrush数据进行关键词难度分析')
        if 'ahrefs' in sources:
            summary['recommendations'].append('使用Ahrefs数据进行反向链接分析')
        if 'similarweb' in sources:
            summary['recommendations'].append('使用Similarweb数据进行流量分析')
        
        return summary
    
    def save_results(self, results: Dict, output_dir: str = 'data/seo_tools'):
        """保存结果"""
        try:
            import os
            os.makedirs(output_dir, exist_ok=True)
            
            keyword = results.get('keyword', 'unknown')
            filename = f"seo_analysis_{keyword}_{int(time.time())}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"✓ 结果已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"❌ 保存结果失败: {e}")
            return None


# 便捷函数
def create_seo_collector() -> IntegratedSEOCollector:
    """创建集成SEO采集器"""
    return IntegratedSEOCollector()


def analyze_keyword_with_seo_tools(keyword: str, **kwargs) -> Dict[str, Any]:
    """使用SEO工具分析关键词"""
    collector = create_seo_collector()
    return collector.get_comprehensive_keyword_data(keyword, **kwargs)


def analyze_competitor_with_seo_tools(domain: str, **kwargs) -> Dict[str, pd.DataFrame]:
    """使用SEO工具分析竞争对手"""
    collector = create_seo_collector()
    return collector.get_competitor_analysis(domain, **kwargs)


if __name__ == "__main__":
    # 测试集成SEO采集器
    print("=== 测试集成SEO工具采集器 ===")
    
    collector = IntegratedSEOCollector()
    
    # 测试关键词分析
    print("\n1. 测试关键词分析:")
    keyword_results = collector.get_comprehensive_keyword_data("AI tools")
    print(f"   关键词: {keyword_results['keyword']}")
    print(f"   数据源: {list(keyword_results['sources'].keys())}")
    print(f"   数据质量: {keyword_results['summary']['data_quality']}")
    
    # 测试竞争对手分析
    print("\n2. 测试竞争对手分析:")
    competitor_results = collector.get_competitor_analysis("openai.com")
    print(f"   域名: openai.com")
    print(f"   数据源: {list(competitor_results.keys())}")
    for tool, df in competitor_results.items():
        print(f"   {tool}: {len(df)} 个关键词")
    
    print("\n✅ 测试完成!")