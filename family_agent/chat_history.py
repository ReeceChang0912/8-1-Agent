"""
聊天历史记录管理
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class ChatHistoryManager:
    """聊天历史管理器"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.history_file = self.data_dir / "chat_history.json"
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 加载历史
        self.history: Dict[str, List[Dict]] = {}
        self._load_history()
    
    def _load_history(self):
        """加载聊天历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"加载聊天历史失败: {e}")
                self.history = {}
    
    def _save_history(self):
        """保存聊天历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存聊天历史失败: {e}")
    
    def add_message(self, user_id: str, role: str, content: str, emotion: Optional[str] = None):
        """添加消息"""
        if user_id not in self.history:
            self.history[user_id] = []
        
        message = {
            'role': role,
            'content': content,
            'emotion': emotion,
            'timestamp': datetime.now().isoformat()
        }
        
        self.history[user_id].append(message)
        
        # 限制每个用户最多保存500条消息
        if len(self.history[user_id]) > 500:
            self.history[user_id] = self.history[user_id][-500:]
        
        self._save_history()
    
    def get_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """获取用户聊天历史"""
        if user_id not in self.history:
            return []
        
        return self.history[user_id][-limit:]
    
    def clear_history(self, user_id: str):
        """清空用户聊天历史"""
        if user_id in self.history:
            del self.history[user_id]
            self._save_history()
    
    def search_history(self, user_id: str, keyword: str) -> List[Dict]:
        """搜索聊天历史"""
        if user_id not in self.history:
            return []
        
        results = []
        for msg in self.history[user_id]:
            if keyword.lower() in msg['content'].lower():
                results.append(msg)
        
        return results
