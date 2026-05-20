"""
购物清单路由 - PostgreSQL版
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ShoppingItemCreate(BaseModel):
    name: str
    quantity: str = "1"
    unit: str = "件"
    category: str = "general"
    priority: str = "normal"
    notes: str = ""
    current_stock: float = 0
    target_stock: float = 0
    restock_threshold: float = 0
    is_favorite: bool = False
    family_id: str = ""


def get_agent():
    from backend.main import get_agent as _get_agent
    return _get_agent()


@router.get("/shopping")
async def get_shopping_list(family_id: str = ""):
    agent = get_agent()
    items = agent.shopping_list.get_items(family_id=family_id)
    # 添加 purchased 布尔字段（前端兼容）
    for item in items:
        item['purchased'] = item.get('status') == 'purchased'
    return {"items": items}


@router.post("/shopping", status_code=201)
async def add_shopping_item(item_data: ShoppingItemCreate):
    agent = get_agent()
    agent.shopping_list.add_item(
        name=item_data.name,
        quantity=item_data.quantity,
        unit=item_data.unit,
        category=item_data.category,
        priority=item_data.priority,
        notes=item_data.notes,
        current_stock=item_data.current_stock,
        target_stock=item_data.target_stock,
        restock_threshold=item_data.restock_threshold,
        is_favorite=item_data.is_favorite,
        family_id=getattr(item_data, "family_id", "")
    )
    return {"success": True, "message": f"已添加: {item_data.name}"}


@router.put("/shopping/{item_id}")
async def update_shopping_item(item_id: int, item_data: ShoppingItemCreate, family_id: str = ""):
    agent = get_agent()
    agent.shopping_list.update_item(item_id, family_id=family_id, **item_data.model_dump(exclude={"family_id"}))
    return {"success": True, "message": f"已更新: {item_data.name}"}


@router.post("/shopping/{item_id}/toggle")
async def toggle_shopping_item(item_id: int, family_id: str = ""):
    agent = get_agent()
    agent.shopping_list.toggle_purchased(item_id, family_id=family_id)
    return {"success": True}


@router.delete("/shopping/{item_name}")
async def remove_shopping_item(item_name: str, family_id: str = ""):
    agent = get_agent()
    items = agent.shopping_list.get_items(family_id=family_id)
    for item in items:
        if item.get('name') == item_name:
            agent.shopping_list.remove_item(item['id'], family_id=family_id)
            return {"success": True, "message": f"已删除: {item_name}"}
    return {"success": False, "message": f"未找到: {item_name}"}


@router.get("/shopping/stats")
async def get_shopping_stats(family_id: str = ""):
    agent = get_agent()
    stats = agent.shopping_list.get_shopping_summary(family_id=family_id)
    return stats


@router.get("/suggestions/{member_name}")
async def get_smart_suggestions(member_name: str):
    agent = get_agent()
    suggestions = agent.shopping_list.get_smart_suggestions(member_name)
    return {"suggestions": suggestions}
