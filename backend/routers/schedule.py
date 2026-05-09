"""
日程管理路由
"""
from fastapi import APIRouter
from datetime import datetime
from pydantic import BaseModel

from family_agent.schedule_recommender import SmartScheduleRecommender

router = APIRouter()


class ReminderCreate(BaseModel):
    date: str
    event: str


def get_agent():
    from backend.main import get_agent as _get_agent
    return _get_agent()


def get_recommender() -> SmartScheduleRecommender:
    from backend.main import get_db_manager
    return SmartScheduleRecommender(db_manager=get_db_manager())


@router.get("/reminders")
async def get_reminders():
    """获取所有日程"""
    agent = get_agent()
    return {"reminders": agent.reminders}


@router.post("/reminders", status_code=201)
async def add_reminder(reminder_data: ReminderCreate):
    """添加日程"""
    agent = get_agent()
    reminder_dict = reminder_data.model_dump()
    agent.reminders.append(reminder_dict)
    # 同时写入数据库
    if agent.db:
        try:
            agent.db.add_reminder(reminder_dict['date'], reminder_dict['event'])
        except Exception as e:
            print(f"保存日程到数据库失败: {e}")
    return {"success": True, "message": "日程已添加"}


@router.delete("/reminders/{reminder_id}")
async def remove_reminder(reminder_id: int):
    """删除日程"""
    agent = get_agent()
    agent.reminders = [r for r in agent.reminders if r.get('id') != reminder_id]
    if agent.db:
        try:
            agent.db.remove_reminder(reminder_id)
        except Exception as e:
            print(f"从数据库删除日程失败: {e}")
    return {"success": True, "message": "日程已删除"}


@router.get("/recommendations/{member_name}")
async def get_recommendations(member_name: str, date: str = None):
    """Get schedule recommendations"""
    recommender = get_recommender()
    date = date or datetime.now().strftime('%Y-%m-%d')
    suggestions = recommender.recommend_schedule(member_name, date)
    return {"recommendations": suggestions}


@router.get("/free-times/{member_name}")
async def get_free_times(member_name: str, date: str = None):
    """Get predicted free time slots"""
    recommender = get_recommender()
    date = date or datetime.now().strftime('%Y-%m-%d')
    free_times = recommender.predict_free_time(member_name, date)
    return {"free_times": free_times}
