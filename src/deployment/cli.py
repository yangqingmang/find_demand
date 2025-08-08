#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
部署命令行接口
"""

import os
import sys
import argparse
import json
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.deployment.deployment_manager import DeploymentManager


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='网站一键部署工具')
    
    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 部署命令
    deploy_parser = subparsers.add_parser('deploy', help='部署网站')
    deploy_parser.add_argument('source_dir', help='网站源文件目录')
    deploy_parser.add_argument('--deployer', '-d', choices=['cloudflare', 'vercel'], 
                              help='部署服务（默认使用配置文件中的默认服务）')
    deploy_parser.add_argument('--config', '-c', help='配置文件路径')
    deploy_parser.add_argument('--project-name', help='项目名称')
    deploy_parser.add_argument('--custom-domain', help='自定义域名')
    
    # 配置命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_subparsers = config_parser.add_subparsers(dest='config_action')
    
    # 生成配置模板
    template_parser = config_subparsers.add_parser('template', help='生成配置文件模板')
    template_parser.add_argument('output_path', help='输出文件路径')
    
    # 验证配置
    validate_parser = config_subparsers.add_parser('validate', help='验证配置')
    validate_parser.add_argument('--config', '-c', help='配置文件路径')
    validate_parser.add_argument('--deployer', '-d', choices=['cloudflare', 'vercel'], 
                                help='验证特定部署服务的配置')
    
    # 列出支持的部署服务
    list_parser = subparsers.add_parser('list', help='列出支持的部署服务')
    
    # 查看部署历史
    history_parser = subparsers.add_parser('history', help='查看部署历史')
    history_parser.add_argument('--deployer', '-d', choices=['cloudflare', 'vercel'], 
                               help='查看特定部署服务的历史')
    history_parser.add_argument('--stats', action='store_true', help='显示统计信息')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'deploy':
            return handle_deploy(args)
        elif args.command == 'config':
            return handle_config(args)
        elif args.command == 'list':
            return handle_list(args)
        elif args.command == 'history':
            return handle_history(args)
        else:
            parser.print_help()
            return 1
    except Exception as e:
        print(f"错误: {e}")
        return 1


def handle_deploy(args) -> int:
    """处理部署命令"""
    # 检查源目录
    if not os.path.exists(args.source_dir):
        print(f"错误: 源目录不存在: {args.source_dir}")
        return 1
    
    # 初始化部署管理器
    manager = DeploymentManager(args.config)
    
    # 准备自定义配置
    custom_config = {}
    if args.project_name:
        custom_config['project_name'] = args.project_name
    if args.custom_domain:
        custom_config['custom_domain'] = args.custom_domain
    
    # 执行部署
    print(f"开始部署网站: {args.source_dir}")
    success, result, deployment_info = manager.deploy_website(
        source_dir=args.source_dir,
        deployer_name=args.deployer,
        custom_config=custom_config
    )
    
    if success:
        print(f"✅ 部署成功!")
        print(f"🌐 访问地址: {result}")
        
        # 显示部署信息
        if deployment_info:
            print(f"📊 部署ID: {deployment_info.get('deployment_id', 'N/A')}")
            print(f"🚀 部署服务: {args.deployer or manager.config.get('default_deployer', 'N/A')}")
            
            features = deployment_info.get('supported_features', [])
            if features:
                print(f"✨ 支持功能: {', '.join(features)}")
        
        return 0
    else:
        print(f"❌ 部署失败: {result}")
        return 1


def handle_config(args) -> int:
    """处理配置命令"""
    if args.config_action == 'template':
        manager = DeploymentManager()
        if manager.generate_config_template(args.output_path):
            print(f"✅ 配置模板已生成: {args.output_path}")
            print("请编辑配置文件，填入您的API密钥和项目信息")
            return 0
        else:
            print("❌ 配置模板生成失败")
            return 1
    
    elif args.config_action == 'validate':
        manager = DeploymentManager(args.config)
        
        if args.deployer:
            # 验证特定部署服务
            is_valid, error_msg = manager.validate_deployer_config(args.deployer)
            if is_valid:
                print(f"✅ {args.deployer} 配置验证通过")
                return 0
            else:
                print(f"❌ {args.deployer} 配置验证失败: {error_msg}")
                return 1
        else:
            # 验证所有部署服务
            all_valid = True
            for deployer_name in manager.get_available_deployers():
                is_valid, error_msg = manager.validate_deployer_config(deployer_name)
                if is_valid:
                    print(f"✅ {deployer_name}: 配置有效")
                else:
                    print(f"❌ {deployer_name}: {error_msg}")
                    all_valid = False
            
            return 0 if all_valid else 1
    
    else:
        print("请指定配置操作: template 或 validate")
        return 1


def handle_list(args) -> int:
    """处理列表命令"""
    manager = DeploymentManager()
    
    print("支持的部署服务:")
    print("=" * 50)
    
    for deployer_name in manager.get_available_deployers():
        info = manager.get_deployer_info(deployer_name)
        print(f"\n🚀 {deployer_name.upper()}")
        print(f"   必需配置: {', '.join(info['config_required'])}")
        print(f"   支持功能: {', '.join(info['supported_features'])}")
    
    return 0


def handle_history(args) -> int:
    """处理历史命令"""
    manager = DeploymentManager(args.config)
    
    if args.stats:
        # 显示统计信息
        stats = manager.get_deployment_stats()
        print("部署统计信息:")
        print("=" * 50)
        print(f"总部署次数: {stats['total_deployments']}")
        print(f"成功次数: {stats['successful_deployments']}")
        print(f"失败次数: {stats['failed_deployments']}")
        print(f"成功率: {stats['success_rate']:.1f}%")
        
        if stats['deployer_stats']:
            print("\n各服务统计:")
            for deployer, stat in stats['deployer_stats'].items():
                print(f"  {deployer}: {stat['success']}/{stat['total']} 成功")
    
    else:
        # 显示部署历史
        if args.deployer:
            deployments = manager.list_deployments(args.deployer)
            print(f"{args.deployer} 部署历史:")
        else:
            deployments = manager.get_deployment_history()
            print("所有部署历史:")
        
        print("=" * 80)
        
        if not deployments:
            print("暂无部署记录")
            return 0
        
        for deployment in reversed(deployments[-10:]):  # 显示最近10次
            status = "✅" if deployment['success'] else "❌"
            print(f"{status} {deployment['timestamp']} | {deployment['deployer']} | {deployment['result']}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())