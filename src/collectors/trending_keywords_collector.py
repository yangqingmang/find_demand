#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendingKeywords.net 数据收集器
从 https://trendingkeywords.net/ 获取热门关键词数据
"""

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import random
from typing import List, Dict, Optional
import logging


class TrendingKeywordsCollector:
    """TrendingKeywords.net 数据收集器"""
    
    def __init__(self):
        self.base_url = "https://trendingkeywords.net/"
        self.session = self._create_session()
        self.ssl_retry_attempts = 3
        self.ssl_retry_backoff = 1.2
        
        # 设置日志
        self.logger = logging.getLogger(__name__)

    def _create_session(self) -> requests.Session:
        """Create a session with retry-aware adapters."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        retry_config = Retry(
            total=3,
            connect=3,
            read=2,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=None
        )
        adapter = HTTPAdapter(max_retries=retry_config, pool_maxsize=5, pool_block=True)
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session

    def _reset_session(self) -> None:
        """Recreate the underlying HTTP session after persistent TLS failures."""
        try:
            self.session.close()
        finally:
            self.session = self._create_session()

    def _request_with_retries(self, url: str, timeout: int = 10) -> requests.Response:
        """Perform a GET request with defensive TLS retries."""
        last_error: Optional[Exception] = None
        for attempt in range(1, self.ssl_retry_attempts + 1):
            try:
                return self.session.get(url, timeout=timeout)
            except requests.exceptions.SSLError as ssl_error:
                last_error = ssl_error
                self.logger.warning(
                    "TLS 握手异常 (%s/%s): %s", attempt, self.ssl_retry_attempts, ssl_error
                )
                self._reset_session()
                sleep_time = min(self.ssl_retry_backoff * attempt, 3)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            except requests.RequestException as request_error:
                last_error = request_error
                if attempt >= self.ssl_retry_attempts:
                    break
                sleep_time = min(self.ssl_retry_backoff * attempt, 3)
                if sleep_time > 0:
                    time.sleep(sleep_time)
        if last_error:
            raise last_error
        raise RuntimeError("请求未能成功且未捕获具体异常")
        
    def fetch_trending_keywords(self, max_pages: int = 3, delay_range: tuple = (1, 3)) -> pd.DataFrame:
        """
        获取热门关键词数据
        
        Args:
            max_pages: 最大抓取页数
            delay_range: 请求间隔时间范围(秒)
            
        Returns:
            包含关键词数据的DataFrame
        """
        all_keywords = []
        
        try:
            for page in range(1, max_pages + 1):
                self.logger.info(f"正在抓取第 {page} 页...")
                
                # 构建页面URL
                if page == 1:
                    url = self.base_url
                else:
                    url = f"{self.base_url}?page={page}"
                
                # 获取页面数据
                keywords = self._fetch_page_keywords(url)
                if keywords:
                    all_keywords.extend(keywords)
                    self.logger.info(f"第 {page} 页获取到 {len(keywords)} 个关键词")
                else:
                    self.logger.warning(f"第 {page} 页未获取到数据")
                    break
                
                # 随机延迟避免被封
                if page < max_pages:
                    delay = random.uniform(*delay_range)
                    time.sleep(delay)
            
            # 转换为DataFrame
            if all_keywords:
                df = pd.DataFrame(all_keywords)
                self.logger.info(f"总共获取到 {len(df)} 个关键词")
                return df
            else:
                self.logger.warning("未获取到任何关键词数据")
                return pd.DataFrame()
                
        except Exception as e:
            self.logger.error(f"获取热门关键词失败: {e}")
            return pd.DataFrame()
    
    def _fetch_page_keywords(self, url: str) -> List[Dict]:
        """
        获取单页关键词数据
        
        Args:
            url: 页面URL
            
        Returns:
            关键词数据列表
        """
        try:
            response = self._request_with_retries(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            keywords = []
            
            # 查找关键词条目
            # 根据网站结构，关键词通常在特定的容器中
            keyword_containers = self._find_keyword_containers(soup)
            
            for container in keyword_containers:
                keyword_data = self._extract_keyword_data(container)
                if keyword_data:
                    keywords.append(keyword_data)
            
            return keywords
            
        except requests.RequestException as e:
            self.logger.error(f"请求页面失败 {url}: {e}")
            return []
        except Exception as e:
            self.logger.error(f"解析页面失败 {url}: {e}")
            return []
    
    def _find_keyword_containers(self, soup: BeautifulSoup) -> List:
        """
        查找包含关键词的容器元素
        
        Args:
            soup: BeautifulSoup对象
            
        Returns:
            关键词容器列表
        """
        containers = []
        
        # 根据调试结果，查找包含搜索量的卡片容器
        # 每个关键词都在一个带有特定class的div容器中
        card_containers = soup.find_all('div', class_=lambda x: x and 'max-w-sm' in x and 'bg-white' in x and 'rounded-lg' in x)
        
        if card_containers:
            self.logger.info(f"找到 {len(card_containers)} 个卡片容器")
            return card_containers[:50]  # 限制数量
        
        # 备用方案：查找包含搜索量文本的元素
        volume_pattern = re.compile(r'\d+k?/Month', re.IGNORECASE)
        volume_elements = soup.find_all(string=volume_pattern)
        
        for element in volume_elements:
            # 向上查找卡片容器 (通常是3-4级父元素)
            parent = element.parent
            for _ in range(4):  # 向上查找4级
                if parent and parent.name == 'div':
                    classes = parent.get('class', [])
                    # 查找包含卡片样式的容器
                    if any('bg-white' in str(classes) or 'shadow' in str(classes) or 'rounded' in str(classes)):
                        if parent not in containers:
                            containers.append(parent)
                        break
                if parent:
                    parent = parent.parent
                else:
                    break
        
        return containers[:50]  # 限制数量避免过多
    
    def _extract_keyword_data(self, container) -> Optional[Dict]:
        """
        从容器元素中提取关键词数据
        
        Args:
            container: 包含关键词信息的HTML元素
            
        Returns:
            关键词数据字典或None
        """
        try:
            # 提取关键词名称
            keyword = self._extract_keyword_name(container)
            if not keyword:
                return None
            
            # 提取搜索量
            volume = self._extract_search_volume(container)
            
            # 提取描述
            description = self._extract_description(container)
            
            # 提取类别/标签
            category = self._extract_category(container)
            
            return {
                'keyword': keyword.strip(),
                'search_volume': volume,
                'volume_text': self._extract_volume_text(container),
                'description': description.strip() if description else '',
                'category': category.strip() if category else '',
                'source': 'TrendingKeywords.net',
                'query': keyword.strip()  # 为了兼容现有系统
            }
            
        except Exception as e:
            self.logger.debug(f"提取关键词数据失败: {e}")
            return None
    
    def _extract_keyword_name(self, container) -> Optional[str]:
        """提取关键词名称"""
        # 根据调试结果，关键词名称通常是容器中的第一行文本
        full_text = container.get_text()
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        if lines:
            # 第一行通常是关键词名称
            first_line = lines[0]
            
            # 清理文本，移除搜索量信息
            clean_line = re.sub(r'\(\d+k?/Month\)', '', first_line).strip()
            clean_line = re.sub(r'\d+k?/Month', '', clean_line).strip()
            
            # 验证是否为有效的关键词
            if not clean_line:
                return None
            if len(clean_line) <= 1 or len(clean_line) >= 100:
                return None
            if clean_line.startswith('http'):
                return None
            if re.match(r'^\d+$', clean_line):
                return None
            if 'Last 90 days' in clean_line or clean_line == 'Detail':
                return None
            return clean_line
        
        # 备用方案：尝试其他选择器
        selectors = [
            'h3', 'h4', 'h5',
            '.keyword-name', '.title', '.name',
            'strong', 'b'
        ]
        
        for selector in selectors:
            element = container.select_one(selector)
            if element:
                text = element.get_text().strip()
                # 清理文本，移除搜索量信息
                text = re.sub(r'\(\d+k?/Month\)', '', text).strip()
                text = re.sub(r'\d+k?/Month', '', text).strip()
                if text and len(text) > 1 and len(text) < 100:
                    return text
        
        return None
    
    def _extract_search_volume(self, container) -> int:
        """提取搜索量数值"""
        volume_text = self._extract_volume_text(container)
        if volume_text:
            # 提取数字
            match = re.search(r'(\d+(?:\.\d+)?)k?', volume_text, re.IGNORECASE)
            if match:
                num = float(match.group(1))
                # 如果包含k，乘以1000
                if 'k' in volume_text.lower():
                    num *= 1000
                return int(num)
        return 0
    
    def _extract_volume_text(self, container) -> Optional[str]:
        """提取搜索量文本"""
        text = container.get_text()
        # 查找搜索量模式
        match = re.search(r'\d+k?/Month', text, re.IGNORECASE)
        return match.group(0) if match else None
    
    def _extract_description(self, container) -> Optional[str]:
        """提取描述信息"""
        # 根据调试结果，描述通常是第三行文本
        full_text = container.get_text()
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        
        # 查找描述行（通常是较长的文本，不包含搜索量）
        for line in lines:
            # 跳过关键词名称、搜索量、链接文本
            if (re.search(r'\d+k?/Month', line, re.IGNORECASE) or
                'Last 90 days' in line or
                'Detail' == line.strip() or
                len(line) < 20):
                continue
            
            # 找到描述文本
            if len(line) > 20 and len(line) < 500:
                # 清理描述文本
                desc = re.sub(r'\d+k?/Month', '', line).strip()
                if desc:
                    return desc
        
        # 备用方案：查找特定元素
        desc_selectors = [
            '.description', '.desc', '.summary',
            'p', '.content', '.detail'
        ]
        
        for selector in desc_selectors:
            element = container.select_one(selector)
            if element:
                desc = element.get_text().strip()
                # 过滤掉搜索量信息
                desc = re.sub(r'\d+k?/Month', '', desc).strip()
                if desc and len(desc) > 10:
                    return desc
        
        return None
    
    def _extract_category(self, container) -> Optional[str]:
        """提取类别信息"""
        # 查找类别标签
        cat_selectors = [
            '.category', '.tag', '.label',
            '.badge', '.chip'
        ]
        
        for selector in cat_selectors:
            element = container.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return None
    
    def get_trending_keywords_for_analysis(self, max_keywords: int = 50) -> pd.DataFrame:
        """
        获取用于分析的热门关键词
        
        Args:
            max_keywords: 最大关键词数量
            
        Returns:
            格式化的关键词DataFrame
        """
        # 获取原始数据
        df = self.fetch_trending_keywords(max_pages=3)
        
        if df.empty:
            return pd.DataFrame(columns=['query'])
        
        # 按搜索量排序
        if 'search_volume' in df.columns:
            df = df.sort_values('search_volume', ascending=False)
        
        # 限制数量
        df = df.head(max_keywords)
        
        # 确保有query列用于后续分析
        if 'query' not in df.columns and 'keyword' in df.columns:
            df['query'] = df['keyword']
        
        try:
            from src.pipeline.cleaning.cleaner import clean_terms
            cleaned = clean_terms(df['query'].astype(str).tolist())
            if not cleaned:
                return pd.DataFrame(columns=['query'])
            return pd.DataFrame({'query': cleaned})
        except Exception:
            return df[['query']].copy()
    
    def save_results(self, df: pd.DataFrame, output_dir: str) -> str:
        """
        保存结果到文件
        
        Args:
            df: 关键词DataFrame
            output_dir: 输出目录
            
        Returns:
            保存的文件路径
        """
        import os
        from datetime import datetime
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trending_keywords_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        self.logger.info(f"结果已保存到: {filepath}")
        return filepath


def main():
    """测试函数"""
    collector = TrendingKeywordsCollector()
    
    print("🔍 开始获取 TrendingKeywords.net 数据...")
    df = collector.fetch_trending_keywords(max_pages=2)
    
    if not df.empty:
        print(f"✅ 成功获取 {len(df)} 个关键词")
        print("\n📊 样本数据:")
        print(df.head().to_string())
        
        # 保存结果
        output_file = collector.save_results(df, "output")
        print(f"\n📁 结果已保存到: {output_file}")
    else:
        print("❌ 未获取到数据")


if __name__ == "__main__":
    main()
