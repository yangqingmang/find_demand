#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
趋势数据缓存机制
基于现有 RootWordTrendsAnalyzer 的数据存储策略，扩展支持任意关键词的缓存
"""

import os
import json
import pickle
import hashlib
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import logging

from src.utils.logger import setup_logger
from src.utils.file_utils import ensure_directory_exists


class TrendsCache:
    """趋势数据缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/trends_cache", 
                 cache_duration_hours: int = 24,
                 max_cache_size_mb: int = 500):
        """
        初始化缓存管理器
        
        Args:
            cache_dir: 缓存目录
            cache_duration_hours: 缓存有效期（小时）
            max_cache_size_mb: 最大缓存大小（MB）
        """
        self.cache_dir = cache_dir
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # 转换为字节
        
        ensure_directory_exists(self.cache_dir)
        self.logger = setup_logger(__name__)
        
        # 初始化SQLite数据库用于缓存索引
        self.db_path = os.path.join(self.cache_dir, "cache_index.db")
        self._init_database()
        
        # 缓存配置
        self.config = {
            'cache_formats': ['json', 'pickle', 'csv'],
            'compression_enabled': True,
            'auto_cleanup': True,
            'offline_mode_enabled': True,
            'backup_enabled': True
        }
        
        self.logger.info(f"趋势缓存初始化完成，缓存目录: {self.cache_dir}")
    
    def _init_database(self):
        """初始化缓存索引数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建缓存索引表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache_index (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        cache_key TEXT UNIQUE NOT NULL,
                        keyword TEXT NOT NULL,
                        timeframe TEXT,
                        data_type TEXT,
                        file_path TEXT NOT NULL,
                        file_size INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        access_count INTEGER DEFAULT 0,
                        data_quality_score REAL DEFAULT 0.0,
                        is_offline_available BOOLEAN DEFAULT 1
                    )
                ''')
                
                # 创建缓存统计表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cache_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT UNIQUE NOT NULL,
                        total_requests INTEGER DEFAULT 0,
                        cache_hits INTEGER DEFAULT 0,
                        cache_misses INTEGER DEFAULT 0,
                        cache_size_mb REAL DEFAULT 0.0,
                        cleanup_count INTEGER DEFAULT 0
                    )
                ''')
                
                # 创建索引
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cache_key ON cache_index(cache_key)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_keyword ON cache_index(keyword)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_index(expires_at)')
                
                conn.commit()
                self.logger.info("缓存数据库初始化完成")
                
        except Exception as e:
            self.logger.error(f"初始化缓存数据库失败: {e}")
    
    def _generate_cache_key(self, keyword: str, timeframe: str = None, 
                          data_type: str = "trends") -> str:
        """
        生成缓存键
        
        Args:
            keyword: 关键词
            timeframe: 时间范围
            data_type: 数据类型
            
        Returns:
            缓存键
        """
        key_components = [keyword.lower().strip(), timeframe or "default", data_type]
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode('utf-8')).hexdigest()
    
    def get(self, keyword: str, timeframe: str = None, 
            data_type: str = "trends") -> Optional[Dict[str, Any]]:
        """
        从缓存获取数据
        
        Args:
            keyword: 关键词
            timeframe: 时间范围
            data_type: 数据类型
            
        Returns:
            缓存的数据，如果不存在或过期则返回None
        """
        cache_key = self._generate_cache_key(keyword, timeframe, data_type)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查询缓存记录
                cursor.execute('''
                    SELECT file_path, expires_at, data_quality_score, access_count
                    FROM cache_index 
                    WHERE cache_key = ? AND (expires_at > ? OR expires_at IS NULL)
                ''', (cache_key, datetime.now().isoformat()))
                
                result = cursor.fetchone()
                
                if result:
                    file_path, expires_at, quality_score, access_count = result
                    
                    # 检查文件是否存在
                    if os.path.exists(file_path):
                        # 加载缓存数据
                        cached_data = self._load_cache_file(file_path)
                        
                        if cached_data:
                            # 更新访问统计
                            cursor.execute('''
                                UPDATE cache_index 
                                SET last_accessed = ?, access_count = access_count + 1
                                WHERE cache_key = ?
                            ''', (datetime.now().isoformat(), cache_key))
                            
                            # 更新缓存统计
                            self._update_cache_stats('hit')
                            
                            self.logger.debug(f"缓存命中: {keyword}")
                            return {
                                'data': cached_data,
                                'cached_at': expires_at,
                                'quality_score': quality_score,
                                'access_count': access_count + 1,
                                'source': 'cache'
                            }
                    else:
                        # 文件不存在，清理数据库记录
                        cursor.execute('DELETE FROM cache_index WHERE cache_key = ?', (cache_key,))
                
                # 缓存未命中
                self._update_cache_stats('miss')
                self.logger.debug(f"缓存未命中: {keyword}")
                return None
                
        except Exception as e:
            self.logger.error(f"获取缓存数据失败: {e}")
            return None
    
    def set(self, keyword: str, data: Dict[str, Any], timeframe: str = None,
            data_type: str = "trends", quality_score: float = 0.0) -> bool:
        """
        设置缓存数据
        
        Args:
            keyword: 关键词
            data: 要缓存的数据
            timeframe: 时间范围
            data_type: 数据类型
            quality_score: 数据质量评分
            
        Returns:
            是否成功设置缓存
        """
        cache_key = self._generate_cache_key(keyword, timeframe, data_type)
        
        try:
            # 生成文件路径
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{cache_key}_{timestamp}.json"
            file_path = os.path.join(self.cache_dir, filename)
            
            # 保存数据到文件
            if self._save_cache_file(file_path, data):
                file_size = os.path.getsize(file_path)
                expires_at = datetime.now() + self.cache_duration
                
                # 更新数据库索引
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # 删除旧的缓存记录
                    cursor.execute('DELETE FROM cache_index WHERE cache_key = ?', (cache_key,))
                    
                    # 插入新的缓存记录
                    cursor.execute('''
                        INSERT INTO cache_index 
                        (cache_key, keyword, timeframe, data_type, file_path, file_size,
                         expires_at, data_quality_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (cache_key, keyword, timeframe, data_type, file_path, 
                          file_size, expires_at.isoformat(), quality_score))
                    
                    conn.commit()
                
                self.logger.debug(f"缓存数据已保存: {keyword}")
                
                # 检查缓存大小并清理
                self._cleanup_if_needed()
                
                return True
            
        except Exception as e:
            self.logger.error(f"设置缓存数据失败: {e}")
            
        return False
    
    def _save_cache_file(self, file_path: str, data: Dict[str, Any]) -> bool:
        """保存缓存文件"""
        try:
            # 添加缓存元数据
            cache_data = {
                'cached_at': datetime.now().isoformat(),
                'cache_version': '1.0',
                'data': data
            }
            
            # 保存为JSON格式
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存缓存文件失败: {e}")
            return False
    
    def _load_cache_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """加载缓存文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                return cache_data.get('data')
                
        except Exception as e:
            self.logger.error(f"加载缓存文件失败: {e}")
            return None
    
    def _update_cache_stats(self, operation: str):
        """更新缓存统计"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取今日统计
                cursor.execute('SELECT * FROM cache_stats WHERE date = ?', (today,))
                result = cursor.fetchone()
                
                if result:
                    # 更新统计
                    if operation == 'hit':
                        cursor.execute('''
                            UPDATE cache_stats 
                            SET total_requests = total_requests + 1,
                                cache_hits = cache_hits + 1
                            WHERE date = ?
                        ''', (today,))
                    elif operation == 'miss':
                        cursor.execute('''
                            UPDATE cache_stats 
                            SET total_requests = total_requests + 1,
                                cache_misses = cache_misses + 1
                            WHERE date = ?
                        ''', (today,))
                else:
                    # 创建新的统计记录
                    hits = 1 if operation == 'hit' else 0
                    misses = 1 if operation == 'miss' else 0
                    cursor.execute('''
                        INSERT INTO cache_stats (date, total_requests, cache_hits, cache_misses)
                        VALUES (?, ?, ?, ?)
                    ''', (today, 1, hits, misses))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"更新缓存统计失败: {e}")
    
    def _cleanup_if_needed(self):
        """根据需要清理缓存"""
        try:
            # 检查缓存大小
            total_size = self._get_cache_size()
            
            if total_size > self.max_cache_size:
                self.logger.info(f"缓存大小超限 ({total_size / 1024 / 1024:.1f}MB)，开始清理...")
                self._cleanup_expired_cache()
                self._cleanup_least_used_cache()
        
        except Exception as e:
            self.logger.error(f"缓存清理失败: {e}")
    
    def _get_cache_size(self) -> int:
        """获取缓存总大小"""
        total_size = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT SUM(file_size) FROM cache_index')
                result = cursor.fetchone()
                if result and result[0]:
                    total_size = result[0]
        except Exception as e:
            self.logger.error(f"获取缓存大小失败: {e}")
        
        return total_size
    
    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查找过期的缓存
                cursor.execute('''
                    SELECT file_path FROM cache_index 
                    WHERE expires_at < ?
                ''', (datetime.now().isoformat(),))
                
                expired_files = cursor.fetchall()
                
                # 删除过期文件
                for (file_path,) in expired_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # 删除数据库记录
                cursor.execute('DELETE FROM cache_index WHERE expires_at < ?', 
                             (datetime.now().isoformat(),))
                
                conn.commit()
                
                if expired_files:
                    self.logger.info(f"清理了 {len(expired_files)} 个过期缓存文件")
                    
        except Exception as e:
            self.logger.error(f"清理过期缓存失败: {e}")
    
    def _cleanup_least_used_cache(self, cleanup_count: int = 10):
        """清理最少使用的缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 查找最少使用的缓存
                cursor.execute('''
                    SELECT file_path FROM cache_index 
                    ORDER BY access_count ASC, last_accessed ASC
                    LIMIT ?
                ''', (cleanup_count,))
                
                least_used_files = cursor.fetchall()
                
                # 删除文件
                for (file_path,) in least_used_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # 删除数据库记录
                if least_used_files:
                    file_paths = [f[0] for f in least_used_files]
                    placeholders = ','.join(['?' for _ in file_paths])
                    cursor.execute(f'DELETE FROM cache_index WHERE file_path IN ({placeholders})', 
                                 file_paths)
                
                conn.commit()
                
                if least_used_files:
                    self.logger.info(f"清理了 {len(least_used_files)} 个最少使用的缓存文件")
                    
        except Exception as e:
            self.logger.error(f"清理最少使用缓存失败: {e}")
    
    def clear_all(self) -> bool:
        """清空所有缓存"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取所有缓存文件
                cursor.execute('SELECT file_path FROM cache_index')
                all_files = cursor.fetchall()
                
                # 删除所有文件
                for (file_path,) in all_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                
                # 清空数据库
                cursor.execute('DELETE FROM cache_index')
                cursor.execute('DELETE FROM cache_stats')
                
                conn.commit()
                
            self.logger.info(f"已清空所有缓存 ({len(all_files)} 个文件)")
            return True
            
        except Exception as e:
            self.logger.error(f"清空缓存失败: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 基本统计
                cursor.execute('SELECT COUNT(*), SUM(file_size) FROM cache_index')
                count_result = cursor.fetchone()
                total_files = count_result[0] if count_result else 0
                total_size = count_result[1] if count_result and count_result[1] else 0
                
                # 今日统计
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute('SELECT * FROM cache_stats WHERE date = ?', (today,))
                today_stats = cursor.fetchone()
                
                # 热门关键词
                cursor.execute('''
                    SELECT keyword, access_count FROM cache_index 
                    ORDER BY access_count DESC LIMIT 10
                ''')
                popular_keywords = cursor.fetchall()
                
                return {
                    'total_files': total_files,
                    'total_size_mb': round(total_size / 1024 / 1024, 2),
                    'cache_dir': self.cache_dir,
                    'today_stats': {
                        'requests': today_stats[2] if today_stats else 0,
                        'hits': today_stats[3] if today_stats else 0,
                        'misses': today_stats[4] if today_stats else 0,
                        'hit_rate': round(today_stats[3] / today_stats[2] * 100, 1) 
                                   if today_stats and today_stats[2] > 0 else 0
                    },
                    'popular_keywords': [
                        {'keyword': kw, 'access_count': count} 
                        for kw, count in popular_keywords
                    ],
                    'config': self.config
                }
                
        except Exception as e:
            self.logger.error(f"获取缓存统计失败: {e}")
            return {}
    
    def enable_offline_mode(self, keywords: List[str]) -> Dict[str, Any]:
        """
        启用离线模式，预加载指定关键词的缓存
        
        Args:
            keywords: 要预加载的关键词列表
            
        Returns:
            预加载结果
        """
        self.logger.info(f"启用离线模式，预加载 {len(keywords)} 个关键词")
        
        results = {
            'total_keywords': len(keywords),
            'cached_keywords': [],
            'missing_keywords': [],
            'offline_ready': False
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for keyword in keywords:
                    # 检查是否已缓存
                    cache_key = self._generate_cache_key(keyword)
                    cursor.execute('''
                        SELECT keyword, file_path FROM cache_index 
                        WHERE cache_key = ? AND (expires_at > ? OR expires_at IS NULL)
                    ''', (cache_key, datetime.now().isoformat()))
                    
                    result = cursor.fetchone()
                    
                    if result and os.path.exists(result[1]):
                        results['cached_keywords'].append(keyword)
                    else:
                        results['missing_keywords'].append(keyword)
                
                # 标记为离线可用
                cursor.execute('''
                    UPDATE cache_index 
                    SET is_offline_available = 1 
                    WHERE keyword IN ({})
                '''.format(','.join(['?' for _ in results['cached_keywords']])), 
                          results['cached_keywords'])
                
                conn.commit()
                
                results['offline_ready'] = len(results['missing_keywords']) == 0
                
                self.logger.info(f"离线模式准备完成，可用: {len(results['cached_keywords'])}, "
                               f"缺失: {len(results['missing_keywords'])}")
                
        except Exception as e:
            self.logger.error(f"启用离线模式失败: {e}")
        
        return results
    
    def export_cache_backup(self, backup_path: str = None) -> str:
        """
        导出缓存备份
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            备份文件路径
        """
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.cache_dir, f"cache_backup_{timestamp}.json")
        
        try:
            backup_data = {
                'backup_time': datetime.now().isoformat(),
                'cache_stats': self.get_cache_stats(),
                'cache_index': []
            }
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM cache_index')
                
                columns = [description[0] for description in cursor.description]
                for row in cursor.fetchall():
                    backup_data['cache_index'].append(dict(zip(columns, row)))
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"缓存备份已导出: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"导出缓存备份失败: {e}")
            return ""