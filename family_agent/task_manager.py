"""
家庭任务管理系统 - PostgreSQL版
支持家庭成员之间的任务分配和消息传递
"""
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json


class FamilyTask:
    """家庭任务（数据对象）"""
    
    def __init__(self, task_id: str, from_member: str, to_member: str,
                 content: str, task_type: str = "general",
                 priority: str = "normal", status: str = "pending",
                 created_at: str = None, completed_at: str = None,
                 notes: str = ""):
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


class TaskManager:
    """
    家庭任务管理器
    
    功能:
    1. 创建任务(家庭成员间互相分配)
    2. 查看我的任务
    3. 完成任务
    4. 任务统计
    """
    
    def __init__(self, db_manager=None, data_dir: str = "data"):
        """
        初始化任务管理器
        Args:
            db_manager: DatabaseManager 实例
            data_dir: 数据目录（兼容旧接口）
        """
        self.db = db_manager
        self.data_dir = Path(data_dir)

    def create_task(
        self,
        from_member: str,
        to_member: str,
        content: str,
        task_type: str = "general",
        priority: str = "normal",
        notes: str = "",
        family_id: str = ""
    ) -> Optional[Dict]:
        """创建任务"""
        if not self.db:
            return None
        
        import hashlib, time
        task_id = f"task_{hashlib.md5(f'{from_member}_{to_member}_{time.time()}'.encode()).hexdigest()[:12]}"
        
        self.db.add_task(
            task_id=task_id,
            from_member=from_member,
            to_member=to_member,
            content=content,
            task_type=task_type,
            priority=priority,
            status="pending",
            family_id=family_id
        )
        
        # 创建通知给接收者
        if self.db:
            self.db.add_notification(
                member_name=to_member,
                title=f"新任务来自 {from_member}",
                message=content,
                notification_type='task',
                priority=priority
            )
        
        return {
            "task_id": task_id,
            "from_member": from_member,
            "to_member": to_member,
            "content": content
        }

    def get_my_tasks(self, member_name: str, status: str = "pending", family_id: str = "") -> List[Dict]:
        """获取指定成员的任务"""
        if not self.db:
            return []
        return self.db.get_tasks(to_member=member_name, status=status, family_id=family_id)

    def get_sent_tasks(self, member_name: str, family_id: str = "") -> List[Dict]:
        """获取我发出的任务"""
        if not self.db:
            return []
        with self.db.conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM tasks WHERE family_id = %s AND from_member = %s ORDER BY created_at DESC",
                (family_id or "", member_name)
            )
            return [dict(row) for row in cursor.fetchall()]

    def complete_task(self, task_id: str, family_id: str = "") -> bool:
        """完成任务"""
        if self.db:
            return self.db.update_task(
                task_id,
                family_id=family_id,
                status='completed',
                completed_at=datetime.now().isoformat(),
            )
        return False

    def cancel_task(self, task_id: str, family_id: str = "") -> bool:
        """取消任务"""
        if self.db:
            return self.db.update_task(task_id, family_id=family_id, status='cancelled')
        return False

    def delete_task(self, task_id: str, family_id: str = "") -> bool:
        """删除任务"""
        if self.db:
            return self.db.delete_task(task_id, family_id=family_id)
        return False

    def get_unread_count(self, member_name: str, family_id: str = "") -> int:
        """获取未读任务数量"""
        tasks = self.get_my_tasks(member_name, "pending", family_id=family_id)
        return len(tasks)

    def get_statistics(self, member_name: str = None, family_id: str = "") -> Dict:
        """获取任务统计"""
        if not self.db:
            return {}
        
        if member_name:
            my_tasks = self.get_my_tasks(member_name, "all", family_id=family_id)
            sent_tasks = self.get_sent_tasks(member_name, family_id=family_id)
            
            return {
                "received": {
                    "total": len(my_tasks),
                    "pending": len([t for t in my_tasks if t['status'] == "pending"]),
                    "completed": len([t for t in my_tasks if t['status'] == "completed"]),
                    "cancelled": len([t for t in my_tasks if t['status'] == "cancelled"])
                },
                "sent": {
                    "total": len(sent_tasks),
                    "pending": len([t for t in sent_tasks if t['status'] == "pending"]),
                    "completed": len([t for t in sent_tasks if t['status'] == "completed"])
                }
            }
        else:
            # 全局统计
            stats = self.db.get_stats()
            # 添加任务特定统计
            with self.db.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
                stats['pending_tasks'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM tasks")
                stats['total_tasks'] = cursor.fetchone()[0]
            return stats
