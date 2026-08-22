"""个人中心路由：用户身体档案（身高/体重/年龄/性别/活动水平）+ BMI / TDEE"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User, UserPlan
from ..routers.auth import get_current_user
from ..routers.plan import _get_or_create_plan

router = APIRouter(prefix="/api/profile", tags=["profile"])

try:
    from modules.nutrition_db import bmi, bmi_category, tdee
except Exception:
    def bmi(h, w): return round(w / ((h / 100) ** 2), 1)
    def bmi_category(v): return "正常"
    def tdee(h, w, a, g, act): return 2000

ACTIVITIES = ["久坐", "轻度", "中度", "高强度"]


def _build_profile(plan: UserPlan, user: User) -> dict:
    has = bool(plan.height_cm and plan.weight_kg and plan.age)
    height = float(plan.height_cm or 0)
    weight = float(plan.weight_kg or 0)
    age = int(plan.age or 0)
    gender = plan.gender or "男"
    activity = plan.activity or "轻度"
    info = {
        "height_cm": height or None,
        "weight_kg": weight or None,
        "age": age or None,
        "gender": gender,
        "activity": activity,
        "has_profile": has,
        # API Key 配置状态（不返回完整 Key，只返回是否已配置）
        "has_zhipu_key": bool(user.zhipu_api_key),
        "has_dashscope_key": bool(user.dashscope_api_key),
        "has_doubao_key": bool(user.doubao_api_key),
    }
    if has:
        info["bmi"] = bmi(height, weight)
        info["bmi_category"] = bmi_category(info["bmi"])
        info["tdee"] = tdee(height, weight, age, gender, activity)
    else:
        info["bmi"] = None
        info["bmi_category"] = None
        info["tdee"] = None
    return info


@router.get("")
def get_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = _get_or_create_plan(db, user)
    return _build_profile(plan, user)


@router.put("")
def update_profile(req: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    plan = _get_or_create_plan(db, user)
    if "height_cm" in req and req["height_cm"] is not None:
        plan.height_cm = max(100, min(float(req["height_cm"]), 250))
    if "weight_kg" in req and req["weight_kg"] is not None:
        plan.weight_kg = max(25, min(float(req["weight_kg"]), 300))
    if "age" in req and req["age"] is not None:
        plan.age = max(10, min(int(req["age"]), 120))
    if "gender" in req and req["gender"] in ("男", "女"):
        plan.gender = req["gender"]
    if "activity" in req and req["activity"] in ACTIVITIES:
        plan.activity = req["activity"]
    # 保存 API Key
    if "zhipu_api_key" in req:
        user.zhipu_api_key = (req["zhipu_api_key"] or "").strip()
    if "dashscope_api_key" in req:
        user.dashscope_api_key = (req["dashscope_api_key"] or "").strip()
    if "doubao_api_key" in req:
        user.doubao_api_key = (req["doubao_api_key"] or "").strip()
    
    db.commit()
    db.refresh(plan)
    db.refresh(user)
    return _build_profile(plan, user)
