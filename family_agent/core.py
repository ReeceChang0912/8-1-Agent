"""
家庭智能管家核心引擎
整合所有模块：角色管理、记忆、知识库、工具、情感识别
"""

import json
import re
import logging
from typing import List, Dict, Optional
from pathlib import Path

from .role_manager import RoleManager, FamilyMember, InteractionStyle, PermissionLevel
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
from .wechat_integration import WeChatIntegration
from .smart_home import SmartHomeIntegration
from .mcp_integration import MCPIntegration
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class FamilyAgentCore:
    """家庭智能管家核心引擎"""

    def __init__(self, data_dir: str = None):
        # Use relative path based on project directory
        if data_dir is None:
            project_root = Path(__file__).resolve().parent.parent
            data_dir = str(project_root / "data")

        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 PostgreSQL 数据库连接
        try:
            self.db = DatabaseManager()
            logger.info("✅ PostgreSQL 数据库连接成功")
        except Exception as e:
            logger.warning(f"⚠️ PostgreSQL 连接失败，使用降级模式: {e}")
            self.db = None

        # 初始化各模块（支持 PostgreSQL 的传入 db_manager）
        self.role_manager = RoleManager(db_manager=self.db)
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
        self.shopping_list = ShoppingListManager(db_manager=self.db, data_dir=str(self.data_dir))
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
        self.task_manager = TaskManager(db_manager=self.db, data_dir=str(self.data_dir))

        # 初始化Phase 3功能
        self.wechat = WeChatIntegration(agent_core=self)
        self.smart_home = SmartHomeIntegration()
        self.mcp = MCPIntegration(agent_core=self)

        # 数据存储（从数据库加载）
        self.members = {}
        self._load_members()
        self.events = []
        self.reminders = []
        self._load_reminders()

        logger.info("🏡 家庭智能管家核心引擎初始化完成")

    def _load_members(self):
        """从数据库加载成员到内存"""
        if not self.db:
            return
        try:
            rows = self.db.get_all_members()
            for row in rows:
                member = FamilyMember(
                    name=row['name'],
                    role=row['role'],
                    age=row['age'],
                    side=row.get('side', 'core'),
                    interaction_style=row.get('interaction_style', 'peer'),
                    permission=row.get('permission', 'member'),
                    preferences=json.loads(row['preferences']) if row.get('preferences') else []
                )
                self.members[member.name] = member
        except Exception as e:
            logger.warning(f"加载成员失败: {e}")

    def _load_reminders(self):
        """从数据库加载日程到内存"""
        if not self.db:
            return
        try:
            rows = self.db.get_all_reminders()
            for row in rows:
                self.reminders.append({
                    'id': row['id'],
                    'date': row['date'],
                    'event': row['event'],
                    'member': row.get('member', '')
                })
        except Exception as e:
            logger.warning(f"加载日程失败: {e}")
    
    def chat(self, message: str, user_id: str = None) -> str:
        """
        处理对话

        流程：
        1. 识别用户身份
        2. 检测是否为指令或确认回复
        3. 检测情绪
        4. 保存到记忆
        5. 检索相关知识
        6. 生成回复
        """

        # 初始化用户确认状态
        if not hasattr(self, '_pending_confirmations'):
            self._pending_confirmations = {}

        # 1. 识别用户
        if user_id:
            user = self.role_manager.identify_user(user_name=user_id)
            if user:
                personalized_prompt = user.get_system_prompt()
            else:
                personalized_prompt = "你是一个温馨的家庭助手。"
        else:
            personalized_prompt = "你是一个温馨的家庭助手。"

        # 2. 检查是否是斜杠指令（直接执行，无需确认）
        if message.startswith('/'):
            return self._handle_slash_command(message, user_id)

        # 3. 检查是否有待确认的操作
        logger.info(f"[确认流程] user_id={user_id}, message={message}")
        if hasattr(self, '_pending_confirmations'):
            logger.info(f"[确认流程] 当前待确认: {self._pending_confirmations}")
        pending = self._pending_confirmations.get(user_id) if self._pending_confirmations else None
        if pending:
            logger.info(f"[确认流程] 找到待确认操作: intent={pending['intent']}")
            # 检查用户是否确认
            msg_clean = message.strip().lower()
            confirm_keywords = ['是', '好', '确认', '执行', '嗯', '对', '可以', '确定', '是的', '好的', 'ok', 'yes', 'y', '行', '来吧', '搞定']
            cancel_keywords = ['不', '不用', '取消', '不了', '算了', '不要', '没有', '否', 'no', 'n']

            is_confirm = msg_clean in confirm_keywords or msg_clean.rstrip('。.!！?？') in confirm_keywords
            is_cancel = msg_clean in cancel_keywords or any(kw in msg_clean for kw in ['不', '取消', '不用'])

            logger.info(f"[确认流程] 用户回复='{msg_clean}', is_confirm={is_confirm}, is_cancel={is_cancel}")

            if is_confirm:
                # 用户确认，执行操作
                logger.info(f"[确认流程] 用户确认，开始执行")
                result = self._execute_pending_action(pending, user_id)
                del self._pending_confirmations[user_id]
                logger.info(f"[确认流程] 执行完成")
                return result
            elif is_cancel:
                logger.info(f"[确认流程] 用户取消")
                del self._pending_confirmations[user_id]
                return "好的，已取消操作，还有什么需要帮忙的吗？"
            else:
                # 用户说了别的话，取消待确认，走正常对话
                logger.info(f"[确认流程] 用户输入其他内容，取消待确认")
                del self._pending_confirmations[user_id]

        # 4. 检测情绪
        emotion_result = self.emotion_engine.detect_emotion(message)
        self._last_emotion = emotion_result['primary_emotion'].value
        primary_emotion = emotion_result['primary_emotion']

        # 5. 保存用户消息到短期记忆
        self.memory_manager.add_memory(
            content=f"[User] {message}",
            memory_type=MemoryType.SHORT_TERM,
            source="chat",
            tags=["conversation"]
        )

        # 6. 如果是负面情绪，先生成安抚回应
        if primary_emotion.value in ['anger', 'sadness', 'anxiety']:
            comfort_response = self.emotion_engine.generate_comfort_response(
                primary_emotion,
                context=message
            )
            self.memory_manager.add_memory(
                content=f"[Assistant] {comfort_response}",
                memory_type=MemoryType.SHORT_TERM,
                source="chat"
            )
            return comfort_response

        # 7. 检测并执行工具调用 - 非指令消息先询问确认
        intent_result = self.task_executor.intent_recognizer.recognize_intent(message)
        logger.info(f"[确认流程] 意图识别结果: {intent_result['intent']}")
        if intent_result['intent'] != 'chat':
            # 检测到意图，先询问确认
            intent = intent_result['intent']
            confirm_msg = self._build_confirmation_message(intent, message)
            # 保存待确认操作
            self._pending_confirmations[user_id] = {
                'intent': intent,
                'message': message,
                'intent_result': intent_result
            }
            return confirm_msg

        # 8. 检索相关记忆
        relevant_memories = self.memory_manager.retrieve_memories(
            query=message,
            n_results=3
        )

        memory_context = ""
        if relevant_memories:
            memory_context = "\n相关记忆:\n" + "\n".join([
                m['content'] for m in relevant_memories
            ])

        # 9. 检索相关知识
        knowledge_results = self.knowledge_base.search(message, n_results=2)

        knowledge_context = ""
        if knowledge_results:
            knowledge_context = "\n相关知识:\n" + "\n".join([
                r['content'] for r in knowledge_results
            ])

        # 10. 构建提示词
        full_prompt = f"""
{personalized_prompt}

{memory_context}

{knowledge_context}

用户消息: {message}

请给出温暖、有帮助的回复。
"""

        # 11. 生成回复
        if self.llm:
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
            response = self._generate_simple_response(message, emotion_result)

        # 12. 保存回复到记忆
        self.memory_manager.add_memory(
            content=f"[Assistant] {response}",
            memory_type=MemoryType.SHORT_TERM,
            source="chat"
        )

        return response

    def _handle_slash_command(self, message: str, user_id: str = None) -> str:
        """处理斜杠指令（直接执行，无需确认）"""
        parts = message.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''

        if cmd == '/shopping':
            if not args:
                return (
                    "🛒 请告诉我需要买什么，例如:\n"
                    "  `/shopping 牛奶和鸡蛋`\n"
                    "  `/shopping 一袋大米`"
                )
            return self.task_executor._handle_add_shopping_item(f"买{args}", {})
        elif cmd == '/remind':
            if not args:
                return (
                    "📅 请告诉我提醒内容，例如:\n"
                    "  `/remind 明天下午3点开会`\n"
                    "  `/remind 周五买菜`"
                )
            return self.task_executor._handle_create_reminder(f"提醒我{args}", {})
        elif cmd == '/knowledge':
            if not args:
                return (
                    "📚 请告诉我查询内容，例如:\n"
                    "  `/knowledge 高血压注意事项`\n"
                    "  `/knowledge 感冒怎么处理`"
                )
            return self.task_executor._handle_search_knowledge(f"查询{args}", {})
        elif cmd == '/photo':
            return "📸 请在聊天框中点击上传按钮选择照片，我会自动分析并保存到照片记忆中!"
        elif cmd == '/help':
            return (
                "📋 **可用指令:**\n"
                "  `/shopping <物品>` - 添加购物清单\n"
                "  `/remind <内容>` - 创建日程提醒\n"
                "  `/knowledge <问题>` - 搜索知识库\n"
                "  `/photo` - 上传照片\n"
                "  `/help` - 显示此帮助\n\n"
                "💡 **普通聊天**时，如果检测到相关意图，我会先询问你确认再执行。"
            )
        else:
            return f"未知指令: {cmd}\n输入 `/help` 查看可用指令列表。"

    def _build_confirmation_message(self, intent: str, message: str) -> str:
        """构建确认询问消息"""
        prompts = {
            'create_reminder': f"📅 我检测到你想创建日程提醒，请确认是否执行？(是/否)",
            'add_shopping_item': f"🛒 我检测到你想添加购物清单，请确认是否执行？(是/否)",
            'search_knowledge': f"📚 我检测到你想搜索知识库，请确认是否执行？(是/否)",
            'upload_photo': f"📸 我检测到你想上传照片，请确认是否执行？(是/否)",
            'query_member': f"👤 我检测到你想查询家庭成员信息，请确认是否执行？(是/否)",
            'assign_task': f"✅ 我检测到你想分配任务，请确认是否执行？(是/否)",
        }
        return prompts.get(intent, f"我检测到你想执行操作，请确认是否执行？(是/否)")

    def _execute_pending_action(self, pending: dict, user_id: str = None) -> str:
        """执行待确认的操作"""
        intent = pending['intent']
        message = pending['message']
        # 使用 task_executor 执行
        return self.task_executor.execute(message, user_id)
    
    def get_last_emotion(self) -> Optional[str]:
        """获取最后一次检测到的情绪"""
        return getattr(self, '_last_emotion', None)

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

    def remove_member(self, name: str):
        """删除家庭成员"""
        if name in self.members:
            del self.members[name]
        self.role_manager.remove_member(name)

    def update_member(self, name: str, **kwargs):
        """更新家庭成员信息"""
        if name in self.members:
            member = self.members[name]
            if 'role' in kwargs:
                member.role = kwargs['role']
            if 'age' in kwargs:
                member.age = kwargs['age']
            if 'side' in kwargs:
                member.side = kwargs['side']
            if 'interaction_style' in kwargs:
                style_map = {'peer': InteractionStyle.PEER, 'elder': InteractionStyle.ELDER,
                             'child': InteractionStyle.CHILD, 'formal': InteractionStyle.FORMAL}
                member.interaction_style = style_map.get(kwargs['interaction_style'], InteractionStyle.PEER)
            if 'permission' in kwargs:
                perm_map = {'admin': PermissionLevel.ADMIN, 'member': PermissionLevel.MEMBER,
                            'guest': PermissionLevel.GUEST, 'child': PermissionLevel.CHILD}
                member.permission = perm_map.get(kwargs['permission'], PermissionLevel.MEMBER)
            self.role_manager.update_member(name, **kwargs)
    
    def add_reminder(self, date: str, event: str, members: List[str] = None):
        """添加提醒"""
        reminder = {
            "date": date,
            "event": event,
            "members": members or [],
            "created_at": __import__('datetime').datetime.now().isoformat()
        }
        self.reminders.append(reminder)
        # 持久化到数据库
        if self.db:
            try:
                self.db.add_reminder(date, event)
            except Exception as e:
                logger.warning(f"保存日程到数据库失败: {e}")
    
    def get_upcoming_events(self, days: int = 30) -> List[Dict]:
        """获取即将事件"""
        return self.events[:10]  # 简化实现
    
    def get_all_members(self):
        """获取所有成员"""
        return list(self.members.values())
