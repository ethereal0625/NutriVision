"""
meal_compensator.py - 膳食动态补偿模块

根据当日已摄入情况，动态生成后续餐次的补偿建议，
帮助用户在一天或一个周期内达到整体饮食平衡。
"""

import json
import logging
from typing import Any, Dict, List, Optional


from modules.llm_client import chat_completion

logger = logging.getLogger(__name__)


def generate_compensation_advice(
    today_intake: Dict[str, Any],
    goal: str,
    target_calories: int,
    macro_targets: Optional[Dict[str, float]] = None,
    profile: Optional[Dict[str, Any]] = None,
    weekly_trend: Optional[Dict[str, Any]] = None,
    model: str = "qwen-plus",
) -> Dict[str, Any]:
    """生成膳食补偿建议。"""

    # 计算剩余预算
    total_cal = today_intake.get("total_calories", 0)
    macros = today_intake.get("macros", {})
    remaining_cal = max(target_calories - total_cal, 0)

    remaining_macros = {}
    if macro_targets:
        for k in ["protein", "carbs", "fat"]:
            target_v = macro_targets.get(k, 0) or 0
            actual_v = macros.get(k, 0) or 0
            remaining_macros[k] = max(round(target_v - actual_v, 1), 0)

    # 判断当前状态
    ratio = total_cal / target_calories if target_calories else 0
    if ratio <= 0.3:
        status = "under"
    elif ratio <= 0.8:
        status = "on_track"
    elif ratio <= 1.1:
        status = "slightly_over"
    else:
        status = "over"

    # 判断是否还有可能拉回来
    meals = today_intake.get("meals", [])
    meal_types_done = [m.get("meal_type") for m in meals]
    remaining_meals = [m for m in ["早餐", "午餐", "晚餐", "加餐", "饮品"] if m not in meal_types_done]
    can_balance = remaining_cal > 0 and len(remaining_meals) > 0

    # 构建 Prompt
    profile_text = ""
    if profile:
        profile_text = (
            f"\n用户健康档案：身高 {profile.get('height')}cm，"
            f"体重 {profile.get('weight')}kg，{profile.get('gender')}，"
            f"{profile.get('age')}岁，活动水平：{profile.get('activity')}，"
            f"BMI {profile.get('bmi')}，TDEE约 {profile.get('tdee')} kcal/天。"
        )

    weekly_text = ""
    if weekly_trend:
        weekly_text = (
            f"\n本周趋势：日均摄入 {weekly_trend.get('avg_calories', 0)} kcal，"
            f"超标天数 {weekly_trend.get('days_over', 0)}，"
            f"不足天数 {weekly_trend.get('days_under', 0)}。"
        )

    meals_text = "\n".join([
        f"  - {m.get('meal_type', '?')}：{m.get('dish_name', '?')}（{m.get('calories', 0)} kcal）"
        for m in meals
    ]) or "  （暂无记录）"

    macro_text = ""
    if macros:
        macro_text = (
            f"\n今日宏量营养素摄入：蛋白质 {macros.get('protein', 0)}g，"
            f"碳水 {macros.get('carbs', 0)}g，脂肪 {macros.get('fat', 0)}g。"
        )

    macro_target_text = ""
    if macro_targets:
        macro_target_text = (
            f"\n每日宏量目标：蛋白质 {macro_targets.get('protein', 0)}g，"
            f"碳水 {macro_targets.get('carbs', 0)}g，脂肪 {macro_targets.get('fat', 0)}g。"
        )

    remaining_meals_str = ", ".join(remaining_meals) if remaining_meals else "无"

    prompt = (
        "你是一名资深营养师，擅长动态膳食规划。用户希望在一天内达到饮食平衡。\n\n"
        f"用户健康目标：{goal}"
        f"{profile_text}"
        f"\n每日目标热量：{target_calories} kcal"
        f"{macro_target_text}"
        f"\n\n【今日已摄入】"
        f"\n总热量：{total_cal} kcal（占目标 {round(ratio * 100)}%）"
        f"{macro_text}"
        f"\n\n【已记录餐次】"
        f"\n{meals_text}"
        f"\n\n【剩余预算】"
        f"\n热量：{remaining_cal} kcal"
        f"\n蛋白质：{remaining_macros.get('protein', '?')}g"
        f"\n碳水：{remaining_macros.get('carbs', '?')}g"
        f"\n脂肪：{remaining_macros.get('fat', '?')}g"
        f"\n\n【还未吃的餐次】{remaining_meals_str}"
        f"{weekly_text}"
        "\n\n请根据以上信息，给出动态补偿建议。只输出严格 JSON，不要 markdown："
        "\n{"
        '\n  "next_meal_advice": {'
        '\n    "direction": "下一餐的饮食方向（如：清淡高蛋白/低碳水/高纤维等，4-6字）",'
        '\n    "suggested_dishes": ["推荐菜品1", "推荐菜品2", "推荐菜品3"],'
        '\n    "avoid": ["需要避免的食物1", "需要避免的食物2"],'
        '\n    "reason": "推荐理由（结合已摄入情况分析，20-40字）"'
        "\n  },"
        '\n  "today_outlook": {'
        '\n    "can_balance": true,'
        '\n    "note": "对今天能否达标的判断和建议（30-50字）"'
        "\n  },"
        '\n  "tomorrow_advice": {'
        '\n    "needed": true,'
        '\n    "note": "如果今天无法平衡，给出明天的调整建议（30-50字）；否则为空字符串"'
        "\n  },"
        '\n  "weekly_insight": {'
        '\n    "trend": "improving/stable/declining",'
        '\n    "note": "本周趋势分析和整体建议（30-50字）"'
        "\n  }"
        "\n}"
    )

    try:
        advice = chat_completion(prompt, model)
    except Exception as e:
        logger.error("Compensation advice generation failed: %s", e)
        advice = {}

    return {
        "remaining_budget": {
            "calories": remaining_cal,
            **remaining_macros,
        },
        "status": status,
        "ratio_percent": round(ratio * 100, 1),
        "next_meal_advice": advice.get("next_meal_advice", {}),
        "today_outlook": advice.get("today_outlook", {}),
        "tomorrow_advice": advice.get("tomorrow_advice", {}),
        "weekly_insight": advice.get("weekly_insight", {}),
    }
