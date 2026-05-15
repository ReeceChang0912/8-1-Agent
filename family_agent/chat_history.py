"""
聊天历史记录管理 - PostgreSQL版
"""
from typing import List, Dict, Optional
from datetime import datetime


class ChatHistoryManager:
    """聊天历史管理器 - 使用 PostgreSQL"""

    def __init__(self, db_manager=None, data_dir: str = "data"):
        """
        初始化聊天历史管理器
        Args:
            db_manager: DatabaseManager 实例
            data_dir: 数据目录（兼容旧接口，实际不使用）
        """
        self.db = db_manager

    def create_session(self, user_id: str, title: str = None) -> Dict:
        if self.db:
            return self.db.create_chat_session(user_id, title)
        return {"session_id": "", "user_id": user_id, "title": title or "新对话"}

    def list_sessions(self, user_id: str, limit: int = 50) -> List[Dict]:
        if self.db:
            return self.db.list_chat_sessions(user_id, limit)
        return []

    def update_session_title(self, user_id: str, session_id: str, title: str) -> bool:
        if self.db:
            return self.db.update_chat_session_title(user_id, session_id, title)
        return False

    def archive_session(self, user_id: str, session_id: str) -> bool:
        if self.db:
            return self.db.archive_chat_session(user_id, session_id)
        return False

    def add_message(self, user_id: str, role: str, content: str, emotion: str = None,
                    session_id: str = None):
        """添加消息"""
        if self.db:
            self.db.add_chat_message(user_id, role, content, emotion, session_id=session_id)

    def get_history(self, user_id: str, limit: int = 50, session_id: str = None) -> List[Dict]:
        """获取用户聊天历史"""
        if self.db:
            return self.db.get_chat_history(user_id, limit, session_id=session_id)
        return []

    def clear_history(self, user_id: str, session_id: str = None):
        """清空用户聊天历史"""
        if self.db:
            self.db.clear_chat_history(user_id, session_id=session_id)

    def search_history(self, user_id: str, keyword: str) -> List[Dict]:
        """搜索聊天历史"""
        history = self.get_history(user_id, limit=1000)
        return [m for m in history if keyword.lower() in m.get('content', '').lower()]
