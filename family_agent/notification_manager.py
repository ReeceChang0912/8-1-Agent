"""
推送通知管理器
支持任务通知、日程提醒、纪念日提醒等
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class NotificationManager:
    """通知管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.notifications_file = self.data_dir / "notifications.json"
        self.notifications_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.notifications: List[Dict] = []
        self._load_notifications()
    
    def _load_notifications(self):
        """加载通知"""
        if self.notifications_file.exists():
            try:
                with open(self.notifications_file, 'r', encoding='utf-8') as f:
                    self.notifications = json.load(f)
            except Exception as e:
                print(f"加载通知失败: {e}")
                self.notifications = []
    
    def _save_notifications(self):
        """保存通知"""
        try:
            with open(self.notifications_file, 'w', encoding='utf-8') as f:
                json.dump(self.notifications, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存通知失败: {e}")
    
    def create_notification(self, 
                           member_name: str, 
                           title: str, 
                           message: str,
                           notification_type: str = "general",
                           priority: str = "normal",
                           scheduled_time: Optional[str] = None) -> Dict:
        """创建通知"""
        notif_id = f"notif_{hash(f'{member_name}{title}{datetime.now()}') % 1000000:06d}"
        
        notification = {
            'id': notif_id,
            'member_name': member_name,
            'title': title,
            'message': message,
            'type': notification_type,  # task, reminder, anniversary, system
            'priority': priority,  # low, normal, high, urgent
            'scheduled_time': scheduled_time,
            'is_read': False,
            'created_at': datetime.now().isoformat(),
            'read_at': None
        }
        
        self.notifications.append(notification)
        self._save_notifications()
        
        return notification
    
    def get_unread_notifications(self, member_name: str, limit: int = 20) -> List[Dict]:
        """获取未读通知"""
        unread = [
            n for n in self.notifications 
            if n['member_name'] == member_name and not n['is_read']
        ]
        return unread[-limit:]
    
    def get_all_notifications(self, member_name: str, limit: int = 50) -> List[Dict]:
        """获取所有通知"""
        member_notifs = [n for n in self.notifications if n['member_name'] == member_name]
        return member_notifs[-limit:]
    
    def mark_as_read(self, notification_id: str):
        """标记为已读"""
        for notif in self.notifications:
            if notif['id'] == notification_id:
                notif['is_read'] = True
                notif['read_at'] = datetime.now().isoformat()
                self._save_notifications()
                return True
        return False
    
    def mark_all_read(self, member_name: str):
        """标记所有为已读"""
        count = 0
        for notif in self.notifications:
            if notif['member_name'] == member_name and not notif['is_read']:
                notif['is_read'] = True
                notif['read_at'] = datetime.now().isoformat()
                count += 1
        self._save_notifications()
        return count
    
    def get_unread_count(self, member_name: str) -> int:
        """获取未读数量"""
        return sum(1 for n in self.notifications 
                  if n['member_name'] == member_name and not n['is_read'])
    
    def delete_notification(self, notification_id: str):
        """删除通知"""
        self.notifications = [n for n in self.notifications if n['id'] != notification_id]
        self._save_notifications()
    
    def clear_old_notifications(self, days: int = 30):
        """清理旧通知"""
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self.notifications)
        
        self.notifications = [
            n for n in self.notifications
            if datetime.fromisoformat(n['created_at']) > cutoff
        ]
        
        removed = original_count - len(self.notifications)
        if removed > 0:
            self._save_notifications()
        
        return removed
