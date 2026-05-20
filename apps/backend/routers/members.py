"""
Member management routes.
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import re

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

class MemberPhoneBind(BaseModel):
    family_id: str
    member_name: str
    phone_number: str
    openid: str = ""



def get_agent() -> FamilyAgentCore:
    from backend.main import get_agent as _get_agent
    return _get_agent()


def get_auth_manager():
    from backend.main import get_auth_manager as _get_auth
    return _get_auth()


def _split_member_refs(value) -> List[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    parts = re.split(r"[,，/|;、\s]+", text)
    return [part.strip() for part in parts if part.strip()]


def _matches_member(value, member_name: str) -> bool:
    if not member_name:
        return False
    return any(member_name.lower() == ref.lower() for ref in _split_member_refs(value))


@router.get("/members")
async def get_members():
    agent = get_agent()
    return {
        "members": [
            {
                "name": m.name,
                "role": m.role,
                "age": m.age,
                "side": m.side,
                "interaction_style": m.interaction_style.value if hasattr(m.interaction_style, "value") else str(m.interaction_style),
                "permission": m.permission.value if hasattr(m.permission, "value") else str(m.permission),
            }
            for m in agent.members.values()
        ]
    }


@router.get("/members/stats")
async def get_member_stats(family_id: str = ""):
    agent = get_agent()
    db = getattr(agent, "db", None)
    members = list(agent.members.values())

    shopping_items = []
    chore_items = []
    travel_items = []
    try:
        shopping_items = agent.shopping_list.get_items(family_id=family_id) or []
    except Exception:
        shopping_items = []
    if db:
        try:
            chore_items = db.get_chore_records(family_id=family_id) or []
        except Exception:
            chore_items = []
        try:
            travel_items = db.get_travel_records(family_id=family_id) or []
        except Exception:
            travel_items = []

    done_statuses = {"已完成", "已打卡", "已补录", "completed", "done", "finished"}
    member_rows = []
    for member in members:
        name = member.name
        member_shopping = [item for item in shopping_items if (item.get("added_by") or "") == name]
        member_chores = [item for item in chore_items if (item.get("assignee") or "") == name]
        member_travel = [item for item in travel_items if _matches_member(item.get("companion"), name)]

        try:
            task_stats = agent.task_manager.get_statistics(name, family_id=family_id) or {}
        except Exception:
            task_stats = {}

        sent_stats = task_stats.get("sent", {}) if isinstance(task_stats, dict) else {}
        received_stats = task_stats.get("received", {}) if isinstance(task_stats, dict) else {}
        points_total = sum(float(item.get("points") or 0) for item in member_chores)
        engagement_score = (
            len(member_shopping)
            + len(member_chores)
            + len(member_travel)
            + int(sent_stats.get("total") or 0)
            + int(received_stats.get("total") or 0)
        )

        member_rows.append({
            "name": name,
            "role": member.role,
            "age": member.age,
            "side": member.side,
            "interaction_style": member.interaction_style.value if hasattr(member.interaction_style, "value") else str(member.interaction_style),
            "permission": member.permission.value if hasattr(member.permission, "value") else str(member.permission),
            "shopping": {
                "added": len(member_shopping),
                "purchased": sum(1 for item in member_shopping if item.get("status") == "purchased"),
                "pending": sum(1 for item in member_shopping if item.get("status") != "purchased"),
                "favorites": sum(1 for item in member_shopping if item.get("is_favorite")),
                "restock": sum(1 for item in member_shopping if float(item.get("current_stock") or 0) <= float(item.get("restock_threshold") or 0)),
            },
            "chores": {
                "assigned": len(member_chores),
                "done": sum(1 for item in member_chores if item.get("status") in done_statuses),
                "points": round(points_total, 1),
            },
            "travel": {
                "participations": len(member_travel),
                "upcoming": sum(1 for item in member_travel if item.get("travel_date")),
            },
            "tasks": {
                "sent": int(sent_stats.get("total") or 0),
                "received": int(received_stats.get("total") or 0),
                "received_completed": int(received_stats.get("completed") or 0),
                "pending": int(received_stats.get("pending") or 0),
            },
            "engagement_score": engagement_score,
        })

    member_rows.sort(key=lambda item: (-item["engagement_score"], item["name"]))
    summary = {
        "member_count": len(members),
        "active_member_count": sum(1 for item in member_rows if item["engagement_score"] > 0),
        "shopping_items": len(shopping_items),
        "chore_items": len(chore_items),
        "travel_items": len(travel_items),
        "top_member": member_rows[0]["name"] if member_rows else "",
    }
    return {"summary": summary, "members": member_rows}


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
        preferences=member_data.preferences or [],
    )
    agent.add_member(member)

    if session_id and auth.db:
        current_user = auth.get_current_user(session_id)
        if current_user:
            session_info = auth.verify_session(session_id)
            if session_info:
                family_id = session_info.get("family_id", "")
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
async def export_data(format: str = "json"):
    manager = DataMigrationManager()
    file_path = manager.export_all(format=format)
    return FileResponse(file_path, filename=f"family_data_export.{format}")


@router.post("/import")
async def import_data(file: UploadFile = File(...), format: str = "json"):
    manager = DataMigrationManager()
    temp_path = f"data/temp_import.{format}"
    with open(temp_path, "wb") as f:
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
    return manager.create_invite(family_id, creator)


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

