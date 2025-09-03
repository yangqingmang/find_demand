#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from spider.lummstudio_spider import LummStudioSpider

def main():
    print("=" * 50)
    print("LummStudio SEO小课堂爬虫")
    print("=" * 50)
    
    spider = LummStudioSpider()
    
    try:
        result = spider.crawl()
        
        print("\n" + "=" * 50)
        print("爬取完成!")
        print("=" * 50)
        print(f"📊 总文章数: {result['total_articles']}")
        print(f"💾 JSON文件: {result['json_file']}")
        print(f"📝 Markdown文件: {result['markdown_file']}")
        print(f"🌐 HTML文件数: {len(result.get('html_files', []))}")
        
        # 显示前几篇文章的标题
        if result['data']:
            print(f"\n📋 文章列表预览 (前5篇):")
            for i, article in enumerate(result['data'][:5], 1):
                print(f"  {i}. {article.get('original_title', article.get('title', 'N/A'))}")
                if article.get('date'):
                    print(f"     日期: {article['date']}")
                print()
        
        # 显示HTML文件保存位置
        if result.get('html_files'):
            print(f"🌐 HTML文件保存在: src/spider/html_pages/")
            print(f"   共 {len(result['html_files'])} 个文件")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断了爬取过程")
    except Exception as e:
        print(f"\n❌ 爬取过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()