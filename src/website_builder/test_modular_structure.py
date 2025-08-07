#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试模块化结构的脚本
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_imports():
    """测试所有模块的导入"""
    print("正在测试模块导入...")
    
    try:
        # 测试核心模块导入
        from src.website_builder.builder_core import IntentBasedWebsiteBuilder
        print("✓ IntentBasedWebsiteBuilder 导入成功")
        
        from src.website_builder.structure_generator import WebsiteStructureGenerator
        print("✓ WebsiteStructureGenerator 导入成功")
        
        from src.website_builder.content_planner import ContentPlanGenerator
        print("✓ ContentPlanGenerator 导入成功")
        
        from src.website_builder.page_templates import PageTemplateManager
        print("✓ PageTemplateManager 导入成功")
        
        from src.website_builder.utils import ensure_dir, load_data_file, save_json_file
        print("✓ 工具函数导入成功")
        
        # 测试包级别导入
        from src.website_builder import (
            IntentBasedWebsiteBuilder,
            WebsiteStructureGenerator,
            ContentPlanGenerator,
            PageTemplateManager
        )
        print("✓ 包级别导入成功")
        
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基本功能"""
    print("\n正在测试基本功能...")
    
    try:
        # 测试页面模板管理器
        from src.website_builder.page_templates import PageTemplateManager
        template_manager = PageTemplateManager()
        
        # 获取首页模板
        homepage_template = template_manager.get_template('homepage')
        if homepage_template:
            print("✓ 页面模板管理器工作正常")
        else:
            print("✗ 页面模板管理器获取模板失败")
            return False
        
        # 测试工具函数
        from src.website_builder.utils import generate_url_slug, count_words
        
        slug = generate_url_slug("测试 URL Slug")
        if slug:
            print(f"✓ URL slug生成成功: {slug}")
        
        word_count = count_words("这是一个测试文本 with English words")
        if word_count > 0:
            print(f"✓ 单词计数功能正常: {word_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ 功能测试失败: {e}")
        return False

def test_integration():
    """测试模块集成"""
    print("\n正在测试模块集成...")
    
    try:
        from src.website_builder.builder_core import IntentBasedWebsiteBuilder
        from src.website_builder.utils import ensure_dir
        
        # 创建测试输出目录
        test_output_dir = "test_output"
        ensure_dir(test_output_dir)
        
        # 创建构建器实例
        builder = IntentBasedWebsiteBuilder(output_dir=test_output_dir)
        
        if builder:
            print("✓ 构建器实例创建成功")
        
        # 清理测试目录
        import shutil
        if os.path.exists(test_output_dir):
            shutil.rmtree(test_output_dir)
        
        return True
        
    except Exception as e:
        print(f"✗ 集成测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试模块化结构...")
    print("=" * 50)
    
    # 运行所有测试
    tests = [
        ("模块导入测试", test_imports),
        ("基本功能测试", test_basic_functionality),
        ("模块集成测试", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1
            print(f"✓ {test_name}通过")
        else:
            print(f"✗ {test_name}失败")
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！模块化结构工作正常。")
        return True
    else:
        print("❌ 部分测试失败，需要检查模块化结构。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)