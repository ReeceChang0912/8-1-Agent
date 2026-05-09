"""
工作台路由 - 提供工作台首页数据
"""
from fastapi import APIRouter, Query
from typing import Optional

from services.workbench_service import (
    fetch_weather,
    fetch_news,
    fetch_daily_briefing,
    fetch_upcoming_holidays,
    get_workbench_data,
)

router = APIRouter()


@router.get("/workbench")
async def get_workbench(city: str = Query("上海", description="城市")):
    """获取工作台所有数据"""
    return get_workbench_data(city)


@router.get("/workbench/weather")
async def get_weather(city: str = Query("上海", description="城市名称")):
    """获取天气信息"""
    data = fetch_weather(city)
    return {"success": data.get('success', False), "data": data}


@router.get("/workbench/news")
async def get_news(
    category: str = Query("ai", description="分类: ai/internet/investment"),
    limit: int = Query(12, description="数量"),
):
    """获取新闻列表"""
    items = fetch_news(category, limit)
    return {"success": True, "category": category, "items": items}


@router.get("/workbench/briefing")
async def get_daily_briefing():
    """获取八点一刻每日简报"""
    briefing = fetch_daily_briefing()
    return {"success": True, "data": briefing}


@router.get("/workbench/holidays")
async def get_holidays():
    """获取临近节日"""
    holidays = fetch_upcoming_holidays()
    return {"success": True, "items": holidays}
