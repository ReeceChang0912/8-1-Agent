"""
任务管理路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class TaskCreate(BaseModel):
    from_member: str
    to_member: str
    content: str
    task_type: str = "general"
    priority: str = "normal"


def get_agent():
    from main import get_agent as _get_agent
    return _get_agent()


@router.get("/tasks/my")
async def get_my_tasks(member_name: str, status: str = "pending"):
    """获取我的任务"""
    agent = get_agent()
    tasks = agent.task_manager.get_my_tasks(member_name, status)
    return {"tasks": tasks}


@router.get("/tasks/unread-count")
async def get_unread_count(member_name: str):
    """获取未读任务数"""
    agent = get_agent()
    count = agent.task_manager.get_unread_count(member_name)
    return {"count": count}


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: str):
    """完成任务"""
    agent = get_agent()
    agent.task_manager.complete_task(task_id)
    return {"success": True, "message": "任务已完成"}
