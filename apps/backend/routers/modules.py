"""
平台模块路由
返回家庭管理系统的模块目录与路线图
"""
from fastapi import APIRouter

router = APIRouter()

MODULES = [
    {
        "id": "chat",
        "title": "智能对话",
        "status": "ready",
        "category": "core",
        "description": "统一入口，承载家庭助手、记忆和任务交互。",
        "web_route": "/chat",
        "miniapp_route": "/pages/webview/webview",
        "owner": "platform",
    },
    {
        "id": "finance",
        "title": "家庭财务",
        "status": "ready",
        "category": "core",
        "description": "收支记录、月度汇总、趋势分析、分类管理。",
        "web_route": "/finance",
        "miniapp_route": "/pages/webview/webview",
        "owner": "finance",
    },
    {
        "id": "wedding",
        "title": "备婚管理",
        "status": "ready",
        "category": "life",
        "description": "婚礼筹备、预算、待办、供应商、时间线。",
        "web_route": "/modules/wedding",
        "miniapp_route": "/pages/webview/webview",
        "owner": "product",
    },
    {
        "id": "insurance",
        "title": "保险管理",
        "status": "ready",
        "category": "life",
        "description": "保单、到期提醒、保障范围、家庭成员覆盖。",
        "web_route": "/modules/insurance",
        "miniapp_route": "/pages/webview/webview",
        "owner": "product",
    },
    {
        "id": "vehicle",
        "title": "车辆管理",
        "status": "ready",
        "category": "life",
        "description": "保养、年检、保险、加油、违章与费用记录。",
        "web_route": "/modules/vehicle",
        "miniapp_route": "/pages/webview/webview",
        "owner": "product",
    },
    {
        "id": "fitness",
        "title": "健身管理",
        "status": "ready",
        "category": "life",
        "description": "训练计划、身体数据、餐饮记录、目标跟踪。",
        "web_route": "/modules/fitness",
        "miniapp_route": "/pages/webview/webview",
        "owner": "product",
    },
    {
        "id": "housing",
        "title": "住房管理",
        "status": "ready",
        "category": "life",
        "description": "房贷、租房、物业、水电燃气、维修报修。",
        "web_route": "/modules/housing",
        "miniapp_route": "/pages/webview/webview",
        "owner": "product",
    },
    {
        "id": "documents",
        "title": "证件管理",
        "status": "ready",
        "category": "life",
        "description": "身份证、护照、驾照、房产证、到期提醒。",
        "web_route": "/modules/documents",
        "miniapp_route": "/pages/webview/webview",
        "owner": "product",
    },
    {
        "id": "schedule",
        "title": "家庭日程",
        "status": "planned",
        "category": "core",
        "description": "生日、纪念日、节假日、接送安排与同步提醒。",
        "web_route": "/schedule",
        "miniapp_route": "/pages/webview/webview",
        "owner": "platform",
    },
    {
        "id": "chores",
        "title": "家务分工",
        "status": "planned",
        "category": "life",
        "description": "轮值表、家务分配、完成提醒、家庭协作。",
        "web_route": "",
        "miniapp_route": "",
        "owner": "product",
    },
    {
        "id": "shopping",
        "title": "采购管理",
        "status": "planned",
        "category": "core",
        "description": "常买清单、库存、补货提醒、家庭采购协同。",
        "web_route": "/shopping",
        "miniapp_route": "/pages/webview/webview",
        "owner": "platform",
    },
    {
        "id": "health",
        "title": "健康管理",
        "status": "ready",
        "category": "life",
        "description": "体检报告、用药、慢病跟踪、复诊安排。",
        "web_route": "/modules/health",
        "miniapp_route": "/pages/webview/webview",
        "owner": "product",
    },
    {
        "id": "travel",
        "title": "旅行管理",
        "status": "ready",
        "category": "life",
        "description": "行程、预算、打包清单、预订信息。",
        "web_route": "/modules/travel",
        "miniapp_route": "/pages/webview/webview",
        "owner": "product",
    },
]


@router.get("/modules")
def list_modules():
    return {
        "items": MODULES,
        "ready_count": sum(1 for item in MODULES if item["status"] == "ready"),
        "planned_count": sum(1 for item in MODULES if item["status"] != "ready"),
    }
