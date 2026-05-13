"""
家庭财务管理路由
提供收支记录、月度汇总、分类管理等功能
"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# 预定义分类
INCOME_CATEGORIES = ["工资", "奖金", "投资收益", "兼职收入", "红包", "其他收入"]
EXPENSE_CATEGORIES = ["餐饮", "交通", "购物", "住房", "娱乐", "医疗", "教育", "通讯", "人情", "其他支出"]


class TransactionCreate(BaseModel):
    amount: float
    transaction_type: str  # "income" or "expense"
    category: str
    description: str = ""
    transaction_date: str  # "YYYY-MM-DD"
    created_by: str = ""


class TransactionUpdate(BaseModel):
    amount: Optional[float] = None
    transaction_type: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    transaction_date: Optional[str] = None
    created_by: Optional[str] = None


def get_db():
    from backend.main import get_db_manager
    return get_db_manager()


@router.get("/finance/categories")
def get_categories():
    """获取预定义分类列表"""
    return {
        "income": INCOME_CATEGORIES,
        "expense": EXPENSE_CATEGORIES,
    }


@router.get("/finance/summary")
def get_summary(year: int = Query(default=None), month: int = Query(default=None)):
    """获取月度汇总数据（大盘）"""
    from datetime import datetime
    now = datetime.now()
    y = year or now.year
    m = month or now.month
    db = get_db()
    if not db:
        return {"total_income": 0, "total_expense": 0, "balance": 0, "income_breakdown": [], "expense_breakdown": []}
    try:
        return db.get_monthly_summary(y, m)
    except Exception as e:
        return {"total_income": 0, "total_expense": 0, "balance": 0, "income_breakdown": [], "expense_breakdown": [], "error": str(e)}


@router.get("/finance/trend")
def get_trend(months: int = Query(default=6, ge=1, le=24)):
    """获取月度趋势数据"""
    db = get_db()
    if not db:
        return []
    try:
        return db.get_monthly_trend(months)
    except Exception as e:
        return []


@router.get("/finance/transactions")
def get_transactions(
    year: int = Query(default=None),
    month: int = Query(default=None),
    transaction_type: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """获取分页交易记录"""
    from datetime import datetime
    now = datetime.now()
    y = year or now.year
    m = month or now.month
    db = get_db()
    if not db:
        return {"items": [], "total": 0, "page": page, "page_size": page_size}
    try:
        return db.get_transactions(y, m, transaction_type, category, page, page_size)
    except Exception as e:
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "error": str(e)}


@router.post("/finance/transactions")
def create_transaction(data: TransactionCreate):
    """新增交易记录"""
    if data.amount <= 0:
        return {"success": False, "message": "金额必须大于0"}
    if data.transaction_type not in ("income", "expense"):
        return {"success": False, "message": "类型必须是 income 或 expense"}
    if not data.category:
        return {"success": False, "message": "分类不能为空"}
    db = get_db()
    if not db:
        return {"success": False, "message": "数据库不可用"}
    try:
        tid = db.add_transaction(
            amount=data.amount,
            transaction_type=data.transaction_type,
            category=data.category,
            description=data.description,
            transaction_date=data.transaction_date,
            created_by=data.created_by,
        )
        return {"success": True, "id": tid, "message": "添加成功"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.put("/finance/transactions/{transaction_id}")
def update_transaction(transaction_id: int, data: TransactionUpdate):
    """编辑交易记录"""
    db = get_db()
    if not db:
        return {"success": False, "message": "数据库不可用"}
    kwargs = {k: v for k, v in data.dict().items() if v is not None}
    if not kwargs:
        return {"success": False, "message": "没有需要更新的字段"}
    try:
        ok = db.update_transaction(transaction_id, **kwargs)
        return {"success": ok, "message": "更新成功" if ok else "记录不存在"}
    except Exception as e:
        return {"success": False, "message": str(e)}


@router.delete("/finance/transactions/{transaction_id}")
def delete_transaction(transaction_id: int):
    """删除交易记录"""
    db = get_db()
    if not db:
        return {"success": False, "message": "数据库不可用"}
    try:
        ok = db.delete_transaction(transaction_id)
        return {"success": ok, "message": "删除成功" if ok else "记录不存在"}
    except Exception as e:
        return {"success": False, "message": str(e)}
