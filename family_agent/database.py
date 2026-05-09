"""
PostgreSQL 数据库管理器
替代 JSON 文件存储和 SQLite，提供并发安全和数据完整性
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
from dotenv import load_dotenv

load_dotenv()


class DatabaseManager:
    """PostgreSQL 数据库管理器"""

    def __init__(self, db_url: str = None):
        """
        初始化数据库连接
        Args:
            db_url: PostgreSQL 连接字符串，格式: postgresql://user:password@host:port/dbname
                   如果不提供，从环境变量 DATABASE_URL 读取
        """
        self.db_url = db_url or os.getenv('DATABASE_URL')
        if not self.db_url:
            raise ValueError(
                "缺少数据库连接配置。请在环境变量中设置 DATABASE_URL，"
                "格式: postgresql://user:password@host:port/dbname"
            )
        self.conn = None
        self._connect()
        self._init_tables()

    def _connect(self):
        """建立数据库连接"""
        try:
            self.conn = psycopg2.connect(
                self.db_url,
                cursor_factory=RealDictCursor
            )
            self.conn.autocommit = True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise

    def _init_tables(self):
        """初始化数据库表"""
        with self.conn.cursor() as cursor:
            # 家庭成员表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    age INTEGER NOT NULL,
                    side TEXT DEFAULT 'core',
                    interaction_style TEXT DEFAULT 'peer',
                    permission TEXT DEFAULT 'member',
                    preferences TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 购物清单项表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shopping_items (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    quantity TEXT DEFAULT '1',
                    category TEXT DEFAULT 'general',
                    priority TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'pending',
                    added_by TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 日程表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id SERIAL PRIMARY KEY,
                    date TEXT NOT NULL,
                    event TEXT NOT NULL,
                    member TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 聊天历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    emotion TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    from_member TEXT NOT NULL,
                    to_member TEXT NOT NULL,
                    content TEXT NOT NULL,
                    task_type TEXT DEFAULT 'general',
                    priority TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                )
            """)

            # 照片索引表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS photos (
                    id SERIAL PRIMARY KEY,
                    photo_id TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    upload_date TEXT,
                    description TEXT DEFAULT '',
                    tags TEXT DEFAULT '[]',
                    people TEXT DEFAULT '[]',
                    event TEXT DEFAULT '',
                    location TEXT DEFAULT '',
                    mood TEXT DEFAULT 'neutral',
                    metadata TEXT DEFAULT '{}'
                )
            """)

            # 通知表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    member_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    notification_type TEXT DEFAULT 'general',
                    priority TEXT DEFAULT 'normal',
                    is_read BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 审计日志表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    success BOOLEAN DEFAULT TRUE,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 邀请表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invites (
                    id SERIAL PRIMARY KEY,
                    code TEXT UNIQUE NOT NULL,
                    family_id TEXT NOT NULL,
                    creator TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE
                )
            """)

            # 购物历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS shopping_history (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    quantity TEXT,
                    member TEXT NOT NULL,
                    purchase_date TEXT NOT NULL
                )
            """)

            # 家庭表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS families (
                    family_id TEXT PRIMARY KEY,
                    family_name TEXT NOT NULL,
                    members TEXT DEFAULT '[]',
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 会话表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    member_name TEXT NOT NULL,
                    login_time TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)

    # ===== 剩下的方法与之前一致 =====
    # （成员管理、购物清单、日程、聊天历史、任务、照片、通知等）

    def add_member(self, name: str, role: str, age: int, side: str = 'core',
                   interaction_style: str = 'peer', permission: str = 'member',
                   preferences: List[str] = None):
        with self.conn.cursor() as cursor:
            try:
                prefs = json.dumps(preferences or [])
                cursor.execute("""
                    INSERT INTO members (name, role, age, side, interaction_style, permission, preferences)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, role, age, side, interaction_style, permission, prefs))
                return True
            except psycopg2.IntegrityError:
                return False

    def get_all_members(self) -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM members ORDER BY created_at')
            return [dict(row) for row in cursor.fetchall()]

    def get_member(self, name: str) -> Optional[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM members WHERE name = %s', (name,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def remove_member(self, name: str):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM members WHERE name = %s', (name,))
            return cursor.rowcount > 0

    def update_member(self, name: str, **kwargs):
        if not kwargs:
            return False
        set_clause = ', '.join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [name]
        with self.conn.cursor() as cursor:
            cursor.execute(f"UPDATE members SET {set_clause} WHERE name = %s", values)
            return cursor.rowcount > 0

    def add_shopping_item(self, name: str, quantity: str = '1', category: str = 'general',
                          priority: str = 'normal', added_by: str = '',
                          status: str = 'pending'):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO shopping_items (name, quantity, category, priority, added_by, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (name, quantity, category, priority, added_by, status))

    def get_all_shopping_items(self, status: str = None) -> List[Dict]:
        with self.conn.cursor() as cursor:
            if status:
                cursor.execute('SELECT * FROM shopping_items WHERE status = %s ORDER BY created_at', (status,))
            else:
                cursor.execute('SELECT * FROM shopping_items ORDER BY created_at')
            return [dict(row) for row in cursor.fetchall()]

    def update_shopping_item(self, item_id: int, **kwargs):
        if not kwargs:
            return False
        set_clause = ', '.join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [item_id]
        with self.conn.cursor() as cursor:
            cursor.execute(f"UPDATE shopping_items SET {set_clause} WHERE id = %s", values)
            return cursor.rowcount > 0

    def remove_shopping_item(self, item_id: int):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM shopping_items WHERE id = %s', (item_id,))
            return cursor.rowcount > 0

    def add_reminder(self, date: str, event: str, member: str = ''):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reminders (date, event, member)
                VALUES (%s, %s, %s)
            """, (date, event, member))

    def get_all_reminders(self, member: str = None) -> List[Dict]:
        with self.conn.cursor() as cursor:
            if member:
                cursor.execute('SELECT * FROM reminders WHERE member = %s ORDER BY date', (member,))
            else:
                cursor.execute('SELECT * FROM reminders ORDER BY date')
            return [dict(row) for row in cursor.fetchall()]

    def remove_reminder(self, reminder_id: int):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM reminders WHERE id = %s', (reminder_id,))
            return cursor.rowcount > 0

    def add_chat_message(self, user_id: str, role: str, content: str, emotion: str = None):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_history (user_id, role, content, emotion)
                VALUES (%s, %s, %s, %s)
            """, (user_id, role, content, emotion))

    def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM chat_history
                WHERE user_id = %s
                ORDER BY timestamp ASC
                LIMIT %s
            """, (user_id, limit))
            return [dict(row) for row in cursor.fetchall()]

    def clear_chat_history(self, user_id: str):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM chat_history WHERE user_id = %s', (user_id,))

    def add_task(self, task_id: str, from_member: str, to_member: str, content: str,
                 task_type: str = 'general', priority: str = 'normal',
                 status: str = 'pending'):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tasks (id, from_member, to_member, content, task_type, priority, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (task_id, from_member, to_member, content, task_type, priority, status))

    def get_tasks(self, to_member: str = None, status: str = None) -> List[Dict]:
        with self.conn.cursor() as cursor:
            query = 'SELECT * FROM tasks WHERE 1=1'
            params = []
            if to_member:
                query += ' AND to_member = %s'
                params.append(to_member)
            if status:
                query += ' AND status = %s'
                params.append(status)
            query += ' ORDER BY created_at DESC'
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_task(self, task_id: str, **kwargs):
        if not kwargs:
            return False
        set_clause = ', '.join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [task_id]
        with self.conn.cursor() as cursor:
            cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = %s", values)
            return cursor.rowcount > 0

    def delete_task(self, task_id: str):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
            return cursor.rowcount > 0

    def add_photo(self, photo_id: str, filename: str, upload_date: str, **kwargs):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO photos (photo_id, filename, upload_date, description, tags, people, event, location, mood, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                photo_id, filename, upload_date,
                kwargs.get('description', ''),
                json.dumps(kwargs.get('tags', [])),
                json.dumps(kwargs.get('people', [])),
                kwargs.get('event', ''),
                kwargs.get('location', ''),
                kwargs.get('mood', 'neutral'),
                json.dumps(kwargs.get('metadata', {}))
            ))

    def get_photos(self, **kwargs) -> List[Dict]:
        with self.conn.cursor() as cursor:
            query = 'SELECT * FROM photos WHERE 1=1'
            params = []
            for key, value in kwargs.items():
                if key == 'tags_contains':
                    query += " AND tags::text LIKE %s"
                    params.append(f"%{value}%")
                else:
                    query += f" AND {key} = %s"
                    params.append(value)
            query += ' ORDER BY upload_date DESC'
            cursor.execute(query, params)
            rows = cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d['tags'] = json.loads(d['tags']) if d['tags'] else []
                d['people'] = json.loads(d['people']) if d['people'] else []
                d['metadata'] = json.loads(d['metadata']) if d['metadata'] else {}
                result.append(d)
            return result

    def add_notification(self, member_name: str, title: str, message: str,
                         notification_type: str = 'general', priority: str = 'normal'):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO notifications (member_name, title, message, notification_type, priority)
                VALUES (%s, %s, %s, %s, %s)
            """, (member_name, title, message, notification_type, priority))

    def get_notifications(self, member_name: str, is_read: bool = None) -> List[Dict]:
        with self.conn.cursor() as cursor:
            query = 'SELECT * FROM notifications WHERE member_name = %s'
            params = [member_name]
            if is_read is not None:
                query += ' AND is_read = %s'
                params.append(is_read)
            query += ' ORDER BY created_at DESC'
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def mark_notification_read(self, notification_id: int):
        with self.conn.cursor() as cursor:
            cursor.execute('UPDATE notifications SET is_read = TRUE WHERE id = %s', (notification_id,))
            return cursor.rowcount > 0

    def add_audit_log(self, action: str, resource_type: str = None, resource_id: str = None,
                        user_id: str = None, details: str = None,
                        ip_address: str = None, success: bool = True):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, resource_type, resource_id, details, ip_address, success)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, action, resource_type, resource_id, details, ip_address, success))

    def add_invite(self, code: str, family_id: str, creator: str, expires_at: str):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO invites (code, family_id, creator, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (code, family_id, creator, expires_at))

    def get_invite(self, code: str) -> Optional[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM invites WHERE code = %s', (code,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def mark_invite_used(self, code: str):
        with self.conn.cursor() as cursor:
            cursor.execute('UPDATE invites SET used = TRUE WHERE code = %s', (code,))

    def add_shopping_history(self, name: str, quantity: str, member: str):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO shopping_history (name, quantity, member, purchase_date)
                VALUES (%s, %s, %s, %s)
            """, (name, quantity, member, datetime.now().isoformat()))

    def get_shopping_history(self) -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM shopping_history ORDER BY purchase_date DESC')
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict:
        stats = {}
        with self.conn.cursor() as cursor:
            for table in ['members', 'reminders', 'shopping_items', 'chat_history', 'tasks']:
                cursor.execute(f'SELECT COUNT(*) AS cnt FROM {table}')
                row = cursor.fetchone()
                stats[f'{table}_count'] = row['cnt'] if row else 0
        return stats

    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute(query, params)
            try:
                return [dict(row) for row in cursor.fetchall()]
            except psycopg2.ProgrammingError:
                return []

    def close(self):
        if self.conn:
            self.conn.close()

    def add_family(self, family_id: str, family_name: str, members: List[str] = None):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS families (
                    family_id TEXT PRIMARY KEY,
                    family_name TEXT NOT NULL,
                    members TEXT DEFAULT '[]',
                    settings TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                INSERT INTO families (family_id, family_name, members, settings)
                VALUES (%s, %s, %s, %s)
            """, (family_id, family_name, json.dumps(members or []), json.dumps({})))
            return True

    def get_family(self, family_id: str) -> Optional[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM families WHERE family_id = %s', (family_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d['members'] = json.loads(d['members']) if d['members'] else []
                d['settings'] = json.loads(d['settings']) if d['settings'] else {}
                return d
            return None

    def get_all_families(self) -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM families')
            rows = cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d['members'] = json.loads(d['members']) if d['members'] else []
                d['settings'] = json.loads(d['settings']) if d['settings'] else {}
                result.append(d)
            return result

    def add_family_member(self, family_id: str, member_name: str):
        family = self.get_family(family_id)
        if family:
            members = family['members']
            if member_name not in members:
                members.append(member_name)
                with self.conn.cursor() as cursor:
                    cursor.execute('UPDATE families SET members = %s WHERE family_id = %s',
                                   (json.dumps(members), family_id))
            return True
        return False

    def remove_family_member(self, family_id: str, member_name: str):
        family = self.get_family(family_id)
        if family:
            members = [m for m in family['members'] if m != member_name]
            with self.conn.cursor() as cursor:
                cursor.execute('UPDATE families SET members = %s WHERE family_id = %s',
                               (json.dumps(members), family_id))
            return True
        return False

    def create_session(self, session_id: str, member_name: str, expires_at: str = None):
        if not expires_at:
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    member_name TEXT NOT NULL,
                    login_time TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            cursor.execute("""
                INSERT INTO sessions (session_id, member_name, login_time, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (session_id, member_name, datetime.now().isoformat(), expires_at))

    def get_session(self, session_id: str) -> Optional[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM sessions WHERE session_id = %s', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def verify_session(self, session_id: str) -> Optional[Dict]:
        session = self.get_session(session_id)
        if not session:
            return None
        if not session.get('is_active'):
            return None
        from datetime import datetime, timedelta
        if datetime.now() > datetime.fromisoformat(session['expires_at']):
            self.delete_session(session_id)
            return None
        return session

    def delete_session(self, session_id: str):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM sessions WHERE session_id = %s', (session_id,))

    def cleanup_expired_sessions(self):
        from datetime import datetime, timedelta
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM sessions WHERE expires_at < %s', (datetime.now().isoformat(),))
