"""
成员管理路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from family_agent.core import FamilyAgentCore
from family_agent.role_manager import FamilyMember, InteractionStyle, PermissionLevel

router = APIRouter()

class MemberCreate(BaseModel):
    name: str
    role: str
    age: int
    side: str = "core"
    interaction_style: str = "peer"
    permission: str = "member"
    preferences: Optional[List[str]] = []


def get_agent() -> FamilyAgentCore:
    from main import get_agent as _get_agent
    return _get_agent()


def get_auth_manager():
    from main import get_auth_manager as _get_auth
    return _get_auth()


@router.get("/members")
async def get_members():
    """获取所有成员"""
    agent = get_agent()
    members_list = [
        {
            "name": m.name,
            "role": m.role,
            "age": m.age,
            "side": m.side,
            "interaction_style": m.interaction_style.value if hasattr(m.interaction_style, 'value') else str(m.interaction_style),
            "permission": m.permission.value if hasattr(m.permission, 'value') else str(m.permission),
        }
        for m in agent.members.values()
    ]
    return members_list


@router.post("/members", status_code=201)
async def add_member(member_data: MemberCreate, session_id: str = None):
    """添加成员"""
    agent = get_agent()
    auth = get_auth_manager()
    
    if member_data.name in agent.members:
        raise HTTPException(status_code=400, detail="成员已存在")
    
    # 映射字符串到枚举
    style_map = {
        "peer": InteractionStyle.PEER,
        "elder": InteractionStyle.ELDER,
        "junior": InteractionStyle.JUNIOR,
    }
    perm_map = {
        "admin": PermissionLevel.ADMIN,
        "member": PermissionLevel.MEMBER,
        "guest": PermissionLevel.GUEST,
    }
    
    member = FamilyMember(
        name=member_data.name,
        role=member_data.role,
        age=member_data.age,
        side=member_data.side,
        interaction_style=style_map.get(member_data.interaction_style, InteractionStyle.PEER),
        permission=perm_map.get(member_data.permission, PermissionLevel.MEMBER),
        preferences=member_data.preferences or []
    )
    
    agent.add_member(member)
    
    # 同步到认证系统
    if session_id:
        current_user = auth.get_current_user(session_id)
        if current_user:
            session_info = auth.verify_session(session_id)
            if session_info:
                family_id = session_info['family_id']
                if family_id in auth.families:
                    auth.families[family_id].add_member(member_data.name)
                    auth._save_families()
    
    return {"success": True, "message": f"成员 {member_data.name} 添加成功"}


@router.delete("/members/{name}")
async def remove_member(name: str):
    """删除成员"""
    agent = get_agent()
    if name not in agent.members:
        raise HTTPException(status_code=404, detail="成员不存在")
    
    agent.remove_member(name)
    return {"success": True, "message": f"成员 {name} 已删除"}


from fastapi import UploadFile, File
from family_agent.data_migration import DataMigrationManager

@router.get("/export")
async def export_data(format: str = 'json'):
    """Export all data"""
    manager = DataMigrationManager()
    file_path = manager.export_all(format=format)
    return FileResponse(file_path, filename=f"family_data_export.{format}")

@router.post("/import")
async def import_data(file: UploadFile = File(...), format: str = 'json'):
    """Import data from file"""
    manager = DataMigrationManager()
    # Save uploaded file
    temp_path = f"data/temp_import.{format}"
    with open(temp_path, 'wb') as f:
        f.write(await file.read())
    # Import
    success = manager.import_all(temp_path, format=format)
    # Clean up
    Path(temp_path).unlink(missing_ok=True)
    return {"success": success}
