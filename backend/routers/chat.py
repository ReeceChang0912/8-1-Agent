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

executor = ThreadPoolExecutor(max_workers=4)

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    emotion: Optional[str] = None


def get_agent() -> FamilyAgentCore:
    from backend.main import get_agent as _get_agent
    return _get_agent()

def get_db_manager():
    from backend.main import get_db_manager as _get_db
    return _get_db()

_chat_history = None

def get_chat_history() -> ChatHistoryManager:
    global _chat_history
    if _chat_history is None:
        _chat_history = ChatHistoryManager(db_manager=get_db_manager())
    return _chat_history


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


@router.websocket("/chat/stream/{user_id}")
async def websocket_chat(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            request = json.loads(data)
            message = request.get('message', '')
            get_chat_history().add_message(user_id, 'user', message)
            await manager.send_message(user_id, json.dumps({'type': 'typing', 'data': True}))
            loop = asyncio.get_event_loop()
            agent = get_agent()
            response, emotion = await loop.run_in_executor(
                executor,
                lambda: (agent.chat(message, user_id=user_id), agent.get_last_emotion())
            )
            get_chat_history().add_message(user_id, 'assistant', response, emotion)
            for i, char in enumerate(response):
                await manager.send_message(user_id, json.dumps({'type': 'chunk', 'data': char, 'index': i}))
                await asyncio.sleep(0.03)
            await manager.send_message(user_id, json.dumps({
                'type': 'complete', 'data': {'full_response': response, 'emotion': emotion}
            }))
    except WebSocketDisconnect:
        manager.disconnect(user_id)
    except Exception as e:
        print(f"WebSocket错误: {e}")
        manager.disconnect(user_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        agent = get_agent()
        response = agent.chat(request.message, user_id=request.user_id)
        emotion = agent.get_last_emotion()
        if request.user_id:
            get_chat_history().add_message(request.user_id, 'user', request.message)
            get_chat_history().add_message(request.user_id, 'assistant', response, emotion)
        return ChatResponse(response=response, emotion=emotion)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/history/{user_id}")
async def get_chat_history_endpoint(user_id: str, limit: int = 50):
    history = get_chat_history().get_history(user_id, limit)
    return {"history": history, "total": len(history)}


@router.post("/chat/history/{user_id}/clear")
async def clear_chat_history_endpoint(user_id: str):
    get_chat_history().clear_history(user_id)
    return {"success": True, "message": "聊天历史已清空"}
