#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网站项目管理器
用于管理多个主题的网站项目
"""

import json
import os
import shutil
from datetime import datetime
from typing import List, Dict, Optional

class ProjectManager:
    """网站项目管理器"""
    
    def __init__(self):
        self.projects_dir = 'generated_websites'
        self.index_file = os.path.join(self.projects_dir, 'projects_index.json')
        self.ensure_projects_dir()
    
    def ensure_projects_dir(self):
        """确保项目目录存在"""
        os.makedirs(self.projects_dir, exist_ok=True)
    
    def load_projects_index(self) -> List[Dict]:
        """加载项目索引"""
        if not os.path.exists(self.index_file):
            return []
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 读取项目索引失败: {e}")
            return []
    
    def save_projects_index(self, projects: List[Dict]):
        """保存项目索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(projects, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存项目索引失败: {e}")
    
    def list_projects(self) -> List[Dict]:
        """列出所有项目"""
        projects = self.load_projects_index()
        
        if not projects:
            print("📭 暂无项目")
            return []
        
        print(f"\n📋 项目列表 (共 {len(projects)} 个项目):")
        print("=" * 100)
        
        for i, project in enumerate(projects, 1):
            status_emoji = {
                'plan_generated': '📋',
                'website_generated': '🌐',
                'deployed': '🚀',
                'archived': '📦'
            }.get(project.get('status', 'unknown'), '❓')
            
            print(f"{i}. {status_emoji} {project['project_name']}")
            print(f"   主题: {project['theme']} | 关键词: {project['main_keyword']}")
            print(f"   创建时间: {project['created_at'][:19].replace('T', ' ')}")
            print(f"   目录: {project['directory']}")
            print(f"   状态: {project.get('status', 'unknown')}")
            print("-" * 100)
        
        return projects
    
    def get_project_by_index(self, index: int) -> Optional[Dict]:
        """根据索引获取项目"""
        projects = self.load_projects_index()
        if 1 <= index <= len(projects):
            return projects[index - 1]
        return None
    
    def get_project_by_theme(self, theme: str) -> List[Dict]:
        """根据主题获取项目"""
        projects = self.load_projects_index()
        return [p for p in projects if p['theme'] == theme]
    
    def update_project_status(self, project_dir: str, new_status: str):
        """更新项目状态"""
        projects = self.load_projects_index()
        
        for project in projects:
            if project['directory'] == project_dir:
                project['status'] = new_status
                project['updated_at'] = datetime.now().isoformat()
                break
        
        self.save_projects_index(projects)
        print(f"✅ 项目状态已更新为: {new_status}")
    
    def archive_project(self, project_dir: str):
        """归档项目"""
        if not os.path.exists(project_dir):
            print(f"❌ 项目目录不存在: {project_dir}")
            return False
        
        # 创建归档目录
        archive_dir = os.path.join(self.projects_dir, 'archived')
        os.makedirs(archive_dir, exist_ok=True)
        
        # 移动项目到归档目录
        project_name = os.path.basename(project_dir)
        archive_path = os.path.join(archive_dir, project_name)
        
        try:
            shutil.move(project_dir, archive_path)
            self.update_project_status(archive_path, 'archived')
            print(f"📦 项目已归档到: {archive_path}")
            return True
        except Exception as e:
            print(f"❌ 归档失败: {e}")
            return False
    
    def delete_project(self, project_dir: str, confirm: bool = False):
        """删除项目"""
        if not confirm:
            print("⚠️  删除操作需要确认，请设置 confirm=True")
            return False
        
        if not os.path.exists(project_dir):
            print(f"❌ 项目目录不存在: {project_dir}")
            return False
        
        try:
            shutil.rmtree(project_dir)
            
            # 从索引中移除
            projects = self.load_projects_index()
            projects = [p for p in projects if p['directory'] != project_dir]
            self.save_projects_index(projects)
            
            print(f"🗑️ 项目已删除: {project_dir}")
            return True
        except Exception as e:
            print(f"❌ 删除失败: {e}")
            return False
    
    def create_symlink_to_latest(self, theme: str = None):
        """创建指向最新项目的符号链接"""
        projects = self.load_projects_index()
        
        if theme:
            # 筛选特定主题的项目
            theme_projects = [p for p in projects if p['theme'] == theme]
            if not theme_projects:
                print(f"❌ 未找到主题为 {theme} 的项目")
                return False
            latest_project = theme_projects[0]  # 索引已按时间排序
        else:
            # 获取最新项目
            if not projects:
                print("❌ 没有可用项目")
                return False
            latest_project = projects[0]
        
        # 创建符号链接
        link_path = 'generated_website'
        
        # 删除现有链接或目录
        if os.path.exists(link_path):
            if os.path.islink(link_path):
                os.unlink(link_path)
            else:
                # 如果是目录，先备份
                backup_path = f"generated_website_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.move(link_path, backup_path)
                print(f"📦 原目录已备份到: {backup_path}")
        
        try:
            # 创建符号链接
            if os.name == 'nt':  # Windows
                # Windows 需要管理员权限创建符号链接，使用目录连接
                import subprocess
                subprocess.run(['mklink', '/D', link_path, latest_project['directory']], 
                             shell=True, check=True)
            else:  # Unix/Linux/Mac
                os.symlink(latest_project['directory'], link_path)
            
            print(f"🔗 已创建符号链接: {link_path} -> {latest_project['directory']}")
            print(f"📋 当前活动项目: {latest_project['project_name']}")
            return True
            
        except Exception as e:
            print(f"❌ 创建符号链接失败: {e}")
            # 回退方案：复制目录
            try:
                website_source = os.path.join(latest_project['directory'], 'website_source')
                if os.path.exists(website_source):
                    shutil.copytree(website_source, link_path)
                    print(f"📁 已复制网站文件到: {link_path}")
                    return True
            except Exception as e2:
                print(f"❌ 复制目录也失败: {e2}")
            return False
    
    def get_project_stats(self) -> Dict:
        """获取项目统计信息"""
        projects = self.load_projects_index()
        
        stats = {
            'total_projects': len(projects),
            'by_theme': {},
            'by_status': {},
            'latest_project': None,
            'oldest_project': None
        }
        
        if not projects:
            return stats
        
        # 按主题统计
        for project in projects:
            theme = project['theme']
            stats['by_theme'][theme] = stats['by_theme'].get(theme, 0) + 1
        
        # 按状态统计
        for project in projects:
            status = project.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
        
        # 最新和最旧项目
        stats['latest_project'] = projects[0]
        stats['oldest_project'] = projects[-1]
        
        return stats
    
    def print_stats(self):
        """打印项目统计信息"""
        stats = self.get_project_stats()
        
        print(f"\n📊 项目统计信息")
        print("=" * 50)
        print(f"总项目数: {stats['total_projects']}")
        
        if stats['total_projects'] > 0:
            print(f"\n📋 按主题分布:")
            for theme, count in stats['by_theme'].items():
                print(f"  {theme}: {count} 个项目")
            
            print(f"\n🏷️ 按状态分布:")
            for status, count in stats['by_status'].items():
                status_name = {
                    'plan_generated': '计划已生成',
                    'website_generated': '网站已生成',
                    'deployed': '已部署',
                    'archived': '已归档'
                }.get(status, status)
                print(f"  {status_name}: {count} 个项目")
            
            print(f"\n🕒 时间信息:")
            latest = stats['latest_project']
            oldest = stats['oldest_project']
            print(f"  最新项目: {latest['project_name']} ({latest['created_at'][:10]})")
            print(f"  最旧项目: {oldest['project_name']} ({oldest['created_at'][:10]})")
    
    def cleanup_empty_projects(self):
        """清理空项目目录"""
        projects = self.load_projects_index()
        cleaned_projects = []
        removed_count = 0
        
        for project in projects:
            project_dir = project['directory']
            if os.path.exists(project_dir) and os.listdir(project_dir):
                cleaned_projects.append(project)
            else:
                print(f"🗑️ 清理空项目: {project['project_name']}")
                if os.path.exists(project_dir):
                    try:
                        os.rmdir(project_dir)
                    except:
                        pass
                removed_count += 1
        
        if removed_count > 0:
            self.save_projects_index(cleaned_projects)
            print(f"✅ 已清理 {removed_count} 个空项目")
        else:
            print("✅ 没有需要清理的空项目")

def main():
    """主函数 - 提供命令行界面"""
    import sys
    
    manager = ProjectManager()
    
    if len(sys.argv) < 2:
        print("📋 项目管理器使用方法:")
        print("  python project_manager.py list          # 列出所有项目")
        print("  python project_manager.py stats         # 显示统计信息")
        print("  python project_manager.py link [theme]  # 创建符号链接到最新项目")
        print("  python project_manager.py cleanup       # 清理空项目")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        manager.list_projects()
    elif command == 'stats':
        manager.print_stats()
    elif command == 'link':
        theme = sys.argv[2] if len(sys.argv) > 2 else None
        manager.create_symlink_to_latest(theme)
    elif command == 'cleanup':
        manager.cleanup_empty_projects()
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()