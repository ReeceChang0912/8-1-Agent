"""
日程管理路由
"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ReminderCreate(BaseModel):
    date: str
    event: str


def get_agent():
    from main import get_agent as _get_agent
    return _get_agent()


@router.get("/reminders")
async def get_reminders():
    """获取所有日程"""
    agent = get_agent()
    return agent.reminders


@router.post("/reminders", status_code=201)
async def add_reminder(reminder_data: ReminderCreate):
    """添加日程"""
    agent = get_agent()
    agent.reminders.append(reminder_data.dict())
    agent._save_reminders()
    return {"success": True, "message": "日程已添加"}
