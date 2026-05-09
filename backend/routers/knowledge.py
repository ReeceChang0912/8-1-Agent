"""
知识库路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class KnowledgeAdd(BaseModel):
    title: str
    content: str
    category: str = "general"
    tags: Optional[list] = []

class KnowledgeSearch(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 10


def get_agent():
    from backend.main import get_agent as _get_agent
    return _get_agent()


@router.post("/knowledge/add", status_code=201)
async def add_knowledge(knowledge_data: KnowledgeAdd):
    agent = get_agent()
    doc_id = agent.knowledge_base.add_text(
        text=knowledge_data.content,
        title=knowledge_data.title,
        category=knowledge_data.category,
        tags=knowledge_data.tags or []
    )
    return {"success": True, "doc_id": doc_id, "message": "知识已添加"}


@router.get("/knowledge/search")
async def search_knowledge(query: str, category: Optional[str] = None, limit: int = 10):
    agent = get_agent()
    results = agent.knowledge_base.search(query=query, category=category, n_results=limit)
    return {"results": results, "total": len(results)}


@router.get("/knowledge/categories")
async def get_categories():
    agent = get_agent()
    categories = [{"key": k, "name": v} for k, v in agent.knowledge_base.CATEGORIES.items()]
    return {"categories": categories}
