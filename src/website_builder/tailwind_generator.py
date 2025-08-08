#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TailwindCSS版本的HTML生成器
"""

import os
import json
from typing import Dict, Any, List
from datetime import datetime

class TailwindHTMLGenerator:
    """使用TailwindCSS的HTML生成器"""
    
    def __init__(self, output_dir: str = "generated_website_tailwind"):
        self.output_dir = output_dir
        self.ensure_output_dir()
    
    def ensure_output_dir(self):
        """确保输出目录存在"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 创建子目录
        subdirs = ['intent', 'keyword', 'content', 'products', 'categories']
        for subdir in subdirs:
            subdir_path = os.path.join(self.output_dir, subdir)
            if not os.path.exists(subdir_path):
                os.makedirs(subdir_path)
    
    def generate_base_template(self) -> str:
        """生成使用TailwindCSS的基础HTML模板"""
        return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="keywords" content="{keywords}">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    colors: {{
                        primary: '#667eea',
                        secondary: '#764ba2',
                    }},
                    animation: {{
                        'fade-in-up': 'fadeInUp 0.6s ease-out',
                        'bounce-in': 'bounceIn 0.8s ease-out',
                    }},
                    keyframes: {{
                        fadeInUp: {{
                            '0%': {{ opacity: '0', transform: 'translateY(30px)' }},
                            '100%': {{ opacity: '1', transform: 'translateY(0)' }},
                        }},
                        bounceIn: {{
                            '0%': {{ opacity: '0', transform: 'scale(0.3)' }},
                            '50%': {{ opacity: '1', transform: 'scale(1.05)' }},
                            '70%': {{ transform: 'scale(0.9)' }},
                            '100%': {{ opacity: '1', transform: 'scale(1)' }},
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body class="bg-gray-50 font-sans">
    <!-- 导航栏 -->
    <header class="bg-white shadow-lg sticky top-0 z-50">
        <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center h-16">
                <div class="flex-shrink-0">
                    <a href="/" class="text-2xl font-bold text-primary hover:text-secondary transition-colors">
                        基于搜索意图的内容平台
                    </a>
                </div>
                <div class="hidden md:block">
                    <div class="ml-10 flex items-baseline space-x-4">
                        <a href="/" class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors">首页</a>
                        <a href="/intent/i" class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors">信息获取</a>
                        <a href="/intent/c" class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors">商业评估</a>
                        <a href="/intent/e" class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors">交易购买</a>
                        <a href="/intent/n" class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors">导航直达</a>
                        <a href="/intent/b" class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors">行为后续</a>
                        <a href="/intent/l" class="text-gray-700 hover:text-primary px-3 py-2 rounded-md text-sm font-medium transition-colors">本地/到店</a>
                    </div>
                </div>
                <!-- 移动端菜单按钮 -->
                <div class="md:hidden">
                    <button type="button" class="text-gray-700 hover:text-primary focus:outline-none focus:text-primary" id="mobile-menu-button">
                        <i class="fas fa-bars text-xl"></i>
                    </button>
                </div>
            </div>
        </nav>
        <!-- 移动端菜单 -->
        <div class="md:hidden hidden" id="mobile-menu">
            <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t">
                <a href="/" class="text-gray-700 hover:text-primary block px-3 py-2 rounded-md text-base font-medium">首页</a>
                <a href="/intent/i" class="text-gray-700 hover:text-primary block px-3 py-2 rounded-md text-base font-medium">信息获取</a>
                <a href="/intent/c" class="text-gray-700 hover:text-primary block px-3 py-2 rounded-md text-base font-medium">商业评估</a>
                <a href="/intent/e" class="text-gray-700 hover:text-primary block px-3 py-2 rounded-md text-base font-medium">交易购买</a>
                <a href="/intent/n" class="text-gray-700 hover:text-primary block px-3 py-2 rounded-md text-base font-medium">导航直达</a>
                <a href="/intent/b" class="text-gray-700 hover:text-primary block px-3 py-2 rounded-md text-base font-medium">行为后续</a>
                <a href="/intent/l" class="text-gray-700 hover:text-primary block px-3 py-2 rounded-md text-base font-medium">本地/到店</a>
            </div>
        </div>
    </header>
    
    <!-- 主要内容 -->
    <main class="min-h-screen">
        {content}
    </main>
    
    <!-- 底部 -->
    <footer class="bg-gray-900 text-white">
        <div class="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                    <h3 class="text-lg font-semibold mb-4 text-primary">关于我们</h3>
                    <p class="text-gray-300">基于搜索意图的内容平台，为用户提供精准的内容体验。</p>
                </div>
                <div>
                    <h3 class="text-lg font-semibold mb-4 text-primary">快速链接</h3>
                    <ul class="space-y-2">
                        <li><a href="/intent/i" class="text-gray-300 hover:text-white transition-colors">信息获取</a></li>
                        <li><a href="/intent/c" class="text-gray-300 hover:text-white transition-colors">商业评估</a></li>
                        <li><a href="/intent/e" class="text-gray-300 hover:text-white transition-colors">交易购买</a></li>
                    </ul>
                </div>
                <div>
                    <h3 class="text-lg font-semibold mb-4 text-primary">联系我们</h3>
                    <p class="text-gray-300">邮箱: contact@example.com</p>
                    <p class="text-gray-300">电话: +86 123-4567-8900</p>
                </div>
            </div>
            <div class="border-t border-gray-700 mt-8 pt-8 text-center">
                <p class="text-gray-400">&copy; 2025 基于搜索意图的内容平台. 保留所有权利.</p>
            </div>
        </div>
    </footer>
    
    <script>
        // 移动端菜单切换
        document.getElementById('mobile-menu-button').addEventListener('click', function() {{
            const menu = document.getElementById('mobile-menu');
            menu.classList.toggle('hidden');
        }});
        
        // 平滑滚动
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{ behavior: 'smooth' }});
                }}
            }});
        }});
    </script>
</body>
</html>"""
    
    def generate_homepage(self, structure: Dict[str, Any]) -> str:
        """生成使用TailwindCSS的首页HTML"""
        hero_section = """
        <!-- 英雄区域 -->
        <section class="bg-gradient-to-br from-primary to-secondary text-white py-20 lg:py-32">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h1 class="text-4xl md:text-6xl font-bold mb-6 animate-fade-in-up">
                    基于搜索意图的内容平台
                </h1>
                <p class="text-xl md:text-2xl mb-8 opacity-90 animate-fade-in-up" style="animation-delay: 0.2s;">
                    为用户提供精准的内容体验
                </p>
                <a href="#intent-nav" class="inline-block bg-white text-primary px-8 py-4 rounded-full font-semibold text-lg hover:transform hover:-translate-y-1 hover:shadow-2xl transition-all duration-300 animate-bounce-in" style="animation-delay: 0.4s;">
                    开始探索
                </a>
            </div>
        </section>
        """
        
        intent_nav_section = """
        <!-- 意图导航区域 -->
        <section id="intent-nav" class="py-20 bg-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <h2 class="text-4xl md:text-5xl font-bold text-center mb-16 text-gray-800">
                    按意图浏览内容
                </h2>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    <!-- 信息获取 -->
                    <div class="group bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border border-gray-100 hover:border-blue-200">
                        <div class="text-center">
                            <div class="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-6 group-hover:bg-blue-200 transition-colors">
                                <i class="fas fa-info-circle text-2xl text-blue-600"></i>
                            </div>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">信息获取</h3>
                            <p class="text-gray-600 mb-6">获取定义、概念和教程内容</p>
                            <a href="/not-supported.html" class="inline-flex items-center text-blue-600 font-semibold hover:text-blue-700 transition-colors">
                                探索 <i class="fas fa-arrow-right ml-2"></i>
                            </a>
                        </div>
                    </div>
                    
                    <!-- 商业评估 -->
                    <div class="group bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border border-gray-100 hover:border-green-200">
                        <div class="text-center">
                            <div class="inline-flex items-center justify-center w-16 h-16 bg-green-100 rounded-full mb-6 group-hover:bg-green-200 transition-colors">
                                <i class="fas fa-chart-line text-2xl text-green-600"></i>
                            </div>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">商业评估</h3>
                            <p class="text-gray-600 mb-6">产品对比、评测和推荐</p>
                            <a href="/not-supported.html" class="inline-flex items-center text-green-600 font-semibold hover:text-green-700 transition-colors">
                                探索 <i class="fas fa-arrow-right ml-2"></i>
                            </a>
                        </div>
                    </div>
                    
                    <!-- 交易购买 -->
                    <div class="group bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border border-gray-100 hover:border-red-200">
                        <div class="text-center">
                            <div class="inline-flex items-center justify-center w-16 h-16 bg-red-100 rounded-full mb-6 group-hover:bg-red-200 transition-colors">
                                <i class="fas fa-shopping-cart text-2xl text-red-600"></i>
                            </div>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">交易购买</h3>
                            <p class="text-gray-600 mb-6">价格信息和优惠折扣</p>
                            <a href="/not-supported.html" class="inline-flex items-center text-red-600 font-semibold hover:text-red-700 transition-colors">
                                探索 <i class="fas fa-arrow-right ml-2"></i>
                            </a>
                        </div>
                    </div>
                    
                    <!-- 导航直达 -->
                    <div class="group bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border border-gray-100 hover:border-purple-200">
                        <div class="text-center">
                            <div class="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-6 group-hover:bg-purple-200 transition-colors">
                                <i class="fas fa-compass text-2xl text-purple-600"></i>
                            </div>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">导航直达</h3>
                            <p class="text-gray-600 mb-6">登录入口和下载链接</p>
                            <a href="/not-supported.html" class="inline-flex items-center text-purple-600 font-semibold hover:text-purple-700 transition-colors">
                                探索 <i class="fas fa-arrow-right ml-2"></i>
                            </a>
                        </div>
                    </div>
                    
                    <!-- 行为后续 -->
                    <div class="group bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border border-gray-100 hover:border-yellow-200">
                        <div class="text-center">
                            <div class="inline-flex items-center justify-center w-16 h-16 bg-yellow-100 rounded-full mb-6 group-hover:bg-yellow-200 transition-colors">
                                <i class="fas fa-cogs text-2xl text-yellow-600"></i>
                            </div>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">行为后续</h3>
                            <p class="text-gray-600 mb-6">故障解决和高级配置</p>
                            <a href="/not-supported.html" class="inline-flex items-center text-yellow-600 font-semibold hover:text-yellow-700 transition-colors">
                                探索 <i class="fas fa-arrow-right ml-2"></i>
                            </a>
                        </div>
                    </div>
                    
                    <!-- 本地/到店 -->
                    <div class="group bg-white p-8 rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-2 border border-gray-100 hover:border-indigo-200">
                        <div class="text-center">
                            <div class="inline-flex items-center justify-center w-16 h-16 bg-indigo-100 rounded-full mb-6 group-hover:bg-indigo-200 transition-colors">
                                <i class="fas fa-map-marker-alt text-2xl text-indigo-600"></i>
                            </div>
                            <h3 class="text-xl font-semibold mb-3 text-gray-800">本地/到店</h3>
                            <p class="text-gray-600 mb-6">附近门店和路线信息</p>
                            <a href="/not-supported.html" class="inline-flex items-center text-indigo-600 font-semibold hover:text-indigo-700 transition-colors">
                                探索 <i class="fas fa-arrow-right ml-2"></i>
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """
        
        content = hero_section + intent_nav_section
        
        return self.generate_base_template().format(
            title="基于搜索意图的内容平台 - 首页",
            description="为用户提供基于搜索意图的精准内容体验，涵盖信息获取、商业评估、交易购买等多个维度。",
            keywords="搜索意图,内容平台,AI工具,信息获取,商业评估",
            content=content
        )
    
    def generate_intent_page(self, intent: str, intent_data: List[Dict[str, Any]]) -> str:
        """生成意图页面HTML"""
        intent_names = {
            'I': '信息获取',
            'C': '商业评估', 
            'E': '交易购买',
            'N': '导航直达',
            'B': '行为后续',
            'L': '本地/到店'
        }
        
        intent_colors = {
            'I': 'blue',
            'C': 'green',
            'E': 'red',
            'N': 'purple',
            'B': 'yellow',
            'L': 'indigo'
        }
        
        intent_name = intent_names.get(intent, intent)
        color = intent_colors.get(intent, 'blue')
        
        # 生成页面内容
        content = f"""
        <!-- 页面头部 -->
        <section class="bg-gradient-to-r from-{color}-500 to-{color}-600 text-white py-16">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
                <h1 class="text-4xl md:text-5xl font-bold mb-4">{intent_name}内容总览</h1>
                <p class="text-xl opacity-90">探索{intent_name}相关的所有内容和资源</p>
            </div>
        </section>
        
        <!-- 内容网格 -->
        <section class="py-16 bg-gray-50">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        """
        
        # 添加关键词内容卡片
        for item in intent_data:
            if item.get('type') == 'keyword':
                keyword = item.get('keyword', '')
                title = item.get('title', keyword)
                url = item.get('url', '#')
                priority = item.get('seo_priority', 'medium')
                
                priority_colors = {
                    'high': 'green',
                    'medium': 'yellow',
                    'low': 'gray'
                }
                priority_color = priority_colors.get(priority, 'gray')
                
                content += f"""
                    <div class="bg-white p-6 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-1">
                        <h3 class="text-xl font-semibold mb-3">
                            <a href="{url}" class="text-gray-800 hover:text-{color}-600 transition-colors">{title}</a>
                        </h3>
                        <p class="text-gray-600 mb-4">关键词: {keyword}</p>
                        <div class="flex items-center justify-between">
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-{color}-100 text-{color}-800">
                                {intent_name}
                            </span>
                            <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-{priority_color}-100 text-{priority_color}-800">
                                {priority}
                            </span>
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
            'I': '信息获取',
            'C': '商业评估', 
            'E': '交易购买',
            'N': '导航直达',
            'B': '行为后续',
            'L': '本地/到店'
        }
        
        intent_colors = {
            'I': 'blue',
            'C': 'green',
            'E': 'red',
            'N': 'purple',
            'B': 'yellow',
            'L': 'indigo'
        }
        
        intent_name = intent_names.get(intent, intent)
        color = intent_colors.get(intent, 'blue')
        
        content = f"""
        <!-- 页面头部 -->
        <section class="bg-gradient-to-r from-{color}-500 to-{color}-600 text-white py-16">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="text-center mb-8">
                    <h1 class="text-4xl md:text-5xl font-bold mb-4">{keyword}</h1>
                    <nav class="text-{color}-100">
                        <a href="/" class="hover:text-white transition-colors">首页</a>
                        <span class="mx-2">></span>
                        <a href="/intent/{intent.lower()}" class="hover:text-white transition-colors">{intent_name}</a>
                        <span class="mx-2">></span>
                        <span class="text-white">{keyword}</span>
                    </nav>
                </div>
            </div>
        </section>
        
        <!-- 主要内容 -->
        <section class="py-16 bg-white">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-12">
                    <!-- 主要内容 -->
                    <div class="lg:col-span-2">
                        <article class="prose prose-lg max-w-none">
                            <h2 class="text-3xl font-bold text-gray-800 mb-6">关于 "{keyword}"</h2>
                            <p class="text-gray-600 text-lg leading-relaxed mb-8">
                                这里是关于 "{keyword}" 的详细内容。根据搜索意图分析，这个关键词属于{intent_name}类别。
                            </p>
                            
                            <div class="space-y-8">
                                <section class="bg-gray-50 p-6 rounded-xl">
                                    <h3 class="text-2xl font-semibold text-gray-800 mb-4">概述</h3>
                                    <p class="text-gray-600 leading-relaxed">
                                        针对 "{keyword}" 的全面介绍和分析。
                                    </p>
                                </section>
                                
                                <section class="bg-gray-50 p-6 rounded-xl">
                                    <h3 class="text-2xl font-semibold text-gray-800 mb-4">详细信息</h3>
                                    <p class="text-gray-600 leading-relaxed">
                                        更多关于 "{keyword}" 的详细信息和使用指南。
                                    </p>
                                </section>
                                
                                <section class="bg-gray-50 p-6 rounded-xl">
                                    <h3 class="text-2xl font-semibold text-gray-800 mb-4">相关资源</h3>
                                    <ul class="space-y-2 text-gray-600">
                                        <li class="flex items-center">
                                            <i class="fas fa-check-circle text-{color}-500 mr-3"></i>
                                            相关工具和资源链接
                                        </li>
                                        <li class="flex items-center">
                                            <i class="fas fa-check-circle text-{color}-500 mr-3"></i>
                                            进一步学习材料
                                        </li>
                                        <li class="flex items-center">
                                            <i class="fas fa-check-circle text-{color}-500 mr-3"></i>
                                            社区讨论和支持
                                        </li>
                                    </ul>
                                </section>
                            </div>
                        </article>
                    </div>
                    
                    <!-- 侧边栏 -->
                    <div class="lg:col-span-1">
                        <div class="bg-gray-50 p-6 rounded-xl sticky top-24">
                            <h3 class="text-xl font-semibold text-gray-800 mb-4">相关内容</h3>
                            <ul class="space-y-3">
                                <li>
                                    <a href="/intent/{intent.lower()}" class="flex items-center text-{color}-600 hover:text-{color}-700 transition-colors">
                                        <i class="fas fa-arrow-right mr-2"></i>
                                        更多{intent_name}内容
                                    </a>
                                </li>
                                <li>
                                    <a href="/" class="flex items-center text-{color}-600 hover:text-{color}-700 transition-colors">
                                        <i class="fas fa-home mr-2"></i>
                                        返回首页
                                    </a>
                                </li>
                            </ul>
                            
                            <div class="mt-6 pt-6 border-t border-gray-200">
                                <h4 class="text-lg font-semibold text-gray-800 mb-3">标签</h4>
                                <div class="flex flex-wrap gap-2">
                                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-{color}-100 text-{color}-800">
                                        {intent_name}
                                    </span>
                                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 text-gray-800">
                                        {keyword}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>
        """
        
        return self.generate_base_template().format(
            title=f"{keyword} - {intent_name} - 基于搜索意图的内容平台",
            description=f"关于{keyword}的详细信息和指南，属于{intent_name}搜索意图类别。",
            keywords=f"{keyword},{intent_name},搜索意图",
            content=content
        )
    
    def generate_website(self, structure_file: str, content_plan_file: str = None):
        """生成完整的TailwindCSS网站"""
        # 读取网站结构
        with open(structure_file, 'r', encoding='utf-8') as f:
            structure = json.load(f)
        
        print("开始生成TailwindCSS网站文件...")
        
        # 生成首页
        homepage_html = self.generate_homepage(structure)
        with open(os.path.join(self.output_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(homepage_html)
        print("✅ TailwindCSS首页生成完成")
        
        # 生成意图页面
        intent_pages = structure.get('intent_pages', {})
        for intent, pages in intent_pages.items():
            intent_html = self.generate_intent_page(intent, pages)
            intent_file = os.path.join(self.output_dir, 'intent', f'{intent.lower()}.html')
            with open(intent_file, 'w', encoding='utf-8') as f:
                f.write(intent_html)
            
            # 生成关键词页面
            for page in pages:
                if page.get('type') == 'keyword':
                    keyword = page.get('keyword', '')
                    keyword_html = self.generate_keyword_page(keyword, intent)
                    keyword_slug = keyword.replace(' ', '-').lower()
                    keyword_file = os.path.join(self.output_dir, 'keyword', f'{keyword_slug}.html')
                    with open(keyword_file, 'w', encoding='utf-8') as f:
                        f.write(keyword_html)
        
        print(f"✅ TailwindCSS意图页面和关键词页面生成完成")
        
        # 生成网站地图
        self.generate_sitemap(structure)
        print("✅ 网站地图生成完成")
        
        print(f"\n🎉 TailwindCSS网站生成完成！文件保存在: {self.output_dir}")
        print(f"📁 总共生成了 {self.count_generated_files()} 个文件")
    
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
    
    parser = argparse.ArgumentParser(description='TailwindCSS网站生成器')
    parser.add_argument('--structure', '-s', required=True, help='网站结构JSON文件路径')
    parser.add_argument('--content', '-c', help='内容计划JSON文件路径')
    parser.add_argument('--output', '-o', default='generated_website_tailwind', help='输出目录')
    
    args = parser.parse_args()
    
    generator = TailwindHTMLGenerator(args.output)
    generator.generate_website(args.structure, args.content)

if __name__ == "__main__":
    main()
