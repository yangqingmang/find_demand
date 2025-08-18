#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多项目部署脚本
支持按主题部署不同的网站项目
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.website_builder.project_manager import ProjectManager
from src.deployment.deployment_manager import DeploymentManager

def deploy_specific_project(project_manager, deployment_manager, project_index):
    """部署指定项目"""
    project = project_manager.get_project_by_index(project_index)
    if not project:
        print(f"❌ 项目索引 {project_index} 不存在")
        return False
    
    # 查找网站源文件
    project_dir = project['directory']
    website_source = os.path.join(project_dir, 'website_source')
    
    if not os.path.exists(website_source):
        print(f"❌ 项目 {project['project_name']} 的网站源文件不存在")
        print(f"💡 请先运行网站生成器为该项目生成网站文件")
        return False
    
    print(f"\n🚀 开始部署项目: {project['project_name']}")
    print(f"📁 源文件目录: {website_source}")
    
    # 执行部署
    success, result, deployment_record = deployment_manager.deploy_website(
        source_dir=website_source,
        deployer_name='vercel',
        project_info=project
    )
    
    if success:
        print(f"✅ 部署成功！")
        print(f"🌐 访问地址: {result}")
        project_manager.update_project_status(project_dir, 'deployed')
    else:
        print(f"❌ 部署失败: {result}")
    
    return success

def deploy_by_theme(project_manager, deployment_manager, theme):
    """按主题部署最新项目"""
    theme_projects = project_manager.get_project_by_theme(theme)
    if not theme_projects:
        print(f"❌ 未找到主题为 {theme} 的项目")
        return False
    
    latest_project = theme_projects[0]  # 已按时间排序
    
    print(f"\n🎯 部署主题 {theme} 的最新项目: {latest_project['project_name']}")
    
    # 使用部署管理器的新方法
    success, result, deployment_record = deployment_manager.deploy_project_by_theme(theme, 'vercel')
    
    if success:
        print(f"✅ 部署成功！")
        print(f"🌐 访问地址: {result}")
    else:
        print(f"❌ 部署失败: {result}")
    
    return success

def deploy_all_projects(project_manager, deployment_manager):
    """部署所有项目"""
    projects = project_manager.load_projects_index()
    if not projects:
        print("❌ 没有可部署的项目")
        return False
    
    print(f"\n🚀 开始批量部署 {len(projects)} 个项目...")
    
    success_count = 0
    failed_count = 0
    
    for i, project in enumerate(projects, 1):
        print(f"\n[{i}/{len(projects)}] 部署项目: {project['project_name']}")
        
        if deploy_specific_project(project_manager, deployment_manager, i):
            success_count += 1
        else:
            failed_count += 1
    
    print(f"\n📊 批量部署完成:")
    print(f"   ✅ 成功: {success_count} 个项目")
    print(f"   ❌ 失败: {failed_count} 个项目")
    
    return success_count > 0

def create_symlink_interactive(project_manager):
    """交互式创建符号链接"""
    projects = project_manager.load_projects_index()
    if not projects:
        print("❌ 没有可用项目")
        return False
    
    print(f"\n🔗 符号链接选项:")
    print("1. 链接到最新项目")
    print("2. 按主题链接")
    print("3. 链接到指定项目")
    
    try:
        choice = input("请选择 (1-3): ").strip()
        
        if choice == '1':
            return project_manager.create_symlink_to_latest()
        elif choice == '2':
            # 显示可用主题
            themes = set(p['theme'] for p in projects)
            print(f"\n可用主题: {', '.join(themes)}")
            theme = input("请输入主题名称: ").strip()
            return project_manager.create_symlink_to_latest(theme)
        elif choice == '3':
            project_manager.list_projects()
            index = int(input("请输入项目编号: ").strip())
            project = project_manager.get_project_by_index(index)
            if project:
                return project_manager.create_symlink_to_latest()
            else:
                print("❌ 无效的项目编号")
                return False
        else:
            print("❌ 无效选择")
            return False
            
    except (ValueError, KeyboardInterrupt):
        print("\n❌ 操作取消")
        return False

def main():
    """主函数"""
    print("🚀 多项目部署管理器")
    print("=" * 60)
    
    # 创建管理器
    project_manager = ProjectManager()
    deployment_manager = DeploymentManager()
    
    # 显示项目统计
    project_manager.print_stats()
    
    # 列出所有项目
    projects = project_manager.list_projects()
    
    if not projects:
        print("\n❌ 没有可部署的项目")
        print("💡 请先运行网站生成器创建项目")
        return
    
    while True:
        print(f"\n🎯 部署选项:")
        print("1. 部署指定项目")
        print("2. 部署指定主题的最新项目")
        print("3. 部署所有项目")
        print("4. 创建符号链接到项目")
        print("5. 查看部署历史")
        print("6. 清理空项目")
        print("7. 退出")
        
        try:
            choice = input("\n请选择操作 (1-7): ").strip()
            
            if choice == '1':
                # 部署指定项目
                try:
                    index = int(input("请输入项目编号: ").strip())
                    deploy_specific_project(project_manager, deployment_manager, index)
                except ValueError:
                    print("❌ 请输入有效的数字")
            
            elif choice == '2':
                # 部署指定主题
                themes = set(p['theme'] for p in projects)
                print(f"\n可用主题: {', '.join(themes)}")
                theme = input("请输入主题名称: ").strip()
                if theme in themes:
                    deploy_by_theme(project_manager, deployment_manager, theme)
                else:
                    print("❌ 主题不存在")
            
            elif choice == '3':
                # 部署所有项目
                confirm = input("确认部署所有项目？(y/N): ").strip().lower()
                if confirm == 'y':
                    deploy_all_projects(project_manager, deployment_manager)
            
            elif choice == '4':
                # 创建符号链接
                create_symlink_interactive(project_manager)
            
            elif choice == '5':
                # 查看部署历史
                history = deployment_manager.get_deployment_history()
                if history:
                    print(f"\n📋 最近 {min(5, len(history))} 次部署:")
                    for record in history[-5:]:
                        status = "✅" if record['success'] else "❌"
                        print(f"  {status} {record['timestamp'][:19]} - {record.get('project_info', {}).get('project_name', 'Unknown')}")
                else:
                    print("\n📭 暂无部署历史")
            
            elif choice == '6':
                # 清理空项目
                project_manager.cleanup_empty_projects()
            
            elif choice == '7':
                # 退出
                print("👋 再见！")
                break
            
            else:
                print("❌ 无效选择，请输入 1-7")
                
        except KeyboardInterrupt:
            print("\n\n👋 用户取消操作，再见！")
            break
        except Exception as e:
            print(f"\n❌ 操作失败: {e}")

if __name__ == "__main__":
    main()