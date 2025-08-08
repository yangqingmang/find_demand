#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cloudflare Pages 部署器
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional, Any, Tuple
from .base_deployer import BaseDeployer


class CloudflareDeployer(BaseDeployer):
    """Cloudflare Pages 部署器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化Cloudflare部署器
        
        Args:
            config: 部署配置，包含：
                - api_token: Cloudflare API Token
                - account_id: Cloudflare Account ID
                - project_name: 项目名称
                - custom_domain: 自定义域名（可选）
        """
        super().__init__(config)
        self.api_token = self.config.get('api_token')
        self.account_id = self.config.get('account_id')
        self.project_name = self.config.get('project_name')
        self.custom_domain = self.config.get('custom_domain')
        
        self.api_base = 'https://api.cloudflare.com/client/v4'
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

    def validate_config(self) -> Tuple[bool, str]:
        """验证Cloudflare配置"""
        if not self.api_token:
            return False, "缺少Cloudflare API Token"
        
        if not self.account_id:
            return False, "缺少Cloudflare Account ID"
        
        if not self.project_name:
            return False, "缺少项目名称"
        
        # 验证项目名称格式
        if not self.project_name.replace('-', '').replace('_', '').isalnum():
            return False, "项目名称只能包含字母、数字、连字符和下划线"
        
        # 测试API连接
        try:
            response = requests.get(
                f'{self.api_base}/accounts/{self.account_id}',
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code != 200:
                return False, f"API连接失败: {response.status_code}"
            
            self.log("Cloudflare API连接验证成功")
            return True, ""
            
        except Exception as e:
            return False, f"API连接测试失败: {e}"

    def prepare_files(self, source_dir: str, temp_dir: str) -> bool:
        """准备Cloudflare Pages部署文件"""
        try:
            # 复制所有文件到临时目录
            exclude_patterns = [
                '.git',
                '.gitignore',
                'node_modules',
                '.env',
                '*.log',
                '.DS_Store'
            ]
            
            if not self.copy_files(source_dir, temp_dir, exclude_patterns):
                return False
            
            # 生成_headers文件（用于设置HTTP头）
            headers_content = """/*
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
"""
            
            headers_path = os.path.join(temp_dir, '_headers')
            with open(headers_path, 'w', encoding='utf-8') as f:
                f.write(headers_content)
            
            # 生成_redirects文件（用于SPA路由）
            redirects_content = """# SPA fallback
/*    /index.html   200
"""
            
            redirects_path = os.path.join(temp_dir, '_redirects')
            with open(redirects_path, 'w', encoding='utf-8') as f:
                f.write(redirects_content)
            
            self.log("Cloudflare Pages文件准备完成")
            return True
            
        except Exception as e:
            self.log(f"文件准备失败: {e}", 'error')
            return False

    def create_project(self) -> bool:
        """创建Cloudflare Pages项目"""
        try:
            # 检查项目是否已存在
            response = requests.get(
                f'{self.api_base}/accounts/{self.account_id}/pages/projects/{self.project_name}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                self.log(f"项目 {self.project_name} 已存在")
                return True
            
            # 创建新项目
            project_data = {
                'name': self.project_name,
                'production_branch': 'main',
                'build_config': {
                    'build_command': '',
                    'destination_dir': '',
                    'root_dir': ''
                }
            }
            
            response = requests.post(
                f'{self.api_base}/accounts/{self.account_id}/pages/projects',
                headers=self.headers,
                json=project_data
            )
            
            if response.status_code == 200:
                self.log(f"项目 {self.project_name} 创建成功")
                return True
            else:
                self.log(f"项目创建失败: {response.status_code} - {response.text}", 'error')
                return False
                
        except Exception as e:
            self.log(f"创建项目失败: {e}", 'error')
            return False

    def upload_files(self, temp_dir: str) -> bool:
        """上传文件到Cloudflare Pages"""
        try:
            # 创建ZIP压缩包
            zip_path = os.path.join(os.path.dirname(temp_dir), f'{self.project_name}.zip')
            if not self.create_zip_archive(temp_dir, zip_path):
                return False
            
            # 上传文件
            with open(zip_path, 'rb') as f:
                files = {'file': f}
                headers_without_content_type = {
                    'Authorization': f'Bearer {self.api_token}'
                }
                
                response = requests.post(
                    f'{self.api_base}/accounts/{self.account_id}/pages/projects/{self.project_name}/deployments',
                    headers=headers_without_content_type,
                    files=files
                )
            
            # 清理ZIP文件
            os.remove(zip_path)
            
            if response.status_code == 200:
                deployment_data = response.json()
                self.deployment_id = deployment_data['result']['id']
                self.deployment_url = deployment_data['result']['url']
                self.log(f"文件上传成功，部署ID: {self.deployment_id}")
                return True
            else:
                self.log(f"文件上传失败: {response.status_code} - {response.text}", 'error')
                return False
                
        except Exception as e:
            self.log(f"文件上传失败: {e}", 'error')
            return False

    def deploy(self, temp_dir: str) -> Tuple[bool, str]:
        """执行Cloudflare Pages部署"""
        try:
            self.log("开始Cloudflare Pages部署")
            
            # 创建项目
            if not self.create_project():
                return False, "项目创建失败"
            
            # 上传文件
            if not self.upload_files(temp_dir):
                return False, "文件上传失败"
            
            # 等待部署完成
            self.log("等待部署完成...")
            max_wait_time = 300  # 5分钟
            wait_time = 0
            
            while wait_time < max_wait_time:
                status_info = self.get_deployment_status()
                
                if status_info['status'] == 'success':
                    self.deployment_status = 'success'
                    self.log(f"部署成功！访问地址: {self.deployment_url}")
                    
                    # 设置自定义域名
                    if self.custom_domain:
                        self.setup_custom_domain()
                    
                    return True, self.deployment_url
                
                elif status_info['status'] == 'failure':
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
            
            response = requests.get(
                f'{self.api_base}/accounts/{self.account_id}/pages/projects/{self.project_name}/deployments/{self.deployment_id}',
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()['result']
                return {
                    'status': data['latest_stage']['status'],
                    'message': data['latest_stage'].get('name', ''),
                    'url': data.get('url', ''),
                    'created_on': data.get('created_on', ''),
                    'modified_on': data.get('modified_on', '')
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
            
            domain_data = {
                'name': self.custom_domain
            }
            
            response = requests.post(
                f'{self.api_base}/accounts/{self.account_id}/pages/projects/{self.project_name}/domains',
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

    def get_supported_features(self) -> List[str]:
        """获取Cloudflare Pages支持的功能"""
        return [
            'static_hosting',
            'custom_domain',
            'https',
            'cdn',
            'edge_functions',
            'analytics',
            'preview_deployments',
            'git_integration'
        ]