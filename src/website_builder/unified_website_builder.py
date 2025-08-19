#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
统一的网站建设工具 - 整合所有建站功能
支持基于搜索意图的网站生成、SEO优化、多主题适配
"""

import os
import sys
import json
import pandas as pd
import argparse
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any, Union

# 导入现有的核心模块
from src.website_builder.builder_core import IntentBasedWebsiteBuilder
from src.website_builder.html_generator import HTMLGenerator
from src.website_builder.tailwind_generator import TailwindHTMLGenerator

# 可选的SEO模块
try:
    from src.website_builder.seo.seo_workflow_engine import SEOWorkflowEngine
    SEO_AVAILABLE = True
except ImportError:
    SEO_AVAILABLE = False
    print("⚠️ SEO模块不可用")

# 可选的部署模块
try:
    from src.website_builder.website_deployer import WebsiteDeployer
    DEPLOY_AVAILABLE = True
except ImportError:
    DEPLOY_AVAILABLE = False
    print("⚠️ 部署模块不可用")


class UnifiedWebsiteBuilder:
    """统一的网站建设工具 - 基于现有的 IntentBasedWebsiteBuilder"""

    def __init__(self, intent_data_path: str = None, output_dir: str = "output", 
                 config: Dict = None, enable_seo: bool = True):
        """
        初始化统一网站建设工具
        
        Args:
            intent_data_path: 意图数据文件路径
            output_dir: 输出基础目录
            config: 配置参数
            enable_seo: 是否启用SEO优化
        """
        self.intent_data_path = intent_data_path
        self.output_dir = output_dir
        self.config = config or {}
        self.enable_seo = enable_seo and SEO_AVAILABLE
        
        # 使用现有的核心建站工具
        self.core_builder = IntentBasedWebsiteBuilder(
            intent_data_path=intent_data_path,
            output_dir=output_dir,
            config=config
        )
        
        # 初始化SEO引擎
        if self.enable_seo:
            try:
                self.seo_engine = SEOWorkflowEngine("src/website_builder/seo/seo_optimization_workflow.json")
                print("✅ SEO优化引擎初始化成功")
            except Exception as e:
                print(f"⚠️ SEO引擎初始化失败: {e}")
                self.seo_engine = None
                self.enable_seo = False
        else:
            self.seo_engine = None
        
        # 初始化HTML生成器
        use_tailwind = self.config.get('use_tailwind', False)
        if use_tailwind:
            self.html_generator = TailwindHTMLGenerator(self.core_builder.output_dir)
            print("✅ 使用 TailwindCSS 生成器")
        else:
            self.html_generator = HTMLGenerator(self.core_builder.output_dir)
            print("✅ 使用标准 HTML 生成器")
        
        print(f"🚀 统一网站建设工具初始化完成")
        print(f"📁 输出目录: {self.core_builder.output_dir}")
        print(f"🔧 SEO优化: {'启用' if self.enable_seo else '禁用'}")

    def load_intent_data(self) -> bool:
        """加载意图数据"""
        return self.core_builder.load_intent_data()

    def generate_website_structure(self) -> Dict[str, Any]:
        """生成网站结构"""
        structure = self.core_builder.generate_website_structure()
        
        # 如果启用SEO，应用SEO优化
        if self.enable_seo and self.seo_engine and structure:
            self._apply_seo_optimization(structure)
        
        return structure

    def _apply_seo_optimization(self, structure: Dict[str, Any]):
        """应用SEO优化到网站结构"""
        print("🔍 正在应用SEO优化...")
        
        try:
            # 为首页应用SEO优化
            if 'homepage' in structure:
                homepage_seo = self._optimize_page_seo({
                    'title': structure['homepage']['title'],
                    'primary_keyword': '搜索意图内容平台',
                    'keywords': ['搜索意图', '内容平台', 'AI工具', '智能分析'],
                    'intent': 'N',
                    'url': '/'
                })
                structure['homepage']['seo_optimization'] = homepage_seo
            
            # 为意图页面应用SEO优化
            if 'intent_pages' in structure:
                for intent, pages in structure['intent_pages'].items():
                    for i, page in enumerate(pages):
                        page_seo = self._optimize_page_seo({
                            'title': page.get('title', ''),
                            'primary_keyword': page.get('title', ''),
                            'keywords': [page.get('title', '')],
                            'intent': intent,
                            'url': page.get('url', '')
                        })
                        structure['intent_pages'][intent][i]['seo_optimization'] = page_seo
            
            print("✅ SEO优化应用完成")
            
        except Exception as e:
            print(f"⚠️ SEO优化应用失败: {e}")

    def _optimize_page_seo(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """优化单个页面的SEO"""
        if not self.seo_engine:
            return {}
        
        try:
            # 生成SEO Meta标签
            meta_tags = self.seo_engine.get_seo_meta_tags(page_data)
            
            # 获取内容模板
            content_template = self.seo_engine.get_content_template(page_data.get('intent', 'I'))
            
            # 生成SEO友好的URL
            seo_url = self.seo_engine.get_url_structure(page_data)
            
            return {
                'meta_tags': meta_tags,
                'content_template': content_template,
                'seo_url': seo_url,
                'optimized': True
            }
            
        except Exception as e:
            return {'error': str(e)}

    def create_content_plan(self) -> List[Dict[str, Any]]:
        """创建内容计划"""
        content_plan = self.core_builder.create_content_plan()
        
        # 如果启用SEO，为内容计划添加SEO信息
        if self.enable_seo and self.seo_engine and content_plan:
            self._enhance_content_plan_with_seo(content_plan)
        
        return content_plan

    def _enhance_content_plan_with_seo(self, content_plan: List[Dict[str, Any]]):
        """为内容计划添加SEO增强"""
        print("🔍 正在为内容计划添加SEO优化...")
        
        for item in content_plan:
            try:
                # 准备页面数据
                page_data = {
                    'title': item['title'],
                    'primary_keyword': item['title'],
                    'keywords': [item['title']],
                    'intent': item.get('intent', 'I'),
                    'url': item.get('page_url', '')
                }
                
                # 应用SEO优化
                seo_optimization = self._optimize_page_seo(page_data)
                
                # 添加SEO信息
                item['seo_optimization'] = seo_optimization
                item['seo_optimized'] = seo_optimization.get('optimized', False)
                
            except Exception as e:
                print(f"⚠️ 为内容项 '{item['title']}' 添加SEO信息失败: {e}")

    def generate_website_source(self) -> str:
        """生成网站源代码"""
        # 确保已生成网站结构和内容计划
        if not hasattr(self.core_builder, 'website_structure') or not self.core_builder.website_structure:
            print("❌ 请先生成网站结构")
            return ""
        
        if not hasattr(self.core_builder, 'content_plan') or not self.core_builder.content_plan:
            print("❌ 请先创建内容计划")
            return ""
        
        print("💻 正在生成网站源代码...")
        
        try:
            # 使用HTML生成器生成网站
            structure_file = os.path.join(self.core_builder.output_dir, 'website_structure.json')
            content_plan_file = os.path.join(self.core_builder.output_dir, 'content_plan.json')
            
            # 保存结构和内容计划文件（如果不存在）
            if not os.path.exists(structure_file):
                with open(structure_file, 'w', encoding='utf-8') as f:
                    json.dump(self.core_builder.website_structure, f, ensure_ascii=False, indent=2)
            
            if not os.path.exists(content_plan_file):
                with open(content_plan_file, 'w', encoding='utf-8') as f:
                    json.dump(self.core_builder.content_plan, f, ensure_ascii=False, indent=2)
            
            # 生成网站
            self.html_generator.generate_website(structure_file, content_plan_file)
            
            source_dir = self.html_generator.output_dir
            print(f"✅ 网站源代码生成完成: {source_dir}")
            return source_dir
            
        except Exception as e:
            print(f"❌ 网站源代码生成失败: {e}")
            return ""

    def deploy_website(self, deployer_name: str = None, custom_config: Dict[str, Any] = None) -> Tuple[bool, str]:
        """部署网站"""
        return self.core_builder.deploy_website(deployer_name, custom_config)

    def get_available_deployers(self) -> List[str]:
        """获取可用的部署服务"""
        return self.core_builder.get_available_deployers()

    def validate_deployment_config(self, deployer_name: str) -> Tuple[bool, str]:
        """验证部署配置"""
        return self.core_builder.validate_deployment_config(deployer_name)

    def generate_complete_website(self) -> Dict[str, Any]:
        """生成完整的网站（一键生成）"""
        print("🚀 开始一键生成完整网站...")
        
        results = {
            'success': False,
            'steps_completed': [],
            'errors': [],
            'output_dir': self.core_builder.output_dir
        }
        
        try:
            # 步骤1: 加载意图数据
            if not self.load_intent_data():
                results['errors'].append('加载意图数据失败')
                return results
            results['steps_completed'].append('数据加载')
            
            # 步骤2: 生成网站结构
            structure = self.generate_website_structure()
            if not structure:
                results['errors'].append('网站结构生成失败')
                return results
            results['steps_completed'].append('网站结构生成')
            
            # 步骤3: 创建内容计划
            content_plan = self.create_content_plan()
            if not content_plan:
                results['errors'].append('内容计划创建失败')
                return results
            results['steps_completed'].append('内容计划创建')
            
            # 步骤4: 生成网站源代码
            source_dir = self.generate_website_source()
            if not source_dir:
                results['errors'].append('网站源代码生成失败')
                return results
            results['steps_completed'].append('源代码生成')
            results['source_dir'] = source_dir
            
            results['success'] = True
            print("🎉 完整网站生成成功！")
            
        except Exception as e:
            results['errors'].append(f'生成过程中发生错误: {e}')
            print(f"❌ 网站生成失败: {e}")
        
        return results

    # 为了向后兼容，提供一些属性访问
    @property
    def output_dir(self):
        return self.core_builder.output_dir
    
    @property
    def website_structure(self):
        return getattr(self.core_builder, 'website_structure', None)
    
    @property
    def content_plan(self):
        return getattr(self.core_builder, 'content_plan', None)
    
    @property
    def intent_summary(self):
        return getattr(self.core_builder, 'intent_summary', None)


def main():
    """主函数 - 提供命令行接口"""
    parser = argparse.ArgumentParser(description='统一的网站建设工具')
    
    parser.add_argument('--input', '-i', type=str, help='输入文件路径（CSV或JSON）')
    parser.add_argument('--output', '-o', type=str, default='output', help='输出基础目录路径')
    parser.add_argument('--action', '-a', type=str, 
                        choices=['analyze', 'structure', 'content', 'source', 'deploy', 'all'], 
                        default='all', help='执行的操作')
    parser.add_argument('--project-name', type=str, default='website', help='项目名称')
    parser.add_argument('--deployer', type=str, choices=['cloudflare', 'vercel'], help='部署服务')
    parser.add_argument('--deployment-config', type=str, help='部署配置文件路径')
    parser.add_argument('--custom-domain', type=str, help='自定义域名')
    parser.add_argument('--use-tailwind', action='store_true', help='使用TailwindCSS样式框架')
    parser.add_argument('--enable-seo', action='store_true', default=True, help='启用SEO优化')
    parser.add_argument('--disable-seo', action='store_true', help='禁用SEO优化')
    parser.add_argument('--version', '-v', action='version', 
                        version='统一网站建设工具 v3.0.0 (整合版)')
    
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
        
        # 创建统一建站工具实例
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
                print(f"✅ 完成步骤: {', '.join(results['steps_completed'])}")
                
                if 'source_dir' in results:
                    print(f"💻 源代码目录: {results['source_dir']}")
                
                return 0
            else:
                print(f"\n❌ 网站生成失败")
                print(f"✅ 已完成步骤: {', '.join(results['steps_completed'])}")
                print(f"❌ 错误信息: {', '.join(results['errors'])}")
                return 1
        else:
            # 分步执行
            if not builder.load_intent_data():
                print("❌ 加载意图数据失败，程序退出")
                return 1
            
            if args.action == 'analyze':
                print("✅ 意图数据分析完成")
                return 0
            
            if args.action == 'structure':
                structure = builder.generate_website_structure()
                if structure:
                    print("✅ 网站结构生成完成")
                    return 0
                else:
                    print("❌ 网站结构生成失败")
                    return 1
            
            if args.action == 'content':
                builder.generate_website_structure()
                content_plan = builder.create_content_plan()
                if content_plan:
                    print("✅ 内容计划创建完成")
                    return 0
                else:
                    print("❌ 内容计划创建失败")
                    return 1
            
            if args.action == 'source':
                builder.generate_website_structure()
                builder.create_content_plan()
                source_dir = builder.generate_website_source()
                if source_dir:
                    print(f"✅ 网站源代码生成完成: {source_dir}")
                    return 0
                else:
                    print("❌ 网站源代码生成失败")
                    return 1
            
            if args.action == 'deploy':
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


if __name__ == "__main__":
    sys.exit(main())