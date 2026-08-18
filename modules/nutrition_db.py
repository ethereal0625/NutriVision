"""
nutrition_db.py - Local food calorie database and nutrition computation.

Contains a comprehensive Chinese food calorie database and functions
to compute total calories from a dish's ingredient list.
"""

import logging
from typing import Dict, List, Optional, Tuple

from config import NUTRITION_DEFAULTS

logger = logging.getLogger(__name__)

DEFAULT_PER_100G = NUTRITION_DEFAULTS["default_kcal_per_100g"]
FRY_OIL_G = NUTRITION_DEFAULTS["fry_oil_g"]
STIR_OIL_G = NUTRITION_DEFAULTS["stir_oil_g"]

# -- Food Calorie Database (kcal per 100g) ----------------------------------

FOOD_CALORIES: Dict[str, int] = {
    "\u9e21\u80f8\u8089": 165, "\u9e21\u817f\u8089": 181, "\u9e21\u7fc5": 222, "\u9e21\u76ae": 363, "\u9e21\u722a": 254,
    "\u9e2d\u8089": 240, "\u7626\u732a\u8089": 143, "\u4e94\u82b1\u8089": 395, "\u91cc\u810a\u8089": 155, "\u732a\u91cc\u810a": 155,
    "\u732a\u6392\u8089": 278, "\u6392\u9aa8": 264, "\u732a\u8e44": 260, "\u725b\u8089": 125, "\u725b\u8169": 332,
    "\u725b\u91cc\u810a": 107, "\u7f8a\u8089": 203, "\u57fa\u6839": 393, "\u9999\u80a0": 508, "\u706b\u817f": 330,
    "\u9e21\u86cb": 144, "\u9e2d\u86cb": 180, "\u76ae\u86cb": 171,
    "\u4e09\u6587\u9c7c": 208, "\u9c88\u9c7c": 105, "\u5e26\u9c7c": 127, "\u9ec4\u82b1\u9c7c": 99, "\u9c23\u9c7c": 109,
    "\u8349\u9c7c": 113, "\u9cab\u9c7c": 108, "\u9c76\u9c7c": 88, "\u867e": 101, "\u57fa\u56f4\u867e": 101,
    "\u5c0f\u9f99\u867e": 90, "\u87f9": 95, "\u9c7f\u9c7c": 92, "\u7ae0\u9c7c": 83, "\u6247\u8d1d": 60,
    "\u751f\u869d": 73, "\u86e4\u8782": 62, "\u9c9c\u9c7c": 84,
    "\u897f\u5170\u82b1": 36, "\u82b1\u6930\u83dc": 25, "\u83e0\u83dc": 28, "\u751f\u83dc": 16, "\u6cb9\u9ea6\u83dc": 15,
    "\u9ec4\u74dc": 16, "\u756a\u8304": 20, "\u897f\u7ea2\u67ff": 20, "\u80e1\u841d\u535c": 41, "\u767d\u841d\u535c": 23,
    "\u571f\u8c46": 77, "\u9a6c\u94c3\u85af": 77, "\u7ea2\u85af": 86, "\u5730\u74dc": 86, "\u7389\u7c73": 112,
    "\u9752\u6912": 22, "\u8fa3\u6912": 25, "\u6d0b\u8471": 40, "\u5927\u767d\u83dc": 20, "\u767d\u83dc": 20,
    "\u8304\u5b50": 25, "\u56db\u5b63\u8c46": 31, "\u5357\u74dc": 23, "\u51ac\u74dc": 12, "\u5c71\u836f": 57,
    "\u83b2\u85d5": 74, "\u85e4": 74, "\u86d1\u83c7": 22, "\u9999\u83c7": 26, "\u91d1\u9488\u83c7": 26,
    "\u674f\u9c8d\u83c7": 35, "\u6728\u8033": 27, "\u6d77\u5e26": 13, "\u7af9\u7b0b": 23, "\u82a6\u7b0b": 22,
    "\u82b9\u83dc": 20, "\u97ed\u83dc": 25, "\u8c46\u82bd": 30, "\u83b4\u7b0b": 15,
    "\u8c46\u8150": 84, "\u8c46\u8150\u5e72": 140, "\u8c46\u5e72": 140, "\u8150\u7afa": 461, "\u8c46\u6d46": 31,
    "\u7c89\u4e1d": 338, "\u7c89\u6761": 337, "\u5e72\u571f\u8c46": 154,
    "\u7c73\u996d": 116, "\u767d\u7c73\u996d": 116, "\u767d\u7ca5": 46, "\u7ca5": 46, "\u9762\u6761": 110,
    "\u610f\u5927\u5229\u9762": 131, "\u901a\u5fc3\u7c89": 131, "\u4e4c\u51ac\u9762": 120, "\u7c73\u7c89": 346,
    "\u9992\u5934": 223, "\u82b1\u5377": 217, "\u9762\u5305": 265, "\u5168\u9ea6\u9762\u5305": 246,
    "\u71d5\u9ea6": 389, "\u7ce0\u7c73": 111, "\u997a\u5b50": 240, "\u5305\u5b50": 227, "\u7cef\u5b50": 195,
    "\u6c64\u5706": 270, "\u6cb9\u6761": 388, "\u70e7\u997c": 326, "\u714e\u997c": 336, "\u70d9\u997c": 255,
    "\u7092\u996d": 163, "\u62ab\u8428": 266, "\u6c49\u5821": 295, "\u5bff\u53f8": 160, "\u4e09\u660e\u6cbb": 240,
    "\u82f9\u679c": 53, "\u9999\u8549": 93, "\u6a59\u5b50": 48, "\u897f\u74dc": 30, "\u8461\u8404": 45,
    "\u8349\u8393": 32, "\u84dd\u8393": 57, "\u68a8": 51, "\u6851": 42, "\u731b\u7334\u6843": 61,
    "\u706b\u9f99\u679c": 55, "\u8292\u679c": 60, "\u83e0\u841d": 44, "\u6930\u5b50": 241, "\u725b\u6cb9\u679c": 160,
    "\u98df\u7528\u6cb9": 899, "\u6cb9": 899, "\u6a44\u6984\u6cb9": 899, "\u83dc\u7c7d\u6cb9": 899,
    "\u7389\u7c73\u6cb9": 899, "\u82b1\u751f\u6cb9": 899, "\u5927\u8c46\u6cb9": 899, "\u82b1\u6912\u6cb9": 899,
    "\u732a\u6cb9": 897, "\u9ec4\u6cb9": 717, "\u6c99\u62c9\u9171": 700, "\u86cb\u9ec4\u9171": 680,
    "\u82b1\u751f\u9171": 588, "\u829d\u9ebb\u9171": 630, "\u8702\u871c": 321, "\u767d\u7802\u7cd6": 400, "\u7cd6": 400,
    "\u51b0\u7cd6": 400, "\u9171\u6cb9": 63, "\u751f\u62bd": 63, "\u8001\u62bd": 63, "\u756a\u8304\u9171": 81,
    "\u8fa3\u6912\u6cb9": 900, "\u869d\u6cb9": 114, "\u8c46\u74e3\u9171": 178, "\u8c46\u8c46": 250,
    "\u5496\u55b1\u9171": 140, "\u829d\u58eb": 328, "\u5976\u916a": 328, "\u725b\u5976": 54, "\u9178\u5976": 72,
    "\u6de1\u5976\u6cb9": 340, "\u5976\u6cb9": 340,
    "\u82b1\u751f": 574, "\u6838\u6843": 646, "\u674f\u4ec1": 579, "\u8170\u679c": 553, "\u5f00\u5fc3\u679c": 562,
    "\u74dc\u5b50": 606, "\u6817\u5b50": 185, "\u69b4\u5b50": 598, "\u677e\u5b50": 621,
    "\u85af\u6761": 312, "\u70b8\u9e21": 246, "\u53ef\u4e50": 43, "\u5976\u8336": 70, "\u51b0\u6dc7\u6dcb": 207,
    "\u96ea\u7cd5": 207, "\u5de7\u514b\u529b": 546, "\u86cb\u7cd5": 348, "\u997c\u5e72": 435, "\u85af\u7247": 548,
    "\u7206\u7c73\u82b1": 387, "\u751c\u751c\u5708": 421, "\u6708\u997c": 405, "\u6c64": 30, "\u9e21\u6c64": 40,
    "\u725b\u8089\u6c64": 80, "\u706b\u9505": 200, "\u9ebb\u8fa3\u70eb": 150, "\u70e4\u8089": 240, "\u70e7\u70e4": 220,
    "\u70e4\u9e2d": 436, "\u7ea2\u70e7\u8089": 470, "\u7cd6\u918b\u91cc\u810a": 290, "\u5bab\u4fdd\u9e21\u4e01": 210,
    "\u9c7c\u9999\u8089\u4e1d": 190, "\u9ebb\u5a46\u8c46\u8150": 130, "\u56de\u9505\u8089": 380, "\u7ea2\u70e7\u9c7c": 170,
    "\u6e05\u84b8\u9c7c": 130, "\u767d\u707c\u867e": 105, "\u852c\u83dc\u6c99\u62c9": 60, "\u51ef\u6492\u6c99\u62c9": 250,
    "\u6c34\u679c\u6c99\u62c9": 80, "\u7ea2\u85af\u7ca5": 60, "\u76ae\u86cb\u7626\u8089\u7ca5": 90,
}


def lookup(name: str) -> Optional[int]:
    """Look up the calorie content (kcal/100g) for a food item by name."""
    name = (name or "").strip().lower()
    if not name:
        return None
    for key in sorted(FOOD_CALORIES, key=len, reverse=True):
        if len(key) < 2:
            continue
        if key in name or name in key:
            return FOOD_CALORIES[key]
    return None


def compute_calories(analysis: dict) -> Tuple[int, List[dict], List[str]]:
    """
    Compute total calories from a dish analysis.

    Args:
        analysis: Dict with 'ingredients' and 'cooking_method' keys.

    Returns:
        Tuple of (total_calories, breakdown_list, unlisted_ingredients).
    """
    total = 0.0
    breakdown: List[dict] = []
    unlisted: List[str] = []

    for item in analysis.get("ingredients", []):
        if isinstance(item, dict):
            name = str(item.get("name", ""))
            weight = float(item.get("weight_g", 0) or 0)
        else:
            name = str(item)
            weight = 0.0

        kcal100 = lookup(name)
        if kcal100 is None:
            kcal100 = DEFAULT_PER_100G
            unlisted.append(name)

        cal = weight * kcal100 / 100.0
        breakdown.append({
            "name": name,
            "weight_g": weight,
            "kcal_per_100g": kcal100,
            "calories": round(cal),
        })
        total += cal

    # Add estimated oil for frying/stir-frying if not already listed
    method = (analysis.get("cooking_method") or "").lower()
    has_oil = any("\u6cb9" in b["name"] for b in breakdown)
    oil_add = 0
    if any(k in method for k in ("deep", "frit")):
        oil_add = FRY_OIL_G
    elif any(k in method for k in ("fry", "saut\u00e9", "stir", "pan")) and not has_oil:
        oil_add = STIR_OIL_G
    if oil_add:
        cal = oil_add * FOOD_CALORIES["\u98df\u7528\u6cb9"] / 100.0
        breakdown.append({
            "name": "\u98df\u7528\u6cb9\uff08\u4f30\u7b97\uff09", "weight_g": oil_add,
            "kcal_per_100g": FOOD_CALORIES["\u98df\u7528\u6cb9"], "calories": round(cal),
        })
        total += cal

    return round(total), breakdown, unlisted


def bmi(height_cm: float, weight_kg: float) -> float:
    """Calculate BMI from height (cm) and weight (kg)."""
    h = height_cm / 100.0
    return round(weight_kg / (h * h), 1)


def bmi_category(v: float) -> str:
    """Return Chinese BMI category string."""
    if v < 18.5:
        return "\u504f\u7626"
    if v < 24:
        return "\u6b63\u5e38"
    if v < 28:
        return "\u504f\u80d6"
    return "\u80a5\u80d6"


def tdee(height_cm: float, weight_kg: float, age: int, gender: str, activity: str) -> int:
    """Calculate Total Daily Energy Expenditure using Mifflin-St Jeor equation."""
    if gender == "\u7537":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    factors = {"\u4e45\u5750": 1.2, "\u8f7b\u5ea6": 1.375, "\u4e2d\u5ea6": 1.55, "\u9ad8\u5f3a\u5ea6": 1.725}
    return round(bmr * factors.get(activity, 1.2))

