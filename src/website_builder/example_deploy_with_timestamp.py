#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
演示带时间戳目录的完整建站和部署流程
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.website_builder.builder_core import IntentBasedWebsiteBuilder


def main():
    """演示完整的建站和部署流程"""
    
    print("🚀 演示带时间戳目录的完整建站和部署流程")
    print("=" * 60)
    
    # 配置示例
    configs = [
        {
            'project_name': 'ecommerce_site',
            'description': '电商网站示例'
        },
        {
            'project_name': 'blog_platform',
            'description': '博客平台示例'
        },
        {
            'project_name': 'corporate_website',
            'description': '企业官网示例'
        }
    ]
    
    for i, config in enumerate(configs, 1):
        print(f"\n📋 示例{i}: {config['description']}")
        print("-" * 40)
        
        # 创建建站工具实例
        builder = IntentBasedWebsiteBuilder(
            intent_data_path='data/sample_keywords.csv',
            output_dir='output',
            config={
                'project_name': config['project_name'],
                'deployment_config_path': 'deployment_config.json'
            }
        )
        
        print(f"📁 项目目录: {builder.output_dir}")
        
        # 模拟建站流程
        print("🔄 执行建站流程...")
        
        # 1. 加载意图数据（模拟）
        print("  ✅ 意图数据加载完成")
        
        # 2. 生成网站结构（模拟）
        print("  ✅ 网站结构生成完成")
        
        # 3. 创建内容计划（模拟）
        print("  ✅ 内容计划创建完成")
        
        # 4. 生成网站源代码（模拟）
        source_dir = os.path.join(builder.output_dir, 'website_source')
        os.makedirs(source_dir, exist_ok=True)
        
        # 创建示例HTML文件
        with open(os.path.join(source_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['description']}</title>
</head>
<body>
    <h1>{config['description']}</h1>
    <p>项目目录: {os.path.basename(builder.output_dir)}</p>
    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</body>
</html>""")
        
        print(f"  ✅ 网站源代码生成完成: {source_dir}")
        
        # 5. 模拟部署配置
        deployment_configs = [
            {
                'name': 'Vercel',
                'deployer': 'vercel',
                'config': {
                    'project_name': config['project_name'],
                    'custom_domain': f"{config['project_name']}.example.com"
                }
            },
            {
                'name': 'Cloudflare Pages',
                'deployer': 'cloudflare',
                'config': {
                    'project_name': config['project_name'],
                    'custom_domain': f"{config['project_name']}.pages.dev"
                }
            }
        ]
        
        print("🌐 可用的部署选项:")
        for j, deploy_config in enumerate(deployment_configs, 1):
            print(f"  {j}. {deploy_config['name']}")
            print(f"     项目名: {deploy_config['config']['project_name']}")
            print(f"     域名: {deploy_config['config']['custom_domain']}")
        
        print(f"\n📊 项目信息总结:")
        print(f"  - 项目名称: {config['project_name']}")
        print(f"  - 项目目录: {os.path.basename(builder.output_dir)}")
        print(f"  - 源代码路径: {source_dir}")
        print(f"  - 配置文件: deployment_config.json")
    
    print("\n" + "=" * 60)
    print("🎯 使用说明:")
    print("""
1. 每次运行都会生成带时间戳的独立目录
2. 目录格式: {project_name}_{YYYYMMDD_HHMMSS}
3. 支持多个项目并行开发
4. 部署时会自动识别项目信息

命令行使用示例:
python -m src.website_builder.intent_based_website_builder \\
  --input data/keywords.csv \\
  --output output \\
  --project-name my_website \\
  --action all

部署示例:
python -m src.website_builder.intent_based_website_builder \\
  --input data/keywords.csv \\
  --output output \\
  --project-name my_website \\
  --action deploy \\
  --deployer vercel \\
  --deployment-config deployment_config.json
    """)
    
    print("\n📁 生成的目录结构:")
    print("""
output/
├── ecommerce_site_20240108_143052/
│   ├── website_structure_2024-01-08.json
│   ├── content_plan_2024-01-08.json
│   ├── deployment_info.json
│   └── website_source/
│       └── index.html
├── blog_platform_20240108_143053/
│   ├── website_structure_2024-01-08.json
│   ├── content_plan_2024-01-08.json
│   └── website_source/
│       └── index.html
├── corporate_website_20240108_143054/
│   ├── website_structure_2024-01-08.json
│   ├── content_plan_2024-01-08.json
│   └── website_source/
│       └── index.html
└── deployment_history.json  # 全局部署历史
    """)


if __name__ == "__main__":
    main()