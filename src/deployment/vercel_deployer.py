#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vercel 部署器
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional, Any, Tuple
from .base_deployer import BaseDeployer


class VercelDeployer(BaseDeployer):
    """Vercel 部署器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化Vercel部署器
        
        Args:
            config: 部署配置，包含：
                - api_token: Vercel API Token
                - team_id: 团队ID（可选）
                - project_name: 项目名称
                - custom_domain: 自定义域名（可选）
        """
        super().__init__(config)
        self.api_token = self.config.get('api_token')
        self.team_id = self.config.get('team_id')
        self.project_name = self.config.get('project_name')
        self.custom_domain = self.config.get('custom_domain')
        
        self.api_base = 'https://api.vercel.com'
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

    def validate_config(self) -> Tuple[bool, str]:
        """验证Vercel配置"""
        if not self.api_token:
            return False, "缺少Vercel API Token"
        
        if not self.project_name:
            return False, "缺少项目名称"
        
        # 验证项目名称格式
        if not self.project_name.replace('-', '').isalnum():
            return False, "项目名称只能包含字母、数字和连字符"
        
        # 测试API连接
        try:
            url = f'{self.api_base}/v2/user'
            if self.team_id:
                url += f'?teamId={self.team_id}'
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code != 200:
                return False, f"API连接失败: {response.status_code}"
            
            self.log("Vercel API连接验证成功")
            return True, ""
            
        except Exception as e:
            return False, f"API连接测试失败: {e}"

    def prepare_files(self, source_dir: str, temp_dir: str) -> bool:
        """准备Vercel部署文件"""
        try:
            # 复制所有文件到临时目录
            exclude_patterns = [
                '.git',
                '.gitignore',
                'node_modules',
                '.env',
                '*.log',
                '.DS_Store',
                '.vercel'
            ]
            
            if not self.copy_files(source_dir, temp_dir, exclude_patterns):
                return False
            
            # 生成vercel.json配置文件
            vercel_config = {
                "version": 2,
                "builds": [
                    {
                        "src": "**/*",
                        "use": "@vercel/static"
                    }
                ],
                "routes": [
                    {
                        "src": "/(.*)",
                        "dest": "/$1"
                    }
                ],
                "headers": [
                    {
                        "source": "/(.*)",
                        "headers": [
                            {
                                "key": "X-Frame-Options",
                                "value": "DENY"
                            },
                            {
                                "key": "X-Content-Type-Options",
                                "value": "nosniff"
                            },
                            {
                                "key": "X-XSS-Protection",
                                "value": "1; mode=block"
                            }
                        ]
                    }
                ]
            }
            
            vercel_config_path = os.path.join(temp_dir, 'vercel.json')
            with open(vercel_config_path, 'w', encoding='utf-8') as f:
                json.dump(vercel_config, f, indent=2)
            
            self.log("Vercel文件准备完成")
            return True
            
        except Exception as e:
            self.log(f"文件准备失败: {e}", 'error')
            return False

    def create_deployment(self, temp_dir: str) -> bool:
        """创建Vercel部署"""
        try:
            # 准备文件列表
            files = []
            for root, dirs, filenames in os.walk(temp_dir):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_path, temp_dir).replace('\\', '/')
                    
                    # 读取文件内容
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    files.append({
                        'file': relative_path,
                        'data': content.hex()  # Vercel API需要十六进制编码
                    })
            
            # 创建部署请求
            deployment_data = {
                'name': self.project_name,
                'files': files,
                'projectSettings': {
                    'framework': None,
                    'buildCommand': None,
                    'outputDirectory': None
                }
            }
            
            url = f'{self.api_base}/v13/deployments'
            if self.team_id:
                url += f'?teamId={self.team_id}'
            
            response = requests.post(
                url,
                headers=self.headers,
                json=deployment_data
            )
            
            if response.status_code == 200:
                deployment_info = response.json()
                self.deployment_id = deployment_info['id']
                self.deployment_url = f"https://{deployment_info['url']}"
                self.log(f"部署创建成功，部署ID: {self.deployment_id}")
                return True
            else:
                self.log(f"部署创建失败: {response.status_code} - {response.text}", 'error')
                return False
                
        except Exception as e:
            self.log(f"创建部署失败: {e}", 'error')
            return False

    def deploy(self, temp_dir: str) -> Tuple[bool, str]:
        """执行Vercel部署"""
        try:
            self.log("开始Vercel部署")
            
            # 创建部署
            if not self.create_deployment(temp_dir):
                return False, "部署创建失败"
            
            # 等待部署完成
            self.log("等待部署完成...")
            max_wait_time = 300  # 5分钟
            wait_time = 0
            
            while wait_time < max_wait_time:
                status_info = self.get_deployment_status()
                
                if status_info['status'] == 'READY':
                    self.deployment_status = 'success'
                    self.log(f"部署成功！访问地址: {self.deployment_url}")
                    
                    # 设置自定义域名
                    if self.custom_domain:
                        self.setup_custom_domain()
                    
                    return True, self.deployment_url
                
                elif status_info['status'] == 'ERROR':
                    self.deployment_status = 'failed'
                    return False, "部署失败"
                
                time.sleep(10)
                wait_time += 10
                self.log(f"部署进行中... ({wait_time}s)")
            
            return False, "部署超时"
            
        except Exception as e:
            self.log(f"部署失败: {e}", 'error')
            return False, str(e)

    def get_deployment_status(self) -> Dict[str, Any]:
        """获取部署状态"""
        try:
            if not self.deployment_id:
                return {'status': 'unknown', 'message': '未找到部署ID'}
            
            url = f'{self.api_base}/v13/deployments/{self.deployment_id}'
            if self.team_id:
                url += f'?teamId={self.team_id}'
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': data['readyState'],
                    'message': data.get('name', ''),
                    'url': f"https://{data['url']}",
                    'created_at': data.get('createdAt', ''),
                    'ready_at': data.get('readyAt', '')
                }
            else:
                return {'status': 'error', 'message': f'API请求失败: {response.status_code}'}
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def setup_custom_domain(self) -> bool:
        """设置自定义域名"""
        try:
            if not self.custom_domain:
                return True
            
            # 首先需要获取项目ID
            project_id = self.get_or_create_project()
            if not project_id:
                return False
            
            domain_data = {
                'name': self.custom_domain
            }
            
            url = f'{self.api_base}/v9/projects/{project_id}/domains'
            if self.team_id:
                url += f'?teamId={self.team_id}'
            
            response = requests.post(
                url,
                headers=self.headers,
                json=domain_data
            )
            
            if response.status_code == 200:
                self.log(f"自定义域名 {self.custom_domain} 设置成功")
                return True
            else:
                self.log(f"自定义域名设置失败: {response.status_code} - {response.text}", 'warning')
                return False
                
        except Exception as e:
            self.log(f"自定义域名设置失败: {e}", 'warning')
            return False

    def get_or_create_project(self) -> Optional[str]:
        """获取或创建项目"""
        try:
            # 查找现有项目
            url = f'{self.api_base}/v9/projects'
            if self.team_id:
                url += f'?teamId={self.team_id}'
            
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                projects = response.json()['projects']
                for project in projects:
                    if project['name'] == self.project_name:
                        return project['id']
            
            # 创建新项目
            project_data = {
                'name': self.project_name,
                'framework': None
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=project_data
            )
            
            if response.status_code == 200:
                return response.json()['id']
            
            return None
            
        except Exception as e:
            self.log(f"获取或创建项目失败: {e}", 'error')
            return None

    def get_supported_features(self) -> List[str]:
        """获取Vercel支持的功能"""
        return [
            'static_hosting',
            'custom_domain',
            'https',
            'cdn',
            'serverless_functions',
            'edge_functions',
            'analytics',
            'preview_deployments',
            'git_integration',
            'automatic_https'
        ]