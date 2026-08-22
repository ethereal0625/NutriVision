"""
nutrition_score.py - 营养评分系统

根据食物的热量、宏量营养素比例、烹饪方式等综合评分
评分等级：A（优秀）、B（良好）、C（一般）、D（需改善）
"""

from typing import Dict, Optional


def calculate_nutrition_score(
    calories: int,
    macros: Dict[str, float],
    cooking_method: str = "",
    goal: str = "均衡饮食",
    target_calories: int = 2000,
) -> Dict:
    """
    计算营养评分

    Args:
        calories: 总热量 (kcal)
        macros: {"protein": g, "carbs": g, "fat": g}
        cooking_method: 烹饪方式
        goal: 健康目标
        target_calories: 每日目标热量

    Returns:
        {
            "grade": "A/B/C/D",
            "score": 0-100,
            "color": "green/yellow/orange/red",
            "label": "优秀/良好/一般/需改善",
            "details": {
                "calorie_score": 0-100,
                "macro_score": 0-100,
                "cooking_score": 0-100,
            },
            "advice": "改善建议"
        }
    """
    # 1. 热量评分（占 40%）
    calorie_ratio = calories / target_calories if target_calories else 0.5
    if calorie_ratio <= 0.3:
        calorie_score = 100  # 很低热量
    elif calorie_ratio <= 0.5:
        calorie_score = 85
    elif calorie_ratio <= 0.7:
        calorie_score = 70
    elif calorie_ratio <= 1.0:
        calorie_score = 60
    else:
        calorie_score = max(0, 60 - (calorie_ratio - 1.0) * 100)

    # 2. 宏量营养素评分（占 40%）
    total_kcal = macros.get("protein", 0) * 4 + macros.get("carbs", 0) * 4 + macros.get("fat", 0) * 9
    if total_kcal > 0:
        protein_pct = macros.get("protein", 0) * 4 / total_kcal * 100
        carbs_pct = macros.get("carbs", 0) * 4 / total_kcal * 100
        fat_pct = macros.get("fat", 0) * 9 / total_kcal * 100
    else:
        protein_pct = carbs_pct = fat_pct = 33

    # 理想比例：蛋白 20-30%, 碳水 50-60%, 脂肪 20-30%
    protein_score = 100 if 20 <= protein_pct <= 35 else max(0, 100 - abs(protein_pct - 27) * 3)
    carbs_score = 100 if 45 <= carbs_pct <= 65 else max(0, 100 - abs(carbs_pct - 55) * 2)
    fat_score = 100 if 20 <= fat_pct <= 35 else max(0, 100 - abs(fat_pct - 27) * 3)
    macro_score = (protein_score + carbs_score + fat_score) / 3

    # 3. 烹饪方式评分（占 20%）
    healthy_methods = ["清蒸", "水煮", "凉拌", "烤", "炖", "焖"]
    moderate_methods = ["炒", "煎", "红烧", "卤"]
    unhealthy_methods = ["炸", "油炸", "干", "糖醋"]

    if any(m in cooking_method for m in healthy_methods):
        cooking_score = 90
    elif any(m in cooking_method for m in moderate_methods):
        cooking_score = 60
    elif any(m in cooking_method for m in unhealthy_methods):
        cooking_score = 30
    else:
        cooking_score = 70  # 默认

    # 综合评分
    total_score = round(calorie_score * 0.4 + macro_score * 0.4 + cooking_score * 0.2)

    # 评级
    if total_score >= 85:
        grade, color, label = "A", "green", "优秀"
    elif total_score >= 70:
        grade, color, label = "B", "blue", "良好"
    elif total_score >= 55:
        grade, color, label = "C", "orange", "一般"
    else:
        grade, color, label = "D", "red", "需改善"

    # 改善建议
    advice = []
    if calorie_score < 70:
        advice.append(f"热量偏高（{calories}kcal），建议控制分量")
    if protein_pct < 20:
        advice.append("蛋白质不足，建议增加瘦肉/蛋/豆制品")
    if fat_pct > 35:
        advice.append("脂肪偏高，建议减少油炸/肥肉")
    if carbs_pct > 65:
        advice.append("碳水偏高，建议减少精制主食")
    if cooking_score < 60:
        advice.append("烹饪方式不够健康，建议改为清蒸/水煮")

    if not advice:
        advice.append("营养均衡，继续保持！")

    return {
        "grade": grade,
        "score": total_score,
        "color": color,
        "label": label,
        "details": {
            "calorie_score": round(calorie_score),
            "macro_score": round(macro_score),
            "cooking_score": round(cooking_score),
        },
        "advice": advice,
    }