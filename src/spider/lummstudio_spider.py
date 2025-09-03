import requests
from bs4 import BeautifulSoup
import time
import json
import os
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import html
import hashlib
from pathlib import Path

class LummStudioSpider:
    def __init__(self):
        self.base_url = "https://www.lummstudio.com"
        self.start_url = "https://www.lummstudio.com/docs/seo/miniclass"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.scraped_urls = set()
        self.data = []
        
    def get_page_content(self, url):
        """获取页面内容"""
        try:
            # 更新请求头，移除可能导致问题的压缩设置
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Connection': 'keep-alive',
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"获取页面失败 {url}: {e}")
            return None
    
    def parse_article_links(self, html_content):
        """解析文章链接"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # 查找所有文章卡片链接 - 尝试多种选择器
        article_links = []
        
        # 方法1: 原始选择器
        article_links.extend(soup.find_all('a', class_='card padding--lg cardContainer_ob4h'))
        
        # 方法2: 查找包含cardContainer的类
        article_links.extend(soup.find_all('a', class_=lambda x: x and 'cardContainer' in x))
        
        # 方法3: 查找所有指向/docs/的链接
        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link.get('href', '')
            if href.startswith('/docs/') and 'miniclass' not in href:
                article_links.append(link)
        
        # 去重
        seen_urls = set()
        unique_links = []
        for link in article_links:
            href = link.get('href', '')
            if href and href not in seen_urls:
                seen_urls.add(href)
                unique_links.append(link)
        
        print(f"找到 {len(unique_links)} 个候选链接")
        
        for link in unique_links:
            href = link.get('href')
            if href and href.startswith('/docs/'):
                full_url = urljoin(self.base_url, href)
                
                # 获取标题 - 尝试多种方式
                title = ''
                title_elem = link.find('h2', class_=lambda x: x and 'cardTitle' in x) if link.find('h2') else None
                if title_elem:
                    title = title_elem.get('title', '') or title_elem.get_text()
                    title = title.replace('📄️', '').replace('<!-- -->', '').strip()
                else:
                    # 尝试从链接文本获取标题
                    title = link.get_text().strip()
                
                # 获取日期
                date = ''
                date_elem = link.find('p', class_=lambda x: x and 'cardDescription' in x) if link.find('p') else None
                if date_elem:
                    date_text = date_elem.get('title', '') or date_elem.get_text()
                    date = date_text.replace('日期：', '').strip()
                
                if title:  # 只添加有标题的链接
                    links.append({
                        'url': full_url,
                        'title': title,
                        'date': date
                    })
                    print(f"  - {title} ({date})")
        
        return links
    
    def parse_article_content(self, html_content, url):
        """解析文章内容"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 获取标题
        title_elem = soup.find('h1')
        title = title_elem.get_text().strip() if title_elem else ''
        
        # 获取主要内容区域
        content_elem = soup.find('article') or soup.find('main') or soup.find('div', class_='markdown')
        
        if not content_elem:
            # 尝试其他可能的内容容器
            content_elem = soup.find('div', {'class': re.compile(r'.*content.*|.*article.*|.*post.*')})
        
        content = ''
        if content_elem:
            # 移除导航和其他不相关元素
            for elem in content_elem.find_all(['nav', 'aside', 'footer', 'header']):
                elem.decompose()
            
            # 获取文本内容
            content = content_elem.get_text(separator='\n', strip=True)
        
        # 获取页面描述
        description = ''
        desc_elem = soup.find('meta', {'name': 'description'})
        if desc_elem:
            description = desc_elem.get('content', '')
        
        return {
            'url': url,
            'title': title,
            'description': description,
            'content': content,
            'scraped_at': datetime.now().isoformat()
        }
    
    def save_data(self, filename=None):
        """保存数据到文件"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lummstudio_data_{timestamp}.json"
        
        filepath = os.path.join('data', filename)
        os.makedirs('data', exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        
        print(f"数据已保存到: {filepath}")
        return filepath
    
    def save_markdown(self, filename=None):
        """保存为Markdown格式"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lummstudio_articles_{timestamp}.md"
        
        filepath = os.path.join('src/spider/markdown', filename)
        os.makedirs('src/spider/markdown', exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# 哥飞小课堂 - SEO文章合集\n\n")
            f.write(f"爬取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            for item in self.data:
                f.write(f"## {item['title']}\n\n")
                f.write(f"**URL**: {item['url']}\n\n")
                if item.get('description'):
                    f.write(f"**描述**: {item['description']}\n\n")
                f.write(f"**内容**:\n\n{item['content']}\n\n")
                f.write("---\n\n")
        
        print(f"Markdown文件已保存到: {filepath}")
        return filepath
    
    def save_individual_html(self, article_data, html_content):
        """保存单个文章为HTML文件"""
        # 创建安全的文件名
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', article_data.get('original_title', article_data.get('title', 'untitled')))
        safe_title = safe_title[:100]  # 限制文件名长度
        
        # 添加日期前缀
        date_prefix = article_data.get('date', '').replace('-', '')
        if date_prefix:
            filename = f"{date_prefix}_{safe_title}.html"
        else:
            filename = f"{safe_title}.html"
        
        # 创建保存目录
        save_dir = os.path.join('src/spider/html_pages')
        os.makedirs(save_dir, exist_ok=True)
        
        filepath = os.path.join(save_dir, filename)
        
        # 如果文件已存在，先删除旧文件
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"删除旧文件: {filename}")
        
        # 创建完整的HTML页面
        full_html = self.create_complete_html(article_data, html_content)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_html)
        
        print(f"HTML文件已保存: {filename}")
        return filepath
    
    def create_complete_html(self, article_data, original_html):
        """创建完整的HTML页面"""
        soup = BeautifulSoup(original_html, 'html.parser')
        
        # 提取主要内容
        main_content = soup.find('main') or soup.find('article') or soup.find('div', {'class': re.compile(r'.*content.*')})
        
        if not main_content:
            # 如果找不到主要内容区域，使用整个body
            main_content = soup.find('body') or soup
        
        # 处理图片下载
        print(f"  正在处理图片...")
        main_content, failed_images = self.process_images_in_html(main_content, article_data.get('original_title', article_data.get('title', 'untitled')))
        
        # 将失败的图片信息添加到文章数据中
        if failed_images:
            article_data['failed_images'] = failed_images
        
        # 创建新的HTML文档
        html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(article_data.get('title', ''))}</title>
    <meta name="description" content="{html.escape(article_data.get('description', ''))}">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
        }}
        .article-header {{
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .article-title {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #2c3e50;
        }}
        .article-meta {{
            color: #666;
            font-size: 0.9em;
        }}
        .article-content {{
            font-size: 1.1em;
        }}
        .article-content h1, .article-content h2, .article-content h3 {{
            color: #2c3e50;
            margin-top: 30px;
        }}
        .article-content p {{
            margin-bottom: 15px;
        }}
        .article-content code {{
            background-color: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }}
        .article-content pre {{
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .article-content blockquote {{
            border-left: 4px solid #ddd;
            margin: 20px 0;
            padding-left: 20px;
            color: #666;
        }}
        .article-content img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .article-content figure {{
            margin: 20px 0;
            text-align: center;
        }}
        .article-content figure img {{
            max-width: 100%;
            height: auto;
        }}
        .source-info {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="article-header">
        <h1 class="article-title">{html.escape(article_data.get('title', ''))}</h1>
        <div class="article-meta">
            <p><strong>原始链接:</strong> <a href="{article_data.get('url', '')}" target="_blank">{article_data.get('url', '')}</a></p>
            {f'<p><strong>发布日期:</strong> {article_data.get("date", "")}</p>' if article_data.get('date') else ''}
            {f'<p><strong>描述:</strong> {html.escape(article_data.get("description", ""))}</p>' if article_data.get('description') else ''}
            <p><strong>爬取时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
    
    <div class="article-content">
        {str(main_content)}
    </div>
    
    <div class="source-info">
        <p>本文章来源于: <a href="https://www.lummstudio.com" target="_blank">路漫漫 - LummStudio</a></p>
        <p>爬取工具: LummStudio Spider</p>
    </div>
</body>
</html>"""
        
        return html_template
    
    def download_image(self, img_url, save_dir, max_retries=3):
        """下载图片到本地，支持重试机制"""
        # 生成图片文件名
        parsed_url = urlparse(img_url)
        img_name = os.path.basename(parsed_url.path)
        if not img_name or '.' not in img_name:
            # 如果没有文件名或扩展名，使用URL的hash值
            img_hash = hashlib.md5(img_url.encode()).hexdigest()[:10]
            img_name = f"image_{img_hash}.jpg"
        
        # 确保文件名安全
        img_name = re.sub(r'[<>:"/\\|?*]', '_', img_name)
        img_path = os.path.join(save_dir, img_name)
        
        # 如果图片已存在，直接返回
        if os.path.exists(img_path):
            return img_name, None
        
        # 重试下载
        for attempt in range(max_retries):
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'https://www.lummstudio.com/'
                }
                
                response = requests.get(img_url, headers=headers, timeout=15, stream=True)
                response.raise_for_status()
                
                with open(img_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"  图片已下载: {img_name}")
                return img_name, None
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  图片下载失败 (尝试 {attempt + 1}/{max_retries}): {img_name}")
                    time.sleep(2)  # 等待2秒后重试
                else:
                    print(f"  图片下载最终失败 {img_url}: {e}")
                    # 返回失败信息，包含URL和建议的文件名
                    return None, {'url': img_url, 'filename': img_name, 'path': img_path}
        
        return None, {'url': img_url, 'filename': img_name, 'path': img_path}
    
    def process_images_in_html(self, soup, article_title):
        """处理HTML中的图片，下载到本地并更新链接"""
        # 创建图片保存目录
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', article_title)[:50]
        img_dir = os.path.join('src/spider/html_pages/images', safe_title)
        os.makedirs(img_dir, exist_ok=True)
        
        # 查找所有图片标签
        images = soup.find_all('img')
        downloaded_count = 0
        failed_images = []
        
        for img in images:
            src = img.get('src')
            if not src:
                continue
            
            # 转换为绝对URL
            if src.startswith('//'):
                img_url = 'https:' + src
            elif src.startswith('/'):
                img_url = urljoin(self.base_url, src)
            elif src.startswith('http'):
                img_url = src
            else:
                continue
            
            # 下载图片
            local_img_name, failed_info = self.download_image(img_url, img_dir)
            if local_img_name:
                # 更新图片链接为相对路径
                relative_path = f"images/{safe_title}/{local_img_name}"
                img['src'] = relative_path
                downloaded_count += 1
            elif failed_info:
                # 记录失败的图片信息
                failed_images.append(failed_info)
        
        if downloaded_count > 0:
            print(f"  共下载 {downloaded_count} 张图片")
        
        # 返回soup和失败的图片列表
        return soup, failed_images
    
    def cleanup_old_html_files(self):
        """清理旧的HTML文件和图片"""
        save_dir = os.path.join('src/spider/html_pages')
        if os.path.exists(save_dir):
            # 清理HTML文件
            html_files = [f for f in os.listdir(save_dir) if f.endswith('.html') and f != 'index.html']
            if html_files:
                print(f"清理 {len(html_files)} 个旧HTML文件...")
                for file in html_files:
                    file_path = os.path.join(save_dir, file)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"删除文件失败 {file}: {e}")
            
            # 清理图片目录
            img_dir = os.path.join(save_dir, 'images')
            if os.path.exists(img_dir):
                print("清理旧图片文件...")
                import shutil
                try:
                    shutil.rmtree(img_dir)
                    print("图片目录清理完成")
                except Exception as e:
                    print(f"清理图片目录失败: {e}")
            
            if html_files:
                print("旧文件清理完成")
    
    def crawl(self):
        """开始爬取"""
        print("开始爬取 LummStudio SEO 小课堂...")
        
        # 清理旧的HTML文件
        self.cleanup_old_html_files()
        
        # 获取主页面内容
        print(f"正在获取主页面: {self.start_url}")
        main_content = self.get_page_content(self.start_url)
        if not main_content:
            print("无法获取主页面内容")
            return
        
        # 解析文章链接
        article_links = self.parse_article_links(main_content)
        print(f"找到 {len(article_links)} 篇文章")
        
        # 爬取每篇文章
        html_files = []
        all_failed_images = []  # 收集所有失败的图片
        for i, link_info in enumerate(article_links, 1):
            url = link_info['url']
            if url in self.scraped_urls:
                continue
                
            print(f"正在爬取 ({i}/{len(article_links)}): {link_info['title']}")
            
            content = self.get_page_content(url)
            if content:
                article_data = self.parse_article_content(content, url)
                article_data.update({
                    'original_title': link_info['title'],
                    'date': link_info['date']
                })
                self.data.append(article_data)
                self.scraped_urls.add(url)
                
                # 保存单个HTML文件
                html_file = self.save_individual_html(article_data, content)
                html_files.append(html_file)
                
                # 添加延迟避免过于频繁的请求
                time.sleep(1)
            else:
                print(f"跳过无法获取的页面: {url}")
        
        print(f"爬取完成！共获取 {len(self.data)} 篇文章")
        
        # 保存数据
        json_file = self.save_data()
        md_file = self.save_markdown()
        
        return {
            'total_articles': len(self.data),
            'json_file': json_file,
            'markdown_file': md_file,
            'html_files': html_files,
            'data': self.data
        }

def main():
    spider = LummStudioSpider()
    result = spider.crawl()
    
    print("\n=== 爬取结果 ===")
    print(f"总文章数: {result['total_articles']}")
    print(f"JSON文件: {result['json_file']}")
    print(f"Markdown文件: {result['markdown_file']}")

if __name__ == "__main__":
    main()