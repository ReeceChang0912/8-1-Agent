"""
推送通知管理器 - PostgreSQL版
支持任务通知、日程提醒、纪念日提醒等
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import hashlib


class NotificationManager:
    """通知管理器 - 使用 PostgreSQL"""

    def __init__(self, db_manager=None, data_dir: str = "data"):
        """
        初始化通知管理器
        Args:
            db_manager: DatabaseManager 实例
            data_dir: 数据目录（兼容旧接口）
        """
        self.db = db_manager
        self.data_dir = data_dir

    def create_notification(self,
                               member_name: str,
                               title: str,
                               message: str,
                               notification_type: str = "general",
                               priority: str = "normal",
                               scheduled_time: Optional[str] = None) -> Dict:
        """创建通知"""
        if self.db:
            self.db.add_notification(
                member_name=member_name,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority
            )

        notif_id = f"notif_{hashlib.md5(f'{member_name}{title}{datetime.now()}'.encode()).hexdigest()[:12]}"

        return {
            'id': notif_id,
            'member_name': member_name,
            'title': title,
            'message': message,
            'type': notification_type,
            'priority': priority,
            'scheduled_time': scheduled_time,
            'is_read': False,
            'created_at': datetime.now().isoformat(),
            'read_at': None
        }

    def get_unread_notifications(self, member_name: str, limit: int = 20) -> List[Dict]:
        """获取未读通知"""
        if not self.db:
            return []
        return self.db.get_notifications(member_name=member_name, is_read=False)[:limit]

    def get_all_notifications(self, member_name: str, limit: int = 50) -> List[Dict]:
        """获取所有通知"""
        if not self.db:
            return []
        return self.db.get_notifications(member_name=member_name)[:limit]

    def mark_as_read(self, notification_id: int) -> bool:
        """标记为已读"""
        if self.db:
            return self.db.mark_notification_read(notification_id)
        return False

    def mark_all_read(self, member_name: str) -> int:
        """标记所有为已读"""
        if not self.db:
            return 0
        notifications = self.db.get_notifications(member_name=member_name, is_read=False)
        count = 0
        for notif in notifications:
            if self.db.mark_notification_read(notif['id']):
                count += 1
        return count

    def get_unread_count(self, member_name: str) -> int:
        """获取未读数量"""
        if not self.db:
            return 0
        notifications = self.db.get_notifications(member_name=member_name, is_read=False)
        return len(notifications)

    def delete_notification(self, notification_id: int) -> bool:
        """删除通知"""
        if self.db:
            with self.db.conn.cursor() as cursor:
                cursor.execute('DELETE FROM notifications WHERE id = %s', (notification_id,))
                return cursor.rowcount > 0
        return False

    def clear_old_notifications(self, days: int = 30) -> int:
        """清理旧通知"""
        if not self.db:
            return 0
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        with self.db.conn.cursor() as cursor:
            cursor.execute('DELETE FROM notifications WHERE created_at < %s', (cutoff,))
            return cursor.rowcount
