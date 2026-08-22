"""食物分析路由：多模型视觉分析 + 营养核算 + 改造方案"""
import json
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

# 复用 handoff 根目录下的业务模块
_BACKEND = Path(__file__).resolve().parent.parent.parent   # backend/
_PROJECT = _BACKEND.parent                                # handoff/
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))

from modules.health_advisor import generate_plan, generate_swap_suggestions
from modules.nutrition_db import bmi, bmi_category, compute_calories, compute_macros, lookup_macros, tdee
from modules.vision_analyzer import analyze_with_check

from ..database import get_db
from ..routers.auth import get_current_user
from ..models import FoodProduct, HistoryItem, User, UserPlan

router = APIRouter(prefix="/api", tags=["analyze"])

DEFAULT_MODELS = ["qwen-vl-plus"]
VALID_GOALS = ["减脂", "控糖", "增肌", "均衡饮食"]


@router.post("/analyze")
def analyze(
    file: UploadFile = File(...),
    models: str = Form("qwen-vl-plus"),
    goal: str = Form("减脂"),
    profile: str = Form("{}"),
    db=Depends(get_db),
    user: User = Depends(get_current_user),
):
    if goal not in VALID_GOALS:
        goal = "减脂"
    try:
        profile_data = json.loads(profile or "{}")
    except Exception:
        profile_data = {}
    # 前端未传档案时：自动读取用户个人中心已保存的档案（有则用于个性化建议）
    if not profile_data:
        try:
            up = db.query(UserPlan).filter(UserPlan.user_id == user.id).first()
            if up and up.height_cm and up.weight_kg and up.age:
                profile_data = {
                    "height": up.height_cm, "weight": up.weight_kg,
                    "age": up.age, "gender": up.gender or "男",
                    "activity": up.activity or "轻度",
                }
        except Exception:
            profile_data = {}
    model_list = [m.strip() for m in models.split(",") if m.strip()] or DEFAULT_MODELS

    suffix = Path(file.filename or "food.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    try:
        # Module A：多模型视觉分析
        results = {}
        for m in model_list:
            results[m] = analyze_with_check(tmp_path, model=m)

        food_results = {m: r for m, r in results.items() if r.get("is_food") and r.get("analysis")}
        if not food_results:
            return {"is_food": False, "message": "未检测到食物，请上传包含食物、菜肴、食材或饮品的图片。", "results": results}

        primary_model = list(food_results)[0]
        primary = food_results[primary_model]["analysis"]

        # 热量核算（每个模型）
        computed_by_model = {}
        breakdown_by_model = {}
        unlisted_by_model = {}
        for m, r in food_results.items():
            cc, bd, ul = compute_calories(r["analysis"])
            # 每行补充每100g宏量（供前端编辑克重后重算营养结构）
            for item in bd:
                p100, c100, f100 = lookup_macros(item["name"]) or (0.0, 0.0, 0.0)
                item["protein_per_100g"] = round(p100, 1)
                item["carbs_per_100g"] = round(c100, 1)
                item["fat_per_100g"] = round(f100, 1)
            computed_by_model[m] = cc
            breakdown_by_model[m] = bd
            unlisted_by_model[m] = ul
        primary_cc = computed_by_model[primary_model]
        primary_breakdown = breakdown_by_model[primary_model]
        primary_unlisted = unlisted_by_model[primary_model]

        # 用户档案
        profile_info = None
        if profile_data:
            h = float(profile_data.get("height", 170))
            w = float(profile_data.get("weight", 65))
            a = int(profile_data.get("age", 22))
            g = profile_data.get("gender", "男")
            act = profile_data.get("activity", "轻度")
            profile_info = {
                "height": h, "weight": w, "age": a, "gender": g, "activity": act,
                "bmi": round(bmi(h, w), 1),
                "tdee": tdee(h, w, a, g, act),
            }

        # Module B：改造方案
        plan = generate_plan(primary, goal, profile=profile_info, computed_calories=primary_cc)

        # 食材替换建议
        try:
            swaps = generate_swap_suggestions(primary, goal)
        except Exception:
            swaps = []

        # 宏量营养素（主模型）
        macros, macros_details = compute_macros(primary)
        total_kcal_macro = (macros["protein"] * 4 + macros["carbs"] * 4 + macros["fat"] * 9) or 1
        macros["protein_pct"] = round(macros["protein"] * 4 / total_kcal_macro * 100, 1)
        macros["carbs_pct"] = round(macros["carbs"] * 4 / total_kcal_macro * 100, 1)
        macros["fat_pct"] = round(macros["fat"] * 9 / total_kcal_macro * 100, 1)

        # 品牌商品匹配（如蜜雪冰城柠檬水）
        matched_products = []
        try:
            kw = f"%{primary.get('dish_name', '')}%"
            matched_products = [
                {"brand": p.brand, "name": p.name, "serving": p.serving, "kcal": p.kcal, "note": p.note}
                for p in db.query(FoodProduct).filter(FoodProduct.name.like(kw)).limit(3)
            ]
        except Exception:
            matched_products = []

        return {
            "is_food": True,
            "matched_products": matched_products,
            "primary_model": primary_model,
            "models": list(food_results),
            "results": {m: food_results[m]["analysis"] for m in food_results},
            "calories_by_model": computed_by_model,
            "breakdown_by_model": breakdown_by_model,
            "unlisted_by_model": unlisted_by_model,
            "calories": primary_cc,
            "macros": macros,
            "macros_details": macros_details,
            "breakdown": primary_breakdown,
            "unlisted": primary_unlisted,
            "plan": plan,
            "swap_suggestions": swaps,
            "profile": profile_info,
        }
    finally:
        try:
            Path(tmp_path).unlink(missing_ok=True)
        except Exception:
            pass
