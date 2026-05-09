"""
情感识别与沟通方案生成引擎
"""

from typing import Dict, List, Optional
from enum import Enum


class EmotionType(Enum):
    """情绪类型"""
    JOY = "joy"
    ANGER = "anger"
    SADNESS = "sadness"
    ANXIETY = "anxiety"
    FEAR = "fear"
    SURPRISE = "surprise"
    NEUTRAL = "neutral"


class CommunicationStrategy(Enum):
    """沟通策略"""
    NVC = "non_violent_communication"  # 非暴力沟通
    EMPATHY = "empathy"                # 共情倾听
    BOUNDARY = "boundary_setting"      # 边界设定
    APPRECIATION = "appreciation"      # 表达感谢
    APOLOGY = "apology"                # 道歉


class EmotionEngine:
    """情感识别与处理引擎"""
    
    EMOTION_KEYWORDS = {
        EmotionType.ANGER: [
            "生气", "愤怒", "烦", "讨厌", "受不了", "气死", "恨",
            "恼火", "郁闷", "烦躁", "暴躁", "怒"
        ],
        EmotionType.SADNESS: [
            "伤心", "难过", "哭", "悲伤", "失落", "失望", "痛苦",
            "委屈", "沮丧", "抑郁", "孤单", "寂寞"
        ],
        EmotionType.ANXIETY: [
            "担心", "焦虑", "紧张", "害怕", "压力", "愁", "不安",
            "担忧", "恐慌", "纠结", "犹豫"
        ],
        EmotionType.JOY: [
            "开心", "高兴", "快乐", "幸福", "满足", "欣慰", "激动",
            "兴奋", "爽", "棒", "好极了"
        ]
    }
    
    def __init__(self):
        pass
    
    def detect_emotion(self, text: str) -> Dict:
        """检测文本中的情绪"""
        return self._rule_based_detect(text)
    
    def _rule_based_detect(self, text: str) -> Dict:
        """基于规则的情绪检测"""
        emotion_scores = {
            EmotionType.ANGER: 0,
            EmotionType.SADNESS: 0,
            EmotionType.ANXIETY: 0,
            EmotionType.JOY: 0,
            EmotionType.NEUTRAL: 0
        }

        has_keyword = False
        for emotion, keywords in self.EMOTION_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    emotion_scores[emotion] += 2
                    has_keyword = True

        if "!" in text or "！" in text:
            emotion_scores[EmotionType.JOY] += 1

        if "?" in text or "？" in text:
            emotion_scores[EmotionType.ANXIETY] += 0.5

        # No real keywords matched → neutral, reset punctuation-based scores
        if not has_keyword:
            emotion_scores[EmotionType.NEUTRAL] = 1
            emotion_scores[EmotionType.ANXIETY] = 0
            emotion_scores[EmotionType.JOY] = 0

        # Tie-breaking: prefer NEUTRAL > JOY > first-in-order
        tie_order = [EmotionType.NEUTRAL, EmotionType.JOY, EmotionType.ANGER,
                     EmotionType.SADNESS, EmotionType.ANXIETY, EmotionType.FEAR,
                     EmotionType.SURPRISE]
        max_score = max(emotion_scores.values())
        candidates = [e for e, s in emotion_scores.items() if s == max_score]
        primary_emotion = candidates[0]
        for e in tie_order:
            if e in candidates:
                primary_emotion = e
                break

        total_score = sum(emotion_scores.values())
        confidence = emotion_scores[primary_emotion] / total_score if total_score > 0 else 0.5

        return {
            "primary_emotion": primary_emotion,
            "confidence": min(confidence * 2, 1.0),
            "all_emotions": emotion_scores
        }
    
    def generate_comfort_response(self, emotion: EmotionType, context: str = "") -> str:
        """生成安抚回应"""
        
        comfort_templates = {
            EmotionType.ANGER: [
                "我理解你现在很生气，这是正常的。深呼吸一下，我们一起想想怎么处理这个问题。",
                "听起来这件事让你很困扰。先冷静一下，我可以帮你分析一下情况。",
                "我能感受到你的愤怒。要不要先休息一下，等情绪平复了我们再讨论？"
            ],
            EmotionType.SADNESS: [
                "看到你这么难过，我也很心疼。记住，我在这里陪着你。",
                "没关系的，每个人都有低潮期。想聊聊发生了什么吗？",
                "我理解你的感受。有时候哭出来会好受一些，我会一直在这里听你说。"
            ],
            EmotionType.ANXIETY: [
                "别太担心，事情总会解决的。我们一步一步来。",
                "我理解你的焦虑。让我们先把问题列出来，一个一个解决。",
                "放轻松，你已经在努力了。需要我帮你做些什么吗？"
            ],
            EmotionType.JOY: [
                "太好了！看到你这么开心我也很高兴！",
                "这真是个好消息！恭喜你！",
                "真为你感到高兴！分享一下具体是什么事吧！"
            ]
        }
        
        templates = comfort_templates.get(emotion, ["我在这里陪着你。"])
        
        import random
        response = random.choice(templates)
        
        if context:
            response += f"\n\n关于你提到的：{context}，我们可以一起想办法。"
        
        return response
    
    def generate_nvc_response(self, situation: str, other_person: str = "") -> str:
        """
        生成非暴力沟通（NVC）话术
        
        NVC四要素：观察、感受、需要、请求
        """
        
        nvc_template = f"""
当面对"{situation}"这个情况时，建议使用非暴力沟通方式：

【观察】客观描述事实，不加评判
例如："我注意到最近..."

【感受】表达自己的感受
例如："我感到有些担心/困惑/难过..."

【需要】说明自己的需求
例如："因为我希望/需要..."

【请求】提出具体的请求
例如："你是否可以...？"

完整示例：
"我注意到{situation}，我感到有些担心，因为我很重视我们的关系和谐。你是否愿意我们一起找个时间好好聊聊？"

{'针对' + other_person if other_person else ''}，建议语气保持温和，避免指责性语言。
"""
        
        return nvc_template
    
    def suggest_communication_strategy(
        self,
        emotion: EmotionType,
        relationship: str,
        situation: str
    ) -> Dict:
        """建议沟通策略"""
        
        strategies = []
        
        if emotion in [EmotionType.ANGER, EmotionType.SADNESS]:
            strategies.append({
                "strategy": CommunicationStrategy.EMPATHY.value,
                "description": "先共情倾听，让对方感受到被理解",
                "action": "耐心倾听，不要急于给建议，多用'我理解'、'我明白'"
            })
        
        if "批评" in situation or "指责" in situation:
            strategies.append({
                "strategy": CommunicationStrategy.BOUNDARY.value,
                "description": "温和地设定边界",
                "action": "使用'我'陈述句，如'我希望我们能互相尊重'"
            })
        
        if relationship in ["父母", "长辈"]:
            strategies.append({
                "strategy": CommunicationStrategy.APPRECIATION.value,
                "description": "先表达感谢和认可",
                "action": "感谢对方的关心，再表达自己的想法"
            })
        
        strategies.append({
            "strategy": CommunicationStrategy.NVC.value,
            "description": "使用非暴力沟通",
            "action": self.generate_nvc_response(situation, relationship)
        })
        
        return {
            "emotion_detected": emotion.value,
            "suggested_strategies": strategies,
            "general_advice": "保持冷静，尊重对方，寻找共同点"
        }
