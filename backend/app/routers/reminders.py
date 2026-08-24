"""用户自定义提醒路由（喝水 / 吃药等）"""
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Reminder, User
from ..schemas import ReminderCreate, ReminderOut
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/reminders", tags=["reminders"])

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _validate_time(time_str: str) -> str:
    time_str = (time_str or "").strip()
    if not _TIME_RE.match(time_str):
        raise HTTPException(422, "提醒时间格式应为 HH:MM（如 09:00）")
    return time_str


@router.get("", response_model=list[ReminderOut])
def list_reminders(db=Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Reminder)
        .filter(Reminder.user_id == user.id)
        .order_by(Reminder.time.asc())
        .all()
    )


@router.post("", response_model=ReminderOut)
def create_reminder(
    req: ReminderCreate,
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = Reminder(
        user_id=user.id,
        title=(req.title or "喝水").strip()[:50],
        time=_validate_time(req.time),
        enabled=1 if req.enabled else 0,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


@router.put("/{reminder_id}", response_model=ReminderOut)
def update_reminder(
    reminder_id: int,
    req: ReminderCreate,
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user.id).first()
    if not r:
        raise HTTPException(404, "提醒不存在")
    r.title = (req.title or r.title).strip()[:50]
    r.time = _validate_time(req.time or r.time)
    r.enabled = 1 if req.enabled else 0
    db.commit()
    db.refresh(r)
    return r


@router.delete("/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    r = db.query(Reminder).filter(Reminder.id == reminder_id, Reminder.user_id == user.id).first()
    if not r:
        raise HTTPException(404, "提醒不存在")
    db.delete(r)
    db.commit()
    return {"ok": True}
