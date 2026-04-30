"""
MCP (Model Context Protocol) 集成模块
支持标准化的AI工具调用协议
"""

import logging
from typing import Dict, List, Optional, Any
import json

logger = logging.getLogger(__name__)


class MCPIntegration:
    """
    MCP协议集成管理器
    
    功能：
    1. 注册和管理MCP工具
    2. 处理工具调用请求
    3. 返回标准化响应
    4. 支持动态工具发现
    """
    
    def __init__(self, agent_core=None):
        self.agent_core = agent_core
        self.tools = {}
        self.resources = {}
        
        # 注册内置工具
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """注册内置工具"""
        
        # 家庭信息查询工具
        self.register_tool(
            name="get_family_info",
            description="获取家庭成员信息",
            parameters={
                "type": "object",
                "properties": {
                    "member_name": {
                        "type": "string",
                        "description": "成员姓名（可选）"
                    }
                }
            },
            handler=self._handle_get_family_info
        )
        
        # 日程查询工具
        self.register_tool(
            name="get_schedule",
            description="查询家庭日程安排",
            parameters={
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "日期 (YYYY-MM-DD)"
                    }
                }
            },
            handler=self._handle_get_schedule
        )
        
        # 购物清单工具
        self.register_tool(
            name="manage_shopping_list",
            description="管理购物清单",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["add", "remove", "list"],
                        "description": "操作类型"
                    },
                    "item": {
                        "type": "string",
                        "description": "物品名称"
                    }
                },
                "required": ["action"]
            },
            handler=self._handle_shopping_list
        )
        
        # 记忆查询工具
        self.register_tool(
            name="search_memory",
            description="搜索家庭记忆",
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["query"]
            },
            handler=self._handle_search_memory
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict,
        handler: callable
    ):
        """
        注册MCP工具
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: JSON Schema 参数定义
            handler: 处理函数
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters,
            "handler": handler
        }
        logger.info(f"✅ 注册MCP工具: {name}")
    
    def list_tools(self) -> List[Dict]:
        """列出所有可用工具"""
        return [
            {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
            for tool in self.tools.values()
        ]
    
    def call_tool(self, tool_name: str, arguments: Dict) -> Dict:
        """
        调用工具
        
        Args:
            tool_name: 工具名称
            arguments: 参数字典
        
        Returns:
            工具执行结果
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"未知工具: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            tool = self.tools[tool_name]
            handler = tool["handler"]
            
            # 执行工具
            result = handler(arguments)
            
            return {
                "success": True,
                "tool": tool_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"工具执行失败: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name
            }
    
    def handle_mcp_request(self, request: Dict) -> Dict:
        """
        处理MCP请求
        
        Args:
            request: MCP请求对象
        
        Returns:
            MCP响应对象
        """
        method = request.get("method")
        params = request.get("params", {})
        
        # tools/list - 列出工具
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": self.list_tools()
                }
            }
        
        # tools/call - 调用工具
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            result = self.call_tool(tool_name, arguments)
            
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": result
            }
        
        # resources/list - 列出资源
        elif method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "resources": list(self.resources.values())
                }
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32601,
                    "message": f"不支持的方法: {method}"
                }
            }
    
    # ===== 内置工具处理器 =====
    
    def _handle_get_family_info(self, args: Dict) -> Dict:
        """处理家庭成员查询"""
        if not self.agent_core:
            return {"error": "Agent核心未初始化"}
        
        member_name = args.get("member_name")
        
        if member_name:
            member = self.agent_core.members.get(member_name)
            if member:
                return {
                    "name": member.name,
                    "role": member.role,
                    "age": member.age,
                    "side": member.side
                }
            else:
                return {"error": f"未找到成员: {member_name}"}
        else:
            # 返回所有成员
            return {
                "members": [
                    {
                        "name": m.name,
                        "role": m.role,
                        "age": m.age
                    }
                    for m in self.agent_core.members.values()
                ]
            }
    
    def _handle_get_schedule(self, args: Dict) -> Dict:
        """处理日程查询"""
        if not self.agent_core:
            return {"error": "Agent核心未初始化"}
        
        date = args.get("date")
        
        reminders = self.agent_core.reminders
        if date:
            # 过滤指定日期的提醒
            reminders = [r for r in reminders if date in r.get('date', '')]
        
        return {
            "date": date or "all",
            "reminders": reminders
        }
    
    def _handle_shopping_list(self, args: Dict) -> Dict:
        """处理购物清单"""
        if not self.agent_core:
            return {"error": "Agent核心未初始化"}
        
        action = args.get("action")
        item = args.get("item")
        
        if action == "add" and item:
            self.agent_core.shopping_list.add_item(name=item)
            return {"success": True, "message": f"已添加: {item}"}
        
        elif action == "remove" and item:
            success = self.agent_core.shopping_list.remove_item(item)
            return {"success": success, "message": f"已删除: {item}" if success else "未找到物品"}
        
        elif action == "list":
            items = self.agent_core.shopping_list.get_items()
            return {
                "items": [
                    {
                        "name": i.name,
                        "quantity": i.quantity,
                        "category": i.category,
                        "purchased": i.purchased
                    }
                    for i in items
                ]
            }
        
        return {"error": "无效操作"}
    
    def _handle_search_memory(self, args: Dict) -> Dict:
        """处理记忆搜索"""
        if not self.agent_core:
            return {"error": "Agent核心未初始化"}
        
        query = args.get("query", "")
        
        memories = self.agent_core.memory_manager.retrieve_memories(
            query=query,
            n_results=5
        )
        
        return {
            "query": query,
            "memories": memories
        }
    
    def get_mcp_server_info(self) -> Dict:
        """获取MCP服务器信息"""
        return {
            "name": "Family Agent MCP Server",
            "version": "1.0.0",
            "description": "家庭智能管家MCP服务",
            "tools_count": len(self.tools),
            "capabilities": ["tools", "resources"]
        }

