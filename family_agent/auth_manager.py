"""
用户认证和会话管理
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import hashlib
import secrets
import json
from pathlib import Path


class UserSession:
    """用户会话"""
    
    def __init__(
        self,
        session_id: str,
        member_name: str,
        login_time: str = None,
        expires_at: str = None,
        is_active: bool = True
    ):
        self.session_id = session_id
        self.member_name = member_name
        self.login_time = login_time or datetime.now().isoformat()
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=24)).isoformat()
        self.is_active = is_active
    
    def is_expired(self) -> bool:
        """检查会话是否过期"""
        return datetime.now() > datetime.fromisoformat(self.expires_at)
    
    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "member_name": self.member_name,
            "login_time": self.login_time,
            "expires_at": self.expires_at,
            "is_active": self.is_active
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'UserSession':
        return UserSession(**data)


class AuthManager:
    """
    认证管理器
    
    功能:
    1. 用户登录/登出
    2. 会话管理
    3. Token验证
    """
    
    def __init__(self, data_file: str = "data/sessions.json"):
        self.data_file = Path(data_file)
        self.sessions: Dict[str, UserSession] = {}
        self._load_sessions()
    
    def login(self, member_name: str, password: str = None) -> Optional[Dict]:
        """
        用户登录
        
        Args:
            member_name: 成员姓名
            password: 密码(可选,简化版本可以不需要)
        
        Returns:
            会话信息或None
        """
        
        # 生成会话ID
        session_id = secrets.token_urlsafe(32)
        
        # 创建会话
        session = UserSession(
            session_id=session_id,
            member_name=member_name,
            login_time=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=24)).isoformat()
        )
        
        # 保存会话
        self.sessions[session_id] = session
        self._save_sessions()
        
        return {
            "session_id": session_id,
            "member_name": member_name,
            "login_time": session.login_time,
            "expires_at": session.expires_at
        }
    
    def logout(self, session_id: str) -> bool:
        """用户登出"""
        if session_id in self.sessions:
            self.sessions[session_id].is_active = False
            del self.sessions[session_id]
            self._save_sessions()
            return True
        return False
    
    def verify_session(self, session_id: str) -> Optional[Dict]:
        """
        验证会话
        
        Args:
            session_id: 会话ID
        
        Returns:
            会话信息或None
        """
        
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # 检查是否激活
        if not session.is_active:
            return None
        
        # 检查是否过期
        if session.is_expired():
            del self.sessions[session_id]
            self._save_sessions()
            return None
        
        return {
            "session_id": session.session_id,
            "member_name": session.member_name,
            "login_time": session.login_time,
            "expires_at": session.expires_at
        }
    
    def get_current_user(self, session_id: str) -> Optional[str]:
        """获取当前用户姓名"""
        session_info = self.verify_session(session_id)
        if session_info:
            return session_info["member_name"]
        return None
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        expired_ids = [
            sid for sid, session in self.sessions.items()
            if session.is_expired() or not session.is_active
        ]
        
        for sid in expired_ids:
            del self.sessions[sid]
        
        if expired_ids:
            self._save_sessions()
    
    def get_active_sessions_count(self) -> int:
        """获取活跃会话数"""
        return len([s for s in self.sessions.values() if s.is_active and not s.is_expired()])
    
    def _load_sessions(self):
        """加载会话数据"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sessions = {
                    sid: UserSession.from_dict(s) 
                    for sid, s in data.items()
                }
    
    def _save_sessions(self):
        """保存会话数据"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(
                {sid: s.to_dict() for sid, s in self.sessions.items()},
                f, ensure_ascii=False, indent=2
            )
