"""
工具引擎 - 管理所有可用工具
"""

from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass


@dataclass
class FamilyTool:
    """家庭工具定义"""
    name: str
    description: str
    func: Callable
    parameters: Dict


class ToolEngine:
    """工具引擎"""
    
    def __init__(self, agent_core=None):
        self.agent_core = agent_core
        self.tools: Dict[str, FamilyTool] = {}
        self._register_builtin_tools()
    
    def register_tool(self, tool: FamilyTool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[FamilyTool]:
        """获取工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        """列出所有工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"未知工具: {tool_name}")
        
        try:
            result = tool.func(**kwargs)
            return result
        except Exception as e:
            raise
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        
        self.register_tool(FamilyTool(
            name="query_family_member",
            description="查询家庭成员信息",
            func=self._query_family_member,
            parameters={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "成员姓名"}
                },
                "required": ["name"]
            }
        ))
        
        self.register_tool(FamilyTool(
            name="set_reminder",
            description="设置提醒",
            func=self._set_reminder,
            parameters={
                "type": "object",
                "properties": {
                    "date": {"type": "string", "description": "日期 YYYY-MM-DD"},
                    "event": {"type": "string", "description": "事件描述"}
                },
                "required": ["date", "event"]
            }
        ))
        
        self.register_tool(FamilyTool(
            name="get_upcoming_events",
            description="查询即将到来的事件",
            func=self._get_upcoming_events,
            parameters={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "未来多少天", "default": 30}
                }
            }
        ))
        
        self.register_tool(FamilyTool(
            name="recommend_gift",
            description="推荐礼物",
            func=self._recommend_gift,
            parameters={
                "type": "object",
                "properties": {
                    "member_name": {"type": "string", "description": "收礼人姓名"},
                    "occasion": {"type": "string", "description": "场合"},
                    "budget": {"type": "number", "description": "预算"}
                },
                "required": ["member_name", "occasion"]
            }
        ))
        
        self.register_tool(FamilyTool(
            name="search_knowledge",
            description="搜索知识库",
            func=self._search_knowledge,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "category": {"type": "string", "description": "分类"}
                },
                "required": ["query"]
            }
        ))
    
    def _query_family_member(self, name: str) -> Dict:
        """查询家庭成员"""
        if self.agent_core:
            member = self.agent_core.get_member(name)
            if member:
                return {
                    "name": member.name,
                    "role": member.role,
                    "age": member.age
                }
        return {"error": f"未找到成员: {name}"}
    
    def _set_reminder(self, date: str, event: str) -> Dict:
        """设置提醒"""
        return {"status": "success", "message": f"已设置提醒: {event}"}
    
    def _get_upcoming_events(self, days: int = 30) -> List:
        """获取即将事件"""
        return []
    
    def _recommend_gift(self, member_name: str, occasion: str, budget: float = 500) -> List[str]:
        """推荐礼物"""
        gift_suggestions = {
            "生日": ["定制礼品", "鲜花", "保健品", "书籍"],
            "春节": ["红包", "年货礼盒", "保健品", "茶叶"],
            "中秋": ["月饼礼盒", "水果礼篮", "茶叶"],
        }
        
        return gift_suggestions.get(occasion, ["实用礼品"])[:5]
    
    def _search_knowledge(self, query: str, category: str = None) -> List[Dict]:
        """搜索知识库"""
        if self.agent_core and hasattr(self.agent_core, 'knowledge_base'):
            return self.agent_core.knowledge_base.search(query, category=category)
        return []
