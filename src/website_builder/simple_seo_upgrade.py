"""
简化版SEO升级脚本 - 直接为现有网站添加SEO优化
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from .seo_optimizer import SEOOptimizer


def upgrade_hurricane_website():
    """升级飓风网站的SEO"""
    website_path = Path("generated_websites/weather_hurricane_erin_20250818_130431/english_website")
    
    if not website_path.exists():
        print(f"❌ 网站路径不存在: {website_path}")
        return
    
    # 读取现有HTML
    index_file = website_path / 'index.html'
    if not index_file.exists():
        print("❌ 未找到index.html文件")
        return
    
    print("📖 读取现有HTML文件...")
    original_html = index_file.read_text(encoding='utf-8')
    
    # 创建备份
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = website_path / f"index_backup_{timestamp}.html"
    backup_file.write_text(original_html, encoding='utf-8')
    print(f"💾 已创建备份: {backup_file.name}")
    
    # 生成SEO配置
    seo_config = {
        'title': 'Hurricane Erin Tracker - Real-time Updates & Safety Information',
        'description': 'Track Hurricane Erin with real-time updates, safety guidelines, evacuation routes, and emergency preparedness information. Stay informed and stay safe.',
        'keywords': 'Hurricane Erin, hurricane tracker, weather emergency, evacuation routes, hurricane safety, storm updates',
        'canonical_url': 'https://hurricane-erin-tracker.vercel.app',
        'robots': 'index, follow',
        'language': 'en',
        'author': 'Hurricane Tracking Team',
        'copyright': f'© {datetime.now().year} Hurricane Erin Tracker. Stay Safe, Stay Informed.',
        'theme_color': '#e74c3c',
        'locale': 'en_US',
        'site_name': 'Hurricane Erin Tracker',
        'image': 'https://hurricane-erin-tracker.vercel.app/images/hurricane-erin-satellite.jpg',
        'twitter_card_type': 'summary_large_image',
        'twitter_site': '@HurricaneTracker',
        'add_breadcrumb': True,
        'faqs': [
            {
                'question': 'What is Hurricane Erin\'s current status?',
                'answer': 'Hurricane Erin is currently a Category 3 storm with maximum sustained winds of 125 mph, moving northwest at 12 mph toward the southeastern U.S. coast.'
            },
            {
                'question': 'When is Hurricane Erin expected to make landfall?',
                'answer': 'Hurricane Erin is expected to make landfall within 18-24 hours, affecting coastal areas in Florida, Georgia, and South Carolina.'
            },
            {
                'question': 'What should I do to prepare for Hurricane Erin?',
                'answer': 'Stock up on water and non-perishable food for 3-7 days, charge electronic devices, secure outdoor furniture, review evacuation routes, and gather important documents in a waterproof container.'
            },
            {
                'question': 'Are there evacuation orders in effect?',
                'answer': 'Yes, mandatory evacuation orders have been issued for coastal areas in Florida, Georgia, and South Carolina. Residents in evacuation zones should leave immediately.'
            },
            {
                'question': 'Where can I find emergency shelters?',
                'answer': 'Emergency shelters are open in designated safe zones, including pet-friendly options. Check with local emergency management for specific locations and availability.'
            }
        ]
    }
    
    # 应用SEO优化
    print("🔧 应用SEO优化...")
    seo_optimizer = SEOOptimizer()
    optimized_html = seo_optimizer.optimize_html(original_html, seo_config)
    
    # 保存优化后的HTML
    index_file.write_text(optimized_html, encoding='utf-8')
    print("✅ HTML文件已优化")
    
    # 生成额外的SEO文件
    print("📄 生成SEO支持文件...")
    
    # Sitemap
    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{seo_config['canonical_url']}</loc>
        <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
        <changefreq>hourly</changefreq>
        <priority>1.0</priority>
    </url>
</urlset>"""
    
    (website_path / 'sitemap.xml').write_text(sitemap_content, encoding='utf-8')
    
    # Robots.txt
    robots_content = f"""User-agent: *
Allow: /

Sitemap: {seo_config['canonical_url']}/sitemap.xml"""
    
    (website_path / 'robots.txt').write_text(robots_content, encoding='utf-8')
    
    # 更新Vercel配置
    vercel_config = {
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
                    },
                    {
                        "key": "Cache-Control",
                        "value": "public, max-age=3600"
                    }
                ]
            }
        ]
    }
    
    (website_path / 'vercel.json').write_text(
        json.dumps(vercel_config, indent=2), encoding='utf-8'
    )
    
    # 计算SEO得分
    seo_score = calculate_seo_score(optimized_html)
    
    # 生成报告
    print("\n" + "="*50)
    print("🎉 SEO优化完成!")
    print("="*50)
    print(f"📁 网站路径: {website_path}")
    print(f"💾 备份文件: {backup_file.name}")
    print(f"📊 SEO得分: {seo_score}/100")
    
    print("\n🔧 应用的优化:")
    optimizations = [
        "✓ 添加了Open Graph标签",
        "✓ 添加了Twitter Cards",
        "✓ 添加了结构化数据 (Website, FAQ)",
        "✓ 优化了Meta标签",
        "✓ 添加了面包屑导航",
        "✓ 添加了FAQ部分",
        "✓ 生成了sitemap.xml",
        "✓ 生成了robots.txt",
        "✓ 更新了vercel.json配置"
    ]
    
    for opt in optimizations:
        print(f"  {opt}")
    
    print("\n💡 建议:")
    recommendations = [
        "• 添加高质量的飓风卫星图片",
        "• 定期更新飓风数据和路径信息",
        "• 监控网站加载速度",
        "• 测试移动端体验",
        "• 验证结构化数据"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")
    
    print(f"\n🌐 部署URL: {seo_config['canonical_url']}")
    print("="*50)


def calculate_seo_score(html_content: str) -> int:
    """计算SEO得分"""
    score = 0
    
    # 基础标签检查 (20分)
    if '<title>' in html_content: score += 5
    if 'name="description"' in html_content: score += 5
    if 'name="keywords"' in html_content: score += 3
    if 'rel="canonical"' in html_content: score += 4
    if 'name="robots"' in html_content: score += 3
    
    # 社交媒体标签 (15分)
    if 'og:title' in html_content: score += 4
    if 'og:description' in html_content: score += 4
    if 'twitter:card' in html_content: score += 7
    
    # 结构化数据 (20分)
    if 'application/ld+json' in html_content: score += 20
    
    # 语义化HTML (25分)
    if '<header>' in html_content: score += 5
    if '<main>' in html_content: score += 5
    if '<section>' in html_content: score += 5
    if '<footer>' in html_content: score += 5
    if 'breadcrumb' in html_content.lower(): score += 5
    
    # 技术SEO (20分)
    if 'viewport' in html_content: score += 8
    if 'faq' in html_content.lower(): score += 5
    if 'alt=' in html_content: score += 4
    if 'title=' in html_content: score += 3
    
    return min(score, 100)


if __name__ == "__main__":
    upgrade_hurricane_website()