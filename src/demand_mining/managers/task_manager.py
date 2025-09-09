#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理器 - 负责每日任务自动生成和管理
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, asdict

from .base_manager import BaseManager


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class TaskPriority(Enum):
    """任务优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(Enum):
    """任务类型枚举"""
    KEYWORD_VERIFICATION = "keyword_verification"
    SERP_ANALYSIS = "serp_analysis"
    TRENDS_CHECK = "trends_check"
    COMPETITOR_ANALYSIS = "competitor_analysis"
    DATA_UPDATE = "data_update"
    QUALITY_REVIEW = "quality_review"


@dataclass
class Task:
    """任务数据类"""
    id: str
    keyword: str
    task_type: TaskType
    priority: TaskPriority
    status: TaskStatus
    title: str
    description: str
    estimated_time: int  # 预估时间（分钟）
    created_at: datetime
    due_date: datetime
    completed_at: Optional[datetime] = None
    verification_data: Optional[Dict[str, Any]] = None
    score: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        # 转换枚举为字符串
        data['task_type'] = self.task_type.value
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        # 转换日期为字符串
        data['created_at'] = self.created_at.isoformat()
        data['due_date'] = self.due_date.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        return data


class TaskManager(BaseManager):
    """任务管理器 - 负责每日任务自动生成和管理"""
    
    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        
        # 任务管理配置
        self.task_config = self.config.get('task_management', {
            'daily_task_limit': 20,
            'priority_weights': {
                'trends_score': 0.3,
                'serp_score': 0.4,
                'business_value': 0.3
            },
            'auto_generation_time': '09:00',
            'task_expiry_days': 7
        })
        
        # 初始化数据库
        self.db_path = os.path.join(self.output_dir, 'tasks.db')
        self._init_database()
        
        print("📋 任务管理器初始化完成")
    
    def _init_database(self):
        """初始化任务数据库"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    estimated_time INTEGER,
                    score REAL,
                    tags TEXT,
                    created_at TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    completed_at TEXT,
                    verification_data TEXT
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_status ON tasks(status)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_priority ON tasks(priority)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_due_date ON tasks(due_date)
            ''')
    
    def analyze(self, action: str = 'generate_daily_tasks', **kwargs) -> Dict[str, Any]:
        """主要分析方法 - 实现BaseManager的抽象方法"""
        if action == 'generate_daily_tasks':
            return self.generate_daily_tasks()
        elif action == 'get_tasks':
            return self.get_tasks(**kwargs)
        elif action == 'update_task':
            return self.update_task(**kwargs)
        elif action == 'get_task_stats':
            return self.get_task_statistics()
        else:
            raise ValueError(f"不支持的操作: {action}")
    
    def generate_daily_tasks(self, target_date: datetime = None) -> Dict[str, Any]:
        """生成每日任务"""
        if target_date is None:
            target_date = datetime.now()
        
        print(f"🔄 开始生成 {target_date.strftime('%Y-%m-%d')} 的每日任务...")
        
        # 获取候选关键词（这里模拟数据，实际应从关键词分析结果中获取）
        candidate_keywords = self._get_candidate_keywords()
        
        # 生成任务
        generated_tasks = []
        daily_limit = self.task_config['daily_task_limit']
        
        # 按优先级排序候选关键词
        sorted_keywords = self._prioritize_keywords(candidate_keywords)
        
        # 生成不同类型的任务
        task_count = 0
        for keyword_data in sorted_keywords:
            if task_count >= daily_limit:
                break
            
            # 为每个关键词生成多种类型的任务
            tasks = self._generate_tasks_for_keyword(keyword_data, target_date)
            
            for task in tasks:
                if task_count >= daily_limit:
                    break
                
                # 检查是否已存在相同任务
                if not self._task_exists(task.keyword, task.task_type, target_date):
                    self._save_task(task)
                    generated_tasks.append(task)
                    task_count += 1
        
        # 生成任务报告
        report = self._generate_task_report(generated_tasks, target_date)
        
        print(f"✅ 成功生成 {len(generated_tasks)} 个任务")
        
        return {
            'success': True,
            'generated_count': len(generated_tasks),
            'target_date': target_date.strftime('%Y-%m-%d'),
            'tasks': [task.to_dict() for task in generated_tasks],
            'report': report
        }
    
    def _get_candidate_keywords(self) -> List[Dict[str, Any]]:
        """获取候选关键词（模拟数据）"""
        # 实际实现中应该从关键词分析结果、趋势数据等获取
        return [
            {
                'keyword': 'ai image generator',
                'trends_score': 0.8,
                'serp_score': 0.6,
                'business_value': 0.9,
                'search_volume': 50000,
                'competition': 0.7
            },
            {
                'keyword': 'cat coloring pages',
                'trends_score': 0.7,
                'serp_score': 0.4,
                'business_value': 0.6,
                'search_volume': 30000,
                'competition': 0.3
            },
            {
                'keyword': 'pdf converter',
                'trends_score': 0.6,
                'serp_score': 0.8,
                'business_value': 0.8,
                'search_volume': 80000,
                'competition': 0.9
            },
            {
                'keyword': 'weather forecast',
                'trends_score': 0.9,
                'serp_score': 0.9,
                'business_value': 0.5,
                'search_volume': 100000,
                'competition': 0.95
            },
            {
                'keyword': 'online calculator',
                'trends_score': 0.5,
                'serp_score': 0.3,
                'business_value': 0.7,
                'search_volume': 25000,
                'competition': 0.4
            }
        ]
    
    def _prioritize_keywords(self, keywords: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于多维度评分对关键词进行优先级排序"""
        weights = self.task_config['priority_weights']
        
        for keyword_data in keywords:
            # 计算综合评分
            score = (
                keyword_data.get('trends_score', 0) * weights['trends_score'] +
                keyword_data.get('serp_score', 0) * weights['serp_score'] +
                keyword_data.get('business_value', 0) * weights['business_value']
            )
            keyword_data['priority_score'] = score
        
        # 按评分降序排序
        return sorted(keywords, key=lambda x: x['priority_score'], reverse=True)
    
    def _generate_tasks_for_keyword(self, keyword_data: Dict[str, Any], target_date: datetime) -> List[Task]:
        """为单个关键词生成相关任务"""
        keyword = keyword_data['keyword']
        priority_score = keyword_data['priority_score']
        
        # 根据评分确定优先级
        if priority_score >= 0.8:
            priority = TaskPriority.HIGH
        elif priority_score >= 0.6:
            priority = TaskPriority.MEDIUM
        else:
            priority = TaskPriority.LOW
        
        tasks = []
        
        # 关键词验证任务
        if keyword_data.get('serp_score', 0) < 0.7:
            task_id = f"verify_{keyword.replace(' ', '_')}_{target_date.strftime('%Y%m%d')}"
            task = Task(
                id=task_id,
                keyword=keyword,
                task_type=TaskType.KEYWORD_VERIFICATION,
                priority=priority,
                status=TaskStatus.PENDING,
                title=f"验证关键词: {keyword}",
                description=f"验证'{keyword}'在Semrush中的KD值和搜索量数据",
                estimated_time=15,
                created_at=datetime.now(),
                due_date=target_date + timedelta(days=1),
                score=priority_score,
                tags=['verification', 'semrush']
            )
            tasks.append(task)
        
        # SERP分析任务
        if keyword_data.get('competition', 0) > 0.5:
            task_id = f"serp_{keyword.replace(' ', '_')}_{target_date.strftime('%Y%m%d')}"
            task = Task(
                id=task_id,
                keyword=keyword,
                task_type=TaskType.SERP_ANALYSIS,
                priority=priority,
                status=TaskStatus.PENDING,
                title=f"SERP分析: {keyword}",
                description=f"分析'{keyword}'的搜索结果页面竞争结构",
                estimated_time=20,
                created_at=datetime.now(),
                due_date=target_date + timedelta(days=2),
                score=priority_score,
                tags=['serp', 'competition']
            )
            tasks.append(task)
        
        # 趋势检查任务
        if keyword_data.get('trends_score', 0) > 0.8:
            task_id = f"trends_{keyword.replace(' ', '_')}_{target_date.strftime('%Y%m%d')}"
            task = Task(
                id=task_id,
                keyword=keyword,
                task_type=TaskType.TRENDS_CHECK,
                priority=priority,
                status=TaskStatus.PENDING,
                title=f"趋势检查: {keyword}",
                description=f"检查'{keyword}'的Google Trends异常数据",
                estimated_time=10,
                created_at=datetime.now(),
                due_date=target_date + timedelta(days=3),
                score=priority_score,
                tags=['trends', 'google']
            )
            tasks.append(task)
        
        return tasks
    
    def _task_exists(self, keyword: str, task_type: TaskType, target_date: datetime) -> bool:
        """检查任务是否已存在"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT COUNT(*) FROM tasks WHERE keyword = ? AND task_type = ? AND DATE(created_at) = DATE(?)',
                (keyword, task_type.value, target_date.isoformat())
            )
            return cursor.fetchone()[0] > 0
    
    def _save_task(self, task: Task):
        """保存任务到数据库"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO tasks (
                    id, keyword, task_type, priority, status, title, description,
                    estimated_time, score, tags, created_at, due_date, completed_at, verification_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                task.id, task.keyword, task.task_type.value, task.priority.value,
                task.status.value, task.title, task.description, task.estimated_time,
                task.score, json.dumps(task.tags), task.created_at.isoformat(),
                task.due_date.isoformat(), 
                task.completed_at.isoformat() if task.completed_at else None,
                json.dumps(task.verification_data) if task.verification_data else None
            ))
    
    def _generate_task_report(self, tasks: List[Task], target_date: datetime) -> str:
        """生成任务报告"""
        high_priority = [t for t in tasks if t.priority == TaskPriority.HIGH]
        medium_priority = [t for t in tasks if t.priority == TaskPriority.MEDIUM]
        low_priority = [t for t in tasks if t.priority == TaskPriority.LOW]
        
        report = f"""## 今日待办任务 ({target_date.strftime('%Y-%m-%d')})

### 🔥 高优先级 (需在今日完成)
"""
        
        for i, task in enumerate(high_priority, 1):
            report += f"{i}. {task.title}\n"
        
        if not high_priority:
            report += "暂无高优先级任务\n"
        
        report += "\n### 📊 中优先级 (本周内完成)\n"
        
        for i, task in enumerate(medium_priority, 1):
            report += f"{i}. {task.title}\n"
        
        if not medium_priority:
            report += "暂无中优先级任务\n"
        
        report += "\n### 📝 低优先级 (有时间时处理)\n"
        
        for i, task in enumerate(low_priority, 1):
            report += f"{i}. {task.title}\n"
        
        if not low_priority:
            report += "暂无低优先级任务\n"
        
        return report
    
    def get_tasks(self, status: str = None, priority: str = None, 
                  date_range: tuple = None) -> Dict[str, Any]:
        """获取任务列表"""
        query = 'SELECT * FROM tasks WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        
        if date_range:
            query += ' AND created_at BETWEEN ? AND ?'
            params.extend([date_range[0].isoformat(), date_range[1].isoformat()])
        
        query += ' ORDER BY priority DESC, score DESC, created_at DESC'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        tasks = []
        for row in rows:
            task_data = dict(row)
            # 解析JSON字段
            task_data['tags'] = json.loads(task_data['tags']) if task_data['tags'] else []
            if task_data['verification_data']:
                task_data['verification_data'] = json.loads(task_data['verification_data'])
            tasks.append(task_data)
        
        return {
            'success': True,
            'count': len(tasks),
            'tasks': tasks
        }
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新任务状态"""
        allowed_fields = ['status', 'completed_at', 'verification_data']
        
        # 构建更新语句
        set_clauses = []
        params = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                set_clauses.append(f'{field} = ?')
                if field == 'completed_at' and isinstance(value, datetime):
                    params.append(value.isoformat())
                elif field == 'verification_data' and isinstance(value, dict):
                    params.append(json.dumps(value))
                else:
                    params.append(value)
        
        if not set_clauses:
            return {'success': False, 'error': '没有有效的更新字段'}
        
        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            
            if cursor.rowcount == 0:
                return {'success': False, 'error': '任务不存在'}
        
        return {'success': True, 'updated_task_id': task_id}
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            # 总体统计
            cursor = conn.execute('SELECT COUNT(*) FROM tasks')
            total_tasks = cursor.fetchone()[0]
            
            # 按状态统计
            cursor = conn.execute('''
                SELECT status, COUNT(*) as count 
                FROM tasks 
                GROUP BY status
            ''')
            status_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 按优先级统计
            cursor = conn.execute('''
                SELECT priority, COUNT(*) as count 
                FROM tasks 
                GROUP BY priority
            ''')
            priority_stats = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 今日任务统计
            today = datetime.now().strftime('%Y-%m-%d')
            cursor = conn.execute('''
                SELECT COUNT(*) FROM tasks 
                WHERE DATE(created_at) = ?
            ''', (today,))
            today_tasks = cursor.fetchone()[0]
            
            # 逾期任务统计
            cursor = conn.execute('''
                SELECT COUNT(*) FROM tasks 
                WHERE status != 'completed' AND due_date < ?
            ''', (datetime.now().isoformat(),))
            overdue_tasks = cursor.fetchone()[0]
        
        return {
            'total_tasks': total_tasks,
            'today_tasks': today_tasks,
            'overdue_tasks': overdue_tasks,
            'status_distribution': status_stats,
            'priority_distribution': priority_stats,
            'completion_rate': (
                status_stats.get('completed', 0) / total_tasks * 100 
                if total_tasks > 0 else 0
            )
        }
    
    def mark_overdue_tasks(self):
        """标记逾期任务"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE tasks 
                SET status = 'overdue' 
                WHERE status IN ('pending', 'in_progress') 
                AND due_date < ?
            ''', (datetime.now().isoformat(),))
            
            return cursor.rowcount
    
    def get_daily_task_report(self, target_date: datetime = None) -> str:
        """获取每日任务报告"""
        if target_date is None:
            target_date = datetime.now()
        
        date_str = target_date.strftime('%Y-%m-%d')
        
        # 获取当日任务
        result = self.get_tasks(date_range=(
            target_date.replace(hour=0, minute=0, second=0, microsecond=0),
            target_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        ))
        
        if not result['success'] or not result['tasks']:
            return f"## {date_str} 任务报告\n\n暂无任务"
        
        tasks = result['tasks']
        
        # 按优先级分组
        high_tasks = [t for t in tasks if t['priority'] == 'high']
        medium_tasks = [t for t in tasks if t['priority'] == 'medium']
        low_tasks = [t for t in tasks if t['priority'] == 'low']
        
        report = f"## {date_str} 任务报告\n\n"
        
        if high_tasks:
            report += "### 🔥 高优先级任务\n"
            for i, task in enumerate(high_tasks, 1):
                status_icon = "✅" if task['status'] == 'completed' else "⏳"
                report += f"{i}. {status_icon} {task['title']} ({task['estimated_time']}分钟)\n"
            report += "\n"
        
        if medium_tasks:
            report += "### 📊 中优先级任务\n"
            for i, task in enumerate(medium_tasks, 1):
                status_icon = "✅" if task['status'] == 'completed' else "⏳"
                report += f"{i}. {status_icon} {task['title']} ({task['estimated_time']}分钟)\n"
            report += "\n"
        
        if low_tasks:
            report += "### 📝 低优先级任务\n"
            for i, task in enumerate(low_tasks, 1):
                status_icon = "✅" if task['status'] == 'completed' else "⏳"
                report += f"{i}. {status_icon} {task['title']} ({task['estimated_time']}分钟)\n"
        
        # 添加统计信息
        completed_count = len([t for t in tasks if t['status'] == 'completed'])
        total_time = sum(t['estimated_time'] for t in tasks)
        
        report += f"\n---\n"
        report += f"**统计**: {completed_count}/{len(tasks)} 已完成, 预估总时间: {total_time}分钟\n"
        
        return report