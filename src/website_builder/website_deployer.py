#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
网站部署集成模块 - 将建站脚本与部署功能集成
"""

import os
import sys
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.deployment.deployment_manager import DeploymentManager
from src.website_builder.html_generator import HTMLGenerator


class WebsiteDeployer:
    """网站部署器 - 集成建站和部署功能"""

    def __init__(self, deployment_config_path: str = None):
        """
        初始化网站部署器
        
        Args:
            deployment_config_path: 部署配置文件路径
        """
        self.deployment_manager = DeploymentManager(deployment_config_path)
        self.html_generator = HTMLGenerator()

    def deploy_website_structure(self, 
                                website_structure: Dict[str, Any],
                                content_plan: List[Dict[str, Any]],
                                output_dir: str,
                                deployer_name: str = None,
                                custom_config: Dict[str, Any] = None) -> Tuple[bool, str]:
        """
        部署网站结构
        
        Args:
            website_structure: 网站结构
            content_plan: 内容计划
            output_dir: 输出目录
            deployer_name: 部署服务名称
            custom_config: 自定义配置
            
        Returns:
            (是否成功, 部署URL或错误信息)
        """
        try:
            # 1. 生成HTML文件
            print("正在生成HTML文件...")
            html_output_dir = os.path.join(output_dir, 'html')
            
            if not self._generate_html_files(website_structure, content_plan, html_output_dir):
                return False, "HTML文件生成失败"
            
            # 2. 部署到云服务器
            print(f"正在部署到 {deployer_name or '默认服务'}...")
            success, result, deployment_info = self.deployment_manager.deploy_website(
                source_dir=html_output_dir,
                deployer_name=deployer_name,
                custom_config=custom_config
            )
            
            if success:
                # 保存部署信息
                self._save_deployment_info(output_dir, deployment_info)
                return True, result
            else:
                return False, result
                
        except Exception as e:
            return False, f"部署过程中发生错误: {e}"

    def _generate_html_files(self, 
                           website_structure: Dict[str, Any],
                           content_plan: List[Dict[str, Any]],
                           output_dir: str) -> bool:
        """
        生成HTML文件
        
        Args:
            website_structure: 网站结构
            content_plan: 内容计划
            output_dir: 输出目录
            
        Returns:
            是否成功
        """
        try:
            # 确保输出目录存在
            os.makedirs(output_dir, exist_ok=True)
            
            # 生成首页
            if not self._generate_homepage(website_structure, output_dir):
                return False
            
            # 生成意图页面
            if not self._generate_intent_pages(website_structure, output_dir):
                return False
            
            # 生成内容页面
            if not self._generate_content_pages(website_structure, content_plan, output_dir):
                return False
            
            # 生成CSS和JS文件
            if not self._generate_assets(output_dir):
                return False
            
            print(f"HTML文件生成完成: {output_dir}")
            return True
            
        except Exception as e:
            print(f"HTML文件生成失败: {e}")
            return False

    def _generate_homepage(self, website_structure: Dict[str, Any], output_dir: str) -> bool:
        """生成首页"""
        try:
            homepage = website_structure.get('homepage', {})
            
            html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{homepage.get('title', '基于搜索意图的内容平台')}</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header>
        <nav>
            <h1>{homepage.get('title', '基于搜索意图的内容平台')}</h1>
        </nav>
    </header>
    
    <main>
        <section class="hero">
            <h2>为用户提供精准的内容体验</h2>
            <p>基于搜索意图分析，提供个性化的内容推荐</p>
        </section>
        
        <section class="intent-nav">
            <h3>按意图浏览</h3>
            <div class="intent-grid">
"""
            
            # 添加意图导航
            intent_pages = website_structure.get('intent_pages', {})
            for intent, pages in intent_pages.items():
                if pages:
                    first_page = pages[0]
                    html_content += f"""
                <div class="intent-card">
                    <h4><a href="{first_page['url']}">{first_page.get('intent_name', intent)}</a></h4>
                    <p>探索{first_page.get('intent_name', intent)}相关内容</p>
                </div>
"""
            
            html_content += """
            </div>
        </section>
    </main>
    
    <footer>
        <p>&copy; 2024 基于搜索意图的内容平台</p>
    </footer>
</body>
</html>
"""
            
            # 保存首页文件
            index_path = os.path.join(output_dir, 'index.html')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"首页生成失败: {e}")
            return False

    def _generate_intent_pages(self, website_structure: Dict[str, Any], output_dir: str) -> bool:
        """生成意图页面"""
        try:
            intent_pages = website_structure.get('intent_pages', {})
            
            for intent, pages in intent_pages.items():
                for page in pages:
                    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page['title']}</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <header>
        <nav>
            <a href="../index.html">首页</a>
            <h1>{page['title']}</h1>
        </nav>
    </header>
    
    <main>
        <article>
            <h2>{page['title']}</h2>
            <p>这是关于{page.get('intent_name', intent)}的内容页面。</p>
            
            <section>
                <h3>相关内容</h3>
                <p>在这里展示与{page.get('intent_name', intent)}相关的内容列表。</p>
            </section>
        </article>
    </main>
    
    <footer>
        <p>&copy; 2024 基于搜索意图的内容平台</p>
    </footer>
</body>
</html>
"""
                    
                    # 创建目录结构
                    page_dir = os.path.dirname(page['url'].lstrip('/'))
                    if page_dir:
                        full_page_dir = os.path.join(output_dir, page_dir)
                        os.makedirs(full_page_dir, exist_ok=True)
                    
                    # 保存页面文件
                    page_filename = os.path.basename(page['url']) or 'index.html'
                    if not page_filename.endswith('.html'):
                        page_filename += '.html'
                    
                    page_path = os.path.join(output_dir, page['url'].lstrip('/'))
                    if page_path.endswith('/'):
                        page_path = os.path.join(page_path, 'index.html')
                    elif not page_path.endswith('.html'):
                        page_path += '.html'
                    
                    os.makedirs(os.path.dirname(page_path), exist_ok=True)
                    
                    with open(page_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"意图页面生成失败: {e}")
            return False

    def _generate_content_pages(self, 
                              website_structure: Dict[str, Any],
                              content_plan: List[Dict[str, Any]],
                              output_dir: str) -> bool:
        """生成内容页面"""
        try:
            content_pages = website_structure.get('content_pages', {})
            
            for page_id, page in content_pages.items():
                # 从内容计划中找到对应的内容
                page_content = None
                for content in content_plan:
                    if content.get('page_url') == page['url']:
                        page_content = content
                        break
                
                html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{page['title']}</title>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <header>
        <nav>
            <a href="../index.html">首页</a>
            <h1>{page['title']}</h1>
        </nav>
    </header>
    
    <main>
        <article>
            <h2>{page['title']}</h2>
            <p>关键词: {page.get('keyword', '')}</p>
            <p>意图类型: {page.get('intent', '')}</p>
            
"""
                
                # 添加内容区块
                if page_content and 'sections' in page_content:
                    for section in page_content['sections']:
                        html_content += f"""
            <section>
                <h3>{section['name']}</h3>
                <p>这里是{section['name']}的内容，建议字数: {section.get('word_count', 0)}字</p>
            </section>
"""
                
                html_content += """
        </article>
    </main>
    
    <footer>
        <p>&copy; 2024 基于搜索意图的内容平台</p>
    </footer>
</body>
</html>
"""
                
                # 创建目录结构并保存文件
                page_path = os.path.join(output_dir, page['url'].lstrip('/'))
                if page_path.endswith('/'):
                    page_path = os.path.join(page_path, 'index.html')
                elif not page_path.endswith('.html'):
                    page_path += '.html'
                
                os.makedirs(os.path.dirname(page_path), exist_ok=True)
                
                with open(page_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"内容页面生成失败: {e}")
            return False

    def _generate_assets(self, output_dir: str) -> bool:
        """生成CSS和JS文件"""
        try:
            # 生成CSS文件
            css_content = """
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
    background-color: #f5f5f5;
}

header {
    background: #fff;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    padding: 1rem 0;
}

nav {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
    display: flex;
    align-items: center;
    gap: 2rem;
}

nav h1 {
    color: #2563eb;
    font-size: 1.5rem;
}

nav a {
    color: #666;
    text-decoration: none;
    font-weight: 500;
}

nav a:hover {
    color: #2563eb;
}

main {
    max-width: 1200px;
    margin: 2rem auto;
    padding: 0 2rem;
}

/* 首页样式 */
.hero {
    text-align: center;
    padding: 4rem 0;
    background: #fff;
    border-radius: 8px;
    margin-bottom: 3rem;
}

.hero h2 {
    font-size: 2.5rem;
    color: #1f2937;
    margin-bottom: 1rem;
}

.hero p {
    font-size: 1.2rem;
    color: #6b7280;
}

.intent-nav {
    background: #fff;
    padding: 2rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}

.intent-nav h3 {
    font-size: 1.8rem;
    color: #1f2937;
    margin-bottom: 2rem;
    text-align: center;
}

.intent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.intent-card {
    background: #f8fafc;
    padding: 2rem;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
    transition: transform 0.2s, box-shadow 0.2s;
}

.intent-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.intent-card h4 {
    margin-bottom: 1rem;
}

.intent-card h4 a {
    color: #2563eb;
    text-decoration: none;
    font-size: 1.2rem;
}

.intent-card h4 a:hover {
    text-decoration: underline;
}

.intent-card p {
    color: #6b7280;
}

/* 文章页面样式 */
article {
    background: #fff;
    padding: 3rem;
    border-radius: 8px;
    margin-bottom: 2rem;
}

article h2 {
    font-size: 2rem;
    color: #1f2937;
    margin-bottom: 1rem;
}

article section {
    margin: 2rem 0;
}

article section h3 {
    font-size: 1.5rem;
    color: #374151;
    margin-bottom: 1rem;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.5rem;
}

/* 页脚样式 */
footer {
    background: #1f2937;
    color: #fff;
    text-align: center;
    padding: 2rem 0;
    margin-top: 4rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
    nav {
        flex-direction: column;
        gap: 1rem;
    }
    
    .hero h2 {
        font-size: 2rem;
    }
    
    .intent-grid {
        grid-template-columns: 1fr;
    }
    
    article {
        padding: 2rem;
    }
    
    main {
        padding: 0 1rem;
    }
}
"""
            
            css_path = os.path.join(output_dir, 'styles.css')
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(css_content)
            
            return True
            
        except Exception as e:
            print(f"资源文件生成失败: {e}")
            return False

    def _save_deployment_info(self, output_dir: str, deployment_info: Dict[str, Any]) -> None:
        """保存部署信息"""
        try:
            deployment_file = os.path.join(output_dir, 'deployment_info.json')
            
            deployment_record = {
                'timestamp': datetime.now().isoformat(),
                'deployment_info': deployment_info
            }
            
            with open(deployment_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(deployment_record, f, ensure_ascii=False, indent=2)
            
            print(f"部署信息已保存: {deployment_file}")
            
        except Exception as e:
            print(f"保存部署信息失败: {e}")

    def get_available_deployers(self) -> List[str]:
        """获取可用的部署服务"""
        return self.deployment_manager.get_available_deployers()

    def validate_deployment_config(self, deployer_name: str) -> Tuple[bool, str]:
        """验证部署配置"""
        return self.deployment_manager.validate_deployer_config(deployer_name)

    def get_deployment_history(self) -> List[Dict[str, Any]]:
        """获取部署历史"""
        return self.deployment_manager.get_deployment_history()

    def get_deployment_stats(self) -> Dict[str, Any]:
        """获取部署统计信息"""
        return self.deployment_manager.get_deployment_stats()
