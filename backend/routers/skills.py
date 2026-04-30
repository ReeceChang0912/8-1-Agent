"""
技能中心路由
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class SkillToggle(BaseModel):
    enabled: bool


def get_agent():
    from main import get_agent as _get_agent
    return _get_agent()


@router.get("/skills")
async def get_skills():
    """获取技能列表"""
    agent = get_agent()
    skills = agent.skill_engine.get_all_skills()
    return {"skills": skills}


@router.post("/skills/{skill_id}/toggle")
async def toggle_skill(skill_id: str, toggle_data: SkillToggle):
    """启用/禁用技能"""
    agent = get_agent()
    agent.skill_engine.toggle_skill(skill_id, toggle_data.enabled)
    return {"success": True, "message": f"技能已{'启用' if toggle_data.enabled else '禁用'}"}
