"""
推送通知API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from family_agent.notification_manager import NotificationManager

router = APIRouter()


def get_notification_manager() -> NotificationManager:
    from backend.main import get_db_manager
    db = get_db_manager()
    return NotificationManager(db_manager=db, data_dir="data")


class CreateNotificationRequest(BaseModel):
    member_name: str
    title: str
    message: str
    notification_type: str = "general"
    priority: str = "normal"
    scheduled_time: Optional[str] = None


@router.get("/notifications/unread/{member_name}")
def get_unread_notifications(member_name: str, limit: int = 20):
    try:
        notif_mgr = get_notification_manager()
        notifications = notif_mgr.get_unread_notifications(member_name, limit)
        unread_count = notif_mgr.get_unread_count(member_name)
        return {'success': True, 'notifications': notifications, 'unread_count': unread_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/all/{member_name}")
def get_all_notifications(member_name: str, limit: int = 50):
    try:
        notifications = get_notification_manager().get_all_notifications(member_name, limit)
        return {'success': True, 'notifications': notifications}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/create")
def create_notification(request: CreateNotificationRequest):
    try:
        notification = get_notification_manager().create_notification(
            member_name=request.member_name,
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            priority=request.priority,
            scheduled_time=request.scheduled_time
        )
        return {'success': True, 'notification': notification}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/mark-read/{notification_id}")
def mark_as_read(notification_id: str):
    try:
        success = get_notification_manager().mark_as_read(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="通知不存在")
        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/mark-all-read/{member_name}")
def mark_all_read(member_name: str):
    try:
        count = get_notification_manager().mark_all_read(member_name)
        return {'success': True, 'marked_count': count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: str):
    try:
        get_notification_manager().delete_notification(notification_id)
        return {'success': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/unread-count/{member_name}")
def get_unread_count(member_name: str):
    try:
        count = get_notification_manager().get_unread_count(member_name)
        return {'success': True, 'unread_count': count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
