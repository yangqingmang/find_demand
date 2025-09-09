#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知提醒系统

支持多种通知方式：
- 邮件通知
- 微信通知（通过企业微信机器人）
- 钉钉通知（通过钉钉机器人）
- 任务截止提醒
- 完成度统计报告

作者: AI Assistant
创建时间: 2025-01-27
"""

import smtplib
import json
import requests
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path


class NotificationType(Enum):
    """通知类型枚举"""
    EMAIL = "email"
    WECHAT = "wechat"
    DINGTALK = "dingtalk"


class Priority(Enum):
    """优先级枚举"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class NotificationConfig:
    """通知配置"""
    # 邮件配置
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    email_user: str = ""
    email_password: str = ""
    email_recipients: List[str] = None
    
    # 微信配置
    wechat_webhook_url: str = ""
    
    # 钉钉配置
    dingtalk_webhook_url: str = ""
    dingtalk_secret: str = ""
    
    # 通知开关
    email_enabled: bool = True
    wechat_enabled: bool = False
    dingtalk_enabled: bool = False
    
    def __post_init__(self):
        if self.email_recipients is None:
            self.email_recipients = []


@dataclass
class Task:
    """任务数据结构"""
    id: str
    title: str
    description: str
    priority: Priority
    deadline: datetime
    status: str = "pending"
    created_at: datetime = None
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, config: NotificationConfig):
        """
        初始化通知管理器
        
        Args:
            config: 通知配置
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def send_notification(self, 
                         message: str, 
                         subject: str = "需求挖掘系统通知",
                         notification_types: List[NotificationType] = None,
                         priority: Priority = Priority.MEDIUM) -> Dict[str, bool]:
        """
        发送通知
        
        Args:
            message: 通知消息
            subject: 通知主题
            notification_types: 通知类型列表，默认为所有启用的类型
            priority: 优先级
            
        Returns:
            Dict[str, bool]: 各通知方式的发送结果
        """
        if notification_types is None:
            notification_types = self._get_enabled_notification_types()
            
        results = {}
        
        for notification_type in notification_types:
            try:
                if notification_type == NotificationType.EMAIL:
                    results["email"] = self._send_email(subject, message, priority)
                elif notification_type == NotificationType.WECHAT:
                    results["wechat"] = self._send_wechat(message, priority)
                elif notification_type == NotificationType.DINGTALK:
                    results["dingtalk"] = self._send_dingtalk(subject, message, priority)
            except Exception as e:
                self.logger.error(f"发送{notification_type.value}通知失败: {e}")
                results[notification_type.value] = False
                
        return results
    
    def send_task_reminder(self, tasks: List[Task]) -> Dict[str, bool]:
        """
        发送任务截止提醒
        
        Args:
            tasks: 任务列表
            
        Returns:
            Dict[str, bool]: 发送结果
        """
        if not tasks:
            return {}
            
        # 按优先级分组
        high_priority_tasks = [t for t in tasks if t.priority == Priority.HIGH]
        medium_priority_tasks = [t for t in tasks if t.priority == Priority.MEDIUM]
        low_priority_tasks = [t for t in tasks if t.priority == Priority.LOW]
        
        # 生成提醒消息
        message = self._generate_task_reminder_message(
            high_priority_tasks, medium_priority_tasks, low_priority_tasks
        )
        
        subject = f"任务截止提醒 - {datetime.now().strftime('%Y-%m-%d')}"
        
        return self.send_notification(message, subject, priority=Priority.HIGH)
    
    def send_completion_report(self, 
                             completed_tasks: List[Task],
                             pending_tasks: List[Task],
                             overdue_tasks: List[Task]) -> Dict[str, bool]:
        """
        发送完成度统计报告
        
        Args:
            completed_tasks: 已完成任务
            pending_tasks: 待完成任务
            overdue_tasks: 逾期任务
            
        Returns:
            Dict[str, bool]: 发送结果
        """
        total_tasks = len(completed_tasks) + len(pending_tasks) + len(overdue_tasks)
        completion_rate = len(completed_tasks) / total_tasks * 100 if total_tasks > 0 else 0
        
        message = self._generate_completion_report_message(
            completed_tasks, pending_tasks, overdue_tasks, completion_rate
        )
        
        subject = f"任务完成度报告 - {datetime.now().strftime('%Y-%m-%d')}"
        
        return self.send_notification(message, subject, priority=Priority.MEDIUM)
    
    def _send_email(self, subject: str, message: str, priority: Priority) -> bool:
        """
        发送邮件通知
        
        Args:
            subject: 邮件主题
            message: 邮件内容
            priority: 优先级
            
        Returns:
            bool: 发送是否成功
        """
        if not self.config.email_enabled or not self.config.email_recipients:
            return False
            
        try:
            # 创建邮件对象
            msg = MIMEMultipart()
            msg['From'] = self.config.email_user
            msg['To'] = ", ".join(self.config.email_recipients)
            msg['Subject'] = Header(subject, 'utf-8')
            
            # 设置优先级
            if priority == Priority.HIGH:
                msg['X-Priority'] = '1'
                msg['X-MSMail-Priority'] = 'High'
            
            # 添加邮件内容
            msg.attach(MIMEText(message, 'plain', 'utf-8'))
            
            # 发送邮件
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.email_user, self.config.email_password)
            server.sendmail(self.config.email_user, self.config.email_recipients, msg.as_string())
            server.quit()
            
            self.logger.info(f"邮件通知发送成功: {subject}")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件发送失败: {e}")
            return False
    
    def _send_wechat(self, message: str, priority: Priority) -> bool:
        """
        发送微信通知（企业微信机器人）
        
        Args:
            message: 消息内容
            priority: 优先级
            
        Returns:
            bool: 发送是否成功
        """
        if not self.config.wechat_enabled or not self.config.wechat_webhook_url:
            return False
            
        try:
            # 根据优先级添加标识
            priority_emoji = {
                Priority.HIGH: "🔥",
                Priority.MEDIUM: "📊",
                Priority.LOW: "📝"
            }
            
            formatted_message = f"{priority_emoji.get(priority, '')} {message}"
            
            payload = {
                "msgtype": "text",
                "text": {
                    "content": formatted_message
                }
            }
            
            response = requests.post(
                self.config.wechat_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.logger.info("微信通知发送成功")
                return True
            else:
                self.logger.error(f"微信通知发送失败: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"微信通知发送失败: {e}")
            return False
    
    def _send_dingtalk(self, subject: str, message: str, priority: Priority) -> bool:
        """
        发送钉钉通知
        
        Args:
            subject: 通知主题
            message: 消息内容
            priority: 优先级
            
        Returns:
            bool: 发送是否成功
        """
        if not self.config.dingtalk_enabled or not self.config.dingtalk_webhook_url:
            return False
            
        try:
            # 根据优先级设置颜色
            priority_colors = {
                Priority.HIGH: "#FF0000",  # 红色
                Priority.MEDIUM: "#FFA500",  # 橙色
                Priority.LOW: "#008000"  # 绿色
            }
            
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": subject,
                    "text": f"## {subject}\n\n{message}"
                }
            }
            
            # 如果配置了密钥，添加签名
            if self.config.dingtalk_secret:
                import time
                import hmac
                import hashlib
                import base64
                import urllib.parse
                
                timestamp = str(round(time.time() * 1000))
                secret_enc = self.config.dingtalk_secret.encode('utf-8')
                string_to_sign = f'{timestamp}\n{self.config.dingtalk_secret}'
                string_to_sign_enc = string_to_sign.encode('utf-8')
                hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                
                url = f"{self.config.dingtalk_webhook_url}&timestamp={timestamp}&sign={sign}"
            else:
                url = self.config.dingtalk_webhook_url
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    self.logger.info("钉钉通知发送成功")
                    return True
                else:
                    self.logger.error(f"钉钉通知发送失败: {result.get('errmsg')}")
                    return False
            else:
                self.logger.error(f"钉钉通知发送失败: {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"钉钉通知发送失败: {e}")
            return False
    
    def _get_enabled_notification_types(self) -> List[NotificationType]:
        """
        获取启用的通知类型
        
        Returns:
            List[NotificationType]: 启用的通知类型列表
        """
        enabled_types = []
        
        if self.config.email_enabled:
            enabled_types.append(NotificationType.EMAIL)
        if self.config.wechat_enabled:
            enabled_types.append(NotificationType.WECHAT)
        if self.config.dingtalk_enabled:
            enabled_types.append(NotificationType.DINGTALK)
            
        return enabled_types
    
    def _generate_task_reminder_message(self, 
                                      high_tasks: List[Task],
                                      medium_tasks: List[Task],
                                      low_tasks: List[Task]) -> str:
        """
        生成任务提醒消息
        
        Args:
            high_tasks: 高优先级任务
            medium_tasks: 中优先级任务
            low_tasks: 低优先级任务
            
        Returns:
            str: 格式化的提醒消息
        """
        message_parts = []
        message_parts.append(f"📅 任务截止提醒 - {datetime.now().strftime('%Y-%m-%d')}")
        message_parts.append("")
        
        if high_tasks:
            message_parts.append("🔥 高优先级任务 (需紧急处理):")
            for i, task in enumerate(high_tasks, 1):
                deadline_str = task.deadline.strftime('%Y-%m-%d %H:%M')
                message_parts.append(f"{i}. {task.title} (截止: {deadline_str})")
            message_parts.append("")
        
        if medium_tasks:
            message_parts.append("📊 中优先级任务 (本周内完成):")
            for i, task in enumerate(medium_tasks, 1):
                deadline_str = task.deadline.strftime('%Y-%m-%d %H:%M')
                message_parts.append(f"{i}. {task.title} (截止: {deadline_str})")
            message_parts.append("")
        
        if low_tasks:
            message_parts.append("📝 低优先级任务 (有时间时处理):")
            for i, task in enumerate(low_tasks, 1):
                deadline_str = task.deadline.strftime('%Y-%m-%d %H:%M')
                message_parts.append(f"{i}. {task.title} (截止: {deadline_str})")
            message_parts.append("")
        
        message_parts.append("请及时处理相关任务，确保项目进度。")
        
        return "\n".join(message_parts)
    
    def _generate_completion_report_message(self, 
                                          completed_tasks: List[Task],
                                          pending_tasks: List[Task],
                                          overdue_tasks: List[Task],
                                          completion_rate: float) -> str:
        """
        生成完成度报告消息
        
        Args:
            completed_tasks: 已完成任务
            pending_tasks: 待完成任务
            overdue_tasks: 逾期任务
            completion_rate: 完成率
            
        Returns:
            str: 格式化的报告消息
        """
        message_parts = []
        message_parts.append(f"📊 任务完成度报告 - {datetime.now().strftime('%Y-%m-%d')}")
        message_parts.append("")
        
        # 总体统计
        total_tasks = len(completed_tasks) + len(pending_tasks) + len(overdue_tasks)
        message_parts.append(f"📈 总体统计:")
        message_parts.append(f"  • 总任务数: {total_tasks}")
        message_parts.append(f"  • 已完成: {len(completed_tasks)} ({completion_rate:.1f}%)")
        message_parts.append(f"  • 进行中: {len(pending_tasks)}")
        message_parts.append(f"  • 已逾期: {len(overdue_tasks)}")
        message_parts.append("")
        
        # 完成率评价
        if completion_rate >= 80:
            message_parts.append("✅ 完成度优秀，继续保持！")
        elif completion_rate >= 60:
            message_parts.append("⚠️ 完成度良好，还有提升空间。")
        else:
            message_parts.append("❌ 完成度偏低，需要加强任务管理。")
        
        # 逾期任务提醒
        if overdue_tasks:
            message_parts.append("")
            message_parts.append("🚨 逾期任务提醒:")
            for i, task in enumerate(overdue_tasks[:5], 1):  # 最多显示5个
                overdue_days = (datetime.now() - task.deadline).days
                message_parts.append(f"{i}. {task.title} (逾期{overdue_days}天)")
            
            if len(overdue_tasks) > 5:
                message_parts.append(f"... 还有{len(overdue_tasks) - 5}个逾期任务")
        
        message_parts.append("")
        message_parts.append("请关注任务进度，及时调整工作计划。")
        
        return "\n".join(message_parts)


class NotificationScheduler:
    """通知调度器"""
    
    def __init__(self, notification_manager: NotificationManager):
        """
        初始化通知调度器
        
        Args:
            notification_manager: 通知管理器
        """
        self.notification_manager = notification_manager
        self.logger = logging.getLogger(__name__)
    
    def schedule_daily_reminders(self, tasks: List[Task], reminder_time: str = "09:00"):
        """
        安排每日提醒
        
        Args:
            tasks: 任务列表
            reminder_time: 提醒时间 (HH:MM格式)
        """
        # 这里可以集成APScheduler等调度库
        # 示例实现：检查当前时间是否到达提醒时间
        current_time = datetime.now().strftime("%H:%M")
        if current_time == reminder_time:
            # 筛选需要提醒的任务
            today = datetime.now().date()
            tomorrow = today + timedelta(days=1)
            
            urgent_tasks = [
                task for task in tasks 
                if task.status == "pending" and task.deadline.date() <= tomorrow
            ]
            
            if urgent_tasks:
                self.notification_manager.send_task_reminder(urgent_tasks)
    
    def schedule_completion_reports(self, 
                                  tasks: List[Task], 
                                  report_intervals: List[int] = None):
        """
        安排完成度报告
        
        Args:
            tasks: 任务列表
            report_intervals: 报告间隔（小时），默认为[1, 3, 6]
        """
        if report_intervals is None:
            report_intervals = [1, 3, 6]
        
        # 分类任务
        now = datetime.now()
        completed_tasks = [t for t in tasks if t.status == "completed"]
        pending_tasks = [t for t in tasks if t.status == "pending" and t.deadline > now]
        overdue_tasks = [t for t in tasks if t.status == "pending" and t.deadline <= now]
        
        # 发送报告
        self.notification_manager.send_completion_report(
            completed_tasks, pending_tasks, overdue_tasks
        )


def create_notification_manager(config_dict: Dict[str, Any]) -> NotificationManager:
    """
    创建通知管理器的工厂函数
    
    Args:
        config_dict: 配置字典
        
    Returns:
        NotificationManager: 通知管理器实例
    """
    config = NotificationConfig(**config_dict)
    return NotificationManager(config)


# 示例使用
if __name__ == "__main__":
    # 配置示例
    config = NotificationConfig(
        email_user="your_email@gmail.com",
        email_password="your_app_password",
        email_recipients=["recipient@example.com"],
        email_enabled=True,
        wechat_webhook_url="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your_key",
        wechat_enabled=False,
        dingtalk_webhook_url="https://oapi.dingtalk.com/robot/send?access_token=your_token",
        dingtalk_enabled=False
    )
    
    # 创建通知管理器
    notification_manager = NotificationManager(config)
    
    # 发送测试通知
    result = notification_manager.send_notification(
        "这是一条测试通知消息",
        "测试通知",
        priority=Priority.HIGH
    )
    
    print(f"通知发送结果: {result}")
    
    # 创建测试任务
    test_tasks = [
        Task(
            id="1",
            title="验证关键词搜索量",
            description="验证AI工具类关键词的搜索量数据",
            priority=Priority.HIGH,
            deadline=datetime.now() + timedelta(hours=2)
        ),
        Task(
            id="2",
            title="更新竞品分析",
            description="更新主要竞品的最新数据",
            priority=Priority.MEDIUM,
            deadline=datetime.now() + timedelta(days=1)
        )
    ]
    
    # 发送任务提醒
    reminder_result = notification_manager.send_task_reminder(test_tasks)
    print(f"任务提醒发送结果: {reminder_result}")