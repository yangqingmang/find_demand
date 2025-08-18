"""
增强版网站构建器 - 集成SEO优化功能
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .seo_optimizer import SEOOptimizer
from .html_generator import HTMLGenerator
from .content_planner import ContentPlanner


class EnhancedWebsiteBuilder:
    """集成SEO优化的增强版网站构建器"""
    
    def __init__(self):
        self.seo_optimizer = SEOOptimizer()
        self.html_generator = HTMLGenerator()
        self.content_planner = ContentPlanner()
    
    def build_optimized_website(self, project_config: Dict) -> Dict:
        """
        构建SEO优化的网站
        
        Args:
            project_config: 项目配置信息
        
        Returns:
            构建结果信息
        """
        try:
            # 1. 生成项目基础信息
            project_info = self._prepare_project_info(project_config)
            
            # 2. 规划网站内容
            website_plan = self._plan_website_content(project_info)
            
            # 3. 生成SEO配置
            seo_config = self.seo_optimizer.generate_seo_config(
                project_info, website_plan
            )
            
            # 4. 生成HTML内容
            html_content = self._generate_html_content(website_plan, project_info)
            
            # 5. 应用SEO优化
            optimized_html = self.seo_optimizer.optimize_html(html_content, seo_config)
            
            # 6. 生成支持文件
            support_files = self._generate_support_files(project_info, seo_config)
            
            # 7. 保存网站文件
            output_path = self._save_website_files(
                project_info, optimized_html, support_files
            )
            
            # 8. 生成SEO报告
            seo_report = self._generate_seo_report(seo_config, optimized_html)
            
            return {
                'success': True,
                'project_info': project_info,
                'output_path': output_path,
                'seo_config': seo_config,
                'seo_report': seo_report,
                'files_created': list(support_files.keys()) + ['index.html']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'project_info': project_config
            }
    
    def _prepare_project_info(self, config: Dict) -> Dict:
        """准备项目基础信息"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        project_info = {
            'project_name': config.get('project_name', 'Untitled Project'),
            'main_keyword': config.get('main_keyword', ''),
            'theme': config.get('theme', 'general'),
            'target_audience': config.get('target_audience', 'general'),
            'language': config.get('language', 'en'),
            'created_at': datetime.now().isoformat(),
            'directory': f"generated_websites/{config.get('main_keyword', 'project').replace(' ', '_')}_{timestamp}",
            'status': 'building'
        }
        
        return project_info
    
    def _plan_website_content(self, project_info: Dict) -> Dict:
        """规划网站内容"""
        main_keyword = project_info['main_keyword']
        theme = project_info['theme']
        
        # 基础网站规划
        website_plan = {
            'title': f"{main_keyword.title()} - Professional Guide & Resources",
            'description': f"Comprehensive guide and resources for {main_keyword}. Get expert insights, tips, and tools.",
            'site_name': f"{main_keyword.title()} Guide",
            'url': '',  # 将在部署时填充
            'image': '',  # 将在生成时填充
            'sections': self._generate_content_sections(main_keyword, theme),
            'navigation': self._generate_navigation(main_keyword, theme),
            'footer_links': self._generate_footer_links(main_keyword, theme)
        }
        
        return website_plan
    
    def _generate_content_sections(self, main_keyword: str, theme: str) -> List[Dict]:
        """生成内容部分"""
        base_sections = [
            {
                'id': 'hero',
                'title': f'Welcome to {main_keyword.title()}',
                'content': f'Your comprehensive resource for everything related to {main_keyword}.',
                'type': 'hero'
            },
            {
                'id': 'features',
                'title': 'Key Features',
                'content': f'Discover the amazing features and benefits of {main_keyword}.',
                'type': 'features'
            },
            {
                'id': 'guide',
                'title': 'Complete Guide',
                'content': f'Step-by-step guide to mastering {main_keyword}.',
                'type': 'guide'
            },
            {
                'id': 'resources',
                'title': 'Resources',
                'content': f'Additional resources and tools for {main_keyword}.',
                'type': 'resources'
            }
        ]
        
        # 根据主题添加特定内容
        theme_sections = {
            'weather': [
                {
                    'id': 'forecast',
                    'title': 'Weather Forecast',
                    'content': 'Get accurate weather predictions and alerts.',
                    'type': 'forecast'
                },
                {
                    'id': 'safety',
                    'title': 'Safety Guidelines',
                    'content': 'Important safety information and emergency procedures.',
                    'type': 'safety'
                }
            ],
            'ai': [
                {
                    'id': 'tools',
                    'title': 'AI Tools',
                    'content': 'Explore the latest AI tools and technologies.',
                    'type': 'tools'
                },
                {
                    'id': 'tutorials',
                    'title': 'Tutorials',
                    'content': 'Learn AI with our comprehensive tutorials.',
                    'type': 'tutorials'
                }
            ],
            'technology': [
                {
                    'id': 'reviews',
                    'title': 'Product Reviews',
                    'content': 'In-depth reviews of the latest technology products.',
                    'type': 'reviews'
                },
                {
                    'id': 'news',
                    'title': 'Tech News',
                    'content': 'Stay updated with the latest technology news.',
                    'type': 'news'
                }
            ]
        }
        
        if theme in theme_sections:
            base_sections.extend(theme_sections[theme])
        
        return base_sections
    
    def _generate_navigation(self, main_keyword: str, theme: str) -> List[Dict]:
        """生成导航菜单"""
        base_nav = [
            {'text': 'Home', 'href': '#hero'},
            {'text': 'Features', 'href': '#features'},
            {'text': 'Guide', 'href': '#guide'},
            {'text': 'Resources', 'href': '#resources'}
        ]
        
        theme_nav = {
            'weather': [
                {'text': 'Forecast', 'href': '#forecast'},
                {'text': 'Safety', 'href': '#safety'}
            ],
            'ai': [
                {'text': 'Tools', 'href': '#tools'},
                {'text': 'Tutorials', 'href': '#tutorials'}
            ],
            'technology': [
                {'text': 'Reviews', 'href': '#reviews'},
                {'text': 'News', 'href': '#news'}
            ]
        }
        
        if theme in theme_nav:
            base_nav.extend(theme_nav[theme])
        
        return base_nav
    
    def _generate_footer_links(self, main_keyword: str, theme: str) -> List[Dict]:
        """生成页脚链接"""
        return [
            {'text': 'About', 'href': '#about'},
            {'text': 'Contact', 'href': '#contact'},
            {'text': 'Privacy Policy', 'href': '#privacy'},
            {'text': 'Terms of Service', 'href': '#terms'}
        ]
    
    def _generate_html_content(self, website_plan: Dict, project_info: Dict) -> str:
        """生成HTML内容"""
        # 这里应该调用实际的HTML生成器
        # 为了演示，我们生成一个基础的HTML模板
        
        html_template = f"""<!DOCTYPE html>
<html lang="{project_info.get('language', 'en')}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{website_plan['title']}</title>
    <meta name="description" content="{website_plan['description']}">
    <meta name="keywords" content="{project_info['main_keyword']}, guide, resources, tools">
    <link rel="stylesheet" href="/css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <header class="header">
        <nav class="navbar">
            <div class="container">
                <div class="nav-brand">
                    <a href="/"><i class="fas fa-star"></i> {website_plan['site_name']}</a>
                </div>
                <ul class="nav-menu">
                    {self._generate_nav_html(website_plan['navigation'])}
                </ul>
            </div>
        </nav>
    </header>
    
    <main class="main-content">
        {self._generate_sections_html(website_plan['sections'])}
    </main>
    
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>{website_plan['site_name']}</h3>
                    <p>{website_plan['description']}</p>
                </div>
                <div class="footer-section">
                    <h3>Quick Links</h3>
                    <ul>
                        {self._generate_footer_links_html(website_plan['footer_links'])}
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; {datetime.now().year} {website_plan['site_name']}. All rights reserved.</p>
            </div>
        </div>
    </footer>
    
    <script src="/js/main.js"></script>
</body>
</html>"""
        
        return html_template
    
    def _generate_nav_html(self, navigation: List[Dict]) -> str:
        """生成导航HTML"""
        nav_items = []
        for item in navigation:
            nav_items.append(f'<li><a href="{item["href"]}">{item["text"]}</a></li>')
        return '\n                    '.join(nav_items)
    
    def _generate_sections_html(self, sections: List[Dict]) -> str:
        """生成内容部分HTML"""
        sections_html = []
        
        for section in sections:
            if section['type'] == 'hero':
                sections_html.append(f"""
        <section id="{section['id']}" class="hero">
            <div class="container">
                <div class="hero-content">
                    <h1 class="hero-title">{section['title']}</h1>
                    <p class="hero-subtitle">{section['content']}</p>
                </div>
            </div>
        </section>""")
            else:
                sections_html.append(f"""
        <section id="{section['id']}" class="section">
            <div class="container">
                <h2>{section['title']}</h2>
                <p>{section['content']}</p>
            </div>
        </section>""")
        
        return '\n'.join(sections_html)
    
    def _generate_footer_links_html(self, footer_links: List[Dict]) -> str:
        """生成页脚链接HTML"""
        links = []
        for link in footer_links:
            links.append(f'<li><a href="{link["href"]}">{link["text"]}</a></li>')
        return '\n                        '.join(links)
    
    def _generate_support_files(self, project_info: Dict, seo_config: Dict) -> Dict:
        """生成支持文件"""
        support_files = {}
        
        # CSS文件
        support_files['css/style.css'] = self._generate_css_content()
        
        # JavaScript文件
        support_files['js/main.js'] = self._generate_js_content()
        
        # Sitemap
        support_files['sitemap.xml'] = self._generate_sitemap(seo_config)
        
        # Robots.txt
        support_files['robots.txt'] = self._generate_robots_txt(seo_config)
        
        # Vercel配置
        support_files['vercel.json'] = self._generate_vercel_config()
        
        return support_files
    
    def _generate_css_content(self) -> str:
        """生成CSS内容"""
        return """
/* 基础样式 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* 头部样式 */
.header {
    background: #fff;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 1000;
}

.navbar {
    padding: 1rem 0;
}

.navbar .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.nav-brand a {
    font-size: 1.5rem;
    font-weight: bold;
    color: #3498db;
    text-decoration: none;
}

.nav-menu {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-menu a {
    color: #666;
    text-decoration: none;
    transition: color 0.3s;
}

.nav-menu a:hover {
    color: #3498db;
}

/* 主要内容样式 */
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 100px 0;
    text-align: center;
}

.hero-title {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.hero-subtitle {
    font-size: 1.2rem;
    opacity: 0.9;
}

.section {
    padding: 80px 0;
}

.section h2 {
    font-size: 2.5rem;
    margin-bottom: 2rem;
    text-align: center;
    color: #333;
}

/* 页脚样式 */
.footer {
    background: #2c3e50;
    color: white;
    padding: 40px 0 20px;
}

.footer-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
}

.footer-section h3 {
    margin-bottom: 1rem;
}

.footer-section ul {
    list-style: none;
}

.footer-section ul li {
    margin-bottom: 0.5rem;
}

.footer-section a {
    color: #bdc3c7;
    text-decoration: none;
    transition: color 0.3s;
}

.footer-section a:hover {
    color: white;
}

.footer-bottom {
    text-align: center;
    padding-top: 2rem;
    border-top: 1px solid #34495e;
    color: #bdc3c7;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .nav-menu {
        flex-direction: column;
        gap: 1rem;
    }
    
    .hero-title {
        font-size: 2rem;
    }
    
    .section h2 {
        font-size: 2rem;
    }
}
"""
    
    def _generate_js_content(self) -> str:
        """生成JavaScript内容"""
        return """
// 基础JavaScript功能
document.addEventListener('DOMContentLoaded', function() {
    // 平滑滚动
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // 导航栏滚动效果
    window.addEventListener('scroll', function() {
        const header = document.querySelector('.header');
        if (window.scrollY > 100) {
            header.style.background = 'rgba(255, 255, 255, 0.95)';
            header.style.backdropFilter = 'blur(10px)';
        } else {
            header.style.background = '#fff';
            header.style.backdropFilter = 'none';
        }
    });
    
    console.log('Website loaded successfully!');
});
"""
    
    def _generate_sitemap(self, seo_config: Dict) -> str:
        """生成Sitemap"""
        base_url = seo_config.get('canonical_url', 'https://example.com')
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
    
    def _generate_robots_txt(self, seo_config: Dict) -> str:
        """生成robots.txt"""
        base_url = seo_config.get('canonical_url', 'https://example.com')
        
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
    
    def _save_website_files(self, project_info: Dict, html_content: str, support_files: Dict) -> str:
        """保存网站文件"""
        output_path = Path(project_info['directory'])
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存主HTML文件
        (output_path / 'index.html').write_text(html_content, encoding='utf-8')
        
        # 保存支持文件
        for file_path, content in support_files.items():
            file_full_path = output_path / file_path
            file_full_path.parent.mkdir(parents=True, exist_ok=True)
            file_full_path.write_text(content, encoding='utf-8')
        
        # 保存项目信息
        project_info_path = output_path / 'project_info.json'
        project_info_path.write_text(
            json.dumps(project_info, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        
        return str(output_path)
    
    def _generate_seo_report(self, seo_config: Dict, html_content: str) -> Dict:
        """生成SEO报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'seo_score': self._calculate_seo_score(seo_config, html_content),
            'optimizations_applied': [
                'Basic SEO tags',
                'Open Graph tags',
                'Twitter Cards',
                'Structured data',
                'Image optimization',
                'Internal linking',
                'Breadcrumb navigation',
                'FAQ section'
            ],
            'recommendations': [
                'Monitor page loading speed',
                'Test mobile responsiveness',
                'Validate structured data',
                'Check link integrity',
                'Update content regularly'
            ]
        }
        
        return report
    
    def _calculate_seo_score(self, seo_config: Dict, html_content: str) -> int:
        """计算SEO得分"""
        score = 0
        
        # 基础标签 (20分)
        if seo_config.get('title'): score += 5
        if seo_config.get('description'): score += 5
        if seo_config.get('keywords'): score += 3
        if seo_config.get('canonical_url'): score += 4
        if seo_config.get('robots'): score += 3
        
        # 社交媒体标签 (15分)
        if 'og:title' in html_content: score += 4
        if 'og:description' in html_content: score += 4
        if 'twitter:card' in html_content: score += 7
        
        # 结构化数据 (20分)
        if 'application/ld+json' in html_content: score += 20
        
        # 内容优化 (25分)
        if '<header>' in html_content: score += 5
        if '<main>' in html_content: score += 5
        if '<section>' in html_content: score += 5
        if 'breadcrumb' in html_content.lower(): score += 5
        if 'faq' in html_content.lower(): score += 5
        
        # 技术SEO (20分)
        if 'viewport' in html_content: score += 8
        if 'font-awesome' in html_content: score += 7
        if 'application/ld+json' in html_content: score += 5
        
        return min(score, 100)  # 最高100分


# 使用示例和测试函数
def test_enhanced_website_builder():
    """测试增强版网站构建器"""
    builder = EnhancedWebsiteBuilder()
    
    # 测试配置
    test_config = {
        'project_name': 'AI Tools Guide',
        'main_keyword': 'ai tools',
        'theme': 'ai',
        'target_audience': 'developers',
        'language': 'en'
    }
    
    # 构建网站
    result = builder.build_optimized_website(test_config)
    
    if result['success']:
        print(f"✅ 网站构建成功!")
        print(f"📁 输出路径: {result['output_path']}")
        print(f"📊 SEO得分: {result['seo_report']['seo_score']}/100")
        print(f"📄 创建文件: {', '.join(result['files_created'])}")
        
        # 显示SEO优化项目
        print("\n🔧 应用的SEO优化:")
        for optimization in result['seo_report']['optimizations_applied']:
            print(f"  ✓ {optimization}")
        
        # 显示建议
        print("\n💡 优化建议:")
        for recommendation in result['seo_report']['recommendations']:
            print(f"  • {recommendation}")
    else:
        print(f"❌ 网站构建失败: {result['error']}")
    
    return result


if __name__ == "__main__":
    # 运行测试
    test_result = test_enhanced_website_builder()
