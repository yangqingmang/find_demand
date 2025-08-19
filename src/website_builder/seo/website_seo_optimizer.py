#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网站SEO优化工具 - 对现有网站结构进行SEO优化
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from src.seo.seo_workflow_engine import SEOWorkflowEngine

class WebsiteSEOOptimizer:
    """网站SEO优化工具"""
    
    def __init__(self, config_path: str = "src/seo/seo_optimization_workflow.json"):
        """
        初始化SEO优化工具
        
        Args:
            config_path: SEO配置文件路径
        """
        self.config_path = config_path
        self.seo_engine = None
        self.optimization_results = {}
        
        # 初始化SEO引擎
        try:
            self.seo_engine = SEOWorkflowEngine(config_path)
            print(f"SEO优化引擎初始化成功，配置文件: {config_path}")
        except Exception as e:
            print(f"SEO引擎初始化失败: {e}")
            raise
    
    def analyze_website_structure(self, website_path: str) -> Dict[str, Any]:
        """
        分析现有网站结构
        
        Args:
            website_path: 网站目录路径或结构文件路径
            
        Returns:
            网站结构分析结果
        """
        print(f"正在分析网站结构: {website_path}")
        
        website_data = {}
        
        if os.path.isfile(website_path):
            # 如果是文件，尝试加载JSON结构
            try:
                with open(website_path, 'r', encoding='utf-8') as f:
                    website_data = json.load(f)
                print(f"成功加载网站结构文件")
            except Exception as e:
                print(f"加载网站结构文件失败: {e}")
                return {}
        
        elif os.path.isdir(website_path):
            # 如果是目录，扫描HTML文件
            website_data = self._scan_website_directory(website_path)
        
        else:
            print(f"错误: 路径不存在 - {website_path}")
            return {}
        
        # 分析网站结构
        analysis_result = {
            'website_path': website_path,
            'analysis_time': datetime.now().isoformat(),
            'structure_type': 'file' if os.path.isfile(website_path) else 'directory',
            'pages_found': 0,
            'seo_issues': [],
            'optimization_opportunities': [],
            'website_data': website_data
        }
        
        # 统计页面数量
        if 'homepage' in website_data:
            analysis_result['pages_found'] += 1
        
        for section in ['intent_pages', 'content_pages', 'product_pages', 'category_pages']:
            if section in website_data:
                if isinstance(website_data[section], dict):
                    analysis_result['pages_found'] += len(website_data[section])
                elif isinstance(website_data[section], list):
                    analysis_result['pages_found'] += len(website_data[section])
        
        # 检查SEO问题
        self._identify_seo_issues(website_data, analysis_result)
        
        print(f"网站结构分析完成，发现 {analysis_result['pages_found']} 个页面")
        
        return analysis_result
    
    def _scan_website_directory(self, directory_path: str) -> Dict[str, Any]:
        """
        扫描网站目录，提取页面信息
        
        Args:
            directory_path: 网站目录路径
            
        Returns:
            网站结构数据
        """
        print(f"正在扫描网站目录: {directory_path}")
        
        website_data = {
            'homepage': {},
            'intent_pages': {},
            'content_pages': {},
            'product_pages': {},
            'category_pages': {},
            'other_pages': {}
        }
        
        # 扫描HTML文件
        html_files = []
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory_path)
                    html_files.append(relative_path)
        
        # 分类页面
        for html_file in html_files:
            page_info = self._extract_page_info(os.path.join(directory_path, html_file))
            
            if html_file == 'index.html' or html_file.endswith('/index.html'):
                website_data['homepage'] = page_info
            elif html_file.startswith('intent/'):
                intent_name = os.path.splitext(os.path.basename(html_file))[0]
                website_data['intent_pages'][intent_name] = page_info
            elif html_file.startswith('keyword/'):
                keyword_name = os.path.splitext(os.path.basename(html_file))[0]
                website_data['content_pages'][keyword_name] = page_info
            elif html_file.startswith('product'):
                product_name = os.path.splitext(os.path.basename(html_file))[0]
                website_data['product_pages'][product_name] = page_info
            else:
                page_name = os.path.splitext(html_file)[0]
                website_data['other_pages'][page_name] = page_info
        
        print(f"扫描完成，发现 {len(html_files)} 个HTML文件")
        
        return website_data
    
    def _extract_page_info(self, html_file_path: str) -> Dict[str, Any]:
        """
        从HTML文件提取页面信息
        
        Args:
            html_file_path: HTML文件路径
            
        Returns:
            页面信息
        """
        page_info = {
            'file_path': html_file_path,
            'title': '',
            'meta_description': '',
            'meta_keywords': '',
            'h1_tags': [],
            'h2_tags': [],
            'internal_links': [],
            'images': [],
            'word_count': 0
        }
        
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 简单的HTML解析（实际项目中建议使用BeautifulSoup）
            import re
            
            # 提取title
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
            if title_match:
                page_info['title'] = title_match.group(1).strip()
            
            # 提取meta description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            if desc_match:
                page_info['meta_description'] = desc_match.group(1)
            
            # 提取meta keywords
            keywords_match = re.search(r'<meta[^>]*name=["\']keywords["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
            if keywords_match:
                page_info['meta_keywords'] = keywords_match.group(1)
            
            # 提取H1标签
            h1_matches = re.findall(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE | re.DOTALL)
            page_info['h1_tags'] = [h1.strip() for h1 in h1_matches]
            
            # 提取H2标签
            h2_matches = re.findall(r'<h2[^>]*>(.*?)</h2>', content, re.IGNORECASE | re.DOTALL)
            page_info['h2_tags'] = [h2.strip() for h2 in h2_matches]
            
            # 简单计算字数（去除HTML标签）
            text_content = re.sub(r'<[^>]+>', '', content)
            page_info['word_count'] = len(text_content.split())
            
        except Exception as e:
            print(f"提取页面信息失败 {html_file_path}: {e}")
        
        return page_info
    
    def _identify_seo_issues(self, website_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> None:
        """
        识别SEO问题
        
        Args:
            website_data: 网站数据
            analysis_result: 分析结果
        """
        issues = []
        opportunities = []
        
        # 检查首页SEO
        if 'homepage' in website_data:
            homepage = website_data['homepage']
            if not homepage.get('title'):
                issues.append('首页缺少标题')
            if not homepage.get('meta_description'):
                issues.append('首页缺少meta描述')
            if not homepage.get('h1_tags'):
                issues.append('首页缺少H1标签')
        
        # 检查页面SEO优化情况
        all_pages = []
        for section in ['intent_pages', 'content_pages', 'product_pages', 'category_pages']:
            if section in website_data:
                if isinstance(website_data[section], dict):
                    all_pages.extend(website_data[section].values())
                elif isinstance(website_data[section], list):
                    all_pages.extend(website_data[section])
        
        pages_without_seo = 0
        for page in all_pages:
            if not page.get('seo_optimization'):
                pages_without_seo += 1
        
        if pages_without_seo > 0:
            issues.append(f'{pages_without_seo} 个页面未进行SEO优化')
            opportunities.append('为所有页面添加SEO优化')
        
        # 检查sitemap
        if 'sitemap' not in website_data:
            issues.append('缺少网站地图')
            opportunities.append('生成XML网站地图')
        
        analysis_result['seo_issues'] = issues
        analysis_result['optimization_opportunities'] = opportunities
    
    def optimize_website(self, website_data: Dict[str, Any], output_dir: str = "optimized_output") -> Dict[str, Any]:
        """
        优化整个网站
        
        Args:
            website_data: 网站数据
            output_dir: 输出目录
            
        Returns:
            优化结果
        """
        print("正在执行网站SEO优化...")
        
        os.makedirs(output_dir, exist_ok=True)
        
        optimization_results = {
            'start_time': datetime.now().isoformat(),
            'pages_optimized': 0,
            'pages_failed': 0,
            'optimizations_applied': [],
            'errors': [],
            'optimized_website_data': {}
        }
        
        # 深拷贝网站数据
        import copy
        optimized_data = copy.deepcopy(website_data)
        
        # 优化首页
        if 'homepage' in optimized_data:
            try:
                self._optimize_page(optimized_data['homepage'], 'homepage')
                optimization_results['pages_optimized'] += 1
                optimization_results['optimizations_applied'].append('首页SEO优化')
            except Exception as e:
                optimization_results['pages_failed'] += 1
                optimization_results['errors'].append(f'首页优化失败: {e}')
        
        # 优化各类页面
        for section_name in ['intent_pages', 'content_pages', 'product_pages', 'category_pages']:
            if section_name in optimized_data:
                section_data = optimized_data[section_name]
                
                if isinstance(section_data, dict):
                    for page_id, page_data in section_data.items():
                        try:
                            self._optimize_page(page_data, f'{section_name}_{page_id}')
                            optimization_results['pages_optimized'] += 1
                        except Exception as e:
                            optimization_results['pages_failed'] += 1
                            optimization_results['errors'].append(f'{section_name}_{page_id} 优化失败: {e}')
                
                elif isinstance(section_data, list):
                    for i, page_data in enumerate(section_data):
                        try:
                            self._optimize_page(page_data, f'{section_name}_{i}')
                            optimization_results['pages_optimized'] += 1
                        except Exception as e:
                            optimization_results['pages_failed'] += 1
                            optimization_results['errors'].append(f'{section_name}_{i} 优化失败: {e}')
        
        # 生成网站地图
        try:
            sitemap_data = self._generate_sitemap(optimized_data)
            optimized_data['sitemap'] = sitemap_data
            optimization_results['optimizations_applied'].append('生成XML网站地图')
        except Exception as e:
            optimization_results['errors'].append(f'网站地图生成失败: {e}')
        
        # 生成SEO报告
        try:
            seo_report = self._generate_optimization_report(optimized_data, optimization_results)
            optimized_data['seo_report'] = seo_report
            optimization_results['optimizations_applied'].append('生成SEO优化报告')
        except Exception as e:
            optimization_results['errors'].append(f'SEO报告生成失败: {e}')
        
        optimization_results['optimized_website_data'] = optimized_data
        optimization_results['end_time'] = datetime.now().isoformat()
        
        # 保存优化结果
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_file = os.path.join(output_dir, f'seo_optimized_website_{timestamp}.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(optimized_data, f, ensure_ascii=False, indent=2)
        
        # 保存优化报告
        report_file = os.path.join(output_dir, f'seo_optimization_report_{timestamp}.json')
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(optimization_results, f, ensure_ascii=False, indent=2)
        
        print(f"网站SEO优化完成:")
        print(f"  - 优化页面: {optimization_results['pages_optimized']}")
        print(f"  - 失败页面: {optimization_results['pages_failed']}")
        print(f"  - 优化结果保存到: {output_file}")
        print(f"  - 优化报告保存到: {report_file}")
        
        return optimization_results
    
    def _optimize_page(self, page_data: Dict[str, Any], page_id: str) -> None:
        """
        优化单个页面
        
        Args:
            page_data: 页面数据
            page_id: 页面ID
        """
        # 准备SEO优化数据
        seo_data = {
            'primary_keyword': page_data.get('title', page_data.get('keyword', '')),
            'keywords': self._extract_keywords_from_page(page_data),
            'intent': self._determine_page_intent(page_data),
            'url': page_data.get('url', f'/{page_id}'),
            'title': page_data.get('title', ''),
            'keyword_density': 2.5,
            'content_uniqueness': 90,
            'readability_score': 65,
            'page_load_time': 2.0,
            'mobile_friendly': True
        }
        
        # 应用SEO优化
        if self.seo_engine:
            # 生成Meta标签
            meta_tags = self.seo_engine.get_seo_meta_tags(seo_data)
            
            # 获取内容模板
            content_template = self.seo_engine.get_content_template(seo_data['intent'])
            
            # 生成SEO友好URL
            seo_url = self.seo_engine.get_url_structure(seo_data)
            
            # 验证SEO质量
            quality_check = self.seo_engine.validate_seo_quality(seo_data)
            
            # 更新页面数据
            page_data['seo_optimization'] = {
                'meta_tags': meta_tags,
                'content_template': content_template,
                'seo_url': seo_url,
                'quality_score': quality_check.get('overall_score', 0),
                'recommendations': quality_check.get('recommendations', []),
                'optimization_timestamp': datetime.now().isoformat()
            }
    
    def _extract_keywords_from_page(self, page_data: Dict[str, Any]) -> List[str]:
        """
        从页面数据中提取关键词
        
        Args:
            page_data: 页面数据
            
        Returns:
            关键词列表
        """
        keywords = []
        
        # 从标题提取
        if 'title' in page_data:
            keywords.append(page_data['title'])
        
        # 从关键词字段提取
        if 'keyword' in page_data:
            keywords.append(page_data['keyword'])
        
        # 从现有关键词列表提取
        if 'keywords' in page_data:
            if isinstance(page_data['keywords'], list):
                keywords.extend(page_data['keywords'])
            elif isinstance(page_data['keywords'], str):
                keywords.extend(page_data['keywords'].split(','))
        
        # 从meta关键词提取
        if 'meta_keywords' in page_data:
            keywords.extend(page_data['meta_keywords'].split(','))
        
        # 去重并清理
        unique_keywords = []
        for keyword in keywords:
            cleaned = keyword.strip()
            if cleaned and cleaned not in unique_keywords:
                unique_keywords.append(cleaned)
        
        return unique_keywords[:10]  # 限制关键词数量
    
    def _determine_page_intent(self, page_data: Dict[str, Any]) -> str:
        """
        确定页面搜索意图
        
        Args:
            page_data: 页面数据
            
        Returns:
            搜索意图代码
        """
        # 如果已经有意图信息
        if 'intent' in page_data:
            return page_data['intent']
        
        # 根据页面类型推断意图
        page_type = page_data.get('type', '')
        if page_type == 'product' or 'product' in page_data.get('url', ''):
            return 'E'  # 交易购买
        elif page_type == 'article' or 'content' in page_data.get('url', ''):
            return 'I'  # 信息获取
        elif 'comparison' in page_data.get('title', '').lower():
            return 'C'  # 商业评估
        else:
            return 'I'  # 默认为信息获取
    
    def _generate_sitemap(self, website_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成网站地图
        
        Args:
            website_data: 网站数据
            
        Returns:
            网站地图数据
        """
        sitemap_urls = []
        
        # 添加首页
        if 'homepage' in website_data:
            sitemap_urls.append({
                'url': '/',
                'priority': 1.0,
                'changefreq': 'daily',
                'lastmod': datetime.now().isoformat()
            })
        
        # 添加其他页面
        for section_name in ['intent_pages', 'content_pages', 'product_pages', 'category_pages']:
            if section_name in website_data:
                section_data = website_data[section_name]
                priority = self._get_section_priority(section_name)
                
                if isinstance(section_data, dict):
                    for page_data in section_data.values():
                        if 'url' in page_data:
                            sitemap_urls.append({
                                'url': page_data['url'],
                                'priority': priority,
                                'changefreq': 'weekly',
                                'lastmod': datetime.now().isoformat()
                            })
                
                elif isinstance(section_data, list):
                    for page_data in section_data:
                        if 'url' in page_data:
                            sitemap_urls.append({
                                'url': page_data['url'],
                                'priority': priority,
                                'changefreq': 'weekly',
                                'lastmod': datetime.now().isoformat()
                            })
        
        return {
            'urls': sitemap_urls,
            'total_urls': len(sitemap_urls),
            'generated_at': datetime.now().isoformat()
        }
    
    def _get_section_priority(self, section_name: str) -> float:
        """
        获取页面段落的优先级
        
        Args:
            section_name: 段落名称
            
        Returns:
            优先级值
        """
        priority_map = {
            'intent_pages': 0.9,
            'product_pages': 0.8,
            'content_pages': 0.7,
            'category_pages': 0.6
        }
        return priority_map.get(section_name, 0.5)
    
    def _generate_optimization_report(self, website_data: Dict[str, Any], 
                                    optimization_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成SEO优化报告
        
        Args:
            website_data: 网站数据
            optimization_results: 优化结果
            
        Returns:
            SEO优化报告
        """
        report = {
            'generation_time': datetime.now().isoformat(),
            'optimization_summary': {
                'total_pages': optimization_results['pages_optimized'] + optimization_results['pages_failed'],
                'pages_optimized': optimization_results['pages_optimized'],
                'pages_failed': optimization_results['pages_failed'],
                'success_rate': 0.0
            },
            'seo_metrics': {
                'pages_with_meta_tags': 0,
                'pages_with_content_templates': 0,
                'average_seo_score': 0.0,
                'total_seo_issues': len(optimization_results.get('errors', []))
            },
            'recommendations': [],
            'next_steps': []
        }
        
        # 计算成功率
        total_pages = report['optimization_summary']['total_pages']
        if total_pages > 0:
            report['optimization_summary']['success_rate'] = round(
                optimization_results['pages_optimized'] / total_pages * 100, 1
            )
        
        # 统计SEO指标
        all_scores = []
        pages_with_meta = 0
        pages_with_templates = 0
        
        for section_name in ['homepage', 'intent_pages', 'content_pages', 'product_pages', 'category_pages']:
            if section_name in website_data:
                section_data = website_data[section_name]
                
                if section_name == 'homepage':
                    # 处理首页
                    if 'seo_optimization' in section_data:
                        seo_opt = section_data['seo_optimization']
                        if 'meta_tags' in seo_opt:
                            pages_with_meta += 1
                        if 'content_template' in seo_opt:
                            pages_with_templates += 1
                        if 'quality_score' in seo_opt:
                            all_scores.append(seo_opt['quality_score'])
                else:
                    # 处理其他页面
                    pages = []
                    if isinstance(section_data, dict):
                        pages = section_data.values()
                    elif isinstance(section_data, list):
                        pages = section_data
                    
                    for page in pages:
                        if 'seo_optimization' in page:
                            seo_opt = page['seo_optimization']
                            if 'meta_tags' in seo_opt:
                                pages_with_meta += 1
                            if 'content_template' in seo_opt:
                                pages_with_templates += 1
                            if 'quality_score' in seo_opt:
                                all_scores.append(seo_opt['quality_score'])
        
        report['seo_metrics']['pages_with_meta_tags'] = pages_with_meta
        report['seo_metrics']['pages_with_content_templates'] = pages_with_templates
        
        if all_scores:
            report['seo_metrics']['average_seo_score'] = round(sum(all_scores) / len(all_scores), 1)
        
        # 生成建议
        if report['seo_metrics']['average_seo_score'] < 60:
            report['recommendations'].append('整体SEO评分较低，建议重点优化内容质量')
        elif report['seo_metrics']['average_seo_score'] < 80:
            report['recommendations'].append('SEO评分中等，建议继续优化技术SEO')
        else:
            report['recommendations'].append('SEO评分良好，建议定期监控和维护')
        
        if optimization_results['pages_failed'] > 0:
            report['recommendations'].append(f'有 {optimization_results["pages_failed"]} 个页面优化失败，需要手动检查')
        
        # 下一步建议
        report['next_steps'] = [
            '定期监控关键词排名',
            '分析用户行为数据',
            '持续优化内容质量',
            '建设高质量外链',
            '提升页面加载速度'
        ]
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='网站SEO优化工具')
    
    parser.add_argument('--website', '-w', type=str, required=True,
                        help='网站路径（目录或JSON文件）')
    parser.add_argument('--output', '-o', type=str, default='seo_optimized_output',
                        help='输出目录')
    parser.add_argument('--config', '-c', type=str, 
                        default='src/seo/seo_optimization_workflow.json',
                        help='SEO配置文件路径')
    parser.add_argument('--action', '-a', type=str,
                        choices=['analyze', 'optimize', 'all'],
                        default='all', help='执行的操作')
    
    args = parser.parse_args()
    
    try:
        # 初始化SEO优化工具
        optimizer = WebsiteSEOOptimizer(args.config)
        
        # 分析网站结构
        if args.action in ['analyze', 'all']:
            print("=== 网站结构分析 ===")
            analysis_result = optimizer.analyze_website_structure(args.website)
            
            print(f"发现页面: {analysis_result['pages_found']}")
            print(f"SEO问题: {len(analysis_result['seo_issues'])}")
            print(f"优化机会: {len(analysis_result['optimization_opportunities'])}")
            
            if analysis_result['seo_issues']:
                print("\nSEO问题:")
                for issue in analysis_result['seo_issues']:
                    print(f"  - {issue}")
            
            if analysis_result['optimization_opportunities']:
                print("\n优化机会:")
                for opportunity in analysis_result['optimization_opportunities']:
                    print(f"  - {opportunity}")
        
        # 执行SEO优化
        if args.action in ['optimize', 'all']:
            print("\n=== SEO优化执行 ===")
            
            # 如果是分析阶段的结果，使用其网站数据
            if args.action == 'all' and 'analysis_result' in locals():
                website_data = analysis_result['website_data']
            else:
                # 重新分析网站
                analysis_result = optimizer.analyze_website_structure(args.website)
                website_data = analysis_result['website_data']
            
            optimization_results = optimizer.optimize_website(website_data, args.output)
            
            print(f"\n优化完成:")
            print(f"  成功优化: {optimization_results['pages_optimized']} 页面")
            print(f"  优化失败: {optimization_results['pages_failed']} 页面")
            
            if optimization_results['errors']:
                print(f"\n错误信息:")
                for error in optimization_results['errors'][:5]:  # 只显示前5个错误
                    print(f"  - {error}")
        
        print("\n操作完成!")
        
    except Exception as e:
        print(f"程序执行失败: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
