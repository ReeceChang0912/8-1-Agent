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
import uuid
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
        self._connection = None
        self._connect()
        self._init_tables()

    def _connect(self):
        """建立数据库连接"""
        try:
            self._connection = psycopg2.connect(
                self.db_url,
                cursor_factory=RealDictCursor
            )
            self._connection.autocommit = True
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise

    @property
    def conn(self):
        """自动重连的连接属性"""
        try:
            # Check if connection exists and is open (closed == 0 means open)
            if not self._connection or self._connection.closed != 0:
                self._connect()
            else:
                # Test the connection with a simple query
                with self._connection.cursor() as c:
                    c.execute("SELECT 1")
        except (psycopg2.InterfaceError, psycopg2.OperationalError, AttributeError):
            self._connect()
        return self._connection

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
                    family_id TEXT DEFAULT '',
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
                    family_id TEXT DEFAULT '',
                    date TEXT NOT NULL,
                    event TEXT NOT NULL,
                    member TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("ALTER TABLE shopping_items ADD COLUMN IF NOT EXISTS family_id TEXT DEFAULT ''")
            cursor.execute("ALTER TABLE reminders ADD COLUMN IF NOT EXISTS family_id TEXT DEFAULT ''")

            # 聊天历史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    session_id TEXT PRIMARY KEY,
                    family_id TEXT DEFAULT '',
                    user_id TEXT NOT NULL,
                    title TEXT DEFAULT '新对话',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    archived BOOLEAN DEFAULT FALSE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id SERIAL PRIMARY KEY,
                    family_id TEXT DEFAULT '',
                    user_id TEXT NOT NULL,
                    session_id TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    emotion TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS session_id TEXT")
            cursor.execute("ALTER TABLE chat_history ADD COLUMN IF NOT EXISTS family_id TEXT DEFAULT ''")
            cursor.execute("ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS family_id TEXT DEFAULT ''")
            cursor.execute("""
                SELECT user_id, MAX(timestamp) AS updated_at
                FROM chat_history
                WHERE session_id IS NULL
                GROUP BY user_id
            """)
            legacy_rows = cursor.fetchall()
            for row in legacy_rows:
                user_id = row['user_id']
                session_id = "legacy_" + uuid.uuid5(uuid.NAMESPACE_DNS, f"chat:{user_id}").hex
                cursor.execute("""
                    INSERT INTO chat_sessions (session_id, user_id, title, updated_at)
                    VALUES (%s, %s, %s, COALESCE(%s, CURRENT_TIMESTAMP))
                    ON CONFLICT (session_id) DO NOTHING
                """, (session_id, user_id, "历史对话", row.get('updated_at')))
                cursor.execute("""
                    UPDATE chat_history
                    SET session_id = %s
                    WHERE user_id = %s AND session_id IS NULL
                """, (session_id, user_id))
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_history_user_session
                ON chat_history (family_id, user_id, session_id, timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_updated
                ON chat_sessions (family_id, user_id, updated_at DESC)
            """)

            # 任务表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    family_id TEXT DEFAULT '',
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
            cursor.execute("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS family_id TEXT DEFAULT ''")
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_shopping_items_family_status
                ON shopping_items (family_id, status, created_at)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_reminders_family_date
                ON reminders (family_id, date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_family_member_status
                ON tasks (family_id, to_member, status, created_at)
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
                    family_id TEXT DEFAULT '',
                    member_name TEXT NOT NULL,
                    login_time TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            cursor.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS family_id TEXT DEFAULT ''")

            # 财务交易表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    amount NUMERIC(12,2) NOT NULL,
                    transaction_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    transaction_date DATE NOT NULL,
                    created_by TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 业务模块表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS wedding_items (
                    id SERIAL PRIMARY KEY,
                    family_id TEXT DEFAULT '',
                    item_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    owner TEXT DEFAULT '',
                    planned_amount NUMERIC(12,2) DEFAULT 0,
                    amount NUMERIC(12,2) DEFAULT 0,
                    status TEXT DEFAULT 'todo',
                    item_date TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("ALTER TABLE wedding_items ADD COLUMN IF NOT EXISTS planned_amount NUMERIC(12,2) DEFAULT 0")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS insurance_policies (
                    id SERIAL PRIMARY KEY,
                    family_id TEXT DEFAULT '',
                    record_type TEXT DEFAULT 'policy',
                    name TEXT NOT NULL,
                    title TEXT DEFAULT '',
                    holder TEXT NOT NULL,
                    company TEXT DEFAULT '',
                    coverage TEXT DEFAULT '',
                    premium NUMERIC(12,2) DEFAULT 0,
                    amount NUMERIC(12,2) DEFAULT 0,
                    renew_date TEXT DEFAULT '',
                    status TEXT DEFAULT '有效',
                    note TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("ALTER TABLE insurance_policies ADD COLUMN IF NOT EXISTS record_type TEXT DEFAULT 'policy'")
            cursor.execute("ALTER TABLE insurance_policies ADD COLUMN IF NOT EXISTS title TEXT DEFAULT ''")
            cursor.execute("ALTER TABLE insurance_policies ADD COLUMN IF NOT EXISTS note TEXT DEFAULT ''")
            cursor.execute("ALTER TABLE insurance_policies ADD COLUMN IF NOT EXISTS amount NUMERIC(12,2) DEFAULT 0")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS document_records (
                    id SERIAL PRIMARY KEY,
                    family_id TEXT DEFAULT '',
                    doc_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    holder TEXT DEFAULT '',
                    number TEXT DEFAULT '',
                    issuer TEXT DEFAULT '',
                    issue_date TEXT DEFAULT '',
                    expiry_date TEXT DEFAULT '',
                    reminder_days INTEGER DEFAULT 30,
                    status TEXT DEFAULT '有效',
                    note TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicle_records (
                    id SERIAL PRIMARY KEY,
                    family_id TEXT DEFAULT '',
                    record_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    plate TEXT DEFAULT '',
                    model TEXT DEFAULT '',
                    mileage NUMERIC(12,2) DEFAULT 0,
                    amount NUMERIC(12,2) DEFAULT 0,
                    record_date TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    note TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("ALTER TABLE vehicle_records ADD COLUMN IF NOT EXISTS note TEXT DEFAULT ''")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fitness_records (
                    id SERIAL PRIMARY KEY,
                    family_id TEXT DEFAULT '',
                    record_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    record_date TEXT DEFAULT '',
                    duration NUMERIC(12,2) DEFAULT 0,
                    calories NUMERIC(12,2) DEFAULT 0,
                    protein NUMERIC(12,2) DEFAULT 0,
                    weight NUMERIC(12,2) DEFAULT 0,
                    body_fat NUMERIC(12,2) DEFAULT 0,
                    waist NUMERIC(12,2) DEFAULT 0,
                    status TEXT DEFAULT '',
                    note TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("ALTER TABLE fitness_records ADD COLUMN IF NOT EXISTS protein NUMERIC(12,2) DEFAULT 0")

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
                          status: str = 'pending', family_id: str = ''):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO shopping_items (family_id, name, quantity, category, priority, added_by, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (family_id or "", name, quantity, category, priority, added_by, status))

    def get_all_shopping_items(self, status: str = None, family_id: str = '') -> List[Dict]:
        with self.conn.cursor() as cursor:
            if status:
                cursor.execute(
                    'SELECT * FROM shopping_items WHERE family_id = %s AND status = %s ORDER BY created_at',
                    (family_id or "", status)
                )
            else:
                cursor.execute(
                    'SELECT * FROM shopping_items WHERE family_id = %s ORDER BY created_at',
                    (family_id or "",)
                )
            return [dict(row) for row in cursor.fetchall()]

    def update_shopping_item(self, item_id: int, family_id: str = '', **kwargs):
        if not kwargs:
            return False
        set_clause = ', '.join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [item_id, family_id or ""]
        with self.conn.cursor() as cursor:
            cursor.execute(f"UPDATE shopping_items SET {set_clause} WHERE id = %s AND family_id = %s", values)
            return cursor.rowcount > 0

    def remove_shopping_item(self, item_id: int, family_id: str = ''):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM shopping_items WHERE id = %s AND family_id = %s', (item_id, family_id or ""))
            return cursor.rowcount > 0

    def add_reminder(self, date: str, event: str, member: str = '', family_id: str = ''):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO reminders (family_id, date, event, member)
                VALUES (%s, %s, %s, %s)
            """, (family_id or "", date, event, member))

    def get_all_reminders(self, member: str = None, family_id: str = '') -> List[Dict]:
        with self.conn.cursor() as cursor:
            if member:
                cursor.execute(
                    'SELECT * FROM reminders WHERE family_id = %s AND member = %s ORDER BY date',
                    (family_id or "", member)
                )
            else:
                cursor.execute('SELECT * FROM reminders WHERE family_id = %s ORDER BY date', (family_id or "",))
            return [dict(row) for row in cursor.fetchall()]

    def remove_reminder(self, reminder_id: int, family_id: str = ''):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM reminders WHERE id = %s AND family_id = %s', (reminder_id, family_id or ""))
            return cursor.rowcount > 0

    def create_chat_session(self, user_id: str, title: str = None, family_id: str = "") -> Dict:
        session_id = uuid.uuid4().hex
        session_title = title or "新对话"
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_sessions (session_id, family_id, user_id, title)
                VALUES (%s, %s, %s, %s)
            """, (session_id, family_id or "", user_id, session_title))
        return {
            "session_id": session_id,
            "family_id": family_id or "",
            "user_id": user_id,
            "title": session_title,
        }

    def ensure_chat_session(self, user_id: str, session_id: str = None, title: str = None,
                            family_id: str = "") -> Dict:
        if session_id:
            existing = self.get_chat_session(user_id, session_id, family_id=family_id)
            if existing:
                return existing
        return self.create_chat_session(user_id, title, family_id=family_id)

    def get_chat_session(self, user_id: str, session_id: str, family_id: str = "") -> Optional[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM chat_sessions
                WHERE user_id = %s AND session_id = %s AND family_id = %s AND archived = FALSE
            """, (user_id, session_id, family_id or ""))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_chat_sessions(self, user_id: str, limit: int = 50, family_id: str = "") -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    s.session_id,
                    s.family_id,
                    s.user_id,
                    s.title,
                    s.created_at,
                    s.updated_at,
                    COALESCE(COUNT(h.id), 0) AS message_count,
                    (
                        SELECT h2.content
                        FROM chat_history h2
                        WHERE h2.session_id = s.session_id AND h2.family_id = s.family_id
                        ORDER BY h2.timestamp DESC, h2.id DESC
                        LIMIT 1
                    ) AS last_message
                FROM chat_sessions s
                LEFT JOIN chat_history h
                    ON h.session_id = s.session_id
                    AND h.family_id = s.family_id
                    AND h.user_id = s.user_id
                WHERE s.user_id = %s AND s.family_id = %s AND s.archived = FALSE
                GROUP BY s.session_id, s.family_id, s.user_id, s.title, s.created_at, s.updated_at
                ORDER BY s.updated_at DESC
                LIMIT %s
            """, (user_id, family_id or "", limit))
            return [dict(row) for row in cursor.fetchall()]

    def update_chat_session_title(self, user_id: str, session_id: str, title: str, family_id: str = "") -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE chat_sessions
                SET title = %s, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND session_id = %s AND family_id = %s
            """, (title[:80] or "新对话", user_id, session_id, family_id or ""))
            return cursor.rowcount > 0

    def archive_chat_session(self, user_id: str, session_id: str, family_id: str = "") -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                UPDATE chat_sessions
                SET archived = TRUE, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = %s AND session_id = %s AND family_id = %s
            """, (user_id, session_id, family_id or ""))
            return cursor.rowcount > 0

    def add_chat_message(self, user_id: str, role: str, content: str, emotion: str = None,
                         session_id: str = None, family_id: str = ""):
        if session_id:
            session = self.ensure_chat_session(user_id, session_id, family_id=family_id)
            session_id = session["session_id"]
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO chat_history (family_id, user_id, session_id, role, content, emotion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (family_id or "", user_id, session_id, role, content, emotion))
            if session_id:
                cursor.execute("""
                    UPDATE chat_sessions
                    SET updated_at = CURRENT_TIMESTAMP,
                        title = CASE
                            WHEN title = '新对话' AND %s = 'user'
                            THEN %s
                            ELSE title
                        END
                    WHERE session_id = %s AND user_id = %s AND family_id = %s
                """, (role, self._derive_chat_title(content), session_id, user_id, family_id or ""))

    def get_chat_history(self, user_id: str, limit: int = 50, session_id: str = None,
                         family_id: str = "") -> List[Dict]:
        with self.conn.cursor() as cursor:
            if session_id:
                cursor.execute("""
                    SELECT * FROM chat_history
                    WHERE user_id = %s AND session_id = %s AND family_id = %s
                    ORDER BY timestamp ASC, id ASC
                    LIMIT %s
                """, (user_id, session_id, family_id or "", limit))
            else:
                cursor.execute("""
                    SELECT * FROM chat_history
                    WHERE user_id = %s AND family_id = %s
                    ORDER BY timestamp ASC, id ASC
                    LIMIT %s
                """, (user_id, family_id or "", limit))
            return [dict(row) for row in cursor.fetchall()]

    def clear_chat_history(self, user_id: str, session_id: str = None, family_id: str = ""):
        with self.conn.cursor() as cursor:
            if session_id:
                cursor.execute(
                    'DELETE FROM chat_history WHERE user_id = %s AND session_id = %s AND family_id = %s',
                    (user_id, session_id, family_id or "")
                )
            else:
                cursor.execute('DELETE FROM chat_history WHERE user_id = %s AND family_id = %s', (user_id, family_id or ""))

    def _derive_chat_title(self, content: str) -> str:
        text = " ".join((content or "").split())
        return text[:28] or "新对话"

    def add_task(self, task_id: str, from_member: str, to_member: str, content: str,
                 task_type: str = 'general', priority: str = 'normal',
                 status: str = 'pending', family_id: str = ''):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tasks (id, family_id, from_member, to_member, content, task_type, priority, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (task_id, family_id or "", from_member, to_member, content, task_type, priority, status))

    def get_tasks(self, to_member: str = None, status: str = None, family_id: str = '') -> List[Dict]:
        with self.conn.cursor() as cursor:
            query = 'SELECT * FROM tasks WHERE family_id = %s'
            params = [family_id or ""]
            if to_member:
                query += ' AND to_member = %s'
                params.append(to_member)
            if status and status != 'all':
                query += ' AND status = %s'
                params.append(status)
            query += ' ORDER BY created_at DESC'
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def update_task(self, task_id: str, family_id: str = '', **kwargs):
        if not kwargs:
            return False
        set_clause = ', '.join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [task_id, family_id or ""]
        with self.conn.cursor() as cursor:
            cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = %s AND family_id = %s", values)
            return cursor.rowcount > 0

    def delete_task(self, task_id: str, family_id: str = ''):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM tasks WHERE id = %s AND family_id = %s', (task_id, family_id or ""))
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

    def initialize_family_defaults(self, family_id: str, admin_name: str):
        """为新家庭初始化默认数据"""
        try:
            # 1. 添加默认家庭成员模板
            default_members = [
                {"name": admin_name, "role": "admin", "age": 35, "side": "core", 
                 "interaction_style": "peer", "permission": "admin", "preferences": []},
                {"name": "妈妈", "role": "parent", "age": 33, "side": "core", 
                 "interaction_style": "warm", "permission": "member", "preferences": []},
                {"name": "孩子", "role": "child", "age": 8, "side": "core", 
                 "interaction_style": "playful", "permission": "member", "preferences": []}
            ]
            
            for member in default_members:
                if member["name"] != admin_name:  # 避免重复添加管理员
                    self.add_member(
                        name=member["name"],
                        role=member["role"],
                        age=member["age"],
                        side=member["side"],
                        interaction_style=member["interaction_style"],
                        permission=member["permission"],
                        preferences=json.dumps(member["preferences"])
                    )
            
            # 2. 添加初始购物清单示例
            default_shopping = [
                {"name": "牛奶", "quantity": "1瓶", "category": "食品", "priority": "high", "added_by": admin_name},
                {"name": "鸡蛋", "quantity": "1盒", "category": "食品", "priority": "normal", "added_by": admin_name},
                {"name": "面包", "quantity": "1袋", "category": "食品", "priority": "normal", "added_by": admin_name},
                {"name": "洗洁精", "quantity": "1瓶", "category": "日用品", "priority": "low", "added_by": admin_name}
            ]
            
            for item in default_shopping:
                self.add_shopping_item(
                    name=item["name"],
                    quantity=item["quantity"],
                    category=item["category"],
                    priority=item["priority"],
                    added_by=item["added_by"]
                )
            
            # 3. 添加示例日程安排（未来7天）
            from datetime import date, timedelta
            today = date.today()
            sample_reminders = [
                {"date": (today + timedelta(days=0)).isoformat(), "event": "欢迎加入智能家庭助手！开始探索吧 🎉", "member": "all"},
                {"date": (today + timedelta(days=1)).isoformat(), "event": "晚上7点：家庭会议 - 讨论周末计划", "member": "all"},
                {"date": (today + timedelta(days=2)).isoformat(), "event": "上午10点：超市购物日", "member": admin_name},
                {"date": (today + timedelta(days=3)).isoformat(), "event": "下午3点：孩子的兴趣班", "member": "孩子"},
                {"date": (today + timedelta(days=5)).isoformat(), "event": "周末家庭活动建议：公园野餐或看电影", "member": "all"}
            ]
            
            for reminder in sample_reminders:
                self.add_reminder(
                    date=reminder["date"],
                    event=reminder["event"],
                    member=reminder["member"]
                )
            
            # 4. 添加欢迎消息到通知
            welcome_notifications = [
                {
                    "id": f"welcome_{family_id}_1",
                    "type": "info",
                    "title": "👋 欢迎来到智能家庭助手！",
                    "message": f"你好 {admin_name}！你的家庭 '{family_id}' 已创建成功。",
                    "time": datetime.now().isoformat(),
                    "read": False,
                    "priority": "high"
                },
                {
                    "id": f"welcome_{family_id}_2",
                    "type": "tip",
                    "title": "💡 快速开始提示",
                    "message": "试试说：'提醒我明天买牛奶' 或 '添加苹果到购物清单'",
                    "time": datetime.now().isoformat(),
                    "read": False,
                    "priority": "normal"
                },
                {
                    "id": f"welcome_{family_id}_3",
                    "type": "info",
                    "title": "👨‍👩‍👧‍👦 家庭成员",
                    "message": "已为您预设了家庭成员模板，您可以在成员管理中修改或删除。",
                    "time": datetime.now().isoformat(),
                    "read": False,
                    "priority": "normal"
                }
            ]
            
            for notif in welcome_notifications:
                self.add_notification(
                    notification_id=notif["id"],
                    n_type=notif["type"],
                    title=notif["title"],
                    message=notif["message"],
                    time=notif["time"],
                    read=notif["read"],
                    priority=notif["priority"]
                )
            
            return True
        except Exception as e:
            print(f"初始化家庭默认数据失败: {e}")
            return False

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

    def create_session(self, session_id: str, member_name: str, expires_at: str = None, family_id: str = ""):
        if not expires_at:
            expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        with self.conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    family_id TEXT DEFAULT '',
                    member_name TEXT NOT NULL,
                    login_time TEXT,
                    expires_at TEXT,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """)
            cursor.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS family_id TEXT DEFAULT ''")
            cursor.execute("""
                INSERT INTO sessions (session_id, family_id, member_name, login_time, expires_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (session_id, family_id or "", member_name, datetime.now().isoformat(), expires_at))

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

    # ===== 财务管理 =====

    def add_transaction(self, amount: float, transaction_type: str, category: str,
                        transaction_date: str, description: str = '', created_by: str = ''):
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO transactions (amount, transaction_type, category, description, transaction_date, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (amount, transaction_type, category, description, transaction_date, created_by))
            row = cursor.fetchone()
            return row['id'] if row else None

    def get_transactions(self, year: int, month: int, transaction_type: str = None,
                         category: str = None, page: int = 1, page_size: int = 20) -> Dict:
        with self.conn.cursor() as cursor:
            conditions = ["EXTRACT(YEAR FROM transaction_date) = %s", "EXTRACT(MONTH FROM transaction_date) = %s"]
            params = [year, month]
            if transaction_type:
                conditions.append("transaction_type = %s")
                params.append(transaction_type)
            if category:
                conditions.append("category = %s")
                params.append(category)

            where = " AND ".join(conditions)
            offset = (page - 1) * page_size

            # 总数
            cursor.execute(f"SELECT COUNT(*) AS cnt FROM transactions WHERE {where}", params)
            total = cursor.fetchone()['cnt'] or 0

            # 分页数据
            cursor.execute(f"""
                SELECT * FROM transactions WHERE {where}
                ORDER BY transaction_date DESC, created_at DESC
                LIMIT %s OFFSET %s
            """, params + [page_size, offset])
            items = [dict(row) for row in cursor.fetchall()]

            return {"items": items, "total": total, "page": page, "page_size": page_size}

    def get_transaction_by_id(self, transaction_id: int) -> Optional[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute('SELECT * FROM transactions WHERE id = %s', (transaction_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_transaction(self, transaction_id: int, **kwargs):
        if not kwargs:
            return False
        set_clause = ', '.join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [transaction_id]
        with self.conn.cursor() as cursor:
            cursor.execute(f"UPDATE transactions SET {set_clause} WHERE id = %s", values)
            return cursor.rowcount > 0

    def delete_transaction(self, transaction_id: int):
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM transactions WHERE id = %s', (transaction_id,))
            return cursor.rowcount > 0

    def get_monthly_summary(self, year: int, month: int) -> Dict:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT transaction_type, category,
                       SUM(amount)::float AS total,
                       COUNT(*)::int AS count
                FROM transactions
                WHERE EXTRACT(YEAR FROM transaction_date) = %s
                  AND EXTRACT(MONTH FROM transaction_date) = %s
                GROUP BY transaction_type, category
                ORDER BY transaction_type, total DESC
            """, (year, month))
            rows = cursor.fetchall()

            total_income = 0.0
            total_expense = 0.0
            income_breakdown = []
            expense_breakdown = []

            for row in rows:
                d = dict(row)
                if d['transaction_type'] == 'income':
                    total_income += d['total']
                    income_breakdown.append(d)
                else:
                    total_expense += d['total']
                    expense_breakdown.append(d)

            return {
                "total_income": round(total_income, 2),
                "total_expense": round(total_expense, 2),
                "balance": round(total_income - total_expense, 2),
                "income_breakdown": income_breakdown,
                "expense_breakdown": expense_breakdown,
            }

    def get_monthly_trend(self, months: int = 6) -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    EXTRACT(YEAR FROM transaction_date)::int AS year,
                    EXTRACT(MONTH FROM transaction_date)::int AS month,
                    transaction_type,
                    SUM(amount)::float AS total
                FROM transactions
                WHERE transaction_date >= DATE_TRUNC('month', CURRENT_DATE) - (%s || ' months')::interval
                GROUP BY year, month, transaction_type
                ORDER BY year DESC, month DESC
            """, (str(months),))
            rows = cursor.fetchall()
            # 组织为按月份分组
            month_map = {}
            for row in rows:
                d = dict(row)
                key = f"{d['year']}-{d['month']:02d}"
                if key not in month_map:
                    month_map[key] = {"month": key, "year": d['year'], "month_num": d['month'], "income": 0, "expense": 0}
                if d['transaction_type'] == 'income':
                    month_map[key]["income"] = d['total']
                else:
                    month_map[key]["expense"] = d['total']
            return list(month_map.values())

    def add_wedding_item(self, item_type: str, title: str, description: str = "",
                         owner: str = "", planned_amount: float = 0, amount: float = 0, status: str = "todo",
                         item_date: str = "", family_id: str = "") -> int:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO wedding_items (family_id, item_type, title, description, owner, planned_amount, amount, status, item_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (family_id or "", item_type, title, description, owner, planned_amount, amount, status, item_date))
            return cursor.fetchone()["id"]

    def get_wedding_items(self, family_id: str = "") -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM wedding_items
                WHERE family_id = %s
                ORDER BY updated_at DESC, created_at DESC
            """, (family_id or "",))
            return [dict(row) for row in cursor.fetchall()]

    def update_wedding_item(self, item_id: int, family_id: str = "", **kwargs) -> bool:
        if not kwargs:
            return False
        set_clause = ", ".join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [item_id, family_id or ""]
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                UPDATE wedding_items
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND family_id = %s
            """, values)
            return cursor.rowcount > 0

    def delete_wedding_item(self, item_id: int, family_id: str = "") -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM wedding_items WHERE id = %s AND family_id = %s', (item_id, family_id or ""))
            return cursor.rowcount > 0

    def add_insurance_policy(self, name: str, holder: str = "", company: str = "",
                             coverage: str = "", premium: float = 0, amount: float = 0,
                             renew_date: str = "", status: str = "有效",
                             record_type: str = "policy", title: str = "",
                             note: str = "", family_id: str = "") -> int:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO insurance_policies (family_id, record_type, name, title, holder, company, coverage, premium, amount, renew_date, status, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (family_id or "", record_type, name, title, holder, company, coverage, premium, amount, renew_date, status, note))
            return cursor.fetchone()["id"]

    def get_insurance_policies(self, family_id: str = "") -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM insurance_policies
                WHERE family_id = %s
                ORDER BY updated_at DESC, created_at DESC
            """, (family_id or "",))
            return [dict(row) for row in cursor.fetchall()]

    def update_insurance_policy(self, policy_id: int, family_id: str = "", **kwargs) -> bool:
        if not kwargs:
            return False
        set_clause = ", ".join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [policy_id, family_id or ""]
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                UPDATE insurance_policies
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND family_id = %s
            """, values)
            return cursor.rowcount > 0

    def delete_insurance_policy(self, policy_id: int, family_id: str = "") -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM insurance_policies WHERE id = %s AND family_id = %s', (policy_id, family_id or ""))
            return cursor.rowcount > 0

    def add_document_record(self, doc_type: str, title: str, holder: str = "", number: str = "",
                            issuer: str = "", issue_date: str = "", expiry_date: str = "",
                            reminder_days: int = 30, status: str = "有效", note: str = "",
                            family_id: str = "") -> int:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO document_records (family_id, doc_type, title, holder, number, issuer, issue_date, expiry_date, reminder_days, status, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (family_id or "", doc_type, title, holder, number, issuer, issue_date, expiry_date, reminder_days, status, note))
            return cursor.fetchone()["id"]

    def get_document_records(self, family_id: str = "") -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM document_records
                WHERE family_id = %s
                ORDER BY updated_at DESC, created_at DESC
            """, (family_id or "",))
            return [dict(row) for row in cursor.fetchall()]

    def update_document_record(self, record_id: int, family_id: str = "", **kwargs) -> bool:
        if not kwargs:
            return False
        set_clause = ", ".join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [record_id, family_id or ""]
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                UPDATE document_records
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND family_id = %s
            """, values)
            return cursor.rowcount > 0

    def delete_document_record(self, record_id: int, family_id: str = "") -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM document_records WHERE id = %s AND family_id = %s', (record_id, family_id or ""))
            return cursor.rowcount > 0

    def add_vehicle_record(self, record_type: str, title: str, plate: str = "",
                           model: str = "", mileage: float = 0, amount: float = 0,
                           record_date: str = "", status: str = "", note: str = "",
                           family_id: str = "") -> int:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO vehicle_records (family_id, record_type, title, plate, model, mileage, amount, record_date, status, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (family_id or "", record_type, title, plate, model, mileage, amount, record_date, status, note))
            return cursor.fetchone()["id"]

    def get_vehicle_records(self, family_id: str = "") -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM vehicle_records
                WHERE family_id = %s
                ORDER BY updated_at DESC, created_at DESC
            """, (family_id or "",))
            return [dict(row) for row in cursor.fetchall()]

    def update_vehicle_record(self, record_id: int, family_id: str = "", **kwargs) -> bool:
        if not kwargs:
            return False
        set_clause = ", ".join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [record_id, family_id or ""]
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                UPDATE vehicle_records
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND family_id = %s
            """, values)
            return cursor.rowcount > 0

    def delete_vehicle_record(self, record_id: int, family_id: str = "") -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM vehicle_records WHERE id = %s AND family_id = %s', (record_id, family_id or ""))
            return cursor.rowcount > 0

    def add_fitness_record(self, record_type: str, title: str, record_date: str = "",
                           duration: float = 0, calories: float = 0, protein: float = 0, weight: float = 0,
                           body_fat: float = 0, waist: float = 0, status: str = "",
                           note: str = "", family_id: str = "") -> int:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO fitness_records (family_id, record_type, title, record_date, duration, calories, protein, weight, body_fat, waist, status, note)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (family_id or "", record_type, title, record_date, duration, calories, protein, weight, body_fat, waist, status, note))
            return cursor.fetchone()["id"]

    def get_fitness_records(self, family_id: str = "") -> List[Dict]:
        with self.conn.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM fitness_records
                WHERE family_id = %s
                ORDER BY updated_at DESC, created_at DESC
            """, (family_id or "",))
            return [dict(row) for row in cursor.fetchall()]

    def update_fitness_record(self, record_id: int, family_id: str = "", **kwargs) -> bool:
        if not kwargs:
            return False
        set_clause = ", ".join([f"{k} = %s" for k in kwargs])
        values = list(kwargs.values()) + [record_id, family_id or ""]
        with self.conn.cursor() as cursor:
            cursor.execute(f"""
                UPDATE fitness_records
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s AND family_id = %s
            """, values)
            return cursor.rowcount > 0

    def delete_fitness_record(self, record_id: int, family_id: str = "") -> bool:
        with self.conn.cursor() as cursor:
            cursor.execute('DELETE FROM fitness_records WHERE id = %s AND family_id = %s', (record_id, family_id or ""))
            return cursor.rowcount > 0
