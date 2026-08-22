"""
common.py - Shared utilities: API key loading, JSON parsing, retry, caching.
"""

import os
import re
import json
import time
import logging
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv

from config import BASE_DIR, API_KEY_ENV_VARS, LIMITS

logger = logging.getLogger(__name__)

# Load .env file on import
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
    logger.debug("Loaded .env from %s", _env_file)


def load_api_key(provider: str = "dashscope") -> str:
    """Load API key for the given provider from environment or .env file."""
    env_var = API_KEY_ENV_VARS.get(provider)
    if not env_var:
        raise ValueError(f"Unknown provider: {provider}")
    key = os.environ.get(env_var)
    if not key:
        raise SystemExit(f"\u672a\u8bbe\u7f6e {env_var}\uff0c\u8bf7\u5728 .env \u6587\u4ef6\u4e2d\u914d\u7f6e")
    return key


# Backward-compatible aliases
def load_zhipu_api_key() -> str:
    """Load Zhipu API key (alias for load_api_key('zhipu'))."""
    return load_api_key("zhipu")


def load_doubao_api_key() -> str:
    """Load Doubao API key (alias for load_api_key('doubao'))."""
    return load_api_key("doubao")


def _extract_json_span(text: str):
    """找到第一个完整 JSON 对象/数组的起始与结束下标，失败返回 None。"""
    for i, ch in enumerate(text):
        if ch not in "[{":
            continue
        depth = 0
        in_str = False
        escape = False
        for j in range(i, len(text)):
            c = text[j]
            if in_str:
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == '"':
                    in_str = False
                continue
            if c == '"':
                in_str = True
            elif c in "[{":
                depth += 1
            elif c in "]}":
                depth -= 1
                if depth == 0:
                    return i, j + 1
        break
    return None


def parse_json(text: str) -> Any:
    """Extract and parse the first JSON object/array from model output text."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except Exception:
        pass
    span = _extract_json_span(text)
    if span:
        try:
            return json.loads(text[span[0]:span[1]])
        except Exception:
            pass
    raise ValueError(f"\u65e0\u6cd5\u89e3\u6790\u6a21\u578b\u8f93\u51fa: {text[:100]}")


def retry(fn: Callable, attempts: Optional[int] = None) -> Any:
    """Retry a function with exponential backoff."""
    if attempts is None:
        attempts = LIMITS["max_retry_attempts"]
    last_exc: Optional[Exception] = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:
            last_exc = e
            logger.warning("Attempt %d/%d failed: %s", i + 1, attempts, e)
            time.sleep(2 ** i)
    raise last_exc  # type: ignore[misc]


def load_json_cache(path: Path) -> dict:
    """Load a JSON cache file, returning empty dict on any error."""
    path = Path(path)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_json_cache(path: Path, data: dict) -> None:
    """Save data to a JSON cache file."""
    path = Path(path)
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

