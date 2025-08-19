# 工具模块 (Utils)

## 概述

工具模块包含项目的辅助函数和通用工具，为其他模块提供基础支持。

**注意**: 项目配置管理已迁移到 `src/config/settings.py`，支持更安全的API密钥管理。

## 历史说明

此模块原本包含配置管理功能，现已重构为更安全的配置系统：
- 旧配置文件：`src/utils/config.py` (已删除)
- 新配置系统：`src/config/settings.py`

新配置系统的优势：
- 支持多种配置源（环境变量、.env文件、用户配置）
- 安全的API密钥管理
- 配置优先级管理
- 更好的错误处理和验证

#### 主要配置

**默认配置 (DEFAULT_CONFIG)**
```python
{
    # 分析参数
    'timeframe': 'today 3-m',      # 默认时间范围
    'geo': '',                     # 默认地区（全球）
    'min_score': 10,               # 最低评分过滤
    'output_dir': 'data',          # 输出目录
    
    # 评分权重
    'volume_weight': 0.4,          # 搜索量权重
    'growth_weight': 0.4,          # 增长率权重
    'kd_weight': 0.2,              # 关键词难度权重
    
    # 高分关键词阈值
    'high_score_threshold': 70,
    
    # API配置
    'request_timeout': 30,         # 请求超时时间（秒）
    'retry_attempts': 3,           # 重试次数
    'retry_delay': 2,              # 重试延迟（秒）
    
    # 输出配置
    'save_intermediate_results': True,  # 是否保存中间结果
    'generate_charts': False,           # 是否生成图表
    'export_formats': ['csv', 'json'],  # 导出格式
}
```

**地区代码映射 (GEO_CODES)**
```python
{
    '全球': '',
    '美国': 'US',
    '英国': 'GB',
    '加拿大': 'CA',
    '澳大利亚': 'AU',
    '德国': 'DE',
    '法国': 'FR',
    '日本': 'JP',
    '韩国': 'KR',
    '中国': 'CN',
    '印度': 'IN',
    '巴西': 'BR',
    '墨西哥': 'MX',
    '南非': 'ZA',
}
```

**时间范围选项 (TIMEFRAME_OPTIONS)**
```python
{
    '过去7天': 'now 7-d',
    '过去1个月': 'now 1-m',
    '过去3个月': 'now 3-m',
    '过去12个月': 'now 12-m',
    '过去5年': 'now 5-y',
}
```

**搜索意图类型 (INTENT_TYPES)**
```python
{
    'I': '信息型 (Informational)',
    'N': '导航型 (Navigational)', 
    'C': '商业型 (Commercial)',
    'E': '交易型 (Transactional)',
    'B': '行为型 (Behavioral)'
}
```

**评分等级 (SCORE_GRADES)**
```python
{
    'A': {'min': 80, 'color': '🟢', 'desc': '优秀'},
    'B': {'min': 60, 'color': '🟡', 'desc': '良好'},
    'C': {'min': 40, 'color': '🟠', 'desc': '一般'},
    'D': {'min': 20, 'color': '🔴', 'desc': '较差'},
    'F': {'min': 0, 'color': '⚫', 'desc': '很差'}
}
```

#### 辅助函数

**get_score_grade(score)**
```python
# 根据分数获取等级
grade, info = get_score_grade(75)
print(f"等级: {grade}, 描述: {info['desc']}, 颜色: {info['color']}")
# 输出: 等级: B, 描述: 良好, 颜色: 🟡
```

**get_geo_code(geo_name)**
```python
# 根据地区名称获取代码
code = get_geo_code('美国')
print(code)  # 输出: US
```

**get_timeframe_code(timeframe_name)**
```python
# 根据时间范围名称获取代码
code = get_timeframe_code('过去3个月')
print(code)  # 输出: today 3-m
```

#### 使用方法

```python
from src.utils.config import (
    DEFAULT_CONFIG, 
    GEO_CODES, 
    get_score_grade,
    get_geo_code
)

# 使用默认配置
output_dir = DEFAULT_CONFIG['output_dir']
min_score = DEFAULT_CONFIG['min_score']

# 获取地区代码
us_code = get_geo_code('美国')

# 获取评分等级
grade, info = get_score_grade(85)
```

## 配置管理最佳实践

### 1. 环境配置

可以通过环境变量覆盖默认配置：

```python
import os
from src.utils.config import DEFAULT_CONFIG

# 从环境变量读取配置
config = DEFAULT_CONFIG.copy()
config['output_dir'] = os.getenv('OUTPUT_DIR', config['output_dir'])
config['min_score'] = int(os.getenv('MIN_SCORE', config['min_score']))
```

### 2. 配置文件

支持从JSON文件加载配置：

```python
import json
from src.utils.config import DEFAULT_CONFIG

def load_config(config_file='config.json'):
    """从文件加载配置"""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
        
        # 合并配置
        config = DEFAULT_CONFIG.copy()
        config.update(user_config)
        return config
    except FileNotFoundError:
        return DEFAULT_CONFIG
```

### 3. 配置验证

添加配置验证确保参数合理：

```python
def validate_config(config):
    """验证配置参数"""
    # 验证权重总和
    weights = ['volume_weight', 'growth_weight', 'kd_weight']
    total_weight = sum(config[w] for w in weights)
    if not (0.99 <= total_weight <= 1.01):
        raise ValueError(f"权重总和应为1.0，当前为{total_weight}")
    
    # 验证分数范围
    if not (0 <= config['min_score'] <= 100):
        raise ValueError("最低评分应在0-100范围内")
    
    # 验证地区代码
    if config['geo'] and config['geo'] not in GEO_CODES.values():
        raise ValueError(f"无效的地区代码: {config['geo']}")
    
    return True
```

## 扩展配置

### 添加新的地区代码

```python
# 在config.py中添加新地区
GEO_CODES.update({
    '俄罗斯': 'RU',
    '意大利': 'IT',
    '西班牙': 'ES',
})
```

### 添加新的时间范围

```python
# 添加自定义时间范围
TIMEFRAME_OPTIONS.update({
    '过去6个月': 'today 6-m',
    '过去2年': 'today 2-y',
})
```

### 添加新的评分等级

```python
# 添加更细粒度的评分等级
SCORE_GRADES.update({
    'S': {'min': 90, 'color': '⭐', 'desc': '卓越'},
    'A+': {'min': 85, 'color': '🟢', 'desc': '优秀+'},
})
```

## 配置文件示例

**config.json**
```json
{
  "output_dir": "results",
  "min_score": 20,
  "volume_weight": 0.5,
  "growth_weight": 0.3,
  "kd_weight": 0.2,
  "high_score_threshold": 80,
  "request_timeout": 60,
  "retry_attempts": 5,
  "generate_charts": true,
  "export_formats": ["csv", "json", "xlsx"]
}
```

## 注意事项

1. **权重平衡** - 确保所有权重参数总和为1.0
2. **参数范围** - 验证数值参数在合理范围内
3. **向后兼容** - 添加新配置时保持向后兼容性
4. **文档同步** - 修改配置时同步更新文档
5. **安全性** - 敏感配置（如API密钥）应通过环境变量管理

## 依赖关系

配置模块是基础模块，被其他所有模块依赖：

- **core.market_analyzer** - 使用默认配置和权重设置
- **collectors.trends_collector** - 使用地区代码和时间范围
- **analyzers.keyword_scorer** - 使用评分权重和等级定义
- **analyzers.intent_analyzer** - 使用意图类型定义

通过集中管理配置，确保整个项目的一致性和可维护性。