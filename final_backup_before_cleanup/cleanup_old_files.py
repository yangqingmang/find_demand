#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目清理脚本
清理重构后不再需要的旧文件，保持项目目录整洁
"""

import os
import shutil
import sys
from pathlib import Path

def get_files_to_cleanup():
    """获取需要清理的文件列表"""
    
    # 已经迁移到src/目录的旧文件
    old_source_files = [
        'market_analyzer.py',      # 已迁移到 src/core/
        'trends_collector.py',     # 已迁移到 src/collectors/
        'keyword_scorer.py',       # 已迁移到 src/analyzers/
        'intent_analyzer.py',      # 已迁移到 src/analyzers/
        'config.py',              # 已迁移到 src/utils/
        'run_analysis.py',        # 已被 main.py 替代
    ]
    
    # 可能不再需要的文件
    optional_cleanup_files = [
        'pray_score.py',          # 如果不再使用
        'pray_ranking.csv',       # 如果不再需要
        '手册.MD',                # 如果已整合到新文档中
        'migrate_project.py',     # 迁移完成后可删除
        'cleanup_old_files.py',   # 清理完成后可删除
        '项目架构说明.md',         # 临时说明文档
    ]
    
    # 可能的临时目录
    temp_directories = [
        '__pycache__',
        '.codebuddy',
        'backup_old_files',       # 如果确认不需要备份
    ]
    
    return old_source_files, optional_cleanup_files, temp_directories

def backup_before_cleanup():
    """在清理前创建最终备份"""
    backup_dir = 'final_backup_before_cleanup'
    
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    
    os.makedirs(backup_dir, exist_ok=True)
    
    old_files, optional_files, _ = get_files_to_cleanup()
    all_files = old_files + optional_files
    
    backed_up = []
    for file in all_files:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, file))
            backed_up.append(file)
    
    if backed_up:
        print(f"✓ 已备份 {len(backed_up)} 个文件到 {backup_dir}/")
        for file in backed_up:
            print(f"  - {file}")
    
    return backup_dir

def cleanup_old_source_files():
    """清理已迁移的旧源文件"""
    old_files, _, _ = get_files_to_cleanup()
    
    cleaned = []
    for file in old_files:
        if os.path.exists(file):
            # 检查对应的新文件是否存在
            new_file_exists = False
            
            if file == 'market_analyzer.py':
                new_file_exists = os.path.exists('src/core/market_analyzer.py')
            elif file == 'trends_collector.py':
                new_file_exists = os.path.exists('src/collectors/trends_collector.py')
            elif file == 'keyword_scorer.py':
                new_file_exists = os.path.exists('src/analyzers/keyword_scorer.py')
            elif file == 'intent_analyzer.py':
                new_file_exists = os.path.exists('src/analyzers/intent_analyzer.py')
            elif file == 'config.py':
                new_file_exists = os.path.exists('src/utils/config.py')
            elif file == 'run_analysis.py':
                new_file_exists = os.path.exists('main.py')
            
            if new_file_exists:
                os.remove(file)
                cleaned.append(file)
                print(f"✓ 已删除旧文件: {file}")
            else:
                print(f"⚠ 跳过 {file} (对应的新文件不存在)")
    
    return cleaned

def cleanup_optional_files():
    """清理可选文件（需要用户确认）"""
    _, optional_files, _ = get_files_to_cleanup()
    
    print("\n以下文件可能不再需要，是否删除？")
    
    to_delete = []
    for file in optional_files:
        if os.path.exists(file):
            while True:
                choice = input(f"删除 {file}? (y/n/s=跳过): ").lower().strip()
                if choice in ['y', 'yes']:
                    to_delete.append(file)
                    break
                elif choice in ['n', 'no']:
                    print(f"保留 {file}")
                    break
                elif choice in ['s', 'skip']:
                    break
                else:
                    print("请输入 y(是), n(否), 或 s(跳过)")
    
    # 删除确认的文件
    deleted = []
    for file in to_delete:
        try:
            os.remove(file)
            deleted.append(file)
            print(f"✓ 已删除: {file}")
        except Exception as e:
            print(f"✗ 删除失败 {file}: {e}")
    
    return deleted

def cleanup_temp_directories():
    """清理临时目录"""
    _, _, temp_dirs = get_files_to_cleanup()
    
    cleaned_dirs = []
    for dir_name in temp_dirs:
        if os.path.exists(dir_name):
            if dir_name == '__pycache__':
                # Python缓存目录，可以安全删除
                shutil.rmtree(dir_name)
                cleaned_dirs.append(dir_name)
                print(f"✓ 已删除缓存目录: {dir_name}")
            elif dir_name == 'backup_old_files':
                # 询问是否删除备份目录
                choice = input(f"删除备份目录 {dir_name}? (y/n): ").lower().strip()
                if choice in ['y', 'yes']:
                    shutil.rmtree(dir_name)
                    cleaned_dirs.append(dir_name)
                    print(f"✓ 已删除备份目录: {dir_name}")
                else:
                    print(f"保留备份目录: {dir_name}")
            else:
                # 其他目录询问用户
                choice = input(f"删除目录 {dir_name}? (y/n): ").lower().strip()
                if choice in ['y', 'yes']:
                    shutil.rmtree(dir_name)
                    cleaned_dirs.append(dir_name)
                    print(f"✓ 已删除目录: {dir_name}")
    
    return cleaned_dirs

def show_cleanup_summary(backup_dir, cleaned_files, deleted_files, cleaned_dirs):
    """显示清理摘要"""
    print("\n" + "="*60)
    print("🧹 项目清理完成!")
    print("="*60)
    
    if backup_dir and os.path.exists(backup_dir):
        print(f"\n📦 备份位置: {backup_dir}/")
    
    if cleaned_files:
        print(f"\n✅ 已清理的旧源文件 ({len(cleaned_files)}个):")
        for file in cleaned_files:
            print(f"   - {file}")
    
    if deleted_files:
        print(f"\n🗑️ 已删除的可选文件 ({len(deleted_files)}个):")
        for file in deleted_files:
            print(f"   - {file}")
    
    if cleaned_dirs:
        print(f"\n📁 已清理的目录 ({len(cleaned_dirs)}个):")
        for dir_name in cleaned_dirs:
            print(f"   - {dir_name}/")
    
    print(f"\n📁 当前项目结构:")
    print("""
find_demand/
├── src/                    # 新的模块化源代码
│   ├── core/              # 核心分析器
│   ├── collectors/        # 数据采集器
│   ├── analyzers/         # 分析器
│   └── utils/             # 工具和配置
├── main.py                # 主入口文件
├── data/                  # 数据输出目录
├── docs/                  # 原始文档
├── docs_backup/           # 文档备份
└── README.md              # 项目说明
    """)
    
    print("\n🚀 使用新架构:")
    print("   python main.py \"ai tools\"")
    
    if backup_dir and os.path.exists(backup_dir):
        print(f"\n💡 提示: 如果需要恢复文件，请查看 {backup_dir}/ 目录")

def main():
    """主函数"""
    print("项目清理工具")
    print("=" * 40)
    print("此工具将帮助清理重构后不再需要的旧文件")
    print()
    
    # 显示将要处理的文件
    old_files, optional_files, temp_dirs = get_files_to_cleanup()
    
    print("📋 将要处理的文件:")
    print("\n🔄 已迁移的旧源文件 (将自动删除):")
    for file in old_files:
        if os.path.exists(file):
            print(f"   - {file}")
    
    print("\n❓ 可选清理的文件 (需要确认):")
    for file in optional_files:
        if os.path.exists(file):
            print(f"   - {file}")
    
    print("\n📁 可能的临时目录:")
    for dir_name in temp_dirs:
        if os.path.exists(dir_name):
            print(f"   - {dir_name}/")
    
    print()
    choice = input("是否继续清理? (y/n): ").lower().strip()
    if choice not in ['y', 'yes']:
        print("已取消清理")
        return
    
    # 创建备份
    print("\n1. 创建最终备份...")
    backup_dir = backup_before_cleanup()
    
    # 清理已迁移的源文件
    print("\n2. 清理已迁移的源文件...")
    cleaned_files = cleanup_old_source_files()
    
    # 清理可选文件
    print("\n3. 处理可选文件...")
    deleted_files = cleanup_optional_files()
    
    # 清理临时目录
    print("\n4. 清理临时目录...")
    cleaned_dirs = cleanup_temp_directories()
    
    # 显示摘要
    show_cleanup_summary(backup_dir, cleaned_files, deleted_files, cleaned_dirs)

if __name__ == "__main__":
    main()