#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import json

def detailed_debug():
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
        
        # 保存原始HTML到文件
        with open('debug_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("原始HTML已保存到 debug_page.html")
        
        # 显示前1000个字符
        print("\n页面内容预览 (前1000字符):")
        print("=" * 50)
        print(response.text[:1000])
        print("=" * 50)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找所有script标签，看是否有动态内容
        scripts = soup.find_all('script')
        print(f"\n找到 {len(scripts)} 个script标签")
        
        for i, script in enumerate(scripts[:3], 1):
            if script.string:
                print(f"\nScript {i} 内容预览:")
                print(script.string[:200] + "..." if len(script.string) > 200 else script.string)
        
        # 查找可能包含数据的元素
        print("\n查找可能的数据容器:")
        data_containers = soup.find_all(['div', 'section', 'main'], id=True)
        for container in data_containers:
            print(f"ID: {container.get('id')}, 标签: {container.name}")
            
        # 查找所有class属性
        all_elements = soup.find_all(class_=True)
        unique_classes = set()
        for elem in all_elements:
            classes = elem.get('class', [])
            for cls in classes:
                unique_classes.add(cls)
        
        print(f"\n找到的所有CSS类名 (前20个):")
        for i, cls in enumerate(sorted(list(unique_classes))[:20], 1):
            print(f"  {i}. {cls}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    detailed_debug()