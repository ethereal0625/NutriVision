"""成就徽章路由：根据历史记录与饮水记录计算用户已解锁徽章"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import HistoryItem, User, UserPlan, WaterLog
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/badges", tags=["badges"])

BADGES = [
    {"id": "first_analysis", "icon": "🥗", "name": "首次分析", "desc": "完成第一次食物热量分析"},
    {"id": "streak_3", "icon": "📅", "name": "连续 3 天记录", "desc": "历史或饮水打卡连续 3 天"},
    {"id": "streak_7", "icon": "🔥", "name": "连续 7 天记录", "desc": "历史或饮水打卡连续 7 天"},
    {"id": "first_water", "icon": "💧", "name": "首杯水", "desc": "完成第一次饮水打卡"},
    {"id": "goal_hit", "icon": "🎯", "name": "目标达成", "desc": "某天热量摄入在计划目标 ±20% 内"},
    {"id": "perfect_week", "icon": "👑", "name": "完美一周", "desc": "一周 7 天都有记录"},
]


def _record_dates(db: Session, user_id: int) -> set:
    """汇总饮食与饮水记录日期（按日期去重）"""
    history_dates = {
        d for (d,) in db.query(HistoryItem.date)
        .filter(HistoryItem.user_id == user_id, HistoryItem.date != "")
        .distinct()
    }
    water_dates = {
        d for (d,) in db.query(WaterLog.date)
        .filter(WaterLog.user_id == user_id, WaterLog.date != "")
        .distinct()
    }
    return history_dates | water_dates


def _consecutive_run_end(dates: set, length: int):
    """返回最早一段连续 length 天记录的结束日期，没有则返回 None"""
    days = sorted(date.fromisoformat(d) for d in dates)
    if not days:
        return None
    run = 1
    prev = days[0]
    for day in days[1:]:
        if (day - prev).days == 1:
            run += 1
            if run == length:
                return day.isoformat()
        else:
            run = 1
        prev = day
    return None


def _perfect_week_end(dates: set):
    """返回最早一个完整 7 天周的结束日期，没有则返回 None"""
    today = date.today()
    for d in sorted(dates):
        day = date.fromisoformat(d)
        if day > today:
            continue
        monday = day - timedelta(days=day.isoweekday() - 1)
        week_end = monday + timedelta(days=6)
        if week_end > today:
            continue
        week = {(monday + timedelta(days=i)).isoformat() for i in range(7)}
        if week <= dates:
            return week_end.isoformat()
    return None


@router.get("")
def get_badges(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """返回当前用户的徽章列表"""
    has_history = bool(db.query(HistoryItem.id).filter(HistoryItem.user_id == user.id).first())
    has_water = bool(db.query(WaterLog.id).filter(WaterLog.user_id == user.id).first())

    first_analysis_at = None
    if has_history:
        first_history = (
            db.query(HistoryItem)
            .filter(HistoryItem.user_id == user.id)
            .order_by(HistoryItem.created_at.asc())
            .first()
        )
        first_analysis_at = first_history.date or first_history.created_at.strftime("%Y-%m-%d")

    first_water_at = None
    if has_water:
        first_water = (
            db.query(WaterLog)
            .filter(WaterLog.user_id == user.id)
            .order_by(WaterLog.created_at.asc())
            .first()
        )
        first_water_at = first_water.date or first_water.created_at.strftime("%Y-%m-%d")

    dates = _record_dates(db, user.id)
    streak_3_at = _consecutive_run_end(dates, 3)
    streak_7_at = _consecutive_run_end(dates, 7)
    perfect_week_at = _perfect_week_end(dates)

    # 目标达成：某天历史记录热量合计在计划目标 ±20% 内
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    target = plan.target_calories if plan and plan.target_calories else 2000
    goal_hit_at = None
    if target > 0:
        low, high = round(target * 0.8), round(target * 1.2)
        daily_totals = (
            db.query(HistoryItem.date, func.sum(HistoryItem.calories))
            .filter(HistoryItem.user_id == user.id, HistoryItem.date != "")
            .group_by(HistoryItem.date)
            .all()
        )
        goal_hit_at = next(
            (d for d, total in sorted(daily_totals) if low <= total <= high),
            None,
        )

    results = []
    for meta in BADGES:
        unlocked_at = {
            "first_analysis": first_analysis_at,
            "streak_3": streak_3_at,
            "streak_7": streak_7_at,
            "first_water": first_water_at,
            "goal_hit": goal_hit_at,
            "perfect_week": perfect_week_at,
        }[meta["id"]]
        results.append({
            "id": meta["id"],
            "icon": meta["icon"],
            "name": meta["name"],
            "desc": meta["desc"],
            "unlocked": unlocked_at is not None,
            "unlocked_at": unlocked_at,
        })
    return results
