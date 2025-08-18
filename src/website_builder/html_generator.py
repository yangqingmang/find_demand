#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
HTML网站生成器 - 将网站结构转换为实际的HTML文件
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime

class HTMLGenerator:
    """HTML网站生成器类"""
    
    def __init__(self, output_dir: str = "generated_website", use_tailwind: bool = False):
        self.output_dir = output_dir
        self.use_tailwind = use_tailwind
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 创建子目录
        subdirs = ['css', 'js', 'images', 'intent', 'keyword', 'content', 'products', 'categories']
        for subdir in subdirs:
            subdir_path = os.path.join(self.output_dir, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path)
    
    def generate_base_template(self) -> str:
        """Generate base HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <link rel="stylesheet" href="styles.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <header class="header">
        <nav class="navbar">
            <div class="container">
                <div class="nav-brand">
                    <a href="/">Intent-Based Content Platform</a>
                </div>
                <ul class="nav-menu">
                    <li><a href="/">Home</a></li>
                    <li><a href="/intent/i">Information</a></li>
                    <li><a href="/intent/c">Commercial</a></li>
                    <li><a href="/intent/e">Transactional</a></li>
                    <li><a href="/intent/n">Navigational</a></li>
                    <li><a href="/intent/b">Behavioral</a></li>
                    <li><a href="/intent/l">Local</a></li>
                </ul>
            </div>
        </nav>
    </header>
    
    <main class="main-content">
        {content}
    </main>
    
    <footer class="footer">
        <div class="container">
            <div class="footer-content">
                <div class="footer-section">
                    <h3>About Us</h3>
                    <p>Intent-based content platform providing precise content experiences for users.</p>
                </div>
                <div class="footer-section">
                    <h3>Quick Links</h3>
                    <ul>
                        <li><a href="/intent/i">Information</a></li>
                        <li><a href="/intent/c">Commercial</a></li>
                        <li><a href="/intent/e">Transactional</a></li>
                    </ul>
                </div>
                <div class="footer-section">
                    <h3>Contact Us</h3>
                    <p>Email: contact@example.com</p>
                    <p>Phone: +1 123-456-7890</p>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2025 Intent-Based Content Platform. All rights reserved.</p>
            </div>
        </div>
    </footer>
    
    <script src="script.js"></script>
</body>
</html>"""
    
    def generate_homepage(self, structure: Dict[str, Any]) -> str:
        """生成首页HTML"""
        homepage = structure.get('homepage', {})
        
        if self.use_tailwind:
            hero_section = """
            <section class="bg-gradient-to-br from-primary to-secondary text-white py-20">
                <div class="max-w-6xl mx-auto px-6 text-center">
                    <h1 class="text-5xl font-bold mb-6">基于搜索意图的内容平台</h1>
                    <p class="text-xl mb-8 opacity-90">为用户提供精准的内容体验</p>
                    <a href="#intent-nav" class="inline-block bg-white text-primary px-8 py-4 rounded-full font-semibold hover:transform hover:-translate-y-1 transition-all duration-300 shadow-lg">开始探索</a>
                </div>
            </section>
            """
            
            intent_nav_section = """
            <section id="intent-nav" class="py-20 bg-white">
                <div class="max-w-6xl mx-auto px-6">
                    <h2 class="text-4xl font-bold text-center mb-12 text-gray-800">按意图浏览内容</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        <div class="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-gray-100">
                            <i class="fas fa-info-circle text-4xl text-blue-500 mb-4"></i>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">信息获取</h3>
                            <p class="text-gray-600 mb-4">获取定义、概念和教程内容</p>
                            <a href="/intent/i" class="text-blue-500 font-semibold hover:text-blue-600 transition-colors">探索 →</a>
                        </div>
                        <div class="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-gray-100">
                            <i class="fas fa-chart-line text-4xl text-green-500 mb-4"></i>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">商业评估</h3>
                            <p class="text-gray-600 mb-4">产品对比、评测和推荐</p>
                            <a href="/intent/c" class="text-green-500 font-semibold hover:text-green-600 transition-colors">探索 →</a>
                        </div>
                        <div class="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-gray-100">
                            <i class="fas fa-shopping-cart text-4xl text-red-500 mb-4"></i>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">交易购买</h3>
                            <p class="text-gray-600 mb-4">价格信息和优惠折扣</p>
                            <a href="/intent/e" class="text-red-500 font-semibold hover:text-red-600 transition-colors">探索 →</a>
                        </div>
                        <div class="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-gray-100">
                            <i class="fas fa-compass text-4xl text-purple-500 mb-4"></i>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">导航直达</h3>
                            <p class="text-gray-600 mb-4">登录入口和下载链接</p>
                            <a href="/intent/n" class="text-purple-500 font-semibold hover:text-purple-600 transition-colors">探索 →</a>
                        </div>
                        <div class="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-gray-100">
                            <i class="fas fa-cogs text-4xl text-yellow-500 mb-4"></i>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">行为后续</h3>
                            <p class="text-gray-600 mb-4">故障解决和高级配置</p>
                            <a href="/intent/b" class="text-yellow-500 font-semibold hover:text-yellow-600 transition-colors">探索 →</a>
                        </div>
                        <div class="bg-white p-8 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-gray-100">
                            <i class="fas fa-map-marker-alt text-4xl text-indigo-500 mb-4"></i>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">本地/到店</h3>
                            <p class="text-gray-600 mb-4">附近门店和路线信息</p>
                            <a href="/intent/l" class="text-indigo-500 font-semibold hover:text-indigo-600 transition-colors">探索 →</a>
                        </div>
                    </div>
                </div>
            </section>
            """
        else:
            hero_section = """
            <section class="hero">
                <div class="container">
                    <div class="hero-content">
                        <h1 class="hero-title">Intent-Based Content Platform</h1>
                        <p class="hero-subtitle">Providing precise content experiences for users</p>
                        <a href="#intent-nav" class="cta-button">Start Exploring</a>
                    </div>
                </div>
            </section>
            """
            
            intent_nav_section = """
            <section id="intent-nav" class="intent-navigation">
                <div class="container">
                    <h2>Browse Content by Intent</h2>
                    <div class="intent-grid">
                        <div class="intent-card">
                            <i class="fas fa-info-circle"></i>
                            <h3>Information</h3>
                            <p>Get definitions, concepts and tutorial content</p>
                            <a href="/intent/i" class="intent-link">Explore →</a>
                        </div>
                        <div class="intent-card">
                            <i class="fas fa-chart-line"></i>
                            <h3>Commercial</h3>
                            <p>Product comparisons, reviews and recommendations</p>
                            <a href="/intent/c" class="intent-link">Explore →</a>
                        </div>
                        <div class="intent-card">
                            <i class="fas fa-shopping-cart"></i>
                            <h3>Transactional</h3>
                            <p>Pricing information and discount offers</p>
                            <a href="/intent/e" class="intent-link">Explore →</a>
                        </div>
                        <div class="intent-card">
                            <i class="fas fa-compass"></i>
                            <h3>Navigational</h3>
                            <p>Login portals and download links</p>
                            <a href="/intent/n" class="intent-link">Explore →</a>
                        </div>
                        <div class="intent-card">
                            <i class="fas fa-cogs"></i>
                            <h3>Behavioral</h3>
                            <p>Troubleshooting and advanced configuration</p>
                            <a href="/intent/b" class="intent-link">Explore →</a>
                        </div>
                        <div class="intent-card">
                            <i class="fas fa-map-marker-alt"></i>
                            <h3>Local</h3>
                            <p>Nearby stores and location information</p>
                            <a href="/intent/l" class="intent-link">Explore →</a>
                        </div>
                    </div>
                </div>
            </section>
            """
        
        content = hero_section + intent_nav_section
        
        return self.generate_base_template().format(
            title="Intent-Based Content Platform - Home",
            description="Providing precise content experiences based on search intent, covering information retrieval, commercial evaluation, transactions and more.",
            keywords="search intent,content platform,AI tools,information retrieval,commercial evaluation",
            content=content
        )
    
    def generate_intent_page(self, intent: str, intent_data: List[Dict[str, Any]]) -> str:
        """生成意图页面HTML"""
        intent_names = {
            'I': 'Information',
            'C': 'Commercial', 
            'E': 'Transactional',
            'N': 'Navigational',
            'B': 'Behavioral',
            'L': 'Local'
        }
        
        intent_name = intent_names.get(intent, intent)
        
        # 生成页面内容
        content = f"""
        <section class="page-header">
            <div class="container">
                <h1>{intent_name}内容总览</h1>
                <p>探索{intent_name}相关的所有内容和资源</p>
            </div>
        </section>
        
        <section class="content-grid">
            <div class="container">
                <div class="grid">
        """
        
        # 添加关键词内容卡片
        for item in intent_data:
            if item.get('type') == 'keyword':
                keyword = item.get('keyword', '')
                title = item.get('title', keyword)
                url = item.get('url', '#')
                
                content += f"""
                    <div class="content-card">
                        <h3><a href="{url}">{title}</a></h3>
                        <p>Keyword: {keyword}</p>
                        <div class="card-meta">
                            <span class="intent-tag">{intent_name}</span>
                            <span class="priority-tag">{item.get('seo_priority', 'medium')}</span>
                        </div>
                    </div>
                """
        
        content += """
                </div>
            </div>
        </section>
        """
        
        return self.generate_base_template().format(
            title=f"{intent_name}内容总览 - 基于搜索意图的内容平台",
            description=f"探索{intent_name}相关的所有内容，包括相关关键词和详细信息。",
            keywords=f"{intent_name},搜索意图,内容平台",
            content=content
        )
    
    def generate_keyword_page(self, keyword: str, intent: str) -> str:
        """生成关键词页面HTML"""
        intent_names = {
            'I': 'Information',
            'C': 'Commercial', 
            'E': 'Transactional',
            'N': 'Navigational',
            'B': 'Behavioral',
            'L': 'Local'
        }
        
        intent_name = intent_names.get(intent, intent)
        
        content = f"""
        <section class="page-header">
            <div class="container">
                <h1>{keyword}</h1>
                <div class="breadcrumb">
                    <a href="/">首页</a> > 
                    <a href="/intent/{intent.lower()}">{intent_name}</a> > 
                    {keyword}
                </div>
            </div>
        </section>
        
        <section class="keyword-content">
            <div class="container">
                <div class="content-wrapper">
                    <article class="main-content">
                        <h2>About "{keyword}"</h2>
                        <p>Here is detailed content about "{keyword}". Based on search intent analysis, this keyword belongs to the {intent_name} category.</p>
                        
                        <div class="content-sections">
                            <section class="content-section">
                                <h3>Overview</h3>
                                <p>Comprehensive introduction and analysis of "{keyword}".</p>
                            </section>
                            
                            <section class="content-section">
                                <h3>Detailed Information</h3>
                                <p>More detailed information and usage guide about "{keyword}".</p>
                            </section>
                            
                            <section class="content-section">
                                <h3>Related Resources</h3>
                                <ul>
                                    <li>Related tools and resource links</li>
                                    <li>Further learning materials</li>
                                    <li>Community discussions and support</li>
                                </ul>
                            </section>
                        </div>
                    </article>
                    
                    <aside class="sidebar">
                        <div class="sidebar-widget">
                            <h3>相关内容</h3>
                            <ul>
                                <li><a href="/intent/{intent.lower()}">更多{intent_name}内容</a></li>
                                <li><a href="/">返回首页</a></li>
                            </ul>
                        </div>
                    </aside>
                </div>
            </div>
        </section>
        """
        
        return self.generate_base_template().format(
            title=f"{keyword} - {intent_name} - Intent-Based Content Platform",
            description=f"Detailed information and guide about {keyword}, belonging to {intent_name} search intent category.",
            keywords=f"{keyword},{intent_name},search intent",
            content=content
        )
    
    def generate_css(self) -> str:
        """生成CSS样式文件"""
        return """/* 基础样式重置 */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8f9fa;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* 头部导航 */
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
    color: #2c3e50;
    text-decoration: none;
}

.nav-menu {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-menu a {
    color: #555;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.3s;
}

.nav-menu a:hover {
    color: #3498db;
}

/* 主要内容区域 */
.main-content {
    min-height: calc(100vh - 200px);
}

/* 英雄区域 */
.hero {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 4rem 0;
    text-align: center;
}

.hero-title {
    font-size: 3rem;
    margin-bottom: 1rem;
    font-weight: 700;
}

.hero-subtitle {
    font-size: 1.2rem;
    margin-bottom: 2rem;
    opacity: 0.9;
}

.cta-button {
    display: inline-block;
    background: #fff;
    color: #667eea;
    padding: 1rem 2rem;
    border-radius: 50px;
    text-decoration: none;
    font-weight: 600;
    transition: transform 0.3s, box-shadow 0.3s;
}

.cta-button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

/* 意图导航 */
.intent-navigation {
    padding: 4rem 0;
    background: #fff;
}

.intent-navigation h2 {
    text-align: center;
    margin-bottom: 3rem;
    font-size: 2.5rem;
    color: #2c3e50;
}

.intent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.intent-card {
    background: #fff;
    padding: 2rem;
    border-radius: 15px;
    box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    text-align: center;
    transition: transform 0.3s, box-shadow 0.3s;
}

.intent-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 35px rgba(0,0,0,0.15);
}

.intent-card i {
    font-size: 3rem;
    color: #3498db;
    margin-bottom: 1rem;
}

.intent-card h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: #2c3e50;
}

.intent-card p {
    color: #666;
    margin-bottom: 1.5rem;
}

.intent-link {
    color: #3498db;
    text-decoration: none;
    font-weight: 600;
    transition: color 0.3s;
}

.intent-link:hover {
    color: #2980b9;
}

/* 页面头部 */
.page-header {
    background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
    color: white;
    padding: 3rem 0;
    text-align: center;
}

.page-header h1 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.breadcrumb {
    margin-top: 1rem;
    opacity: 0.9;
}

.breadcrumb a {
    color: white;
    text-decoration: none;
}

.breadcrumb a:hover {
    text-decoration: underline;
}

/* 内容网格 */
.content-grid {
    padding: 4rem 0;
    background: #f8f9fa;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
}

.content-card {
    background: #fff;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 3px 15px rgba(0,0,0,0.1);
    transition: transform 0.3s;
}

.content-card:hover {
    transform: translateY(-3px);
}

.content-card h3 {
    margin-bottom: 1rem;
}

.content-card h3 a {
    color: #2c3e50;
    text-decoration: none;
}

.content-card h3 a:hover {
    color: #3498db;
}

.card-meta {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
}

.intent-tag, .priority-tag {
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
}

.intent-tag {
    background: #e3f2fd;
    color: #1976d2;
}

.priority-tag {
    background: #f3e5f5;
    color: #7b1fa2;
}

/* 关键词页面 */
.keyword-content {
    padding: 4rem 0;
    background: #fff;
}

.content-wrapper {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 3rem;
}

.main-content {
    background: #fff;
}

.content-section {
    margin-bottom: 2rem;
}

.content-section h3 {
    color: #2c3e50;
    margin-bottom: 1rem;
    font-size: 1.3rem;
}

.sidebar {
    background: #f8f9fa;
    padding: 2rem;
    border-radius: 10px;
    height: fit-content;
}

.sidebar-widget h3 {
    margin-bottom: 1rem;
    color: #2c3e50;
}

.sidebar-widget ul {
    list-style: none;
}

.sidebar-widget li {
    margin-bottom: 0.5rem;
}

.sidebar-widget a {
    color: #3498db;
    text-decoration: none;
}

.sidebar-widget a:hover {
    text-decoration: underline;
}

/* 底部 */
.footer {
    background: #2c3e50;
    color: white;
    padding: 3rem 0 1rem;
}

.footer-content {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
    margin-bottom: 2rem;
}

.footer-section h3 {
    margin-bottom: 1rem;
    color: #3498db;
}

.footer-section ul {
    list-style: none;
}

.footer-section li {
    margin-bottom: 0.5rem;
}

.footer-section a {
    color: #bdc3c7;
    text-decoration: none;
}

.footer-section a:hover {
    color: white;
}

.footer-bottom {
    border-top: 1px solid #34495e;
    padding-top: 1rem;
    text-align: center;
    color: #bdc3c7;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2rem;
    }
    
    .intent-grid {
        grid-template-columns: 1fr;
    }
    
    .content-wrapper {
        grid-template-columns: 1fr;
    }
    
    .nav-menu {
        flex-direction: column;
        gap: 1rem;
    }
}"""
    
    def generate_js(self) -> str:
        """生成JavaScript文件"""
        return """// 主要JavaScript功能
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
    
    // 搜索功能（如果需要）
    const searchInput = document.querySelector('#search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const cards = document.querySelectorAll('.content-card');
            
            cards.forEach(card => {
                const title = card.querySelector('h3').textContent.toLowerCase();
                const content = card.textContent.toLowerCase();
                
                if (title.includes(query) || content.includes(query)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    // 返回顶部按钮
    const backToTop = document.createElement('button');
    backToTop.innerHTML = '<i class="fas fa-arrow-up"></i>';
    backToTop.className = 'back-to-top';
    backToTop.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #3498db;
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        cursor: pointer;
        display: none;
        z-index: 1000;
        transition: all 0.3s;
    `;
    
    document.body.appendChild(backToTop);
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTop.style.display = 'block';
        } else {
            backToTop.style.display = 'none';
        }
    });
    
    backToTop.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
});"""
    
    def generate_website(self, structure_file: str, content_plan_file: str = None):
        """生成完整网站"""
        # 读取网站结构
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure = json.load(f)
        
        print("Starting website generation...")
        
        # Generate homepage
        homepage_html = self.generate_homepage(structure)
        with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(homepage_html)
        print("✅ Homepage generation completed")
        
        # Generate intent pages
        intent_pages = structure.get('intent_pages', {})
        for intent, pages in intent_pages.items():
            intent_html = self.generate_intent_page(intent, pages)
            intent_file = os.path.join(self.output_dir, 'intent', f'{intent.lower()}.html')
            with open(intent_file, 'w', encoding='utf-8') as f:
                f.write(intent_html)
            
            # Generate keyword pages
            for page in pages:
                if page.get('type') == 'keyword':
                    keyword = page.get('keyword', '')
                    keyword_html = self.generate_keyword_page(keyword, intent)
                    keyword_slug = keyword.replace(' ', '-').lower()
                    keyword_file = os.path.join(self.output_dir, 'keyword', f'{keyword_slug}.html')
                    with open(keyword_file, 'w', encoding='utf-8') as f:
                        f.write(keyword_html)
        
        print(f"✅ Intent pages and keyword pages generation completed")
        
        # Generate CSS file - 直接在根目录创建 styles.css
        css_content = self.generate_css()
        with open(os.path.join(self.output_dir, 'styles.css'), 'w', encoding='utf-8') as f:
            f.write(css_content)
        print("✅ CSS stylesheet generation completed")
        
        # Generate JavaScript file - 直接在根目录创建 script.js
        js_content = self.generate_js()
        with open(os.path.join(self.output_dir, 'script.js'), 'w', encoding='utf-8') as f:
            f.write(js_content)
        print("✅ JavaScript file generation completed")
        
        # Generate sitemap
        self.generate_sitemap(structure)
        print("✅ Sitemap generation completed")
        
        print(f"\n🎉 Website generation completed! Files saved in: {self.output_dir}")
        print(f"📁 Total generated files: {self.count_generated_files()}")
    
    def generate_sitemap(self, structure: Dict[str, Any]):
        """生成网站地图"""
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/</loc>
        <lastmod>{date}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
""".format(date=datetime.now().strftime('%Y-%m-%d'))
        
        # 添加意图页面
        intent_pages = structure.get('intent_pages', {})
        for intent, pages in intent_pages.items():
            for page in pages:
                url = page.get('url', '')
                if url:
                    sitemap_content += f"""    <url>
        <loc>https://example.com{url}</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
"""
        
        sitemap_content += "</urlset>"
        
        with open(os.path.join(self.output_dir, 'sitemap.xml'), 'w', encoding='utf-8') as f:
            f.write(sitemap_content)
    
    def count_generated_files(self) -> int:
        """统计生成的文件数量"""
        count = 0
        for root, dirs, files in os.walk(self.output_dir):
            count += len(files)
        return count

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='HTML网站生成器')
    parser.add_argument('--structure', '-s', required=True, help='网站结构JSON文件路径')
    parser.add_argument('--content', '-c', help='内容计划JSON文件路径')
    parser.add_argument('--output', '-o', default='generated_website', help='输出目录')
    
    args = parser.parse_args()
    
    generator = HTMLGenerator(args.output)
    generator.generate_website(args.structure, args.content)

if __name__ == "__main__":
    main()