"""
日程管理路由
"""
from fastapi import APIRouter
from datetime import datetime
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


from family_agent.schedule_recommender import SmartScheduleRecommender

@router.get("/recommendations/{member_name}")
async def get_recommendations(member_name: str, date: str = None):
    """Get schedule recommendations"""
    recommender = SmartScheduleRecommender()
    date = date or datetime.now().strftime('%Y-%m-%d')
    suggestions = recommender.recommend_schedule(member_name, date)
    return {"recommendations": suggestions}

@router.get("/free-times/{member_name}")
async def get_free_times(member_name: str, date: str = None):
    """Get predicted free time slots"""
    recommender = SmartScheduleRecommender()
    date = date or datetime.now().strftime('%Y-%m-%d')
    free_times = recommender.predict_free_time(member_name, date)
    return {"free_times": free_times}
