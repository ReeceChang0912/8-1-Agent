"""
认证相关路由。
"""
import os
from datetime import datetime, timedelta
from typing import Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from family_agent.family_auth import FamilyAuthManager

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
    invite_code: Optional[str] = None


class WeChatLoginRequest(BaseModel):
    code: str
    family_id: Optional[str] = ""
    member_name: Optional[str] = ""


class PhoneLoginRequest(BaseModel):
    code: str
    family_id: str


class PhoneBindLoginRequest(BaseModel):
    code: str
    family_id: str
    member_name: str
    wechat_code: Optional[str] = ""


def get_auth_manager() -> FamilyAuthManager:
    from backend.main import get_auth_manager as _get_auth
    return _get_auth()


def _persist_login(auth: FamilyAuthManager, member_name: str, family_id: str = ""):
    family = auth.get_family_info(family_id) if family_id else None
    login_result = auth.login(member_name, family_id=family_id)
    return {
        "session_id": login_result["session_id"] if login_result else None,
        "family_id": family_id,
        "family_name": family["family_name"] if family else "",
        "member_name": member_name,
    }


def _wechat_jscode2session(code: str) -> dict:
    appid = os.getenv("WECHAT_APPID", "").strip()
    secret = os.getenv("WECHAT_APPSECRET", "").strip()
    if not appid or not secret:
        return {"success": False, "message": "缺少 WECHAT_APPID 或 WECHAT_APPSECRET 配置"}

    resp = requests.get(
        "https://api.weixin.qq.com/sns/jscode2session",
        params={
            "appid": appid,
            "secret": secret,
            "js_code": code,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    data = resp.json()
    if data.get("errcode"):
        return {"success": False, "message": data.get("errmsg", "微信登录失败"), "wechat": data}
    return {"success": True, "wechat": data}


def _wechat_phone_number(code: str) -> dict:
    appid = os.getenv("WECHAT_APPID", "").strip()
    secret = os.getenv("WECHAT_APPSECRET", "").strip()
    if not appid or not secret:
        return {"success": False, "message": "缺少 WECHAT_APPID 或 WECHAT_APPSECRET 配置"}

    token_resp = requests.get(
        "https://api.weixin.qq.com/cgi-bin/token",
        params={
            "grant_type": "client_credential",
            "appid": appid,
            "secret": secret,
        },
        timeout=10,
    )
    token_data = token_resp.json()
    if token_data.get("errcode"):
        return {"success": False, "message": token_data.get("errmsg", "获取微信 access_token 失败"), "wechat": token_data}

    access_token = token_data.get("access_token", "")
    if not access_token:
        return {"success": False, "message": "获取微信 access_token 失败", "wechat": token_data}

    phone_resp = requests.post(
        "https://api.weixin.qq.com/wxa/business/getuserphonenumber",
        params={"access_token": access_token},
        json={"code": code},
        timeout=10,
    )
    phone_data = phone_resp.json()
    if phone_data.get("errcode"):
        return {"success": False, "message": phone_data.get("errmsg", "获取手机号失败"), "wechat": phone_data}
    return {"success": True, "wechat": phone_data}


def _extract_phone_number(phone_result: dict) -> str:
    phone_data = phone_result.get("wechat", {}).get("phone_info", {})
    return phone_data.get("purePhoneNumber") or phone_data.get("phoneNumber") or ""


def _validate_family_member(auth: FamilyAuthManager, family_id: str, member_name: str) -> tuple[Optional[dict], Optional[dict]]:
    family = auth.get_family_info(family_id)
    if not family:
        return None, {"success": False, "message": "家庭号不存在"}
    if member_name not in family.get("members", []):
        return None, {"success": False, "message": "该成员不在家庭中，请先加入或邀请"}
    return family, None


@router.post("/login")
async def login(request: LoginRequest):
    auth = get_auth_manager()
    if not auth or not auth.db:
        return {"success": False, "message": "数据库未连接，请检查 DATABASE_URL 配置"}
    family, error = _validate_family_member(auth, request.family_id, request.member_name)
    if error:
        return error
    result = auth.login(request.member_name, family_id=request.family_id)
    if result:
        return {
            "success": True,
            "session_id": result["session_id"],
            "family_id": request.family_id,
            "family_name": family["family_name"] if family else "",
            "member_name": result["member_name"],
            "message": f"欢迎回来，{result['member_name']}!",
        }
    return {"success": False, "message": "登录失败"}


@router.post("/wechat-login")
async def wechat_login(request: WeChatLoginRequest):
    auth = get_auth_manager()
    if not auth or not auth.db:
        return {"success": False, "message": "数据库未连接，请检查 DATABASE_URL 配置"}

    member_name = request.member_name.strip()
    family_id = request.family_id.strip()
    if not member_name or not family_id:
        return {"success": False, "message": "缺少家庭号或成员名"}

    family, error = _validate_family_member(auth, family_id, member_name)
    if error:
        return error

    wechat_result = _wechat_jscode2session(request.code)
    if not wechat_result.get("success"):
        return wechat_result

    wechat_data = wechat_result["wechat"]
    login_payload = _persist_login(auth, member_name, family_id)
    binding = auth.db.upsert_wechat_binding(
        openid=wechat_data.get("openid", ""),
        unionid=wechat_data.get("unionid", ""),
        family_id=family_id,
        member_name=member_name,
        code=request.code,
        session_key=wechat_data.get("session_key", ""),
        session_id=login_payload.get("session_id", ""),
        expires_at=(datetime.now() + timedelta(hours=2)).isoformat(),
    )
    if wechat_data.get("openid"):
        auth.db.upsert_member_contact(
            family_id=family_id,
            member_name=member_name,
            openid=wechat_data.get("openid", ""),
        )
    return {
        "success": True,
        **login_payload,
        "family_name": family["family_name"] if family else login_payload.get("family_name", ""),
        "wechat_openid": wechat_data.get("openid", ""),
        "wechat_unionid": wechat_data.get("unionid", ""),
        "wechat_binding": binding,
    }


@router.post("/phone-login")
async def phone_login(request: PhoneLoginRequest):
    auth = get_auth_manager()
    if not auth or not auth.db:
        return {"success": False, "message": "数据库未连接，请检查 DATABASE_URL 配置"}

    family_id = request.family_id.strip()
    if not family_id:
        return {"success": False, "message": "缺少家庭号"}

    family = auth.get_family_info(family_id)
    if not family:
        return {"success": False, "message": "家庭号不存在"}

    phone_result = _wechat_phone_number(request.code)
    if not phone_result.get("success"):
        return phone_result

    phone_number = _extract_phone_number(phone_result)
    if not phone_number:
        return {"success": False, "message": "未获取到手机号"}

    contact = auth.db.get_member_contact_by_phone(family_id, phone_number)
    if not contact:
        return {
            "success": False,
            "need_bind": True,
            "message": "该手机号尚未绑定家庭成员，请填写成员名后完成绑定",
        }

    member_name = contact.get("member_name", "")
    login_payload = _persist_login(auth, member_name, family_id)
    auth.db.upsert_member_contact(
        family_id=family_id,
        member_name=member_name,
        phone_number=phone_number,
        openid=contact.get("openid", ""),
    )
    return {
        "success": True,
        **login_payload,
        "family_name": family["family_name"] if family else login_payload.get("family_name", ""),
        "phone_number": phone_number,
    }


@router.post("/phone-bind-login")
async def phone_bind_login(request: PhoneBindLoginRequest):
    auth = get_auth_manager()
    if not auth or not auth.db:
        return {"success": False, "message": "数据库未连接，请检查 DATABASE_URL 配置"}

    family_id = request.family_id.strip()
    member_name = request.member_name.strip()
    if not family_id or not member_name:
        return {"success": False, "message": "请填写家庭号和成员名"}

    family, error = _validate_family_member(auth, family_id, member_name)
    if error:
        return error

    phone_result = _wechat_phone_number(request.code)
    if not phone_result.get("success"):
        return phone_result

    phone_number = _extract_phone_number(phone_result)
    if not phone_number:
        return {"success": False, "message": "未获取到手机号"}

    existing = auth.db.get_member_contact_by_phone(family_id, phone_number)
    if existing and existing.get("member_name") and existing.get("member_name") != member_name:
        return {
            "success": False,
            "message": f"该手机号已绑定成员 {existing.get('member_name')}，请确认家庭成员身份",
        }

    openid = ""
    unionid = ""
    session_key = ""
    if request.wechat_code:
        wechat_result = _wechat_jscode2session(request.wechat_code)
        if wechat_result.get("success"):
            wechat_data = wechat_result["wechat"]
            openid = wechat_data.get("openid", "")
            unionid = wechat_data.get("unionid", "")
            session_key = wechat_data.get("session_key", "")

    login_payload = _persist_login(auth, member_name, family_id)
    contact = auth.db.upsert_member_contact(
        family_id=family_id,
        member_name=member_name,
        phone_number=phone_number,
        openid=openid,
    )

    binding = None
    if openid:
        binding = auth.db.upsert_wechat_binding(
            openid=openid,
            unionid=unionid,
            family_id=family_id,
            member_name=member_name,
            code=request.wechat_code,
            session_key=session_key,
            session_id=login_payload.get("session_id", ""),
            expires_at=(datetime.now() + timedelta(hours=2)).isoformat(),
        )

    return {
        "success": True,
        **login_payload,
        "family_name": family["family_name"] if family else login_payload.get("family_name", ""),
        "phone_number": phone_number,
        "member_contact": contact,
        "wechat_openid": openid,
        "wechat_unionid": unionid,
        "wechat_binding": binding,
        "message": "手机号已绑定并登录",
    }


@router.post("/create-family")
async def create_family(request: CreateFamilyRequest):
    auth = get_auth_manager()
    result = auth.create_family(request.family_name, request.admin_name)
    if not result.get("success", True):
        return result
    family_id = result["family_id"]
    login_result = auth.login(request.admin_name, family_id=family_id)
    family = auth.get_family_info(family_id)
    return {
        "success": True,
        "family_id": family_id,
        "family_name": family["family_name"] if family else request.family_name,
        "session_id": login_result["session_id"] if login_result else None,
        "member_name": request.admin_name,
        "message": f"家庭 '{request.family_name}' 创建成功! 家庭号: {family_id}",
    }


@router.post("/join-family")
async def join_family(request: JoinFamilyRequest):
    auth = get_auth_manager()
    invite_family_id = request.family_id
    if request.invite_code:
        from backend.routers.members import get_invite_manager

        invite = get_invite_manager().validate_invite(request.invite_code)
        if not invite:
            return {"success": False, "message": "邀请码无效或已过期"}
        invite_family_id = invite.get("family_id") or request.family_id

    family = auth.get_family_info(invite_family_id)
    if not family:
        return {"success": False, "message": "家庭号不存在"}
    if request.member_name in family.get("members", []):
        return {"success": False, "message": "该成员已在家庭中"}
    result = auth.db.add_family_member(invite_family_id, request.member_name) if auth.db else False
    if not result:
        return {"success": False, "message": "添加成员失败"}
    login_result = auth.login(request.member_name, family_id=invite_family_id)
    if request.invite_code:
        from backend.routers.members import get_invite_manager

        get_invite_manager().mark_used(request.invite_code)
    return {
        "success": True,
        "session_id": login_result["session_id"] if login_result else None,
        "family_id": invite_family_id,
        "family_name": family["family_name"],
        "member_name": request.member_name,
        "message": f"成功加入家庭 '{family['family_name']}'!",
    }


@router.get("/verify")
async def verify_session(session_id: str):
    auth = get_auth_manager()
    session_info = auth.verify_session(session_id)
    if session_info:
        return {"valid": True, **session_info}
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
        "family_name": family.get("family_name", ""),
        "members": family.get("members", []),
    }
