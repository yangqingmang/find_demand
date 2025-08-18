#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
部署管理器 - 统一管理多种部署服务
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .base_deployer import BaseDeployer
from .cloudflare_deployer import CloudflareDeployer
from .vercel_deployer import VercelDeployer


class DeploymentManager:
    """部署管理器"""

    # 支持的部署服务
    SUPPORTED_DEPLOYERS = {
        'cloudflare': CloudflareDeployer,
        'vercel': VercelDeployer
    }

    def __init__(self, config_path: str = None):
        """
        初始化部署管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.deployment_history = []

    def _load_config(self) -> Dict[str, Any]:
        """加载部署配置"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"加载部署配置失败: {e}")
        
        # 返回默认配置
        return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "default_deployer": "vercel",
            "deployers": {
                "cloudflare": {
                    "api_token": "",
                    "account_id": "",
                    "project_name": "my-website",
                    "custom_domain": ""
                },
                "vercel": {
                    "api_token": "",
                    "team_id": "",
                    "project_name": "my-website",
                    "custom_domain": ""
                }
            },
            "deployment_settings": {
                "auto_cleanup": True,
                "max_retries": 3,
                "timeout": 300
            }
        }

    def get_available_deployers(self) -> List[str]:
        """获取可用的部署服务列表"""
        return list(self.SUPPORTED_DEPLOYERS.keys())

    def get_deployer_info(self, deployer_name: str) -> Dict[str, Any]:
        """
        获取部署服务信息
        
        Args:
            deployer_name: 部署服务名称
            
        Returns:
            部署服务信息
        """
        if deployer_name not in self.SUPPORTED_DEPLOYERS:
            return {}
        
        deployer_class = self.SUPPORTED_DEPLOYERS[deployer_name]
        temp_deployer = deployer_class()
        
        return {
            'name': deployer_name,
            'supported_features': temp_deployer.get_supported_features(),
            'config_required': self._get_required_config(deployer_name)
        }

    def _get_required_config(self, deployer_name: str) -> List[str]:
        """获取部署服务所需的配置项"""
        config_requirements = {
            'cloudflare': ['api_token', 'account_id', 'project_name'],
            'vercel': ['api_token', 'project_name']
        }
        return config_requirements.get(deployer_name, [])

    def validate_deployer_config(self, deployer_name: str) -> Tuple[bool, str]:
        """
        验证部署服务配置
        
        Args:
            deployer_name: 部署服务名称
            
        Returns:
            (是否有效, 错误信息)
        """
        if deployer_name not in self.SUPPORTED_DEPLOYERS:
            return False, f"不支持的部署服务: {deployer_name}"
        
        if deployer_name not in self.config.get('deployers', {}):
            return False, f"缺少 {deployer_name} 的配置"
        
        deployer_config = self.config['deployers'][deployer_name]
        deployer_class = self.SUPPORTED_DEPLOYERS[deployer_name]
        deployer = deployer_class(deployer_config)
        
        return deployer.validate_config()

    def deploy_website(self, 
                      source_dir: str, 
                      deployer_name: str = None,
                      custom_config: Dict[str, Any] = None,
                      project_info: Dict[str, Any] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        部署网站
        
        Args:
            source_dir: 网站源文件目录
            deployer_name: 部署服务名称，如果为None则使用默认服务
            custom_config: 自定义配置，会覆盖默认配置
            project_info: 项目信息（用于多项目管理）
            
        Returns:
            (是否成功, 部署URL或错误信息, 部署信息)
        """
        # 确定使用的部署服务
        if not deployer_name:
            deployer_name = self.config.get('default_deployer', 'vercel')
        
        if deployer_name not in self.SUPPORTED_DEPLOYERS:
            return False, f"不支持的部署服务: {deployer_name}", {}
        
        # 准备配置
        deployer_config = self.config.get('deployers', {}).get(deployer_name, {}).copy()
        if custom_config:
            deployer_config.update(custom_config)
        
        # 如果有项目信息，自动设置项目名称
        if project_info:
            theme = project_info.get('theme', 'website')
            main_keyword = project_info.get('main_keyword', 'site')
            # 生成项目名称
            clean_keyword = ''.join(c for c in main_keyword.lower() if c.isalnum() or c in '-_')[:20]
            project_name = f"{theme}-{clean_keyword}".replace('_', '-')
            deployer_config['project_name'] = project_name
            
            print(f"🎯 自动设置项目名称: {project_name}")
        
        # 创建部署器
        deployer_class = self.SUPPORTED_DEPLOYERS[deployer_name]
        deployer = deployer_class(deployer_config)
        
        # 验证配置
        is_valid, error_msg = deployer.validate_config()
        if not is_valid:
            return False, f"配置验证失败: {error_msg}", {}
        
        # 验证源文件目录
        if not os.path.exists(source_dir):
            return False, f"源文件目录不存在: {source_dir}", {}
        
        # 开始部署
        temp_dir = None
        try:
            # 创建临时目录
            temp_dir = deployer.create_temp_dir()
            
            # 验证文件
            is_valid, error_msg = deployer.validate_files(source_dir)
            if not is_valid:
                return False, f"文件验证失败: {error_msg}", {}
            
            # 准备文件
            if not deployer.prepare_files(source_dir, temp_dir):
                return False, "文件准备失败", {}
            
            # 验证准备后的文件
            is_valid, error_msg = deployer.validate_files(temp_dir)
            if not is_valid:
                return False, f"准备后文件验证失败: {error_msg}", {}
            
            # 执行部署
            success, result = deployer.deploy(temp_dir)
            
            # 记录部署历史
            deployment_record = {
                'timestamp': datetime.now().isoformat(),
                'deployer': deployer_name,
                'source_dir': source_dir,
                'project_directory': self._extract_project_directory(source_dir),
                'project_info': project_info or {},
                'success': success,
                'result': result,
                'deployment_info': deployer.get_deployment_info(),
                'config_used': custom_config or {}
            }
            self.deployment_history.append(deployment_record)
            
            # 保存部署历史到文件
            self._save_deployment_history_to_file(deployment_record)
            
            return success, result, deployment_record
            
        except Exception as e:
            error_msg = f"部署过程中发生错误: {e}"
            
            # 记录失败的部署历史
            deployment_record = {
                'timestamp': datetime.now().isoformat(),
                'deployer': deployer_name,
                'source_dir': source_dir,
                'project_info': project_info or {},
                'success': False,
                'result': error_msg,
                'deployment_info': {}
            }
            self.deployment_history.append(deployment_record)
            
            return False, error_msg, {}
            
        finally:
            # 清理临时目录
            if temp_dir and self.config.get('deployment_settings', {}).get('auto_cleanup', True):
                deployer.cleanup_temp_dir(temp_dir)

    def deploy_project_by_theme(self, theme: str, deployer_name: str = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        根据主题部署最新项目
        
        Args:
            theme: 项目主题
            deployer_name: 部署服务名称
            
        Returns:
            (是否成功, 部署URL或错误信息, 部署信息)
        """
        # 导入项目管理器
        try:
            from ..website_builder.project_manager import ProjectManager
            manager = ProjectManager()
            
            # 获取指定主题的项目
            theme_projects = manager.get_project_by_theme(theme)
            if not theme_projects:
                return False, f"未找到主题为 {theme} 的项目", {}
            
            # 获取最新项目
            latest_project = theme_projects[0]  # 已按时间排序
            
            # 查找网站源文件目录
            project_dir = latest_project['directory']
            website_source = os.path.join(project_dir, 'website_source')
            
            if not os.path.exists(website_source):
                return False, f"项目 {latest_project['project_name']} 的网站源文件不存在", {}
            
            print(f"🚀 部署项目: {latest_project['project_name']}")
            print(f"📁 源文件目录: {website_source}")
            
            # 执行部署
            success, result, deployment_record = self.deploy_website(
                source_dir=website_source,
                deployer_name=deployer_name,
                project_info=latest_project
            )
            
            if success:
                # 更新项目状态
                manager.update_project_status(project_dir, 'deployed')
            
            return success, result, deployment_record
            
        except ImportError:
            return False, "无法导入项目管理器", {}
        except Exception as e:
            return False, f"部署项目失败: {e}", {}

    def get_deployment_history(self) -> List[Dict[str, Any]]:
        """获取部署历史"""
        return self.deployment_history

    def get_latest_deployment(self, deployer_name: str = None) -> Optional[Dict[str, Any]]:
        """
        获取最新的部署记录
        
        Args:
            deployer_name: 部署服务名称，如果为None则返回最新的任意部署
            
        Returns:
            部署记录或None
        """
        filtered_history = self.deployment_history
        
        if deployer_name:
            filtered_history = [
                record for record in self.deployment_history 
                if record['deployer'] == deployer_name
            ]
        
        if not filtered_history:
            return None
        
        return max(filtered_history, key=lambda x: x['timestamp'])

    def save_config(self, config_path: str = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config_path: 配置文件路径，如果为None则使用初始化时的路径
            
        Returns:
            是否成功保存
        """
        save_path = config_path or self.config_path
        if not save_path:
            return False
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False

    def update_deployer_config(self, deployer_name: str, config: Dict[str, Any]) -> bool:
        """
        更新部署服务配置
        
        Args:
            deployer_name: 部署服务名称
            config: 新的配置
            
        Returns:
            是否成功更新
        """
        if deployer_name not in self.SUPPORTED_DEPLOYERS:
            return False
        
        if 'deployers' not in self.config:
            self.config['deployers'] = {}
        
        self.config['deployers'][deployer_name] = config
        return True

    def set_default_deployer(self, deployer_name: str) -> bool:
        """
        设置默认部署服务
        
        Args:
            deployer_name: 部署服务名称
            
        Returns:
            是否成功设置
        """
        if deployer_name not in self.SUPPORTED_DEPLOYERS:
            return False
        
        self.config['default_deployer'] = deployer_name
        return True

    def generate_config_template(self, output_path: str) -> bool:
        """
        生成配置文件模板
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            是否成功生成
        """
        try:
            template = {
                "default_deployer": "vercel",
                "deployers": {
                    "cloudflare": {
                        "api_token": "your_cloudflare_api_token",
                        "account_id": "your_cloudflare_account_id",
                        "project_name": "my-website",
                        "custom_domain": "example.com"
                    },
                    "vercel": {
                        "api_token": "your_vercel_api_token",
                        "team_id": "your_team_id_optional",
                        "project_name": "my-website",
                        "custom_domain": "example.com"
                    }
                },
                "deployment_settings": {
                    "auto_cleanup": True,
                    "max_retries": 3,
                    "timeout": 300
                }
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(template, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"生成配置模板失败: {e}")
            return False

    def list_deployments(self, deployer_name: str) -> List[Dict[str, Any]]:
        """
        列出指定部署服务的所有部署记录
        
        Args:
            deployer_name: 部署服务名称
            
        Returns:
            部署记录列表
        """
        return [
            record for record in self.deployment_history 
            if record['deployer'] == deployer_name
        ]

    def _extract_project_directory(self, source_dir: str) -> str:
        """从源目录路径中提取项目目录名"""
        # 如果是website_source目录，则获取其父目录名
        if source_dir.endswith('website_source'):
            return os.path.basename(os.path.dirname(source_dir))
        else:
            return os.path.basename(source_dir)

    def _save_deployment_history_to_file(self, deployment_record: Dict[str, Any]) -> None:
        """保存部署历史到文件"""
        try:
            # 确定历史文件路径
            history_dir = os.path.dirname(os.path.dirname(deployment_record['source_dir']))
            if not history_dir or not os.path.exists(history_dir):
                history_dir = 'output'  # 默认目录
            
            history_file = os.path.join(history_dir, 'deployment_history.json')
            
            # 读取现有历史
            history = []
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # 添加新记录
            history.append(deployment_record)
            
            # 保持最近100条记录
            if len(history) > 100:
                history = history[-100:]
            
            # 保存历史
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            
            print(f"📝 部署历史已更新: {history_file}")
            
        except Exception as e:
            print(f"⚠️ 保存部署历史失败: {e}")

    def load_deployment_history_from_file(self, base_dir: str = 'output') -> List[Dict[str, Any]]:
        """从文件加载部署历史"""
        try:
            history_file = os.path.join(base_dir, 'deployment_history.json')
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"读取部署历史失败: {e}")
            return []

    def get_deployment_stats(self) -> Dict[str, Any]:
        """
        获取部署统计信息
        
        Returns:
            统计信息字典
        """
        # 合并内存中的历史和文件中的历史
        all_history = self.deployment_history + self.load_deployment_history_from_file()
        
        total_deployments = len(all_history)
        successful_deployments = len([r for r in all_history if r['success']])
        failed_deployments = total_deployments - successful_deployments
        
        deployer_stats = {}
        project_stats = {}
        
        for record in all_history:
            deployer = record['deployer']
            project = record.get('project_directory', 'unknown')
            
            # 部署服务统计
            if deployer not in deployer_stats:
                deployer_stats[deployer] = {'total': 0, 'success': 0, 'failed': 0}
            
            deployer_stats[deployer]['total'] += 1
            if record['success']:
                deployer_stats[deployer]['success'] += 1
            else:
                deployer_stats[deployer]['failed'] += 1
            
            # 项目统计
            if project not in project_stats:
                project_stats[project] = {'total': 0, 'success': 0, 'failed': 0, 'last_deployment': ''}
            
            project_stats[project]['total'] += 1
            if record['success']:
                project_stats[project]['success'] += 1
            else:
                project_stats[project]['failed'] += 1
            
            # 更新最后部署时间
            if record['timestamp'] > project_stats[project]['last_deployment']:
                project_stats[project]['last_deployment'] = record['timestamp']
        
        return {
            'total_deployments': total_deployments,
            'successful_deployments': successful_deployments,
            'failed_deployments': failed_deployments,
            'success_rate': (successful_deployments / total_deployments * 100) if total_deployments > 0 else 0,
            'deployer_stats': deployer_stats,
            'project_stats': project_stats
        }
