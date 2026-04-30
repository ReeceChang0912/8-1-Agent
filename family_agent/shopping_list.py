"""
购物清单管理模块
支持共享清单、智能合并、分类管理
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class ShoppingItem:
    """购物项"""
    name: str
    quantity: str = "1"
    unit: str = "个"
    category: str = "general"  # food/daily/electronic/etc.
    priority: str = "normal"  # high/normal/low
    assigned_to: str = ""  # 负责人
    purchased: bool = False
    notes: str = ""
    added_by: str = ""
    added_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
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
    
    @staticmethod
    def from_dict(data: Dict) -> 'ShoppingItem':
        return ShoppingItem(**data)


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
    
    def __init__(self, data_file: str = "data/shopping_list.json"):
        self.data_file = Path(data_file)
        self.items: List[ShoppingItem] = []
        self._load_items()
    
    def add_item(
        self,
        name: str,
        quantity: str = "1",
        unit: str = "个",
        category: str = "general",
        priority: str = "normal",
        assigned_to: str = "",
        notes: str = "",
        added_by: str = ""
    ) -> ShoppingItem:
        """添加购物项"""
        
        # 检查是否已存在相似项
        existing = self._find_similar_item(name)
        if existing:
            # 合并数量
            try:
                new_qty = float(existing.quantity) + float(quantity)
                existing.quantity = str(int(new_qty)) if new_qty == int(new_qty) else str(new_qty)
                existing.notes += f"\n{notes}" if notes else ""
                self._save_items()
                return existing
            except:
                pass
        
        # 创建新项
        item = ShoppingItem(
            name=name,
            quantity=quantity,
            unit=unit,
            category=category,
            priority=priority,
            assigned_to=assigned_to,
            notes=notes,
            added_by=added_by
        )
        
        self.items.append(item)
        self._save_items()
        
        return item
    
    def remove_item(self, item_name: str) -> bool:
        """删除购物项"""
        for i, item in enumerate(self.items):
            if item.name == item_name:
                self.items.pop(i)
                self._save_items()
                return True
        return False
    
    def mark_purchased(self, item_name: str) -> bool:
        """标记为已购买"""
        for item in self.items:
            if item.name == item_name:
                item.purchased = True
                self._save_items()
                return True
        return False
    
    def mark_unpurchased(self, item_name: str) -> bool:
        """标记为未购买"""
        for item in self.items:
            if item.name == item_name:
                item.purchased = False
                self._save_items()
                return True
        return False
    
    def get_items(
        self,
        category: str = None,
        priority: str = None,
        purchased: bool = None,
        assigned_to: str = None
    ) -> List[ShoppingItem]:
        """获取购物项（支持过滤）"""
        
        filtered = self.items
        
        if category:
            filtered = [item for item in filtered if item.category == category]
        
        if priority:
            filtered = [item for item in filtered if item.priority == priority]
        
        if purchased is not None:
            filtered = [item for item in filtered if item.purchased == purchased]
        
        if assigned_to:
            filtered = [item for item in filtered if item.assigned_to == assigned_to]
        
        # 按优先级排序
        priority_order = {"high": 0, "normal": 1, "low": 2}
        filtered.sort(key=lambda x: priority_order.get(x.priority, 1))
        
        return filtered
    
    def get_shopping_summary(self) -> Dict:
        """获取购物清单摘要"""
        total = len(self.items)
        purchased = sum(1 for item in self.items if item.purchased)
        unpurchased = total - purchased
        
        # 按分类统计
        categories = {}
        for item in self.items:
            cat = item.category
            if cat not in categories:
                categories[cat] = {"total": 0, "purchased": 0}
            categories[cat]["total"] += 1
            if item.purchased:
                categories[cat]["purchased"] += 1
        
        # 按负责人统计
        assignees = {}
        for item in self.items:
            if item.assigned_to:
                person = item.assigned_to
                if person not in assignees:
                    assignees[person] = {"total": 0, "purchased": 0}
                assignees[person]["total"] += 1
                if item.purchased:
                    assignees[person]["purchased"] += 1
        
        return {
            "total_items": total,
            "purchased": purchased,
            "unpurchased": unpurchased,
            "completion_rate": purchased / total if total > 0 else 0,
            "by_category": categories,
            "by_assignee": assignees
        }
    
    def generate_shopping_route(self, store_layout: Dict = None) -> List[str]:
        """
        生成采购路线建议
        
        Args:
            store_layout: 超市布局（可选）
        
        Returns:
            推荐的采购顺序
        """
        
        # 简化版：按分类分组
        categories_needed = set()
        for item in self.items:
            if not item.purchased:
                categories_needed.add(item.category)
        
        # 默认路线顺序
        default_route = ["food", "daily", "health", "home", "electronics", "clothing", "other"]
        
        route = [cat for cat in default_route if cat in categories_needed]
        
        return route
    
    def clear_purchased(self) -> int:
        """清除已购买的项"""
        initial_count = len(self.items)
        self.items = [item for item in self.items if not item.purchased]
        removed_count = initial_count - len(self.items)
        
        if removed_count > 0:
            self._save_items()
        
        return removed_count
    
    def _find_similar_item(self, name: str) -> Optional[ShoppingItem]:
        """查找相似的购物项（用于合并）"""
        name_lower = name.lower()
        
        for item in self.items:
            if item.name.lower() == name_lower:
                return item
            
            # 模糊匹配
            if name_lower in item.name.lower() or item.name.lower() in name_lower:
                return item
        
        return None
    
    def _load_items(self):
        """加载购物清单"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.items = [ShoppingItem.from_dict(item) for item in data]
    
    def _save_items(self):
        """保存购物清单"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump([item.to_dict() for item in self.items], 
                     f, ensure_ascii=False, indent=2)
