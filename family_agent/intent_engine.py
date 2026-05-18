"""
智能意图识别和任务执行引擎
让AI助手能够理解用户意图并自动执行相应操作
"""

import re
from typing import Dict, Optional, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class IntentRecognizer:
    """意图识别器"""
    
    def __init__(self):
        # 定义意图模式
        self.intent_patterns = {
            'create_reminder': [
                r'提醒我(.+)',
                r'设置提醒(.+)',
                r'记住(.+)',
                r'别忘了(.+)',
                r'安排(.+)',
                r'要去(.+)',
                r'准备去(.+)',
            ],
            'add_shopping_item': [
                r'买(.+)',
                r'购买(.+)',
                r'添加到购物清单(.+)',
                r'购物清单加上(.+)',
                r'需要买(.+)',
            ],
            'search_knowledge': [
                r'查询(.+)',
                r'搜索(.+)',
                r'查找(.+)',
                r'了解一下(.+)',
                r'(.+)是什么',
                r'(.+)怎么做',
            ],
            'query_member': [
                r'(.+)的信息',
                r'查看(.+)',
                r'(.+)是谁',
            ],
            'upload_photo': [
                r'上传照片',
                r'保存照片',
                r'存照片',
            ],
            'smart_home_control': [
                r'打开(.+)',
                r'关闭(.+)',
                r'调节(.+)',
                r'设置(.+)',
            ],
            'assign_task': [
                r'让(.+)买(.+)',
                r'叫(.+)买(.+)',
                r'请(.+)买(.+)',
                r'提醒(.+)买(.+)',
                r'让(.+)(.+)',
                r'叫(.+)(.+)',
            ],
            'add_knowledge': [
                r'记一下(.+)',
                r'记录一下(.+)',
                r'添加到知识库(.+)',
                r'保存到知识库(.+)',
                r'学一下(.+)',
                r'知识库记(.+)',
                r'记住这个知识(.+)',
            ],
        }
    
    def recognize_intent(self, message: str) -> Dict:
        """
        识别用户意图
        
        Returns:
            {
                'intent': 'create_reminder',
                'confidence': 0.9,
                'entities': {...}
            }
        """
        
        message_lower = message.lower()

        # 先做模块级启发式识别，避免被通用“查看/查询”模式提前吞掉
        if any(k in message for k in ['备婚', '婚礼']):
            if any(k in message for k in ['查看', '看看', '查询', '统计', '汇总', '情况', '进度']):
                return {'intent': 'query_wedding', 'confidence': 0.9, 'raw_text': message}
            if any(k in message for k in ['添加', '新增', '加一个', '记一条', '记个', '补一个']):
                return {'intent': 'add_wedding_item', 'confidence': 0.88, 'raw_text': message}

        if any(k in message for k in ['保险', '保单', '续保', '理赔', '车险']):
            if any(k in message for k in ['查看', '看看', '查询', '统计', '汇总', '情况']):
                return {'intent': 'query_insurance', 'confidence': 0.9, 'raw_text': message}
            if any(k in message for k in ['添加', '新增', '加一个', '记一条', '补一个']):
                return {'intent': 'add_insurance_record', 'confidence': 0.88, 'raw_text': message}

        if any(k in message for k in ['车辆', '保养', '年检']) or ('车' in message and '车险' not in message):
            if any(k in message for k in ['查看', '看看', '查询', '统计', '汇总', '情况']):
                return {'intent': 'query_vehicle', 'confidence': 0.88, 'raw_text': message}
            if any(k in message for k in ['添加', '新增', '加一个', '记一条', '补一个']):
                return {'intent': 'add_vehicle_record', 'confidence': 0.86, 'raw_text': message}

        if any(k in message for k in ['健身', '训练', '体重', '体脂', '饮食', '热量', '蛋白']):
            if any(k in message for k in ['查看', '看看', '查询', '统计', '汇总', '情况']):
                return {'intent': 'query_fitness', 'confidence': 0.88, 'raw_text': message}
            if any(k in message for k in ['添加', '新增', '加一个', '记一条', '补一个', '记下']):
                return {'intent': 'add_fitness_record', 'confidence': 0.86, 'raw_text': message}

        if any(k in message for k in ['财务', '收支', '账单', '支出', '收入']):
            if any(k in message for k in ['查看', '看看', '查询', '统计', '汇总', '情况']):
                return {'intent': 'query_finance', 'confidence': 0.88, 'raw_text': message}
            if any(k in message for k in ['记', '新增', '添加', '花了', '支出', '收入了', '赚了']):
                return {'intent': 'add_finance_record', 'confidence': 0.86, 'raw_text': message}
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    return {
                        'intent': intent,
                        'confidence': 0.85,
                        'matched_pattern': pattern,
                        'raw_text': message
                    }
        
        # 默认意图
        return {
            'intent': 'chat',
            'confidence': 0.5,
            'raw_text': message
        }


class TaskExecutor:
    """任务执行器"""
    
    def __init__(self, agent_core):
        self.agent = agent_core
        self.intent_recognizer = IntentRecognizer()
    
    def execute(self, message: str, user_id: str = None, family_id: str = None) -> Optional[str]:
        """
        执行任务
        
        Returns:
            如果执行了任务,返回执行结果;否则返回None继续正常对话
        """
        
        # 1. 识别意图
        intent_result = self.intent_recognizer.recognize_intent(message)
        intent = intent_result['intent']
        
        logger.info(f"识别到意图: {intent}")
        
        # 2. 根据意图执行相应操作
        if intent == 'create_reminder':
            return self._handle_create_reminder(message, intent_result, family_id=family_id)
        
        elif intent == 'add_shopping_item':
            return self._handle_add_shopping_item(message, intent_result, family_id=family_id)
        
        elif intent == 'search_knowledge':
            return self._handle_search_knowledge(message, intent_result)

        elif intent == 'query_wedding':
            return self._handle_query_wedding(message, family_id=family_id)

        elif intent == 'add_wedding_item':
            return self._handle_add_wedding_item(message, family_id=family_id)

        elif intent == 'query_insurance':
            return self._handle_query_insurance(message, family_id=family_id)

        elif intent == 'add_insurance_record':
            return self._handle_add_insurance_record(message, family_id=family_id)

        elif intent == 'query_vehicle':
            return self._handle_query_vehicle(message, family_id=family_id)

        elif intent == 'add_vehicle_record':
            return self._handle_add_vehicle_record(message, family_id=family_id)

        elif intent == 'query_fitness':
            return self._handle_query_fitness(message, family_id=family_id)

        elif intent == 'add_fitness_record':
            return self._handle_add_fitness_record(message, family_id=family_id)

        elif intent == 'query_finance':
            return self._handle_query_finance(message)

        elif intent == 'add_finance_record':
            return self._handle_add_finance_record(message, user_id=user_id)
        
        elif intent == 'query_member':
            return self._handle_query_member(message, intent_result)
        
        elif intent == 'upload_photo':
            return self._handle_upload_photo(message, intent_result)
        
        elif intent == 'assign_task':
            return self._handle_assign_task(message, intent_result, user_id=user_id, family_id=family_id)

        elif intent == 'add_knowledge':
            return self._handle_add_knowledge(message, intent_result)

        # 其他意图交给正常对话流程
        return None
    
    def _handle_create_reminder(self, message: str, intent: Dict, family_id: str = None) -> str:
        """处理创建提醒"""

        # 提取时间
        time_pattern = r'(今天|明天|后天|\d+月\d+日|\d+:\d+|周[一二三四五六日])'
        time_match = re.search(time_pattern, message)
        date_str = self._parse_time(time_match.group(0) if time_match else "明天")

        # 提取事件：去掉时间词和意向词，剩下的就是事件
        event_clean = message
        # 去掉匹配到的时间
        if time_match:
            event_clean = event_clean.replace(time_match.group(0), '', 1)
        # 去掉常用语气词
        for word in ['我要', '我想', '打算', '准备', '要去', '想去', '需要', '安排',
                     '提醒我', '设置提醒', '记住', '别忘了', '帮我']:
            event_clean = event_clean.replace(word, '', 1)
        event_clean = event_clean.strip().strip('，,。.!！?？')

        if event_clean:
            self.agent.add_reminder(date_str, event_clean, family_id=family_id)

            return f"✅ 已添加到日程安排:\n📅 时间: {date_str}\n📝 事件: {event_clean}\n\n你可以随时查看和管理日程!"

        return "抱歉,我没有理解清楚。请告诉我具体要做什么事?"
    
    def _handle_add_shopping_item(self, message: str, intent: Dict, family_id: str = None) -> str:
        """处理添加购物项"""
        
        # 提取物品名称
        item_match = re.search(r'买(.+)|购买(.+)|添加到购物清单(.+)|购物清单加上(.+)|需要买(.+)', message)
        
        if item_match:
            item_name = (item_match.group(1) or item_match.group(2) or 
                        item_match.group(3) or item_match.group(4) or 
                        item_match.group(5)).strip()
            
            # 添加到购物清单
            self.agent.shopping_list.add_item(
                name=item_name,
                quantity="1",
                category="general",
                priority="normal",
                family_id=family_id or ""
            )
            
            return f"✅ 已添加到购物清单:\n🛒 物品: {item_name}\n\n你可以在购物清单页面查看和管理!"
        
        return "抱歉,我没有听清楚要买什么。能再说一遍吗?"
    
    def _handle_search_knowledge(self, message: str, intent: Dict) -> str:
        """处理知识搜索"""
        
        # 提取搜索关键词
        query_match = re.search(r'查询(.+)|搜索(.+)|查找(.+)|了解一下(.+)|(.+)是什么|(.+)怎么做', message)
        
        if query_match:
            query = (query_match.group(1) or query_match.group(2) or 
                    query_match.group(3) or query_match.group(4) or
                    query_match.group(5) or query_match.group(6)).strip()
            
            # 搜索知识库
            results = self.agent.knowledge_base.search(query, n_results=3)
            
            if results:
                response = f"🔍 找到相关知识:\n\n"
                for i, result in enumerate(results[:2], 1):
                    content = result['content'][:200]
                    response += f"{i}. {content}...\n\n"
                
                response += "\n💡 你可以在知识库页面查看更多详细信息!"
                return response
            else:
                return f"📚 暂时没有找到关于'{query}'的知识。\n\n你可以:\n1. 在知识库页面手动添加相关知识\n2. 问我其他问题"
        
        return None
    
    def _handle_query_member(self, message: str, intent: Dict) -> str:
        """处理成员查询"""
        
        # 提取成员姓名
        name_match = re.search(r'(.+)的信息|查看(.+)|(.+)是谁', message)
        
        if name_match:
            name = (name_match.group(1) or name_match.group(2) or name_match.group(3)).strip()
            
            member = self.agent.get_member(name)
            
            if member:
                return (f"👤 家庭成员信息:\n"
                       f"姓名: {member.name}\n"
                       f"角色: {member.role}\n"
                       f"年龄: {member.age}\n"
                       f"交互风格: {member.interaction_style.value}\n"
                       f"权限等级: {member.permission.value}")
            else:
                return f"❌ 没有找到名为'{name}'的家庭成员。\n\n你可以在家庭成员页面添加新成员。"
        
        return None
    
    def _handle_upload_photo(self, message: str, intent: Dict) -> str:
        """处理照片上传提示"""
        return "📸 请在聊天框中点击上传按钮选择照片,我会自动分析并保存到照片记忆中!"

    def _handle_query_wedding(self, message: str, family_id: str = None) -> str:
        action = 'list' if any(k in message for k in ['列出', '列表', '明细']) else 'summary'
        return self.agent._handle_wedding_command(action, family_id=family_id)

    def _handle_add_wedding_item(self, message: str, family_id: str = None) -> str:
        item_type = 'todo'
        if any(k in message for k in ['预算', '费用', '花费']):
            item_type = 'budget'
        elif any(k in message for k in ['酒店', '摄影', '司仪', '化妆', '供应商']):
            item_type = 'vendor'
        elif any(k in message for k in ['时间', '节点', '档期']):
            item_type = 'timeline'
        title = re.sub(r'.*(添加|新增|加一个|记一条|补一个)', '', message).strip('：: ，,。')
        title = title or '新的备婚事项'
        self.agent.db.add_wedding_item(item_type=item_type, title=title, family_id=family_id or "")
        return f"✅ 已新增备婚记录：{title}\n类型：{item_type}"

    def _handle_query_insurance(self, message: str, family_id: str = None) -> str:
        action = 'list' if any(k in message for k in ['列出', '列表', '明细']) else 'summary'
        return self.agent._handle_insurance_command(action, family_id=family_id)

    def _handle_add_insurance_record(self, message: str, family_id: str = None) -> str:
        record_type = 'policy'
        if any(k in message for k in ['提醒', '续保']):
            record_type = 'reminder'
        elif any(k in message for k in ['理赔']):
            record_type = 'claim'
        title = re.sub(r'.*(添加|新增|加一个|记一条|补一个)', '', message).strip('：: ，,。')
        title = title or '新的保险记录'
        self.agent.db.add_insurance_policy(name=title, title=title, record_type=record_type, family_id=family_id or "")
        return f"✅ 已新增保险记录：{title}\n类型：{record_type}"

    def _handle_query_vehicle(self, message: str, family_id: str = None) -> str:
        action = 'list' if any(k in message for k in ['列出', '列表', '明细']) else 'summary'
        return self.agent._handle_vehicle_command(action, family_id=family_id)

    def _handle_add_vehicle_record(self, message: str, family_id: str = None) -> str:
        record_type = 'vehicle'
        if any(k in message for k in ['保养', '机油', '维修']):
            record_type = 'service'
        elif any(k in message for k in ['费用', '加油', '停车']):
            record_type = 'expense'
        title = re.sub(r'.*(添加|新增|加一个|记一条|补一个)', '', message).strip('：: ，,。')
        title = title or '新的车辆记录'
        self.agent.db.add_vehicle_record(record_type=record_type, title=title, family_id=family_id or "")
        return f"✅ 已新增车辆记录：{title}\n类型：{record_type}"

    def _handle_query_fitness(self, message: str, family_id: str = None) -> str:
        action = 'list' if any(k in message for k in ['列出', '列表', '明细']) else 'summary'
        return self.agent._handle_fitness_command(action, family_id=family_id)

    def _handle_add_fitness_record(self, message: str, family_id: str = None) -> str:
        record_type = 'workout'
        kwargs = {}
        if any(k in message for k in ['体重', '体脂', '腰围']):
            record_type = 'metric'
            weight_match = re.search(r'(\d+(?:\.\d+)?)\s*kg', message.lower())
            if weight_match:
                kwargs['weight'] = float(weight_match.group(1))
        elif any(k in message for k in ['早餐', '午餐', '晚餐', '加餐', '饮食', '热量', '蛋白']):
            record_type = 'meal'
            protein_match = re.search(r'(\d+(?:\.\d+)?)\s*g', message.lower())
            if protein_match:
                kwargs['protein'] = float(protein_match.group(1))
        duration_match = re.search(r'(\d+)\s*分钟', message)
        if duration_match:
            kwargs['duration'] = float(duration_match.group(1))
        calorie_match = re.search(r'(\d+)\s*k?cal', message.lower())
        if calorie_match:
            kwargs['calories'] = float(calorie_match.group(1))
        title = re.sub(r'.*(添加|新增|加一个|记一条|补一个|记下)', '', message).strip('：: ，,。')
        title = title or '新的健身记录'
        self.agent.db.add_fitness_record(record_type=record_type, title=title, family_id=family_id or "", **kwargs)
        return f"✅ 已新增健身记录：{title}\n类型：{record_type}"

    def _handle_query_finance(self, message: str) -> str:
        return self.agent._handle_finance_command('summary')

    def _handle_add_finance_record(self, message: str, user_id: str = None) -> str:
        amount_match = re.search(r'(\d+(?:\.\d+)?)', message)
        if not amount_match:
            return "抱歉，我没识别到金额。比如：`今天买菜花了 68`。"

        amount = float(amount_match.group(1))
        is_income = any(k in message for k in ['收入', '进账', '赚了', '收到'])
        transaction_type = 'income' if is_income else 'expense'

        category_map = [
            ('餐饮', ['吃饭', '晚饭', '午饭', '早餐', '外卖', '买菜', '奶茶']),
            ('交通', ['打车', '地铁', '公交', '加油', '停车', '高速']),
            ('购物', ['买', '下单', '淘宝', '京东', '拼多多']),
            ('医疗', ['医院', '药', '体检']),
            ('娱乐', ['电影', '游戏', '唱歌', '聚会']),
            ('教育', ['课程', '学费', '书', '培训']),
        ]

        category = '其他收入' if is_income else '其他支出'
        for candidate, keywords in category_map:
            if any(keyword in message for keyword in keywords):
                category = candidate
                break

        description = re.sub(r'(\d+(?:\.\d+)?)', '', message).strip('：: ，,。')
        today = datetime.now().strftime('%Y-%m-%d')
        tid = self.agent.db.add_transaction(
            amount=amount,
            transaction_type=transaction_type,
            category=category,
            description=description,
            transaction_date=today,
            created_by=user_id or '',
        )
        direction = '收入' if is_income else '支出'
        return f"✅ 已记一笔{direction}：¥{amount:.2f}\n分类：{category}\n日期：{today}"
    
    def _handle_assign_task(self, message: str, intent: Dict, user_id: str = None, family_id: str = None) -> str:
        """处理分配任务"""
        
        # 提取目标成员和任务内容
        patterns = [
            r'让(.+)买(.+)',
            r'叫(.+)买(.+)',
            r'请(.+)买(.+)',
            r'提醒(.+)买(.+)',
            r'让(.+)(.+)',
            r'叫(.+)(.+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                to_member = match.group(1).strip()
                task_content = match.group(2).strip()
                
                # 如果是"买"开头的,添加到购物清单
                if '买' in task_content:
                    item_name = task_content.replace('买', '').strip()
                    
                    # 创建家庭任务
                    self.agent.task_manager.create_task(
                        from_member=user_id or "当前用户",
                        to_member=to_member,
                        content=f"买{item_name}",
                        task_type="shopping",
                        priority="normal",
                        family_id=family_id or ""
                    )
                    
                    # 同时也添加到购物清单
                    self.agent.shopping_list.add_item(
                        name=item_name,
                        quantity="1",
                        category="general",
                        priority="normal",
                        notes=f"由 {to_member} 购买",
                        family_id=family_id or ""
                    )
                    
                    return (f"✅ 已创建任务并通知 {to_member}:\n"
                           f"📝 任务: 买{item_name}\n"
                           f"🛒 已添加到购物清单\n\n"
                           f"当 {to_member} 登录时,会看到这个任务!")
                else:
                    # 一般任务
                    self.agent.task_manager.create_task(
                        from_member=user_id or "当前用户",
                        to_member=to_member,
                        content=task_content,
                        task_type="general",
                        priority="normal",
                        family_id=family_id or ""
                    )
                    
                    return (f"✅ 已给 {to_member} 分配任务:\n"
                           f"📝 内容: {task_content}\n\n"
                           f"当 {to_member} 登录时会看到!")
        
        return "抱歉,我没有理解清楚。格式例如:'让妈妈买一袋米'"

    def _classify_category(self, text: str) -> str:
        """根据文本内容自动分类"""
        if re.search(r'感冒|发烧|咳嗽|健康|药|病|养生|锻炼|体检|营养|饮食|运动', text):
            return 'health'
        if re.search(r'菜|做饭|食谱|烹饪|美食|好吃|食材|厨房', text):
            return 'cooking'
        if re.search(r'钱|理财|投资|省|花|预算|存款|股票|保险|账单', text):
            return 'finance'
        if re.search(r'旅游|旅行|去|玩|景点|酒店|机票|出发', text):
            return 'travel'
        if re.search(r'法|律师|合同|权益|条款|规定|政策', text):
            return 'legal'
        if re.search(r'教育|学习|学校|考试|老师|课程|孩子|儿童', text):
            return 'education'
        if re.search(r'老婆|老公|家人|家庭|关系|沟通|相处|父母|孩子|感情', text):
            return 'relationship'
        return 'general'

    def _handle_add_knowledge(self, message: str, intent: Dict) -> str:
        """处理添加到知识库"""
        # 提取要保存的内容
        patterns = [
            r'记一下(.+)',
            r'记录一下(.+)',
            r'添加到知识库(.+)',
            r'保存到知识库(.+)',
            r'学一下(.+)',
            r'知识库记(.+)',
            r'记住这个知识(.+)',
        ]

        content = None
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                content = match.group(1).strip()
                break

        if not content:
            return "请告诉我需要记住什么内容，例如：\"记一下感冒要多喝热水\""

        # 自动分类
        category = self._classify_category(content)

        # 生成标题（取前20个字）
        title = content[:20] + ('...' if len(content) > 20 else '')

        # 保存到知识库
        self.agent.knowledge_base.add_text(
            text=content,
            title=title,
            category=category,
            tags=[category]
        )

        category_names = {
            'health': '健康医疗', 'cooking': '美食烹饪', 'finance': '家庭财务',
            'travel': '旅游出行', 'legal': '法律法规', 'education': '教育学习',
            'relationship': '家庭关系', 'general': '综合知识',
        }
        cat_name = category_names.get(category, '综合知识')

        return (f"📚 已保存到知识库!\n"
                f"📝 内容: {content}\n"
                f"🏷️ 分类: {cat_name}\n\n"
                f"你可以在知识库页面查看和管理所有知识!")

    def _parse_time(self, time_str: str) -> str:
        """解析时间字符串"""
        
        now = datetime.now()
        
        if time_str == "明天":
            target = now.replace(hour=9, minute=0, second=0)
            from datetime import timedelta
            target = target + timedelta(days=1)
            return target.strftime("%Y-%m-%d %H:%M")
        
        elif time_str == "后天":
            target = now.replace(hour=9, minute=0, second=0)
            from datetime import timedelta
            target = target + timedelta(days=2)
            return target.strftime("%Y-%m-%d %H:%M")
        
        # 其他格式尝试解析
        try:
            # 尝试解析 "3月15日" 格式
            month_day_match = re.search(r'(\d+)月(\d+)日', time_str)
            if month_day_match:
                month = int(month_day_match.group(1))
                day = int(month_day_match.group(2))
                target = now.replace(month=month, day=day, hour=9, minute=0, second=0)
                return target.strftime("%Y-%m-%d %H:%M")
        except:
            pass
        
        # 默认明天
        from datetime import timedelta
        target = now.replace(hour=9, minute=0, second=0) + timedelta(days=1)
        return target.strftime("%Y-%m-%d %H:%M")
