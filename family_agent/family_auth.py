"""
家庭认证系统 - PostgreSQL版
支持家庭号和成员管理
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import secrets
import json
from pathlib import Path


class FamilyAccount:
    """家庭账号（数据对象）"""
    
    def __init__(self, family_id: str, family_name: str = "我的家庭",
                 members: List[str] = None, settings: Dict = None):
        self.family_id = family_id
        self.family_name = family_name
        self.members = members or []
        self.settings = settings or {}

    def add_member(self, member_name: str):
        if member_name not in self.members:
            self.members.append(member_name)
    
    def remove_member(self, member_name: str):
        if member_name in self.members:
            self.members.remove(member_name)
    
    def to_dict(self) -> Dict:
        return {
            "family_id": self.family_id,
            "family_name": self.family_name,
            "members": self.members,
            "settings": self.settings
        }


class UserSession:
    """用户会话（数据对象）"""
    
    def __init__(self, session_id: str, member_name: str,
                 login_time: str = None, expires_at: str = None, is_active: bool = True):
        self.session_id = session_id
        self.member_name = member_name
        self.login_time = login_time or datetime.now().isoformat()
        self.expires_at = expires_at or (datetime.now() + timedelta(hours=24)).isoformat()
        self.is_active = is_active
    
    def is_expired(self) -> bool:
        return datetime.now() > datetime.fromisoformat(self.expires_at)


class FamilyAuthManager:
    """家庭认证管理器"""
    """
    家庭认证管理器
    
    功能：
    1. 创建/加入家庭
    2. 成员管理
    3. 登录/登出
    4. 会话管理
    """
    
    def __init__(self, db_manager=None, data_dir: str = "data"):
        """
        初始化认证管理器
        Args:
            db_manager: DatabaseManager 实例
            data_dir: 数据目录（兼容旧接口）
        """
        self.db = db_manager
        self.data_dir = Path(data_dir)

    def create_family(self, family_name: str, admin_name: str) -> Dict:
        """创建新家庭"""
        if not self.db:
            return {"success": False, "message": "数据库未初始化"}
        
        # 生成家庭号 (6位数字)
        family_id = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # 确保家庭号唯一
        while self.db.get_family(family_id):
            family_id = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # 创建家庭
        result = self.db.add_family(family_id, family_name, [admin_name])
        
        if result:
            # 初始化默认数据
            self.db.initialize_family_defaults(family_id, admin_name)
            
            return {
                "family_id": family_id,
                "family_name": family_name,
                "admin": admin_name,
                "message": f"✅ 家庭创建成功!\n家庭号: {family_id}\n已为您初始化默认数据（家庭成员、购物清单、日程安排）\n请分享给家人加入"
            }
        return {"success": False, "message": "创建家庭失败"}
    
    def join_family(self, family_id: str, member_name: str) -> Dict:
        """加入现有家庭"""
        if not self.db:
            return {"success": False, "message": "数据库未初始化"}
        
        family = self.db.get_family(family_id)
        if not family:
            return {"success": False, "message": "❌ 家庭号不存在"}
        
        result = self.db.add_family_member(family_id, member_name)
        if result:
            return {
                "success": True,
                "family_id": family_id,
                "family_name": family['family_name'],
                "member_name": member_name
            }
        return {"success": False, "message": "加入家庭失败"}
    
    def get_family_members(self, family_id: str) -> List[str]:
        """获取家庭成员列表"""
        family = self.db.get_family(family_id) if self.db else None
        return family['members'] if family else []
    
    def get_family_info(self, family_id: str) -> Optional[Dict]:
        """获取家庭信息"""
        return self.db.get_family(family_id) if self.db else None
    
    def login(self, member_name: str) -> Optional[Dict]:
        """用户登录"""
        if not self.db:
            return None
        
        # 生成会话ID
        session_id = secrets.token_urlsafe(32)
        expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
        
        self.db.create_session(session_id, member_name, expires_at)
        
        return {
            "session_id": session_id,
            "member_name": member_name,
            "login_time": datetime.now().isoformat(),
            "expires_at": expires_at
        }
    
    def logout(self, session_id: str) -> bool:
        """用户登出"""
        if self.db:
            self.db.delete_session(session_id)
            return True
        return False
    
    def verify_session(self, session_id: str) -> Optional[Dict]:
        """验证会话"""
        if not self.db:
            return None
        
        session = self.db.verify_session(session_id)
        return session
    
    def get_current_user(self, session_id: str) -> Optional[str]:
        """获取当前用户姓名"""
        session_info = self.verify_session(session_id)
        if session_info:
            return session_info["member_name"]
        return None
    
    def cleanup_expired_sessions(self):
        """清理过期会话"""
        if self.db:
            self.db.cleanup_expired_sessions()
    
    def get_active_sessions_count(self) -> int:
        """获取活跃会话数"""
        if not self.db:
            return 0
        with self.db.conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_active = TRUE")
            return cursor.fetchone()[0]

# 兼容别名
FamilyAuth = FamilyAuthManager
