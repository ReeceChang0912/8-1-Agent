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

    def add_message(self, user_id: str, role: str, content: str, emotion: str = None):
        """添加消息"""
        if self.db:
            self.db.add_chat_message(user_id, role, content, emotion)

    def get_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取用户聊天历史"""
        if self.db:
            return self.db.get_chat_history(user_id, limit)
        return []

    def clear_history(self, user_id: str):
        """清空用户聊天历史"""
        if self.db:
            self.db.clear_chat_history(user_id)

    def search_history(self, user_id: str, keyword: str) -> List[Dict]:
        """搜索聊天历史"""
        history = self.get_history(user_id, limit=1000)
        return [m for m in history if keyword.lower() in m.get('content', '').lower()]
