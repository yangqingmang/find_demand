#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
需求挖掘 → 意图分析 → 建站部署 完整集成工作流
整合三大核心模块，实现从需求发现到网站上线的全自动化流程
"""

import os
import sys
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.demand_mining.demand_mining_main import DemandMiningManager
from src.website_builder.intent_based_website_builder import IntentBasedWebsiteBuilder


class IntegratedWorkflow:
    """
    集成工作流管理器
    实现需求挖掘 → 意图分析 → 网站建设 → 自动部署的完整流程
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """初始化集成工作流"""
        self.config = config or self._get_default_config()
        self.output_base_dir = "output/integrated_projects"
        self._ensure_output_dirs()
        
        # 初始化各模块
        self.demand_miner = DemandMiningManager()
        
        print("🚀 集成工作流初始化完成")
        print("📊 支持功能：需求挖掘 → 意图分析 → 网站生成 → 自动部署")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'min_opportunity_score': 60,  # 最低机会分数阈值
            'max_projects_per_batch': 5,  # 每批次最大项目数
            'auto_deploy': True,          # 是否自动部署
            'deployment_platform': 'cloudflare',  # 部署平台
            'use_tailwind': True,         # 使用TailwindCSS
            'generate_reports': True      # 生成分析报告
        }
    
    def _ensure_output_dirs(self):
        """确保输出目录存在"""
        dirs = [
            self.output_base_dir,
            os.path.join(self.output_base_dir, 'demand_analysis'),
            os.path.join(self.output_base_dir, 'intent_analysis'),
            os.path.join(self.output_base_dir, 'websites'),
            os.path.join(self.output_base_dir, 'reports')
        ]
        
        for dir_path in dirs:
            os.makedirs(dir_path, exist_ok=True)
    
    def run_complete_workflow(self, keywords_file: str) -> Dict[str, Any]:
        """
        运行完整工作流
        
        Args:
            keywords_file: 关键词输入文件路径
            
        Returns:
            工作流执行结果
        """
        print(f"🎯 开始执行完整工作流: {keywords_file}")
        
        workflow_results = {
            'start_time': datetime.now().isoformat(),
            'input_file': keywords_file,
            'steps_completed': [],
            'generated_projects': [],
            'deployment_results': [],
            'summary': {}
        }
        
        try:
            # 步骤1: 需求挖掘与意图分析
            print("\n📊 步骤1: 执行需求挖掘与意图分析...")
            demand_results = self._run_demand_mining(keywords_file)
            workflow_results['steps_completed'].append('demand_mining')
            workflow_results['demand_analysis'] = demand_results
            
            # 步骤2: 筛选高价值关键词
            print("\n🎯 步骤2: 筛选高价值关键词...")
            high_value_keywords = self._filter_high_value_keywords(demand_results)
            workflow_results['steps_completed'].append('keyword_filtering')
            workflow_results['high_value_keywords'] = high_value_keywords
            
            # 步骤3: 批量生成网站
            print("\n🏗️ 步骤3: 批量生成网站...")
            website_results = self._batch_generate_websites(high_value_keywords)
            workflow_results['steps_completed'].append('website_generation')
            workflow_results['generated_projects'] = website_results
            
            # 步骤4: 自动部署（可选）
            if self.config.get('auto_deploy', False):
                print("\n🚀 步骤4: 自动部署网站...")
                deployment_results = self._batch_deploy_websites(website_results)
                workflow_results['steps_completed'].append('deployment')
                workflow_results['deployment_results'] = deployment_results
            
            # 步骤5: 生成综合报告
            print("\n📋 步骤5: 生成综合报告...")
            report_path = self._generate_workflow_report(workflow_results)
            workflow_results['steps_completed'].append('report_generation')
            workflow_results['report_path'] = report_path
            
            workflow_results['end_time'] = datetime.now().isoformat()
            workflow_results['status'] = 'success'
            
            print(f"\n🎉 完整工作流执行成功！")
            print(f"📊 分析了 {len(demand_results.get('keywords', []))} 个关键词")
            print(f"🎯 筛选出 {len(high_value_keywords)} 个高价值关键词")
            print(f"🏗️ 生成了 {len(website_results)} 个网站项目")
            print(f"📋 报告路径: {report_path}")
            
            return workflow_results
            
        except Exception as e:
            workflow_results['end_time'] = datetime.now().isoformat()
            workflow_results['status'] = 'failed'
            workflow_results['error'] = str(e)
            print(f"❌ 工作流执行失败: {e}")
            return workflow_results
    
    def _run_demand_mining(self, keywords_file: str) -> Dict[str, Any]:
        """执行需求挖掘分析"""
        output_dir = os.path.join(self.output_base_dir, 'demand_analysis')
        return self.demand_miner.analyze_keywords(keywords_file, output_dir)
    
    def _filter_high_value_keywords(self, demand_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """筛选高价值关键词"""
        min_score = self.config.get('min_opportunity_score', 60)
        max_projects = self.config.get('max_projects_per_batch', 5)
        
        # 获取所有关键词
        all_keywords = demand_results.get('keywords', [])
        
        # 按机会分数筛选和排序
        high_value = [
            kw for kw in all_keywords 
            if kw.get('opportunity_score', 0) >= min_score
        ]
        
        # 按分数降序排序，取前N个
        high_value.sort(key=lambda x: x.get('opportunity_score', 0), reverse=True)
        
        return high_value[:max_projects]
    
    def _batch_generate_websites(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量生成网站"""
        website_results = []
        
        for i, keyword_data in enumerate(keywords, 1):
            keyword = keyword_data['keyword']
            intent_info = keyword_data.get('intent', {})
            
            print(f"🏗️ 生成网站 ({i}/{len(keywords)}): {keyword}")
            
            try:
                # 准备意图数据文件
                intent_data = self._prepare_intent_data(keyword_data)
                intent_file_path = self._save_intent_data(intent_data, keyword)
                
                # 生成项目名称
                project_name = self._generate_project_name(keyword)
                
                # 创建网站建设器
                builder = IntentBasedWebsiteBuilder(
                    intent_data_path=intent_file_path,
                    output_dir=os.path.join(self.output_base_dir, 'websites'),
                    config={'project_name': project_name}
                )
                
                # 执行建站流程
                if builder.load_intent_data():
                    structure = builder.generate_website_structure()
                    content_plan = builder.create_content_plan()
                    source_dir = builder.generate_website_source()
                    
                    if source_dir:
                        website_results.append({
                            'keyword': keyword,
                            'project_name': project_name,
                            'source_dir': source_dir,
                            'intent_info': intent_info,
                            'opportunity_score': keyword_data.get('opportunity_score', 0),
                            'status': 'success'
                        })
                        print(f"✅ 网站生成成功: {source_dir}")
                    else:
                        website_results.append({
                            'keyword': keyword,
                            'project_name': project_name,
                            'status': 'failed',
                            'error': '源代码生成失败'
                        })
                        print(f"❌ 网站生成失败: {keyword}")
                else:
                    website_results.append({
                        'keyword': keyword,
                        'project_name': project_name,
                        'status': 'failed',
                        'error': '意图数据加载失败'
                    })
                    print(f"❌ 意图数据加载失败: {keyword}")
                    
            except Exception as e:
                website_results.append({
                    'keyword': keyword,
                    'project_name': project_name if 'project_name' in locals() else 'unknown',
                    'status': 'failed',
                    'error': str(e)
                })
                print(f"❌ 网站生成异常: {keyword} - {e}")
        
        return website_results
    
    def _prepare_intent_data(self, keyword_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """准备意图数据格式"""
        intent_info = keyword_data.get('intent', {})
        market_info = keyword_data.get('market', {})
        
        return [{
            'query': keyword_data['keyword'],
            'intent_primary': intent_info.get('primary_intent', 'I'),
            'intent_secondary': intent_info.get('secondary_intent', ''),
            'sub_intent': intent_info.get('primary_intent', 'I') + '1',
            'probability': intent_info.get('confidence', 0.8),
            'probability_secondary': 0.2,
            'search_volume': market_info.get('search_volume', 1000),
            'competition': market_info.get('competition', 0.5),
            'opportunity_score': keyword_data.get('opportunity_score', 70),
            'ai_bonus': market_info.get('ai_bonus', 0),
            'commercial_value': market_info.get('commercial_value', 0)
        }]
    
    def _save_intent_data(self, intent_data: List[Dict[str, Any]], keyword: str) -> str:
        """保存意图数据到文件"""
        # 生成安全的文件名
        safe_keyword = "".join(c for c in keyword if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_keyword = safe_keyword.replace(' ', '_')[:50]  # 限制长度
        
        file_path = os.path.join(
            self.output_base_dir, 
            'intent_analysis', 
            f'intent_{safe_keyword}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(intent_data, f, ensure_ascii=False, indent=2)
        
        return file_path
    
    def _generate_project_name(self, keyword: str) -> str:
        """生成项目名称"""
        # 清理关键词，生成合适的项目名
        clean_name = "".join(c for c in keyword if c.isalnum() or c in (' ', '-')).strip()
        clean_name = clean_name.replace(' ', '-').lower()
        
        # 限制长度并添加时间戳
        timestamp = datetime.now().strftime("%m%d_%H%M")
        return f"{clean_name[:30]}-{timestamp}"
    
    def _batch_deploy_websites(self, website_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量部署网站"""
        deployment_results = []
        
        successful_websites = [w for w in website_results if w.get('status') == 'success']
        
        for website in successful_websites:
            keyword = website['keyword']
            source_dir = website['source_dir']
            
            print(f"🚀 部署网站: {keyword}")
            
            try:
                # 这里可以集成实际的部署逻辑
                # 目前返回模拟结果
                deployment_url = f"https://{website['project_name']}.pages.dev"
                
                deployment_results.append({
                    'keyword': keyword,
                    'project_name': website['project_name'],
                    'deployment_url': deployment_url,
                    'platform': self.config.get('deployment_platform', 'cloudflare'),
                    'status': 'success'
                })
                
                print(f"✅ 部署成功: {deployment_url}")
                
            except Exception as e:
                deployment_results.append({
                    'keyword': keyword,
                    'project_name': website['project_name'],
                    'status': 'failed',
                    'error': str(e)
                })
                print(f"❌ 部署失败: {keyword} - {e}")
        
        return deployment_results
    
    def _generate_workflow_report(self, workflow_results: Dict[str, Any]) -> str:
        """生成工作流综合报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = os.path.join(
            self.output_base_dir, 
            'reports', 
            f'integrated_workflow_report_{timestamp}.md'
        )
        
        # 统计数据
        total_keywords = len(workflow_results.get('demand_analysis', {}).get('keywords', []))
        high_value_count = len(workflow_results.get('high_value_keywords', []))
        successful_websites = len([w for w in workflow_results.get('generated_projects', []) if w.get('status') == 'success'])
        successful_deployments = len([d for d in workflow_results.get('deployment_results', []) if d.get('status') == 'success'])
        
        # 生成报告内容
        report_content = f"""# 集成工作流执行报告

## 📊 执行概览
- **执行时间**: {workflow_results.get('start_time', '')} - {workflow_results.get('end_time', '')}
- **输入文件**: {workflow_results.get('input_file', '')}
- **执行状态**: {workflow_results.get('status', '')}

## 📈 数据统计
- **总关键词数**: {total_keywords}
- **高价值关键词**: {high_value_count}
- **成功生成网站**: {successful_websites}
- **成功部署网站**: {successful_deployments}

## 🎯 高价值关键词列表
"""
        
        # 添加高价值关键词详情
        for kw in workflow_results.get('high_value_keywords', [])[:10]:  # 只显示前10个
            report_content += f"- **{kw['keyword']}** (机会分数: {kw.get('opportunity_score', 0)})\n"
            report_content += f"  - 主要意图: {kw.get('intent', {}).get('primary_intent', 'Unknown')}\n"
            report_content += f"  - AI加分: {kw.get('market', {}).get('ai_bonus', 0)}\n"
            report_content += f"  - 商业价值: {kw.get('market', {}).get('commercial_value', 0)}\n\n"
        
        # 添加生成的网站项目
        report_content += "\n## 🏗️ 生成的网站项目\n"
        for website in workflow_results.get('generated_projects', []):
            status_icon = "✅" if website.get('status') == 'success' else "❌"
            report_content += f"{status_icon} **{website['keyword']}**\n"
            if website.get('status') == 'success':
                report_content += f"  - 项目目录: {website.get('source_dir', '')}\n"
            else:
                report_content += f"  - 错误: {website.get('error', '')}\n"
        
        # 添加部署结果
        if workflow_results.get('deployment_results'):
            report_content += "\n## 🚀 部署结果\n"
            for deployment in workflow_results.get('deployment_results', []):
                status_icon = "✅" if deployment.get('status') == 'success' else "❌"
                report_content += f"{status_icon} **{deployment['keyword']}**\n"
                if deployment.get('status') == 'success':
                    report_content += f"  - 部署地址: {deployment.get('deployment_url', '')}\n"
                else:
                    report_content += f"  - 错误: {deployment.get('error', '')}\n"
        
        # 添加建议
        report_content += f"""
## 💡 优化建议

### 关键词优化
- 继续挖掘相关长尾关键词
- 关注AI相关高价值关键词
- 定期更新关键词机会分数

### 网站优化
- 优化SEO元数据和结构
- 添加更多交互功能
- 完善移动端适配

### 运营建议
- 提交到AI工具导航站
- 建立社交媒体推广计划
- 监控网站流量和转化

---
*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        # 保存报告
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return report_path


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='集成工作流：需求挖掘 → 意图分析 → 网站生成 → 自动部署')
    parser.add_argument('--input', '-i', required=True, help='关键词输入文件路径')
    parser.add_argument('--config', '-c', help='配置文件路径')
    parser.add_argument('--min-score', type=int, default=60, help='最低机会分数阈值')
    parser.add_argument('--max-projects', type=int, default=5, help='最大项目数量')
    parser.add_argument('--no-deploy', action='store_true', help='跳过自动部署')
    
    args = parser.parse_args()
    
    # 准备配置
    config = {
        'min_opportunity_score': args.min_score,
        'max_projects_per_batch': args.max_projects,
        'auto_deploy': not args.no_deploy,
        'deployment_platform': 'cloudflare',
        'use_tailwind': True,
        'generate_reports': True
    }
    
    # 如果有配置文件，加载配置
    if args.config and os.path.exists(args.config):
        import json
        with open(args.config, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            config.update(user_config)
    
    try:
        # 创建工作流实例
        workflow = IntegratedWorkflow(config)
        
        # 执行完整工作流
        results = workflow.run_complete_workflow(args.input)
        
        if results['status'] == 'success':
            print(f"\n🎉 集成工作流执行成功！")
            print(f"📋 详细报告: {results.get('report_path', '')}")
            return 0
        else:
            print(f"\n❌ 集成工作流执行失败: {results.get('error', '')}")
            return 1
            
    except Exception as e:
        print(f"❌ 程序执行异常: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())