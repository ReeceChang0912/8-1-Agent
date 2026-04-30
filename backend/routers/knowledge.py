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
    from main import get_agent as _get_agent
    return _get_agent()


@router.post("/knowledge/add", status_code=201)
async def add_knowledge(knowledge_data: KnowledgeAdd):
    """添加知识"""
    agent = get_agent()
    doc_id = agent.knowledge_base.add_document(
        title=knowledge_data.title,
        content=knowledge_data.content,
        category=knowledge_data.category,
        tags=knowledge_data.tags or []
    )
    return {"success": True, "doc_id": doc_id, "message": "知识已添加"}


@router.get("/knowledge/search")
async def search_knowledge(query: str, category: Optional[str] = None, limit: int = 10):
    """搜索知识"""
    agent = get_agent()
    results = agent.knowledge_base.search(
        query=query,
        category=category,
        limit=limit
    )
    return {"results": results, "total": len(results)}


@router.get("/knowledge/categories")
async def get_categories():
    """获取所有分类"""
    agent = get_agent()
    categories = agent.knowledge_base.get_categories()
    return {"categories": categories}
