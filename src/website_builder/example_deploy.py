#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网站建设和部署完整示例
"""

import os
import sys

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.website_builder.builder_core import IntentBasedWebsiteBuilder


def main():
    """完整的建站和部署示例"""
    
    print("🚀 开始基于搜索意图的网站建设和部署流程")
    print("=" * 60)
    
    # 1. 初始化建站工具
    print("\n📋 步骤1: 初始化建站工具")
    
    config = {
        'deployment_config_path': 'deployment_config.json'  # 部署配置文件路径
    }
    
    builder = IntentBasedWebsiteBuilder(
        intent_data_path='data/keywords.csv',  # 关键词数据文件
        output_dir='output/my_website',        # 输出目录
        config=config
    )
    
    # 2. 加载意图数据
    print("\n📊 步骤2: 加载意图数据")
    if not builder.load_intent_data():
        print("❌ 意图数据加载失败")
        return 1
    
    # 3. 生成网站结构
    print("\n🏗️ 步骤3: 生成网站结构")
    website_structure = builder.generate_website_structure()
    if not website_structure:
        print("❌ 网站结构生成失败")
        return 1
    
    # 4. 创建内容计划
    print("\n📝 步骤4: 创建内容计划")
    content_plan = builder.create_content_plan()
    if not content_plan:
        print("❌ 内容计划创建失败")
        return 1
    
    # 5. 查看可用的部署服务
    print("\n🌐 步骤5: 查看可用的部署服务")
    available_deployers = builder.get_available_deployers()
    print(f"可用的部署服务: {', '.join(available_deployers)}")
    
    # 6. 验证部署配置
    print("\n🔍 步骤6: 验证部署配置")
    for deployer in available_deployers:
        is_valid, error_msg = builder.validate_deployment_config(deployer)
        if is_valid:
            print(f"✅ {deployer}: 配置有效")
        else:
            print(f"⚠️ {deployer}: {error_msg}")
    
    # 7. 部署网站
    print("\n🚀 步骤7: 部署网站")
    
    # 选择部署服务 (这里以Vercel为例)
    deployer_name = 'vercel'
    
    # 自定义配置
    custom_config = {
        'project_name': 'my-intent-website',
        'custom_domain': 'example.com'  # 可选
    }
    
    success, result = builder.deploy_website(
        deployer_name=deployer_name,
        custom_config=custom_config
    )
    
    if success:
        print(f"🎉 网站部署成功！")
        print(f"🌐 访问地址: {result}")
        
        # 8. 查看部署历史
        print("\n📈 步骤8: 查看部署历史")
        history = builder.get_deployment_history()
        if history:
            latest = history[-1]
            print(f"最新部署: {latest['timestamp']}")
            print(f"部署服务: {latest['deployer']}")
            print(f"部署状态: {'成功' if latest['success'] else '失败'}")
        
        return 0
    else:
        print(f"❌ 网站部署失败: {result}")
        return 1


def example_cli_usage():
    """命令行使用示例"""
    print("\n" + "=" * 60)
    print("📖 命令行使用示例:")
    print("=" * 60)
    
    examples = [
        {
            'title': '基本建站和部署',
            'command': '''python -m src.website_builder.intent_based_website_builder \\
  --input data/keywords.csv \\
  --output output/my_website \\
  --deploy \\
  --deployer vercel \\
  --deployment-config deployment_config.json'''
        },
        {
            'title': '指定项目名称和自定义域名',
            'command': '''python -m src.website_builder.intent_based_website_builder \\
  --input data/keywords.csv \\
  --output output/my_website \\
  --deploy \\
  --deployer cloudflare \\
  --project-name my-awesome-site \\
  --custom-domain mysite.com \\
  --deployment-config deployment_config.json'''
        },
        {
            'title': '仅部署已生成的网站',
            'command': '''python -m src.website_builder.intent_based_website_builder \\
  --input data/keywords.csv \\
  --output output/my_website \\
  --action deploy \\
  --deployer vercel'''
        },
        {
            'title': '使用部署工具单独部署',
            'command': '''python -m src.deployment.cli deploy output/my_website/html \\
  --deployer vercel \\
  --config deployment_config.json \\
  --project-name my-site'''
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}:")
        print(f"   {example['command']}")


def example_config_setup():
    """配置设置示例"""
    print("\n" + "=" * 60)
    print("⚙️ 配置设置示例:")
    print("=" * 60)
    
    print("\n1. 生成配置文件模板:")
    print("   python -m src.deployment.cli config template deployment_config.json")
    
    print("\n2. 验证配置:")
    print("   python -m src.deployment.cli config validate --config deployment_config.json")
    
    print("\n3. 查看支持的部署服务:")
    print("   python -m src.deployment.cli list")
    
    print("\n4. 查看部署历史:")
    print("   python -m src.deployment.cli history --config deployment_config.json")


if __name__ == '__main__':
    try:
        # 运行主示例
        result = main()
        
        # 显示命令行使用示例
        example_cli_usage()
        
        # 显示配置设置示例
        example_config_setup()
        
        print("\n" + "=" * 60)
        print("✨ 示例运行完成！")
        print("💡 提示: 请先配置好API密钥和项目信息再进行实际部署")
        print("=" * 60)
        
        sys.exit(result)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 运行过程中发生错误: {e}")
        sys.exit(1)