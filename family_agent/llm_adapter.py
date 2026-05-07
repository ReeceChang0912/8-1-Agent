"""
LLM适配器 - 支持多种大语言模型
提供统一的接口，可切换不同的LLM提供商
"""

from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class LLMAdapter:
    """
    LLM适配器
    
    支持的模型：
    1. OpenAI GPT-4/GPT-3.5
    2. 阿里云通义千问 (Qwen)
    3. DeepSeek
    4. 本地Ollama模型
    5. 模拟模式（无API时）
    """
    
    def __init__(self, provider: str = "mock"):
        """
        初始化LLM适配器
        
        Args:
            provider: LLM提供商 ("openai", "qwen", "deepseek", "ollama", "mock")
        """
        self.provider = provider
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化对应的客户端"""
        
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "qwen":
            self._init_qwen()
        elif self.provider == "deepseek":
            self._init_deepseek()
        elif self.provider == "ollama":
            self._init_ollama()
        else:
            # Mock模式，不需要初始化
            pass
    
    def _init_openai(self):
        """初始化OpenAI客户端"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("⚠️ 未设置OPENAI_API_KEY，使用Mock模式")
                self.provider = "mock"
                return
            
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI客户端初始化成功")
            
        except ImportError:
            print("⚠️ 未安装openai库，使用Mock模式")
            self.provider = "mock"
    
    def _init_qwen(self):
        """初始化通义千问客户端"""
        try:
            from dashscope import Generation
            
            api_key = os.getenv("QWEN_API_KEY")
            if not api_key:
                print("⚠️ 未设置QWEN_API_KEY，使用Mock模式")
                self.provider = "mock"
                return
            
            import dashscope
            dashscope.api_key = api_key
            self.client = Generation
            print("✅ 通义千问客户端初始化成功")
            
        except ImportError:
            print("⚠️ 未安装dashscope库，使用Mock模式")
            self.provider = "mock"
    
    def _init_deepseek(self):
        """初始化DeepSeek客户端"""
        try:
            from openai import OpenAI
            
            api_key = os.getenv("DEEPSEEK_API_KEY")
            if not api_key:
                print("⚠️ 未设置DEEPSEEK_API_KEY，使用Mock模式")
                self.provider = "mock"
                return
            
            # DeepSeek使用OpenAI兼容接口
            api_base = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
            self.client = OpenAI(
                api_key=api_key,
                base_url=api_base
            )
            self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
            print(f"✅ DeepSeek客户端初始化成功 (模型: {self.model})")
            
        except ImportError:
            print("⚠️ 未安装openai库，使用Mock模式")
            self.provider = "mock"
    
    def _init_ollama(self):
        """初始化Ollama客户端"""
        try:
            import requests
            
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
            self.client = ollama_url
            self.model = os.getenv("OLLAMA_MODEL", "qwen2.5")
            
            # 测试连接
            response = requests.get(f"{ollama_url}/api/tags")
            if response.status_code == 200:
                print(f"✅ Ollama客户端初始化成功 (模型: {self.model})")
            else:
                print("⚠️ Ollama服务未运行，使用Mock模式")
                self.provider = "mock"
                
        except Exception as e:
            print(f"⚠️ Ollama连接失败: {e}，使用Mock模式")
            self.provider = "mock"
    
    def chat(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """
        发送聊天请求
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            temperature: 温度参数 (0-1)
        
        Returns:
            AI回复文本
        """
        
        if self.provider == "openai":
            return self._chat_openai(messages, temperature)
        elif self.provider == "qwen":
            return self._chat_qwen(messages, temperature)
        elif self.provider == "deepseek":
            return self._chat_deepseek(messages, temperature)
        elif self.provider == "ollama":
            return self._chat_ollama(messages, temperature)
        else:
            return self._chat_mock(messages)
    
    def _chat_openai(self, messages: List[Dict], temperature: float) -> str:
        """OpenAI聊天"""
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # 或 "gpt-4"
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"OpenAI调用失败: {e}")
            return self._chat_mock(messages)
    
    def _chat_qwen(self, messages: List[Dict], temperature: float) -> str:
        """通义千问聊天"""
        try:
            # 转换消息格式
            qwen_messages = []
            for msg in messages:
                qwen_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            response = self.client.call(
                model='qwen-turbo',
                messages=qwen_messages,
                temperature=temperature
            )
            
            if response.status_code == 200:
                return response.output.text
            else:
                print(f"Qwen调用失败: {response.message}")
                return self._chat_mock(messages)
                
        except Exception as e:
            print(f"Qwen调用失败: {e}")
            return self._chat_mock(messages)
    
    def _chat_deepseek(self, messages: List[Dict], temperature: float) -> str:
        """DeepSeek聊天"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"DeepSeek调用失败: {e}")
            return self._chat_mock(messages)
    
    def _chat_ollama(self, messages: List[Dict], temperature: float) -> str:
        """Ollama聊天"""
        try:
            import requests
            
            # 转换消息格式
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False,
                "options": {
                    "temperature": temperature
                }
            }
            
            response = requests.post(
                f"{self.client}/api/chat",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['message']['content']
            else:
                print(f"Ollama调用失败: {response.text}")
                return self._chat_mock(messages)
                
        except Exception as e:
            print(f"Ollama调用失败: {e}")
            return self._chat_mock(messages)
    
    def _chat_mock(self, messages: List[Dict]) -> str:
        """
        Mock模式 - 基于规则的简单回复
        
        用于没有API密钥时的降级方案
        """
        
        # 获取最后一条用户消息
        user_message = ""
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        # 简单的关键词匹配回复
        responses = {
            "你好": "你好！很高兴为你服务。有什么我可以帮你的吗？",
            "谢谢": "不客气！如果还有其他问题，随时告诉我。",
            "再见": "再见！祝你有美好的一天！",
        }
        
        # 检查关键词
        for keyword, response in responses.items():
            if keyword in user_message:
                return response
        
        # 默认回复
        default_responses = [
            "我理解了你的问题。作为一个家庭助手，我会尽力帮助你。",
            "这是一个很好的问题。让我想想怎么回答...",
            "我明白了。请继续说，我在听。",
            "感谢你的分享。作为家庭管家，我会记住这些信息。",
        ]
        
        import random
        return random.choice(default_responses)
    
    def analyze_image(self, image_path: str, prompt: str) -> dict:
        """
        Analyze image using LLM vision capabilities.

        Args:
            image_path: Path to image file
            prompt: Analysis prompt

        Returns:
            dict with keys: description, tags, people, event, location, mood
        """
        import base64
        from pathlib import Path

        try:
            if not Path(image_path).exists():
                return {"description": "", "tags": [], "people": [], "event": "", "location": "", "mood": "neutral"}

            # For mock mode or non-vision models, return heuristic analysis
            if self.provider == "mock":
                return self._analyze_image_mock(image_path, prompt)

            # Try vision API if supported
            # DeepSeek doesn't support vision yet, fallback to mock
            return self._analyze_image_mock(image_path, prompt)

        except Exception as e:
            print(f"Image analysis failed: {e}")
            return {"description": "", "tags": [], "people": [], "event": "", "location": "", "mood": "neutral"}

    def _analyze_image_mock(self, image_path: str, prompt: str) -> dict:
        """Fallback heuristic image analysis"""
        from pathlib import Path
        filename = Path(image_path).stem
        return {
            "description": f"照片 {filename}",
            "tags": ["照片", "家庭"],
            "people": [],
            "event": "",
            "location": "",
            "mood": "neutral"
        }

    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context: str = ""
    ) -> str:
        """
        生成回复的便捷方法
        
        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            context: 上下文信息（记忆、知识等）
        
        Returns:
            AI回复
        """
        
        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加上下文
        if context:
            messages.append({
                "role": "system",
                "content": f"相关上下文信息：\n{context}"
            })
        
        # 添加用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 调用LLM
        return self.chat(messages)


# 全局LLM实例
_llm_instance: Optional[LLMAdapter] = None


def get_llm(provider: str = None) -> LLMAdapter:
    """
    获取LLM实例（单例模式）
    
    Args:
        provider: LLM提供商，如果不指定则使用配置中的
    
    Returns:
        LLMAdapter实例
    """
    global _llm_instance
    
    if _llm_instance is None:
        # 从环境变量读取配置
        if provider is None:
            provider = os.getenv("LLM_PROVIDER", "mock")
        
        _llm_instance = LLMAdapter(provider=provider)
    
    return _llm_instance


def reset_llm():
    """重置LLM实例"""
    global _llm_instance
    _llm_instance = None
