"""
成员管理路由
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path

from family_agent.core import FamilyAgentCore
from family_agent.role_manager import FamilyMember, InteractionStyle, PermissionLevel
from family_agent.data_migration import DataMigrationManager
from family_agent.invite_manager import InviteManager

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
    from backend.main import get_agent as _get_agent
    return _get_agent()


def get_auth_manager():
    from backend.main import get_auth_manager as _get_auth
    return _get_auth()


@router.get("/members")
async def get_members():
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
    return {"members": members_list}


@router.post("/members", status_code=201)
async def add_member(member_data: MemberCreate, session_id: str = None):
    agent = get_agent()
    auth = get_auth_manager()

    if member_data.name in agent.members:
        raise HTTPException(status_code=400, detail="成员已存在")

    style_map = {
        "peer": InteractionStyle.PEER,
        "elder": InteractionStyle.ELDER,
        "child": InteractionStyle.CHILD,
        "formal": InteractionStyle.FORMAL,
    }
    perm_map = {
        "admin": PermissionLevel.ADMIN,
        "member": PermissionLevel.MEMBER,
        "guest": PermissionLevel.GUEST,
        "child": PermissionLevel.CHILD,
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

    if session_id and auth.db:
        current_user = auth.get_current_user(session_id)
        if current_user:
            session_info = auth.verify_session(session_id)
            if session_info:
                family_id = session_info.get('family_id', '')
                if family_id:
                    auth.db.add_family_member(family_id, member_data.name)

    return {"success": True, "message": f"成员 {member_data.name} 添加成功"}


@router.delete("/members/{name}")
async def remove_member(name: str):
    agent = get_agent()
    if name not in agent.members:
        raise HTTPException(status_code=404, detail="成员不存在")
    agent.remove_member(name)
    return {"success": True, "message": f"成员 {name} 已删除"}


@router.put("/members/{name}")
async def update_member(name: str, data: MemberCreate):
    agent = get_agent()
    if name not in agent.members:
        raise HTTPException(status_code=404, detail="成员不存在")
    agent.update_member(
        name=name,
        role=data.role,
        age=data.age,
        side=data.side,
        interaction_style=data.interaction_style,
        permission=data.permission,
    )
    return {"success": True, "message": f"成员 {name} 已更新"}


@router.get("/export")
async def export_data(format: str = 'json'):
    manager = DataMigrationManager()
    file_path = manager.export_all(format=format)
    return FileResponse(file_path, filename=f"family_data_export.{format}")


@router.post("/import")
async def import_data(file: UploadFile = File(...), format: str = 'json'):
    manager = DataMigrationManager()
    temp_path = f"data/temp_import.{format}"
    with open(temp_path, 'wb') as f:
        f.write(await file.read())
    success = manager.import_all(temp_path, format=format)
    Path(temp_path).unlink(missing_ok=True)
    return {"success": success}


def get_invite_manager() -> InviteManager:
    from backend.main import get_db_manager
    return InviteManager(db_manager=get_db_manager())


@router.post("/invite/create")
async def create_invite(family_id: str, creator: str):
    manager = get_invite_manager()
    invite = manager.create_invite(family_id, creator)
    return invite


@router.get("/invite/{code}")
async def validate_invite(code: str):
    manager = get_invite_manager()
    invite = manager.validate_invite(code)
    if invite:
        return {"valid": True, "invite": invite}
    return {"valid": False}


@router.get("/invite/{code}/qrcode")
async def get_qr_code(code: str):
    manager = get_invite_manager()
    qr_path = manager.generate_qr_code(code)
    if qr_path:
        return FileResponse(qr_path)
    return {"error": "Failed to generate QR code"}
