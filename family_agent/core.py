"""
家庭智能管家核心引擎
整合所有模块：角色管理、记忆、知识库、工具、情感识别
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path

from .role_manager import RoleManager, FamilyMember
from .memory_manager import FamilyMemoryManager, MemoryType
from .knowledge_base import KnowledgeBase
from .tool_engine import ToolEngine
from .emotion_engine import EmotionEngine
from .llm_adapter import get_llm
from .shopping_list import ShoppingListManager
from .photo_memory import PhotoMemoryManager
from .smart_photo_analyzer import SmartPhotoAnalyzer
from .intent_engine import TaskExecutor
from .task_manager import TaskManager
from .auth_manager import AuthManager
from .wechat_integration import WeChatIntegration
from .smart_home import SmartHomeIntegration
from .mcp_integration import MCPIntegration

logger = logging.getLogger(__name__)


class FamilyAgentCore:
    """家庭智能管家核心引擎"""
    
    def __init__(self, data_dir: str = None):
        # Use relative path based on project directory
        if data_dir is None:
            from pathlib import Path
            project_root = Path(__file__).resolve().parent.parent
            data_dir = str(project_root / "data")
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化各模块
        self.role_manager = RoleManager(data_file=str(self.data_dir / "members.json"))
        self.memory_manager = FamilyMemoryManager(data_dir=str(self.data_dir / "memory"))
        self.knowledge_base = KnowledgeBase(
            kb_dir=str(self.data_dir / "knowledge_docs"),
            db_dir=str(self.data_dir / "knowledge_db")
        )
        self.tool_engine = ToolEngine(agent_core=self)
        self.emotion_engine = EmotionEngine()
        
        # 初始化LLM（可选）
        try:
            self.llm = get_llm()
            logger.info("✅ LLM适配器初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ LLM初始化失败，使用规则模式: {e}")
            self.llm = None
        
        # 初始化扩展功能
        self.shopping_list = ShoppingListManager(data_file=str(self.data_dir / "shopping_list.json"))
        self.photo_memory = PhotoMemoryManager(
            photo_dir=str(self.data_dir.parent / "photos"),
            index_file=str(self.data_dir / "photo_index.json")
        )
        
        # 初始化智能照片分析器
        self.photo_analyzer = SmartPhotoAnalyzer(
            photo_manager=self.photo_memory,
            llm_adapter=self.llm
        )
        
        # 初始化任务执行器(意图识别)
        self.task_executor = TaskExecutor(agent_core=self)
        
        # 初始化家庭任务管理器
        self.task_manager = TaskManager(data_file=str(self.data_dir / "family_tasks.json"))
        
        # 初始化Phase 3功能
        self.wechat = WeChatIntegration(agent_core=self)
        self.smart_home = SmartHomeIntegration()
        self.mcp = MCPIntegration(agent_core=self)
        
        # 数据存储
        self.members = {}
        self.events = []
        self.reminders = []
        
        logger.info("🏡 家庭智能管家核心引擎初始化完成")
    
    def chat(self, message: str, user_id: str = None) -> str:
        """
        处理对话
        
        流程：
        1. 识别用户身份
        2. 检测情绪
        3. 保存到记忆
        4. 检索相关知识
        5. 生成回复
        """
        
        # 1. 识别用户
        if user_id:
            user = self.role_manager.identify_user(account=user_id)
            if user:
                personalized_prompt = user.get_system_prompt()
            else:
                personalized_prompt = "你是一个温馨的家庭助手。"
        else:
            personalized_prompt = "你是一个温馨的家庭助手。"
        
        # 2. 检测情绪
        emotion_result = self.emotion_engine.detect_emotion(message)
        primary_emotion = emotion_result['primary_emotion']
        
        # 3. 保存用户消息到短期记忆
        self.memory_manager.add_memory(
            content=f"[User] {message}",
            memory_type=MemoryType.SHORT_TERM,
            source="chat",
            tags=["conversation"]
        )
        
        # 4. 如果是负面情绪，先生成安抚回应
        if primary_emotion.value in ['anger', 'sadness', 'anxiety']:
            comfort_response = self.emotion_engine.generate_comfort_response(
                primary_emotion,
                context=message
            )
            
            # 保存安抚回应
            self.memory_manager.add_memory(
                content=f"[Assistant] {comfort_response}",
                memory_type=MemoryType.SHORT_TERM,
                source="chat"
            )
            
            return comfort_response
        
        # 5. 检索相关记忆
        relevant_memories = self.memory_manager.retrieve_memories(
            query=message,
            n_results=3
        )
        
        memory_context = ""
        if relevant_memories:
            memory_context = "\n相关记忆:\n" + "\n".join([
                m['content'] for m in relevant_memories
            ])
        
        # 6. 检索相关知识
        knowledge_results = self.knowledge_base.search(message, n_results=2)
        
        knowledge_context = ""
        if knowledge_results:
            knowledge_context = "\n相关知识:\n" + "\n".join([
                r['content'] for r in knowledge_results
            ])
        
        # 7. 检测并执行工具调用(创建日程、购物清单等)
        tool_result = self.task_executor.execute(message, user_id)
        if tool_result:
            # 如果任务执行器返回了结果,直接返回
            return tool_result
        
        # 8. 构建提示词
        full_prompt = f"""
{personalized_prompt}

{memory_context}

{knowledge_context}

用户消息: {message}

请给出温暖、有帮助的回复。
"""
        
        # 9. 生成回复
        if self.llm:
            # 使用LLM生成回复
            try:
                response = self.llm.generate_response(
                    system_prompt=personalized_prompt,
                    user_message=message,
                    context=f"{memory_context}\n{knowledge_context}"
                )
            except Exception as e:
                logger.error(f"LLM调用失败，降级到规则模式: {e}")
                response = self._generate_simple_response(message, emotion_result)
        else:
            # 使用规则生成回复
            response = self._generate_simple_response(message, emotion_result)
        
        # 10. 保存回复到记忆
        self.memory_manager.add_memory(
            content=f"[Assistant] {response}",
            memory_type=MemoryType.SHORT_TERM,
            source="chat"
        )
        
        return response
    
    def _generate_simple_response(self, message: str, emotion_result: Dict) -> str:
        """简单回复生成（实际应该调用LLM）"""
        
        # 基于关键词的简单回复
        if "生日" in message:
            return "我可以帮你设置生日提醒，或者推荐一些礼物建议。需要我帮忙吗？"
        
        if "提醒" in message or "记住" in message:
            return "好的，我会帮你记住这件事。你可以告诉我具体的时间和内容。"
        
        if "购物" in message or "买" in message:
            return "我可以帮你管理购物清单。你想添加什么物品？"
        
        if "健康" in message or "医院" in message:
            return "健康是最重要的。如果需要，我可以帮你查找相关的健康知识或设置用药提醒。"
        
        # 默认回复
        responses = [
            "我理解了，请继续说。",
            "嗯嗯，我在听。",
            "这个情况我明白了，有什么我可以帮你的吗？",
            "谢谢你的分享，我会记下来的。"
        ]
        
        import random
        return random.choice(responses)
    
    def add_member(self, member: FamilyMember):
        """添加家庭成员"""
        self.role_manager.add_member(member)
        self.members[member.name] = member
    
    def get_member(self, name: str):
        """获取家庭成员"""
        return self.members.get(name)
    
    def add_reminder(self, date: str, event: str, members: List[str] = None):
        """添加提醒"""
        reminder = {
            "date": date,
            "event": event,
            "members": members or [],
            "created_at": __import__('datetime').datetime.now().isoformat()
        }
        self.reminders.append(reminder)
    
    def get_upcoming_events(self, days: int = 30) -> List[Dict]:
        """获取即将事件"""
        return self.events[:10]  # 简化实现
    
    def get_all_members(self):
        """获取所有成员"""
        return list(self.members.values())
