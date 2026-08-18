"""
image_generator.py - Text-to-image generation via DashScope wanx-v1.
"""

import logging
from pathlib import Path

import dashscope
import requests
from dashscope import ImageSynthesis

from config import LIMITS
from modules.common import load_api_key

logger = logging.getLogger(__name__)


def generate_image(
    prompt: str,
    out_path: str,
    size: str = "1024*1024",
    model: str = "wanx-v1",
    timeout: int = None,
) -> str:
    """
    Generate an image from a text prompt using DashScope wanx model.

    Args:
        prompt: Text description of the image to generate.
        out_path: File path to save the generated image.
        size: Image dimensions (e.g. '1024*1024').
        model: Image generation model name.
        timeout: HTTP timeout in seconds for downloading the result.

    Returns:
        The output file path.
    """
    if timeout is None:
        timeout = LIMITS["image_gen_timeout_seconds"]

    dashscope.api_key = load_api_key("dashscope")
    resp = ImageSynthesis.call(model=model, prompt=prompt, n=1, size=size)
    if resp.status_code != 200:
        raise RuntimeError(
            f"status={resp.status_code} code={resp.code} msg={resp.message}"
        )
    url = resp.output.results[0]["url"]
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_bytes(r.content)
    logger.info("Generated image saved to %s", out_path)
    return out_path

