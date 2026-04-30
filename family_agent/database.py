"""
SQLite 数据库管理器
替代JSON文件存储,提供并发安全和数据完整性
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json


class DatabaseManager:
    """SQLite数据库管理器"""
    
    def __init__(self, db_path: str = "data/family_agent.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        """初始化数据库表"""
        cursor = self.conn.cursor()
        
        # 家庭成员表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                age INTEGER NOT NULL,
                side TEXT DEFAULT 'core',
                interaction_style TEXT DEFAULT 'peer',
                permission TEXT DEFAULT 'member',
                preferences TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 购物清单项表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS shopping_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity TEXT DEFAULT '1',
                category TEXT DEFAULT 'general',
                priority TEXT DEFAULT 'normal',
                status TEXT DEFAULT 'pending',
                added_by TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 日程表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                event TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 聊天历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                emotion TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 任务表
        cursor.execute('''
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
        ''')
        
        self.conn.commit()
    
    # ===== 成员管理 =====
    
    def add_member(self, name: str, role: str, age: int, side: str = 'core',
                   interaction_style: str = 'peer', permission: str = 'member',
                   preferences: List[str] = None):
        """添加成员"""
        cursor = self.conn.cursor()
        prefs = json.dumps(preferences or [])
        try:
            cursor.execute('''
                INSERT INTO members (name, role, age, side, interaction_style, permission, preferences)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, role, age, side, interaction_style, permission, prefs))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False  # 成员已存在
    
    def get_all_members(self) -> List[Dict]:
        """获取所有成员"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM members ORDER BY created_at')
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def remove_member(self, name: str):
        """删除成员"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM members WHERE name = ?', (name,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # ===== 购物清单 =====
    
    def add_shopping_item(self, name: str, quantity: str = '1', category: str = 'general',
                          priority: str = 'normal', added_by: str = ''):
        """添加购物项"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO shopping_items (name, quantity, category, priority, added_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, quantity, category, priority, added_by))
        self.conn.commit()
    
    def get_all_shopping_items(self, status: str = 'pending') -> List[Dict]:
        """获取购物项"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM shopping_items WHERE status = ? ORDER BY created_at', (status,))
        return [dict(row) for row in cursor.fetchall()]
    
    def remove_shopping_item(self, name: str):
        """删除购物项"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM shopping_items WHERE name = ?', (name,))
        self.conn.commit()
    
    # ===== 日程管理 =====
    
    def add_reminder(self, date: str, event: str):
        """添加日程"""
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO reminders (date, event) VALUES (?, ?)', (date, event))
        self.conn.commit()
    
    def get_all_reminders(self) -> List[Dict]:
        """获取所有日程"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM reminders ORDER BY date')
        return [dict(row) for row in cursor.fetchall()]
    
    # ===== 聊天历史 =====
    
    def add_chat_message(self, user_id: str, role: str, content: str, emotion: str = None):
        """添加聊天消息"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO chat_history (user_id, role, content, emotion)
            VALUES (?, ?, ?, ?)
        ''', (user_id, role, content, emotion))
        self.conn.commit()
    
    def get_chat_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取聊天历史"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM chat_history 
            WHERE user_id = ? 
            ORDER BY timestamp ASC 
            LIMIT ?
        ''', (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]
    
    def clear_chat_history(self, user_id: str):
        """清空聊天历史"""
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    # ===== 任务管理 =====
    
    def add_task(self, task_id: str, from_member: str, to_member: str, content: str,
                 task_type: str = 'general', priority: str = 'normal'):
        """添加任务"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO tasks (id, from_member, to_member, content, task_type, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_id, from_member, to_member, content, task_type, priority))
        self.conn.commit()
    
    def get_my_tasks(self, member_name: str, status: str = 'pending') -> List[Dict]:
        """获取我的任务"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM tasks 
            WHERE to_member = ? AND status = ? 
            ORDER BY created_at DESC
        ''', (member_name, status))
        return [dict(row) for row in cursor.fetchall()]
    
    def complete_task(self, task_id: str):
        """完成任务"""
        cursor = self.conn.cursor()
        cursor.execute('''
            UPDATE tasks 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (task_id,))
        self.conn.commit()
    
    # ===== 统计 =====
    
    def get_stats(self) -> Dict:
        """获取统计数据"""
        cursor = self.conn.cursor()
        
        stats = {}
        
        cursor.execute('SELECT COUNT(*) FROM members')
        stats['members_count'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM reminders')
        stats['reminders_count'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM shopping_items WHERE status = 'pending'")
        stats['shopping_items_count'] = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM chat_history')
        stats['chat_messages_count'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tasks WHERE status = 'pending'")
        stats['tasks_count'] = cursor.fetchone()[0]
        
        return stats
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
