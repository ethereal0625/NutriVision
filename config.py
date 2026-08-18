"""
config.py - Centralized configuration for NutriVision.

All API endpoints, model definitions, cache paths, and system limits
are defined here so that other modules only need to import from this file.
"""

from pathlib import Path
from typing import Dict, Any, List

# -- Paths -----------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent
OUTPUT_DIR: Path = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# -- API Endpoints ---------------------------------------------------------
API_ENDPOINTS: Dict[str, str] = {
    "dashscope": "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
    "zhipu":     "https://open.bigmodel.cn/api/paas/v4/chat/completions",
    "doubao":    "https://ark.cn-beijing.volces.com/api/v3/chat/completions",
}

# -- Model Registry --------------------------------------------------------
MODELS: Dict[str, Dict[str, Any]] = {
    "qwen-vl-plus":    {"provider": "dashscope", "type": "vision"},
    "qwen-vl-max":     {"provider": "dashscope", "type": "vision"},
    "glm-4v":          {"provider": "zhipu",     "type": "vision"},
    "doubao-seed-2.0": {"provider": "doubao", "type": "vision", "endpoint_id": "ep-20260815154546-cz6bs"},
    "qwen-plus":       {"provider": "dashscope", "type": "text"},
    "wanx-v1":         {"provider": "dashscope", "type": "image_gen"},
}

# -- API Key Environment Variable Names ------------------------------------
API_KEY_ENV_VARS: Dict[str, str] = {
    "dashscope": "DASHSCOPE_API_KEY",
    "zhipu":     "ZHIPU_API_KEY",
    "doubao":    "DOUBAO_API_KEY",
}

# -- Cache Files -----------------------------------------------------------
CACHE_FILES: Dict[str, Path] = {
    "analysis": OUTPUT_DIR / "analysis_cache.json",
    "plan":     OUTPUT_DIR / "plan_cache.json",
    "history":  OUTPUT_DIR / "history.json",
}

# -- Nutrition Defaults ----------------------------------------------------
NUTRITION_DEFAULTS: Dict[str, Any] = {
    "default_kcal_per_100g": 120,
    "fry_oil_g": 30,
    "stir_oil_g": 15,
}

# -- Health Goals ----------------------------------------------------------
HEALTH_GOALS: List[str] = ["\u51cf\u8102", "\u63a7\u7cd6", "\u589e\u808c", "\u5747\u8861\u996e\u98df"]

# -- System Limits ---------------------------------------------------------
LIMITS: Dict[str, int] = {
    "max_history_items": 50,
    "max_retry_attempts": 4,
    "api_timeout_seconds": 90,
    "image_gen_timeout_seconds": 180,
}

