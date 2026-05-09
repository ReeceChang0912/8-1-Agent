"""
认证相关路由 - PostgreSQL版
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from family_agent.family_auth import FamilyAuthManager
import traceback

router = APIRouter()

class LoginRequest(BaseModel):
    family_id: str
    member_name: str

class CreateFamilyRequest(BaseModel):
    family_name: str
    admin_name: str

class JoinFamilyRequest(BaseModel):
    family_id: str
    member_name: str


def get_auth_manager() -> FamilyAuthManager:
    from backend.main import get_auth_manager as _get_auth
    return _get_auth()


@router.post("/login")
async def login(request: LoginRequest):
    auth = get_auth_manager()
    if not auth:
        return {"success": False, "message": "❌ 数据库未连接，请检查 DATABASE_URL 配置"}
    if not auth.db:
        return {"success": False, "message": "❌ 数据库未连接，请检查 DATABASE_URL 配置"}
    family = auth.get_family_info(request.family_id)
    if not family:
        return {"success": False, "message": "❌ 家庭号不存在"}
    if request.member_name not in family.get('members', []):
        return {"success": False, "message": "❌ 该成员不在家庭中"}
    result = auth.login(request.member_name)
    if result:
        return {
            "success": True,
            "session_id": result['session_id'],
            "family_id": request.family_id,
            "family_name": family['family_name'],
            "member_name": result['member_name'],
            "message": f"✅ 欢迎回来, {result['member_name']}!"
        }
    else:
        return {"success": False, "message": "❌ 登录失败"}


@router.post("/create-family")
async def create_family(request: CreateFamilyRequest):
    auth = get_auth_manager()
    result = auth.create_family(request.family_name, request.admin_name)
    if not result.get('success', True):
        return result
    login_result = auth.login(request.admin_name)
    family_id = result['family_id']
    family = auth.get_family_info(family_id)
    return {
        "success": True,
        "family_id": family_id,
        "family_name": family['family_name'] if family else request.family_name,
        "session_id": login_result['session_id'] if login_result else None,
        "member_name": request.admin_name,
        "message": f"✅ 家庭 '{request.family_name}' 创建成功! 家庭号: {family_id}"
    }


@router.post("/join-family")
async def join_family(request: JoinFamilyRequest):
    auth = get_auth_manager()
    family = auth.get_family_info(request.family_id)
    if not family:
        return {"success": False, "message": "❌ 家庭号不存在"}
    if request.member_name in family.get('members', []):
        return {"success": False, "message": "⚠️ 该成员已在家庭中"}
    result = auth.db.add_family_member(request.family_id, request.member_name) if auth.db else False
    if not result:
        return {"success": False, "message": "❌ 添加成员失败"}
    login_result = auth.login(request.member_name)
    return {
        "success": True,
        "session_id": login_result['session_id'] if login_result else None,
        "family_id": request.family_id,
        "family_name": family['family_name'],
        "member_name": request.member_name,
        "message": f"✅ 成功加入家庭 '{family['family_name']}'!"
    }


@router.get("/verify")
async def verify_session(session_id: str):
    auth = get_auth_manager()
    session_info = auth.verify_session(session_id)
    if session_info:
        return {"valid": True, **session_info}
    else:
        return {"valid": False, "message": "会话已过期或无效"}


@router.post("/logout")
async def logout(session_id: str):
    auth = get_auth_manager()
    auth.logout(session_id)
    return {"success": True, "message": "已退出登录"}


@router.get("/family-members")
async def get_family_members(family_id: str):
    auth = get_auth_manager()
    family = auth.get_family_info(family_id)
    if not family:
        raise HTTPException(status_code=404, detail="家庭不存在")
    return {
        "family_id": family_id,
        "family_name": family.get('family_name', ''),
        "members": family.get('members', [])
    }
