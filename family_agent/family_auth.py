"""
家庭认证系统
支持家庭号和成员管理
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
import secrets
import json
from pathlib import Path
from .audit_logger import AuditLogger


class FamilyAccount:
    """家庭账号"""
    
    def __init__(
        self,
        family_id: str,
        family_name: str = "我的家庭",
        created_at: str = None,
        members: List[str] = None,
        settings: Dict = None
    ):
        self.family_id = family_id
        self.family_name = family_name
        self.created_at = created_at or datetime.now().isoformat()
        self.members = members or []  # 成员姓名列表
        self.settings = settings or {}
    
    def add_member(self, member_name: str):
        """添加成员"""
        if member_name not in self.members:
            self.members.append(member_name)
    
    def remove_member(self, member_name: str):
        """移除成员"""
        if member_name in self.members:
            self.members.remove(member_name)
    
    def to_dict(self) -> Dict:
        return {
            "family_id": self.family_id,
            "family_name": self.family_name,
            "created_at": self.created_at,
            "members": self.members,
            "settings": self.settings
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'FamilyAccount':
        return FamilyAccount(**data)


class UserSession:
    """用户会话"""
    
    def __init__(
        self,
        session_id: str,
        family_id: str,
        member_name: str,
        login_time: str = None,
        expires_at: str = None,
        is_active: bool = True
    ):
        self.session_id = session_id
        self.family_id = family_id
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
            "family_id": self.family_id,
            "member_name": self.member_name,
            "login_time": self.login_time,
            "expires_at": self.expires_at,
            "is_active": self.is_active
        }
    
    @staticmethod
    def from_dict(data: Dict) -> 'UserSession':
        return UserSession(**data)


class FamilyAuthManager:
    """
    家庭认证管理器
    
    功能:
    1. 创建/加入家庭
    2. 成员管理
    3. 登录/登出
    4. 会话管理
    """
    
    def __init__(
        self,
        families_file: str = "data/families.json",
        sessions_file: str = "data/sessions.json",
        data_dir: str = "data"
    ):
        self.families_file = Path(families_file)
        self.sessions_file = Path(sessions_file)
        
        self.families: Dict[str, FamilyAccount] = {}
        self.sessions: Dict[str, UserSession] = {}
        self.audit_logger = AuditLogger(data_dir=data_dir)
        
        self._load_data()
    
    def create_family(self, family_name: str, admin_name: str) -> Dict:
        """
        创建新家庭
        
        Args:
            family_name: 家庭名称
            admin_name: 管理员姓名
        
        Returns:
            家庭信息
        """
        
        # 生成家庭号 (6位数字)
        family_id = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # 确保家庭号唯一
        while family_id in self.families:
            family_id = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # 创建家庭
        family = FamilyAccount(
            family_id=family_id,
            family_name=family_name,
            members=[admin_name]
        )
        
        self.families[family_id] = family
        self._save_families()
        
        # 记录审计日志
        self.audit_logger.log_action(
            user_id=admin_name,
            action='create',
            resource_type='family',
            resource_id=family_id,
            details=f'创建家庭: {family_name}',
            success=True
        )
        
        return {
            "family_id": family_id,
            "family_name": family_name,
            "admin": admin_name,
            "message": f"✅ 家庭创建成功!\n家庭号: {family_id}\n请分享给家人加入"
        }
    
    def join_family(self, family_id: str, member_name: str) -> Dict:
        """
        加入现有家庭
        
        Args:
            family_id: 家庭号
            member_name: 成员姓名
        
        Returns:
            加入结果
        """
        
        if family_id not in self.families:
            return {"success": False, "message": "❌ 家庭号不存在"}
        
        family = self.families[family_id]
        
        # 添加成员
        family.add_member(member_name)
        self._save_families()
        
        # 记录审计日志
        self.audit_logger.log_action(
            user_id=member_name,
            action='create',
            resource_type='member',
            resource_id=family_id,
            details=f'加入家庭: {family.family_name}',
            success=True
        )
        
        return {
            "success": True,
            "family_id": family_id,
            "family_name": family.family_name,
            "member_name": member_name,
            "message": f"✅ 成功加入 {family.family_name}!"
        }
    
    def login(self, family_id: str, member_name: str) -> Optional[Dict]:
        """
        用户登录
        
        Args:
            family_id: 家庭号
            member_name: 成员姓名
        
        Returns:
            会话信息或None
        """
        
        # 验证家庭是否存在
        if family_id not in self.families:
            return None
        
        family = self.families[family_id]
        
        # 验证成员是否属于该家庭
        if member_name not in family.members:
            return None
        
        # 生成会话ID
        session_id = secrets.token_urlsafe(32)
        
        # 创建会话
        session = UserSession(
            session_id=session_id,
            family_id=family_id,
            member_name=member_name,
            login_time=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(hours=24)).isoformat()
        )
        
        # 保存会话
        self.sessions[session_id] = session
        self._save_sessions()
        
        # 记录审计日志
        self.audit_logger.log_action(
            user_id=member_name,
            action='login',
            resource_type='session',
            resource_id=session_id,
            details=f'登录家庭: {family.family_name}',
            success=True
        )
        
        return {
            "session_id": session_id,
            "family_id": family_id,
            "family_name": family.family_name,
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
        
        # 获取家庭信息
        family = self.families.get(session.family_id)
        
        return {
            "session_id": session.session_id,
            "family_id": session.family_id,
            "family_name": family.family_name if family else "未知家庭",
            "member_name": session.member_name,
            "login_time": session.login_time,
            "expires_at": session.expires_at
        }
    
    def get_family_members(self, family_id: str) -> List[str]:
        """获取家庭成员列表"""
        if family_id in self.families:
            return self.families[family_id].members
        return []
    
    def get_family_info(self, family_id: str) -> Optional[Dict]:
        """获取家庭信息"""
        if family_id in self.families:
            family = self.families[family_id]
            return {
                "family_id": family.family_id,
                "family_name": family.family_name,
                "members": family.members,
                "created_at": family.created_at
            }
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
    
    def _load_data(self):
        """加载数据"""
        # 加载家庭数据
        if self.families_file.exists():
            with open(self.families_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.families = {
                    fid: FamilyAccount.from_dict(f) 
                    for fid, f in data.items()
                }
        
        # 加载会话数据
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.sessions = {
                    sid: UserSession.from_dict(s) 
                    for sid, s in data.items()
                }
    
    def _save_families(self):
        """保存家庭数据"""
        self.families_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.families_file, 'w', encoding='utf-8') as f:
            json.dump(
                {fid: f.to_dict() for fid, f in self.families.items()},
                f, ensure_ascii=False, indent=2
            )
    
    def _save_sessions(self):
        """保存会话数据"""
        self.sessions_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(
                {sid: s.to_dict() for sid, s in self.sessions.items()},
                f, ensure_ascii=False, indent=2
            )
