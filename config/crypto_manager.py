#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加密管理器
支持混合加密（RSA + AES）和混合密钥管理
"""

import os
import json
import base64
import getpass
import hashlib
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend


class ConfigCrypto:
    """配置加密管理器"""
    
    def __init__(self, key_sources: list = None):
        """
        初始化加密管理器
        
        Args:
            key_sources: 密钥获取优先级列表，默认为 ['file', 'env', 'prompt']
        """
        self.key_sources = key_sources or ['file', 'env', 'prompt']
        self.private_key = None
        self.public_key = None
        
        # 密钥文件路径
        self.private_key_path = os.path.join(os.path.dirname(__file__), 'private.key')
        self.public_key_path = os.path.join(os.path.dirname(__file__), 'public.key')
    
    def generate_key_pair(self) -> tuple:
        """
        生成 RSA 密钥对
        
        Returns:
            tuple: (private_key, public_key)
        """
        print("正在生成 RSA 密钥对...")
        
        # 生成私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # 获取公钥
        public_key = private_key.public_key()
        
        # 序列化私钥
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        # 序列化公钥
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # 保存到文件
        with open(self.private_key_path, 'wb') as f:
            f.write(private_pem)
        
        with open(self.public_key_path, 'wb') as f:
            f.write(public_pem)
        
        print(f"✓ 私钥已保存到: {self.private_key_path}")
        print(f"✓ 公钥已保存到: {self.public_key_path}")
        print("⚠️  请确保私钥文件安全，不要提交到版本控制系统")
        
        return private_key, public_key
    
    def load_private_key(self) -> Optional[rsa.RSAPrivateKey]:
        """
        按优先级加载私钥
        
        Returns:
            RSAPrivateKey: 私钥对象，如果加载失败返回 None
        """
        for source in self.key_sources:
            try:
                if source == 'file':
                    key = self._load_key_from_file()
                elif source == 'env':
                    key = self._load_key_from_env()
                elif source == 'prompt':
                    key = self._load_key_from_prompt()
                else:
                    continue
                
                if key:
                    print(f"✓ 从 {source} 成功加载私钥")
                    return key
                    
            except Exception as e:
                print(f"⚠️  从 {source} 加载私钥失败: {e}")
                continue
        
        print("❌ 无法从任何来源加载私钥")
        return None
    
    def _load_key_from_file(self) -> Optional[rsa.RSAPrivateKey]:
        """从文件加载私钥"""
        if not os.path.exists(self.private_key_path):
            return None
        
        with open(self.private_key_path, 'rb') as f:
            private_key = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        return private_key
    
    def _load_key_from_env(self) -> Optional[rsa.RSAPrivateKey]:
        """从环境变量加载私钥"""
        key_data = os.getenv('RSA_PRIVATE_KEY')
        if not key_data:
            return None
        
        # 处理环境变量中的换行符
        key_data = key_data.replace('\\n', '\n')
        
        private_key = serialization.load_pem_private_key(
            key_data.encode(),
            password=None,
            backend=default_backend()
        )
        return private_key
    
    def _load_key_from_prompt(self) -> Optional[rsa.RSAPrivateKey]:
        """通过交互式输入加载私钥"""
        print("请输入 RSA 私钥内容（以 -----END PRIVATE KEY----- 结束）:")
        key_lines = []
        while True:
            line = getpass.getpass("") if not key_lines else input()
            key_lines.append(line)
            if "-----END PRIVATE KEY-----" in line:
                break
        
        key_data = '\n'.join(key_lines)
        private_key = serialization.load_pem_private_key(
            key_data.encode(),
            password=None,
            backend=default_backend()
        )
        return private_key
    
    def load_public_key(self) -> Optional[rsa.RSAPublicKey]:
        """加载公钥"""
        if not os.path.exists(self.public_key_path):
            return None
        
        with open(self.public_key_path, 'rb') as f:
            public_key = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )
        return public_key
    
    def encrypt_config(self, config_data: Dict[str, Any]) -> str:
        """
        加密配置数据（生成 .env 格式的字符串）
        
        Args:
            config_data: 配置字典
            
        Returns:
            str: .env 格式的加密配置字符串
        """
        if not self.public_key:
            self.public_key = self.load_public_key()
            if not self.public_key:
                raise ValueError("无法加载公钥，请先生成密钥对")
        
        # 1. 生成随机 AES 密钥
        aes_key = os.urandom(32)  # 256位密钥
        
        # 2. 使用固定 IV（基于项目特征生成，保持一致性）
        project_seed = "find_demand_config_encryption_2024"
        iv = hashlib.sha256(project_seed.encode()).digest()[:16]
        
        # 3. 用 RSA 加密 AES 密钥
        encrypted_aes_key = self.public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 4. 生成 .env 格式的加密配置
        lines = []
        lines.append("# 加密配置文件（敏感信息）")
        lines.append("# 此文件可以安全提交到版本控制系统")
        lines.append("# 配置值已加密，需要私钥才能解密")
        lines.append("")
        
        # 添加加密元数据
        encrypted_key_b64 = base64.b64encode(encrypted_aes_key).decode('utf-8')
        lines.append(f"_ENCRYPTED_KEY={encrypted_key_b64}")
        lines.append("")
        
        # 加密每个配置值
        for key, value in config_data.items():
            if value:  # 只加密非空值
                # 为每个值创建 AES 加密器
                cipher = Cipher(
                    algorithms.AES(aes_key),
                    modes.CBC(iv),
                    backend=default_backend()
                )
                encryptor = cipher.encryptor()
                
                # 填充并加密值
                padded_value = self._pad_data(str(value).encode('utf-8'))
                encrypted_value = encryptor.update(padded_value) + encryptor.finalize()
                
                # 存储加密后的值
                encrypted_value_b64 = base64.b64encode(encrypted_value).decode('utf-8')
                lines.append(f"{key}={encrypted_value_b64}")
            else:
                # 空值保持原样
                lines.append(f"{key}={value}")
        
        return '\n'.join(lines)
    
    def decrypt_config(self, encrypted_data) -> Dict[str, Any]:
        """
        解密配置数据（支持字典和字符串格式）
        
        Args:
            encrypted_data: 加密数据（字典或字符串）
            
        Returns:
            dict: 解密后的配置字典
        """
        if not self.private_key:
            self.private_key = self.load_private_key()
            if not self.private_key:
                raise ValueError("无法加载私钥")
        
        # 如果是字符串，先解析为字典
        if isinstance(encrypted_data, str):
            config_dict = {}
            for line in encrypted_data.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config_dict[key.strip()] = value.strip()
            encrypted_data = config_dict
        
        # 1. 获取加密的 AES 密钥
        encrypted_key_field = None
        if '_ENCRYPTED_KEY' in encrypted_data:
            encrypted_key_field = '_ENCRYPTED_KEY'
        elif '_encrypted_key' in encrypted_data:
            encrypted_key_field = '_encrypted_key'
        elif 'encrypted_key' in encrypted_data:
            # 兼容旧 JSON 格式
            encrypted_aes_key = base64.b64decode(encrypted_data['encrypted_key'])
            iv = base64.b64decode(encrypted_data['iv'])
            encrypted_config = base64.b64decode(encrypted_data['encrypted_config'])
            
            # 使用旧的解密方式
            aes_key = self.private_key.decrypt(
                encrypted_aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            cipher = Cipher(
                algorithms.AES(aes_key),
                modes.CBC(iv),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            
            padded_config = decryptor.update(encrypted_config) + decryptor.finalize()
            config_json = self._unpad_data(padded_config).decode('utf-8')
            
            return json.loads(config_json)
        else:
            raise ValueError("无效的加密数据格式")
        
        # 2. 解密 AES 密钥
        encrypted_aes_key = base64.b64decode(encrypted_data[encrypted_key_field])
        aes_key = self.private_key.decrypt(
            encrypted_aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        # 3. 使用固定 IV
        project_seed = "find_demand_config_encryption_2024"
        iv = hashlib.sha256(project_seed.encode()).digest()[:16]
        
        # 4. 逐个解密配置值
        decrypted_config = {}
        
        for key, encrypted_value in encrypted_data.items():
            if key in ['_ENCRYPTED_KEY', '_encrypted_key']:
                continue  # 跳过元数据
            
            if encrypted_value and isinstance(encrypted_value, str):
                try:
                    # 解密值
                    cipher = Cipher(
                        algorithms.AES(aes_key),
                        modes.CBC(iv),
                        backend=default_backend()
                    )
                    decryptor = cipher.decryptor()
                    
                    encrypted_bytes = base64.b64decode(encrypted_value)
                    padded_value = decryptor.update(encrypted_bytes) + decryptor.finalize()
                    decrypted_value = self._unpad_data(padded_value).decode('utf-8')
                    
                    decrypted_config[key] = decrypted_value
                except:
                    # 如果解密失败，可能是明文值
                    decrypted_config[key] = encrypted_value
            else:
                # 空值或非字符串值保持原样
                decrypted_config[key] = encrypted_value
        
        return decrypted_config
    
    def _pad_data(self, data: bytes) -> bytes:
        """PKCS7 填充"""
        pad_len = 16 - (len(data) % 16)
        return data + bytes([pad_len] * pad_len)
    
    def _unpad_data(self, data: bytes) -> bytes:
        """移除 PKCS7 填充"""
        pad_len = data[-1]
        return data[:-pad_len]


def init_crypto_system():
    """初始化加密系统"""
    crypto = ConfigCrypto()
    
    # 检查是否已有密钥对
    if not os.path.exists(crypto.public_key_path) or not os.path.exists(crypto.private_key_path):
        print("未找到密钥对，正在生成新的密钥对...")
        crypto.generate_key_pair()
    else:
        print("✓ 找到现有密钥对")
    
    return crypto


if __name__ == "__main__":
    # 测试加密系统
    crypto = init_crypto_system()
    
    # 测试配置
    test_config = {
        "GOOGLE_API_KEY": "AIzaSyDc3-Si7-2kIQg8Qf9iJ47KB7jKOE13CCQ",
        "GOOGLE_CSE_ID": "46d7e713108284af4",
        "SECRET_TOKEN": "very_secret_token_123"
    }
    
    print("\n=== 测试加密 ===")
    encrypted = crypto.encrypt_config(test_config)
    print("✓ 配置加密成功")
    
    print("\n=== 测试解密 ===")
    decrypted = crypto.decrypt_config(encrypted)
    print("✓ 配置解密成功")
    
    print(f"原始配置匹配: {test_config == decrypted}")