"""
多角色管理与个性化交互系统
支持家庭成员身份识别、权限控制、交互风格切换
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


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
    """家庭成员档案"""
    name: str
    role: str                 # 爸爸、妈妈、爷爷、奶奶等
    age: int
    side: str = "core"       # core/husband_side/wife_side
    interaction_style: InteractionStyle = InteractionStyle.PEER
    permission: PermissionLevel = PermissionLevel.MEMBER
    
    # 个人偏好
    communication_preferences: Dict = field(default_factory=dict)
    
    # 识别信息
    wechat_id: str = ""
    voice_print_id: str = ""
    login_account: str = ""
    
    # 健康与禁忌
    health_notes: List[str] = field(default_factory=list)
    allergies: List[str] = field(default_factory=list)
    preferences: List[str] = field(default_factory=list)
    taboos: List[str] = field(default_factory=list)
    
    # 关系网络
    relationships: Dict[str, str] = field(default_factory=dict)
    
    def get_system_prompt(self) -> str:
        """生成针对该成员的System Prompt"""
        
        style_prompts = {
            InteractionStyle.CHILD: """
            你是一个亲切的AI助手，正在和一个孩子对话。
            - 使用简单、有趣的语言
            - 多用表情符号和鼓励的话语
            - 解释复杂概念时用比喻和故事
            - 保持积极正面，激发好奇心
            """,
            
            InteractionStyle.ELDER: """
            你是一个尊敬、耐心的AI助手，正在和长辈对话。
            - 使用尊称（您），语气恭敬
            - 语速放慢，表达清晰
            - 避免网络流行语和技术术语
            - 多关心健康和日常生活
            """,
            
            InteractionStyle.PEER: """
            你是一个友好、直接的AI助手，正在和平辈对话。
            - 使用自然、轻松的语气
            - 可以直接表达观点
            - 适当使用幽默
            - 高效解决问题
            """,
            
            InteractionStyle.FORMAL: """
            你是一个专业、正式的AI助手。
            - 使用礼貌、规范的语言
            - 提供结构化、准确的信息
            """
        }
        
        base_prompt = style_prompts.get(self.interaction_style, style_prompts[InteractionStyle.PEER])
        
        personal_info = f"""
        
        当前用户信息：
        - 姓名：{self.name}
        - 角色：{self.role}
        - 喜好：{', '.join(self.preferences) if self.preferences else '无'}
        - 禁忌：{', '.join(self.taboos) if self.taboos else '无'}
        - 健康注意：{', '.join(self.health_notes) if self.health_notes else '无'}
        
        请根据以上信息调整你的回答方式。
        """
        
        return base_prompt + personal_info


class RoleManager:
    """
    角色管理器
    
    功能：
    1. 家庭成员管理
    2. 身份识别（微信ID、声纹、账号）
    3. 权限控制
    4. 交互风格切换
    """
    
    def __init__(self, data_file: str = None):
        if data_file is None:
            import os
            if os.path.exists("D:/myAgent/data"):
                data_file = "D:/myAgent/data/members.json"
            else:
                data_file = "data/members.json"
        
        self.data_file = Path(data_file)
        self.members: Dict[str, FamilyMember] = {}
        self.current_user: Optional[FamilyMember] = None
        
        # 识别映射表
        self.wechat_to_member: Dict[str, str] = {}
        self.voice_to_member: Dict[str, str] = {}
        self.account_to_member: Dict[str, str] = {}
        
        self._load_members()
    
    def add_member(self, member: FamilyMember) -> bool:
        """添加家庭成员"""
        member_id = member.name
        
        self.members[member_id] = member
        
        # 建立识别映射
        if member.wechat_id:
            self.wechat_to_member[member.wechat_id] = member_id
        if member.voice_print_id:
            self.voice_to_member[member.voice_print_id] = member_id
        if member.login_account:
            self.account_to_member[member.login_account] = member_id
        
        self._save_members()
        return True
    
    def identify_user(
        self,
        wechat_id: str = None,
        voice_print: str = None,
        account: str = None
    ) -> Optional[FamilyMember]:
        """识别当前用户身份"""
        member_id = None
        
        if voice_print and voice_print in self.voice_to_member:
            member_id = self.voice_to_member[voice_print]
        elif wechat_id and wechat_id in self.wechat_to_member:
            member_id = self.wechat_to_member[wechat_id]
        elif account and account in self.account_to_member:
            member_id = self.account_to_member[account]
        
        if member_id and member_id in self.members:
            self.current_user = self.members[member_id]
            return self.current_user
        
        return None
    
    def set_current_user(self, member_name: str) -> bool:
        """手动设置当前用户"""
        if member_name in self.members:
            self.current_user = self.members[member_name]
            return True
        return False
    
    def check_permission(self, required_permission: PermissionLevel) -> bool:
        """检查当前用户权限"""
        if not self.current_user:
            return False
        
        permission_hierarchy = {
            PermissionLevel.GUEST: 0,
            PermissionLevel.CHILD: 1,
            PermissionLevel.MEMBER: 2,
            PermissionLevel.ADMIN: 3
        }
        
        user_level = permission_hierarchy.get(self.current_user.permission, 0)
        required_level = permission_hierarchy.get(required_permission, 0)
        
        return user_level >= required_level
    
    def get_personalized_prompt(self) -> str:
        """获取当前用户的个性化Prompt"""
        if not self.current_user:
            return "你是一个家庭助手，请用友好、专业的语气回答问题。"
        
        return self.current_user.get_system_prompt()
    
    def get_family_tree(self) -> Dict:
        """获取家庭关系树"""
        tree = {
            "core_family": [],
            "husband_side": [],
            "wife_side": []
        }
        
        for member in self.members.values():
            if member.side in tree:
                tree[member.side].append({
                    "name": member.name,
                    "role": member.role,
                    "relationships": member.relationships
                })
        
        return tree
    
    def _load_members(self):
        """加载成员数据"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                for member_id, member_data in data.items():
                    # 处理枚举类型
                    if 'interaction_style' in member_data:
                        member_data['interaction_style'] = InteractionStyle(member_data['interaction_style'])
                    if 'permission' in member_data:
                        member_data['permission'] = PermissionLevel(member_data['permission'])
                    
                    member = FamilyMember(**member_data)
                    self.members[member_id] = member
                    
                    # 重建映射
                    if member.wechat_id:
                        self.wechat_to_member[member.wechat_id] = member_id
                    if member.voice_print_id:
                        self.voice_to_member[member.voice_print_id] = member_id
                    if member.login_account:
                        self.account_to_member[member.login_account] = member_id
    
    def _save_members(self):
        """保存成员数据"""
        # 转换枚举为字符串
        data = {}
        for k, v in self.members.items():
            member_dict = v.__dict__.copy()
            member_dict['interaction_style'] = v.interaction_style.value
            member_dict['permission'] = v.permission.value
            data[k] = member_dict
        
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
