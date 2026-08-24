"""膳食动态补偿路由：根据当日已摄入生成后续餐次建议"""
import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import HistoryItem, User, UserPlan
from ..routers.auth import get_current_user
from ..routers.plan import _get_or_create_plan, resolve_target, default_macro_goals, parse_macros
from modules.llm_client import pick_text_model

try:
    from modules.meal_compensator import generate_compensation_advice
except ImportError:
    generate_compensation_advice = None

router = APIRouter(prefix="/api", tags=["compensate"])


@router.get("/compensate")
def get_compensation(
    date_str: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取当日膳食补偿建议"""
    if not date_str:
        date_str = date.today().isoformat()

    plan = _get_or_create_plan(db, user)
    info = resolve_target(plan)
    target = info["target"]
    goal = plan.goal or "均衡饮食"

    # 当日已摄入
    meals = (
        db.query(HistoryItem)
        .filter(HistoryItem.user_id == user.id, HistoryItem.date == date_str)
        .order_by(HistoryItem.created_at.asc())
        .all()
    )
    total_cal = sum(m.calories or 0 for m in meals)
    macros = {"protein": 0.0, "carbs": 0.0, "fat": 0.0}
    meal_list = []
    for m in meals:
        mm = parse_macros(m.result_json)
        for k in macros:
            macros[k] += mm[k]
        meal_list.append({
            "meal_type": m.meal_type or "未分类",
            "dish_name": m.dish_name or "",
            "calories": m.calories or 0,
        })

    # 宏量目标
    macro_targets = {
        "protein": plan.protein_goal or default_macro_goals(target)["protein"],
        "carbs": plan.carb_goal or default_macro_goals(target)["carbs"],
        "fat": plan.fat_goal or default_macro_goals(target)["fat"],
    }

    # 用户档案
    profile = None
    if plan.height_cm and plan.weight_kg and plan.age:
        from modules.nutrition_db import bmi, tdee as calc_tdee
        g = plan.gender or "男"
        profile = {
            "height": plan.height_cm,
            "weight": plan.weight_kg,
            "age": plan.age,
            "gender": g,
            "activity": plan.activity or "轻度",
            "bmi": round(bmi(plan.height_cm, plan.weight_kg), 1),
            "tdee": calc_tdee(plan.height_cm, plan.weight_kg, plan.age, g, plan.activity or "轻度"),
        }

    # 本周趋势
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_items = (
        db.query(HistoryItem)
        .filter(
            HistoryItem.user_id == user.id,
            HistoryItem.date >= week_start.isoformat(),
            HistoryItem.date < (today + timedelta(days=1)).isoformat(),
        )
        .all()
    )
    day_totals = {}
    for m in week_items:
        day_totals[m.date] = day_totals.get(m.date, 0) + (m.calories or 0)
    if day_totals:
        avg_cal = round(sum(day_totals.values()) / len(day_totals), 0)
        days_over = sum(1 for v in day_totals.values() if v > target * 1.1)
        days_under = sum(1 for v in day_totals.values() if v < target * 0.7)
        weekly_trend = {"avg_calories": avg_cal, "days_over": days_over, "days_under": days_under}
    else:
        weekly_trend = None

    if not generate_compensation_advice:
        return {"error": "补偿模块未加载"}

    today_intake = {
        "total_calories": total_cal,
        "macros": macros,
        "meals": meal_list,
    }

    result = generate_compensation_advice(
        today_intake=today_intake,
        goal=goal,
        target_calories=target,
        macro_targets=macro_targets,
        profile=profile,
        weekly_trend=weekly_trend,
        model=pick_text_model(bool(user.dashscope_api_key)),
    )

    # 附加当日汇总信息
    result["today_summary"] = {
        "date": date_str,
        "total_calories": total_cal,
        "target_calories": target,
        "goal": goal,
        "meals": meal_list,
        "macros": {k: round(v, 1) for k, v in macros.items()},
        "macro_targets": macro_targets,
    }

    return result
