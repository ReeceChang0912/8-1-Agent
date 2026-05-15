from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class MemoryUpdate(BaseModel):
    content: str
    importance: Optional[float] = None
    tags: Optional[List[str]] = None


def get_agent():
    from backend.main import get_agent as _get_agent
    return _get_agent()


@router.get("/memory")
def list_memories(
    query: str = "",
    memory_type: str = Query(default="all"),
    limit: int = Query(default=100, ge=1, le=500),
):
    manager = get_agent().memory_manager
    return {
        "items": manager.list_memories(query=query, memory_type=memory_type, limit=limit),
        "stats": manager.get_memory_stats(),
    }


@router.get("/memory/stats")
def memory_stats():
    return get_agent().memory_manager.get_memory_stats()


@router.delete("/memory/{memory_id}")
def delete_memory(memory_id: str):
    ok = get_agent().memory_manager.delete_memory(memory_id)
    return {"success": ok}


@router.put("/memory/{memory_id}")
def update_memory(memory_id: str, request: MemoryUpdate):
    ok = get_agent().memory_manager.update_memory(
        memory_id,
        content=request.content,
        importance=request.importance,
        tags=request.tags,
    )
    return {"success": ok}
