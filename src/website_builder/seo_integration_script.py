"""
SEO集成脚本 - 将SEO优化功能集成到现有建站流程
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .seo_optimizer import SEOOptimizer
from .enhanced_website_builder import EnhancedWebsiteBuilder


class SEOIntegrationManager:
    """SEO集成管理器"""
    
    def __init__(self):
        self.seo_optimizer = SEOOptimizer()
        self.enhanced_builder = EnhancedWebsiteBuilder()
    
    def upgrade_existing_website(self, website_path: str, config: Optional[Dict] = None) -> Dict:
        """
        升级现有网站，添加SEO优化
        
        Args:
            website_path: 现有网站路径
            config: 可选的SEO配置
        
        Returns:
            升级结果
        """
        try:
            website_path = Path(website_path)
            
            if not website_path.exists():
                return {'success': False, 'error': f'网站路径不存在: {website_path}'}
            
            # 1. 读取现有HTML文件
            index_file = website_path / 'index.html'
            if not index_file.exists():
                return {'success': False, 'error': '未找到index.html文件'}
            
            original_html = index_file.read_text(encoding='utf-8')
            
            # 2. 读取项目信息
            project_info = self._load_project_info(website_path)
            
            # 3. 生成SEO配置
            if config is None:
                config = self._generate_default_seo_config(project_info, original_html)
            
            # 4. 应用SEO优化
            optimized_html = self.seo_optimizer.optimize_html(original_html, config)
            
            # 5. 备份原文件
            backup_path = self._create_backup(website_path)
            
            # 6. 保存优化后的文件
            index_file.write_text(optimized_html, encoding='utf-8')
            
            # 7. 生成额外的SEO文件
            self._generate_seo_files(website_path, config)
            
            # 8. 生成升级报告
            upgrade_report = self._generate_upgrade_report(config, original_html, optimized_html)
            
            return {
                'success': True,
                'website_path': str(website_path),
                'backup_path': str(backup_path),
                'seo_config': config,
                'upgrade_report': upgrade_report
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def batch_upgrade_websites(self, websites_dir: str) -> Dict:
        """
        批量升级网站目录下的所有网站
        
        Args:
            websites_dir: 网站目录路径
        
        Returns:
            批量升级结果
        """
        websites_dir = Path(websites_dir)
        results = []
        
        if not websites_dir.exists():
            return {'success': False, 'error': f'网站目录不存在: {websites_dir}'}
        
        # 查找所有网站项目
        for project_dir in websites_dir.iterdir():
            if project_dir.is_dir() and (project_dir / 'index.html').exists():
                print(f"正在升级网站: {project_dir.name}")
                result = self.upgrade_existing_website(str(project_dir))
                results.append({
                    'project': project_dir.name,
                    'result': result
                })
        
        # 统计结果
        successful = sum(1 for r in results if r['result']['success'])
        failed = len(results) - successful
        
        return {
            'success': True,
            'total_projects': len(results),
            'successful': successful,
            'failed': failed,
            'results': results
        }
    
    def _load_project_info(self, website_path: Path) -> Dict:
        """加载项目信息"""
        project_info_file = website_path / 'project_info.json'
        
        if project_info_file.exists():
            try:
                return json.loads(project_info_file.read_text(encoding='utf-8'))
            except:
                pass
        
        # 如果没有项目信息文件，从目录名推断
        dir_name = website_path.name
        return {
            'project_name': dir_name.replace('_', ' ').title(),
            'main_keyword': dir_name.split('_')[0] if '_' in dir_name else dir_name,
            'theme': 'general',
            'created_at': datetime.now().isoformat()
        }
    
    def _generate_default_seo_config(self, project_info: Dict, html_content: str) -> Dict:
        """生成默认SEO配置"""
        main_keyword = project_info.get('main_keyword', 'website')
        
        # 从HTML中提取现有信息
        existing_title = self._extract_title_from_html(html_content)
        existing_description = self._extract_description_from_html(html_content)
        
        config = {
            'title': existing_title or f"{main_keyword.title()} - Professional Guide & Resources",
            'description': existing_description or f"Comprehensive guide and resources for {main_keyword}. Get expert insights, tips, and tools.",
            'keywords': f"{main_keyword}, guide, resources, tips, tools, professional",
            'canonical_url': '',  # 需要用户填写
            'robots': 'index, follow',
            'language': 'en',
            'author': 'Expert Team',
            'copyright': f'© {datetime.now().year} {main_keyword.title()} Guide',
            'theme_color': '#3498db',
            'locale': 'en_US',
            'site_name': f'{main_keyword.title()} Guide',
            'twitter_card_type': 'summary_large_image',
            'add_breadcrumb': True,
            'faqs': self._generate_default_faqs(main_keyword)
        }
        
        return config
    
    def _extract_title_from_html(self, html_content: str) -> Optional[str]:
        """从HTML中提取标题"""
        import re
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        return title_match.group(1).strip() if title_match else None
    
    def _extract_description_from_html(self, html_content: str) -> Optional[str]:
        """从HTML中提取描述"""
        import re
        desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        return desc_match.group(1).strip() if desc_match else None
    
    def _generate_default_faqs(self, main_keyword: str) -> List[Dict]:
        """生成默认FAQ"""
        return [
            {
                'question': f'What is {main_keyword}?',
                'answer': f'{main_keyword.title()} is a comprehensive solution that provides users with advanced features and capabilities for their specific needs.'
            },
            {
                'question': f'How do I get started with {main_keyword}?',
                'answer': f'Getting started with {main_keyword} is easy. Simply follow our step-by-step guide and you\'ll be up and running in no time.'
            },
            {
                'question': f'Is {main_keyword} suitable for beginners?',
                'answer': f'Yes, {main_keyword} is designed to be user-friendly for both beginners and advanced users. We provide comprehensive documentation and support.'
            }
        ]
    
    def _create_backup(self, website_path: Path) -> Path:
        """创建备份"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = website_path.parent / f"{website_path.name}_backup_{timestamp}"
        
        # 复制整个目录
        import shutil
        shutil.copytree(website_path, backup_path)
        
        return backup_path
    
    def _generate_seo_files(self, website_path: Path, config: Dict):
        """生成SEO相关文件"""
        # 生成sitemap.xml
        sitemap_content = self._generate_sitemap(config)
        (website_path / 'sitemap.xml').write_text(sitemap_content, encoding='utf-8')
        
        # 生成robots.txt
        robots_content = self._generate_robots_txt(config)
        (website_path / 'robots.txt').write_text(robots_content, encoding='utf-8')
        
        # 更新或创建vercel.json
        vercel_config = self._generate_vercel_config()
        (website_path / 'vercel.json').write_text(vercel_config, encoding='utf-8')
    
    def _generate_sitemap(self, config: Dict) -> str:
        """生成Sitemap"""
        base_url = config.get('canonical_url', 'https://example.com')
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{base_url}</loc>
        <lastmod>{current_date}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
    
    def _generate_robots_txt(self, config: Dict) -> str:
        """生成robots.txt"""
        base_url = config.get('canonical_url', 'https://example.com')
        
        return f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml"""
    
    def _generate_vercel_config(self) -> str:
        """生成Vercel配置"""
        config = {
            "version": 2,
            "builds": [
                {
                    "src": "**/*",
                    "use": "@vercel/static"
                }
            ],
            "routes": [
                {
                    "src": "/(.*)",
                    "dest": "/$1"
                }
            ],
            "headers": [
                {
                    "source": "/(.*)",
                    "headers": [
                        {
                            "key": "X-Content-Type-Options",
                            "value": "nosniff"
                        },
                        {
                            "key": "X-Frame-Options",
                            "value": "DENY"
                        },
                        {
                            "key": "X-XSS-Protection",
                            "value": "1; mode=block"
                        }
                    ]
                }
            ]
        }
        
        return json.dumps(config, indent=2)
    
    def _generate_upgrade_report(self, config: Dict, original_html: str, optimized_html: str) -> Dict:
        """生成升级报告"""
        # 计算改进项目
        improvements = []
        
        # 检查添加的标签
        if 'og:title' in optimized_html and 'og:title' not in original_html:
            improvements.append('添加了Open Graph标签')
        
        if 'twitter:card' in optimized_html and 'twitter:card' not in original_html:
            improvements.append('添加了Twitter Cards')
        
        if 'application/ld+json' in optimized_html and 'application/ld+json' not in original_html:
            improvements.append('添加了结构化数据')
        
        if 'breadcrumb' in optimized_html.lower() and 'breadcrumb' not in original_html.lower():
            improvements.append('添加了面包屑导航')
        
        if 'faq' in optimized_html.lower() and 'faq' not in original_html.lower():
            improvements.append('添加了FAQ部分')
        
        # 计算SEO得分
        seo_score = self._calculate_seo_score(optimized_html)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'seo_score': seo_score,
            'improvements_made': improvements,
            'files_added': ['sitemap.xml', 'robots.txt', 'vercel.json'],
            'recommendations': [
                '设置正确的canonical_url',
                '添加高质量的网站图片',
                '定期更新内容',
                '监控网站性能',
                '测试移动端体验'
            ]
        }
    
    def _calculate_seo_score(self, html_content: str) -> int:
        """计算SEO得分"""
        score = 0
        
        # 基础标签检查
        if '<title>' in html_content: score += 5
        if 'name="description"' in html_content: score += 5
        if 'name="keywords"' in html_content: score += 3
        if 'rel="canonical"' in html_content: score += 4
        if 'name="robots"' in html_content: score += 3
        
        # 社交媒体标签
        if 'og:title' in html_content: score += 8
        if 'twitter:card' in html_content: score += 7
        
        # 结构化数据
        if 'application/ld+json' in html_content: score += 20
        
        # 语义化HTML
        if '<header>' in html_content: score += 5
        if '<main>' in html_content: score += 5
        if '<section>' in html_content: score += 5
        if '<footer>' in html_content: score += 5
        
        # 其他优化
        if 'viewport' in html_content: score += 8
        if 'breadcrumb' in html_content.lower(): score += 5
        if 'faq' in html_content.lower(): score += 5
        
        return min(score, 100)


def main():
    """主函数 - 提供命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SEO集成工具')
    parser.add_argument('--upgrade', type=str, help='升级指定网站路径')
    parser.add_argument('--batch', type=str, help='批量升级网站目录')
    parser.add_argument('--config', type=str, help='自定义SEO配置文件路径')
    
    args = parser.parse_args()
    
    manager = SEOIntegrationManager()
    
    if args.upgrade:
        # 单个网站升级
        config = None
        if args.config:
            with open(args.config, 'r', encoding='utf-8') as f:
                config = json.load(f)
        
        result = manager.upgrade_existing_website(args.upgrade, config)
        
        if result['success']:
            print(f"✅ 网站升级成功!")
            print(f"📁 网站路径: {result['website_path']}")
            print(f"💾 备份路径: {result['backup_path']}")
            print(f"📊 SEO得分: {result['upgrade_report']['seo_score']}/100")
            
            print("\n🔧 应用的改进:")
            for improvement in result['upgrade_report']['improvements_made']:
                print(f"  ✓ {improvement}")
            
            print("\n📄 添加的文件:")
            for file in result['upgrade_report']['files_added']:
                print(f"  + {file}")
        else:
            print(f"❌ 网站升级失败: {result['error']}")
    
    elif args.batch:
        # 批量升级
        result = manager.batch_upgrade_websites(args.batch)
        
        if result['success']:
            print(f"✅ 批量升级完成!")
            print(f"📊 总项目数: {result['total_projects']}")
            print(f"✅ 成功: {result['successful']}")
            print(f"❌ 失败: {result['failed']}")
            
            # 显示详细结果
            for project_result in result['results']:
                status = "✅" if project_result['result']['success'] else "❌"
                print(f"  {status} {project_result['project']}")
        else:
            print(f"❌ 批量升级失败: {result['error']}")
    
    else:
        print("请指定 --upgrade 或 --batch 参数")
        print("示例:")
        print("  python seo_integration_script.py --upgrade /path/to/website")
        print("  python seo_integration_script.py --batch /path/to/websites/directory")


if __name__ == "__main__":
    main()