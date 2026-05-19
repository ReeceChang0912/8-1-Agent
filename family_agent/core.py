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
    
    def chat(self, message: str, user_id: str = None, family_id: str = None) -> str:
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
        confirmation_key = f"{family_id or ''}:{user_id or ''}"

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
            return self._handle_slash_command(message, user_id, family_id=family_id)

        # 3. 检查是否有待确认的操作
        logger.info(f"[确认流程] user_id={user_id}, message={message}")
        if hasattr(self, '_pending_confirmations'):
            logger.info(f"[确认流程] 当前待确认: {self._pending_confirmations}")
        pending = self._pending_confirmations.get(confirmation_key) if self._pending_confirmations else None
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
                result = self._execute_pending_action(pending, user_id, family_id=family_id)
                del self._pending_confirmations[confirmation_key]
                logger.info(f"[确认流程] 执行完成")
                return result
            elif is_cancel:
                logger.info(f"[确认流程] 用户取消")
                del self._pending_confirmations[confirmation_key]
                return "好的，已取消操作，还有什么需要帮忙的吗？"
            else:
                # 用户说了别的话，取消待确认，走正常对话
                logger.info(f"[确认流程] 用户输入其他内容，取消待确认")
                del self._pending_confirmations[confirmation_key]

        # 4. 检测情绪
        emotion_result = self.emotion_engine.detect_emotion(message)
        self._last_emotion = emotion_result['primary_emotion'].value
        primary_emotion = emotion_result['primary_emotion']

        # 5. 保存用户消息到短期记忆，并提取可长期保留的偏好/事实
        self.memory_manager.remember_conversation_turn(
            user_message=message,
            user_id=user_id,
            family_id=family_id,
            emotion=self._last_emotion,
        )

        # 6. 如果是负面情绪，先生成安抚回应
        if primary_emotion.value in ['anger', 'sadness', 'anxiety']:
            comfort_response = self.emotion_engine.generate_comfort_response(
                primary_emotion,
                context=message
            )
            self.memory_manager.remember_conversation_turn(
                user_message="",
                assistant_response=comfort_response,
                user_id=user_id,
                family_id=family_id,
                emotion=self._last_emotion,
            )
            return comfort_response

        # 7. 检测并执行工具调用 - 非指令消息先询问确认
        intent_result = self.task_executor.intent_recognizer.recognize_intent(message)
        logger.info(f"[确认流程] 意图识别结果: {intent_result['intent']}")
        if intent_result['intent'] != 'chat':
            direct_intents = {
                'query_wedding', 'query_insurance', 'query_vehicle', 'query_fitness', 'query_finance'
            }
            if intent_result['intent'] in direct_intents:
                response = self.task_executor.execute(message, user_id, family_id=family_id)
                if response:
                    self.memory_manager.remember_conversation_turn(
                        user_message="",
                        assistant_response=response,
                        user_id=user_id,
                        family_id=family_id,
                        emotion=self._last_emotion,
                    )
                    return response
            # 检测到意图，先询问确认
            intent = intent_result['intent']
            confirm_msg = self._build_confirmation_message(intent, message)
            # 保存待确认操作
            self._pending_confirmations[confirmation_key] = {
                'intent': intent,
                'message': message,
                'intent_result': intent_result
            }
            return confirm_msg

        module_response = self._handle_module_query(message, family_id=family_id)
        if module_response:
            self.memory_manager.remember_conversation_turn(
                user_message="",
                assistant_response=module_response,
                user_id=user_id,
                family_id=family_id,
                emotion=self._last_emotion,
            )
            return module_response

        # 8. 构建会话记忆上下文：近期对话 + 相关长期记忆 + 工作记忆
        memory_context = self.memory_manager.build_chat_context(
            query=message,
            user_id=user_id,
            family_id=family_id,
            recent_turns=8,
            relevant_limit=5,
        )

        # 9. 检索相关知识
        knowledge_results = self.knowledge_base.search(message, n_results=2)

        knowledge_context = ""
        if knowledge_results:
            knowledge_context = "\n相关知识:\n" + "\n".join([
                r['content'] for r in knowledge_results
            ])

        # 10. 生成回复
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

        # 11. 保存回复到短期记忆
        self.memory_manager.remember_conversation_turn(
            user_message="",
            assistant_response=response,
            user_id=user_id,
            family_id=family_id,
            emotion=self._last_emotion,
        )

        return response

    def _handle_slash_command(self, message: str, user_id: str = None, family_id: str = None) -> str:
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
            return self.task_executor._handle_add_shopping_item(f"买{args}", {}, family_id=family_id)
        elif cmd == '/remind':
            if not args:
                return (
                    "📅 请告诉我提醒内容，例如:\n"
                    "  `/remind 明天下午3点开会`\n"
                    "  `/remind 周五买菜`"
                )
            return self.task_executor._handle_create_reminder(f"提醒我{args}", {}, family_id=family_id)
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
        elif cmd == '/wedding':
            return self._handle_wedding_command(args, family_id=family_id)
        elif cmd == '/insurance':
            return self._handle_insurance_command(args, family_id=family_id)
        elif cmd == '/documents':
            return self._handle_documents_command(args, family_id=family_id)
        elif cmd == '/housing':
            return self._handle_housing_command(args, family_id=family_id)
        elif cmd == '/health':
            return self._handle_health_command(args, family_id=family_id)
        elif cmd == '/travel':
            return self._handle_travel_command(args, family_id=family_id)
        elif cmd == '/vehicle':
            return self._handle_vehicle_command(args, family_id=family_id)
        elif cmd == '/fitness':
            return self._handle_fitness_command(args, family_id=family_id)
        elif cmd == '/finance':
            return self._handle_finance_command(args)
        elif cmd == '/memory':
            return self._handle_memory_command(args, user_id=user_id, family_id=family_id)
        elif cmd == '/help':
            return (
                "📋 **可用指令:**\n"
                "  `/shopping <物品>` - 添加购物清单\n"
                "  `/remind <内容>` - 创建日程提醒\n"
                "  `/knowledge <问题>` - 搜索知识库\n"
                "  `/wedding list` - 查看备婚事项\n"
                "  `/insurance list` - 查看保险记录\n"
                "  `/documents list` - 查看证件记录\n"
                "  `/housing list` - 查看住房记录\n"
                "  `/health list` - 查看健康记录\n"
                "  `/travel summary` - 查看旅行概览\n"
                "  `/travel list` - 查看旅行记录\n"
                "  `/vehicle list` - 查看车辆记录\n"
                "  `/fitness list` - 查看健身记录\n"
                "  `/finance summary` - 查看本月财务摘要\n"
                "  `/memory <关键词>` - 搜索记忆\n"
                "  `/photo` - 上传照片\n"
                "  `/help` - 显示此帮助\n\n"
                "💡 **普通聊天**时，如果检测到相关意图，我会先询问你确认再执行。"
            )
        else:
            return f"未知指令: {cmd}\n输入 `/help` 查看可用指令列表。"

    def _handle_module_query(self, message: str, family_id: str = None) -> Optional[str]:
        if not self.db:
            return None

        text = (message or "").strip()
        if not text:
            return None

        query_words = ('查看', '看看', '查询', '列出', '统计', '总结', '汇总', '情况', '进度')

        if '备婚' in text and any(word in text for word in query_words):
            return self._handle_wedding_command('summary', family_id=family_id)
        if ('保险' in text or '保单' in text) and any(word in text for word in query_words):
            return self._handle_insurance_command('summary', family_id=family_id)
        if ('证件' in text or '身份证' in text or '护照' in text or '驾照' in text) and any(word in text for word in query_words):
            return self._handle_documents_command('summary', family_id=family_id)
        if ('住房' in text or '房租' in text or '房贷' in text or '物业' in text or '水电' in text or '维修' in text) and any(word in text for word in query_words):
            return self._handle_housing_command('summary', family_id=family_id)
        if ('健康' in text or '体检' in text or '用药' in text or '复诊' in text or '慢病' in text or '医院' in text) and any(word in text for word in query_words):
            return self._handle_health_command('summary', family_id=family_id)
        if ('车辆' in text or '保养' in text or '车' in text) and any(word in text for word in query_words):
            return self._handle_vehicle_command('summary', family_id=family_id)
        if ('健身' in text or '训练' in text or '体重' in text or '饮食' in text) and any(word in text for word in query_words):
            return self._handle_fitness_command('summary', family_id=family_id)
        if ('财务' in text or '收支' in text or '账单' in text) and any(word in text for word in query_words):
            return self._handle_finance_command('summary')
        return None

    def _handle_wedding_command(self, args: str, family_id: str = None) -> str:
        if not self.db:
            return "备婚模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        items = self.db.get_wedding_items(family_id=family_id or "")
        if action.startswith('add '):
            raw = action[4:].strip()
            parts = [part.strip() for part in raw.split('|')]
            if len(parts) < 2:
                return "用法示例：`/wedding add todo|确定伴手礼名单|我|2026-06-01`"
            item_type = parts[0]
            title = parts[1]
            owner = parts[2] if len(parts) > 2 else ""
            item_date = parts[3] if len(parts) > 3 else ""
            self.db.add_wedding_item(item_type=item_type, title=title, owner=owner, item_date=item_date, family_id=family_id or "")
            return f"已新增备婚事项：{title}"
        if action == 'list':
            if not items:
                return "当前还没有备婚记录。"
            lines = [f"- {item.get('title')} | {item.get('item_type')} | {item.get('status')}" for item in items[:8]]
            return "备婚记录：\n" + "\n".join(lines)
        budget_total = sum(float(item.get('planned_amount') or 0) for item in items if item.get('item_type') == 'budget')
        spent_total = sum(float(item.get('amount') or 0) for item in items if item.get('item_type') == 'budget')
        todo_count = sum(1 for item in items if item.get('item_type') == 'todo' and item.get('status') != 'done')
        return (
            f"备婚概览：\n"
            f"- 总事项：{len(items)}\n"
            f"- 待办：{todo_count}\n"
            f"- 预算总额：¥{budget_total:.0f}\n"
            f"- 已支付：¥{spent_total:.0f}\n"
            f"- 继续查看可用 `/wedding list`"
        )

    def _handle_insurance_command(self, args: str, family_id: str = None) -> str:
        if not self.db:
            return "保险模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        items = self.db.get_insurance_policies(family_id=family_id or "")
        if action.startswith('add '):
            name = action[4:].strip()
            if not name:
                return "用法示例：`/insurance add 重疾险`"
            self.db.add_insurance_policy(name=name, family_id=family_id or "")
            return f"已新增保险记录：{name}"
        if action == 'list':
            if not items:
                return "当前还没有保险记录。"
            lines = [f"- {item.get('name') or item.get('title')} | {item.get('record_type')} | {item.get('status')}" for item in items[:8]]
            return "保险记录：\n" + "\n".join(lines)
        policies = [item for item in items if (item.get('record_type') or 'policy') == 'policy']
        claims = [item for item in items if item.get('record_type') == 'claim']
        return (
            f"保险概览：\n"
            f"- 保单数：{len(policies)}\n"
            f"- 理赔事项：{len(claims)}\n"
            f"- 年保费：¥{sum(float(item.get('premium') or 0) for item in policies):.0f}\n"
            f"- 继续查看可用 `/insurance list`"
        )

    def _handle_documents_command(self, args: str, family_id: str = None) -> str:
        from datetime import datetime
        if not self.db:
            return "证件管理模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        items = self.db.get_document_records(family_id=family_id or "")
        if action == 'list':
            if not items:
                return "当前还没有证件记录。"
            lines = [f"- {item.get('title')} | {item.get('holder')} | {item.get('expiry_date') or '未设置到期'}" for item in items[:8]]
            return "证件记录：\n" + "\n".join(lines)
        expiring_soon = 0
        expired = 0
        active = 0
        today = datetime.now().date()
        for item in items:
            try:
                expiry = datetime.strptime(item.get('expiry_date') or '', "%Y-%m-%d").date()
            except Exception:
                expiry = None
            if not expiry:
                active += 1
                continue
            if expiry < today:
                expired += 1
            else:
                active += 1
                if (expiry - today).days <= int(item.get('reminder_days') or 30):
                    expiring_soon += 1
        return (
            f"证件概览：\n"
            f"- 总数：{len(items)}\n"
            f"- 有效：{active}\n"
            f"- 临近到期：{expiring_soon}\n"
            f"- 已失效：{expired}\n"
            f"- 继续查看可用 `/documents list`"
        )

    def _handle_housing_command(self, args: str, family_id: str = None) -> str:
        from datetime import datetime
        if not self.db:
            return "住房管理模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        items = self.db.get_housing_records(family_id=family_id or "")
        if action.startswith('add '):
            title = action[4:].strip()
            if not title:
                return "用法示例：`/housing add 本月房租`"
            self.db.add_housing_record(record_type='rent', title=title, family_id=family_id or "")
            return f"已新增住房记录：{title}"
        if action == 'list':
            if not items:
                return "当前还没有住房记录。"
            lines = [f"- {item.get('title')} | {item.get('record_type')} | {item.get('status') or '-'}" for item in items[:8]]
            return "住房记录：\n" + "\n".join(lines)
        today = datetime.now().date()
        due_soon = 0
        overdue = 0
        for item in items:
            due = None
            try:
                if item.get('due_date'):
                    due = datetime.strptime(item.get('due_date'), "%Y-%m-%d").date()
            except Exception:
                due = None
            if not due:
                continue
            if due < today:
                overdue += 1
            elif (due - today).days <= 7:
                due_soon += 1
        return (
            f"住房概览：\n"
            f"- 总数：{len(items)}\n"
            f"- 房屋档案：{sum(1 for item in items if item.get('record_type') == 'property')}\n"
            f"- 房租：{sum(1 for item in items if item.get('record_type') == 'rent')}\n"
            f"- 水电物业：{sum(1 for item in items if item.get('record_type') == 'utility')}\n"
            f"- 维修报修：{sum(1 for item in items if item.get('record_type') == 'repair')}\n"
            f"- 临近到期：{due_soon}\n"
            f"- 已逾期：{overdue}\n"
            f"- 继续查看可用 `/housing list`"
        )

    def _handle_health_command(self, args: str, family_id: str = None) -> str:
        from datetime import datetime
        if not self.db:
            return "健康管理模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        items = self.db.get_health_records(family_id=family_id or "")
        if action.startswith('add '):
            title = action[4:].strip()
            if not title:
                return "用法示例：`/health add 体检报告`"
            record_type = 'exam'
            normalized_title = title
            if any(k in title for k in ['用药', '服药', '药物', '吃药']):
                record_type = 'medication'
                normalized_title = re.sub(r'^(用药|服药|药物|吃药)\s*', '', title).strip()
            elif any(k in title for k in ['复诊', '复查', '回诊', '预约']):
                record_type = 'followup'
                normalized_title = re.sub(r'^(复诊|复查|回诊|预约)\s*', '', title).strip()
            elif any(k in title for k in ['慢病', '高血压', '糖尿病', '慢性病']):
                record_type = 'chronic'
                normalized_title = re.sub(r'^(慢病|高血压|糖尿病|慢性病)\s*', '', title).strip()
            title = normalized_title or title
            self.db.add_health_record(record_type=record_type, title=title, family_id=family_id or "")
            return f"已新增健康记录：{title}（{record_type}）"
        if action == 'list':
            if not items:
                return "当前还没有健康记录。"
            lines = [f"- {item.get('title')} | {item.get('record_type')} | {item.get('status') or '-'}" for item in items[:8]]
            return "健康记录：\n" + "\n".join(lines)
        today = datetime.now().date()
        due_soon = 0
        overdue = 0
        for item in items:
            try:
                visit = datetime.strptime(item.get('next_visit') or '', "%Y-%m-%d").date()
            except Exception:
                visit = None
            if not visit:
                continue
            if visit < today:
                overdue += 1
            elif (visit - today).days <= 14:
                due_soon += 1
        return (
            f"健康概览：\n"
            f"- 总数：{len(items)}\n"
            f"- 体检：{sum(1 for item in items if item.get('record_type') == 'exam')}\n"
            f"- 用药：{sum(1 for item in items if item.get('record_type') == 'medication')}\n"
            f"- 复诊：{sum(1 for item in items if item.get('record_type') == 'followup')}\n"
            f"- 慢病：{sum(1 for item in items if item.get('record_type') == 'chronic')}\n"
            f"- 临近复诊：{due_soon}\n"
            f"- 已逾期：{overdue}\n"
            f"- 继续查看可用 `/health list`"
        )

    def _handle_travel_command(self, args: str, family_id: str = None) -> str:
        from datetime import datetime
        if not self.db:
            return "旅行管理模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        items = self.db.get_travel_records(family_id=family_id or "")
        if action.startswith('add '):
            title = action[4:].strip()
            if not title:
                return "用法示例：`/travel add 国庆去杭州`"
            record_type = 'itinerary'
            if any(k in title for k in ['预算', '费用', '花费', '支出']):
                record_type = 'budget'
            elif any(k in title for k in ['预订', '订票', '机票', '酒店', '门票']):
                record_type = 'booking'
            elif any(k in title for k in ['打包', '行李', '清单']):
                record_type = 'packing'
            self.db.add_travel_record(record_type=record_type, title=title, family_id=family_id or "")
            return f"已新增旅行记录：{title}（{record_type}）"
        if action == 'list':
            if not items:
                return "当前还没有旅行记录。"
            lines = [f"- {item.get('title')} | {item.get('record_type')} | {item.get('status') or '-'}" for item in items[:8]]
            return "旅行记录：\n" + "\n".join(lines)
        today = datetime.now().date()
        upcoming = 0
        for item in items:
            try:
                travel_date = datetime.strptime(item.get('travel_date') or '', "%Y-%m-%d").date()
            except Exception:
                travel_date = None
            if not travel_date:
                continue
            if 0 <= (travel_date - today).days <= 30:
                upcoming += 1
        return (
            f"旅行概览：\n"
            f"- 总数：{len(items)}\n"
            f"- 行程：{sum(1 for item in items if item.get('record_type') == 'itinerary')}\n"
            f"- 预订：{sum(1 for item in items if item.get('record_type') == 'booking')}\n"
            f"- 预算：{sum(1 for item in items if item.get('record_type') == 'budget')}\n"
            f"- 打包：{sum(1 for item in items if item.get('record_type') == 'packing')}\n"
            f"- 近30天行程：{upcoming}\n"
            f"- 继续查看可用 `/travel list`"
        )

    def _handle_vehicle_command(self, args: str, family_id: str = None) -> str:
        if not self.db:
            return "车辆模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        items = self.db.get_vehicle_records(family_id=family_id or "")
        if action.startswith('add '):
            title = action[4:].strip()
            if not title:
                return "用法示例：`/vehicle add 本月保养`"
            self.db.add_vehicle_record(record_type='service', title=title, family_id=family_id or "")
            return f"已新增车辆记录：{title}"
        if action == 'list':
            if not items:
                return "当前还没有车辆记录。"
            lines = [f"- {item.get('title')} | {item.get('record_type')} | {item.get('status') or '-'}" for item in items[:8]]
            return "车辆记录：\n" + "\n".join(lines)
        return (
            f"车辆概览：\n"
            f"- 车辆档案：{sum(1 for item in items if item.get('record_type') == 'vehicle')}\n"
            f"- 保养记录：{sum(1 for item in items if item.get('record_type') == 'service')}\n"
            f"- 费用合计：¥{sum(float(item.get('amount') or 0) for item in items if item.get('record_type') == 'expense'):.0f}\n"
            f"- 继续查看可用 `/vehicle list`"
        )

    def _handle_fitness_command(self, args: str, family_id: str = None) -> str:
        if not self.db:
            return "健身模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        items = self.db.get_fitness_records(family_id=family_id or "")
        if action.startswith('add '):
            title = action[4:].strip()
            if not title:
                return "用法示例：`/fitness add 力量训练`"
            self.db.add_fitness_record(record_type='workout', title=title, family_id=family_id or "")
            return f"已新增健身记录：{title}"
        if action == 'list':
            if not items:
                return "当前还没有健身记录。"
            lines = [f"- {item.get('title')} | {item.get('record_type')} | {item.get('record_date') or '-'}" for item in items[:8]]
            return "健身记录：\n" + "\n".join(lines)
        metrics = [item for item in items if item.get('record_type') == 'metric']
        avg_weight = sum(float(item.get('weight') or 0) for item in metrics) / len(metrics) if metrics else 0
        return (
            f"健身概览：\n"
            f"- 训练记录：{sum(1 for item in items if item.get('record_type') == 'workout')}\n"
            f"- 身体记录：{len(metrics)}\n"
            f"- 平均体重：{avg_weight:.1f} kg\n"
            f"- 饮食记录：{sum(1 for item in items if item.get('record_type') == 'meal')}\n"
            f"- 继续查看可用 `/fitness list`"
        )

    def _handle_finance_command(self, args: str) -> str:
        if not self.db:
            return "财务模块当前不可用，数据库还没有连上。"
        action = (args or 'summary').strip()
        if action not in ('summary', 'month', ''):
            return "当前支持：`/finance summary`"
        from datetime import datetime
        now = datetime.now()
        summary = self.db.get_monthly_summary(now.year, now.month)
        return (
            f"{now.year}年{now.month}月财务概览：\n"
            f"- 收入：¥{summary.get('total_income', 0):.2f}\n"
            f"- 支出：¥{summary.get('total_expense', 0):.2f}\n"
            f"- 结余：¥{summary.get('balance', 0):.2f}"
        )

    def _handle_memory_command(self, args: str, user_id: str = None, family_id: str = None) -> str:
        query = (args or '').strip()
        if not query:
            return "用法示例：`/memory 车辆保养`"
        items = self.memory_manager.list_memories(query=query, limit=8, user_id=user_id, family_id=family_id)
        if not items:
            return f"没有找到和“{query}”相关的记忆。"
        lines = [f"- {item.get('content', '')[:80]}" for item in items[:8]]
        return "相关记忆：\n" + "\n".join(lines)

    def _build_confirmation_message(self, intent: str, message: str) -> str:
        """构建确认询问消息"""
        prompts = {
            'create_reminder': f"📅 我检测到你想创建日程提醒，请确认是否执行？(是/否)",
            'add_shopping_item': f"🛒 我检测到你想添加购物清单，请确认是否执行？(是/否)",
            'add_wedding_item': f"💍 我检测到你想新增备婚事项，请确认是否执行？(是/否)",
            'add_insurance_record': f"🛡️ 我检测到你想新增保险记录，请确认是否执行？(是/否)",
            'add_vehicle_record': f"🚗 我检测到你想新增车辆记录，请确认是否执行？(是/否)",
            'add_fitness_record': f"🏋️ 我检测到你想新增健身记录，请确认是否执行？(是/否)",
            'search_knowledge': f"📚 我检测到你想搜索知识库，请确认是否执行？(是/否)",
            'upload_photo': f"📸 我检测到你想上传照片，请确认是否执行？(是/否)",
            'query_member': f"👤 我检测到你想查询家庭成员信息，请确认是否执行？(是/否)",
            'assign_task': f"✅ 我检测到你想分配任务，请确认是否执行？(是/否)",
            'add_knowledge': f"📚 我检测到你想把这条信息记到知识库，请确认是否执行？(是/否)",
        }
        return prompts.get(intent, f"我检测到你想执行操作，请确认是否执行？(是/否)")

    def _execute_pending_action(self, pending: dict, user_id: str = None, family_id: str = None) -> str:
        """执行待确认的操作"""
        intent = pending['intent']
        message = pending['message']
        # 使用 task_executor 执行
        return self.task_executor.execute(message, user_id, family_id=family_id)
    
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
    
    def add_reminder(self, date: str, event: str, members: List[str] = None, family_id: str = None):
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
                self.db.add_reminder(date, event, family_id=family_id or "")
            except Exception as e:
                logger.warning(f"保存日程到数据库失败: {e}")
    
    def get_upcoming_events(self, days: int = 30) -> List[Dict]:
        """获取即将事件"""
        return self.events[:10]  # 简化实现
    
    def get_all_members(self):
        """获取所有成员"""
        return list(self.members.values())
