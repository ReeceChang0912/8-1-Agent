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
    session_id: Optional[str] = None
    family_id: Optional[str] = ""

class ChatResponse(BaseModel):
    response: str
    emotion: Optional[str] = None
    session_id: Optional[str] = None

class ChatSessionCreate(BaseModel):
    user_id: str
    title: Optional[str] = None
    family_id: Optional[str] = ""

class ChatSessionUpdate(BaseModel):
    title: str


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
            session_id = request.get('session_id')
            family_id = request.get('family_id', '')
            if not session_id:
                session = get_chat_history().create_session(user_id, _derive_title(message), family_id=family_id)
                session_id = session.get('session_id')
            get_chat_history().add_message(user_id, 'user', message, session_id=session_id, family_id=family_id)
            await manager.send_message(user_id, json.dumps({'type': 'typing', 'data': True}))
            loop = asyncio.get_event_loop()
            agent = get_agent()
            response, emotion = await loop.run_in_executor(
                executor,
                lambda: (agent.chat(message, user_id=user_id, family_id=family_id), agent.get_last_emotion())
            )
            get_chat_history().add_message(user_id, 'assistant', response, emotion, session_id=session_id, family_id=family_id)
            for i, char in enumerate(response):
                await manager.send_message(user_id, json.dumps({'type': 'chunk', 'data': char, 'index': i}))
                await asyncio.sleep(0.03)
            await manager.send_message(user_id, json.dumps({
                'type': 'complete',
                'data': {'full_response': response, 'emotion': emotion, 'session_id': session_id}
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
        family_id = request.family_id or ""
        response = agent.chat(request.message, user_id=request.user_id, family_id=family_id)
        emotion = agent.get_last_emotion()
        if request.user_id:
            session_id = request.session_id
            if not session_id:
                session = get_chat_history().create_session(request.user_id, _derive_title(request.message), family_id=family_id)
                session_id = session.get('session_id')
            get_chat_history().add_message(request.user_id, 'user', request.message, session_id=session_id, family_id=family_id)
            get_chat_history().add_message(request.user_id, 'assistant', response, emotion, session_id=session_id, family_id=family_id)
        return ChatResponse(response=response, emotion=emotion, session_id=session_id if request.user_id else None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions/{user_id}")
async def list_chat_sessions_endpoint(user_id: str, limit: int = 50, family_id: str = ""):
    sessions = get_chat_history().list_sessions(user_id, limit, family_id=family_id)
    return {"sessions": sessions}


@router.post("/chat/sessions")
async def create_chat_session_endpoint(request: ChatSessionCreate):
    session = get_chat_history().create_session(request.user_id, request.title, family_id=request.family_id or "")
    return {"success": True, "session": session}


@router.put("/chat/sessions/{user_id}/{session_id}")
async def update_chat_session_endpoint(user_id: str, session_id: str, request: ChatSessionUpdate, family_id: str = ""):
    ok = get_chat_history().update_session_title(user_id, session_id, request.title, family_id=family_id)
    return {"success": ok}


@router.delete("/chat/sessions/{user_id}/{session_id}")
async def archive_chat_session_endpoint(user_id: str, session_id: str, family_id: str = ""):
    ok = get_chat_history().archive_session(user_id, session_id, family_id=family_id)
    return {"success": ok}


@router.get("/chat/history/{user_id}")
async def get_chat_history_endpoint(user_id: str, limit: int = 50, session_id: str = None, family_id: str = ""):
    history = get_chat_history().get_history(user_id, limit, session_id=session_id, family_id=family_id)
    return {"history": history, "total": len(history)}


@router.post("/chat/history/{user_id}/clear")
async def clear_chat_history_endpoint(user_id: str, session_id: str = None, family_id: str = ""):
    get_chat_history().clear_history(user_id, session_id=session_id, family_id=family_id)
    return {"success": True, "message": "聊天历史已清空"}


@router.get("/chat/context/{user_id}")
async def get_chat_context_endpoint(user_id: str, family_id: str = ""):
    db = get_db_manager()
    if not db:
        return {
            "wedding": None,
            "insurance": None,
            "documents": None,
            "housing": None,
            "health": None,
            "vehicle": None,
            "fitness": None,
            "finance": None,
            "memory": [],
        }

    from datetime import datetime
    now = datetime.now()
    def parse_date(value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except Exception:
            return None

    wedding_items = db.get_wedding_items(family_id=family_id)
    insurance_items = db.get_insurance_policies(family_id=family_id)
    document_items = db.get_document_records(family_id=family_id)
    housing_items = db.get_housing_records(family_id=family_id)
    health_items = db.get_health_records(family_id=family_id)
    vehicle_items = db.get_vehicle_records(family_id=family_id)
    fitness_items = db.get_fitness_records(family_id=family_id)
    finance_summary = db.get_monthly_summary(now.year, now.month)
    memory_items = get_agent().memory_manager.list_memories(limit=5, user_id=user_id, family_id=family_id)

    return {
        "wedding": {
            "todo_count": sum(1 for item in wedding_items if item.get("item_type") == "todo" and item.get("status") != "done"),
            "budget_total": round(sum(float(item.get("planned_amount") or 0) for item in wedding_items if item.get("item_type") == "budget"), 2),
            "spent_total": round(sum(float(item.get("amount") or 0) for item in wedding_items if item.get("item_type") == "budget"), 2),
        },
        "insurance": {
            "policy_count": sum(1 for item in insurance_items if (item.get("record_type") or "policy") == "policy"),
            "claim_count": sum(1 for item in insurance_items if item.get("record_type") == "claim"),
        },
        "documents": {
            "total_count": len(document_items),
            "active_count": sum(1 for item in document_items if not item.get("expiry_date")),
            "expiring_soon_count": sum(
                1 for item in document_items
                if (expiry := parse_date(item.get("expiry_date") or "")) and 0 <= (expiry - now.date()).days <= int(item.get("reminder_days") or 30)
            ),
            "expired_count": sum(
                1 for item in document_items
                if (expiry := parse_date(item.get("expiry_date") or "")) and expiry < now.date()
            ),
        },
        "housing": {
            "total_count": len(housing_items),
            "property_count": sum(1 for item in housing_items if item.get("record_type") == "property"),
            "rent_count": sum(1 for item in housing_items if item.get("record_type") == "rent"),
            "utility_count": sum(1 for item in housing_items if item.get("record_type") == "utility"),
            "repair_count": sum(1 for item in housing_items if item.get("record_type") == "repair"),
            "total_amount": round(sum(float(item.get("amount") or 0) for item in housing_items), 2),
        },
        "health": {
            "total_count": len(health_items),
            "exam_count": sum(1 for item in health_items if item.get("record_type") == "exam"),
            "medication_count": sum(1 for item in health_items if item.get("record_type") == "medication"),
            "followup_count": sum(1 for item in health_items if item.get("record_type") == "followup"),
            "chronic_count": sum(1 for item in health_items if item.get("record_type") == "chronic"),
            "abnormal_count": sum(1 for item in health_items if item.get("record_type") == "exam" and item.get("status") == "异常"),
        },
        "vehicle": {
            "vehicle_count": sum(1 for item in vehicle_items if item.get("record_type") == "vehicle"),
            "expense_total": round(sum(float(item.get("amount") or 0) for item in vehicle_items if item.get("record_type") == "expense"), 2),
        },
        "fitness": {
            "workout_count": sum(1 for item in fitness_items if item.get("record_type") == "workout"),
            "avg_weight": round(sum(float(item.get("weight") or 0) for item in fitness_items if item.get("record_type") == "metric") / max(1, sum(1 for item in fitness_items if item.get("record_type") == "metric")), 1) if any(item.get("record_type") == "metric" for item in fitness_items) else 0,
            "protein_today": round(sum(float(item.get("protein") or 0) for item in fitness_items if item.get("record_type") == "meal"), 2),
        },
        "finance": finance_summary,
        "memory": [
            {
                "id": item.get("id"),
                "content": item.get("content"),
                "memory_type": item.get("memory_type"),
                "importance": item.get("importance"),
            }
            for item in memory_items[:5]
        ],
    }


def _derive_title(content: str) -> str:
    text = " ".join((content or "").split())
    return text[:28] or "新对话"
