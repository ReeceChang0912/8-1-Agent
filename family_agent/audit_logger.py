"""
操作日志管理器 - PostgreSQL版
记录用户的所有重要操作,用于审计和追踪
"""
from typing import List, Dict, Optional
from datetime import datetime


class AuditLogger:
    """操作日志管理器 - 使用 PostgreSQL"""

    def __init__(self, db_manager=None, data_dir: str = "data"):
        """
        初始化审计日志管理器
        Args:
            db_manager: DatabaseManager 实例
            data_dir: 数据目录（兼容旧接口）
        """
        self.db = db_manager

    def log_action(self,
                   user_id: str,
                   action: str,
                   resource_type: str = None,
                   resource_id: str = None,
                   details: str = "",
                   ip_address: str = "",
                   success: bool = True) -> Dict:
        """记录操作"""
        if self.db:
            self.db.add_audit_log(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address,
                success=success
            )

        return {
            'id': f"log_{hash(f'{user_id}{action}{datetime.now()}') % 1000000:06d}",
            'user_id': user_id,
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'details': details,
            'ip_address': ip_address,
            'success': success,
            'timestamp': datetime.now().isoformat()
        }

    def get_user_logs(self, user_id: str, limit: int = 100) -> List[Dict]:
        """获取用户日志"""
        if not self.db:
            return []
        with self.db.conn.cursor() as cursor:
            cursor.execute('''
                SELECT * FROM audit_logs
                WHERE user_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            ''', (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_resource_logs(self, resource_type: str, resource_id: str, limit: int = 50) -> List[Dict]:
        """获取资源的操作历史"""
        if not self.db:
            return []
        with self.db.conn.cursor() as cursor:
            cursor.execute('''
                SELECT * FROM audit_logs
                WHERE resource_type = %s AND resource_id = %s
                ORDER BY timestamp DESC
                LIMIT %s
            ''', (resource_type, resource_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_recent_logs(self, hours: int = 24, limit: int = 200) -> List[Dict]:
        """获取最近的日志"""
        if not self.db:
            return []
        cutoff = (datetime.now() - __import__('datetime').timedelta(hours=hours)).isoformat()
        with self.db.conn.cursor() as cursor:
            cursor.execute('''
                SELECT * FROM audit_logs
                WHERE timestamp > %s
                ORDER BY timestamp DESC
                LIMIT %s
            ''', (cutoff, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_failed_actions(self, hours: int = 24) -> List[Dict]:
        """获取失败的操作"""
        if not self.db:
            return []
        cutoff = (datetime.now() - __import__('datetime').timedelta(hours=hours)).isoformat()
        with self.db.conn.cursor() as cursor:
            cursor.execute('''
                SELECT * FROM audit_logs
                WHERE success = FALSE AND timestamp > %s
                ORDER BY timestamp DESC
            ''', (cutoff,))
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self, hours: int = 24) -> Dict:
        """获取操作统计"""
        if not self.db:
            return {}

        cutoff = (datetime.now() - __import__('datetime').timedelta(hours=hours)).isoformat()

        stats = {
            'total_actions': 0,
            'successful_actions': 0,
            'failed_actions': 0,
            'actions_by_type': {},
            'actions_by_user': {},
            'actions_by_resource': {}
        }

        if not self.db:
            return stats

        with self.db.conn.cursor() as cursor:
            cursor.execute('''
                SELECT COUNT(*) FROM audit_logs
                WHERE timestamp > %s
            ''', (cutoff,))
            stats['total_actions'] = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*) FROM audit_logs
                WHERE success = TRUE AND timestamp > %s
            ''', (cutoff,))
            stats['successful_actions'] = cursor.fetchone()[0]

            cursor.execute('''
                SELECT COUNT(*) FROM audit_logs
                WHERE success = FALSE AND timestamp > %s
            ''', (cutoff,))
            stats['failed_actions'] = cursor.fetchone()[0]

            # 按操作类型统计
            cursor.execute('''
                SELECT action, COUNT(*) as cnt FROM audit_logs
                WHERE timestamp > %s
                GROUP BY action
            ''', (cutoff,))
            stats['actions_by_type'] = {row['action']: row['cnt'] for row in cursor.fetchall()}

            # 按用户统计
            cursor.execute('''
                SELECT user_id, COUNT(*) as cnt FROM audit_logs
                WHERE timestamp > %s
                GROUP BY user_id
            ''', (cutoff,))
            stats['actions_by_user'] = {row['user_id']: row['cnt'] for row in cursor.fetchall()}

            # 按资源类型统计
            cursor.execute('''
                SELECT resource_type, COUNT(*) as cnt FROM audit_logs
                WHERE timestamp > %s
                GROUP BY resource_type
            ''', (cutoff,))
            stats['actions_by_resource'] = {row['resource_type']: row['cnt'] for row in cursor.fetchall() if row['resource_type']}

        return stats

    def clear_old_logs(self, days: int = 90) -> int:
        """清理旧日志"""
        if not self.db:
            return 0
        cutoff = (datetime.now() - __import__('datetime').timedelta(days=days)).isoformat()
        with self.db.conn.cursor() as cursor:
            cursor.execute('DELETE FROM audit_logs WHERE timestamp < %s', (cutoff,))
            return cursor.rowcount
