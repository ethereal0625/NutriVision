"""
health_advisor.py - AI-powered health advice and meal modification plans.

Uses DashScope Qwen-plus to generate personalized dietary recommendations
based on visual food analysis, user health goals, and optional health profiles.
"""

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

import dashscope
from dashscope import Generation

from config import CACHE_FILES, HEALTH_GOALS, LIMITS
from modules.common import load_api_key, load_json_cache, parse_json, retry, save_json_cache

logger = logging.getLogger(__name__)


def _cache_key(analysis: dict, goal: str, profile: Optional[dict], computed_calories: Optional[int]) -> str:
    """Generate a deterministic cache key from the input parameters."""
    payload = json.dumps(
        {"a": analysis, "g": goal, "p": profile, "c": computed_calories},
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_plan(
    analysis: dict,
    goal: str,
    model: str = "qwen-plus",
    profile: Optional[dict] = None,
    computed_calories: Optional[int] = None,
    daily_context: Optional[Dict[str, Any]] = None,
    use_cache: bool = True,
) -> dict:
    """
    Generate a health modification plan for a dish.

    Args:
        analysis: The food analysis result from vision_analyzer.
        goal: User's health goal (e.g. '减脂', '控糖').
        model: Text model to use.
        profile: Optional user health profile (height, weight, age, etc.).
        computed_calories: Calorie estimate from nutrition_db.
        use_cache: Whether to use caching.

    Returns:
        Dict with risk_points, modification_plan, healthy_dish_name, etc.
    """
    dashscope.api_key = load_api_key("dashscope")
    cache_file = CACHE_FILES["plan"]

    if use_cache:
        cache = load_json_cache(cache_file)
        ck = _cache_key(analysis, goal, profile, computed_calories)
        if ck in cache:
            logger.debug("Plan cache hit: %s", ck[:16])
            return cache[ck]

    profile_text = ""
    if profile:
        profile_text = (
            f"\n\u7528\u6237\u5065\u5eb7\u6863\u6848\uff1a\u8eab\u9ad8 {profile.get('height')}cm\uff0c"
            f"\u4f53\u91cd {profile.get('weight')}kg\uff0c{profile.get('gender')}\uff0c"
            f"{profile.get('age')}\u5c81\uff0c\u6d3b\u52a8\u6c34\u5e73\uff1a{profile.get('activity')}\uff0c"
            f"BMI {profile.get('bmi')}\uff0c\u5efa\u8bae\u6bcf\u65e5\u6444\u5165\u7ea6 {profile.get('tdee')} kcal\u3002"
        )
    cal_text = (
        f"\n\u7ecf\u8425\u517b\u6570\u636e\u5e93\u6838\u7b97\uff0c\u8be5\u83dc\u54c1\u603b\u70ed\u91cf\u7ea6 {computed_calories} kcal\u3002"
        if computed_calories else ""
    )

    daily_ctx_text = ""
    if daily_context:
        total = daily_context.get("total_calories", 0)
        target = daily_context.get("target_calories", 0)
        meals = daily_context.get("meals", [])
        if target and total:
            pct = round(total / target * 100)
            daily_ctx_text = f"\n\n【当日饮食上下文】用户今天已摄入 {total} kcal（目标 {target} kcal，已占 {pct}%）。"
            if meals:
                meal_details = "、".join([f"{m.get('meal_type','?')}吃了{m.get('dish_name','?')}（{m.get('calories',0)}kcal）" for m in meals])
                daily_ctx_text += f"已记录：{meal_details}。"
            remaining = max(target - total, 0)
            daily_ctx_text += f"剩余预算 {remaining} kcal。请结合这个背景给出改造建议，如果当前菜品会导致超标，请特别提醒。"

    prompt = (
        "\u4f60\u662f\u4e00\u540d\u8d44\u6df1\u8425\u517b\u5e08\u3002\u7528\u6237\u7684\u5065\u5eb7\u76ee\u6807\u662f\uff1a" + goal + "\u3002"
        + profile_text
        + cal_text + daily_ctx_text
        + "\n\u4ee5\u4e0b\u662f\u5bf9\u4e00\u9053\u83dc\u54c1\u7684\u89c6\u89c9\u5206\u6790\u7ed3\u679c\uff1a\n"
        + json.dumps(analysis, ensure_ascii=False)
        + "\n\u8bf7\u7ed3\u5408\u8be5\u76ee\u6807\u4e0e\u7528\u6237\u6863\u6848\uff08\u5982\u6709\uff09\uff0c\u627e\u51fa\u4e0d\u5065\u5eb7\u70b9\uff0c\u7ed9\u51fa\u5177\u4f53\u53ef\u64cd\u4f5c\u7684\u6539\u9020\u65b9\u6848\uff0c"
        "\u5e76\u7ed9\u51fa\u6539\u9020\u540e\u7684\u9884\u671f\u6548\u679c\uff08\u5982\u51cf\u5c11\u591a\u5c11\u70ed\u91cf\u3001\u575a\u6301\u591a\u4e45\u53ef\u51cf\u91cd\u591a\u5c11\u7b49\uff09\u3002"
        "\u53ea\u8f93\u51fa\u4e25\u683c JSON\uff0c\u4e0d\u8981\u4f7f\u7528 markdown \u4ee3\u7801\u5757\uff0c\u683c\u5f0f\uff1a\n"
        "{\n"
        '  "risk_points": ["\u4e0e\u76ee\u6807\u51b2\u7a81\u7684\u4e0d\u5065\u5eb7\u70b9\uff0c"-4\u6761],\n'
        '  "modification_plan": ["\u5177\u4f53\u6539\u9020\u6b65\u9aa4\uff08\u66ff\u6362\u98df\u6750/\u6539\u53d8\u70f9\u996a\u6cd5/\u8c03\u6574\u5206\u91cf\uff09\uff0c3-6\u6761],\n'
        '  "healthy_dish_name": "\u6539\u9020\u540e\u7684\u83dc\u540d\uff08\u4e2d\u6587\uff09",\n'
        '  "image_prompt": "English text-to-image prompt describing the healthy version of this dish, keeping the same plating, tableware and camera angle",\n'
        '  "expected_effects": "\u9884\u671f\u6548\u679c\uff0c\u7ed3\u5408\u7528\u6237\u76ee\u6807\u4e0e\u6863\u6848\uff0c\u7ed9\u51fa\u91cf\u5316\u4f30\u8ba1\uff08\u5982\u6bcf\u9910\u51cf\u5c11\u7ea6XXX kcal\uff0c\u575a\u63013\u4e2a\u6708\u53ef\u51cf\u91cd\u7ea6X kg\uff09",\n  "difficulty": "easy/medium/hard",\n  "before_after": {\n    "before": {"name": "\u539f\u83dc\u540d", "calories": 0, "tags": ["\u9ad8\u8102\u80aa"]},\n    "after": {"name": "\u6539\u9020\u540e\u83dc\u540d", "calories": 0, "tags": ["\u4f4e\u8102\u80aa"]}\n  }\n'
        "}"
    )

    def call():
        resp = Generation.call(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            result_format="message",
        )
        if resp.status_code != 200:
            raise RuntimeError(f"status={resp.status_code} code={resp.code} msg={resp.message}")
        return parse_json(resp.output.choices[0].message.content)

    result = retry(call)

    if use_cache:
        cache = load_json_cache(cache_file)
        cache[ck] = result
        save_json_cache(cache_file, cache)

    return result


def generate_swap_suggestions(
    analysis: dict,
    goal: str,
    model: str = "qwen-plus",
) -> List[Dict[str, str]]:
    """
    Generate ingredient swap suggestions for a dish.

    For each ingredient, suggests a healthier alternative with reasoning.

    Args:
        analysis: The food analysis result from vision_analyzer.
        goal: User's health goal.
        model: Text model to use.

    Returns:
        List of dicts with 'original', 'swap', and 'reason' keys.
    """
    dashscope.api_key = load_api_key("dashscope")

    daily_ctx_text = ""
    if daily_context:
        total = daily_context.get("total_calories", 0)
        target = daily_context.get("target_calories", 0)
        meals = daily_context.get("meals", [])
        if target and total:
            pct = round(total / target * 100)
            daily_ctx_text = f"\n\n【当日饮食上下文】用户今天已摄入 {total} kcal（目标 {target} kcal，已占 {pct}%）。"
            if meals:
                meal_details = "、".join([f"{m.get('meal_type','?')}吃了{m.get('dish_name','?')}（{m.get('calories',0)}kcal）" for m in meals])
                daily_ctx_text += f"已记录：{meal_details}。"
            remaining = max(target - total, 0)
            daily_ctx_text += f"剩余预算 {remaining} kcal。请结合这个背景给出改造建议，如果当前菜品会导致超标，请特别提醒。"

    prompt = (
        "\u4f60\u662f\u4e00\u540d\u8d44\u6df1\u8425\u517b\u5e08\u3002\u7528\u6237\u7684\u5065\u5eb7\u76ee\u6807\u662f\uff1a" + goal + "\u3002\n"
        "\u4ee5\u4e0b\u662f\u5bf9\u4e00\u9053\u83dc\u54c1\u7684\u5206\u6790\u7ed3\u679c\uff1a\n"
        + json.dumps(analysis, ensure_ascii=False)
        + "\n\u8bf7\u9488\u5bf9\u6bcf\u79cd\u98df\u6750\uff0c\u7ed9\u51fa\u66f4\u5065\u5eb7\u7684\u66ff\u6362\u5efa\u8bae\u3002\u53ea\u8f93\u51fa\u4e25\u683c JSON \u65b0\u7ec4\uff0c\u4e0d\u8981 markdown\uff1a\n"
        '[{"original": "\u539f\u98df\u6750\u540d", "swap": "\u66ff\u4ee3\u98df\u6750\u540d", "reason": "\u66ff\u6362\u7406\u7531\uff0810\u5b57\u4ee5\u5185\uff09"}, ...]\n'
        "\u5982\u679c\u67d0\u4e9b\u98df\u6750\u5df2\u7ecf\u8db3\u591f\u5065\u5eb7\uff0c\u53ef\u4ee5\u8df3\u8fc7\u3002\u53ea\u8f93\u51fa\u6709\u66ff\u6362\u4ef7\u503c\u7684\u98df\u6750\uff0c\u6700\u591a8\u6761\u3002"
    )

    def call():
        resp = Generation.call(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            result_format="message",
        )
        if resp.status_code != 200:
            raise RuntimeError(f"status={resp.status_code} code={resp.code} msg={resp.message}")
        return parse_json(resp.output.choices[0].message.content)

    return retry(call)


# Re-export for backward compatibility
from config import HEALTH_GOALS as GOALS

