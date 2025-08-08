#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
部署历史查看工具
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.deployment.deployment_manager import DeploymentManager


def format_timestamp(timestamp_str: str) -> str:
    """格式化时间戳"""
    try:
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return timestamp_str


def print_deployment_record(record: Dict[str, Any], index: int = None) -> None:
    """打印单个部署记录"""
    prefix = f"[{index}] " if index is not None else ""
    status = "✅ 成功" if record['success'] else "❌ 失败"
    
    print(f"{prefix}部署记录:")
    print(f"  时间: {format_timestamp(record['timestamp'])}")
    print(f"  项目: {record.get('project_directory', '未知')}")
    print(f"  服务: {record['deployer']}")
    print(f"  状态: {status}")
    print(f"  结果: {record['result']}")
    
    if record.get('config_used'):
        print(f"  配置: {record['config_used']}")
    
    print()


def show_deployment_history(base_dir: str = 'output') -> None:
    """显示部署历史"""
    manager = DeploymentManager()
    history = manager.load_deployment_history_from_file(base_dir)
    
    if not history:
        print("📝 暂无部署历史记录")
        return
    
    print(f"📋 部署历史记录 (共 {len(history)} 条)")
    print("=" * 60)
    
    # 按时间倒序排列
    history.sort(key=lambda x: x['timestamp'], reverse=True)
    
    for i, record in enumerate(history, 1):
        print_deployment_record(record, i)


def show_deployment_stats(base_dir: str = 'output') -> None:
    """显示部署统计"""
    manager = DeploymentManager()
    stats = manager.get_deployment_stats()
    
    print("📊 部署统计信息")
    print("=" * 60)
    
    print(f"总部署次数: {stats['total_deployments']}")
    print(f"成功次数: {stats['successful_deployments']}")
    print(f"失败次数: {stats['failed_deployments']}")
    print(f"成功率: {stats['success_rate']:.1f}%")
    
    print("\n🔧 按部署服务统计:")
    for deployer, stat in stats['deployer_stats'].items():
        success_rate = (stat['success'] / stat['total'] * 100) if stat['total'] > 0 else 0
        print(f"  {deployer}:")
        print(f"    总计: {stat['total']}")
        print(f"    成功: {stat['success']}")
        print(f"    失败: {stat['failed']}")
        print(f"    成功率: {success_rate:.1f}%")
    
    if 'project_stats' in stats:
        print("\n📁 按项目统计:")
        for project, stat in stats['project_stats'].items():
            success_rate = (stat['success'] / stat['total'] * 100) if stat['total'] > 0 else 0
            last_deployment = format_timestamp(stat['last_deployment']) if stat['last_deployment'] else '从未部署'
            print(f"  {project}:")
            print(f"    总计: {stat['total']}")
            print(f"    成功: {stat['success']}")
            print(f"    失败: {stat['failed']}")
            print(f"    成功率: {success_rate:.1f}%")
            print(f"    最后部署: {last_deployment}")


def show_recent_deployments(base_dir: str = 'output', count: int = 5) -> None:
    """显示最近的部署记录"""
    manager = DeploymentManager()
    history = manager.load_deployment_history_from_file(base_dir)
    
    if not history:
        print("📝 暂无部署历史记录")
        return
    
    # 按时间倒序排列，取最近的几条
    history.sort(key=lambda x: x['timestamp'], reverse=True)
    recent = history[:count]
    
    print(f"🕒 最近 {len(recent)} 次部署")
    print("=" * 60)
    
    for i, record in enumerate(recent, 1):
        print_deployment_record(record, i)


def filter_deployments(base_dir: str = 'output', 
                      deployer: str = None, 
                      project: str = None,
                      success_only: bool = False) -> None:
    """筛选部署记录"""
    manager = DeploymentManager()
    history = manager.load_deployment_history_from_file(base_dir)
    
    if not history:
        print("📝 暂无部署历史记录")
        return
    
    # 应用筛选条件
    filtered = history
    
    if deployer:
        filtered = [r for r in filtered if r['deployer'] == deployer]
    
    if project:
        filtered = [r for r in filtered if project in r.get('project_directory', '')]
    
    if success_only:
        filtered = [r for r in filtered if r['success']]
    
    if not filtered:
        print("📝 没有符合条件的部署记录")
        return
    
    # 构建筛选条件描述
    conditions = []
    if deployer:
        conditions.append(f"部署服务={deployer}")
    if project:
        conditions.append(f"项目包含={project}")
    if success_only:
        conditions.append("仅成功")
    
    condition_str = ", ".join(conditions) if conditions else "无筛选"
    
    print(f"🔍 筛选结果 (条件: {condition_str}, 共 {len(filtered)} 条)")
    print("=" * 60)
    
    # 按时间倒序排列
    filtered.sort(key=lambda x: x['timestamp'], reverse=True)
    
    for i, record in enumerate(filtered, 1):
        print_deployment_record(record, i)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='部署历史查看工具')
    
    parser.add_argument('--base-dir', '-d', default='output', help='基础输出目录')
    parser.add_argument('--action', '-a', choices=['history', 'stats', 'recent', 'filter'], 
                       default='recent', help='操作类型')
    parser.add_argument('--count', '-c', type=int, default=5, help='显示记录数量')
    parser.add_argument('--deployer', help='筛选部署服务')
    parser.add_argument('--project', help='筛选项目名称')
    parser.add_argument('--success-only', action='store_true', help='仅显示成功的部署')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'history':
            show_deployment_history(args.base_dir)
        elif args.action == 'stats':
            show_deployment_stats(args.base_dir)
        elif args.action == 'recent':
            show_recent_deployments(args.base_dir, args.count)
        elif args.action == 'filter':
            filter_deployments(
                base_dir=args.base_dir,
                deployer=args.deployer,
                project=args.project,
                success_only=args.success_only
            )
        
    except Exception as e:
        print(f"❌ 执行过程中发生错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())