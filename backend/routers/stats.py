"""
统计信息路由
"""
from fastapi import APIRouter

router = APIRouter()


def get_agent():
    from main import get_agent as _get_agent
    return _get_agent()


@router.get("/stats")
async def get_stats():
    """获取系统统计"""
    agent = get_agent()
    
    stats = {
        "members_count": len(agent.members),
        "reminders_count": len(agent.reminders),
        "shopping_items_count": len(agent.shopping_list.get_all()),
        "photos_count": len(agent.photo_memory.get_all()),
        "knowledge_docs_count": len(agent.knowledge_base.get_all()),
        "tasks_count": len(agent.task_manager.tasks),
    }
    
    return stats
