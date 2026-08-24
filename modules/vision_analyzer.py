"""
vision_analyzer.py - Multi-model food image analysis.

Supports DashScope (Qwen-VL), Zhipu (GLM-4V), and Doubao Vision models.
All configuration is loaded from config.py.
"""

import base64
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional


from config import API_ENDPOINTS, CACHE_FILES, LIMITS, MODELS
from modules.common import load_api_key, parse_json, retry, load_json_cache, save_json_cache

logger = logging.getLogger(__name__)

# -- Prompt Templates -------------------------------------------------------

SYSTEM_PROMPT = (
    "\u4f60\u662f\u4e00\u540d\u8d44\u6df1\u8425\u517b\u5e08\u517c\u4e13\u4e1a\u7f8e\u98df\u6444\u5f71\u5e08\u3002"
    "\u8bf7\u4ed4\u7ec6\u5206\u6790\u56fe\u7247\u4e2d\u7684\u98df\u7269\uff0c\u4f30\u7b97\u6bcf\u79cd\u98df\u6750\u7684\u514b\u91cd\uff0c"
    "\u53ea\u8f93\u51fa\u4e00\u4e2a\u4e25\u683c\u7684 JSON \u5bf9\u8c61\uff0c\u4e0d\u8981\u8f93\u51fa\u4efb\u4f55\u5176\u4ed6\u6587\u5b57\u3002"
)

USER_PROMPT = (
    "\u8bf7\u8f93\u51fa\u4ee5\u4e0b JSON \u683c\u5f0f\uff1a\n"
    "{\n"
    '  "dish_name": "\u83dc\u540d\uff08\u4e2d\u6587\uff09",\n'
    '  "ingredients": [\n'
    '    {"name": "\u9e21\u80f8\u8089", "weight_g": 150},\n'
    '    {"name": "\u98df\u7528\u6cb9", "weight_g": 20}\n'
    "  ],\n"
    '  "cooking_method": "\u70f9\u996a\u65b9\u5f0f\uff08\u82f1\u6587\uff0c\u5982 deep fried / steamed / braised / stir-fried\uff09",\n'
    '  "health_risk_tags": ["high oil","high sugar","high salt","high calorie","refined carb","processed meat"] \u4e2d\u9009\u62e9\uff0c\u82e5\u5065\u5eb7\u5219\u4e3a [],\n'
    '  "model_calories": \u6574\u4efd\u4f30\u7b97\u70ed\u91cf\uff08\u6574\u6570\uff0c\u5355\u4f4d kcal\uff0c\u4f9b\u53c2\u8003\uff09,\n'
    '  "visual_description": "English visual description for text-to-image generation, including dish, plating, tableware, colors, lighting"\n'
    "}\n"
    "\u8981\u6c42\uff1a\n"
    "1. ingredients \u9010\u9879\u5217\u51fa\u4e3b\u8981\u98df\u6750\u53ca**\u4f30\u7b97\u514b\u91cd** weight_g\uff08\u6574\u6570\uff0c\u719f\u91cd\uff09\uff0c\u98df\u7528\u6cb9/\u9171\u6599\u4e5f\u8981\u5355\u5217\uff1b\n"
    "2. \u514b\u91cd\u4ee3\u8868\u8be5\u98df\u6750\u5728\u6574\u4efd\u83dc\u54c1\u4e2d\u7684\u7528\u91cf\uff1b\n"
    "3. \u53ea\u8f93\u51fa JSON\uff0c\u4e0d\u8981\u4f7f\u7528 markdown \u4ee3\u7801\u5757\u3002"
)

IS_FOOD_PROMPT = (
    "\u4f60\u662f\u4e00\u4e2a\u98df\u7269\u56fe\u7247\u7b5b\u9009\u52a9\u624b\u3002\u5224\u65ad\u56fe\u7247\u7684\u4e3b\u4f53\u662f\u5426\u4e3a\u98df\u7269\u3001\u83dc\u80b4\u3001\u98df\u6750\u6216\u996e\u54c1\u3002"
    '\u53ea\u8f93\u51fa JSON {"is_food": true} \u6216 {"is_food": false}\uff0c\u4e0d\u8981\u8f93\u51fa\u4efb\u4f55\u5176\u4ed6\u6587\u5b57\u3002'
)

# -- Helpers ----------------------------------------------------------------

def _sha256(path: str) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _img_b64(image_path: str) -> str:
    """Read an image file and return its base64 encoding."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _optimized_b64(image_path: str, max_side: int = 1280, quality: int = 85) -> str:
    """Downscale to a JPEG and base64 it; vision APIs reject oversized images."""
    try:
        import io
        from PIL import Image
        img = Image.open(image_path)
        img = img.convert("RGB")
        if max(img.size) > max_side:
            img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality)
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        return _img_b64(image_path)


# -- DashScope (Qwen-VL) via SDK -------------------------------------------

def _dashscope_call(messages: list, model: str) -> dict:
    import dashscope
    from dashscope import MultiModalConversation
    """Call a DashScope vision model via the official SDK."""
    dashscope.api_key = load_api_key("dashscope")

    def fn():
        resp = MultiModalConversation.call(model=model, messages=messages)
        if resp.status_code != 200:
            raise RuntimeError(f"status={resp.status_code} code={resp.code} msg={resp.message}")
        return parse_json(resp.output.choices[0].message.content[0]["text"])

    return retry(fn)


def _dashscope_is_food(image_path: str, model: str) -> bool:
    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"file://{Path(image_path).as_posix()}", "max_pixels": 262144},
                {"text": IS_FOOD_PROMPT},
            ],
        }
    ]
    return bool(_dashscope_call(messages, model).get("is_food"))


def _dashscope_analyze(image_path: str, model: str) -> dict:
    messages = [
        {"role": "system", "content": [{"text": SYSTEM_PROMPT}]},
        {
            "role": "user",
            "content": [
                {"image": f"file://{Path(image_path).as_posix()}", "max_pixels": 1048576},
                {"text": USER_PROMPT},
            ],
        },
    ]
    return _dashscope_call(messages, model)


# -- Generic HTTP API caller (Zhipu / Doubao) ------------------------------

def _http_vision_call(
    provider: str,
    messages: list,
    model: str,
    temperature: float = 0.1,
) -> dict:
    import requests
    """
    Call a vision model via its HTTP API endpoint.
    Works for both Zhipu (GLM-4V) and Doubao since they share the same
    OpenAI-compatible request/response format.
    """
    api_key = load_api_key(provider)
    endpoint = API_ENDPOINTS[provider]
    timeout = LIMITS["api_timeout_seconds"]

    def fn():
        resp = requests.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=timeout,
        )
        if resp.status_code != 200:
            raise RuntimeError(
                f"{provider} status={resp.status_code} body={resp.text[:200]}"
            )
        data = resp.json()
        return parse_json(data["choices"][0]["message"]["content"])

    return retry(fn)


def _zhipu_messages(image_path: str, prompt: str, system: bool = False) -> list:
    """Build message payload for Zhipu GLM-4V (uses raw base64 without data URI)."""
    b64 = _optimized_b64(image_path)
    if system:
        return [
            {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": b64}},
                {"type": "text", "text": prompt},
            ]},
        ]
    return [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": b64}},
            {"type": "text", "text": prompt},
        ]},
    ]


def _doubao_messages(image_path: str, prompt: str, system: bool = False) -> list:
    """Build message payload for Doubao (uses data: URI for base64 images)."""
    b64 = f"data:image/jpeg;base64,{_optimized_b64(image_path)}"
    if system:
        return [
            {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
            {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": b64}},
                {"type": "text", "text": prompt},
            ]},
        ]
    return [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": b64}},
            {"type": "text", "text": prompt},
        ]},
    ]


# -- Public API -------------------------------------------------------------

def is_food(image_path: str, model: str = "qwen-vl-plus") -> bool:
    """Check whether the image contains food."""
    model_info = MODELS.get(model, {"provider": "dashscope"})
    provider = model_info["provider"]

    if provider == "dashscope":
        return _dashscope_is_food(image_path, model)
    elif provider == "zhipu":
        msgs = _zhipu_messages(image_path, IS_FOOD_PROMPT)
        return bool(_http_vision_call("zhipu", msgs, model).get("is_food"))
    elif provider == "doubao":
        actual_model = model_info.get("endpoint_id", model)
        msgs = _doubao_messages(image_path, IS_FOOD_PROMPT)
        return bool(_http_vision_call("doubao", msgs, actual_model).get("is_food"))
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def analyze_image(image_path: str, model: str = "qwen-vl-plus") -> dict:
    """Analyze a food image and return structured dish information."""
    model_info = MODELS.get(model, {"provider": "dashscope"})
    provider = model_info["provider"]

    if provider == "dashscope":
        return _dashscope_analyze(image_path, model)
    elif provider == "zhipu":
        msgs = _zhipu_messages(image_path, USER_PROMPT, system=True)
        return _http_vision_call("zhipu", msgs, model)
    elif provider == "doubao":
        actual_model = model_info.get("endpoint_id", model)
        msgs = _doubao_messages(image_path, USER_PROMPT, system=True)
        return _http_vision_call("doubao", msgs, actual_model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def analyze_with_check(
    image_path: str,
    model: str = "qwen-vl-plus",
    use_cache: bool = True,
) -> Dict[str, Any]:
    """
    First check if the image is food, then analyze it.
    Results are cached by image content hash + model name.
    """
    cache_file = CACHE_FILES["analysis"]
    key = f"{_sha256(image_path)}_{model}"
    cache = load_json_cache(cache_file) if use_cache else {}

    if key in cache:
        logger.debug("Cache hit for %s", key[:16])
        return cache[key]

    food = is_food(image_path, model)
    result: Dict[str, Any] = {"is_food": food, "analysis": None}
    if food:
        result["analysis"] = analyze_image(image_path, model)

    if use_cache:
        cache[key] = result
        save_json_cache(cache_file, cache)
    return result

