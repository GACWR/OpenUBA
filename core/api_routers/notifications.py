'''
Copyright 2019-Present The OpenUBA Platform Authors
notifications router — user notification management
'''

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.db import get_db, Notification
from core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/notifications")
async def list_notifications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50,
):
    '''list current user notifications, newest first'''
    user_id = current_user.get("user_id")
    if not user_id:
        return []

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(n.id),
            "title": n.title,
            "message": n.message,
            "type": n.type,
            "read": n.read,
            "link": n.link,
            "created_at": n.created_at.isoformat() if n.created_at else "",
        }
        for n in notifications
    ]


@router.get("/notifications/unread-count")
async def unread_count(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    '''count unread notifications for badge'''
    user_id = current_user.get("user_id")
    if not user_id:
        return {"count": 0}

    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.read == False)
        .count()
    )
    return {"count": count}


@router.put("/notifications/{notification_id}/read")
async def mark_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    '''mark a notification as read'''
    user_id = current_user.get("user_id")
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notification not found")

    notification.read = True
    db.commit()
    return {"detail": "marked as read"}


@router.put("/notifications/read-all")
async def mark_all_read(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    '''mark all notifications as read'''
    user_id = current_user.get("user_id")
    if not user_id:
        return {"detail": "no user"}

    db.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.read == False,
    ).update({"read": True})
    db.commit()
    return {"detail": "all marked as read"}
