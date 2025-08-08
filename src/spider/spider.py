#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lummstudio_spider.py
--------------------
1. 请求页面 HTML
2. 解析正文 (article 标签)
3. 下载正文内图片，替换为本地相对路径
4. 将 HTML 转 Markdown，落盘保存
"""

import re
import os
import time
import pathlib
import requests
from bs4 import BeautifulSoup
from markdownify import markdownify as md

# ------------------ 全局配置 ------------------ #
URLS = [
    "https://www.lummstudio.com/docs/20240802",
    "https://www.lummstudio.com/docs/20240801",
]

HEADERS = {
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )
}

ROOT_DIR = pathlib.Path(__file__).resolve().parent
ASSET_DIR = ROOT_DIR / "assets"
MD_DIR = ROOT_DIR / "markdown"

ASSET_DIR.mkdir(exist_ok=True)
MD_DIR.mkdir(exist_ok=True)


# ------------------ 工具函数 ------------------ #
def slugify(text: str) -> str:
    """将中文 / 空格标题转化为文件安全的 slug."""
    text = re.sub(r"[^\w\s-]", "", text, flags=re.U).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def download_img(img_url: str) -> str:
    """下载图片到本地 assets/ 目录，返回保存文件名"""
    # 处理相对地址
    if img_url.startswith("//"):
        img_url = "https:" + img_url
    elif img_url.startswith("/"):
        img_url = "https://www.lummstudio.com" + img_url

    # 根据 URL 后缀决定文件名
    filename = slugify(pathlib.Path(img_url).name.split("?")[0])
    ext = pathlib.Path(filename).suffix or ".jpg"
    local_name = f"{int(time.time()*1000)}{ext}"
    local_path = ASSET_DIR / local_name

    # 已存在则跳过
    if local_path.exists():
        return local_name

    try:
        resp = requests.get(img_url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        with open(local_path, "wb") as f:
            f.write(resp.content)
        print(f"[✓] Image saved: {local_name}")
        return local_name
    except Exception as e:
        print(f"[!] Fail download {img_url} -> {e}")
        return img_url  # 回退到原地址


def extract_article(soup: BeautifulSoup) -> BeautifulSoup:
    """
    Lumm Studio 文章的正文都包在 <article> 标签里，
    如果结构改变，可按 class 名或 id 重新定位。
    """
    article = soup.find("article")
    if not article:
        raise RuntimeError("正文 <article> 未找到，检查页面结构！")
    return article


def html_to_markdown(html_str: str) -> str:
    """HTML → Markdown；设置各种转换细节"""
    return md(
        html_str,
        heading_style="ATX",
        strip=["span", "font"],
        # 保留表格 / 引用 / 图片
    )


# ------------------ 主流程 ------------------ #
for url in URLS:
    print(f"\n=== Crawling {url} ===")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"[!] 请求失败: {e}")
        continue

    soup = BeautifulSoup(r.text, "lxml")

    # ------- 1. 提取标题、正文 ------- #
    title_tag = soup.find(["h1", "title"])
    title = title_tag.get_text(strip=True) if title_tag else "untitled"
    slug = slugify(title)

    article = extract_article(soup)

    # ------- 2. 下载并替换图片 ------- #
    for img in article.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        local_name = download_img(src)
        # 将 src 替换为相对路径
        img["src"] = f"./assets/{local_name}"

    # ------- 3. HTML → Markdown ------- #
    markdown_body = html_to_markdown(str(article))
    md_path = MD_DIR / f"{slug}.md"

    front_matter = (
        f"---\n"
        f"title: \"{title}\"\n"
        f"origin: {url}\n"
        f"date: {time.strftime('%Y-%m-%d')}\n"
        f"---\n\n"
    )

    with open(md_path, "w", encoding="utf-8") as md_file:
        md_file.write(front_matter + markdown_body)

    print(f"[✓] Markdown saved: {md_path.relative_to(ROOT_DIR)}")

print("\n🌟 All done!")
