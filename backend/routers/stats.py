"""
统计信息路由
"""
from fastapi import APIRouter

router = APIRouter()


def get_agent():
    from backend.main import get_agent as _get_agent
    return _get_agent()


@router.get("/stats")
async def get_stats():
    agent = get_agent()
    shopping_items = []
    try:
        shopping_items = agent.shopping_list.get_items() or []
    except Exception:
        pass
    photos = []
    try:
        photos = list(agent.photo_memory.photos.values()) if agent.photo_memory.photos else []
    except Exception:
        pass
    stats = {
        "members_count": len(agent.members),
        "reminders_count": len(agent.reminders),
        "shopping_items_count": len(shopping_items),
        "photos_count": len(photos),
        "tasks_count": 0,
    }
    try:
        tasks = agent.task_manager.get_my_tasks("", "all") or []
        stats["tasks_count"] = len(tasks)
    except Exception:
        pass
    return stats
