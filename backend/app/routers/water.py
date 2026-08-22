"""饮水打卡路由"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserPlan, WaterLog
from ..schemas import WaterDayOut, WaterLogCreate, WaterLogOut
from ..routers.auth import get_current_user

router = APIRouter(prefix="/api/water", tags=["water"])

# 鼓励话语库
ENCOURAGEMENTS = [
    "💧 又喝了一杯水，身体在感谢你！",
    "🌟 继续保持，水分充足让你更有活力！",
    "✨ 每一口水都是对健康的投资！",
    "🎯 离今日目标又近了一步！",
    "💪 自律的你真棒，坚持就是胜利！",
    "🌈 水分充足，皮肤也会越来越好哦！",
    "🏆 今天的你比昨天更健康！",
    "🌸 好好照顾自己，从喝水开始！",
    "⭐ 小习惯，大改变，你正在变好！",
    "🍀 健康是一种态度，你做得很好！",
    "🎉 打卡成功！给自己一个微笑吧！",
    "💖 爱自己，从每一杯水开始！",
    "🌺 坚持喝水的人，运气都不会太差！",
    "🔥 你的健康习惯正在养成中！",
    "🌻 今天的努力，是明天健康的基石！",
]

STREAK_MESSAGES = {
    3: "🔥 连续打卡 3 天！习惯正在养成！",
    7: "🎉 一周打卡达成！你已经超越 80% 的人！",
    14: "💪 两周坚持！健康习惯已深入你的生活！",
    21: "🏆 21 天！科学证明习惯已养成！",
    30: "👑 一个月！你是真正的健康达人！",
    60: "🌟 两个月！这种坚持令人敬佩！",
    100: "💎 百日历！你是传说中的健康王者！",
}


def get_encouragement(streak_days: int, total_today: int, goal: int) -> str:
    """生成鼓励话语"""
    import random
    
    # 检查是否达到特殊里程碑
    if streak_days in STREAK_MESSAGES:
        return STREAK_MESSAGES[streak_days]
    
    # 检查是否完成今日目标
    if total_today >= goal:
        return "🎊 今日饮水目标达成！你太棒了！"
    
    # 随机选择鼓励话语
    return random.choice(ENCOURAGEMENTS)


def get_streak_days(db: Session, user_id: int) -> int:
    """计算连续打卡天数"""
    today = date.today()
    streak = 0
    
    # 从今天往前推，检查每天都有打卡
    for i in range(365):  # 最多查一年
        check_date = (today - timedelta(days=i)).isoformat()
        count = db.query(WaterLog).filter(
            WaterLog.user_id == user_id,
            WaterLog.date == check_date
        ).count()
        
        if count > 0:
            streak += 1
        else:
            break
    
    return streak


@router.get("/today")
def get_today_water(
    date_str: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当日饮水记录"""
    if not date_str:
        date_str = date.today().isoformat()
    
    # 获取用户饮水目标
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    goal = plan.water_goal if plan and plan.water_goal else 2000
    
    # 查询当日记录
    logs = (
        db.query(WaterLog)
        .filter(WaterLog.user_id == user.id, WaterLog.date == date_str)
        .order_by(WaterLog.created_at.asc())
        .all()
    )
    
    total = sum(log.amount for log in logs)
    
    return {
        "date": date_str,
        "total": total,
        "goal": goal,
        "percent": round(total / goal * 100, 1) if goal else 0,
        "logs": [
            {
                "id": log.id,
                "amount": log.amount,
                "note": log.note,
                "time": log.created_at.strftime("%H:%M"),
            }
            for log in logs
        ],
        "streak_days": get_streak_days(db, user.id),
    }


@router.post("/log")
def log_water(
    req: WaterLogCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """记录一次饮水"""
    today_str = date.today().isoformat()
    
    # 查询当日已有记录，计算累计
    existing_logs = (
        db.query(WaterLog)
        .filter(WaterLog.user_id == user.id, WaterLog.date == today_str)
        .all()
    )
    current_total = sum(log.amount for log in existing_logs)
    new_total = current_total + req.amount
    
    # 获取目标
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    goal = plan.water_goal if plan and plan.water_goal else 2000
    
    # 创建新记录
    log = WaterLog(
        user_id=user.id,
        date=today_str,
        amount=req.amount,
        total_today=new_total,
        note=req.note,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    
    # 计算连续打卡天数
    streak = get_streak_days(db, user.id)
    
    # 生成鼓励话语
    encouragement = get_encouragement(streak, new_total, goal)
    
    return {
        "id": log.id,
        "amount": log.amount,
        "total_today": new_total,
        "goal": goal,
        "percent": round(new_total / goal * 100, 1) if goal else 0,
        "streak_days": streak,
        "encouragement": encouragement,
        "goal_reached": new_total >= goal,
    }


@router.delete("/{log_id}")
def delete_water_log(
    log_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """删除一条饮水记录"""
    log = db.query(WaterLog).filter(
        WaterLog.id == log_id,
        WaterLog.user_id == user.id
    ).first()
    
    if not log:
        raise HTTPException(404, "记录不存在")
    
    db.delete(log)
    db.commit()
    return {"ok": True}


@router.get("/calendar")
def get_water_calendar(
    year: int = 0,
    month: int = 0,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取某月饮水打卡日历"""
    today = date.today()
    if year == 0:
        year = today.year
    if month == 0:
        month = today.month
    
    # 获取用户饮水目标
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    goal = plan.water_goal if plan and plan.water_goal else 2000
    
    # 查询该月每天的饮水量
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    logs = (
        db.query(WaterLog.date, func.sum(WaterLog.amount))
        .filter(
            WaterLog.user_id == user.id,
            WaterLog.date >= start_date,
            WaterLog.date < end_date,
        )
        .group_by(WaterLog.date)
        .all()
    )
    
    # 构建日历数据
    calendar = {}
    for d, total in logs:
        calendar[d] = {
            "total": total,
            "goal": goal,
            "reached": total >= goal,
        }
    
    # 计算连续打卡天数
    streak = get_streak_days(db, user.id)
    
    # 统计该月数据
    days_logged = len(calendar)
    days_reached = sum(1 for v in calendar.values() if v["reached"])
    
    return {
        "year": year,
        "month": month,
        "calendar": calendar,
        "streak_days": streak,
        "days_logged": days_logged,
        "days_reached": days_reached,
    }