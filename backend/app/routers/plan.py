"""每日计划路由：设置目标 + 查看某天汇总"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import HistoryItem, User, UserPlan
from ..schemas import DayOut, DayMeal, PlanOut, PlanUpdate
from ..routers.auth import get_current_user

try:
    from modules.nutrition_db import tdee
except Exception:
    def tdee(*args, **kwargs):
        return 2000

router = APIRouter(prefix="/api", tags=["plan"])

DEFAULT_TARGET = 2000
DEFAULT_GOAL = "均衡饮食"

# 宏量营养素供能比（默认）：蛋白 20% / 碳水 50% / 脂肪 30%
MACRO_RATIO = {"protein": 0.20, "carbs": 0.50, "fat": 0.30}
MACRO_KCAL_PER_G = {"protein": 4, "carbs": 4, "fat": 9}


def default_macro_goals(target_calories: int) -> dict:
    """按默认供能比 + 热量目标推算每日宏量营养素目标（克）"""
    return {
        "protein": round(target_calories * MACRO_RATIO["protein"] / MACRO_KCAL_PER_G["protein"]),
        "carbs": round(target_calories * MACRO_RATIO["carbs"] / MACRO_KCAL_PER_G["carbs"]),
        "fat": round(target_calories * MACRO_RATIO["fat"] / MACRO_KCAL_PER_G["fat"]),
    }


# ===== 营养学推荐标准（依据中国营养学会 / WHO / 膳食指南） =====
# 安全减重速度：每周 0.5~1 kg（≈7700 kcal/kg 脂肪）
# 减脂：每日热量缺口 300~500 kcal；增肌：每日盈余 300~500 kcal；控糖/均衡：维持平衡
# 安全下限：女性 1200 kcal/天、男性 1500 kcal/天，避免代谢损伤
DEFICIT_RANGE = (300, 500)   # 每日推荐缺口范围
SURPLUS_RANGE = (300, 500)   # 每日推荐盈余范围
SAFE_FLOOR = {"女": 1200, "男": 1500}


def recommend_adjustment(goal: str, tdee_value: int) -> int:
    """按目标类型推荐热量缺口/盈余（正=盈余，负=缺口，0=维持）。"""
    if goal == "减脂":
        deficit = round(tdee_value * 0.15 / 50) * 50
        return -max(DEFICIT_RANGE[0], min(deficit, DEFICIT_RANGE[1]))
    if goal == "增肌":
        surplus = round(tdee_value * 0.10 / 50) * 50
        return max(SURPLUS_RANGE[0], min(surplus, SURPLUS_RANGE[1]))
    return 0  # 控糖 / 均衡饮食：维持热量平衡


def safe_target(target: int, gender: str) -> int:
    """目标热量不低于安全下限。"""
    return max(target, SAFE_FLOOR.get(gender or "男", 1500))


def resolve_target(plan) -> dict:
    """计算最终每日目标热量：有档案用 TDEE+缺口/盈余，无档案用手动目标。"""
    gender = plan.gender or "男"
    has_profile = all([plan.height_cm, plan.weight_kg, plan.age])
    if has_profile:
        tdee_value = tdee(plan.height_cm, plan.weight_kg, plan.age, gender, plan.activity or "轻度")
        if plan.calorie_mode == "manual":
            adjustment = int(plan.adjustment or 0)
            target = safe_target(tdee_value + adjustment, gender)
            return {
                "target": target, "tdee": tdee_value, "adjustment": adjustment,
                "mode": "manual", "note": "按你设定的缺口/盈余计算",
            }
        # auto：按目标智能推荐
        adjustment = recommend_adjustment(plan.goal or "均衡饮食", tdee_value)
        target = safe_target(tdee_value + adjustment, gender)
        note = "智能推荐"
        return {
            "target": target, "tdee": tdee_value, "adjustment": adjustment,
            "mode": "auto", "note": note,
        }
    # 无个人档案：使用手动目标
    return {
        "target": int(plan.target_calories or 2000), "tdee": None,
        "adjustment": 0, "mode": "manual",
        "note": "未填个人档案，按手动目标执行（填写身高体重可自动按 TDEE 推荐）",
    }


def parse_macros(result_json: str) -> dict:
    """从历史记录的 result_json 解析宏量营养素（克），无数据返回全 0"""
    try:
        data = json.loads(result_json or "{}")
        m = data.get("macros") or {}
        return {
            "protein": float(m.get("protein") or 0),
            "carbs": float(m.get("carbs") or 0),
            "fat": float(m.get("fat") or 0),
        }
    except Exception:
        return {"protein": 0, "carbs": 0, "fat": 0}


def _get_or_create_plan(db: Session, user: User) -> UserPlan:
    plan = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
    if not plan:
        plan = UserPlan(user_id=user.id, target_calories=DEFAULT_TARGET, goal=DEFAULT_GOAL)
        db.add(plan)
        db.commit()
        db.refresh(plan)
    return plan


@router.get("/plan", response_model=PlanOut)
def get_plan(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = _get_or_create_plan(db, user)
    _ensure_macro_goals(db, plan)
    info = resolve_target(plan)
    plan.target_calories = info["target"]
    db.commit()
    db.refresh(plan)
    plan.tdee = info["tdee"]
    plan.recommended_adjustment = info["adjustment"]
    plan.target_note = info["note"]
    return plan


def _ensure_macro_goals(db: Session, plan: UserPlan):
    """若宏量目标未设置，则按热量目标自动推算并落库（同一 session）"""
    target = plan.target_calories or DEFAULT_TARGET
    defaults = default_macro_goals(target)
    changed = False
    for attr, key in (("protein_goal", "protein"), ("carb_goal", "carbs"), ("fat_goal", "fat")):
        if getattr(plan, attr, None) is None:
            setattr(plan, attr, defaults[key])
            changed = True
    if changed:
        db.commit()
        db.refresh(plan)


@router.put("/plan", response_model=PlanOut)
def update_plan(req: PlanUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = _get_or_create_plan(db, user)
    plan.target_calories = max(500, min(int(req.target_calories), 8000))
    plan.goal = req.goal or DEFAULT_GOAL
    if getattr(req, "reminder_enabled", None) is not None:
        plan.reminder_enabled = 1 if req.reminder_enabled else 0
    for attr in ("protein_goal", "carb_goal", "fat_goal"):
        v = getattr(req, attr, None)
        if v is not None:
            setattr(plan, attr, max(0, float(v)))
    # 个人档案
    for attr in ("height_cm", "weight_kg", "age", "gender", "activity", "calorie_mode", "adjustment", "water_goal"):
        v = getattr(req, attr, None)
        if v is not None:
            setattr(plan, attr, v)
    db.commit()
    db.refresh(plan)
    # 返回前用最新目标覆盖
    info = resolve_target(plan)
    plan.target_calories = info["target"]
    plan.tdee = info["tdee"]
    plan.recommended_adjustment = info["adjustment"]
    plan.target_note = info["note"]
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/stats")
def get_stats(days: int = 7, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """最近 N 天每日摄入统计：每天合计、目标、是否达标、平均、达标天数。"""
    from datetime import date, timedelta

    days = max(1, min(int(days), 90))
    plan = _get_or_create_plan(db, user)
    target = resolve_target(plan)["target"]
    today = date.today()
    result = []
    within = 0
    for i in range(days - 1, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        total = (
            db.query(HistoryItem)
            .filter(HistoryItem.user_id == user.id, HistoryItem.date == d)
            .with_entities(__import__("sqlalchemy").func.coalesce(__import__("sqlalchemy").func.sum(HistoryItem.calories), 0))
            .scalar()
        ) or 0
        if total and abs(total - target) <= target * 0.2:
            within += 1
        result.append({"date": d, "total": total, "target": target})
    total_sum = sum(r["total"] for r in result)
    # 餐次分布（该周期内）
    from sqlalchemy import func
    meal_rows = (
        db.query(HistoryItem.meal_type, func.sum(HistoryItem.calories))
        .filter(HistoryItem.user_id == user.id, HistoryItem.date >= (today - timedelta(days=days - 1)).isoformat())
        .group_by(HistoryItem.meal_type)
        .all()
    )
    meal_distribution = [{"meal_type": k or "未分类", "calories": int(v or 0)} for k, v in meal_rows]
    # 本周 vs 上周日均
    week_start = today - timedelta(days=today.weekday())
    last_week_start = week_start - timedelta(days=7)
    def avg_between(start, end):
        total = db.query(HistoryItem).filter(
            HistoryItem.user_id == user.id,
            HistoryItem.date >= start.isoformat(),
            HistoryItem.date < end.isoformat(),
        ).with_entities(func.coalesce(func.sum(HistoryItem.calories), 0)).scalar() or 0
        return round(total / 7, 1)
    this_week_avg = avg_between(week_start, today + timedelta(days=1))
    last_week_avg = avg_between(last_week_start, week_start)
    return {
        "days": days,
        "target": target,
        "goal": plan.goal,
        "average": round(total_sum / days, 1),
        "within_target_days": within,
        "daily": result,
        "meal_distribution": meal_distribution,
        "this_week_avg": this_week_avg,
        "last_week_avg": last_week_avg,
    }


@router.get("/day", response_model=DayOut)
def get_day(date: str = "", db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    plan = _get_or_create_plan(db, user)
    meals = (
        db.query(HistoryItem)
        .filter(HistoryItem.user_id == user.id, HistoryItem.date == date)
        .order_by(HistoryItem.created_at.asc())
        .all()
    )
    total = sum(m.calories or 0 for m in meals)
    _ensure_macro_goals(db, plan)
    info = resolve_target(plan)
    target = info["target"]
    # 当日实际宏量摄入（累加有 AI 分析结果的记录）
    macros = {"protein": 0.0, "carbs": 0.0, "fat": 0.0}
    meal_macros = []
    for m in meals:
        mm = parse_macros(m.result_json)
        meal_macros.append(mm)
        for k in macros:
            macros[k] += mm[k]
    macro_targets = {
        "protein": plan.protein_goal or default_macro_goals(target)["protein"],
        "carbs": plan.carb_goal or default_macro_goals(target)["carbs"],
        "fat": plan.fat_goal or default_macro_goals(target)["fat"],
    }
    return DayOut(
        date=date,
        target_calories=target,
        goal=plan.goal,
        total_calories=total,
        remaining=max(target - total, 0),
        percent=round(total / target * 100, 1) if target else 0,
        meals=[
            DayMeal(
                id=m.id,
                dish_name=m.dish_name,
                calories=m.calories,
                meal_type=m.meal_type,
                models=m.models,
                time=m.created_at.strftime("%H:%M"),
                macros=meal_macros[i],
            )
            for i, m in enumerate(meals)
        ],
        macros={k: round(v, 1) for k, v in macros.items()},
        macro_targets=macro_targets,
    )
