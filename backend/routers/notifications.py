"""
推送通知API路由
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from family_agent.notification_manager import NotificationManager

router = APIRouter()
notification_mgr = NotificationManager(data_dir="data")


class CreateNotificationRequest(BaseModel):
    member_name: str
    title: str
    message: str
    notification_type: str = "general"
    priority: str = "normal"
    scheduled_time: Optional[str] = None


@router.get("/notifications/unread/{member_name}")
def get_unread_notifications(member_name: str, limit: int = 20):
    """获取未读通知"""
    try:
        notifications = notification_mgr.get_unread_notifications(member_name, limit)
        unread_count = notification_mgr.get_unread_count(member_name)
        return {
            'success': True,
            'notifications': notifications,
            'unread_count': unread_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/all/{member_name}")
def get_all_notifications(member_name: str, limit: int = 50):
    """获取所有通知"""
    try:
        notifications = notification_mgr.get_all_notifications(member_name, limit)
        return {
            'success': True,
            'notifications': notifications
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/create")
def create_notification(request: CreateNotificationRequest):
    """创建通知"""
    try:
        notification = notification_mgr.create_notification(
            member_name=request.member_name,
            title=request.title,
            message=request.message,
            notification_type=request.notification_type,
            priority=request.priority,
            scheduled_time=request.scheduled_time
        )
        return {
            'success': True,
            'notification': notification
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/mark-read/{notification_id}")
def mark_as_read(notification_id: str):
    """标记为已读"""
    try:
        success = notification_mgr.mark_as_read(notification_id)
        if not success:
            raise HTTPException(status_code=404, detail="通知不存在")
        return {'success': True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/notifications/mark-all-read/{member_name}")
def mark_all_read(member_name: str):
    """标记所有为已读"""
    try:
        count = notification_mgr.mark_all_read(member_name)
        return {
            'success': True,
            'marked_count': count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: str):
    """删除通知"""
    try:
        notification_mgr.delete_notification(notification_id)
        return {'success': True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/notifications/unread-count/{member_name}")
def get_unread_count(member_name: str):
    """获取未读数量"""
    try:
        count = notification_mgr.get_unread_count(member_name)
        return {
            'success': True,
            'unread_count': count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
