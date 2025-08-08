#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基于搜索意图的网站自动建设工具 - 核心构建器
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Set, Optional, Any, Union

from src.analyzers.intent_analyzer_v2 import IntentAnalyzerV2
from src.website_builder.structure_generator import WebsiteStructureGenerator
from src.website_builder.content_planner import ContentPlanGenerator
from src.website_builder.page_templates import PageTemplateManager
from src.website_builder.utils import ensure_dir, load_data_file, save_json_file

class IntentBasedWebsiteBuilder:
    """基于搜索意图的网站自动建设工具核心类"""

    def __init__(self, intent_data_path: str = None, output_dir: str = "output", config: Dict = None):
        """
        初始化网站建设工具
        
        Args:
            intent_data_path: 意图数据文件路径（CSV或JSON）
            output_dir: 输出目录
            config: 配置参数
        """
        # 初始化属性
        self.intent_data_path = intent_data_path
        self.base_output_dir = output_dir
        self.config = config or {}
        self.intent_data = None
        self.intent_summary = None
        self.website_structure = None
        self.content_plan = None
        
        # 生成带时间戳的输出目录
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        project_name = self.config.get('project_name', 'website')
        self.output_dir = os.path.join(self.base_output_dir, f"{project_name}_{timestamp}")
        
        # 创建意图分析器
        self.analyzer = IntentAnalyzerV2()
        
        # 创建页面模板管理器
        self.template_manager = PageTemplateManager()
        
        # 创建网站部署器
        deployment_config_path = self.config.get('deployment_config_path')
        try:
            from src.website_builder.website_deployer import WebsiteDeployer
            self.website_deployer = WebsiteDeployer(deployment_config_path)
        except ImportError:
            self.website_deployer = None
            print("警告: 部署功能不可用，请检查部署模块")
        
        # 创建输出目录
        ensure_dir(self.output_dir)
        
        print(f"基于搜索意图的网站建设工具初始化完成")
        print(f"输出目录: {self.output_dir}")

    def load_intent_data(self) -> bool:
        """
        加载意图数据
        
        Returns:
            是否成功加载
        """
        if not self.intent_data_path:
            print("错误: 未提供意图数据文件路径")
            return False
        
        print(f"正在加载意图数据: {self.intent_data_path}")
        
        try:
            # 加载数据文件
            self.intent_data = load_data_file(self.intent_data_path)
            
            if self.intent_data is None:
                return False
            
            # 检查必要的列
            required_columns = ['query', 'intent_primary']
            missing_columns = [col for col in required_columns if col not in self.intent_data.columns]
            
            if missing_columns:
                print(f"错误: 数据缺少必要的列: {', '.join(missing_columns)}")
                return False
            
            # 生成意图摘要
            self._generate_intent_summary()
            
            print(f"成功加载意图数据，共 {len(self.intent_data)} 条记录")
            return True
            
        except Exception as e:
            print(f"加载意图数据失败: {e}")
            return False

    def _generate_intent_summary(self) -> None:
        """生成意图摘要"""
        if self.intent_data is None:
            return
        
        # 统计意图数量
        intent_counts = self.intent_data['intent_primary'].value_counts().to_dict()
        
        # 计算意图百分比
        total = len(self.intent_data)
        intent_percentages = {
            intent: round(count / total * 100, 1)
            for intent, count in intent_counts.items()
        }
        
        # 按意图分组关键词
        intent_keywords = {}
        for intent in set(self.intent_data['intent_primary']):
            keywords = self.intent_data[self.intent_data['intent_primary'] == intent]['query'].tolist()
            intent_keywords[intent] = keywords
        
        # 创建意图摘要
        self.intent_summary = {
            'total_keywords': total,
            'intent_counts': intent_counts,
            'intent_percentages': intent_percentages,
            'intent_keywords': intent_keywords,
            'intent_descriptions': {
                intent: self.analyzer.INTENT_DESCRIPTIONS.get(intent, '')
                for intent in intent_counts.keys()
            }
        }

    def generate_website_structure(self) -> Dict[str, Any]:
        """
        生成网站结构
        
        Returns:
            网站结构字典
        """
        if self.intent_data is None or self.intent_data.empty or not self.intent_summary:
            print("错误: 未加载意图数据")
            return {}
        
        print("正在生成基于搜索意图的网站结构...")
        
        # 创建结构生成器
        structure_generator = WebsiteStructureGenerator(
            intent_data=self.intent_data,
            intent_summary=self.intent_summary,
            analyzer=self.analyzer,
            template_manager=self.template_manager,
            config=self.config
        )
        
        # 生成网站结构
        self.website_structure = structure_generator.generate()
        
        # 保存网站结构
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'website_structure_{timestamp}.json')
        
        save_json_file(self.website_structure, output_file)
        
        print(f"网站结构生成完成，已保存到: {output_file}")
        
        return self.website_structure

    def create_content_plan(self) -> List[Dict[str, Any]]:
        """
        创建内容计划
        
        Returns:
            内容计划列表
        """
        if not self.website_structure or not self.intent_summary:
            print("错误: 未生成网站结构或意图摘要")
            return []
        
        print("正在创建基于搜索意图的内容计划...")
        
        # 创建内容计划生成器
        content_planner = ContentPlanGenerator(
            website_structure=self.website_structure,
            intent_summary=self.intent_summary,
            analyzer=self.analyzer,
            config=self.config
        )
        
        # 生成内容计划
        self.content_plan = content_planner.generate()
        
        # 保存内容计划
        timestamp = datetime.now().strftime('%Y-%m-%d')
        output_file = os.path.join(self.output_dir, f'content_plan_{timestamp}.json')
        
        save_json_file(self.content_plan, output_file)
        
        print(f"内容计划创建完成，共 {len(self.content_plan)} 个内容项，已保存到: {output_file}")
        
        return self.content_plan

    def generate_website_source(self) -> str:
        """
        生成网站源代码
        
        Returns:
            网站源代码目录路径
        """
        if not self.website_structure:
            print("错误: 请先生成网站结构")
            return ""
        
        if not self.content_plan:
            print("错误: 请先创建内容计划")
            return ""
        
        print("正在生成网站源代码...")
        
        # 创建网站源代码目录
        source_dir = os.path.join(self.output_dir, 'website_source')
        ensure_dir(source_dir)
        
        try:
            # 如果有部署器，使用部署器生成HTML文件
            if self.website_deployer:
                success = self.website_deployer._generate_html_files(
                    self.website_structure, 
                    self.content_plan, 
                    source_dir
                )
                if not success:
                    print("❌ 网站源代码生成失败")
                    return ""
            else:
                # 简单的HTML生成逻辑
                self._generate_simple_html_files(source_dir)
            
            print(f"✅ 网站源代码生成完成: {source_dir}")
            return source_dir
            
        except Exception as e:
            print(f"❌ 网站源代码生成失败: {e}")
            return ""

    def _generate_simple_html_files(self, source_dir: str) -> None:
        """生成简单的HTML文件"""
        # 生成首页
        index_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>基于搜索意图的内容平台</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .hero { text-align: center; padding: 50px 0; }
        .intent-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .intent-card { border: 1px solid #ddd; padding: 20px; border-radius: 8px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>基于搜索意图的内容平台</h1>
            <p>为用户提供精准的内容体验</p>
        </div>
        <div class="intent-grid">
"""
        
        # 添加意图卡片
        for intent, pages in self.website_structure.get('intent_pages', {}).items():
            if pages:
                intent_name = self.analyzer.INTENT_DESCRIPTIONS.get(intent, intent)
                index_html += f"""
            <div class="intent-card">
                <h3>{intent_name}</h3>
                <p>探索{intent_name}相关内容</p>
            </div>
"""
        
        index_html += """
        </div>
    </div>
</body>
</html>
"""
        
        # 保存首页
        with open(os.path.join(source_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(index_html)

    def deploy_website(self, 
                      deployer_name: str = None,
                      custom_config: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        部署网站到云服务器
        
        Args:
            deployer_name: 部署服务名称 ('cloudflare' 或 'vercel')
            custom_config: 自定义配置
            
        Returns:
            (是否成功, 部署URL或错误信息)
        """
        if not self.website_structure:
            return False, "请先生成网站结构"
        
        if not self.content_plan:
            return False, "请先创建内容计划"
        
        print(f"开始部署网站到 {deployer_name or '默认服务'}...")
        
        try:
            success, result = self.website_deployer.deploy_website_structure(
                website_structure=self.website_structure,
                content_plan=self.content_plan,
                output_dir=self.output_dir,
                deployer_name=deployer_name,
                custom_config=custom_config
            )
            
            if success:
                print(f"✅ 网站部署成功！")
                print(f"🌐 访问地址: {result}")
            else:
                print(f"❌ 网站部署失败: {result}")
            
            return success, result
            
        except Exception as e:
            error_msg = f"部署过程中发生错误: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg

    def get_available_deployers(self) -> List[str]:
        """获取可用的部署服务"""
        return self.website_deployer.get_available_deployers()

    def validate_deployment_config(self, deployer_name: str) -> Tuple[bool, str]:
        """验证部署配置"""
        return self.website_deployer.validate_deployment_config(deployer_name)

    def get_deployment_history(self) -> List[Dict[str, Any]]:
        """获取部署历史"""
        return self.website_deployer.get_deployment_history()
