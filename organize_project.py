#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
项目文件整理脚本
将所有网站建设相关的文件迁移到src/website_builder目录
"""

import os
import shutil
from pathlib import Path

def organize_project():
    """整理项目文件结构"""
    
    # 定义需要迁移的文件映射
    files_to_move = {
        # 源文件路径: 目标路径
        'ai_website_builder.py': 'src/website_builder/ai_website_builder.py',
        'website_planner.py': 'src/website_builder/website_planner.py',
        'test_intent_builder.py': 'src/website_builder/test_intent_builder_old.py',
        'test_website_builder.py': 'src/website_builder/test_website_builder_old.py',
    }
    
    # 需要保留在根目录的入口文件
    entry_files = {
        'website_builder_cli.py': '网站建设工具命令行入口'
    }
    
    print("开始整理项目文件结构...")
    
    # 确保目标目录存在
    os.makedirs('src/website_builder', exist_ok=True)
    
    # 迁移文件
    moved_count = 0
    for source, target in files_to_move.items():
        if os.path.exists(source):
            try:
                # 如果目标文件已存在，先备份
                if os.path.exists(target):
                    backup_name = f"{target}.backup"
                    shutil.move(target, backup_name)
                    print(f"备份现有文件: {target} -> {backup_name}")
                
                # 移动文件
                shutil.move(source, target)
                print(f"✓ 迁移文件: {source} -> {target}")
                moved_count += 1
            except Exception as e:
                print(f"✗ 迁移失败: {source} -> {target}, 错误: {e}")
        else:
            print(f"- 文件不存在: {source}")
    
    # 检查入口文件
    print(f"\n检查入口文件:")
    for entry_file, description in entry_files.items():
        if os.path.exists(entry_file):
            print(f"✓ {entry_file} - {description}")
        else:
            print(f"✗ {entry_file} - 文件不存在")
    
    # 生成项目结构报告
    print(f"\n项目整理完成!")
    print(f"成功迁移 {moved_count} 个文件")
    
    # 显示src/website_builder目录结构
    print(f"\nsrc/website_builder 目录结构:")
    website_builder_path = Path('src/website_builder')
    if website_builder_path.exists():
        for file_path in sorted(website_builder_path.iterdir()):
            if file_path.is_file():
                size = file_path.stat().st_size
                print(f"  {file_path.name} ({size} bytes)")
    
    return moved_count

if __name__ == "__main__":
    organize_project()