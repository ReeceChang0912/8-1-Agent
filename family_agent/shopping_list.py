"""
购物清单管理模块 - PostgreSQL版
支持共享清单、智能合并、分类管理
"""
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json


class ShoppingItem:
    """购物项（数据对象）"""
    def __init__(self, name: str, quantity: str = "1", unit: str = "个",
                 category: str = "general", priority: str = "normal",
                 assigned_to: str = "", purchased: bool = False,
                 notes: str = "", added_by: str = "", added_at: str = None):
        self.name = name
        self.quantity = quantity
        self.unit = unit
        self.category = category
        self.priority = priority
        self.assigned_to = assigned_to
        self.purchased = purchased
        self.notes = notes
        self.added_by = added_by
        self.added_at = added_at or datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "category": self.category,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "purchased": self.purchased,
            "notes": self.notes,
            "added_by": self.added_by,
            "added_at": self.added_at
        }


class ShoppingListManager:
    """
    购物清单管理器
    
    功能：
    1. 添加/删除/修改购物项
    2. 智能合并相似项
    3. 按分类和优先级排序
    4. 标记购买状态
    5. 生成采购建议
    """
    
    CATEGORIES = {
        "food": "食品食材",
        "daily": "日用品",
        "electronics": "电子产品",
        "clothing": "服装鞋帽",
        "health": "医药保健",
        "home": "家居用品",
        "other": "其他"
    }
    
    def __init__(self, db_manager=None, data_dir: str = "data"):
        """
        初始化购物清单管理器
        Args:
            db_manager: DatabaseManager 实例
            data_dir: 数据目录（兼容旧接口）
        """
        self.db = db_manager
        self.data_dir = Path(data_dir)
        self.advisor = None
        if db_manager:
            from .smart_shopping import SmartShoppingAdvisor
            self.advisor = SmartShoppingAdvisor(data_dir=str(self.data_dir))

    def add_item(
        self,
        name: str,
        quantity: str = "1",
        unit: str = "个",
        category: str = "general",
        priority: str = "normal",
        assigned_to: str = "",
        notes: str = "",
        added_by: str = "",
        family_id: str = "",
        current_stock: float = 0,
        target_stock: float = 0,
        restock_threshold: float = 0,
        is_favorite: bool = False,
    ) -> ShoppingItem:
        """添加购物项"""
        if self.db:
            self.db.add_shopping_item(
                name=name, quantity=quantity, category=category,
                priority=priority, added_by=added_by, status='pending', family_id=family_id,
                unit=unit, notes=notes, current_stock=current_stock,
                target_stock=target_stock, restock_threshold=restock_threshold,
                is_favorite=is_favorite,
            )
        # 返回对象（用于兼容旧接口）
        return ShoppingItem(
            name=name, quantity=quantity, category=category,
            priority=priority, assigned_to=assigned_to,
            notes=notes, added_by=added_by
        )

    def remove_item(self, item_id: int, family_id: str = "") -> bool:
        """删除购物项"""
        if self.db:
            return self.db.remove_shopping_item(item_id, family_id=family_id)
        return False

    def mark_purchased(self, item_id: int, family_id: str = "") -> bool:
        """标记为已购买"""
        if self.db:
            return self.db.update_shopping_item(item_id, family_id=family_id, status='purchased')
        return False

    def mark_unpurchased(self, item_id: int, family_id: str = "") -> bool:
        """标记为未购买"""
        if self.db:
            return self.db.update_shopping_item(item_id, family_id=family_id, status='pending')
        return False

    def toggle_purchased(self, item_id: int, family_id: str = "") -> bool:
        """切换购买状态"""
        items = self.get_items(family_id=family_id)
        for item in items:
            if item.get('id') == item_id:
                if item.get('status') == 'purchased':
                    return self.mark_unpurchased(item_id, family_id=family_id)
                else:
                    return self.mark_purchased(item_id, family_id=family_id)
        return False

    def update_item(self, item_id: int, family_id: str = "", **kwargs) -> bool:
        """更新购物项"""
        if self.db:
            # 过滤出可更新的字段
            allowed = {
                'name', 'quantity', 'category', 'priority', 'notes', 'unit',
                'current_stock', 'target_stock', 'restock_threshold', 'is_favorite', 'status'
            }
            updates = {k: v for k, v in kwargs.items() if k in allowed}
            return self.db.update_shopping_item(item_id, family_id=family_id, **updates)
        return False

    def get_items(
        self,
        category: str = None,
        priority: str = None,
        purchased: bool = None,
        assigned_to: str = None,
        family_id: str = ""
    ) -> List[Dict]:
        """获取购物项（支持过滤）"""
        if not self.db:
            return []
        
        # 先获取所有或按状态过滤
        status = 'purchased' if purchased else ('pending' if purchased is False else None)
        items = self.db.get_all_shopping_items(status=status, family_id=family_id)
        
        # 内存过滤（简化实现）
        if category:
            items = [i for i in items if i.get('category') == category]
        if priority:
            items = [i for i in items if i.get('priority') == priority]
        if assigned_to:
            items = [i for i in items if i.get('added_by') == assigned_to]
        
        # 按优先级排序
        priority_order = {"high": 0, "normal": 1, "low": 2}
        items.sort(key=lambda x: priority_order.get(x.get('priority', 'normal'), 1))
        
        return items

    def get_shopping_summary(self, family_id: str = "") -> Dict:
        """获取购物清单摘要"""
        if not self.db:
            return {}
        
        all_items = self.db.get_all_shopping_items(family_id=family_id)
        total = len(all_items)
        purchased = sum(1 for i in all_items if i.get('status') == 'purchased')
        unpurchased = total - purchased
        
        # 按分类统计
        categories = {}
        for item in all_items:
            cat = item.get('category', 'other')
            if cat not in categories:
                categories[cat] = {"total": 0, "purchased": 0}
            categories[cat]["total"] += 1
            if item.get('status') == 'purchased':
                categories[cat]["purchased"] += 1
        
        # 按负责人统计
        assignees = {}
        for item in all_items:
            person = item.get('added_by', '')
            if person:
                if person not in assignees:
                    assignees[person] = {"total": 0, "purchased": 0}
                assignees[person]["total"] += 1
                if item.get('status') == 'purchased':
                    assignees[person]["purchased"] += 1
        
        return {
            "total_items": total,
            "purchased": purchased,
            "unpurchased": unpurchased,
            "completion_rate": purchased / total if total > 0 else 0,
            "favorites": sum(1 for i in all_items if i.get('is_favorite')),
            "restock_needed": sum(
                1 for i in all_items
                if float(i.get('current_stock') or 0) <= float(i.get('restock_threshold') or 0)
            ),
            "inventory_value_items": sum(1 for i in all_items if float(i.get('target_stock') or 0) > 0),
            "by_category": categories,
            "by_assignee": assignees
        }

    def generate_shopping_route(self, store_layout: Dict = None) -> List[str]:
        """
        生成采购路线建议
        """
        if not self.db:
            return []
        
        items = self.get_items(purchased=False)
        
        # 简化版：按分类分组
        categories_needed = set()
        for item in items:
            if not item.get('status') == 'purchased':
                categories_needed.add(item.get('category', 'other'))
        
        # 默认路线顺序
        default_route = ["food", "daily", "health", "home", "electronics", "clothing", "other"]
        
        route = [cat for cat in default_route if cat in categories_needed]
        
        return route

    def clear_purchased(self, family_id: str = "") -> int:
        """清除已购买的项"""
        if not self.db:
            return 0
        
        items = self.db.get_all_shopping_items(status='purchased', family_id=family_id)
        count = len(items)
        for item in items:
            self.db.remove_shopping_item(item['id'], family_id=family_id)
        return count

    def get_smart_suggestions(self, member: str) -> List[Dict]:
        """获取智能购物建议"""
        if self.advisor:
            return self.advisor.generate_shopping_suggestions(member)
        return []

    def _find_similar_item(self, name: str) -> Optional[int]:
        """查找相似的购物项（用于合并）"""
        if not self.db:
            return None
        
        name_lower = name.lower()
        items = self.db.get_all_shopping_items()
        
        for item in items:
            if item['name'].lower() == name_lower:
                return item['id']
            # 模糊匹配
            if name_lower in item['name'].lower() or item['name'].lower() in name_lower:
                return item['id']
        return None
