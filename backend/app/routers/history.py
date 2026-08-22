"""历史记录路由：每个用户独立，关联日期与餐次"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import HistoryItem, User
from ..schemas import HistoryCreate, HistoryOut
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["history"])

MEAL_TYPES = ["早餐", "午餐", "晚餐", "加餐", "饮品"]


@router.get("", response_model=list[HistoryOut])
def list_history(date: str = "", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = db.query(HistoryItem).filter(HistoryItem.user_id == user.id)
    if date:
        q = q.filter(HistoryItem.date == date)
    items = q.order_by(HistoryItem.created_at.desc()).all()
    return items


@router.post("", response_model=HistoryOut)
def create_history(req: HistoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    meal_type = req.meal_type if req.meal_type in MEAL_TYPES else ""
    item = HistoryItem(
        user_id=user.id,
        dish_name=req.dish_name,
        calories=req.calories,
        models=req.models,
        goal=req.goal,
        result_json=req.result_json,
        date=req.date,
        meal_type=meal_type,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{item_id}", response_model=HistoryOut)
def update_history(item_id: int, req: HistoryCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(HistoryItem).filter(HistoryItem.id == item_id, HistoryItem.user_id == user.id).first()
    if not item:
        raise HTTPException(404, "记录不存在")
    item.dish_name = req.dish_name
    item.calories = req.calories
    item.goal = req.goal
    item.meal_type = req.meal_type if req.meal_type in MEAL_TYPES else item.meal_type
    item.date = req.date or item.date
    if req.result_json and req.result_json != "{}":
        item.result_json = req.result_json
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}")
def delete_history(item_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    item = db.query(HistoryItem).filter(HistoryItem.id == item_id, HistoryItem.user_id == user.id).first()
    if not item:
        raise HTTPException(404, "记录不存在")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.delete("")
def clear_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    db.query(HistoryItem).filter(HistoryItem.user_id == user.id).delete()
    db.commit()
    return {"ok": True}
