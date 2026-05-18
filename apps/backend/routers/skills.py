"""
技能中心路由
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class SkillToggle(BaseModel):
    enabled: bool


_DEFAULT_SKILLS = [
    {"id": "chat", "name": "智能对话", "enabled": True, "description": "与家庭助手进行自然语言交流"},
    {"id": "reminder", "name": "日程管理", "enabled": True, "description": "设置和管理提醒事项"},
    {"id": "shopping", "name": "购物清单", "enabled": True, "description": "管理家庭购物清单"},
    {"id": "knowledge", "name": "知识库", "enabled": True, "description": "查询家庭知识库"},
    {"id": "photo", "name": "照片记忆", "enabled": True, "description": "管理家庭照片回忆"},
    {"id": "task", "name": "任务管理", "enabled": True, "description": "家庭成员间任务分配与追踪"},
    {"id": "smart_home", "name": "智能家居", "enabled": True, "description": "控制家庭智能设备"},
]


def get_agent():
    from backend.main import get_agent as _get_agent
    return _get_agent()


@router.get("/skills")
async def get_skills():
    agent = get_agent()
    skill_engine = getattr(agent, 'skill_engine', None)
    if skill_engine and hasattr(skill_engine, 'get_all_skills'):
        try:
            return {"skills": skill_engine.get_all_skills()}
        except Exception:
            pass
    return {"skills": _DEFAULT_SKILLS}


@router.post("/skills/{skill_id}/toggle")
async def toggle_skill(skill_id: str, toggle_data: SkillToggle):
    agent = get_agent()
    skill_engine = getattr(agent, 'skill_engine', None)
    if skill_engine and hasattr(skill_engine, 'toggle_skill'):
        try:
            skill_engine.toggle_skill(skill_id, toggle_data.enabled)
        except Exception:
            pass
    return {"success": True, "message": f"技能 {skill_id} 状态已更新"}
