"""
聊天相关路由
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from family_agent.core import FamilyAgentCore
from family_agent.chat_history import ChatHistoryManager

router = APIRouter()

# 线程池用于执行同步的agent.chat()
executor = ThreadPoolExecutor(max_workers=4)

# 数据模型
class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    emotion: Optional[str] = None

# 聊天历史管理器
chat_history = ChatHistoryManager(data_dir="data")


def get_agent() -> FamilyAgentCore:
    """懒加载Agent"""
    from main import get_agent as _get_agent
    return _get_agent()


# ===== WebSocket 连接管理 =====
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_message(self, user_id: str, message: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()


# ===== API 端点 =====

@router.websocket("/chat/stream/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    """WebSocket流式聊天"""
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            request = json.loads(data)
            message = request.get('message', '')
            
            # 保存用户消息到历史
            chat_history.add_message(user_id, 'user', message)
            
            # 发送“正在输入”状态
            await manager.send_message(user_id, json.dumps({
                'type': 'typing',
                'data': True
            }))
            
            # 在线程池中执行同步的agent.chat(),避免阻塞事件循环
            loop = asyncio.get_event_loop()
            agent = get_agent()
            response, emotion = await loop.run_in_executor(
                executor,
                lambda: (agent.chat(message, user_id=user_id), agent.get_last_emotion())
            )
            
            # 保存助手消息到历史
            chat_history.add_message(user_id, 'assistant', response, emotion)
            
            # 逐字发送响应
            for i, char in enumerate(response):
                await manager.send_message(user_id, json.dumps({
                    'type': 'chunk',
                    'data': char,
                    'index': i
                }))
                await asyncio.sleep(0.03)  # 30ms延迟,模拟打字效果
            
            # 发送完成信号
            await manager.send_message(user_id, json.dumps({
                'type': 'complete',
                'data': {
                    'full_response': response,
                    'emotion': emotion
                }
            }))
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket错误: {e}")
        manager.disconnect(user_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """智能对话 (HTTP版,保持兼容)"""
    try:
        agent = get_agent()
        response = agent.chat(request.message, user_id=request.user_id)
        
        # 获取情绪分析
        emotion = agent.get_last_emotion()
        
        # 保存到历史
        if request.user_id:
            chat_history.add_message(request.user_id, 'user', request.message)
            chat_history.add_message(request.user_id, 'assistant', response, emotion)
        
        return ChatResponse(response=response, emotion=emotion)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{user_id}")
async def get_chat_history(user_id: str, limit: int = 50):
    """获取聊天历史"""
    history = chat_history.get_history(user_id, limit)
    return {"history": history, "total": len(history)}


@router.post("/chat/history/{user_id}/clear")
async def clear_chat_history(user_id: str):
    """清空聊天历史"""
    chat_history.clear_history(user_id)
    return {"success": True, "message": "聊天历史已清空"}
