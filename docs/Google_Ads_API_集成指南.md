# Google Ads API 集成指南

## 概述

Google Ads API 可以提供真实的搜索量、CPC（每次点击成本）、竞争度等关键数据，是市场需求分析的重要数据源。本指南将详细说明如何申请和集成 Google Ads API。

## 1. 申请 Google Ads API 访问权限

### 1.1 前置条件

- 拥有 Google 账户
- 拥有 Google Ads 账户（即使没有投放广告也可以）
- 拥有 Google Cloud Platform 项目

### 1.2 申请步骤

#### 步骤1：创建 Google Cloud 项目
1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 记录项目ID，后续配置需要

#### 步骤2：启用 Google Ads API
1. 在 Google Cloud Console 中，转到 "API和服务" > "库"
2. 搜索 "Google Ads API"
3. 点击启用

#### 步骤3：创建服务账户
1. 转到 "API和服务" > "凭据"
2. 点击 "创建凭据" > "服务账户"
3. 填写服务账户详情
4. 下载 JSON 密钥文件，妥善保存

#### 步骤4：申请 Google Ads API 访问权限
1. **登录Google Ads账户**：访问 [Google Ads](https://ads.google.com/)
2. **进入API中心**：在Google Ads界面中，点击右上角的工具图标 → 设置 → API中心
3. **申请Developer Token**：
   - 点击"申请访问权限"或"Request access"
   - 填写申请表单，包括：
     - 应用程序名称（如：Market Research Tool）
     - 使用目的（如：关键词研究和市场分析）
     - 预期的API调用量
     - 联系信息
4. **提交申请**：完成表单后提交申请
5. **等待审核**：通常需要1-3个工作日，Google会通过邮件通知审核结果

**备用申请方法**：
如果在Google Ads界面中找不到API中心，可以尝试以下方法：
1. **直接访问申请表单**：[Google Ads API Access Request](https://support.google.com/google-ads/contact/api_access_request)
2. **通过Google Ads帮助中心**：搜索"Google Ads API access"
3. **联系Google Ads支持**：通过客服申请API访问权限

**申请前准备**：
- 确保Google Ads账户已完全设置（添加付款方式，即使不投放广告）
- 准备详细的使用说明（如：用于关键词研究、市场分析、SEO工具等）
- 确保有有效的联系方式接收审核结果

### 1.3 获取必要的配置信息

申请成功后，您需要获取以下信息：
- **Developer Token**：从 Google Ads 账户获取
- **Client ID** 和 **Client Secret**：从 Google Cloud Console 获取
- **Refresh Token**：通过 OAuth2 流程获取
- **Customer ID**：Google Ads 账户ID

## 2. 安装依赖包

```bash
pip install google-ads==22.1.0
pip install google-auth-oauthlib
```

## 3. 配置文件设置

### 3.1 更新 .env 模板

在 `config/.env.template` 中添加：

```env
# Google Ads API 配置
GOOGLE_ADS_DEVELOPER_TOKEN=your_developer_token_here
GOOGLE_ADS_CLIENT_ID=your_client_id_here
GOOGLE_ADS_CLIENT_SECRET=your_client_secret_here
GOOGLE_ADS_REFRESH_TOKEN=your_refresh_token_here
GOOGLE_ADS_CUSTOMER_ID=your_customer_id_here

# 可选：指定API版本
GOOGLE_ADS_API_VERSION=v15
```

### 3.2 更新配置管理

在 `src/config/settings.py` 中添加：

```python
@property
def GOOGLE_ADS_DEVELOPER_TOKEN(self):
    """Google Ads Developer Token"""
    return os.getenv('GOOGLE_ADS_DEVELOPER_TOKEN')

@property
def GOOGLE_ADS_CLIENT_ID(self):
    """Google Ads Client ID"""
    return os.getenv('GOOGLE_ADS_CLIENT_ID')

@property
def GOOGLE_ADS_CLIENT_SECRET(self):
    """Google Ads Client Secret"""
    return os.getenv('GOOGLE_ADS_CLIENT_SECRET')

@property
def GOOGLE_ADS_REFRESH_TOKEN(self):
    """Google Ads Refresh Token"""
    return os.getenv('GOOGLE_ADS_REFRESH_TOKEN')

@property
def GOOGLE_ADS_CUSTOMER_ID(self):
    """Google Ads Customer ID"""
    return os.getenv('GOOGLE_ADS_CUSTOMER_ID')

@property
def GOOGLE_ADS_API_VERSION(self):
    """Google Ads API Version"""
    return os.getenv('GOOGLE_ADS_API_VERSION', 'v15')

def validate(self):
    """验证配置是否完整"""
    missing = []
    
    # 现有验证...
    
    # Google Ads API 验证
    if not self.GOOGLE_ADS_DEVELOPER_TOKEN:
        missing.append('GOOGLE_ADS_DEVELOPER_TOKEN')
    if not self.GOOGLE_ADS_CLIENT_ID:
        missing.append('GOOGLE_ADS_CLIENT_ID')
    if not self.GOOGLE_ADS_CLIENT_SECRET:
        missing.append('GOOGLE_ADS_CLIENT_SECRET')
    if not self.GOOGLE_ADS_REFRESH_TOKEN:
        missing.append('GOOGLE_ADS_REFRESH_TOKEN')
    if not self.GOOGLE_ADS_CUSTOMER_ID:
        missing.append('GOOGLE_ADS_CUSTOMER_ID')
    
    # 其余验证逻辑...
```

## 4. 创建 Google Ads 数据采集器

创建 `src/collectors/ads_collector.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads 数据采集器
用于获取关键词的搜索量、CPC、竞争度等数据
"""

import pandas as pd
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from typing import List, Dict, Optional
import time

from src.config.settings import config
from src.utils.logger import Logger
from src.utils.exceptions import handle_api_errors

class AdsCollector:
    """Google Ads 数据采集器"""
    
    def __init__(self):
        """初始化采集器"""
        self.logger = Logger('logs/ads_collector.log')
        
        # 验证配置
        config.validate()
        
        # 初始化 Google Ads 客户端
        self.client = self._init_client()
        self.customer_id = config.GOOGLE_ADS_CUSTOMER_ID
        
    def _init_client(self) -> GoogleAdsClient:
        """初始化 Google Ads 客户端"""
        try:
            # 创建配置字典
            google_ads_config = {
                'developer_token': config.GOOGLE_ADS_DEVELOPER_TOKEN,
                'client_id': config.GOOGLE_ADS_CLIENT_ID,
                'client_secret': config.GOOGLE_ADS_CLIENT_SECRET,
                'refresh_token': config.GOOGLE_ADS_REFRESH_TOKEN,
                'use_proto_plus': True
            }
            
            client = GoogleAdsClient.load_from_dict(google_ads_config)
            self.logger.info("Google Ads 客户端初始化成功")
            return client
            
        except Exception as e:
            self.logger.error(f"Google Ads 客户端初始化失败: {e}")
            raise
    
    @handle_api_errors
    def get_keyword_ideas(self, keywords: List[str], geo_target: str = None) -> pd.DataFrame:
        """
        获取关键词创意和搜索量数据
        
        参数:
            keywords: 种子关键词列表
            geo_target: 地理位置目标
            
        返回:
            包含关键词数据的DataFrame
        """
        self.logger.info(f"开始获取关键词创意: {keywords}")
        
        keyword_plan_idea_service = self.client.get_service("KeywordPlanIdeaService")
        
        # 构建请求
        request = self.client.get_type("GenerateKeywordIdeasRequest")
        request.customer_id = self.customer_id
        
        # 设置关键词种子
        request.keyword_seed.keywords.extend(keywords)
        
        # 设置地理位置
        if geo_target:
            geo_target_constant = self._get_geo_target_constant(geo_target)
            if geo_target_constant:
                request.geo_target_constants.append(geo_target_constant)
        
        # 设置语言（中文）
        request.language = self._get_language_constant("zh")
        
        # 设置关键词规划网络
        request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
        
        try:
            # 发送请求
            keyword_ideas = keyword_plan_idea_service.generate_keyword_ideas(request=request)
            
            # 解析结果
            results = []
            for idea in keyword_ideas:
                keyword_data = {
                    'keyword': idea.text,
                    'avg_monthly_searches': self._get_monthly_searches(idea.keyword_idea_metrics),
                    'competition': self._get_competition_level(idea.keyword_idea_metrics),
                    'competition_index': self._get_competition_index(idea.keyword_idea_metrics),
                    'low_top_of_page_bid_micros': self._get_bid_micros(idea.keyword_idea_metrics, 'low'),
                    'high_top_of_page_bid_micros': self._get_bid_micros(idea.keyword_idea_metrics, 'high'),
                    'avg_cpc': self._calculate_avg_cpc(idea.keyword_idea_metrics)
                }
                results.append(keyword_data)
            
            df = pd.DataFrame(results)
            self.logger.info(f"成功获取 {len(df)} 个关键词的数据")
            return df
            
        except GoogleAdsException as ex:
            self.logger.error(f"Google Ads API 请求失败: {ex}")
            raise
    
    def _get_geo_target_constant(self, geo_code: str) -> Optional[str]:
        """获取地理位置常量"""
        geo_target_constant_service = self.client.get_service("GeoTargetConstantService")
        
        # 地区代码映射
        geo_mapping = {
            'US': '2840',  # 美国
            'GB': '2826',  # 英国
            'CN': '2156',  # 中国
            'DE': '2276',  # 德国
            'JP': '2392',  # 日本
            'KR': '2410',  # 韩国
        }
        
        if geo_code in geo_mapping:
            return f"geoTargetConstants/{geo_mapping[geo_code]}"
        
        return None
    
    def _get_language_constant(self, language_code: str) -> str:
        """获取语言常量"""
        language_mapping = {
            'zh': 'languageConstants/1018',  # 中文
            'en': 'languageConstants/1000',  # 英文
        }
        
        return language_mapping.get(language_code, 'languageConstants/1000')
    
    def _get_monthly_searches(self, metrics) -> int:
        """获取月搜索量"""
        if metrics and hasattr(metrics, 'avg_monthly_searches'):
            return metrics.avg_monthly_searches
        return 0
    
    def _get_competition_level(self, metrics) -> str:
        """获取竞争程度"""
        if metrics and hasattr(metrics, 'competition'):
            competition_enum = self.client.enums.KeywordPlanCompetitionEnum
            if metrics.competition == competition_enum.LOW:
                return 'LOW'
            elif metrics.competition == competition_enum.MEDIUM:
                return 'MEDIUM'
            elif metrics.competition == competition_enum.HIGH:
                return 'HIGH'
        return 'UNKNOWN'
    
    def _get_competition_index(self, metrics) -> float:
        """获取竞争指数"""
        if metrics and hasattr(metrics, 'competition_index'):
            return metrics.competition_index
        return 0.0
    
    def _get_bid_micros(self, metrics, bid_type: str) -> int:
        """获取出价（微单位）"""
        if not metrics:
            return 0
            
        if bid_type == 'low' and hasattr(metrics, 'low_top_of_page_bid_micros'):
            return metrics.low_top_of_page_bid_micros
        elif bid_type == 'high' and hasattr(metrics, 'high_top_of_page_bid_micros'):
            return metrics.high_top_of_page_bid_micros
        
        return 0
    
    def _calculate_avg_cpc(self, metrics) -> float:
        """计算平均CPC（美元）"""
        if not metrics:
            return 0.0
            
        low_bid = self._get_bid_micros(metrics, 'low')
        high_bid = self._get_bid_micros(metrics, 'high')
        
        if low_bid > 0 and high_bid > 0:
            # 转换微单位到美元（1美元 = 1,000,000微单位）
            avg_cpc = (low_bid + high_bid) / 2 / 1_000_000
            return round(avg_cpc, 2)
        
        return 0.0
    
    def batch_collect(self, keyword_groups: List[List[str]], geo_target: str = None) -> pd.DataFrame:
        """
        批量采集关键词数据
        
        参数:
            keyword_groups: 关键词组列表
            geo_target: 地理位置目标
            
        返回:
            合并后的DataFrame
        """
        all_results = []
        
        for i, keywords in enumerate(keyword_groups, 1):
            self.logger.info(f"处理关键词组 {i}/{len(keyword_groups)}: {keywords}")
            
            try:
                df = self.get_keyword_ideas(keywords, geo_target)
                all_results.append(df)
                
                # API限制：避免请求过于频繁
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"关键词组 {i} 处理失败: {e}")
                continue
        
        if all_results:
            combined_df = pd.concat(all_results, ignore_index=True)
            # 去重
            combined_df = combined_df.drop_duplicates(subset=['keyword'])
            self.logger.info(f"批量采集完成，共获取 {len(combined_df)} 个关键词")
            return combined_df
        
        return pd.DataFrame()

def main():
    """测试函数"""
    collector = AdsCollector()
    
    # 测试关键词
    test_keywords = ['ai tools', 'chatgpt', 'artificial intelligence']
    
    try:
        df = collector.get_keyword_ideas(test_keywords, geo_target='US')
        print(f"获取到 {len(df)} 个关键词数据")
        print(df.head())
        
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    main()
```

## 5. 集成到主分析器

在 `src/core/market_analyzer.py` 中集成 Google Ads 数据：

```python
# 在导入部分添加
from ..collectors.ads_collector import AdsCollector

# 在 MarketAnalyzer 类中添加方法
def _enrich_with_ads_data(self, df: pd.DataFrame, geo: str = '') -> pd.DataFrame:
    """使用 Google Ads 数据丰富关键词信息"""
    try:
        self.logger.info("开始使用 Google Ads 数据丰富关键词信息")
        
        ads_collector = AdsCollector()
        keywords = df['query'].tolist()
        
        # 分批处理（每批最多50个关键词）
        batch_size = 50
        keyword_batches = [keywords[i:i+batch_size] for i in range(0, len(keywords), batch_size)]
        
        ads_df = ads_collector.batch_collect(keyword_batches, geo_target=geo)
        
        if not ads_df.empty:
            # 合并数据
            df = df.merge(
                ads_df[['keyword', 'avg_monthly_searches', 'competition', 'avg_cpc']],
                left_on='query',
                right_on='keyword',
                how='left'
            )
            
            # 更新搜索量（如果 Google Ads 有数据）
            df['volume'] = df['avg_monthly_searches'].fillna(df['volume'])
            
            self.logger.info("Google Ads 数据丰富完成")
        
        return df
        
    except Exception as e:
        self.logger.error(f"Google Ads 数据丰富失败: {e}")
        return df
```

## 6. 更新配置工具

在 `setup_config.py` 中添加 Google Ads API 配置：

```python
def setup_google_ads_config():
    """设置 Google Ads API 配置"""
    print("=== Google Ads API 配置 ===")
    print("请输入 Google Ads API 配置信息：")
    
    developer_token = getpass.getpass("Developer Token: ").strip()
    client_id = input("Client ID: ").strip()
    client_secret = getpass.getpass("Client Secret: ").strip()
    refresh_token = getpass.getpass("Refresh Token: ").strip()
    customer_id = input("Customer ID (不含连字符): ").strip()
    
    # 验证输入
    if not all([developer_token, client_id, client_secret, refresh_token, customer_id]):
        print("错误：所有字段都不能为空")
        return False
    
    # 保存配置...
    return True
```

## 7. 测试和验证

创建测试脚本 `test_ads_integration.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Ads API 集成测试
"""

from src.collectors.ads_collector import AdsCollector
from src.config.settings import config

def test_ads_api():
    """测试 Google Ads API 连接"""
    try:
        # 显示配置状态
        config.show_config_status()
        
        # 创建采集器
        collector = AdsCollector()
        
        # 测试关键词
        test_keywords = ['ai tools']
        
        # 获取数据
        df = collector.get_keyword_ideas(test_keywords, geo_target='US')
        
        if not df.empty:
            print("✓ Google Ads API 集成测试成功")
            print(f"获取到 {len(df)} 个关键词数据")
            print(df.head())
            return True
        else:
            print("✗ 未获取到数据")
            return False
            
    except Exception as e:
        print(f"✗ Google Ads API 集成测试失败: {e}")
        return False

if __name__ == "__main__":
    test_ads_api()
```

## 8. 使用说明

### 8.1 配置 API 密钥

```bash
python setup_config.py
# 选择配置方式，输入 Google Ads API 相关信息
```

### 8.2 测试集成

```bash
python test_ads_integration.py
```

### 8.3 在主分析中使用

```bash
python main.py "ai tools" --geo US --use-ads-data
```

## 9. 注意事项

### 9.1 API 限制
- Google Ads API 有请求频率限制
- 建议在请求间添加适当延迟
- 监控 API 配额使用情况

### 9.2 数据准确性
- Google Ads 数据基于广告投放数据
- 搜索量可能与实际搜索量有差异
- 建议结合多个数据源进行分析

### 9.3 成本考虑
- Google Ads API 本身免费
- 但需要有 Google Ads 账户
- 建议设置预算限制

## 10. 故障排除

### 常见错误及解决方案

1. **认证失败**
   - 检查 Developer Token 是否正确
   - 确认 OAuth2 凭据配置正确
   - 验证 Customer ID 格式（不含连字符）

2. **API 配额超限**
   - 减少请求频率
   - 分批处理关键词
   - 联系 Google 申请提高配额

3. **数据为空**
   - 检查关键词是否有搜索量
   - 确认地理位置设置正确
   - 验证语言设置

通过以上步骤，您就可以成功集成 Google Ads API，获取真实的搜索量和 CPC 数据，大大提升市场需求分析的准确性！