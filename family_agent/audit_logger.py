"""
操作日志管理器
记录用户的所有重要操作,用于审计和追踪
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class AuditLogger:
    """操作日志管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.log_file = self.data_dir / "audit_log.json"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.logs: List[Dict] = []
        self._load_logs()
    
    def _load_logs(self):
        """加载日志"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.logs = json.load(f)
            except Exception as e:
                print(f"加载日志失败: {e}")
                self.logs = []
    
    def _save_logs(self):
        """保存日志"""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存日志失败: {e}")
    
    def log_action(self, 
                   user_id: str,
                   action: str,
                   resource_type: str,
                   resource_id: str,
                   details: str = "",
                   ip_address: str = "",
                   success: bool = True) -> Dict:
        """记录操作"""
        log_entry = {
            'id': f"log_{hash(f'{user_id}{action}{datetime.now()}') % 1000000:06d}",
            'user_id': user_id,
            'action': action,  # create, update, delete, read, login, logout
            'resource_type': resource_type,  # member, task, shopping_item, reminder, etc.
            'resource_id': resource_id,
            'details': details,
            'ip_address': ip_address,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logs.append(log_entry)
        self._save_logs()
        
        return log_entry
    
    def get_user_logs(self, user_id: str, limit: int = 100) -> List[Dict]:
        """获取用户日志"""
        user_logs = [log for log in self.logs if log['user_id'] == user_id]
        return user_logs[-limit:]
    
    def get_resource_logs(self, resource_type: str, resource_id: str, limit: int = 50) -> List[Dict]:
        """获取资源的操作历史"""
        resource_logs = [
            log for log in self.logs 
            if log['resource_type'] == resource_type and log['resource_id'] == resource_id
        ]
        return resource_logs[-limit:]
    
    def get_recent_logs(self, hours: int = 24, limit: int = 200) -> List[Dict]:
        """获取最近的日志"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            log for log in self.logs
            if datetime.fromisoformat(log['timestamp']) > cutoff
        ]
        return recent[-limit:]
    
    def get_failed_actions(self, hours: int = 24) -> List[Dict]:
        """获取失败的操作"""
        cutoff = datetime.now() - timedelta(hours=hours)
        failed = [
            log for log in self.logs
            if not log['success'] and datetime.fromisoformat(log['timestamp']) > cutoff
        ]
        return failed
    
    def get_statistics(self, hours: int = 24) -> Dict:
        """获取操作统计"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_logs = [
            log for log in self.logs
            if datetime.fromisoformat(log['timestamp']) > cutoff
        ]
        
        stats = {
            'total_actions': len(recent_logs),
            'successful_actions': sum(1 for log in recent_logs if log['success']),
            'failed_actions': sum(1 for log in recent_logs if not log['success']),
            'actions_by_type': {},
            'actions_by_user': {},
            'actions_by_resource': {}
        }
        
        for log in recent_logs:
            # 按操作类型统计
            action = log['action']
            stats['actions_by_type'][action] = stats['actions_by_type'].get(action, 0) + 1
            
            # 按用户统计
            user = log['user_id']
            stats['actions_by_user'][user] = stats['actions_by_user'].get(user, 0) + 1
            
            # 按资源类型统计
            resource = log['resource_type']
            stats['actions_by_resource'][resource] = stats['actions_by_resource'].get(resource, 0) + 1
        
        return stats
    
    def clear_old_logs(self, days: int = 90):
        """清理旧日志"""
        cutoff = datetime.now() - timedelta(days=days)
        original_count = len(self.logs)
        
        self.logs = [
            log for log in self.logs
            if datetime.fromisoformat(log['timestamp']) > cutoff
        ]
        
        removed = original_count - len(self.logs)
        if removed > 0:
            self._save_logs()
        
        return removed
