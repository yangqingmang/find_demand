#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vercel 部署器 - 使用 Vercel CLI
"""

import os
import json
import subprocess
import time
from typing import Dict, List, Optional, Any, Tuple
from base_deployer import BaseDeployer


class VercelDeployer(BaseDeployer):
    """Vercel 部署器 - 基于 CLI"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化Vercel部署器
        
        Args:
            config: 部署配置，包含：
                - api_token: Vercel API Token
                - team_id: 团队ID（可选）
                - project_name: 项目名称
                - custom_domain: 自定义域名（可选）
                - org_id: 组织ID（可选，用于团队部署）
        """
        super().__init__(config)
        self.api_token = self.config.get('api_token')
        self.team_id = self.config.get('team_id')
        self.org_id = self.config.get('org_id')
        self.project_name = self.config.get('project_name')
        self.custom_domain = self.config.get('custom_domain')
        
        # CLI 相关属性
        self.vercel_cli_path = self._find_vercel_cli()

    def _find_vercel_cli(self) -> Optional[str]:
        """查找 Vercel CLI"""
        # 常见的 CLI 路径
        possible_paths = [
            'vercel',
            'npx vercel',
            os.path.join(os.path.expanduser('~'), '.npm-global', 'bin', 'vercel'),
            os.path.join(os.path.expanduser('~'), 'node_modules', '.bin', 'vercel')
        ]
        
        for path in possible_paths:
            try:
                result = subprocess.run(
                    f'{path} --version',
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self.log(f"找到 Vercel CLI: {path}")
                    return path
            except Exception:
                continue
        
        return None

    def _install_vercel_cli(self) -> bool:
        """安装 Vercel CLI"""
        try:
            self.log("正在安装 Vercel CLI...")
            
            # 尝试使用 npm 安装
            result = subprocess.run(
                'npm install -g vercel',
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                self.log("Vercel CLI 安装成功")
                self.vercel_cli_path = 'vercel'
                return True
            else:
                self.log(f"npm 安装失败: {result.stderr}", 'warning')
                
                # 尝试使用 npx
                self.log("尝试使用 npx vercel...")
                self.vercel_cli_path = 'npx vercel'
                return True
                
        except Exception as e:
            self.log(f"安装 Vercel CLI 失败: {e}", 'error')
            return False

    def validate_config(self) -> Tuple[bool, str]:
        """验证Vercel配置"""
        # 检查 Vercel CLI
        if not self.vercel_cli_path:
            self.log("未找到 Vercel CLI，尝试安装...")
            if not self._install_vercel_cli():
                return False, "无法安装或找到 Vercel CLI"
        
        if not self.project_name:
            return False, "缺少项目名称"
        
        # 验证项目名称格式
        if not self.project_name.replace('-', '').replace('_', '').isalnum():
            return False, "项目名称只能包含字母、数字、连字符和下划线"
        
        # 测试 CLI 连接
        try:
            # 设置环境变量
            env = os.environ.copy()
            if self.api_token:
                env['VERCEL_TOKEN'] = self.api_token
            if self.org_id:
                env['VERCEL_ORG_ID'] = self.org_id
            elif self.team_id:
                env['VERCEL_ORG_ID'] = self.team_id
            
            # 测试 CLI 是否工作
            result = subprocess.run(
                f'{self.vercel_cli_path} --version',
                shell=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=10
            )
            
            if result.returncode != 0:
                return False, f"Vercel CLI 测试失败: {result.stderr}"
            
            self.log(f"Vercel CLI 验证成功: {result.stdout.strip()}")
            return True, ""
            
        except Exception as e:
            return False, f"CLI 连接测试失败: {e}"

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
                '.vercel',
                '__pycache__',
                '*.pyc'
            ]
            
            if not self.copy_files(source_dir, temp_dir, exclude_patterns):
                return False
            
            # 生成现代化的 vercel.json 配置文件
            vercel_config = {
                "cleanUrls": True,
                "trailingSlash": False,
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
                            },
                            {
                                "key": "Referrer-Policy",
                                "value": "strict-origin-when-cross-origin"
                            }
                        ]
                    },
                    {
                        "source": "/css/(.*)",
                        "headers": [
                            {
                                "key": "Cache-Control",
                                "value": "public, max-age=31536000, immutable"
                            }
                        ]
                    },
                    {
                        "source": "/js/(.*)",
                        "headers": [
                            {
                                "key": "Cache-Control",
                                "value": "public, max-age=31536000, immutable"
                            }
                        ]
                    },
                    {
                        "source": "/images/(.*)",
                        "headers": [
                            {
                                "key": "Cache-Control",
                                "value": "public, max-age=31536000, immutable"
                            }
                        ]
                    }
                ]
            }
            
            # 如果有自定义域名，添加域名配置
            if self.custom_domain:
                vercel_config["domains"] = [self.custom_domain]
            
            vercel_config_path = os.path.join(temp_dir, 'vercel.json')
            with open(vercel_config_path, 'w', encoding='utf-8') as f:
                json.dump(vercel_config, f, indent=2, ensure_ascii=False)
            
            # 创建 .vercelignore 文件
            vercelignore_content = """
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production
/build
/dist

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
""".strip()
            
            vercelignore_path = os.path.join(temp_dir, '.vercelignore')
            with open(vercelignore_path, 'w', encoding='utf-8') as f:
                f.write(vercelignore_content)
            
            self.log("Vercel文件准备完成")
            return True
            
        except Exception as e:
            self.log(f"文件准备失败: {e}", 'error')
            return False

    def deploy(self, temp_dir: str) -> Tuple[bool, str]:
        """执行Vercel部署"""
        try:
            self.log("开始 Vercel CLI 部署")
            
            # 准备环境变量
            env = os.environ.copy()
            if self.api_token:
                env['VERCEL_TOKEN'] = self.api_token
            if self.org_id:
                env['VERCEL_ORG_ID'] = self.org_id
            elif self.team_id:
                env['VERCEL_ORG_ID'] = self.team_id
            
            # 构建部署命令
            deploy_cmd = f'{self.vercel_cli_path} --prod --yes'
            
            # 添加项目名称
            if self.project_name:
                deploy_cmd += f' --name {self.project_name}'
            
            # 添加组织/团队参数
            if self.org_id:
                deploy_cmd += f' --scope {self.org_id}'
            elif self.team_id:
                deploy_cmd += f' --scope {self.team_id}'
            
            self.log(f"执行部署命令: {deploy_cmd}")
            
            # 执行部署
            result = subprocess.run(
                deploy_cmd,
                shell=True,
                cwd=temp_dir,
                capture_output=True,
                text=True,
                env=env,
                timeout=600  # 10分钟超时
            )
            
            if result.returncode == 0:
                # 从输出中提取部署URL
                output_lines = result.stdout.strip().split('\n')
                deployment_url = None
                
                for line in output_lines:
                    line = line.strip()
                    if line.startswith('https://') and ('vercel.app' in line or self.custom_domain in line):
                        deployment_url = line
                        break
                
                if not deployment_url:
                    # 尝试从最后几行找到URL
                    for line in reversed(output_lines):
                        line = line.strip()
                        if line.startswith('https://'):
                            deployment_url = line
                            break
                
                if deployment_url:
                    self.deployment_url = deployment_url
                    self.deployment_status = 'success'
                    self.log(f"部署成功！访问地址: {deployment_url}")
                    
                    # 设置自定义域名
                    if self.custom_domain and self.custom_domain not in deployment_url:
                        self.setup_custom_domain()
                    
                    return True, deployment_url
                else:
                    self.log("部署成功但无法提取URL", 'warning')
                    self.log(f"完整输出: {result.stdout}")
                    return True, "部署成功，请检查 Vercel 控制台获取URL"
            else:
                self.deployment_status = 'failed'
                error_msg = result.stderr or result.stdout
                self.log(f"部署失败: {error_msg}", 'error')
                
                # 尝试提供更友好的错误信息
                if "VERCEL_TOKEN" in error_msg:
                    return False, "Vercel Token 无效或未设置"
                elif "not found" in error_msg.lower():
                    return False, "Vercel CLI 未找到，请确保已正确安装"
                elif "permission" in error_msg.lower():
                    return False, "权限不足，请检查 Token 权限"
                else:
                    return False, f"部署失败: {error_msg}"
                    
        except subprocess.TimeoutExpired:
            self.log("部署超时", 'error')
            return False, "部署超时，请稍后重试"
        except Exception as e:
            self.log(f"部署过程中发生错误: {e}", 'error')
            return False, str(e)

    def get_deployment_status(self) -> Dict[str, Any]:
        """获取部署状态"""
        try:
            if not self.deployment_url:
                return {'status': 'unknown', 'message': '未找到部署URL'}
            
            # 使用 CLI 获取部署列表
            env = os.environ.copy()
            if self.api_token:
                env['VERCEL_TOKEN'] = self.api_token
            if self.org_id:
                env['VERCEL_ORG_ID'] = self.org_id
            elif self.team_id:
                env['VERCEL_ORG_ID'] = self.team_id
            
            cmd = f'{self.vercel_cli_path} ls --json'
            if self.org_id:
                cmd += f' --scope {self.org_id}'
            elif self.team_id:
                cmd += f' --scope {self.team_id}'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    deployments = json.loads(result.stdout)
                    for deployment in deployments:
                        if deployment.get('name') == self.project_name:
                            return {
                                'status': deployment.get('state', 'unknown'),
                                'message': deployment.get('name', ''),
                                'url': f"https://{deployment.get('url', '')}",
                                'created_at': deployment.get('createdAt', ''),
                                'ready_at': deployment.get('readyAt', '')
                            }
                except json.JSONDecodeError:
                    pass
            
            # 如果无法获取详细状态，返回基本信息
            return {
                'status': self.deployment_status,
                'message': self.project_name,
                'url': self.deployment_url,
                'created_at': '',
                'ready_at': ''
            }
                
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def setup_custom_domain(self) -> bool:
        """设置自定义域名"""
        try:
            if not self.custom_domain:
                return True
            
            self.log(f"设置自定义域名: {self.custom_domain}")
            
            # 准备环境变量
            env = os.environ.copy()
            if self.api_token:
                env['VERCEL_TOKEN'] = self.api_token
            if self.org_id:
                env['VERCEL_ORG_ID'] = self.org_id
            elif self.team_id:
                env['VERCEL_ORG_ID'] = self.team_id
            
            # 使用 CLI 添加域名
            cmd = f'{self.vercel_cli_path} domains add {self.custom_domain}'
            if self.project_name:
                cmd += f' {self.project_name}'
            if self.org_id:
                cmd += f' --scope {self.org_id}'
            elif self.team_id:
                cmd += f' --scope {self.team_id}'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log(f"自定义域名 {self.custom_domain} 设置成功")
                return True
            else:
                error_msg = result.stderr or result.stdout
                if "already exists" in error_msg.lower():
                    self.log(f"域名 {self.custom_domain} 已存在", 'info')
                    return True
                else:
                    self.log(f"自定义域名设置失败: {error_msg}", 'warning')
                    return False
                
        except Exception as e:
            self.log(f"自定义域名设置失败: {e}", 'warning')
            return False

    def list_deployments(self) -> List[Dict[str, Any]]:
        """列出所有部署"""
        try:
            env = os.environ.copy()
            if self.api_token:
                env['VERCEL_TOKEN'] = self.api_token
            if self.org_id:
                env['VERCEL_ORG_ID'] = self.org_id
            elif self.team_id:
                env['VERCEL_ORG_ID'] = self.team_id
            
            cmd = f'{self.vercel_cli_path} ls --json'
            if self.org_id:
                cmd += f' --scope {self.org_id}'
            elif self.team_id:
                cmd += f' --scope {self.team_id}'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    self.log("无法解析部署列表JSON", 'warning')
                    return []
            else:
                self.log(f"获取部署列表失败: {result.stderr}", 'error')
                return []
                
        except Exception as e:
            self.log(f"列出部署失败: {e}", 'error')
            return []

    def remove_deployment(self, deployment_url: str) -> bool:
        """删除指定部署"""
        try:
            env = os.environ.copy()
            if self.api_token:
                env['VERCEL_TOKEN'] = self.api_token
            if self.org_id:
                env['VERCEL_ORG_ID'] = self.org_id
            elif self.team_id:
                env['VERCEL_ORG_ID'] = self.team_id
            
            # 从URL中提取部署名称
            deployment_name = deployment_url.replace('https://', '').split('.')[0]
            
            cmd = f'{self.vercel_cli_path} rm {deployment_name} --yes'
            if self.org_id:
                cmd += f' --scope {self.org_id}'
            elif self.team_id:
                cmd += f' --scope {self.team_id}'
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                env=env,
                timeout=60
            )
            
            if result.returncode == 0:
                self.log(f"部署 {deployment_name} 删除成功")
                return True
            else:
                self.log(f"删除部署失败: {result.stderr}", 'error')
                return False
                
        except Exception as e:
            self.log(f"删除部署失败: {e}", 'error')
            return False

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
            'automatic_https',
            'cli_deployment'
        ]
