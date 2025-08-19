#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具 - 主入口文件
现在使用统一的网站建设工具
"""

import sys
import argparse
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.website_builder.unified_website_builder import UnifiedWebsiteBuilder

# 为了保持向后兼容性，我们重新导出主要的类
IntentBasedWebsiteBuilder = UnifiedWebsiteBuilder
__all__ = ['IntentBasedWebsiteBuilder', 'UnifiedWebsiteBuilder']

def main():
    """主函数 - 提供命令行接口"""
    parser = argparse.ArgumentParser(description='基于搜索意图的网站自动建设工具')
    
    parser.add_argument('--input', '-i', type=str, help='输入文件路径（CSV或JSON）')
    parser.add_argument('--output', '-o', type=str, default='output', help='输出基础目录路径')
    parser.add_argument('--action', '-a', type=str, 
                        choices=['analyze', 'structure', 'content', 'source', 'deploy', 'all'], 
                        default='all', help='执行的操作')
    parser.add_argument('--project-name', type=str, default='website', help='项目名称（用于生成目录名）')
    parser.add_argument('--deployer', type=str, choices=['cloudflare', 'vercel'], help='部署服务')
    parser.add_argument('--deployment-config', type=str, help='部署配置文件路径')
    parser.add_argument('--custom-domain', type=str, help='自定义域名')
    parser.add_argument('--use-tailwind', action='store_true', help='使用TailwindCSS样式框架')
    parser.add_argument('--enable-seo', action='store_true', default=True, help='启用SEO优化')
    parser.add_argument('--disable-seo', action='store_true', help='禁用SEO优化')
    parser.add_argument('--version', '-v', action='version', 
                        version='基于搜索意图的网站自动建设工具 v3.0.0 (统一版)')
    
    args = parser.parse_args()
    
    if not args.input:
        parser.error("必须提供输入文件(--input)")
    
    try:
        # 准备配置
        config = {
            'project_name': args.project_name,
            'use_tailwind': args.use_tailwind
        }
        if args.deployment_config:
            config['deployment_config_path'] = args.deployment_config
        
        # 确定是否启用SEO
        enable_seo = args.enable_seo and not args.disable_seo
        
        # 创建建站工具实例
        builder = UnifiedWebsiteBuilder(
            intent_data_path=args.input,
            output_dir=args.output,
            config=config,
            enable_seo=enable_seo
        )
        
        print(f"📁 项目将生成到: {builder.output_dir}")
        
        # 执行操作
        if args.action == 'all':
            # 一键生成完整网站
            results = builder.generate_complete_website()
            
            if results['success']:
                print(f"\n🎉 所有操作完成成功！")
                print(f"📂 项目输出目录: {results['output_dir']}")
                print(f"🎯 网站主题: {results['website_theme']}")
                print(f"🏷️ 网站类型: {results['website_type']}")
                print(f"✅ 完成步骤: {', '.join(results['steps_completed'])}")
                
                if 'source_dir' in results:
                    print(f"💻 源代码目录: {results['source_dir']}")
                
                # 显示目录结构
                print("\n📋 生成的文件结构:")
                _show_directory_structure(results['output_dir'])
                
                return 0
            else:
                print(f"\n❌ 网站生成失败")
                print(f"✅ 已完成步骤: {', '.join(results['steps_completed'])}")
                print(f"❌ 错误信息: {', '.join(results['errors'])}")
                return 1
        else:
            # 分步执行
            # 加载意图数据
            if not builder.load_intent_data():
                print("❌ 加载意图数据失败，程序退出")
                return 1
            
            # 执行分析
            if args.action == 'analyze':
                print("✅ 意图数据分析完成")
                return 0
            
            # 生成网站结构
            if args.action == 'structure':
                structure = builder.generate_website_structure()
                if structure:
                    print("✅ 网站结构生成完成")
                    return 0
                else:
                    print("❌ 网站结构生成失败")
                    return 1
            
            # 创建内容计划
            if args.action == 'content':
                structure = builder.generate_website_structure()
                if not structure:
                    print("❌ 网站结构生成失败")
                    return 1
                
                content_plan = builder.create_content_plan()
                if content_plan:
                    print("✅ 内容计划创建完成")
                    return 0
                else:
                    print("❌ 内容计划创建失败")
                    return 1
            
            # 生成网站源代码
            if args.action == 'source':
                structure = builder.generate_website_structure()
                if not structure:
                    print("❌ 网站结构生成失败")
                    return 1
                
                content_plan = builder.create_content_plan()
                if not content_plan:
                    print("❌ 内容计划创建失败")
                    return 1
                
                source_dir = builder.generate_website_source()
                if source_dir:
                    print(f"✅ 网站源代码生成完成: {source_dir}")
                    return 0
                else:
                    print("❌ 网站源代码生成失败")
                    return 1
            
            # 部署网站
            if args.action == 'deploy':
                # 准备自定义配置
                custom_config = {}
                if args.project_name:
                    custom_config['project_name'] = args.project_name
                if args.custom_domain:
                    custom_config['custom_domain'] = args.custom_domain
                
                success, result = builder.deploy_website(
                    deployer_name=args.deployer,
                    custom_config=custom_config if custom_config else None
                )
                
                if success:
                    print(f"🌐 部署成功: {result}")
                    return 0
                else:
                    print(f"❌ 部署失败: {result}")
                    return 1
        
    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")
        return 1

def _show_directory_structure(directory: str, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
    """显示目录结构"""
    if current_depth >= max_depth:
        return
    
    try:
        items = sorted(os.listdir(directory))
        for i, item in enumerate(items):
            if item.startswith('.'):
                continue
                
            item_path = os.path.join(directory, item)
            is_last = i == len(items) - 1
            
            current_prefix = "└── " if is_last else "├── "
            print(f"{prefix}{current_prefix}{item}")
            
            if os.path.isdir(item_path) and current_depth < max_depth - 1:
                extension = "    " if is_last else "│   "
                _show_directory_structure(item_path, prefix + extension, max_depth, current_depth + 1)
    except PermissionError:
        pass

if __name__ == "__main__":
    sys.exit(main())