#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
基础部署器 - 定义部署接口和通用功能
"""

import os
import json
import shutil
import zipfile
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class BaseDeployer(ABC):
    """基础部署器抽象类"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化部署器
        
        Args:
            config: 部署配置
        """
        self.config = config or {}
        self.deployment_id = None
        self.deployment_url = None
        self.deployment_status = 'pending'
        self.deployment_logs = []

    @abstractmethod
    def validate_config(self) -> Tuple[bool, str]:
        """
        验证部署配置
        
        Returns:
            (是否有效, 错误信息)
        """
        pass

    @abstractmethod
    def prepare_files(self, source_dir: str, temp_dir: str) -> bool:
        """
        准备部署文件
        
        Args:
            source_dir: 源文件目录
            temp_dir: 临时目录
            
        Returns:
            是否成功
        """
        pass

    @abstractmethod
    def deploy(self, temp_dir: str) -> Tuple[bool, str]:
        """
        执行部署
        
        Args:
            temp_dir: 临时目录
            
        Returns:
            (是否成功, 部署URL或错误信息)
        """
        pass

    @abstractmethod
    def get_deployment_status(self) -> Dict[str, Any]:
        """
        获取部署状态
        
        Returns:
            部署状态信息
        """
        pass

    def log(self, message: str, level: str = 'info') -> None:
        """
        记录日志
        
        Args:
            message: 日志消息
            level: 日志级别
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.deployment_logs.append(log_entry)
        print(f"[{timestamp}] [{level.upper()}] {message}")

    def create_temp_dir(self) -> str:
        """
        创建临时目录
        
        Returns:
            临时目录路径
        """
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix='deploy_')
        self.log(f"创建临时目录: {temp_dir}")
        return temp_dir

    def cleanup_temp_dir(self, temp_dir: str) -> None:
        """
        清理临时目录
        
        Args:
            temp_dir: 临时目录路径
        """
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                self.log(f"清理临时目录: {temp_dir}")
        except Exception as e:
            self.log(f"清理临时目录失败: {e}", 'error')

    def copy_files(self, source_dir: str, dest_dir: str, exclude_patterns: List[str] = None) -> bool:
        """
        复制文件到目标目录
        
        Args:
            source_dir: 源目录
            dest_dir: 目标目录
            exclude_patterns: 排除的文件模式
            
        Returns:
            是否成功
        """
        try:
            exclude_patterns = exclude_patterns or []
            
            for root, dirs, files in os.walk(source_dir):
                # 计算相对路径
                rel_path = os.path.relpath(root, source_dir)
                dest_root = os.path.join(dest_dir, rel_path) if rel_path != '.' else dest_dir
                
                # 创建目录
                os.makedirs(dest_root, exist_ok=True)
                
                # 复制文件
                for file in files:
                    # 检查是否需要排除
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern in file or pattern in os.path.join(rel_path, file):
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        src_file = os.path.join(root, file)
                        dest_file = os.path.join(dest_root, file)
                        shutil.copy2(src_file, dest_file)
            
            self.log(f"文件复制完成: {source_dir} -> {dest_dir}")
            return True
            
        except Exception as e:
            self.log(f"文件复制失败: {e}", 'error')
            return False

    def create_zip_archive(self, source_dir: str, zip_path: str) -> bool:
        """
        创建ZIP压缩包
        
        Args:
            source_dir: 源目录
            zip_path: ZIP文件路径
            
        Returns:
            是否成功
        """
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arc_name)
            
            self.log(f"ZIP压缩包创建完成: {zip_path}")
            return True
            
        except Exception as e:
            self.log(f"ZIP压缩包创建失败: {e}", 'error')
            return False

    def generate_deployment_config(self, temp_dir: str) -> bool:
        """
        生成部署配置文件
        
        Args:
            temp_dir: 临时目录
            
        Returns:
            是否成功
        """
        try:
            # 子类可以重写此方法来生成特定的配置文件
            return True
        except Exception as e:
            self.log(f"生成部署配置失败: {e}", 'error')
            return False

    def validate_files(self, temp_dir: str) -> Tuple[bool, str]:
        """
        验证部署文件
        
        Args:
            temp_dir: 临时目录
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 检查是否有index.html
            index_path = os.path.join(temp_dir, 'index.html')
            if not os.path.exists(index_path):
                return False, "缺少index.html文件"
            
            # 检查文件大小
            total_size = 0
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
            
            # 限制总大小为100MB
            max_size = 100 * 1024 * 1024  # 100MB
            if total_size > max_size:
                return False, f"文件总大小超过限制: {total_size / 1024 / 1024:.1f}MB > 100MB"
            
            self.log(f"文件验证通过，总大小: {total_size / 1024 / 1024:.1f}MB")
            return True, ""
            
        except Exception as e:
            return False, f"文件验证失败: {e}"

    def get_supported_features(self) -> List[str]:
        """
        获取支持的功能特性
        
        Returns:
            功能特性列表
        """
        return [
            'static_hosting',  # 静态网站托管
            'custom_domain',   # 自定义域名
            'https',          # HTTPS支持
            'cdn',            # CDN加速
        ]

    def get_deployment_info(self) -> Dict[str, Any]:
        """
        获取部署信息
        
        Returns:
            部署信息字典
        """
        return {
            'deployment_id': self.deployment_id,
            'deployment_url': self.deployment_url,
            'deployment_status': self.deployment_status,
            'deployment_logs': self.deployment_logs,
            'supported_features': self.get_supported_features(),
            'config': self.config
        }