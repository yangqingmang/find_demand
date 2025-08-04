#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目结构迁移脚本
将旧的项目文件迁移到新的模块化结构中
"""

import os
import shutil
import sys
from pathlib import Path

def create_directory_structure():
    """创建新的目录结构"""
    directories = [
        'src',
        'src/core',
        'src/collectors', 
        'src/analyzers',
        'src/utils',
        'data',
        'docs_backup'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def backup_old_files():
    """备份旧文件"""
    old_files = [
        'market_analyzer.py',
        'trends_collector.py', 
        'keyword_scorer.py',
        'intent_analyzer.py',
        'pray_score.py',
        'run_analysis.py',
        'config.py'
    ]
    
    backup_dir = 'backup_old_files'
    os.makedirs(backup_dir, exist_ok=True)
    
    for file in old_files:
        if os.path.exists(file):
            shutil.copy2(file, os.path.join(backup_dir, file))
            print(f"✓ 备份文件: {file}")

def move_docs():
    """移动文档文件"""
    if os.path.exists('docs'):
        # 备份原有docs目录
        if os.path.exists('docs_backup'):
            shutil.rmtree('docs_backup')
        shutil.copytree('docs', 'docs_backup')
        print("✓ 备份原有docs目录到docs_backup")

def update_imports_in_file(file_path, old_imports, new_imports):
    """更新文件中的import语句"""
    if not os.path.exists(file_path):
        return
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换import语句
        for old_import, new_import in zip(old_imports, new_imports):
            content = content.replace(old_import, new_import)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✓ 更新导入语句: {file_path}")
    except Exception as e:
        print(f"✗ 更新导入语句失败 {file_path}: {e}")

def create_compatibility_layer():
    """创建兼容性层，确保旧的导入方式仍然可用"""
    
    # 在根目录创建兼容性文件
    compatibility_files = {
        'market_analyzer.py': '''# 兼容性导入 - 请使用 main.py 或 from src.core.market_analyzer import MarketAnalyzer
import warnings
warnings.warn("直接导入 market_analyzer.py 已弃用，请使用 'python main.py' 或 'from src.core.market_analyzer import MarketAnalyzer'", DeprecationWarning)

from src.core.market_analyzer import MarketAnalyzer, main

if __name__ == "__main__":
    main()
''',
        
        'trends_collector.py': '''# 兼容性导入 - 请使用 from src.collectors.trends_collector import TrendsCollector
import warnings
warnings.warn("直接导入 trends_collector.py 已弃用，请使用 'from src.collectors.trends_collector import TrendsCollector'", DeprecationWarning)

from src.collectors.trends_collector import TrendsCollector, main

if __name__ == "__main__":
    main()
''',
        
        'keyword_scorer.py': '''# 兼容性导入 - 请使用 from src.analyzers.keyword_scorer import KeywordScorer
import warnings
warnings.warn("直接导入 keyword_scorer.py 已弃用，请使用 'from src.analyzers.keyword_scorer import KeywordScorer'", DeprecationWarning)

from src.analyzers.keyword_scorer import KeywordScorer, main

if __name__ == "__main__":
    main()
''',
        
        'intent_analyzer.py': '''# 兼容性导入 - 请使用 from src.analyzers.intent_analyzer import IntentAnalyzer
import warnings
warnings.warn("直接导入 intent_analyzer.py 已弃用，请使用 'from src.analyzers.intent_analyzer import IntentAnalyzer'", DeprecationWarning)

from src.analyzers.intent_analyzer import IntentAnalyzer, main

if __name__ == "__main__":
    main()
''',
        
        'config.py': '''# 兼容性导入 - 请使用 from src.utils.config import *
import warnings
warnings.warn("直接导入 config.py 已弃用，请使用 'from src.utils.config import *'", DeprecationWarning)

from src.utils.config import *
'''
    }
    
    for filename, content in compatibility_files.items():
        # 只有当新的src结构存在时才创建兼容性文件
        src_file = filename.replace('.py', '').replace('_', '/')
        if filename == 'market_analyzer.py':
            src_path = 'src/core/market_analyzer.py'
        elif filename == 'trends_collector.py':
            src_path = 'src/collectors/trends_collector.py'
        elif filename in ['keyword_scorer.py', 'intent_analyzer.py']:
            src_path = f'src/analyzers/{filename}'
        elif filename == 'config.py':
            src_path = 'src/utils/config.py'
        else:
            continue
            
        if os.path.exists(src_path):
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ 创建兼容性文件: {filename}")

def main():
    """主函数"""
    print("开始项目结构迁移...")
    print("=" * 50)
    
    # 1. 创建目录结构
    print("\n1. 创建新的目录结构")
    create_directory_structure()
    
    # 2. 备份旧文件
    print("\n2. 备份旧文件")
    backup_old_files()
    
    # 3. 移动文档
    print("\n3. 处理文档文件")
    move_docs()
    
    # 4. 创建兼容性层
    print("\n4. 创建兼容性层")
    create_compatibility_layer()
    
    print("\n" + "=" * 50)
    print("✅ 项目结构迁移完成!")
    print("\n📁 新的项目结构:")
    print("""
find_demand/
├── src/                          # 新的源代码目录
│   ├── core/                    # 核心模块
│   ├── collectors/              # 数据采集模块  
│   ├── analyzers/               # 分析器模块
│   └── utils/                   # 工具模块
├── main.py                      # 新的主入口文件
├── backup_old_files/            # 旧文件备份
├── docs_backup/                 # 原文档备份
└── [兼容性文件]                 # 保持向后兼容
    """)
    
    print("\n🚀 使用方法:")
    print("  新方式: python main.py \"ai tools\"")
    print("  旧方式: python run_analysis.py \"ai tools\" (仍然可用)")
    
    print("\n📚 详细文档:")
    print("  - 查看 README.md 了解完整使用说明")
    print("  - 查看 src/*/README.md 了解各模块详情")
    
    print("\n⚠️  注意事项:")
    print("  - 旧的导入方式仍然可用，但会显示弃用警告")
    print("  - 建议逐步迁移到新的导入方式")
    print("  - 原始文件已备份到 backup_old_files/ 目录")

if __name__ == "__main__":
    main()