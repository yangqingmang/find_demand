#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re

def debug_html_structure():
    url = "https://www.lummstudio.com/docs/seo/miniclass"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print("正在获取页面...")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"状态码: {response.status_code}")
        print(f"内容长度: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有链接
        all_links = soup.find_all('a', href=True)
        print(f"\n找到 {len(all_links)} 个链接")
        
        # 过滤出指向/docs/的链接
        docs_links = []
        for link in all_links:
            href = link.get('href', '')
            if href.startswith('/docs/') and 'miniclass' not in href:
                docs_links.append({
                    'href': href,
                    'text': link.get_text().strip()[:100],
                    'class': link.get('class', [])
                })
        
        print(f"\n找到 {len(docs_links)} 个/docs/链接:")
        for i, link in enumerate(docs_links[:10], 1):  # 只显示前10个
            print(f"  {i}. {link['href']}")
            print(f"     文本: {link['text']}")
            print(f"     类名: {link['class']}")
            print()
        
        # 查找包含特定类名的元素
        print("\n查找包含'card'的元素:")
        card_elements = soup.find_all(class_=re.compile(r'.*card.*', re.I))
        print(f"找到 {len(card_elements)} 个包含'card'的元素")
        
        for i, elem in enumerate(card_elements[:5], 1):
            print(f"  {i}. 标签: {elem.name}, 类名: {elem.get('class', [])}")
            if elem.name == 'a':
                print(f"     链接: {elem.get('href', 'N/A')}")
            print()
        
        # 查找文章标题
        print("\n查找可能的文章标题:")
        title_elements = soup.find_all(['h1', 'h2', 'h3'], class_=re.compile(r'.*title.*', re.I))
        for i, elem in enumerate(title_elements[:10], 1):
            print(f"  {i}. {elem.name}: {elem.get_text().strip()[:100]}")
            print(f"     类名: {elem.get('class', [])}")
            print()
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_html_structure()