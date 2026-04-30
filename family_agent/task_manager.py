"""
家庭成员任务管理系统
支持家庭成员之间的任务分配和消息传递
"""

from typing import List, Dict, Optional
from datetime import datetime
import json
from pathlib import Path
from .notification_manager import NotificationManager


class FamilyTask:
    """家庭任务"""
    
    def __init__(
        self,
        task_id: str,
        from_member: str,
        to_member: str,
        content: str,
        task_type: str = "shopping",  # shopping, reminder, message, general
        priority: str = "normal",  # high, normal, low
        status: str = "pending",  # pending, completed, cancelled
        created_at: str = None,
        completed_at: str = None,
        notes: str = ""
    ):
        self.task_id = task_id
        self.from_member = from_member
        self.to_member = to_member
        self.content = content
        self.task_type = task_type
        self.priority = priority
        self.status = status
        self.created_at = created_at or datetime.now().isoformat()
        self.completed_at = completed_at
        self.notes = notes
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "from_member": self.from_member,
            "to_member": self.to_member,
            "content": self.content,
            "task_type": self.task_type,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "notes": self.notes
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'FamilyTask':
        return FamilyTask(**data)


class TaskManager:
    """
    家庭任务管理器
    
    功能:
    1. 创建任务(家庭成员间互相分配)
    2. 查看我的任务
    3. 完成任务
    4. 任务统计
    """
    
    def __init__(self, data_file: str = "data/family_tasks.json", data_dir: str = "data"):
        self.data_file = Path(data_file)
        self.tasks: List[FamilyTask] = []
        self.notification_manager = NotificationManager(data_dir=data_dir)
        self._load_tasks()
    
    def create_task(
        self,
        from_member: str,
        to_member: str,
        content: str,
        task_type: str = "general",
        priority: str = "normal",
        notes: str = ""
    ) -> FamilyTask:
        """
        创建任务
        
        Args:
            from_member: 发起者
            to_member: 接收者
            content: 任务内容
            task_type: 任务类型
            priority: 优先级
            notes: 备注
        
        Returns:
            创建的任务对象
        """
        
        import hashlib
        import time
        
        task_id = f"task_{hashlib.md5(f'{from_member}_{to_member}_{time.time()}'.encode()).hexdigest()[:12]}"
        
        task = FamilyTask(
            task_id=task_id,
            from_member=from_member,
            to_member=to_member,
            content=content,
            task_type=task_type,
            priority=priority,
            status="pending",
            notes=notes
        )
        
        self.tasks.append(task)
        self._save_tasks()
        
        # 创建通知给接收者
        priority_map = {
            'high': 'urgent',
            'normal': 'normal',
            'low': 'low'
        }
        self.notification_manager.create_notification(
            member_name=to_member,
            title=f"新任务来自 {from_member}",
            message=f"{content}",
            notification_type='task',
            priority=priority_map.get(priority, 'normal')
        )
        
        return task
    
    def get_my_tasks(self, member_name: str, status: str = "pending") -> List[FamilyTask]:
        """
        获取指定成员的任務
        
        Args:
            member_name: 成员姓名
            status: 任务状态 (pending, completed, all)
        
        Returns:
            任务列表
        """
        
        if status == "all":
            return [t for t in self.tasks if t.to_member == member_name]
        
        return [t for t in self.tasks if t.to_member == member_name and t.status == status]
    
    def get_sent_tasks(self, member_name: str) -> List[FamilyTask]:
        """获取我发出的任务"""
        return [t for t in self.tasks if t.from_member == member_name]
    
    def complete_task(self, task_id: str) -> bool:
        """完成任务"""
        for task in self.tasks:
            if task.task_id == task_id:
                task.status = "completed"
                task.completed_at = datetime.now().isoformat()
                self._save_tasks()
                return True
        return False
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        for task in self.tasks:
            if task.task_id == task_id:
                task.status = "cancelled"
                self._save_tasks()
                return True
        return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        original_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        
        if len(self.tasks) < original_count:
            self._save_tasks()
            return True
        return False
    
    def get_unread_count(self, member_name: str) -> int:
        """获取未读任务数量"""
        return len(self.get_my_tasks(member_name, "pending"))
    
    def get_statistics(self, member_name: str = None) -> Dict:
        """
        获取任务统计
        
        Args:
            member_name: 如果指定,只统计该成员的数据
        """
        
        if member_name:
            my_tasks = self.get_my_tasks(member_name, "all")
            sent_tasks = self.get_sent_tasks(member_name)
            
            return {
                "received": {
                    "total": len(my_tasks),
                    "pending": len([t for t in my_tasks if t.status == "pending"]),
                    "completed": len([t for t in my_tasks if t.status == "completed"]),
                    "cancelled": len([t for t in my_tasks if t.status == "cancelled"])
                },
                "sent": {
                    "total": len(sent_tasks),
                    "pending": len([t for t in sent_tasks if t.status == "pending"]),
                    "completed": len([t for t in sent_tasks if t.status == "completed"])
                }
            }
        else:
            # 全局统计
            return {
                "total_tasks": len(self.tasks),
                "pending": len([t for t in self.tasks if t.status == "pending"]),
                "completed": len([t for t in self.tasks if t.status == "completed"]),
                "by_type": self._count_by_field("task_type"),
                "by_priority": self._count_by_field("priority")
            }
    
    def _count_by_field(self, field: str) -> Dict:
        """按字段统计"""
        counts = {}
        for task in self.tasks:
            value = getattr(task, field)
            if value not in counts:
                counts[value] = 0
            counts[value] += 1
        return counts
    
    def _load_tasks(self):
        """加载任务数据"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.tasks = [FamilyTask.from_dict(t) for t in data]
    
    def _save_tasks(self):
        """保存任务数据"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(
                [t.to_dict() for t in self.tasks],
                f, ensure_ascii=False, indent=2
            )
