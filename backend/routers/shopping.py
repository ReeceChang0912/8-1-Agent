"""
购物清单路由
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ShoppingItemCreate(BaseModel):
    name: str
    quantity: str = "1"
    category: str = "general"
    priority: str = "normal"


def get_agent():
    from main import get_agent as _get_agent
    return _get_agent()


@router.get("/shopping")
async def get_shopping_list():
    """获取购物清单"""
    agent = get_agent()
    items = agent.shopping_list.get_all()
    return [{"name": i.name, "quantity": i.quantity, "category": i.category, 
             "priority": i.priority, "added_by": i.added_by, "status": i.status}
            for i in items]


@router.post("/shopping", status_code=201)
async def add_shopping_item(item_data: ShoppingItemCreate):
    """添加购物项"""
    agent = get_agent()
    agent.shopping_list.add_item(
        name=item_data.name,
        quantity=item_data.quantity,
        category=item_data.category,
        priority=item_data.priority
    )
    return {"success": True, "message": f"已添加: {item_data.name}"}


@router.delete("/shopping/{name}")
async def remove_shopping_item(name: str):
    """删除购物项"""
    agent = get_agent()
    agent.shopping_list.remove_item(name)
    return {"success": True, "message": f"已删除: {name}"}


@router.post("/shopping/stats")
async def get_shopping_stats():
    """获取购物统计"""
    agent = get_agent()
    stats = agent.shopping_list.get_stats()
    return stats



@router.get("/suggestions/{member_name}")
async def get_smart_suggestions(member_name: str):
    """Get smart shopping suggestions for a member"""
    agent = get_agent()
    suggestions = agent.shopping_list.get_smart_suggestions(member_name)
    return {"suggestions": suggestions}
