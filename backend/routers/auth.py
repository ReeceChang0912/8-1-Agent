"""
认证相关路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from family_agent.family_auth import FamilyAuthManager

router = APIRouter()

# 数据模型
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
    """懒加载认证管理器"""
    from main import get_auth_manager as _get_auth
    return _get_auth()


# ===== API 端点 =====

@router.post("/login")
async def login(request: LoginRequest):
    """用户登录"""
    auth = get_auth_manager()
    result = auth.login(request.family_id, request.member_name)
    
    if result:
        return {
            "success": True,
            "session_id": result['session_id'],
            "family_id": result['family_id'],
            "family_name": result['family_name'],
            "member_name": result['member_name'],
            "message": f"✅ 欢迎回来, {result['member_name']}!"
        }
    else:
        return {"success": False, "message": "❌ 家庭号或姓名不正确"}


@router.post("/create-family")
async def create_family(request: CreateFamilyRequest):
    """创建新家庭"""
    auth = get_auth_manager()
    result = auth.create_family(request.family_name, request.admin_name)
    
    # 自动登录
    login_result = auth.login(result['family_id'], request.admin_name)
    
    return {
        "success": True,
        **result,
        **login_result,
        "message": f"✅ 家庭 '{request.family_name}' 创建成功! 家庭号: {result['family_id']}"
    }


@router.post("/join-family")
async def join_family(request: JoinFamilyRequest):
    """加入现有家庭"""
    auth = get_auth_manager()
    
    if request.family_id not in auth.families:
        return {"success": False, "message": "❌ 家庭号不存在"}
    
    family = auth.families[request.family_id]
    
    if request.member_name in family.members:
        return {"success": False, "message": "⚠️ 该成员已在家庭中"}
    
    # 添加成员
    family.add_member(request.member_name)
    auth._save_families()
    
    # 自动登录
    login_result = auth.login(request.family_id, request.member_name)
    
    return {
        "success": True,
        **login_result,
        "message": f"✅ 成功加入家庭 '{family.family_name}'!"
    }


@router.get("/verify")
async def verify_session(session_id: str):
    """验证会话"""
    auth = get_auth_manager()
    session_info = auth.verify_session(session_id)
    
    if session_info:
        return {"valid": True, **session_info}
    else:
        return {"valid": False, "message": "会话已过期或无效"}


@router.post("/logout")
async def logout(session_id: str):
    """退出登录"""
    auth = get_auth_manager()
    auth.logout(session_id)
    return {"success": True, "message": "已退出登录"}


@router.get("/family-members")
async def get_family_members(family_id: str):
    """获取家庭成员列表"""
    auth = get_auth_manager()
    
    if family_id not in auth.families:
        raise HTTPException(status_code=404, detail="家庭不存在")
    
    family = auth.families[family_id]
    return {
        "family_id": family_id,
        "family_name": family.family_name,
        "members": family.members
    }
