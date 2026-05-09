"""
多角色管理与个性化交互系统 - PostgreSQL版
支持家庭成员身份识别、权限控制、交互风格切换
"""
import json
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass, field


class InteractionStyle(Enum):
    """交互风格"""
    CHILD = "child"           # 童趣、简单、鼓励
    ELDER = "elder"           # 耐心、尊重、慢语速
    PEER = "peer"             # 平等、直接
    FORMAL = "formal"         # 正式、礼貌


class PermissionLevel(Enum):
    """权限等级"""
    ADMIN = "admin"           # 完全控制（夫妻）
    MEMBER = "member"         # 普通成员
    GUEST = "guest"           # 访客（只读）
    CHILD = "child"           # 儿童（受限访问）


@dataclass
class FamilyMember:
    """家庭成员"""
    name: str
    role: str
    age: int
    side: str = "core"          # 男方/女方/核心
    interaction_style: InteractionStyle = InteractionStyle.PEER
    permission: PermissionLevel = PermissionLevel.MEMBER
    preferences: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "role": self.role,
            "age": self.age,
            "side": self.side,
            "interaction_style": self.interaction_style.value if hasattr(self.interaction_style, 'value') else str(self.interaction_style),
            "permission": self.permission.value if hasattr(self.permission, 'value') else str(self.permission),
            "preferences": self.preferences
        }

    @staticmethod
    def from_dict(data: Dict) -> 'FamilyMember':
        style_map = {e.value: e for e in InteractionStyle}
        perm_map = {e.value: e for e in PermissionLevel}
        return FamilyMember(
            name=data["name"],
            role=data["role"],
            age=data["age"],
            side=data.get("side", "core"),
            interaction_style=style_map.get(data.get("interaction_style", "peer"), InteractionStyle.PEER),
            permission=perm_map.get(data.get("permission", "member"), PermissionLevel.MEMBER),
            preferences=data.get("preferences", [])
        )

    def get_system_prompt(self) -> str:
        """生成针对该成员的系统提示词"""
        style = self.interaction_style.value if hasattr(self.interaction_style, 'value') else str(self.interaction_style)

        if style == "child":
            return f"你正在和 {self.name}（{self.age}岁）对话。用童趣、简单的语言，多用鼓励的话。"
        elif style == "elder":
            return f"你正在和 {self.name}（{self.age}岁）对话。请耐心、尊重，语速慢一点。"
        elif style == "formal":
            return f"你正在和 {self.name}（{self.age}岁的{self.role}）对话。请使用正式、礼貌的语气。"
        else:  # peer
            return f"你正在和 {self.name}（{self.age}岁的{self.role}）对话。可以平等、直接地交流。"


class RoleManager:
    """
    角色管理器

    功能：
    1. 家庭成员管理（增删改查）
    2. 用户身份识别
    3. 权限检查
    4. 个性化提示词生成
    5. 家庭关系树
    """

    def __init__(self, db_manager=None):
        """
        初始化角色管理器
        Args:
            db_manager: DatabaseManager 实例
        """
        self.db = db_manager
        self.members: Dict[str, FamilyMember] = {}
        self.current_user: Optional[FamilyMember] = None
        self._load_members()

    def _load_members(self):
        """从数据库加载成员"""
        if not self.db:
            return
        rows = self.db.get_all_members()
        for row in rows:
            member = FamilyMember(
                name=row['name'],
                role=row['role'],
                age=row['age'],
                side=row.get('side', 'core'),
                interaction_style=row.get('interaction_style', 'peer'),
                permission=row.get('permission', 'member'),
                preferences=json.loads(row['preferences']) if row.get('preferences') else []
            )
            self.members[member.name] = member

    def add_member(self, member: FamilyMember) -> bool:
        """添加成员"""
        if self.db:
            result = self.db.add_member(
                name=member.name,
                role=member.role,
                age=member.age,
                side=member.side,
                interaction_style=member.interaction_style.value if hasattr(member.interaction_style, 'value') else str(member.interaction_style),
                permission=member.permission.value if hasattr(member.permission, 'value') else str(member.permission),
                preferences=member.preferences
            )
            if result:
                self.members[member.name] = member
            return result
        return False

    def remove_member(self, name: str) -> bool:
        """移除成员"""
        if self.db:
            result = self.db.remove_member(name)
            if result and name in self.members:
                del self.members[name]
            return result
        return False

    def get_member(self, name: str) -> Optional[FamilyMember]:
        """获取成员"""
        if name in self.members:
            return self.members[name]
        if self.db:
            row = self.db.get_member(name)
            if row:
                member = FamilyMember(
                    name=row['name'],
                    role=row['role'],
                    age=row['age'],
                    side=row.get('side', 'core'),
                    interaction_style=row.get('interaction_style', 'peer'),
                    permission=row.get('permission', 'member'),
                    preferences=json.loads(row['preferences']) if row.get('preferences') else []
                )
                self.members[name] = member
                return member
        return None

    def identify_user(self, user_name: str) -> Optional[FamilyMember]:
        """识别当前用户"""
        member = self.get_member(user_name)
        if member:
            self.current_user = member
        return member

    def set_current_user(self, member_name: str) -> bool:
        """设置当前用户"""
        member = self.get_member(member_name)
        if member:
            self.current_user = member
            return True
        return False

    def check_permission(self, required_permission: PermissionLevel) -> bool:
        """检查当前用户权限"""
        if not self.current_user:
            return False

        level_map = {
            PermissionLevel.ADMIN: 3,
            PermissionLevel.MEMBER: 2,
            PermissionLevel.GUEST: 1,
            PermissionLevel.CHILD: 0
        }

        user_level = level_map.get(self.current_user.permission, 0)
        required_level = level_map.get(required_permission, 0)

        return user_level >= required_level

    def get_personalized_prompt(self) -> str:
        """获取当前用户的个性化提示词"""
        if self.current_user:
            return self.current_user.get_system_prompt()
        return "你是一个家庭智能助手。"

    def get_family_tree(self) -> Dict:
        """获取家庭关系树"""
        tree = {"core": [], "husband_side": [], "wife_side": []}

        for member in self.members.values():
            if member.side == "husband":
                tree["husband_side"].append(member.name)
            elif member.side == "wife":
                tree["wife_side"].append(member.name)
            else:
                tree["core"].append(member.name)

        return tree

    def update_member(self, name: str, **kwargs) -> bool:
        """更新成员信息"""
        if self.db:
            return self.db.update_member(name, **kwargs)
        return False
