#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示带时间戳目录的网站建设示例
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.website_builder.builder_core import IntentBasedWebsiteBuilder


def main():
    """演示如何使用带时间戳的目录功能"""
    
    print("🚀 演示带时间戳目录的网站建设功能")
    print("=" * 60)
    
    # 示例1: 默认项目名称
    print("\n📋 示例1: 使用默认项目名称")
    builder1 = IntentBasedWebsiteBuilder(
        intent_data_path='data/sample_keywords.csv',
        output_dir='output',
        config={'project_name': 'my_website'}
    )
    print(f"生成目录: {builder1.output_dir}")
    
    # 示例2: 自定义项目名称
    print("\n📋 示例2: 使用自定义项目名称")
    builder2 = IntentBasedWebsiteBuilder(
        intent_data_path='data/sample_keywords.csv',
        output_dir='output',
        config={'project_name': 'ecommerce_site'}
    )
    print(f"生成目录: {builder2.output_dir}")
    
    # 示例3: 多次运行，每次生成新目录
    print("\n📋 示例3: 多次运行生成不同目录")
    for i in range(3):
        builder = IntentBasedWebsiteBuilder(
            intent_data_path='data/sample_keywords.csv',
            output_dir='output',
            config={'project_name': f'test_site_{i+1}'}
        )
        print(f"第{i+1}次运行生成目录: {builder.output_dir}")
    
    print("\n✨ 目录命名规则:")
    print("- 格式: {project_name}_{YYYYMMDD_HHMMSS}")
    print("- 示例: my_website_20240108_143052")
    print("- 优势: 每次运行都生成独立目录，避免覆盖")
    
    print("\n📁 推荐的项目组织结构:")
    print("""
output/
├── my_website_20240108_143052/     # 第一次运行
│   ├── website_structure_2024-01-08.json
│   ├── content_plan_2024-01-08.json
│   └── website_source/
│       ├── index.html
│       └── styles.css
├── my_website_20240108_150230/     # 第二次运行
│   ├── website_structure_2024-01-08.json
│   ├── content_plan_2024-01-08.json
│   └── website_source/
│       ├── index.html
│       └── styles.css
└── ecommerce_site_20240108_151045/ # 不同项目
    ├── website_structure_2024-01-08.json
    ├── content_plan_2024-01-08.json
    └── website_source/
        ├── index.html
        └── styles.css
    """)

if __name__ == "__main__":
    main()